"""
State definition for Travel Planning LangGraph workflow
=======================================================
State structure cho 7 agents chính trong hệ thống
"""
from typing import TypedDict, List, Dict, Any, Optional
from datetime import date


class TravelPlanningState(TypedDict, total=False):
    """
    Shared state for the travel planning workflow với 7 agents.
    
    State được truyền giữa các agents trong LangGraph workflow.
    """
    # ========== USER INPUT ==========
    origin: Optional[str]  # Điểm xuất phát
    destination: Optional[str]  # Điểm đến
    start_date: Optional[str]  # Ngày bắt đầu (YYYY-MM-DD)
    days: Optional[int]  # Số ngày
    travelers: Optional[int]  # Số người
    travel_style: Optional[str]  # budget, standard, luxury
    rooms: Optional[int]  # Số phòng
    interests: Optional[List[str]]  # Sở thích
    max_budget: Optional[float]  # Ngân sách tối đa (VNĐ)
    
    # ========== TRANSPORT AGENT OUTPUT ==========
    transport: Optional[Dict[str, Any]]  # Thông tin vận chuyển
    transport_cost: Optional[float]  # Chi phí vận chuyển
    
    # ========== FLIGHT AGENT OUTPUT ==========
    flight: Optional[Dict[str, Any]]  # Thông tin vé máy bay
    departure_date: Optional[str]  # Ngày đi
    return_date: Optional[str]  # Ngày về
    
    # ========== ACCOMMODATION AGENT OUTPUT ==========
    hotels: Optional[List[Dict[str, Any]]]  # Danh sách khách sạn
    selected_hotel: Optional[Dict[str, Any]]  # Khách sạn đã chọn
    accommodation_cost: Optional[float]  # Chi phí lưu trú
    check_in: Optional[str]  # Ngày nhận phòng
    check_out: Optional[str]  # Ngày trả phòng
    
    # ========== ACTIVITIES AGENT OUTPUT ==========
    activities: Optional[List[Dict[str, Any]]]  # Danh sách hoạt động
    restaurants: Optional[List[Dict[str, Any]]]  # Danh sách nhà hàng
    activities_cost: Optional[float]  # Chi phí hoạt động
    dining_cost: Optional[float]  # Chi phí ăn uống
    dining_breakdown: Optional[Dict[str, Any]]  # Chi tiết chi phí ăn uống
    
    # ========== BUDGET AGENT OUTPUT ==========
    budget: Optional[Dict[str, Any]]  # Phân tích ngân sách
    budget_allocation: Optional[Dict[str, Any]]  # Phân bổ ngân sách
    
    # ========== PLANNING AGENT OUTPUT ==========
    itinerary: Optional[Dict[str, Any]]  # Lịch trình chi tiết
    
    # ========== WORKFLOW METADATA ==========
    status: Optional[str]  # success, error, in_progress
    error: Optional[str]  # Lỗi nếu có
    plan_ready: Optional[bool]  # Đã sẵn sàng chưa
    current_step: Optional[str]  # Bước hiện tại
    completed_steps: Optional[List[str]]  # Các bước đã hoàn thành
    
    # ========== ERRORS ==========
    transport_error: Optional[str]
    flight_error: Optional[str]
    accommodation_error: Optional[str]
    activities_error: Optional[str]
    budget_error: Optional[str]
    planning_error: Optional[str]
