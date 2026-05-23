"""
Planning Agent - Agent lap ke hoach.

Chiu trach nhiem:
- Tao lich trinh hang ngay chi tiet.
- Dong goi ket qua cuoi cung theo structured output nghiem ngat.
- Su dung LLM voi Pydantic schema neu kha dung.
"""
import json
import logging
import math
import re
import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from pydantic import ValidationError

from ..base_agent import BaseAgent
from ..state import FullTravelPlanOutput
from tools.planning_tools import (
    get_llm,
    get_llm_candidates,
    get_planning_tools,
    invoke_candidate_structured,
)
from utils.itinerary_formatter import generate_itinerary_description
from utils.location_resolver import normalize_location_text
from utils.semantic_place_classifier import understand_place_semantics

logger = logging.getLogger(__name__)


class PlanningAgent(BaseAgent):
    """Agent xu ly lap ke hoach va dong goi output cuoi cung."""

    def __init__(self):
        super().__init__(
            agent_name="planning_agent",
            description="Creates detailed daily itineraries with strict structured output",
        )
        self.planning_tools = get_planning_tools()

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Tao lich trinh day du va ep output theo FullTravelPlanOutput.

        Args:
            state: State dictionary chua thong tin tong hop tu cac agent truoc.

        Returns:
            Updated state voi:
                - itinerary: raw itinerary tu planning tools
                - itinerary_json: dict tuan thu FullTravelPlanOutput
                - itinerary_description: mo ta tong quan neu tao duoc
        """
        self.log_input(state)

        try:
            start_date = state.get("start_date")
            days = state.get("days", 1)
            destination = state.get("destination")
            hotels = state.get("hotels", [])
            restaurants = state.get("restaurants", [])
            activities = state.get("activities", [])

            if not start_date or not destination:
                state["planning_error"] = "Missing start_date or destination"
                return state

            if days < 1:
                state["planning_error"] = "Days must be at least 1"
                return state

            if days > 30:
                state["planning_error"] = "Days cannot exceed 30"
                return state

            try:
                datetime.strptime(start_date, "%Y-%m-%d")
            except ValueError:
                state["planning_error"] = (
                    f"Invalid date format: {start_date}. Expected YYYY-MM-DD"
                )
                return state

            travel_style = self._normalize_travel_style(state.get("travel_style", "standard"))
            selected_hotel = state.get("selected_hotel")

            enhanced_activities = self._enhance_activities(activities)

            itinerary = self.planning_tools.create_full_itinerary(
                start_date=start_date,
                days=days,
                destination=destination,
                hotels=hotels,
                restaurants=restaurants,
                activities=enhanced_activities,
                travel_style=travel_style,
                selected_hotel=selected_hotel,
            )
            state["itinerary"] = itinerary

            try:
                plan_output = await self._build_structured_output(state=state, itinerary=itinerary)
                itinerary_json = self._model_dump(plan_output)
                state["itinerary_json"] = itinerary_json

                # Tao mo ta tu output da duoc validate de tranh lech schema.
                description = generate_itinerary_description(
                    itinerary_json,
                    llm=get_llm(),
                    force_llm=True,
                )
                state["itinerary_description"] = description
            except ValidationError as exc:
                self.log_error(exc, context={"stage": "planning_output_validation", "state": state})
                state["planning_error"] = f"Structured output validation failed: {exc}"
                state["itinerary_description"] = None
                return state
            except Exception as exc:
                self.log_error(exc, context={"stage": "planning_output_generation", "state": state})
                state["planning_error"] = f"Failed to generate structured itinerary output: {exc}"
                state["itinerary_description"] = None
                return state

            self.log_output(state)
            return state

        except Exception as exc:
            self.log_error(exc, context={"state": state})
            state["planning_error"] = str(exc)
            return state

    def _normalize_travel_style(self, travel_style: Any) -> Any:
        """Ho tro travel_style dang string, list hoac JSON string."""
        if isinstance(travel_style, str):
            try:
                parsed = json.loads(travel_style)
                return parsed
            except (json.JSONDecodeError, ValueError):
                return travel_style
        return travel_style

    def _enhance_activities(self, activities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Bo sung semantic features cho activities neu du lieu nguon chua co."""
        enhanced_activities: List[Dict[str, Any]] = []

        for activity in activities:
            if not isinstance(activity, dict):
                continue

            enhanced_activity = dict(activity)

            if "semantic_features" not in enhanced_activity:
                semantics = understand_place_semantics(
                    name=enhanced_activity.get("name", ""),
                    description=enhanced_activity.get("description", ""),
                    type_hint=enhanced_activity.get("type", ""),
                    category=enhanced_activity.get("category", ""),
                )
                enhanced_activity["semantic_features"] = semantics["features"]
                enhanced_activity["semantic_confidence"] = semantics["confidence"]

                if "duration_hours" not in enhanced_activity:
                    enhanced_activity["duration_hours"] = semantics["features"].get(
                        "duration_hours", 2.0
                    )
                if "best_time" not in enhanced_activity:
                    enhanced_activity["best_time"] = semantics["features"].get(
                        "best_time", ["anytime"]
                    )

            enhanced_activities.append(enhanced_activity)

        return enhanced_activities

    async def _build_structured_output(
        self,
        state: Dict[str, Any],
        itinerary: Dict[str, Any],
    ) -> FullTravelPlanOutput:
        """
        Tao structured output bang structured LLM that.
        """
        prompt = self._build_structured_prompt(state=state, itinerary=itinerary)
        candidates = get_llm_candidates()
        if not candidates:
            raise RuntimeError("Planning LLM is not configured. Check API key and PLANNING_USE_LLM.")

        errors: List[str] = []
        for candidate in candidates:
            candidate_name = candidate.get("name", "unknown")
            try:
                logger.info("Trying structured planning output with provider: %s", candidate_name)
                if candidate.get("type") == "langchain":
                    client = candidate.get("client")
                    if client is None or not hasattr(client, "with_structured_output"):
                        raise RuntimeError(
                            f"Provider '{candidate_name}' does not support structured output"
                        )
                    structured_llm = client.with_structured_output(FullTravelPlanOutput)
                    if hasattr(structured_llm, "ainvoke"):
                        result = await structured_llm.ainvoke(prompt)
                    else:
                        result = structured_llm.invoke(prompt)
                    validated = (
                        result
                        if isinstance(result, FullTravelPlanOutput)
                        else FullTravelPlanOutput.model_validate(result)
                    )
                else:
                    validated = await asyncio.to_thread(
                        invoke_candidate_structured,
                        candidate,
                        prompt,
                        FullTravelPlanOutput,
                    )

                logger.info("Structured planning output succeeded with provider: %s", candidate_name)
                return self._post_process_structured_output(validated, state)
            except Exception as exc:
                logger.warning("Structured planning output failed with provider %s: %s", candidate_name, exc)
                errors.append(f"{candidate_name}: {exc}")

        raise RuntimeError(
            "All planning LLM providers failed: " + " | ".join(errors)
        )

    def _build_structured_prompt(self, state: Dict[str, Any], itinerary: Dict[str, Any]) -> str:
        """Tao prompt gon nhung du du lieu de LLM dong goi ket qua theo schema."""
        draft_payload = self._build_fallback_structured_payload(state=state, itinerary=itinerary)
        context = {
            "trip_request": {
                "origin": state.get("origin"),
                "destination": state.get("destination"),
                "start_date": state.get("start_date"),
                "days": state.get("days"),
                "travelers": state.get("travelers"),
                "travel_style": state.get("travel_style"),
                "max_budget": state.get("max_budget"),
                "interests": state.get("interests"),
            },
            "transport": self._compact_transport_context(state.get("transport")),
            "transport_cost": state.get("transport_cost"),
            "flight": state.get("flight"),
            "hotels": self._compact_places(state.get("hotels"), limit=4),
            "selected_hotel": self._compact_place(state.get("selected_hotel")),
            "accommodation_cost": state.get("accommodation_cost"),
            "activities": self._compact_places(state.get("activities"), limit=6),
            "restaurants": self._compact_places(state.get("restaurants"), limit=4),
            "activities_cost": state.get("activities_cost"),
            "dining_cost": state.get("dining_cost"),
            "budget": state.get("budget"),
            "budget_allocation": state.get("budget_allocation"),
            "itinerary": self._compact_itinerary(itinerary),
            "draft_payload": draft_payload,
        }

        prompt = (
            "Ban la Planning Agent cua he thong Vi Vu.\n"
            "Hay dong goi du lieu du lich thanh mot object tuan thu chinh xac schema Pydantic "
            "FullTravelPlanOutput.\n"
            "Bat buoc:\n"
            "- Chi su dung thong tin duoc cung cap ben duoi lam can cu.\n"
            "- Khong bo sot field nao trong schema va khong them field la.\n"
            "- Neu thieu du lieu, suy luan tu thong tin da co trong state, khong duoc che tao dia diem moi.\n"
            "- Khong tra ve text giai thich ngoai schema.\n"
            "- HAY XEM draft_payload ben duoi la khung hop le can giu nguyen. Bao toan so ngay, so timeline item, place_id, route_flow, khung gio, cost, transport_to_next va cau truc object y nguyen.\n"
            "- Chi duoc lam giau noi dung cho theme, local_hint, plan_b_fallback.reason, packing_checklist va cac chuoi mo ta can thiet. Khong duoc them item 'thuc day', 'chuan bi', hoac bat ky timeline item moi ngoai draft_payload.\n"
            "- route_flow phai theo thu tu di chuyen toi uu trong ngay.\n"
            "- Chi duoc dung place_id da ton tai trong hotells, restaurants, activities hoac itinerary raw.\n"
            "- Tuyet doi khong dua dia diem o tinh thanh khac voi destination.\n"
            "- local_hint phai ca nhan hoa theo tung dia diem, phai bam sat mo ta, dia chi, khung gio, category, tags hoac dac tinh co san cua chinh dia diem do.\n"
            "- Khong duoc viet local_hint theo mot khuon mau lap lai chung chung. Moi local_hint phai co chi tiet rieng cua dia diem dang xet.\n"
            "- plan_b_fallback phai la phuong an du phong thuc te, uu tien indoor hoac che mua che nang gan khu vuc cua dia diem dang xet, va ly do phai noi ro no giai quyet rui ro gi cua dia diem goc.\n"
            "- transport_to_next phai logic theo distance_km. Neu mode la Di bo/Walking thi duration_mins phai tuong ung toc do 4-5 km/h.\n"
            "- Neu khong co can cu de di bo thi uu tien Taxi/Grab thay vi gan nhan walking sai thuc te.\n\n"
            "Du lieu tong hop:\n"
            f"{json.dumps(context, ensure_ascii=False, default=str, indent=2)}"
        )
        return prompt

    def _compact_transport_context(self, transport: Any) -> Any:
        if not isinstance(transport, dict):
            return transport
        keep_keys = [
            "origin",
            "destination",
            "distance_km",
            "duration_minutes",
            "suggested_method",
            "estimated_cost_vnd",
        ]
        return {key: transport.get(key) for key in keep_keys if key in transport}

    def _compact_places(self, places: Any, limit: int = 5) -> List[Dict[str, Any]]:
        compacted: List[Dict[str, Any]] = []
        for place in (places or [])[:limit]:
            compacted.append(self._compact_place(place))
        return compacted

    def _compact_place(self, place: Any) -> Dict[str, Any]:
        if not isinstance(place, dict):
            return {}
        compact = {
            "maDiaDiem": place.get("maDiaDiem") or place.get("place_id") or place.get("id"),
            "name": place.get("name") or place.get("tenDiaDiem"),
            "category": place.get("category") or place.get("type"),
            "address": place.get("address") or place.get("diaChi"),
            "price": place.get("price_per_night", place.get("price")),
            "rating": place.get("rating"),
            "description": self._truncate_sentence(
                place.get("description") or place.get("moTa") or "",
                max_words=18,
            ),
        }
        if place.get("latitude") is not None and place.get("longitude") is not None:
            compact["coords"] = [place.get("latitude"), place.get("longitude")]
        return {key: value for key, value in compact.items() if value not in (None, "", [], {})}

    def _compact_itinerary(self, itinerary: Any) -> Dict[str, Any]:
        if not isinstance(itinerary, dict):
            return {}
        compact_days: List[Dict[str, Any]] = []
        for day in (itinerary.get("itinerary") or [])[:7]:
            compact_timeline: List[Dict[str, Any]] = []
            for item in (day.get("timeline") or [])[:6]:
                source_place = self._extract_source_place(item) if isinstance(item, dict) else {}
                compact_timeline.append(
                    {
                        "time": item.get("time"),
                        "type": item.get("type"),
                        "label": item.get("label"),
                        "travel_time_minutes": item.get("travel_time_minutes"),
                        "activity_name": (
                            source_place.get("name")
                            or item.get("activity")
                            or item.get("label")
                        ),
                        "place": self._compact_place(source_place),
                    }
                )
            compact_days.append(
                {
                    "day": day.get("day"),
                    "date": day.get("date"),
                    "summary": day.get("summary") or day.get("theme"),
                    "timeline": compact_timeline,
                }
            )
        return {"itinerary": compact_days}

    def _post_process_structured_output(
        self,
        plan_output: FullTravelPlanOutput,
        state: Dict[str, Any],
    ) -> FullTravelPlanOutput:
        """Chuan hoa cac rang buoc logic sau khi LLM tra ket qua."""
        source_index = self._build_source_place_index(state)
        payload = self._model_dump(plan_output)

        for day in payload.get("daily_itinerary", []):
            for item in day.get("timeline", []):
                place_id = str(item.get("place_id", "") or "")
                source_place = source_index.get(place_id, {})

                item["transport_to_next"] = self._normalize_transport_to_next(
                    item.get("transport_to_next") or {}
                )
                item["local_hint"] = self._ensure_specific_local_hint(
                    item.get("local_hint", ""),
                    source_place,
                    state,
                )
                item["plan_b_fallback"] = self._ensure_specific_plan_b(
                    item.get("plan_b_fallback") or {},
                    source_place,
                    state,
                )

        return FullTravelPlanOutput.model_validate(payload)

    def _build_source_place_index(self, state: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Lap index place_id -> source place de enrich hint/fallback grounded."""
        indexed: Dict[str, Dict[str, Any]] = {}

        def register(place: Dict[str, Any]) -> None:
            if not isinstance(place, dict):
                return
            for key in ("maDiaDiem", "place_id", "id", "ma_dia_diem"):
                value = place.get(key)
                if value not in (None, ""):
                    indexed[str(value)] = place

        for group_key in ("activities", "restaurants", "hotels"):
            for place in state.get(group_key, []) or []:
                register(place)

        selected_hotel = state.get("selected_hotel")
        if isinstance(selected_hotel, dict):
            register(selected_hotel)

        return indexed

    def _normalize_transport_to_next(self, transport: Dict[str, Any]) -> Dict[str, Any]:
        """Siết logic thời gian di bo ve dung 4-5 km/h."""
        normalized = {
            "mode": str(transport.get("mode") or "Taxi"),
            "duration_mins": self._to_int(transport.get("duration_mins"), default=15),
            "distance_km": self._to_float(transport.get("distance_km"), default=0.0),
        }

        mode_normalized = normalize_location_text(normalized["mode"])
        distance_km = max(normalized["distance_km"], 0.0)
        is_walking = mode_normalized in {"di bo", "walking", "walk", "foot"}

        if is_walking and distance_km > 0:
            min_duration = math.ceil((distance_km / 5.0) * 60)
            max_duration = math.ceil((distance_km / 4.0) * 60)
            expected_duration = max(1, round((distance_km / 4.5) * 60))

            if normalized["duration_mins"] < min_duration or normalized["duration_mins"] > max_duration:
                normalized["duration_mins"] = expected_duration
                normalized["mode"] = "Di bo"

        return normalized

    def _ensure_specific_local_hint(
        self,
        local_hint: str,
        source_place: Dict[str, Any],
        state: Dict[str, Any],
    ) -> str:
        """Buoc local_hint bam sat dac tinh that cua dia diem."""
        if self._looks_specific_enough(local_hint, source_place):
            return str(local_hint).strip()

        place_name = source_place.get("name") or source_place.get("tenDiaDiem") or "dia diem nay"
        address = source_place.get("address") or source_place.get("diaChi") or state.get("destination", "")
        description = self._truncate_sentence(
            source_place.get("description") or source_place.get("moTa") or ""
        )
        category = source_place.get("category") or source_place.get("type") or "tham quan"

        details: List[str] = [f"{place_name} thuoc nhom {category}"]
        if address:
            details.append(f"nam o {address}")
        if description:
            details.append(description)

        return "; ".join(details)

    def _ensure_specific_plan_b(
        self,
        fallback: Dict[str, Any],
        source_place: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Buoc plan B co ly do ca nhan hoa theo dia diem goc."""
        name = str(fallback.get("name") or "").strip()
        reason = str(fallback.get("reason") or "").strip()
        if name and self._looks_specific_enough(reason, source_place):
            return {
                "place_id": None if fallback.get("place_id") in ("", None) else str(fallback.get("place_id")),
                "name": name,
                "reason": reason,
            }

        place_name = source_place.get("name") or source_place.get("tenDiaDiem") or "dia diem goc"
        address = source_place.get("address") or source_place.get("diaChi") or state.get("destination", "")
        category = source_place.get("category") or source_place.get("type") or "ngoai troi"
        normalized_category = normalize_location_text(str(category))
        if any(keyword in normalized_category for keyword in ("bien", "sightseeing", "entertainment", "giai tri", "dia danh")):
            fallback_name = name or f"Quan ca phe hoac bao tang gan {place_name}"
            fallback_reason = (
                f"Neu {place_name} bi anh huong boi mua nang hoac dong khach, chuyen sang diem indoor gan {address} "
                f"de van giu duoc chu de tham quan quanh khu vuc."
            )
        else:
            fallback_name = name or f"Dia diem trong nha gan {place_name}"
            fallback_reason = (
                f"Phuong an du phong giu lich trinh trong cung khu vuc {address} neu {place_name} tam ngung phuc vu "
                f"hoac dieu kien tai cho khong phu hop."
            )

        return {
            "place_id": None if fallback.get("place_id") in ("", None) else str(fallback.get("place_id")),
            "name": fallback_name,
            "reason": fallback_reason,
        }

    def _looks_specific_enough(self, text: str, source_place: Dict[str, Any]) -> bool:
        if not text:
            return False

        normalized_text = normalize_location_text(text)
        if not normalized_text:
            return False

        generic_patterns = [
            "kiem tra thoi tiet truoc khi di chuyen",
            "uu tien di som hon gio cao diem",
            "du phong neu troi mua",
            "diem indoor du phong",
            "quan cafe hoac bao tang gan",
        ]
        if any(pattern in normalized_text for pattern in generic_patterns):
            return False

        source_tokens = self._extract_specific_tokens(source_place)
        if not source_tokens:
            return True
        return any(token in normalized_text for token in source_tokens)

    def _extract_specific_tokens(self, source_place: Dict[str, Any]) -> List[str]:
        values = [
            source_place.get("name"),
            source_place.get("tenDiaDiem"),
            source_place.get("address"),
            source_place.get("diaChi"),
            source_place.get("category"),
            source_place.get("type"),
        ]
        description = source_place.get("description") or source_place.get("moTa") or ""
        values.extend(re.split(r"[,.!;:()\n]+", str(description)))

        tokens: List[str] = []
        for value in values:
            normalized = normalize_location_text(str(value or ""))
            if len(normalized) >= 4:
                tokens.append(normalized)
        return tokens

    def _truncate_sentence(self, text: str, max_words: int = 14) -> str:
        words = str(text or "").split()
        if not words:
            return ""
        shortened = " ".join(words[:max_words]).strip()
        return shortened.rstrip(".,;: ")

    def _build_fallback_structured_payload(
        self,
        state: Dict[str, Any],
        itinerary: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Dong goi schema cuoi cung theo rule-based de giu fail-safe cho monolith."""
        budget_section = self._build_budget_analytics(state)
        daily_itinerary = self._build_daily_itinerary(itinerary, state)
        total_distance_km = self._estimate_total_distance_km(state, daily_itinerary)
        total_estimated_cost = self._estimate_total_cost(state, budget_section)

        payload = {
            "trip_overview": {
                "total_distance_km": total_distance_km,
                "total_estimated_cost": total_estimated_cost,
                "fitness_level_required": self._estimate_fitness_level(state, daily_itinerary),
            },
            "daily_itinerary": daily_itinerary,
            "budget_analytics": budget_section,
            "packing_checklist": self._build_packing_checklist(state),
        }
        return payload

    def _build_budget_analytics(self, state: Dict[str, Any]) -> Dict[str, int]:
        """Tong hop budget theo schema output cuoi."""
        accommodation_total = self._to_int(state.get("accommodation_cost"))

        flight_data = state.get("flight") or {}
        flight_total = self._extract_price(flight_data)
        transportation_total = self._to_int(state.get("transport_cost")) + flight_total

        activities_total = self._to_int(state.get("activities_cost"))
        food_total = self._to_int(state.get("dining_cost"))

        budget = state.get("budget") or {}
        budget_breakdown = budget.get("breakdown") if isinstance(budget, dict) else {}
        if isinstance(budget_breakdown, dict):
            accommodation_total = max(
                accommodation_total,
                self._to_int(budget_breakdown.get("accommodation")),
            )
            transportation_total = max(
                transportation_total,
                self._to_int(budget_breakdown.get("transport")),
            )
            activities_total = max(
                activities_total,
                self._to_int(budget_breakdown.get("activities")),
            )
            food_total = max(
                food_total,
                self._to_int(budget_breakdown.get("dining")),
            )

        subtotal = accommodation_total + transportation_total + food_total + activities_total
        emergency_buffer = max(self._to_int(subtotal * 0.12), 50000 if subtotal > 0 else 0)

        return {
            "accommodation_total": accommodation_total,
            "transportation_total": transportation_total,
            "food_total": food_total,
            "activities_total": activities_total,
            "emergency_buffer": emergency_buffer,
        }

    def _build_daily_itinerary(
        self,
        itinerary: Dict[str, Any],
        state: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Chuyen raw itinerary thanh daily_itinerary theo schema moi."""
        itinerary_days = itinerary.get("itinerary", []) if isinstance(itinerary, dict) else []
        normalized_days: List[Dict[str, Any]] = []

        for day_index, day_plan in enumerate(itinerary_days, start=1):
            if not isinstance(day_plan, dict):
                continue

            timeline_items = self._build_timeline_items(day_plan, day_index, state)
            route_flow = [item["place_id"] for item in timeline_items]
            normalized_days.append(
                {
                    "day": self._to_int(day_plan.get("day"), default=day_index),
                    "date": day_plan.get("date") or self._estimate_date(state, day_index),
                    "theme": day_plan.get("theme") or day_plan.get("summary") or f"Ngay {day_index}",
                    "route_flow": route_flow,
                    "timeline": timeline_items,
                }
            )

        return normalized_days

    def _build_timeline_items(
        self,
        day_plan: Dict[str, Any],
        day_index: int,
        state: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Chuan hoa timeline tung ngay sang schema FullTravelPlanOutput."""
        raw_timeline = day_plan.get("timeline", []) or []
        normalized_items: List[Dict[str, Any]] = []

        filtered_items = [
            item
            for item in raw_timeline
            if isinstance(item, dict) and item.get("type") in {"activity", "meal", "free_time"}
        ]

        if not filtered_items:
            # Fallback neu timeline trong planning tools khong co du lieu phu hop.
            filtered_items = self._build_items_from_activities(day_plan)

        for index, item in enumerate(filtered_items):
            source_place = self._extract_source_place(item)
            place_id = self._extract_place_id(source_place, day_index=day_index, item_index=index + 1)
            next_item = filtered_items[index + 1] if index + 1 < len(filtered_items) else None

            time_start = item.get("time") or item.get("time_start") or self._estimate_time_start(index)
            time_end = self._estimate_time_end(time_start, next_item)

            activity_name = (
                source_place.get("name")
                or item.get("activity")
                or item.get("label")
                or f"Hoat dong {index + 1}"
            )
            cost = self._estimate_item_cost(source_place, item)

            normalized_items.append(
                {
                    "time_start": time_start,
                    "time_end": time_end,
                    "place_id": place_id,
                    "activity_name": activity_name,
                    "cost": cost,
                    "transport_to_next": self._build_transport_to_next(item, source_place),
                    "local_hint": self._build_local_hint(item, source_place, state),
                    "plan_b_fallback": self._build_plan_b_fallback(source_place, item),
                }
            )

        return normalized_items

    def _build_items_from_activities(self, day_plan: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Dung activities phan bo theo ngay neu timeline goc khong du tot de map."""
        items: List[Dict[str, Any]] = []
        for activity_entry in day_plan.get("activities", []) or []:
            if not isinstance(activity_entry, dict):
                continue
            activity_details = activity_entry.get("activity") if isinstance(activity_entry.get("activity"), dict) else activity_entry
            items.append(
                {
                    "type": "activity",
                    "time": activity_entry.get("time") or "09:00",
                    "activity": activity_details.get("name", "Hoat dong"),
                    "activity_details": activity_details,
                    "description": activity_entry.get("description", ""),
                    "travel_time_minutes": activity_entry.get("travel_time_minutes", 15),
                }
            )
        return items

    def _extract_source_place(self, item: Dict[str, Any]) -> Dict[str, Any]:
        """Lay dict dia diem goc tu timeline item."""
        if isinstance(item.get("activity_details"), dict):
            return item["activity_details"]
        if isinstance(item.get("restaurant"), dict):
            return item["restaurant"]
        if isinstance(item.get("activity"), dict):
            return item["activity"]
        return {}

    def _extract_place_id(
        self,
        source_place: Dict[str, Any],
        day_index: int,
        item_index: int,
    ) -> str:
        """Lay ma dia diem uu tien tu DB, neu khong co thi tao id on dinh de khong rong."""
        candidate_fields = [
            "maDiaDiem",
            "place_id",
            "id",
            "ma_dia_diem",
        ]
        for field in candidate_fields:
            value = source_place.get(field)
            if value not in (None, ""):
                return str(value)

        name = str(source_place.get("name", "")).strip()
        if name:
            slug = "_".join(name.lower().split())
            return f"fallback_{slug}"

        return f"day{day_index}_item{item_index}"

    def _estimate_time_start(self, index: int) -> str:
        """Fallback gio bat dau neu timeline goc khong co time."""
        base_hour = 8 + index * 2
        return f"{min(base_hour, 22):02d}:00"

    def _estimate_time_end(self, time_start: str, next_item: Optional[Dict[str, Any]]) -> str:
        """Tinh gio ket thuc dua tren moc tiep theo hoac mac dinh 90 phut."""
        if next_item:
            next_time = next_item.get("time") or next_item.get("time_start")
            if isinstance(next_time, str) and ":" in next_time:
                return next_time

        try:
            start_dt = datetime.strptime(time_start, "%H:%M")
            return (start_dt + timedelta(minutes=90)).strftime("%H:%M")
        except ValueError:
            return "23:00"

    def _build_transport_to_next(
        self,
        item: Dict[str, Any],
        source_place: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Dong goi thong tin di chuyen chang tiep theo."""
        duration_mins = self._to_int(item.get("travel_time_minutes"), default=15)
        distance_km = self._to_float(
            source_place.get("distance_km", item.get("distance_km", 0.0)),
            default=0.0,
        )
        mode = source_place.get("transport_mode") or item.get("transport_mode") or "Taxi"
        return {
            "mode": str(mode),
            "duration_mins": duration_mins,
            "distance_km": distance_km,
        }

    def _build_local_hint(
        self,
        item: Dict[str, Any],
        source_place: Dict[str, Any],
        state: Dict[str, Any],
    ) -> str:
        """Tao local_hint tu description/tips co san, neu khong co thi chen huong dan an toan."""
        existing_hint = (
            source_place.get("local_hint")
            or item.get("local_hint")
            or item.get("description")
        )
        if existing_hint:
            return str(existing_hint)

        destination = state.get("destination", "diem den")
        item_type = item.get("type", "activity")
        if item_type == "meal":
            return (
                f"Tai {destination}, nen hoi gia truoc khi goi mon va uu tien quan dong "
                "nguoi dia phuong de tranh phu thu bat ngo."
            )
        return (
            f"Kiem tra thoi tiet truoc khi di chuyen tai {destination}, di som hon gio cao diem "
            "neu diem nay nam ngoai troi hoac thu hut dong khach."
        )

    def _build_plan_b_fallback(
        self,
        source_place: Dict[str, Any],
        item: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Tao plan B indoor an toan neu du lieu nguon chua tra ve san."""
        fallback = source_place.get("plan_b_fallback")
        if isinstance(fallback, dict):
            return {
                "place_id": None if fallback.get("place_id") in ("", None) else str(fallback.get("place_id")),
                "name": str(fallback.get("name") or "Diem indoor du phong"),
                "reason": str(
                    fallback.get("reason")
                    or "Du phong neu thoi tiet xau hoac lich trinh ngoai troi khong phu hop."
                ),
            }

        name = source_place.get("name") or item.get("activity") or "khu vuc tham quan"
        return {
            "place_id": None,
            "name": f"Quan cafe hoac bao tang gan {name}",
            "reason": "Du phong neu troi mua lon, qua nang hoac diem ngoai troi tam dong cua.",
        }

    def _estimate_item_cost(self, source_place: Dict[str, Any], item: Dict[str, Any]) -> int:
        """Uoc tinh chi phi tai diem tu cac field gia pho bien."""
        candidate_values = [
            item.get("cost"),
            source_place.get("giaVe"),
            source_place.get("price"),
            source_place.get("estimated_cost"),
            source_place.get("price_avg_vnd"),
        ]
        for value in candidate_values:
            result = self._to_int(value, default=-1)
            if result >= 0:
                return result
        return 0

    def _estimate_total_distance_km(
        self,
        state: Dict[str, Any],
        daily_itinerary: List[Dict[str, Any]],
    ) -> float:
        """Tinh tong quang duong noi do uoc tinh."""
        transport = state.get("transport") or {}
        for key in ("distance_km", "total_distance_km"):
            if transport.get(key) is not None:
                return round(self._to_float(transport.get(key), default=0.0), 2)

        total_distance = 0.0
        for day in daily_itinerary:
            for item in day.get("timeline", []):
                total_distance += self._to_float(
                    item.get("transport_to_next", {}).get("distance_km"),
                    default=0.0,
                )
        return round(total_distance, 2)

    def _estimate_total_cost(
        self,
        state: Dict[str, Any],
        budget_section: Dict[str, int],
    ) -> int:
        """Lay tong chi phi uu tien tu budget agent, fallback sang tong cac nhom."""
        budget = state.get("budget") or {}
        candidate_values = [
            budget.get("total_vnd") if isinstance(budget, dict) else None,
            budget.get("total") if isinstance(budget, dict) else None,
            state.get("total_cost"),
            state.get("max_budget"),
        ]
        for value in candidate_values:
            result = self._to_int(value, default=-1)
            if result >= 0:
                return result

        return sum(budget_section.values())

    def _estimate_fitness_level(
        self,
        state: Dict[str, Any],
        daily_itinerary: List[Dict[str, Any]],
    ) -> str:
        """Uoc tinh muc do van dong tu so moc hoat dong va phong cach."""
        travel_style = str(state.get("travel_style", "standard")).lower()
        total_items = sum(len(day.get("timeline", [])) for day in daily_itinerary)
        days = max(self._to_int(state.get("days"), default=1), 1)
        average_items_per_day = total_items / days if days else total_items

        if "adventure" in travel_style or average_items_per_day >= 5:
            return "Cao"
        if average_items_per_day >= 3:
            return "Trung binh"
        return "Thap"

    def _build_packing_checklist(self, state: Dict[str, Any]) -> Dict[str, List[str]]:
        """Tao packing list fail-safe dua tren diem den, so ngay va phong cach."""
        destination = str(state.get("destination", "")).lower()
        interests = [str(item).lower() for item in (state.get("interests") or [])]

        documents = [
            "CCCD hoac ho chieu con hieu luc",
            "Thong tin dat phong va ma dat dich vu",
            "The thanh toan va mot it tien mat menh gia nho",
        ]
        clothing = [
            "Quan ao thoang nhe phu hop thoi tiet diem den",
            "Giay di bo em chan hoac giay chong truot",
            "Ao khoac mong de dung khi di chuyen som hoac toi",
        ]
        medical = [
            "Thuoc dau bung, ha sot va di ung co ban",
            "Kem chong nang va xit chong con trung",
            "Bang ca nhan va dung dich sat khuan mini",
        ]

        coastal_keywords = ["bien", "dao", "phu quoc", "nha trang", "da nang", "vung tau"]
        mountain_keywords = ["sapa", "ha giang", "tay bac", "cao bang", "da lat", "moc chau"]
        spiritual_keywords = {"religious", "cultural", "temple", "pagoda"}

        if any(keyword in destination for keyword in coastal_keywords):
            clothing.append("Do nhanh kho va mu rong vanh cho lich trinh ven bien")
            medical.append("Goi dien giai va thuoc say song neu co di tau")

        if any(keyword in destination for keyword in mountain_keywords):
            clothing.append("Ao giu am nhe va tat day hon neu di vung cao")
            medical.append("Thuoc chong say xe neu cung duong deo dai")

        if spiritual_keywords.intersection(interests):
            clothing.append("Trang phuc kin dao neu co ghe chua, den hoac diem tam linh")

        return {
            "documents": documents,
            "clothing": clothing,
            "medical": medical,
        }

    def _estimate_date(self, state: Dict[str, Any], day_index: int) -> str:
        """Tinh ngay fallback tu start_date va so thu tu ngay."""
        start_date = state.get("start_date")
        if not start_date:
            return "1970-01-01"
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            return (start_dt + timedelta(days=day_index - 1)).strftime("%Y-%m-%d")
        except ValueError:
            return "1970-01-01"

    def _extract_price(self, data: Dict[str, Any]) -> int:
        """Lay gia tu dict theo mot so ten field thuong gap."""
        if not isinstance(data, dict):
            return 0
        for field in ("price", "total_price", "amount", "price_vnd", "min_price"):
            if data.get(field) is not None:
                return self._to_int(data.get(field))
        return 0

    def _to_float(self, value: Any, default: float = 0.0) -> float:
        """Chuyen doi float an toan."""
        if value is None:
            return default
        try:
            if isinstance(value, str):
                value = value.strip().replace(",", "")
            return float(value)
        except (TypeError, ValueError, AttributeError):
            return default

    def _to_int(self, value: Any, default: int = 0) -> int:
        """Chuyen doi int an toan."""
        if value is None:
            return default
        try:
            if isinstance(value, str):
                value = value.strip().replace(",", "")
            return int(float(value))
        except (TypeError, ValueError, AttributeError):
            return default

    def _model_dump(self, model: FullTravelPlanOutput) -> Dict[str, Any]:
        """Tuong thich giua Pydantic v1 va v2."""
        if hasattr(model, "model_dump"):
            return model.model_dump()
        return model.dict()
