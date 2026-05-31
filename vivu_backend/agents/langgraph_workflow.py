"""
LangGraph workflow cho travel planning voi checkpoint va progress callback.
"""
import inspect
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from config.langsmith_config import get_langsmith_config
from utils.cache import get_redis_client
from utils.error_handling import ErrorType, RetryConfig, classify_error, retry_with_backoff

from .state import TravelPlanningState
from .travel_agents.accommodation_agent import AccommodationAgent
from .travel_agents.activities_agent import ActivitiesAgent
from .travel_agents.budget_agent import BudgetAgent
from .travel_agents.flight_agent import FlightAgent
from .travel_agents.planning_agent import PlanningAgent
from .travel_agents.transport_agent import TransportAgent

logger = logging.getLogger(__name__)


class LangGraphTravelWorkflow:
    """Workflow LangGraph cho travel planning."""

    def __init__(self):
        self.langsmith_config = get_langsmith_config()
        self.transport_agent = TransportAgent()
        self.flight_agent = FlightAgent()
        self.accommodation_agent = AccommodationAgent()
        self.activities_agent = ActivitiesAgent()
        self.budget_agent = BudgetAgent()
        self.planning_agent = PlanningAgent()
        self.progress_callback = None
        self.graph = self._build_graph()
        self.checkpointer = self._build_checkpointer() if self.graph else None
        self.app = self.graph.compile(checkpointer=self.checkpointer) if self.graph else None

    def _build_checkpointer(self):
        try:
            client = get_redis_client()
            if client:
                try:
                    from langgraph.checkpoint.redis import RedisSaver

                    logger.info("Using RedisSaver for LangGraph checkpoints")
                    return RedisSaver(client=client)
                except Exception:
                    logger.warning("RedisSaver unavailable, fallback to MemorySaver", exc_info=True)
        except Exception:
            logger.warning("Cannot initialize Redis-backed checkpointer, fallback to MemorySaver", exc_info=True)
        return MemorySaver()

    async def _emit_progress(self, event_type: str, payload: Dict[str, Any]) -> None:
        if not self.progress_callback:
            return
        result = self.progress_callback(event_type, payload)
        if inspect.isawaitable(result):
            await result

    def _build_graph(self) -> Optional[StateGraph]:
        try:
            workflow = StateGraph(TravelPlanningState)
            workflow.add_node("transport", self._transport_node)
            workflow.add_node("flight", self._flight_node)
            workflow.add_node("accommodation", self._accommodation_node)
            workflow.add_node("activities", self._activities_node)
            workflow.add_node("budget", self._budget_node)
            workflow.add_node("planning", self._planning_node)
            workflow.set_entry_point("transport")
            workflow.add_conditional_edges(
                "transport",
                self._should_use_flight,
                {"yes": "flight", "no": "accommodation"},
            )
            workflow.add_edge("flight", "accommodation")
            workflow.add_edge("accommodation", "activities")
            workflow.add_edge("activities", "budget")
            workflow.add_edge("budget", "planning")
            workflow.add_edge("planning", END)
            return workflow
        except Exception as exc:
            logger.error("Error building graph: %s", exc, exc_info=True)
            return None

    def _should_use_flight(self, state: TravelPlanningState) -> str:
        transport = state.get("transport", {})
        return "yes" if transport.get("suggested_method", "") == "flight" else "no"

    def _empty_transport_payload(self) -> Dict[str, Any]:
        return {
            "suggested_method": "ground",
            "estimated_cost_vnd": 0,
            "distance_km": 0,
            "duration_minutes": 0,
            "notes": "Su dung phuong an fallback do node transport gap loi.",
        }

    def _empty_budget_payload(self, state: TravelPlanningState) -> Dict[str, Any]:
        transport = float(state.get("transport_cost") or 0)
        accommodation = float(state.get("accommodation_cost") or 0)
        activities = float(state.get("activities_cost") or 0)
        dining = float(state.get("dining_cost") or 0)
        total = int(transport + accommodation + activities + dining)
        return {
            "total_vnd": total,
            "breakdown": {
                "transport": transport,
                "accommodation": accommodation,
                "activities": activities,
                "dining": dining,
            },
            "notes": "Ngan sach fallback duoc tong hop tu du lieu hien co.",
        }

    def _build_fallback_itinerary_json(self, state: TravelPlanningState, reason: str) -> Dict[str, Any]:
        start_date_raw = state.get("start_date") or datetime.utcnow().strftime("%Y-%m-%d")
        try:
            start_date = datetime.strptime(start_date_raw, "%Y-%m-%d")
        except ValueError:
            start_date = datetime.utcnow()
        total_days = max(1, int(state.get("days") or 1))
        destination = state.get("destination") or "diem den"
        daily_itinerary = []
        for index in range(total_days):
            visit_date = (start_date + timedelta(days=index)).strftime("%Y-%m-%d")
            daily_itinerary.append(
                {
                    "day": index + 1,
                    "date": visit_date,
                    "theme": f"Ngay {index + 1} tai {destination}",
                    "route_flow": [],
                    "timeline": [
                        {
                            "time_start": "09:00",
                            "time_end": "10:00",
                            "place_id": "",
                            "activity_name": "Cap nhat lich trinh thu cong",
                            "cost": 0,
                            "transport_to_next": {
                                "mode": "Tu cap nhat",
                                "duration_mins": 0,
                                "distance_km": 0.0,
                            },
                            "local_hint": "He thong dang su dung lich trinh fallback an toan.",
                            "plan_b_fallback": {
                                "place_id": None,
                                "name": "Theo doi cap nhat tu nhan vien ho tro",
                                "reason": reason[:200],
                            },
                        }
                    ],
                }
            )
        budget_payload = self._empty_budget_payload(state)
        return {
            "trip_overview": {
                "total_distance_km": 0.0,
                "total_estimated_cost": int(budget_payload.get("total_vnd", 0)),
                "fitness_level_required": "Thap",
            },
            "daily_itinerary": daily_itinerary,
            "budget_analytics": {
                "accommodation_total": int(float(state.get("accommodation_cost") or 0)),
                "transportation_total": int(float(state.get("transport_cost") or 0)),
                "food_total": int(float(state.get("dining_cost") or 0)),
                "activities_total": int(float(state.get("activities_cost") or 0)),
                "emergency_buffer": 0,
            },
            "packing_checklist": {
                "documents": ["Can cuoc cong dan"],
                "clothing": ["Trang phuc phu hop thoi tiet"],
                "medical": ["Thuoc ca nhan"],
            },
        }

    async def _emit_node_error(self, state: TravelPlanningState, *, step: str, message: str) -> None:
        await self._emit_progress(
            "progress",
            {
                "step": step,
                "message": message,
                "completed_steps": state.get("completed_steps", []),
                "status": "degraded",
            },
        )

    def _apply_node_fallback(self, state: TravelPlanningState, *, step: str, error_text: str) -> TravelPlanningState:
        state["status"] = state.get("status") or "in_progress"
        completed_steps = list(state.get("completed_steps", []))
        if step not in completed_steps:
            completed_steps.append(step)
        state["completed_steps"] = completed_steps
        state["current_step"] = step

        if step == "transport":
            state.setdefault("transport", self._empty_transport_payload())
            state.setdefault("transport_cost", 0.0)
        elif step == "flight":
            state.setdefault("flight", None)
            state.setdefault("transport_cost", float(state.get("transport_cost") or 0))
        elif step == "accommodation":
            state.setdefault("hotels", [])
            state.setdefault("selected_hotel", None)
            state.setdefault("accommodation_cost", 0.0)
        elif step == "activities":
            state["activities"] = list(state.get("activities") or [])
            state["restaurants"] = list(state.get("restaurants") or [])
            state.setdefault("activities_cost", 0.0)
            state.setdefault("dining_cost", 0.0)
            state["activities_payload_valid"] = True
            state["map_completion_status"] = {
                "activities_ready": bool(state["activities"]),
                "restaurants_ready": bool(state["restaurants"]),
                "fallback_reason": error_text[:200],
            }
        elif step == "budget":
            state["budget"] = self._empty_budget_payload(state)
        elif step == "planning":
            fallback_plan = self._build_fallback_itinerary_json(state, error_text)
            state["budget"] = state.get("budget") or self._empty_budget_payload(state)
            state["itinerary_json"] = fallback_plan
            state["itinerary"] = fallback_plan
            state["plan_ready"] = True
            state["status"] = "success"
        return state

    @retry_with_backoff(config=RetryConfig(max_retries=2, initial_delay=1.0))
    async def _transport_node(self, state: TravelPlanningState) -> TravelPlanningState:
        try:
            state["current_step"] = "transport"
            await self._emit_progress(
                "progress",
                {
                    "step": "transport",
                    "message": "Đang tính phương án di chuyển.",
                    "completed_steps": state.get("completed_steps", []),
                },
            )
            result = await self.transport_agent.execute(state)
            result["completed_steps"] = result.get("completed_steps", []) + ["transport"]
            await self._emit_progress(
                "progress",
                {
                    "step": "transport",
                    "message": "Đã hoàn tất bước di chuyển.",
                    "completed_steps": result.get("completed_steps", []),
                },
            )
            return result
        except Exception as exc:
            error_type = classify_error(exc)
            logger.error("Transport node error (%s): %s", error_type.value, exc, exc_info=True)
            state["transport_error"] = str(exc)
            state = self._apply_node_fallback(state, step="transport", error_text=str(exc))
            await self._emit_node_error(
                state,
                step="transport",
                message="Buoc di chuyen gap loi, he thong dang dung du lieu fallback an toan.",
            )
            return state

    @retry_with_backoff(config=RetryConfig(max_retries=2, initial_delay=1.0))
    async def _flight_node(self, state: TravelPlanningState) -> TravelPlanningState:
        try:
            state["current_step"] = "flight"
            state["departure_date"] = state.get("start_date")
            await self._emit_progress(
                "progress",
                {
                    "step": "flight",
                    "message": "Đang kiểm tra chặng bay phù hợp.",
                    "completed_steps": state.get("completed_steps", []),
                },
            )
            result = await self.flight_agent.execute(state)
            if result.get("flight"):
                result["transport_cost"] = result["flight"].get("price_vnd", 0)
            else:
                result["transport_cost"] = result.get("transport", {}).get("estimated_cost_vnd", 0)
            result["completed_steps"] = result.get("completed_steps", []) + ["flight"]
            await self._emit_progress(
                "progress",
                {
                    "step": "flight",
                    "message": "Đã hoàn tất bước chuyến bay.",
                    "completed_steps": result.get("completed_steps", []),
                },
            )
            return result
        except Exception as exc:
            error_type = classify_error(exc)
            logger.error("Flight node error (%s): %s", error_type.value, exc, exc_info=True)
            state["flight_error"] = str(exc)
            state = self._apply_node_fallback(state, step="flight", error_text=str(exc))
            await self._emit_node_error(
                state,
                step="flight",
                message="Khong lay duoc du lieu chuyen bay, he thong se tiep tuc voi phuong an du phong.",
            )
            return state

    @retry_with_backoff(config=RetryConfig(max_retries=2, initial_delay=1.0))
    async def _accommodation_node(self, state: TravelPlanningState) -> TravelPlanningState:
        try:
            state["current_step"] = "accommodation"
            await self._emit_progress(
                "progress",
                {
                    "step": "accommodation",
                    "message": "Đang tìm nơi lưu trú phù hợp.",
                    "completed_steps": state.get("completed_steps", []),
                },
            )
            state["check_in"] = state.get("start_date")
            if state.get("start_date") and state.get("days"):
                from datetime import datetime, timedelta

                start = datetime.strptime(state["start_date"], "%Y-%m-%d")
                nights = max(1, int(state["days"]) - 1)
                state["nights"] = nights
                end = start + timedelta(days=nights)
                state["check_out"] = end.strftime("%Y-%m-%d")

            result = await self.accommodation_agent.execute(state)
            if result.get("selected_hotel") and result.get("check_in") and result.get("check_out"):
                from datetime import datetime
                from tools.accommodation_tools import get_accommodation_tools

                start = datetime.strptime(result["check_in"], "%Y-%m-%d")
                end = datetime.strptime(result["check_out"], "%Y-%m-%d")
                nights = max(1, (end - start).days)
                acc_tools = get_accommodation_tools()
                result["accommodation_cost"] = acc_tools.calculate_total_accommodation_cost(
                    price_per_night=result["selected_hotel"].get("price_per_night", 0),
                    nights=nights,
                    rooms=result.get("rooms", 1),
                )
            elif result.get("hotels"):
                from tools.accommodation_tools import get_accommodation_tools

                hotel = result["hotels"][0]
                acc_tools = get_accommodation_tools()
                result["accommodation_cost"] = acc_tools.calculate_total_accommodation_cost(
                    price_per_night=hotel.get("price_per_night", 0),
                    nights=result.get("nights", max(1, int(result["days"]) - 1)),
                    rooms=result.get("rooms", 1),
                )

            result["completed_steps"] = result.get("completed_steps", []) + ["accommodation"]
            await self._emit_progress(
                "progress",
                {
                    "step": "accommodation",
                    "message": "Đã hoàn tất bước lưu trú.",
                    "completed_steps": result.get("completed_steps", []),
                },
            )
            return result
        except Exception as exc:
            error_type = classify_error(exc)
            logger.error("Accommodation node error (%s): %s", error_type.value, exc, exc_info=True)
            state["accommodation_error"] = str(exc)
            state = self._apply_node_fallback(state, step="accommodation", error_text=str(exc))
            await self._emit_node_error(
                state,
                step="accommodation",
                message="Khong lay duoc luu tru, he thong se tiep tuc voi danh sach rong co kiem soat.",
            )
            return state

    @retry_with_backoff(config=RetryConfig(max_retries=2, initial_delay=1.0))
    async def _activities_node(self, state: TravelPlanningState) -> TravelPlanningState:
        try:
            state["current_step"] = "activities"
            await self._emit_progress(
                "progress",
                {
                    "step": "activities",
                    "message": "Đang gom hoạt động và gợi ý ăn uống.",
                    "completed_steps": state.get("completed_steps", []),
                },
            )
            result = await self.activities_agent.execute(state)
            result["activities"] = list(result.get("activities") or [])
            result["restaurants"] = list(result.get("restaurants") or [])
            result["activities_cost"] = result.get("activities_cost", 0)
            result["dining_cost"] = result.get("dining_cost", 0)
            result["activities_payload_valid"] = isinstance(result.get("activities"), list) and isinstance(result.get("restaurants"), list)
            result["map_completion_status"] = {
                "activities_ready": len(result.get("activities", [])),
                "restaurants_ready": len(result.get("restaurants", [])),
            }
            result["completed_steps"] = result.get("completed_steps", []) + ["activities"]
            await self._emit_progress(
                "progress",
                {
                    "step": "activities",
                    "message": "Đã hoàn tất bước hoạt động và ẩm thực.",
                    "completed_steps": result.get("completed_steps", []),
                },
            )
            return result
        except Exception as exc:
            error_type = classify_error(exc)
            logger.error("Activities node error (%s): %s", error_type.value, exc, exc_info=True)
            state["activities_error"] = str(exc)
            state = self._apply_node_fallback(state, step="activities", error_text=str(exc))
            await self._emit_node_error(
                state,
                step="activities",
                message="Khong lay duoc hoat dong goi y, he thong se tiep tuc voi state fallback hop le.",
            )
            return state

    async def _budget_node(self, state: TravelPlanningState) -> TravelPlanningState:
        try:
            state["current_step"] = "budget"
            await self._emit_progress(
                "progress",
                {
                    "step": "budget",
                    "message": "Đang cân đối ngân sách toàn hành trình.",
                    "completed_steps": state.get("completed_steps", []),
                },
            )
            result = await self.budget_agent.execute(state)
            result["completed_steps"] = result.get("completed_steps", []) + ["budget"]
            await self._emit_progress(
                "progress",
                {
                    "step": "budget",
                    "message": "Đã hoàn tất bước ngân sách.",
                    "completed_steps": result.get("completed_steps", []),
                },
            )
            return result
        except Exception as exc:
            error_type = classify_error(exc)
            logger.error("Budget node error (%s): %s", error_type.value, exc, exc_info=True)
            state["budget_error"] = str(exc)
            state = self._apply_node_fallback(state, step="budget", error_text=str(exc))
            await self._emit_node_error(
                state,
                step="budget",
                message="Khong tong hop duoc ngan sach day du, he thong se su dung khung fallback.",
            )
            return state

    async def _planning_node(self, state: TravelPlanningState) -> TravelPlanningState:
        try:
            state["current_step"] = "planning"
            await self._emit_progress(
                "progress",
                {
                    "step": "planning",
                    "message": "Đang dựng lịch trình chi tiết theo từng ngày.",
                    "completed_steps": state.get("completed_steps", []),
                },
            )
            result = await self.planning_agent.execute(state)
            result["status"] = "success"
            result["plan_ready"] = True
            result["completed_steps"] = result.get("completed_steps", []) + ["planning"]
            await self._emit_progress(
                "progress",
                {
                    "step": "planning",
                    "message": "Đã hoàn tất bước dựng lịch trình.",
                    "completed_steps": result.get("completed_steps", []),
                },
            )
            itinerary_json = result.get("itinerary_json")
            if isinstance(itinerary_json, dict):
                for day_item in itinerary_json.get("daily_itinerary", []) or []:
                    await self._emit_progress(
                        "day_ready",
                        {
                            "step": "planning",
                            "message": "Đã sẵn sàng một ngày lịch trình.",
                            "day": day_item.get("day"),
                            "date": day_item.get("date"),
                            "theme": day_item.get("theme"),
                            "timeline": day_item.get("timeline", []),
                            "completed_steps": result.get("completed_steps", []),
                        },
                    )
            return result
        except Exception as exc:
            error_type = classify_error(exc)
            logger.error("Planning node error (%s): %s", error_type.value, exc, exc_info=True)
            state["planning_error"] = str(exc)
            state = self._apply_node_fallback(state, step="planning", error_text=str(exc))
            await self._emit_node_error(
                state,
                step="planning",
                message="Khong dung duoc planning chinh, he thong da tra ve lich trinh fallback an toan.",
            )
            return state

    async def run(
        self,
        initial_state: Dict[str, Any],
        config: Optional[Dict] = None,
        progress_callback=None,
    ) -> TravelPlanningState:
        if not self.app:
            raise ValueError("Workflow not available (graph build failed)")

        self.progress_callback = progress_callback
        try:
            state: TravelPlanningState = {
                "status": "in_progress",
                "completed_steps": [],
                "llm_token_usage": {"total": 0},
                "server_flags": {
                    "checkpointer": self.checkpointer.__class__.__name__ if self.checkpointer else "unavailable",
                    "langgraph_enabled": True,
                },
                **initial_state,
            }
            if config is None:
                import uuid

                config = {"configurable": {"thread_id": str(uuid.uuid4())}}

            final_state = await self.app.ainvoke(state, config)
            return final_state
        except Exception as exc:
            error_type = classify_error(exc)
            logger.error("Workflow failed (%s): %s", error_type.value, exc, exc_info=True)
            final_state = state.copy()
            final_state["status"] = "error"
            final_state["error"] = str(exc)
            final_state["error_type"] = error_type.value
            return final_state
        finally:
            self.progress_callback = None


async def run_travel_workflow(
    origin: str,
    destination: str,
    start_date: str,
    days: int,
    travelers: int = 2,
    travel_style: str = "standard",
    **kwargs,
) -> TravelPlanningState:
    workflow = LangGraphTravelWorkflow()
    initial_state = {
        "origin": origin,
        "destination": destination,
        "start_date": start_date,
        "days": days,
        "travelers": travelers,
        "travel_style": travel_style,
        **kwargs,
    }
    return await workflow.run(initial_state)
