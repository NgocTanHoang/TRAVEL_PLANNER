"""
Orchestrator Agent - Agent điều phối
=====================================
Chịu trách nhiệm:
- Nhận yêu cầu từ người dùng
- Phân tích và giao nhiệm vụ cho các agents
- Tổng hợp kết quả từ tất cả agents
- Trả về kế hoạch du lịch hoàn chỉnh
"""
import logging
from typing import Dict, Any, Optional, List
from ..base_agent import BaseAgent
from .transport_agent import TransportAgent
from .flight_agent import FlightAgent
from .accommodation_agent import AccommodationAgent
from .budget_agent import BudgetAgent
from .planning_agent import PlanningAgent
from .activities_agent import ActivitiesAgent

logger = logging.getLogger(__name__)


class OrchestratorAgent(BaseAgent):
    """Agent điều phối toàn bộ hệ thống"""
    
    def __init__(self):
        super().__init__(
            agent_name="orchestrator_agent",
            description="Orchestrates all travel planning agents"
        )
        
        # Initialize all agents
        self.transport_agent = TransportAgent()
        self.flight_agent = FlightAgent()
        self.accommodation_agent = AccommodationAgent()
        self.budget_agent = BudgetAgent()
        self.planning_agent = PlanningAgent()
        self.activities_agent = ActivitiesAgent()
    
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Điều phối toàn bộ quy trình lập kế hoạch
        
        Args:
            state: State dictionary với:
                - origin: Điểm xuất phát
                - destination: Điểm đến
                - start_date: Ngày bắt đầu
                - days: Số ngày
                - travelers: Số người
                - travel_style: 'budget', 'standard', 'luxury'
                
        Returns:
            Updated state với kế hoạch hoàn chỉnh
        """
        self.log_input(state)
        
        try:
            # Bước 1: Transport Agent - Tính khoảng cách và đề xuất phương tiện
            logger.info("Step 1: Transport calculation...")
            state = await self.transport_agent.execute(state)
            
            # Bước 2: Flight Agent - Nếu phương tiện là máy bay
            if state.get('transport', {}).get('suggested_method') == 'flight':
                logger.info("Step 2: Flight price search with airport transfers...")
                
                # Xác định sân bay gần nhất cho origin và destination
                from tools.airport_utils import get_nearest_airport, calculate_airport_transport_cost
                from tools.geo_tools import get_geo_tools
                
                origin = state.get('origin')
                destination = state.get('destination')
                travelers = state.get('travelers', 1)
                
                # Lấy sân bay gần nhất
                origin_airport_info = get_nearest_airport(origin)
                dest_airport_info = get_nearest_airport(destination)
                
                if not origin_airport_info or not dest_airport_info:
                    logger.warning(f"Cannot find airports for {origin} or {destination}")
                    # Fallback: tính như cũ
                    state['departure_date'] = state.get('start_date')
                    state['passengers'] = travelers
                    state = await self.flight_agent.execute(state)
                    flight_price = state.get('flight', {}).get('price_vnd', 0) if state.get('flight') else 0
                    
                    if flight_price == 0:
                        distance_km = state.get('transport', {}).get('distance_km', 0)
                        if distance_km > 0:
                            estimated_price_per_person = min(max(distance_km * 2000, 1_500_000), 8_000_000)
                            flight_price = estimated_price_per_person * travelers
                        else:
                            flight_price = 3_000_000 * travelers
                    
                    state['transport_cost'] = flight_price
                else:
                    # Tính chi phí đầy đủ: origin → airport → flight → airport → destination
                    origin_airport_iata = origin_airport_info[0]
                    origin_airport_name = origin_airport_info[1]
                    dest_airport_iata = dest_airport_info[0]
                    dest_airport_name = dest_airport_info[1]
                    
                    geo_tools = get_geo_tools()
                    
                    # 1. Tính chi phí từ origin → sân bay đi
                    origin_to_airport_route = geo_tools.calculate_distance_time(
                        origin, f"{origin_airport_name}, {origin_airport_info[2]}"
                    )
                    origin_to_airport_cost = 0
                    if origin_to_airport_route:
                        origin_to_airport_dist = origin_to_airport_route['distance_km']
                        # Nếu xa (>50km), dùng xe buýt, gần thì taxi/Grab
                        method_to_airport = 'bus' if origin_to_airport_dist > 50 else 'taxi'
                        origin_to_airport_info = calculate_airport_transport_cost(
                            origin, origin_airport_name, origin_to_airport_dist, method_to_airport
                        )
                        origin_to_airport_cost = origin_to_airport_info['cost_vnd'] * travelers
                    
                    # 2. Tính giá vé máy bay
                    state['departure_date'] = state.get('start_date')
                    state['passengers'] = travelers
                    state['origin'] = origin_airport_iata  # Dùng IATA code cho flight search
                    state['destination'] = dest_airport_iata
                    state = await self.flight_agent.execute(state)
                    
                    flight_price = 0
                    if state.get('flight'):
                        flight_price = (
                            state['flight'].get('price_vnd', 0) or
                            state['flight'].get('price', 0) or
                            state['flight'].get('total_price_vnd', 0) or
                            0
                        )
                    
                    # Ước tính nếu không có giá từ API
                    if flight_price == 0:
                        # Dùng flight_tools để ước tính giá dựa trên route giữa các sân bay
                        from tools.flight_tools import get_flight_tools
                        flight_tools = get_flight_tools()
                        
                        # Ước tính giá dựa trên route giữa sân bay
                        estimated_flight = flight_tools._estimate_price(
                            origin_airport_iata,
                            dest_airport_iata,
                            'oneway',
                            travelers
                        )
                        flight_price = estimated_flight.get('price_vnd', 0)
                        
                        # Đảm bảo giá tối thiểu hợp lý (ít nhất 1.5M/người cho route dài)
                        if flight_price == 0 or flight_price < (1_500_000 * travelers):
                            # Route dài như SGN-HAN phải có giá tối thiểu 2M/người
                            if origin_airport_iata in ['SGN', 'HAN'] and dest_airport_iata in ['SGN', 'HAN']:
                                flight_price = 2_000_000 * travelers
                            else:
                                flight_price = 1_500_000 * travelers
                        
                        logger.info(f"Estimated flight price: {flight_price:,.0f} VNĐ for {origin_airport_iata}->{dest_airport_iata} ({travelers} travelers)")
                    
                    # 3. Tính chi phí từ sân bay đến → destination
                    airport_to_dest_route = geo_tools.calculate_distance_time(
                        f"{dest_airport_name}, {dest_airport_info[2]}", destination
                    )
                    airport_to_dest_cost = 0
                    airport_to_dest_info = None
                    method_from_airport = 'bus'
                    
                    if airport_to_dest_route:
                        airport_to_dest_dist = airport_to_dest_route['distance_km']
                        # Xác định phương tiện phù hợp
                        if airport_to_dest_dist < 30:
                            # Gần: taxi/Grab hoặc xe máy thuê
                            method_from_airport = 'taxi'
                            airport_to_dest_info = calculate_airport_transport_cost(
                                dest_airport_name, destination, airport_to_dest_dist, method_from_airport
                            )
                            airport_to_dest_cost = airport_to_dest_info['cost_vnd'] * travelers
                        elif airport_to_dest_dist < 200:
                            # Trung bình: xe buýt
                            method_from_airport = 'bus'
                            airport_to_dest_info = calculate_airport_transport_cost(
                                dest_airport_name, destination, airport_to_dest_dist, method_from_airport
                            )
                            airport_to_dest_cost = airport_to_dest_info['cost_vnd'] * travelers
                        else:
                            # Xa: xe buýt đường dài
                            method_from_airport = 'bus_long_distance'
                            # Xe buýt đường dài: ~3,000 VNĐ/km (rẻ hơn taxi)
                            airport_to_dest_cost = airport_to_dest_dist * 3000 * travelers
                            airport_to_dest_info = {
                                'cost_vnd': airport_to_dest_cost,
                                'method': 'bus_long_distance',
                                'distance_km': airport_to_dest_dist,
                                'duration_minutes': (airport_to_dest_dist / 60) * 60  # ~60km/h
                            }
                    
                    # Tổng chi phí vận chuyển
                    total_transport_cost = origin_to_airport_cost + flight_price + airport_to_dest_cost
                    
                    state['transport_cost'] = total_transport_cost
                    state['transport_breakdown'] = {
                        'origin_to_airport': {
                            'cost_vnd': origin_to_airport_cost,
                            'method': method_to_airport if origin_to_airport_route else 'unknown',
                            'distance_km': origin_to_airport_route['distance_km'] if origin_to_airport_route else 0,
                            'airport': origin_airport_name
                        },
                        'flight': {
                            'cost_vnd': flight_price,
                            'origin_airport': origin_airport_name,
                            'dest_airport': dest_airport_name
                        },
                        'airport_to_dest': {
                            'cost_vnd': airport_to_dest_cost,
                            'method': method_from_airport if airport_to_dest_route else 'unknown',
                            'distance_km': airport_to_dest_route['distance_km'] if airport_to_dest_route else 0,
                            'airport': dest_airport_name
                        },
                        'total_vnd': total_transport_cost
                    }
                    
                    logger.info(f"Transport breakdown: origin→airport={origin_to_airport_cost:,.0f}, "
                              f"flight={flight_price:,.0f}, airport→dest={airport_to_dest_cost:,.0f}, "
                              f"total={total_transport_cost:,.0f} VNĐ")
                    
                    # Restore origin/destination cho các agent khác
                    state['origin'] = origin
                    state['destination'] = destination
                    
                    # Cập nhật transport object
                    if state.get('transport'):
                        state['transport']['estimated_cost_vnd'] = total_transport_cost
                        state['transport']['breakdown'] = state['transport_breakdown']
            else:
                # Phương tiện khác: lấy từ transport cost đã tính
                transport_cost = state.get('transport_cost', 0)
                if transport_cost == 0:
                    transport_cost = state.get('transport', {}).get('estimated_cost_vnd', 0)
                
                # Nếu vẫn bằng 0, tính lại từ khoảng cách
                if transport_cost == 0:
                    distance_km = state.get('transport', {}).get('distance_km', 0)
                    if distance_km > 0:
                        from tools.transport_tools import get_transport_tools
                        transport_tools = get_transport_tools()
                        method = state.get('transport', {}).get('suggested_method', 'bus')
                        base_cost = transport_tools._calculate_ground_transport_cost(distance_km, method)
                        # Nhân với số người (travelers) nếu là phương tiện cá nhân
                        travelers = state.get('travelers', 1)
                        if method in ['taxi', 'grab', 'car']:
                            transport_cost = base_cost * travelers
                        else:
                            # Xe buýt/tàu: chi phí cố định hoặc nhân với số người tùy loại
                            transport_cost = base_cost * travelers
                        state['transport']['estimated_cost_vnd'] = transport_cost
                        logger.info(f"Calculated transport cost: {transport_cost:,.0f} VNĐ for {method} ({travelers} travelers)")
                
                state['transport_cost'] = transport_cost
            
            # Bước 3: Accommodation Agent - Tìm khách sạn
            logger.info("Step 3: Hotel search...")
            
            # Standardize nights calculation: nights = max(1, days - 1)
            days = state.get('days', 1)
            nights = max(1, days - 1)
            logger.info(f"Planning: days={days} nights={nights} travelers={state.get('travelers', 1)} travel_style={state.get('travel_style', 'standard')}")
            
            state['check_in'] = state.get('start_date')
            state['nights'] = nights  # Store nights in state for consistency
            if state.get('start_date') and days:
                from datetime import datetime, timedelta
                start = datetime.strptime(state['start_date'], '%Y-%m-%d')
                # Use nights instead of days for check_out calculation
                end = start + timedelta(days=nights)
                state['check_out'] = end.strftime('%Y-%m-%d')
            state = await self.accommodation_agent.execute(state)
            
            # Tính chi phí lưu trú nếu đã chọn khách sạn
            if state.get('selected_hotel') and state.get('check_in') and state.get('check_out'):
                from datetime import datetime
                start = datetime.strptime(state['check_in'], '%Y-%m-%d')
                end = datetime.strptime(state['check_out'], '%Y-%m-%d')
                # Use standardized nights calculation
                nights = max(1, (end - start).days)
                from tools.accommodation_tools import get_accommodation_tools
                acc_tools = get_accommodation_tools()
                state['accommodation_cost'] = acc_tools.calculate_total_accommodation_cost(
                    price_per_night=state['selected_hotel'].get('price_per_night', 0),
                    nights=nights,
                    rooms=state.get('rooms', 1)
                )
            elif state.get('hotels'):
                # Ước tính từ khách sạn đầu tiên
                hotel = state['hotels'][0]
                # Use standardized nights from state
                nights = state.get('nights', max(1, state.get('days', 1) - 1))
                from tools.accommodation_tools import get_accommodation_tools
                acc_tools = get_accommodation_tools()
                state['accommodation_cost'] = acc_tools.calculate_total_accommodation_cost(
                    price_per_night=hotel.get('price_per_night', 0),
                    nights=nights,
                    rooms=state.get('rooms', 1)
                )
                logger.info(f"Accommodation cost from hotel: {state['accommodation_cost']:,} VNĐ (nights={nights}, price_per_night={hotel.get('price_per_night', 0):,})")
            
            # Bước 4: Activities Agent - Tìm hoạt động và tính chi phí ăn uống
            logger.info("Step 4: Activities and dining...")
            state = await self.activities_agent.execute(state)
            state['activities_cost'] = state.get('activities_cost', 0)
            state['dining_cost'] = state.get('dining_cost', 0)
            
            # Bước 5: Budget Agent - Tính tổng ngân sách
            logger.info("Step 5: Budget calculation...")
            state = await self.budget_agent.execute(state)
            
            # Bước 6: Planning Agent - Tạo lịch trình chi tiết
            logger.info("Step 6: Itinerary creation...")
            state['restaurants'] = state.get('restaurants', [])
            state['activities'] = state.get('activities', [])
            state = await self.planning_agent.execute(state)
            
            # Tổng hợp kết quả
            state['status'] = 'success'
            state['plan_ready'] = True
            
            logger.info("Orchestration completed successfully")
            self.log_output(state)
            return state
            
        except Exception as e:
            self.log_error(e, context={'state': state})
            state['status'] = 'error'
            state['error'] = str(e)
            return state

