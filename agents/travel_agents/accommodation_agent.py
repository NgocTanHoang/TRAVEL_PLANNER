"""
Accommodation Agent - Agent lưu trú
====================================
Chịu trách nhiệm:
- Tìm kiếm khách sạn
- Tính giá phòng
- Lọc theo tiêu chí (giá, sao, vị trí)
"""
import logging
from typing import Dict, Any, Optional, List
from ..base_agent import BaseAgent
from tools.accommodation_tools import get_accommodation_tools

logger = logging.getLogger(__name__)


class AccommodationAgent(BaseAgent):
    """Agent xử lý lưu trú"""
    
    def __init__(self):
        super().__init__(
            agent_name="accommodation_agent",
            description="Handles hotel search and pricing"
        )
        self.accommodation_tools = get_accommodation_tools()
    
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Xử lý yêu cầu tìm khách sạn
        
        Args:
            state: State dictionary với:
                - destination: Điểm đến
                - check_in: Ngày nhận phòng (YYYY-MM-DD)
                - check_out: Ngày trả phòng (YYYY-MM-DD)
                - guests: Số khách (default: 2)
                - rooms: Số phòng (default: 1)
                - min_price: Giá tối thiểu (optional)
                - max_price: Giá tối đa (optional)
                - stars: Số sao (optional)
                
        Returns:
            Updated state với danh sách khách sạn
        """
        self.log_input(state)
        
        try:
            destination = state.get('destination')
            check_in = state.get('check_in')
            check_out = state.get('check_out')
            guests = state.get('guests', 2)
            rooms = state.get('rooms', 1)
            min_price = state.get('min_price')
            max_price = state.get('max_price')
            stars = state.get('stars')
            
            if not destination:
                state['accommodation_error'] = 'Missing destination'
                return state
            
            # Tìm kiếm khách sạn
            hotels = self.accommodation_tools.search_hotels(
                city=destination,
                check_in=check_in,
                check_out=check_out,
                guests=guests,
                rooms=rooms,
                min_price=min_price,
                max_price=max_price,
                stars=stars
            )
            
            # Tính tổng chi phí nếu đã chọn khách sạn
            selected_hotel = state.get('selected_hotel')
            if selected_hotel and check_in and check_out:
                from datetime import datetime
                start = datetime.strptime(check_in, '%Y-%m-%d')
                end = datetime.strptime(check_out, '%Y-%m-%d')
                nights = (end - start).days
                
                total_cost = self.accommodation_tools.calculate_total_accommodation_cost(
                    price_per_night=selected_hotel.get('price_per_night', 0),
                    nights=nights,
                    rooms=rooms
                )
                state['accommodation_total_cost'] = total_cost
                state['accommodation_cost'] = total_cost
            elif hotels and check_in and check_out:
                # Tính chi phí ước tính từ hotels phù hợp với travel_style
                from datetime import datetime
                start = datetime.strptime(check_in, '%Y-%m-%d')
                end = datetime.strptime(check_out, '%Y-%m-%d')
                nights = (end - start).days
                
                travel_style = state.get('travel_style', 'standard')
                
                # Tìm hotel phù hợp với travel_style
                if travel_style == 'budget':
                    # Lấy hotel giá thấp nhất
                    suitable_hotel = min(hotels, key=lambda h: h.get('price_per_night', float('inf')))
                elif travel_style == 'luxury':
                    # Lấy hotel giá cao nhất hoặc có nhiều sao nhất
                    suitable_hotel = max(hotels, key=lambda h: (h.get('stars', 0), h.get('price_per_night', 0)))
                else:  # standard
                    # Lấy hotel giá trung bình
                    if len(hotels) >= 3:
                        sorted_hotels = sorted(hotels, key=lambda h: h.get('price_per_night', 0))
                        suitable_hotel = sorted_hotels[len(sorted_hotels) // 2]  # Lấy hotel ở giữa
                    else:
                        suitable_hotel = hotels[0] if hotels else None
                
                if suitable_hotel:
                    estimated_price = suitable_hotel.get('price_per_night', 0)
                    if estimated_price > 0:
                        total_cost = self.accommodation_tools.calculate_total_accommodation_cost(
                            price_per_night=estimated_price,
                            nights=nights,
                            rooms=rooms
                        )
                        state['accommodation_cost'] = total_cost
                        state['suggested_hotel'] = suitable_hotel  # Đề xuất hotel này
                    else:
                        # Fallback: Ước tính giá theo travel_style và địa điểm
                        state['accommodation_cost'] = self._estimate_accommodation_cost(
                            destination, nights, rooms, travel_style
                        )
                else:
                    # Fallback: Ước tính giá theo travel_style và địa điểm
                    state['accommodation_cost'] = self._estimate_accommodation_cost(
                        destination, nights, rooms, travel_style
                    )
            else:
                # Fallback: Ước tính giá theo travel_style và địa điểm
                if check_in and check_out:
                    from datetime import datetime
                    start = datetime.strptime(check_in, '%Y-%m-%d')
                    end = datetime.strptime(check_out, '%Y-%m-%d')
                    nights = (end - start).days
                    travel_style = state.get('travel_style', 'standard')
                    state['accommodation_cost'] = self._estimate_accommodation_cost(
                        destination, nights, rooms, travel_style
                    )
            
            state['hotels'] = hotels
            state['accommodation_count'] = len(hotels)
            
            self.log_output(state)
            return state
            
        except Exception as e:
            self.log_error(e, context={'state': state})
            state['accommodation_error'] = str(e)
            state['hotels'] = []
            return state
    
    def _estimate_accommodation_cost(
        self,
        destination: str,
        nights: int,
        rooms: int,
        travel_style: str
    ) -> float:
        """
        Ước tính chi phí lưu trú khi không có dữ liệu thực tế
        Dựa trên travel_style và loại địa điểm
        """
        # Giá một đêm theo travel_style (VNĐ/phòng)
        if travel_style == 'budget':
            base_price_per_night = 300000  # 300k/đêm
        elif travel_style == 'luxury':
            base_price_per_night = 2000000  # 2M/đêm
        else:  # standard
            base_price_per_night = 800000  # 800k/đêm
        
        # Điều chỉnh theo thành phố lớn
        major_cities = ['Hà Nội', 'TP. Hồ Chí Minh', 'Đà Nẵng', 'Hồ Chí Minh', 'Hanoi', 'Ho Chi Minh City', 'Da Nang']
        if any(city.lower() in destination.lower() for city in major_cities):
            base_price_per_night *= 1.3  # Tăng 30% cho thành phố lớn
        
        total_cost = base_price_per_night * nights * rooms
        return round(total_cost)

