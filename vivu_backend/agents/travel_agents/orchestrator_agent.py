"""
Orchestrator Agent - Agent điều phối
===================================
"""
import inspect
import logging
from typing import Any, Dict, Optional

from ..base_agent import BaseAgent
from .accommodation_agent import AccommodationAgent
from .activities_agent import ActivitiesAgent
from .budget_agent import BudgetAgent
from .flight_agent import FlightAgent
from .planning_agent import PlanningAgent
from .transport_agent import TransportAgent

logger = logging.getLogger(__name__)


class OrchestratorAgent(BaseAgent):
    """Agent điều phối toàn bộ hệ thống."""

    def __init__(self):
        super().__init__(
            agent_name="orchestrator_agent",
            description="Orchestrates all travel planning agents",
        )
        self.transport_agent = TransportAgent()
        self.flight_agent = FlightAgent()
        self.accommodation_agent = AccommodationAgent()
        self.budget_agent = BudgetAgent()
        self.planning_agent = PlanningAgent()
        self.activities_agent = ActivitiesAgent()

    async def _emit_progress(
        self,
        progress_callback,
        *,
        event_type: str,
        step: str,
        message: str,
        state: Optional[Dict[str, Any]] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not progress_callback:
            return

        payload = {
            "step": step,
            "message": message,
            "completed_steps": (state or {}).get("completed_steps", []),
            "status": (state or {}).get("status", "running"),
        }
        if extra:
            payload.update(extra)

        result = progress_callback(event_type, payload)
        if inspect.isawaitable(result):
            await result

    async def execute(self, state: Dict[str, Any], progress_callback=None) -> Dict[str, Any]:
        """Điều phối toàn bộ quy trình lập kế hoạch."""
        self.log_input(state)

        try:
            state.setdefault("completed_steps", [])

            logger.info("Step 1: Transport calculation...")
            await self._emit_progress(
                progress_callback,
                event_type="progress",
                step="transport",
                message="Đang tính phương án di chuyển.",
                state=state,
            )
            state = await self.transport_agent.execute(state)
            state["completed_steps"] = state.get("completed_steps", []) + ["transport"]
            await self._emit_progress(
                progress_callback,
                event_type="progress",
                step="transport",
                message="Đã hoàn tất bước di chuyển.",
                state=state,
            )

            if state.get("transport", {}).get("suggested_method") == "flight":
                logger.info("Step 2: Flight price search with airport transfers...")
                await self._emit_progress(
                    progress_callback,
                    event_type="progress",
                    step="flight",
                    message="Đang kiểm tra chặng bay phù hợp.",
                    state=state,
                )

                from tools.airport_utils import calculate_airport_transport_cost, get_nearest_airport
                from tools.geo_tools import get_geo_tools

                origin = state.get("origin")
                destination = state.get("destination")
                travelers = state.get("travelers", 1)

                origin_airport_info = get_nearest_airport(origin)
                dest_airport_info = get_nearest_airport(destination)

                if not origin_airport_info or not dest_airport_info:
                    logger.warning("Cannot find airports for %s or %s", origin, destination)
                    state["departure_date"] = state.get("start_date")
                    state["passengers"] = travelers
                    state = await self.flight_agent.execute(state)
                    flight_price = state.get("flight", {}).get("price_vnd", 0) if state.get("flight") else 0

                    if flight_price == 0:
                        distance_km = state.get("transport", {}).get("distance_km", 0)
                        if distance_km > 0:
                            estimated_price_per_person = min(max(distance_km * 2000, 1_500_000), 8_000_000)
                            flight_price = estimated_price_per_person * travelers
                        else:
                            flight_price = 3_000_000 * travelers

                    state["transport_cost"] = flight_price
                else:
                    origin_airport_iata = origin_airport_info[0]
                    origin_airport_name = origin_airport_info[1]
                    dest_airport_iata = dest_airport_info[0]
                    dest_airport_name = dest_airport_info[1]

                    geo_tools = get_geo_tools()
                    origin_to_airport_route = geo_tools.calculate_distance_time(
                        origin,
                        f"{origin_airport_name}, {origin_airport_info[2]}",
                    )
                    origin_to_airport_cost = 0
                    method_to_airport = "unknown"
                    if origin_to_airport_route:
                        origin_to_airport_dist = origin_to_airport_route["distance_km"]
                        method_to_airport = "bus" if origin_to_airport_dist > 50 else "taxi"
                        origin_to_airport_info = calculate_airport_transport_cost(
                            origin,
                            origin_airport_name,
                            origin_to_airport_dist,
                            method_to_airport,
                        )
                        origin_to_airport_cost = origin_to_airport_info["cost_vnd"] * travelers

                    state["departure_date"] = state.get("start_date")
                    state["passengers"] = travelers
                    state["origin"] = origin_airport_iata
                    state["destination"] = dest_airport_iata
                    state = await self.flight_agent.execute(state)

                    flight_price = 0
                    if state.get("flight"):
                        flight_price = (
                            state["flight"].get("price_vnd", 0)
                            or state["flight"].get("price", 0)
                            or state["flight"].get("total_price_vnd", 0)
                            or 0
                        )

                    if flight_price == 0:
                        from tools.flight_tools import get_flight_tools

                        flight_tools = get_flight_tools()
                        estimated_flight = flight_tools._estimate_price(
                            origin_airport_iata,
                            dest_airport_iata,
                            "oneway",
                            travelers,
                        )
                        flight_price = estimated_flight.get("price_vnd", 0)

                        if flight_price == 0 or flight_price < (1_500_000 * travelers):
                            if origin_airport_iata in ["SGN", "HAN"] and dest_airport_iata in ["SGN", "HAN"]:
                                flight_price = 2_000_000 * travelers
                            else:
                                flight_price = 1_500_000 * travelers

                    airport_to_dest_route = geo_tools.calculate_distance_time(
                        f"{dest_airport_name}, {dest_airport_info[2]}",
                        destination,
                    )
                    airport_to_dest_cost = 0
                    method_from_airport = "unknown"
                    if airport_to_dest_route:
                        airport_to_dest_dist = airport_to_dest_route["distance_km"]
                        if airport_to_dest_dist < 30:
                            method_from_airport = "taxi"
                            airport_to_dest_info = calculate_airport_transport_cost(
                                dest_airport_name,
                                destination,
                                airport_to_dest_dist,
                                method_from_airport,
                            )
                            airport_to_dest_cost = airport_to_dest_info["cost_vnd"] * travelers
                        elif airport_to_dest_dist < 200:
                            method_from_airport = "bus"
                            airport_to_dest_info = calculate_airport_transport_cost(
                                dest_airport_name,
                                destination,
                                airport_to_dest_dist,
                                method_from_airport,
                            )
                            airport_to_dest_cost = airport_to_dest_info["cost_vnd"] * travelers
                        else:
                            method_from_airport = "bus_long_distance"
                            airport_to_dest_cost = airport_to_dest_dist * 3000 * travelers

                    total_transport_cost = origin_to_airport_cost + flight_price + airport_to_dest_cost
                    state["transport_cost"] = total_transport_cost
                    state["transport_breakdown"] = {
                        "origin_to_airport": {
                            "cost_vnd": origin_to_airport_cost,
                            "method": method_to_airport,
                            "distance_km": origin_to_airport_route["distance_km"] if origin_to_airport_route else 0,
                            "airport": origin_airport_name,
                        },
                        "flight": {
                            "cost_vnd": flight_price,
                            "origin_airport": origin_airport_name,
                            "dest_airport": dest_airport_name,
                        },
                        "airport_to_dest": {
                            "cost_vnd": airport_to_dest_cost,
                            "method": method_from_airport,
                            "distance_km": airport_to_dest_route["distance_km"] if airport_to_dest_route else 0,
                            "airport": dest_airport_name,
                        },
                        "total_vnd": total_transport_cost,
                    }

                    state["origin"] = origin
                    state["destination"] = destination
                    if state.get("transport"):
                        state["transport"]["estimated_cost_vnd"] = total_transport_cost
                        state["transport"]["breakdown"] = state["transport_breakdown"]

                state["completed_steps"] = state.get("completed_steps", []) + ["flight"]
                await self._emit_progress(
                    progress_callback,
                    event_type="progress",
                    step="flight",
                    message="Đã hoàn tất bước chuyến bay.",
                    state=state,
                )
            else:
                transport_cost = state.get("transport_cost", 0)
                if transport_cost == 0:
                    transport_cost = state.get("transport", {}).get("estimated_cost_vnd", 0)

                if transport_cost == 0:
                    distance_km = state.get("transport", {}).get("distance_km", 0)
                    if distance_km > 0:
                        from tools.transport_tools import get_transport_tools

                        transport_tools = get_transport_tools()
                        method = state.get("transport", {}).get("suggested_method", "bus")
                        base_cost = transport_tools._calculate_ground_transport_cost(distance_km, method)
                        travelers = state.get("travelers", 1)
                        transport_cost = base_cost * travelers
                        state["transport"]["estimated_cost_vnd"] = transport_cost

                state["transport_cost"] = transport_cost

            logger.info("Step 3: Hotel search...")
            await self._emit_progress(
                progress_callback,
                event_type="progress",
                step="accommodation",
                message="Đang tìm nơi lưu trú phù hợp.",
                state=state,
            )
            days = state.get("days", 1)
            nights = max(1, days - 1)
            state["check_in"] = state.get("start_date")
            state["nights"] = nights
            if state.get("start_date") and days:
                from datetime import datetime, timedelta

                start = datetime.strptime(state["start_date"], "%Y-%m-%d")
                end = start + timedelta(days=nights)
                state["check_out"] = end.strftime("%Y-%m-%d")
            state = await self.accommodation_agent.execute(state)

            if state.get("selected_hotel") and state.get("check_in") and state.get("check_out"):
                from datetime import datetime
                from tools.accommodation_tools import get_accommodation_tools

                start = datetime.strptime(state["check_in"], "%Y-%m-%d")
                end = datetime.strptime(state["check_out"], "%Y-%m-%d")
                nights = max(1, (end - start).days)
                acc_tools = get_accommodation_tools()
                state["accommodation_cost"] = acc_tools.calculate_total_accommodation_cost(
                    price_per_night=state["selected_hotel"].get("price_per_night", 0),
                    nights=nights,
                    rooms=state.get("rooms", 1),
                )
            elif state.get("hotels"):
                from tools.accommodation_tools import get_accommodation_tools

                hotel = state["hotels"][0]
                nights = state.get("nights", max(1, state.get("days", 1) - 1))
                acc_tools = get_accommodation_tools()
                state["accommodation_cost"] = acc_tools.calculate_total_accommodation_cost(
                    price_per_night=hotel.get("price_per_night", 0),
                    nights=nights,
                    rooms=state.get("rooms", 1),
                )

            state["completed_steps"] = state.get("completed_steps", []) + ["accommodation"]
            await self._emit_progress(
                progress_callback,
                event_type="progress",
                step="accommodation",
                message="Đã hoàn tất bước lưu trú.",
                state=state,
            )

            logger.info("Step 4: Activities and dining...")
            await self._emit_progress(
                progress_callback,
                event_type="progress",
                step="activities",
                message="Đang gom hoạt động và gợi ý ăn uống.",
                state=state,
            )
            state = await self.activities_agent.execute(state)
            state["activities_cost"] = state.get("activities_cost", 0)
            state["dining_cost"] = state.get("dining_cost", 0)
            state["completed_steps"] = state.get("completed_steps", []) + ["activities"]
            await self._emit_progress(
                progress_callback,
                event_type="progress",
                step="activities",
                message="Đã hoàn tất bước hoạt động và ẩm thực.",
                state=state,
            )

            logger.info("Step 5: Budget calculation...")
            await self._emit_progress(
                progress_callback,
                event_type="progress",
                step="budget",
                message="Đang cân đối ngân sách toàn hành trình.",
                state=state,
            )
            state = await self.budget_agent.execute(state)
            state["completed_steps"] = state.get("completed_steps", []) + ["budget"]
            await self._emit_progress(
                progress_callback,
                event_type="progress",
                step="budget",
                message="Đã hoàn tất bước ngân sách.",
                state=state,
            )

            logger.info("Step 6: Itinerary creation...")
            await self._emit_progress(
                progress_callback,
                event_type="progress",
                step="planning",
                message="Đang dựng lịch trình chi tiết theo từng ngày.",
                state=state,
            )
            state["restaurants"] = state.get("restaurants", [])
            state["activities"] = state.get("activities", [])
            state = await self.planning_agent.execute(state)
            state["completed_steps"] = state.get("completed_steps", []) + ["planning"]
            await self._emit_progress(
                progress_callback,
                event_type="progress",
                step="planning",
                message="Đã hoàn tất bước dựng lịch trình.",
                state=state,
            )

            itinerary_json = state.get("itinerary_json")
            if isinstance(itinerary_json, dict):
                for day_item in itinerary_json.get("daily_itinerary", []) or []:
                    await self._emit_progress(
                        progress_callback,
                        event_type="day_ready",
                        step="planning",
                        message="Đã sẵn sàng một ngày lịch trình.",
                        state=state,
                        extra={
                            "day": day_item.get("day"),
                            "date": day_item.get("date"),
                            "theme": day_item.get("theme"),
                            "timeline": day_item.get("timeline", []),
                        },
                    )

            state["status"] = "success"
            state["plan_ready"] = True
            logger.info("Orchestration completed successfully")
            self.log_output(state)
            return state
        except Exception as exc:
            self.log_error(exc, context={"state": state})
            state["status"] = "error"
            state["error"] = str(exc)
            return state
