"""
Flight Tools - Công cụ vé máy bay
===================================
- Chuyển đổi tên thành phố sang mã IATA
- Tìm kiếm giá vé máy bay
- Tính giá khứ hồi hoặc một chiều

Lưu ý về FlightAPI:
- Gói free có giới hạn 30 lượt/tháng
- Nên sử dụng caching để tránh gọi API nhiều lần cho cùng một request
- Chỉ sử dụng khi SerpAPI không khả dụng
"""
import logging
from typing import Dict, Any, Optional, List
import requests
import os
from datetime import datetime, timedelta
import hashlib
import json

logger = logging.getLogger(__name__)

# Import cache utility
try:
    from utils.cache import cache_get, cache_set
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False
    logger.warning("Cache utility not available, FlightAPI calls will not be cached")


class FlightTools:
    """Công cụ vé máy bay cho Flight Agent"""
    
    # Mapping tên thành phố → mã IATA
    CITY_IATA_MAP = {
        'Hà Nội': 'HAN',
        'Ha Noi': 'HAN',
        'Hanoi': 'HAN',
        'TP. Hồ Chí Minh': 'SGN',
        'Ho Chi Minh': 'SGN',
        'Ho Chi Minh City': 'SGN',
        'Sài Gòn': 'SGN',
        'Đồng Nai': 'SGN',  # Đồng Nai gần TP.HCM, dùng sân bay SGN
        'Dong Nai': 'SGN',
        'Biên Hòa': 'SGN',  # Thành phố chính của Đồng Nai
        'Bien Hoa': 'SGN',
        'Đà Nẵng': 'DAD',
        'Da Nang': 'DAD',
        'Nha Trang': 'CXR',
        'Phú Quốc': 'PQC',
        'Phu Quoc': 'PQC',
        'Đà Lạt': 'DLI',
        'Da Lat': 'DLI',
        'Huế': 'HUI',
        'Hue': 'HUI',
        'Hải Phòng': 'HPH',
        'Hai Phong': 'HPH',
        'Cần Thơ': 'VCA',
        'Can Tho': 'VCA',
        'Quy Nhon': 'UIH',
        'Quy Nhơn': 'UIH',
    }
    
    def __init__(self):
        self.travelpayouts_token = os.getenv('TRAVELPAYOUTS_TOKEN', '')
        self.flightapi_key = os.getenv('FLIGHTAPI_KEY', '')
        self.base_url = "https://api.travelpayouts.com"
        
        # SerpAPI for Google Flights
        try:
            from tools.serpapi_tools import get_serpapi_tools
            self.serpapi = get_serpapi_tools()
        except Exception as e:
            logger.warning(f"SerpAPI tools not available: {e}")
            self.serpapi = None
        
    def city_to_iata(self, city_name: str) -> Optional[str]:
        """
        Chuyển đổi tên thành phố sang mã IATA
        
        Args:
            city_name: Tên thành phố
            
        Returns:
            Mã IATA hoặc None
        """
        # Tìm trong map (case-insensitive)
        city_lower = city_name.strip().lower()
        for city, iata in self.CITY_IATA_MAP.items():
            if city.lower() == city_lower:
                return iata
        
        return None
    
    def search_flight_prices(
        self,
        origin: str,
        destination: str,
        departure_date: Optional[str] = None,
        return_date: Optional[str] = None,
        passengers: int = 1
    ) -> Dict[str, Any]:
        """
        Tìm kiếm giá vé máy bay
        
        Args:
            origin: Điểm xuất phát (tên thành phố hoặc IATA)
            destination: Điểm đến (tên thành phố hoặc IATA)
            departure_date: Ngày đi (YYYY-MM-DD)
            return_date: Ngày về (YYYY-MM-DD, None nếu một chiều)
            passengers: Số hành khách
            
        Returns:
            Dict với 'price_vnd', 'currency', 'route_type', 'airline', etc.
        """
        # Chuyển đổi sang IATA
        origin_iata = self.city_to_iata(origin)
        dest_iata = self.city_to_iata(destination)
        
        if not origin_iata or not dest_iata:
            return {
                'error': f'Cannot find IATA codes for {origin} or {destination}',
                'price_vnd': None
            }
        
        # Nếu không có ngày, dùng ngày mặc định (30 ngày sau)
        if not departure_date:
            departure_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        
        route_type = 'roundtrip' if return_date else 'oneway'
        
        try:
            # Ưu tiên SerpAPI (Google Flights) - chính xác nhất
            if self.serpapi and self.serpapi.api_key:
                serpapi_result = self.serpapi.search_flights(
                    origin_iata, dest_iata, departure_date, return_date
                )
                
                if serpapi_result.get('status') == 'success' and serpapi_result.get('flights'):
                    # Lấy chuyến bay tốt nhất
                    best_flight = serpapi_result['flights'][0]
                    price = best_flight.get('price', 0)
                    
                    # Nhân với số hành khách
                    total_price = price * passengers
                    
                    return {
                        'price_vnd': total_price,
                        'currency': 'VND',
                        'route_type': route_type,
                        'origin_iata': origin_iata,
                        'destination_iata': dest_iata,
                        'passengers': passengers,
                        'source': 'serpapi',
                        'airline': best_flight.get('airline', 'Unknown'),
                        'flight_number': best_flight.get('flight_number', ''),
                        'duration': best_flight.get('duration', 0),
                        'all_flights': serpapi_result.get('flights', []),
                        'lowest_price': serpapi_result.get('lowest_price', 0) * passengers,
                        'typical_price_range': [
                            p * passengers for p in serpapi_result.get('typical_price_range', [])
                        ]
                    }
            
            # Ưu tiên thứ 2: FlightAPI (chỉ dùng khi SerpAPI không khả dụng để tiết kiệm quota)
            # Gói free có giới hạn 30 lượt/tháng, nên chỉ dùng khi thực sự cần
            if self.flightapi_key:
                flightapi_result = self._search_via_flightapi(
                    origin_iata, dest_iata, departure_date, return_date, passengers
                )
                if flightapi_result.get('price_vnd') and flightapi_result.get('price_vnd') > 0:
                    logger.info(f"FlightAPI used successfully for {origin_iata}->{dest_iata}")
                    return flightapi_result
            
            # Fallback: Travelpayouts API
            if self.travelpayouts_token:
                return self._search_via_travelpayouts(
                    origin_iata, dest_iata, departure_date, return_date, passengers
                )
            
            # Fallback cuối cùng: Ước tính giá
            return self._estimate_price(origin_iata, dest_iata, route_type, passengers)
            
        except Exception as e:
            logger.error(f"Flight search error: {e}")
            return self._estimate_price(origin_iata, dest_iata, route_type, passengers)
    
    def _search_via_flightapi(
        self,
        origin_iata: str,
        dest_iata: str,
        departure_date: str,
        return_date: Optional[str],
        passengers: int
    ) -> Dict[str, Any]:
        """
        Tìm kiếm giá vé máy bay qua FlightAPI.io
        
        Docs: https://api.flightapi.io/
        
        Lưu ý: Gói free có giới hạn 30 lượt/tháng
        - Sử dụng caching để tránh gọi API nhiều lần cho cùng một request
        - Cache TTL: 24 giờ (giá vé thay đổi theo ngày)
        """
        # Tạo cache key từ các tham số
        cache_key_data = {
            'origin': origin_iata,
            'dest': dest_iata,
            'date': departure_date,
            'return': return_date or '',
            'passengers': passengers,
            'source': 'flightapi'
        }
        cache_key_str = json.dumps(cache_key_data, sort_keys=True)
        cache_key = f"flightapi:{hashlib.md5(cache_key_str.encode()).hexdigest()}"
        
        # Kiểm tra cache trước (TTL: 24 giờ để tiết kiệm quota)
        if CACHE_AVAILABLE:
            cached_result = cache_get(cache_key)
            if cached_result:
                logger.info(f"FlightAPI cache hit for {origin_iata}->{dest_iata}")
                return cached_result
        
        try:
            # Xác định endpoint dựa trên loại chuyến bay
            if return_date:
                endpoint = f'https://api.flightapi.io/roundtrip/{self.flightapi_key}'
            else:
                endpoint = f'https://api.flightapi.io/oneway/{self.flightapi_key}'
            
            # Chuẩn bị params
            params = {
                'from': origin_iata,
                'to': dest_iata,
                'date': departure_date,
                'adults': passengers,
                'children': 0,
                'infants': 0,
                'cabin': 'economy',
            }
            
            if return_date:
                params['return'] = return_date
            
            # Gửi request
            response = requests.get(endpoint, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                # Parse response từ FlightAPI
                # Cấu trúc response có thể khác nhau, cần kiểm tra
                if isinstance(data, dict):
                    # Thử các key có thể có
                    price = (
                        data.get('price') or
                        data.get('totalPrice') or
                        data.get('total_price') or
                        data.get('fare', {}).get('total') or
                        0
                    )
                    
                    # Nếu price là số, có thể là USD hoặc VND
                    # FlightAPI thường trả về USD, cần convert sang VND
                    if price > 0:
                        # Nếu giá < 100, có thể là USD (giả sử giá VND sẽ > 100)
                        if price < 100:
                            price_vnd = int(price * 25000)  # Convert USD to VND (~25k VND/USD)
                        else:
                            price_vnd = int(price)
                        
                        # Nhân với số hành khách (nếu chưa nhân)
                        if 'adults' in params and params['adults'] > 1:
                            # Kiểm tra xem giá đã là tổng hay chưa
                            if price_vnd < 5000000:  # Nếu giá < 5M, có thể là giá 1 người
                                price_vnd = price_vnd * passengers
                        
                        result = {
                            'price_vnd': price_vnd,
                            'currency': 'VND',
                            'route_type': 'roundtrip' if return_date else 'oneway',
                            'origin_iata': origin_iata,
                            'destination_iata': dest_iata,
                            'passengers': passengers,
                            'source': 'flightapi',
                            'departure_date': departure_date,
                            'return_date': return_date,
                            'raw_data': data
                        }
                        
                        # Lưu vào cache (TTL: 24 giờ = 86400 giây)
                        if CACHE_AVAILABLE:
                            cache_set(cache_key, result, ttl=86400)
                            logger.info(f"FlightAPI result cached for {origin_iata}->{dest_iata}")
                        
                        return result
            
            # Nếu không thành công, log và return None
            logger.warning(f"FlightAPI returned status {response.status_code}: {response.text[:200]}")
            error_result = {'price_vnd': 0, 'error': f'FlightAPI returned {response.status_code}'}
            
            # Cache error result với TTL ngắn hơn (1 giờ) để tránh retry quá nhiều
            if CACHE_AVAILABLE:
                cache_set(cache_key, error_result, ttl=3600)
            
            return error_result
            
        except Exception as e:
            logger.error(f"FlightAPI search error: {e}")
            error_result = {'price_vnd': 0, 'error': str(e)}
            
            # Cache error với TTL ngắn
            if CACHE_AVAILABLE:
                cache_set(cache_key, error_result, ttl=3600)
            
            return error_result
    
    def _search_via_travelpayouts(
        self,
        origin_iata: str,
        dest_iata: str,
        departure_date: str,
        return_date: Optional[str],
        passengers: int
    ) -> Dict[str, Any]:
        """Tìm kiếm qua Travelpayouts API"""
        # TODO: Implement actual API call
        # Hiện tại return estimate
        return self._estimate_price(origin_iata, dest_iata, 
                                    'roundtrip' if return_date else 'oneway', 
                                    passengers)
    
    def _estimate_price(
        self,
        origin_iata: str,
        dest_iata: str,
        route_type: str,
        passengers: int
    ) -> Dict[str, Any]:
        """
        Ước tính giá vé dựa trên khoảng cách giữa các sân bay
        
        Args:
            origin_iata: Mã IATA điểm đi
            dest_iata: Mã IATA điểm đến
            route_type: 'oneway' hoặc 'roundtrip'
            passengers: Số hành khách
        """
        # Bảng giá ước tính (VNĐ) - một chiều, 1 người
        BASE_PRICES = {
            ('HAN', 'SGN'): 2000000,  # Hà Nội - Sài Gòn: 2M
            ('HAN', 'DAD'): 1500000,  # Hà Nội - Đà Nẵng: 1.5M
            ('DAD', 'SGN'): 1500000,  # Đà Nẵng - Sài Gòn: 1.5M
            ('HAN', 'CXR'): 2500000,  # Hà Nội - Nha Trang: 2.5M
            ('SGN', 'PQC'): 2000000,  # Sài Gòn - Phú Quốc: 2M
        }
        
        # Tìm giá trong bảng
        route_key = (origin_iata, dest_iata)
        reverse_key = (dest_iata, origin_iata)
        
        base_price = BASE_PRICES.get(route_key) or BASE_PRICES.get(reverse_key)
        
        if not base_price:
            # Ước tính mặc định: 1.5M VNĐ
            base_price = 1500000
        
        # Tính giá theo route type
        if route_type == 'roundtrip':
            total_price = base_price * 2 * passengers
        else:
            total_price = base_price * passengers
        
        return {
            'price_vnd': total_price,
            'currency': 'VND',
            'route_type': route_type,
            'origin_iata': origin_iata,
            'destination_iata': dest_iata,
            'passengers': passengers,
            'source': 'estimated',
            'base_price_per_person': base_price
        }


# Singleton instance
_flight_tools = None

def get_flight_tools() -> FlightTools:
    """Get singleton FlightTools instance"""
    global _flight_tools
    if _flight_tools is None:
        _flight_tools = FlightTools()
    return _flight_tools

