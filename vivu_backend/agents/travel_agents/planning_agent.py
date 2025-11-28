"""
Planning Agent - Agent lập kế hoạch
====================================
Chịu trách nhiệm:
- Tạo lịch trình hàng ngày chi tiết
- Phân bổ thời gian hợp lý
- Đề xuất hoạt động theo thời gian
- Sử dụng semantic understanding để sắp xếp hoạt động hợp lý
- Tạo mô tả lịch trình bằng LLM từ dữ liệu JSON
"""
import logging
from typing import Dict, Any, Optional, List
from ..base_agent import BaseAgent
from tools.planning_tools import get_planning_tools
from utils.semantic_place_classifier import (
    understand_place_semantics,
    extract_place_features
)
from utils.itinerary_formatter import (
    format_state_to_json,
    generate_itinerary_description
)

logger = logging.getLogger(__name__)


class PlanningAgent(BaseAgent):
    """Agent xử lý lập kế hoạch"""
    
    def __init__(self):
        super().__init__(
            agent_name="planning_agent",
            description="Creates detailed daily itineraries"
        )
        self.planning_tools = get_planning_tools()
    
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Tạo lịch trình đầy đủ
        
        Args:
            state: State dictionary với:
                - start_date: Ngày bắt đầu (YYYY-MM-DD)
                - days: Số ngày
                - destination: Điểm đến
                - hotels: Danh sách khách sạn (optional)
                - restaurants: Danh sách nhà hàng (optional)
                - activities: Danh sách hoạt động (optional)
                
        Returns:
            Updated state với lịch trình đầy đủ
        """
        self.log_input(state)
        
        try:
            start_date = state.get('start_date')
            days = state.get('days', 1)
            destination = state.get('destination')
            hotels = state.get('hotels', [])
            restaurants = state.get('restaurants', [])
            activities = state.get('activities', [])
            
            # Validation
            if not start_date or not destination:
                state['planning_error'] = 'Missing start_date or destination'
                return state
            
            if days < 1:
                state['planning_error'] = 'Days must be at least 1'
                return state
            
            if days > 30:
                state['planning_error'] = 'Days cannot exceed 30'
                return state
            
            # Validate date format
            try:
                from datetime import datetime
                datetime.strptime(start_date, '%Y-%m-%d')
            except ValueError:
                state['planning_error'] = f'Invalid date format: {start_date}. Expected YYYY-MM-DD'
                return state
            
            # Tạo lịch trình đầy đủ
            # Support both string and list for travel_style
            travel_style = state.get('travel_style', 'standard')
            # Convert JSON string to list if needed
            if isinstance(travel_style, str):
                try:
                    import json
                    travel_style = json.loads(travel_style)
                except (json.JSONDecodeError, ValueError):
                    pass  # Keep as string
            
            selected_hotel = state.get('selected_hotel')
            
            # Cải thiện activities với semantic understanding
            # Thêm thông tin semantic vào activities nếu chưa có
            enhanced_activities = []
            for activity in activities:
                if 'semantic_features' not in activity:
                    # Nếu chưa có semantic features, tính toán lại
                    semantics = understand_place_semantics(
                        name=activity.get('name', ''),
                        description=activity.get('description', ''),
                        type_hint=activity.get('type', ''),
                        category=activity.get('category', '')
                    )
                    activity['semantic_features'] = semantics['features']
                    activity['semantic_confidence'] = semantics['confidence']
                    # Cập nhật duration_hours nếu chưa có
                    if 'duration_hours' not in activity:
                        activity['duration_hours'] = semantics['features'].get('duration_hours', 2.0)
                    # Cập nhật best_time nếu chưa có
                    if 'best_time' not in activity:
                        activity['best_time'] = semantics['features'].get('best_time', ['anytime'])
            
            itinerary = self.planning_tools.create_full_itinerary(
                start_date=start_date,
                days=days,
                destination=destination,
                hotels=hotels,
                restaurants=restaurants,
                activities=activities,  # Sử dụng activities đã được enhance
                travel_style=travel_style,
                selected_hotel=selected_hotel
            )
            
            state['itinerary'] = itinerary
            
            # Tạo JSON data từ state để format cho LLM
            try:
                # Update state với itinerary data để format_state_to_json có thể sử dụng
                state_with_itinerary = state.copy()
                state_with_itinerary['itinerary'] = itinerary
                
                json_data = format_state_to_json(state_with_itinerary)
                state['itinerary_json'] = json_data
                
                # Generate description using LLM (force enable LLM for description generation)
                from tools.planning_tools import get_llm
                llm = get_llm()
                description = generate_itinerary_description(json_data, llm=llm, force_llm=True)
                state['itinerary_description'] = description
                logger.info("Generated itinerary description using LLM")
            except Exception as e:
                logger.warning(f"Failed to generate itinerary description: {e}", exc_info=True)
                state['itinerary_description'] = None
            
            self.log_output(state)
            return state
            
        except Exception as e:
            self.log_error(e, context={'state': state})
            state['planning_error'] = str(e)
            return state

