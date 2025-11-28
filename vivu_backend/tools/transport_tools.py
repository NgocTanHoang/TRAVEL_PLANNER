"""
Transport Tools - Công cụ vận chuyển
=====================================
- Tính khoảng cách và thời gian di chuyển
- Đề xuất phương tiện phù hợp
- Tính chi phí vận chuyển cho tất cả phương tiện:
  - Máy bay (Flight)
  - Xe buýt đường dài (Long-distance bus)
  - Xe bus thành phố (City bus)
  - Taxi công nghệ (Grab, Gojek, Be)
  - Taxi truyền thống
  - Xe máy tự lái (Motorbike)
  - Ô tô tự lái (Car)
  - Tàu hỏa (Train)
"""
import logging
from typing import Dict, Any, Optional, List
from .geo_tools import get_geo_tools

logger = logging.getLogger(__name__)


class TransportTools:
    """Công cụ vận chuyển cho Transport Agent"""
    
    # Bảng giá vận chuyển (VNĐ/km) - cập nhật đầy đủ
    TRANSPORT_RATES = {
        # Phương tiện công cộng
        'city_bus': 2000,        # Xe bus thành phố: 2k/km (vé lượt ~7-15k)
        'long_distance_bus': 3000,  # Xe buýt đường dài: 3k/km (vé ~300k-1M tùy quãng đường)
        'train': 1500,            # Tàu hỏa: 1.5k/km
        
        # Taxi & công nghệ
        'taxi': 15000,            # Taxi truyền thống: 15k/km
        'grab': 12000,            # Grab: 12k/km
        'gojek': 12000,           # Gojek: 12k/km
        'be': 11000,              # Be: 11k/km
        'greencar': 14000,        # VinFast GreenCar 4 chỗ: giá trung bình (sẽ tính chi tiết theo km)
        'luxurycar': 21000,       # VinFast LuxuryCar 5 chỗ: 21k/km (cố định)
        
        # Tự lái
        'motorbike': 2000,        # Xe máy: 2k/km (xăng + hao mòn)
        'car': 5000,              # Ô tô: 5k/km (xăng + hao mòn)
        
        # Phương tiện khác
        'walking': 0,             # Đi bộ: miễn phí
        'bicycle': 0,             # Xe đạp: miễn phí
    }
    
    # Phí cố định (VNĐ)
    FIXED_FEES = {
        'taxi': 20000,            # Phí mở cửa taxi
        'grab': 15000,            # Phí mở cửa Grab
        'greencar': 20000,        # Phí mở cửa GreenCar (VF 5 Plus hoặc VF e34)
        'luxurycar': 21000,       # Phí mở cửa LuxuryCar (VF 8)
        'gojek': 15000,           # Phí mở cửa Gojek
        'be': 15000,              # Phí mở cửa Be
        'city_bus': 0,            # Không có phí cố định
        'long_distance_bus': 0,   # Giá vé đã bao gồm
        'train': 0,               # Giá vé đã bao gồm
        'motorbike': 0,           # Không có phí cố định
        'car': 0,                 # Không có phí cố định
    }
    
    # Tốc độ trung bình (km/h)
    AVERAGE_SPEEDS = {
        'walking': 5,             # 5 km/h
        'bicycle': 15,            # 15 km/h
        'city_bus': 25,           # 25 km/h (trong thành phố)
        'long_distance_bus': 60,  # 60 km/h (đường dài)
        'taxi': 40,               # 40 km/h (trong thành phố)
        'grab': 40,               # 40 km/h
        'gojek': 40,              # 40 km/h
        'be': 40,                 # 40 km/h
        'greencar': 40,           # 40 km/h (trong thành phố)
        'luxurycar': 40,          # 40 km/h (trong thành phố)
        'motorbike': 45,          # 45 km/h (trong thành phố)
        'car': 50,                # 50 km/h (trong thành phố)
        'train': 80,              # 80 km/h
        'flight': 800,            # 800 km/h (tốc độ bay)
    }
    
    # Ngưỡng khoảng cách để đề xuất phương tiện (km)
    DISTANCE_THRESHOLDS = {
        'walking': 2,             # < 2km: đi bộ
        'bicycle': 5,             # < 5km: xe đạp
        'city_bus': 50,           # < 50km trong thành phố: xe bus thành phố
        'taxi_grab': 50,          # < 50km: taxi/Grab
        'motorbike': 100,         # < 100km: xe máy
        'car': 300,               # < 300km: ô tô
        'long_distance_bus': 500, # < 500km: xe buýt đường dài
        'train': 500,             # < 500km: tàu hỏa
        'flight': 500,            # >= 500km: máy bay
    }
    
    def __init__(self):
        self.geo_tools = get_geo_tools()
        # Cache để tránh tìm kiếm lại nhiều lần
        self._train_station_cache = {}  # {location: bool}
        self._airport_cache = {}  # {location: airport_info or None}
    
    def _estimate_distance_haversine(self, origin: str, destination: str) -> float:
        """
        Estimate distance using haversine formula as last resort fallback
        when both VietMap and OpenRouteService fail
        
        Args:
            origin: Điểm xuất phát
            destination: Điểm đến
            
        Returns:
            Distance in km (0 if geocoding fails)
        """
        from math import radians, cos, sin, asin, sqrt
        
        try:
            # Geocode both locations
            origin_coords = self.geo_tools.geocode(origin)
            dest_coords = self.geo_tools.geocode(destination)
            
            if not origin_coords or not dest_coords:
                logger.error(f"Cannot geocode for haversine: {origin} or {destination}")
                return 0
            
            lat1, lon1 = origin_coords['lat'], origin_coords['lon']
            lat2, lon2 = dest_coords['lat'], dest_coords['lon']
            
            # Haversine formula
            lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * asin(sqrt(a))
            r = 6371  # Earth radius in km
            
            distance = c * r
            
            # Apply road distance multiplier (roads are ~1.6x longer than straight line)
            road_distance = distance * 1.6
            
            logger.info(f"Haversine estimate {origin} -> {destination}: {distance:.2f} km (straight), {road_distance:.2f} km (road estimate)")
            return road_distance
            
        except Exception as e:
            logger.error(f"Haversine calculation failed: {e}")
            return 0

    
    def _check_train_station_exists(self, location: str) -> bool:
        """
        Kiểm tra xem location có ga tàu hỏa không bằng cách tìm kiếm thực tế
        Sử dụng VietMap API hoặc web search, không hardcode
        
        Args:
            location: Tên địa điểm/tỉnh thành
            
        Returns:
            True nếu có ga tàu, False nếu không
        """
        # Kiểm tra cache trước
        location_key = location.lower().strip()
        if location_key in self._train_station_cache:
            return self._train_station_cache[location_key]
        
        # Tìm kiếm ga tàu bằng VietMap API
        try:
            from .vietmap_tools import get_vietmap_tools
            vietmap = get_vietmap_tools()
            
            # Tìm kiếm các từ khóa liên quan đến ga tàu
            search_queries = [
                f"ga tàu {location}",
                f"nhà ga {location}",
                f"ga xe lửa {location}",
                f"train station {location}",
            ]
            
            for query in search_queries:
                results = vietmap.search_places(query, location=location, radius=50, limit=5)
                if results:
                    # Kiểm tra xem có kết quả nào là ga tàu không
                    for result in results:
                        name = (result.get('name') or '').lower()
                        address = (result.get('address') or '').lower()
                        category = (result.get('category') or '').lower()
                        
                        # Từ khóa chỉ ga tàu
                        train_keywords = ['ga', 'nhà ga', 'ga tàu', 'ga xe lửa', 'train station', 'railway station']
                        if any(keyword in name or keyword in address or keyword in category for keyword in train_keywords):
                            logger.debug(f"Found train station for {location}: {result.get('name')}")
                            self._train_station_cache[location_key] = True
                            return True
            
            # Nếu không tìm thấy bằng VietMap, thử web search
            try:
                from duckduckgo_search import DDGS
                ddgs = DDGS()
                
                search_query = f"ga tàu {location} Việt Nam"
                results = list(ddgs.text(search_query, max_results=3))
                
                for result in results:
                    title = (result.get('title', '') or '').lower()
                    body = (result.get('body', '') or '').lower()
                    
                    # Kiểm tra xem có đề cập đến ga tàu và location không
                    train_keywords = ['ga tàu', 'nhà ga', 'ga xe lửa', 'train station']
                    location_lower = location.lower()
                    
                    if any(keyword in title or keyword in body for keyword in train_keywords):
                        if location_lower in title or location_lower in body:
                            logger.debug(f"Found train station for {location} via web search")
                            self._train_station_cache[location_key] = True
                            return True
            except Exception as e:
                logger.debug(f"Web search for train station failed: {e}")
            
            # Không tìm thấy ga tàu
            logger.debug(f"No train station found for {location}")
            self._train_station_cache[location_key] = False
            return False
            
        except Exception as e:
            logger.warning(f"Error checking train station for {location}: {e}")
            # Fallback: giả sử không có ga tàu nếu không kiểm tra được
            self._train_station_cache[location_key] = False
            return False
    
    def _check_flight_needed(self, origin: str, destination: str, distance_km: float) -> bool:
        """
        Kiểm tra xem có cần máy bay không dựa trên khoảng cách và tính khả dụng
        - Khoảng cách < 200km: không cần máy bay (có thể dùng phương tiện khác)
        - Khoảng cách >= 200km: kiểm tra xem có sân bay ở cả 2 điểm không
        
        Args:
            origin: Điểm xuất phát
            destination: Điểm đến
            distance_km: Khoảng cách (km)
            
        Returns:
            True nếu cần máy bay, False nếu không
        """
        # Nếu khoảng cách quá ngắn (< 200km), không cần máy bay
        if distance_km < 200:
            logger.debug(f"Flight not needed: distance {distance_km}km < 200km")
            return False
        
        # Kiểm tra sân bay ở origin và destination
        try:
            from .airport_utils import get_nearest_airport
            
            origin_key = origin.lower().strip()
            dest_key = destination.lower().strip()
            
            # Kiểm tra cache
            if origin_key not in self._airport_cache:
                self._airport_cache[origin_key] = get_nearest_airport(origin)
            if dest_key not in self._airport_cache:
                self._airport_cache[dest_key] = get_nearest_airport(destination)
            
            origin_airport = self._airport_cache[origin_key]
            dest_airport = self._airport_cache[dest_key]
            
            if not origin_airport or not dest_airport:
                logger.debug(f"Flight not available: no airport near origin or destination")
                return False
            
            # Nếu origin và destination cùng sân bay, không cần bay
            if origin_airport[0] == dest_airport[0]:
                logger.debug(f"Flight not needed: same airport for origin and destination")
                return False
            
            return True
        except Exception as e:
            logger.warning(f"Error checking flight availability: {e}")
            # Fallback: nếu khoảng cách >= 500km, giả sử cần máy bay
            return distance_km >= 500
    
    def _check_transport_availability(
        self,
        method: str,
        origin: str,
        destination: str,
        distance_km: Optional[float] = None
    ) -> bool:
        """
        Kiểm tra xem phương tiện có khả dụng cho route cụ thể không
        Dựa trên thông tin thực tế từ tìm kiếm, không hardcode
        
        Args:
            method: Phương tiện ('train', 'flight', 'long_distance_bus', etc.)
            origin: Điểm xuất phát
            destination: Điểm đến
            distance_km: Khoảng cách (km) - optional, sẽ tính nếu không có
            
        Returns:
            True nếu phương tiện khả dụng, False nếu không
        """
        if method == 'train':
            # Kiểm tra tàu hỏa: cần có ga ở cả origin và destination
            origin_has_station = self._check_train_station_exists(origin)
            dest_has_station = self._check_train_station_exists(destination)
            
            if not origin_has_station or not dest_has_station:
                logger.debug(f"Train not available: origin or destination has no train station")
                return False
            
            return True
        
        elif method == 'flight':
            # Tính khoảng cách nếu chưa có
            if distance_km is None:
                route_info = self.geo_tools.calculate_distance_time(origin, destination)
                if not route_info:
                    logger.debug(f"Cannot calculate distance for flight check")
                    return False
                distance_km = route_info['distance_km']
            
            # Kiểm tra xem có cần máy bay không
            return self._check_flight_needed(origin, destination, distance_km)
        
        # Các phương tiện khác (xe buýt, taxi, xe máy, ô tô) luôn khả dụng
        # vì có thể di chuyển bằng đường bộ
        return True
    
    def suggest_transport(
        self,
        origin: str,
        destination: str,
        distance_km: Optional[float] = None,
        travelers: int = 1,
        prefer_cheapest: bool = False
    ) -> Dict[str, Any]:
        """
        Đề xuất phương tiện vận chuyển phù hợp nhất
        
        Args:
            origin: Điểm xuất phát
            destination: Điểm đến
            distance_km: Khoảng cách (nếu đã biết, sẽ tính lại nếu None)
            travelers: Số người đi
            prefer_cheapest: Ưu tiên phương tiện rẻ nhất (mặc định: False - cân bằng)
            
        Returns:
            Dict với 'method', 'distance_km', 'duration_minutes', 'estimated_cost', 'all_options'
        """
        # CRITICAL FIX: Validate and calculate distance with fallback
        if distance_km is None or distance_km <= 0:
            logger.info(f"Calculating distance for {origin} -> {destination}")
            route_info = self.geo_tools.calculate_distance_time(origin, destination)
            
            if route_info and route_info.get('distance_km', 0) > 0:
                distance_km = route_info['distance_km']
                logger.info(f"Distance from routing API: {distance_km} km")
            else:
                # Fallback to haversine estimate
                logger.warning(f"Routing API failed or returned 0, using haversine fallback")
                distance_km = self._estimate_distance_haversine(origin, destination)
                
                if distance_km <= 0:
                    logger.error(f"All distance calculation methods failed for {origin} -> {destination}")
                    return {
                        'method': 'unknown',
                        'error': 'Cannot calculate distance - all methods failed',
                        'origin': origin,
                        'destination': destination
                    }
                else:
                    logger.info(f"Using haversine estimate: {distance_km} km")
        
        # Xác định xem có phải trong cùng thành phố không (để phân biệt city_bus vs long_distance_bus)
        is_same_city = self._is_same_city(origin, destination)
        
        # Đề xuất phương tiện dựa trên khoảng cách và tính khả dụng
        # Thử các phương tiện theo thứ tự ưu tiên, chọn phương tiện đầu tiên khả dụng
        potential_methods = []
        if distance_km < self.DISTANCE_THRESHOLDS['walking']:
            potential_methods.append('walking')
        elif distance_km < self.DISTANCE_THRESHOLDS['bicycle']:
            potential_methods.append('bicycle')
        elif distance_km < self.DISTANCE_THRESHOLDS['city_bus'] and is_same_city:
            potential_methods.append('city_bus')
        elif distance_km < self.DISTANCE_THRESHOLDS['taxi_grab']:
            potential_methods.append('grab')  # Ưu tiên Grab hơn taxi
        elif distance_km < self.DISTANCE_THRESHOLDS['motorbike']:
            if travelers <= 2:
                potential_methods.append('motorbike')
            else:
                potential_methods.append('grab')
        elif distance_km < self.DISTANCE_THRESHOLDS['car']:
            if travelers <= 5:
                potential_methods.append('car')
            else:
                potential_methods.append('long_distance_bus')
        elif distance_km < self.DISTANCE_THRESHOLDS['long_distance_bus']:
            potential_methods.append('long_distance_bus')
        elif distance_km < self.DISTANCE_THRESHOLDS['train']:
            potential_methods.append('train')
        else:
            potential_methods.append('flight')
        
        # Kiểm tra tính khả dụng và chọn phương tiện đầu tiên khả dụng
        method = None
        for potential_method in potential_methods:
            if self._check_transport_availability(potential_method, origin, destination, distance_km):
                method = potential_method
                break
        
        # Nếu không có phương tiện nào khả dụng, fallback về phương tiện đường bộ
        if not method:
            logger.warning(f"No available transport method for {origin} -> {destination}, using fallback")
            # Fallback: ưu tiên xe buýt đường dài, nếu không thì xe máy/ô tô
            if distance_km < self.DISTANCE_THRESHOLDS['long_distance_bus']:
                method = 'long_distance_bus'
            elif distance_km < self.DISTANCE_THRESHOLDS['motorbike']:
                method = 'motorbike'
            else:
                method = 'car'
        
        # Tính chi phí chi tiết
        cost_info = self.calculate_transport_cost(distance_km, method, travelers)
        
        # Lấy tất cả các phương tiện có thể (để so sánh)
        all_options = self.compare_all_transport_options(origin, destination, travelers, distance_km)
        
        result = {
            'method': method,
            'method_name': cost_info.get('method_name', method),
            'distance_km': round(distance_km, 2),
            'duration_minutes': cost_info['duration_minutes'],
            'estimated_cost_vnd': cost_info['cost_vnd'],
            'cost_per_person': cost_info['cost_per_person'],
            'description': cost_info['description'],
            'origin': origin,
            'destination': destination,
            'travelers': travelers,
            'all_options': all_options.get('options', []),
            'cheapest_option': all_options.get('cheapest'),
            'fastest_option': all_options.get('fastest')
        }
        print(f"DEBUG: suggest_transport returning distance={result['distance_km']}")
        return result
    
    def _is_same_city(self, origin: str, destination: str) -> bool:
        """
        Kiểm tra xem origin và destination có cùng thành phố không
        (để phân biệt city_bus vs long_distance_bus)
        """
        # Các thành phố lớn
        major_cities = [
            'Hà Nội', 'Hanoi', 'Ha Noi',
            'TP. Hồ Chí Minh', 'Ho Chi Minh', 'Ho Chi Minh City', 'Sài Gòn', 'Sai Gon',
            'Đà Nẵng', 'Da Nang',
            'Hải Phòng', 'Hai Phong',
            'Cần Thơ', 'Can Tho',
            'Nha Trang',
            'Huế', 'Hue',
            'Đà Lạt', 'Da Lat'
        ]
        
        origin_lower = origin.lower()
        dest_lower = destination.lower()
        
        # Kiểm tra xem có cùng thành phố không
        for city in major_cities:
            city_lower = city.lower()
            if city_lower in origin_lower and city_lower in dest_lower:
                return True
        
        return False
    
    def calculate_transport_cost(
        self,
        distance_km: float,
        method: str,
        travelers: int = 1
    ) -> Dict[str, Any]:
        """
        Tính chi phí vận chuyển chi tiết cho tất cả phương tiện
        
        Args:
            distance_km: Khoảng cách (km)
            method: Phương tiện ('flight', 'long_distance_bus', 'city_bus', 'taxi', 'grab', 'motorbike', 'car', 'train')
            travelers: Số người đi
            
        Returns:
            Dict với 'cost_vnd', 'cost_per_person', 'duration_minutes', 'method', 'description'
        """
        if method == 'flight':
            # Máy bay - để Flight Agent tính
            return {
                'cost_vnd': 0,
                'cost_per_person': 0,
                'duration_minutes': round((distance_km / self.AVERAGE_SPEEDS['flight']) * 60, 1),
                'method': 'flight',
                'description': 'Vé máy bay (sẽ được tính bởi Flight Agent)'
            }
        
        # Lấy giá/km
        rate = self.TRANSPORT_RATES.get(method, self.TRANSPORT_RATES['city_bus'])
        fixed_fee = self.FIXED_FEES.get(method, 0)
        speed = self.AVERAGE_SPEEDS.get(method, 40)
        
        # Tính chi phí
        if method == 'long_distance_bus':
            # Xe buýt đường dài: giá vé cố định theo quãng đường
            # Ví dụ: Hà Nội - Sài Gòn (~1700km) ~800k-1.2M/người
            if distance_km < 200:
                cost_per_person = 200000  # 200k
            elif distance_km < 500:
                cost_per_person = 400000  # 400k
            elif distance_km < 1000:
                cost_per_person = 600000  # 600k
            else:
                cost_per_person = 800000  # 800k
            total_cost = cost_per_person * travelers
        elif method == 'city_bus':
            # Xe bus thành phố: vé lượt cố định
            # Mỗi lượt: 7-15k tùy thành phố, giả sử trung bình 10k
            cost_per_trip = 10000
            # Ước tính số lượt cần (giả sử mỗi lượt đi được ~10km)
            trips_needed = max(1, int(distance_km / 10))
            cost_per_person = cost_per_trip * trips_needed
            total_cost = cost_per_person * travelers
        elif method == 'train':
            # Tàu hỏa: giá vé theo quãng đường
            # Ví dụ: Hà Nội - Sài Gòn (~1700km) ~600k-1.5M/người tùy hạng
            if distance_km < 200:
                cost_per_person = 150000  # 150k
            elif distance_km < 500:
                cost_per_person = 300000  # 300k
            elif distance_km < 1000:
                cost_per_person = 500000  # 500k
            else:
                cost_per_person = 800000  # 800k
            total_cost = cost_per_person * travelers
        elif method == 'greencar':
            # VinFast GreenCar 4 chỗ: cấu trúc giá đặc biệt
            # Giá mở cửa: 20.000 VNĐ
            # 24km tiếp theo (km 1-25): 14.000 VNĐ/km (VF 5 Plus) hoặc 15.500 VNĐ/km (VF e34)
            # Từ km thứ 26 trở đi: 12.000 VNĐ/km (VF 5 Plus) hoặc 12.500 VNĐ/km (VF e34)
            # Sử dụng giá trung bình VF 5 Plus (rẻ hơn)
            opening_fee = 20000
            if distance_km <= 0:
                base_cost = opening_fee
            elif distance_km <= 25:
                # 24km tiếp theo (từ km 1-25)
                km_after_opening = distance_km
                base_cost = opening_fee + (km_after_opening * 14000)
            else:
                # Từ km thứ 26 trở đi
                base_cost = opening_fee + (25 * 14000) + ((distance_km - 25) * 12000)
            # GreenCar 4 chỗ có thể chở tối đa 4 người
            if travelers > 4:
                vehicles_needed = (travelers + 3) // 4  # Làm tròn lên
                total_cost = base_cost * vehicles_needed
            else:
                total_cost = base_cost
        elif method == 'luxurycar':
            # VinFast LuxuryCar 5 chỗ: giá cố định 21.000 VNĐ/km
            # Giá mở cửa: 21.000 VNĐ
            opening_fee = 21000
            if distance_km <= 0:
                base_cost = opening_fee
            else:
                base_cost = opening_fee + (distance_km * 21000)
            # LuxuryCar 5 chỗ có thể chở tối đa 5 người
            if travelers > 5:
                vehicles_needed = (travelers + 4) // 5  # Làm tròn lên
                total_cost = base_cost * vehicles_needed
            else:
                total_cost = base_cost
        elif method in ['motorbike', 'car']:
            # Xe máy/ô tô tự lái: chỉ tính xăng + hao mòn (không nhân số người)
            base_cost = distance_km * rate
            total_cost = base_cost  # 1 xe cho nhiều người
        else:
            # Taxi, Grab, Gojek, Be: tính theo km và nhân số người
            base_cost = distance_km * rate + fixed_fee
            # Nếu nhiều người, có thể cần nhiều xe (giả sử 4 người/xe)
            if travelers > 4:
                vehicles_needed = (travelers + 3) // 4  # Làm tròn lên
                total_cost = base_cost * vehicles_needed
            else:
                total_cost = base_cost
        
        # Tính thời gian
        duration_minutes = round((distance_km / speed) * 60, 1)
        
        # Mô tả phương tiện
        method_names = {
            'flight': 'Máy bay',
            'long_distance_bus': 'Xe buýt đường dài',
            'city_bus': 'Xe bus thành phố',
            'taxi': 'Taxi',
            'grab': 'Grab',
            'greencar': 'VinFast GreenCar',
            'luxurycar': 'VinFast LuxuryCar',
            'gojek': 'Gojek',
            'be': 'Be',
            'motorbike': 'Xe máy tự lái',
            'car': 'Ô tô tự lái',
            'train': 'Tàu hỏa',
            'walking': 'Đi bộ',
            'bicycle': 'Xe đạp'
        }
        
        return {
            'cost_vnd': round(total_cost),
            'cost_per_person': round(total_cost / travelers) if travelers > 0 else round(total_cost),
            'duration_minutes': duration_minutes,
            'distance_km': round(distance_km, 2),
            'method': method,
            'method_name': method_names.get(method, method),
            'description': f'{method_names.get(method, method)} - {round(distance_km, 1)}km, ~{duration_minutes} phút'
        }
    
    def _calculate_ground_transport_cost(
        self,
        distance_km: float,
        method: str
    ) -> float:
        """Tính chi phí vận chuyển nội địa (backward compatibility)"""
        result = self.calculate_transport_cost(distance_km, method, travelers=1)
        return result['cost_vnd']
    
    def compare_all_transport_options(
        self,
        origin: str,
        destination: str,
        travelers: int = 1,
        distance_km: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        So sánh tất cả các phương tiện có thể sử dụng
        
        Args:
            origin: Điểm xuất phát
            destination: Điểm đến
            travelers: Số người đi
            distance_km: Khoảng cách (nếu đã biết)
            
        Returns:
            Dict với danh sách các phương tiện và chi phí
        """
        if distance_km is None:
            route_info = self.geo_tools.calculate_distance_time(origin, destination)
            if not route_info:
                return {'error': 'Cannot calculate distance'}
            distance_km = route_info['distance_km']
        
        options = []
        
        # Xác định các phương tiện phù hợp
        potential_options = []
        if distance_km < self.DISTANCE_THRESHOLDS['walking']:
            potential_options.append('walking')
        if distance_km < self.DISTANCE_THRESHOLDS['bicycle']:
            potential_options.append('bicycle')
        if distance_km < self.DISTANCE_THRESHOLDS['city_bus']:
            potential_options.append('city_bus')
        if distance_km < self.DISTANCE_THRESHOLDS['taxi_grab']:
            potential_options.extend(['taxi', 'grab', 'gojek', 'be'])
        if distance_km < self.DISTANCE_THRESHOLDS['motorbike']:
            potential_options.append('motorbike')
        if distance_km < self.DISTANCE_THRESHOLDS['car']:
            potential_options.append('car')
        if distance_km < self.DISTANCE_THRESHOLDS['long_distance_bus']:
            potential_options.append('long_distance_bus')
        if distance_km < self.DISTANCE_THRESHOLDS['train']:
            potential_options.append('train')
        if distance_km >= self.DISTANCE_THRESHOLDS['flight']:
            potential_options.append('flight')
        
        # Lọc các phương tiện khả dụng (kiểm tra tính khả dụng thực tế)
        options = []
        for method in set(potential_options):  # Remove duplicates
            if self._check_transport_availability(method, origin, destination, distance_km):
                options.append(method)
            else:
                logger.debug(f"Filtered out {method} for {origin} -> {destination} (not available)")
        
        # Tính chi phí cho từng phương tiện khả dụng
        results = []
        for method in options:
            try:
                cost_info = self.calculate_transport_cost(distance_km, method, travelers)
                results.append(cost_info)
            except Exception as e:
                logger.warning(f"Error calculating cost for {method}: {e}")
        
        # Sắp xếp theo chi phí
        results.sort(key=lambda x: x['cost_vnd'])
        
        return {
            'origin': origin,
            'destination': destination,
            'distance_km': round(distance_km, 2),
            'travelers': travelers,
            'options': results,
            'cheapest': results[0] if results else None,
            'fastest': min(results, key=lambda x: x['duration_minutes']) if results else None
        }
    
    def calculate_multi_hop_route(
        self,
        origin: str,
        destination: str,
        hubs: List[str] = None
    ) -> Dict[str, Any]:
        """
        Tính toán hành trình nhiều chặng
        
        Args:
            origin: Điểm xuất phát
            destination: Điểm đến
            hubs: Danh sách hub trung gian (nếu None, tự động đề xuất)
            
        Returns:
            Dict với thông tin từng chặng
        """
        # Hubs mặc định - query từ database hoặc sử dụng danh sách động
        # Không hardcode tên thành phố, có thể query từ TinhThanh với loại là thành phố lớn
        if not hubs:
            # Mặc định: các thành phố lớn (có thể query từ database sau)
            # Tạm thời dùng empty list để tính toán dựa trên khoảng cách thực tế
            hubs = []
        
        route_info = self.geo_tools.calculate_distance_time(origin, destination)
        if not route_info:
            return {'error': 'Cannot calculate direct route'}
        
        direct_distance = route_info['distance_km']
        
        # Tìm hub gần nhất với điểm xuất phát và điểm đến
        # TODO: Implement logic tìm hub tốt nhất
        
        # Tạm thời return direct route
        return {
            'type': 'direct',
            'total_distance_km': direct_distance,
            'total_duration_minutes': route_info['duration_minutes'],
            'hops': [
                {
                    'from': origin,
                    'to': destination,
                    'distance_km': direct_distance,
                    'duration_minutes': route_info['duration_minutes'],
                    'method': self.suggest_transport(origin, destination, direct_distance)['method']
                }
            ]
        }


# Singleton instance
_transport_tools = None

def get_transport_tools() -> TransportTools:
    """Get singleton TransportTools instance"""
    global _transport_tools
    if _transport_tools is None:
        _transport_tools = TransportTools()
    return _transport_tools

