"""
State definition for Travel Planning LangGraph workflow.
"""
from typing import TypedDict, List, Dict, Any, Optional

from pydantic import BaseModel, Field


class TravelPlanningState(TypedDict, total=False):
    """
    Shared state for the travel planning workflow with 7 agents.

    State duoc truyen giua cac agents trong LangGraph workflow.
    """
    # ========== USER INPUT ==========
    origin: Optional[str]
    destination: Optional[str]
    start_date: Optional[str]
    days: Optional[int]
    travelers: Optional[int]
    travel_style: Optional[str]
    rooms: Optional[int]
    interests: Optional[List[str]]
    max_budget: Optional[float]

    # ========== TRANSPORT AGENT OUTPUT ==========
    transport: Optional[Dict[str, Any]]
    transport_cost: Optional[float]

    # ========== FLIGHT AGENT OUTPUT ==========
    flight: Optional[Dict[str, Any]]
    departure_date: Optional[str]
    return_date: Optional[str]

    # ========== ACCOMMODATION AGENT OUTPUT ==========
    hotels: Optional[List[Dict[str, Any]]]
    selected_hotel: Optional[Dict[str, Any]]
    accommodation_cost: Optional[float]
    check_in: Optional[str]
    check_out: Optional[str]
    nights: Optional[int]

    # ========== ACTIVITIES AGENT OUTPUT ==========
    activities: Optional[List[Dict[str, Any]]]
    restaurants: Optional[List[Dict[str, Any]]]
    activities_cost: Optional[float]
    dining_cost: Optional[float]
    dining_breakdown: Optional[Dict[str, Any]]

    # ========== BUDGET AGENT OUTPUT ==========
    budget: Optional[Dict[str, Any]]
    budget_allocation: Optional[Dict[str, Any]]

    # ========== PLANNING AGENT OUTPUT ==========
    itinerary: Optional[Dict[str, Any]]
    itinerary_json: Optional[Dict[str, Any]]

    # ========== WORKFLOW METADATA ==========
    status: Optional[str]
    error: Optional[str]
    plan_ready: Optional[bool]
    current_step: Optional[str]
    completed_steps: Optional[List[str]]
    error_type: Optional[str]
    thread_id: Optional[str]
    analytics_request_id: Optional[int]
    workflow_started_at: Optional[str]
    workflow_duration_ms: Optional[int]
    llm_token_usage: Optional[Dict[str, int]]
    server_flags: Optional[Dict[str, Any]]
    map_completion_status: Optional[Dict[str, Any]]
    activities_payload_valid: Optional[bool]

    # ========== ERRORS ==========
    transport_error: Optional[str]
    flight_error: Optional[str]
    accommodation_error: Optional[str]
    activities_error: Optional[str]
    budget_error: Optional[str]
    planning_error: Optional[str]


class StrictBaseModel(BaseModel):
    """Base model dung de ep output schema nghiem ngat cho LLM."""

    model_config = {
        "extra": "forbid",
        "populate_by_name": True,
    }


class TransportToNext(StrictBaseModel):
    mode: str = Field(
        description="Phuong tien di chuyen chang ke tiep: Xe may / Taxi / Di bo"
    )
    duration_mins: int = Field(
        description="Thoi gian di chuyen uoc tinh bang phut"
    )
    distance_km: float = Field(
        description="Khoang cach chang chot bang km"
    )


class PlanBFallback(StrictBaseModel):
    place_id: Optional[str] = Field(
        default=None,
        description="Ma dia diem trong nha thay the"
    )
    name: str = Field(
        description="Ten dia diem indoor du phong"
    )
    reason: str = Field(
        description="Ly do kich hoat phuong an du phong"
    )


class TimelineItem(StrictBaseModel):
    time_start: str = Field(
        description="Gio bat dau HH:MM"
    )
    time_end: str = Field(
        description="Gio ket thuc HH:MM"
    )
    place_id: str = Field(
        description="Ma dia diem maDiaDiem tu DB"
    )
    activity_name: str = Field(
        description="Ten hoat dong hoac ten dia diem"
    )
    cost: int = Field(
        description="Chi phi tai diem uoc tinh"
    )
    transport_to_next: TransportToNext = Field(
        description="Thong tin di chuyen toi diem tiep theo"
    )
    local_hint: str = Field(
        description="Meo ban dia, luu y trang phuc, cach tranh chat chem"
    )
    plan_b_fallback: PlanBFallback = Field(
        description="Phuong an du phong neu thoi tiet xau hoac dieu kien khong phu hop"
    )


class DailyItinerary(StrictBaseModel):
    day: int = Field(
        description="So thu tu ngay"
    )
    date: str = Field(
        description="Ngay hien thi YYYY-MM-DD"
    )
    theme: str = Field(
        description="Chu de hoac diem nhan cua ngay hom do"
    )
    route_flow: List[str] = Field(
        description="Mang chua cac maDiaDiem theo thu tu di chuyen toi uu"
    )
    timeline: List[TimelineItem] = Field(
        description="Danh sach cac moc thoi gian va hoat dong trong ngay"
    )


class TripOverview(StrictBaseModel):
    total_distance_km: float = Field(
        description="Tong quang duong di chuyen noi do uoc tinh"
    )
    total_estimated_cost: int = Field(
        description="Tong chi phi AI tinh toan thuc te"
    )
    fitness_level_required: str = Field(
        description="Muc do van dong: Thap / Trung binh / Cao"
    )


class BudgetAnalytics(StrictBaseModel):
    accommodation_total: int = Field(
        description="Tong tien phong khach san thuc te"
    )
    transportation_total: int = Field(
        description="Tong tien ve may bay, xe khach va di chuyen noi do"
    )
    food_total: int = Field(
        description="Tong tien an uong uoc tinh theo so ngay va so nguoi"
    )
    activities_total: int = Field(
        description="Tong tien ve vao cong, tham quan"
    )
    emergency_buffer: int = Field(
        description="Quy du phong phat sinh tu dong trich lap 10-15 phan tram"
    )


class PackingChecklist(StrictBaseModel):
    documents: List[str] = Field(
        description="Cac loai giay to can thiet ca nhan hoa theo cung duong"
    )
    clothing: List[str] = Field(
        description="Goi y trang phuc theo thoi tiet va dia hinh"
    )
    medical: List[str] = Field(
        description="Thuoc men, vat dung bao ve suc khoe dac thu cua vung mien"
    )


class FullTravelPlanOutput(StrictBaseModel):
    trip_overview: TripOverview = Field(
        description="Tong quan chuyen di va muc do van dong"
    )
    daily_itinerary: List[DailyItinerary] = Field(
        description="Lich trinh chi tiet theo tung ngay"
    )
    budget_analytics: BudgetAnalytics = Field(
        description="Phan tich tong hop ngan sach cua chuyen di"
    )
    packing_checklist: PackingChecklist = Field(
        description="Checklist chuan bi do dung duoc ca nhan hoa theo hanh trinh"
    )
