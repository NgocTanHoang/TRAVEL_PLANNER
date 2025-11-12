"""
Flight Agent - Agent vé máy bay
================================
Chịu trách nhiệm:
- Tìm kiếm giá vé máy bay
- Chuyển đổi tên thành phố sang mã IATA
- Tính giá khứ hồi hoặc một chiều
"""
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from ..base_agent import BaseAgent
from tools.flight_tools import get_flight_tools

logger = logging.getLogger(__name__)


class FlightAgent(BaseAgent):
    """Agent xử lý vé máy bay"""
    
    def __init__(self):
        super().__init__(
            agent_name="flight_agent",
            description="Handles flight price searches and calculations"
        )
        self.flight_tools = get_flight_tools()
    
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Xử lý yêu cầu tìm vé máy bay
        
        Args:
            state: State dictionary với:
                - origin: Điểm xuất phát
                - destination: Điểm đến
                - departure_date: Ngày đi (optional)
                - return_date: Ngày về (optional, None nếu một chiều)
                - passengers: Số hành khách (default: 1)
                
        Returns:
            Updated state với thông tin vé máy bay
        """
        self.log_input(state)
        
        try:
            origin = state.get('origin')
            destination = state.get('destination')
            departure_date = state.get('departure_date')
            return_date = state.get('return_date')
            passengers = state.get('passengers', 1)
            
            if not origin or not destination:
                state['flight_error'] = 'Missing origin or destination'
                return state
            
            # Tìm kiếm giá vé
            flight_info = self.flight_tools.search_flight_prices(
                origin=origin,
                destination=destination,
                departure_date=departure_date,
                return_date=return_date,
                passengers=passengers
            )
            
            if 'error' in flight_info:
                state['flight_error'] = flight_info['error']
                state['flight'] = None
            else:
                state['flight'] = flight_info
            
            self.log_output(state)
            return state
            
        except Exception as e:
            self.log_error(e, context={'state': state})
            state['flight_error'] = str(e)
            state['flight'] = None
            return state

