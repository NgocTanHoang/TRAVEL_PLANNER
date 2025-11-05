"""
Transport Agent - Agent vận chuyển
===================================
Chịu trách nhiệm:
- Tính khoảng cách và thời gian di chuyển
- Đề xuất phương tiện phù hợp
- Tính chi phí vận chuyển nội địa
"""
import logging
from typing import Dict, Any, Optional
from ..base_agent import BaseAgent
from tools.transport_tools import get_transport_tools
from tools.geo_tools import get_geo_tools

logger = logging.getLogger(__name__)


class TransportAgent(BaseAgent):
    """Agent xử lý vận chuyển"""
    
    def __init__(self):
        super().__init__(
            agent_name="transport_agent",
            description="Handles transportation calculations and suggestions"
        )
        self.transport_tools = get_transport_tools()
        self.geo_tools = get_geo_tools()
    
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Xử lý yêu cầu vận chuyển
        
        Args:
            state: State dictionary với:
                - origin: Điểm xuất phát
                - destination: Điểm đến
                
        Returns:
            Updated state với thông tin vận chuyển
        """
        self.log_input(state)
        
        try:
            origin = state.get('origin')
            destination = state.get('destination')
            
            if not origin or not destination:
                state['transport_error'] = 'Missing origin or destination'
                return state
            
            # Tính khoảng cách và thời gian
            route_info = self.geo_tools.calculate_distance_time(origin, destination)
            
            if not route_info:
                state['transport_error'] = 'Cannot calculate route'
                return state
            
            # Đề xuất phương tiện
            suggestion = self.transport_tools.suggest_transport(
                origin, destination, route_info['distance_km']
            )
            
            # Thêm thông tin vào state
            state['transport'] = {
                'origin': origin,
                'destination': destination,
                'distance_km': route_info['distance_km'],
                'duration_minutes': route_info['duration_minutes'],
                'suggested_method': suggestion['method'],
                'estimated_cost_vnd': suggestion.get('estimated_cost_vnd'),
                'route_info': route_info
            }
            
            # Set transport_cost vào state (quan trọng cho budget calculation)
            transport_cost = suggestion.get('estimated_cost_vnd', 0)
            if transport_cost:
                state['transport_cost'] = transport_cost
            elif suggestion['method'] == 'flight':
                # Nếu là máy bay, để Flight Agent tính sau
                state['transport_cost'] = 0  # Sẽ được cập nhật bởi Flight Agent
            else:
                # Fallback: Tính dựa trên distance
                state['transport_cost'] = self.transport_tools._calculate_ground_transport_cost(
                    route_info['distance_km'],
                    suggestion['method']
                )
            
            self.log_output(state)
            return state
            
        except Exception as e:
            self.log_error(e, context={'state': state})
            state['transport_error'] = str(e)
            return state

