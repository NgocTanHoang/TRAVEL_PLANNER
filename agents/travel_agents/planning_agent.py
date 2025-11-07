"""
Planning Agent - Agent lập kế hoạch
====================================
Chịu trách nhiệm:
- Tạo lịch trình hàng ngày chi tiết
- Phân bổ thời gian hợp lý
- Đề xuất hoạt động theo thời gian
"""
import logging
from typing import Dict, Any, Optional, List
from ..base_agent import BaseAgent
from tools.planning_tools import get_planning_tools

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
            itinerary = self.planning_tools.create_full_itinerary(
                start_date=start_date,
                days=days,
                destination=destination,
                hotels=hotels,
                restaurants=restaurants,
                activities=activities,
                travel_style=travel_style,
                selected_hotel=selected_hotel
            )
            
            state['itinerary'] = itinerary
            
            self.log_output(state)
            return state
            
        except Exception as e:
            self.log_error(e, context={'state': state})
            state['planning_error'] = str(e)
            return state

