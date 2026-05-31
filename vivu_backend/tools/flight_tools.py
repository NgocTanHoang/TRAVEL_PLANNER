"""
Flight Tools - Công cụ vé máy bay
===================================
- Chuyển đổi tên thành phố sang mã IATA
- Tìm kiếm giá vé máy bay
- Tính giá khứ hồi hoặc một chiều

Thứ tự ưu tiên API:
1. Amadeus API (nếu có) - Dữ liệu GDS chính thức
2. FlightAPI - API chuyên dụng, dữ liệu từ 700+ OTA (ưu tiên chính)
3. SerpAPI (Google Flights) - Fallback nếu FlightAPI không khả dụng
4. Travelpayouts API (nếu có)

Lưu ý về FlightAPI:
- Gói free có giới hạn 30 lượt/tháng
- Mỗi request tốn 2 credits
- Nên sử dụng caching để tránh gọi API nhiều lần cho cùng một request
"""
import logging
from typing import Dict, Any, Optional, List
import requests
import os
from datetime import datetime, timedelta
import hashlib
import json
import concurrent.futures

logger = logging.getLogger(__name__)
EXTERNAL_API_TIMEOUT_SECONDS = 5.0

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
        
        # Amadeus API
        try:
            from tools.amadeus_tools import get_amadeus_tools
            self.amadeus = get_amadeus_tools()
        except Exception as e:
            logger.warning(f"Amadeus tools not available: {e}")
            self.amadeus = None
        
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
        
        # Danh sách các API theo thứ tự ưu tiên
        api_chain = []
        
        # Ưu tiên 1: Amadeus API - Dữ liệu GDS chính thức, có thể đặt chỗ
        if self.amadeus and self.amadeus.is_available():
            api_chain.append(('amadeus', self._search_via_amadeus))
        
        # Ưu tiên 2: FlightAPI - API chuyên dụng, dữ liệu từ 700+ OTA
        if self.flightapi_key:
            api_chain.append(('flightapi', self._search_via_flightapi))
        
        # Ưu tiên 3: SerpAPI (Google Flights) - fallback nếu FlightAPI không khả dụng
        if self.serpapi and self.serpapi.api_key:
            api_chain.append(('serpapi', self._search_via_serpapi))
        
        # Ưu tiên 4: Travelpayouts API
        if self.travelpayouts_token:
            api_chain.append(('travelpayouts', self._search_via_travelpayouts))
        
        # Thử từng API theo thứ tự ưu tiên
        last_error = None
        for api_name, api_func in api_chain:
            try:
                logger.info(f"Trying {api_name} for {origin_iata}->{dest_iata}")
                result = api_func(origin_iata, dest_iata, departure_date, return_date, passengers)
                
                # Kiểm tra kết quả hợp lệ
                if result and result.get('price_vnd') and result.get('price_vnd') > 0:
                    logger.info(f"✓ {api_name} succeeded for {origin_iata}->{dest_iata}")
                    return result
                else:
                    logger.warning(f"✗ {api_name} returned invalid result, trying next API...")
                    
            except (requests.exceptions.Timeout, concurrent.futures.TimeoutError) as e:
                logger.warning(f"Provider {api_name} timed out after {EXTERNAL_API_TIMEOUT_SECONDS:.1f}s: {e}. Falling back.")
                last_error = e
                continue
            except requests.exceptions.RequestException as e:
                logger.warning(f"✗ {api_name} network error: {e}, trying next API...")
                last_error = e
                continue
            except Exception as e:
                logger.warning(f"✗ {api_name} error: {e}, trying next API...")
                last_error = e
                continue
        
        # Tất cả API đều fail, dùng ước tính
        logger.warning(f"All flight APIs failed for {origin_iata}->{dest_iata}, using estimate. Last error: {last_error}")
        return self._estimate_price(origin_iata, dest_iata, route_type, passengers)
    
    def _search_via_amadeus(
        self,
        origin_iata: str,
        dest_iata: str,
        departure_date: str,
        return_date: Optional[str],
        passengers: int
    ) -> Dict[str, Any]:
        """
        Tìm kiếm qua Amadeus API
        """
        if not self.amadeus or not self.amadeus.is_available():
            raise Exception("Amadeus API not configured or not available")
        
        amadeus_result = self.amadeus.search_flights(
            origin_iata, dest_iata, departure_date, return_date, passengers
        )
        
        if amadeus_result.get('status') == 'success' and amadeus_result.get('flights'):
            # Lấy chuyến bay tốt nhất (rẻ nhất)
            best_flight = min(amadeus_result['flights'], key=lambda x: x.get('price_vnd', float('inf')))
            
            return {
                'price_vnd': best_flight.get('price_vnd', 0),
                'currency': 'VND',
                'route_type': 'roundtrip' if return_date else 'oneway',
                'origin_iata': origin_iata,
                'destination_iata': dest_iata,
                'passengers': passengers,
                'source': 'amadeus',
                'airline': best_flight.get('segments', [{}])[0].get('carrierCode', 'Unknown') if best_flight.get('segments') else 'Unknown',
                'flight_number': best_flight.get('segments', [{}])[0].get('number', '') if best_flight.get('segments') else '',
                'all_flights': amadeus_result.get('flights', []),
                'lowest_price': best_flight.get('price_vnd', 0),
                'amadeus_id': best_flight.get('id', '')
            }
        
        raise Exception(f"Amadeus API returned no valid flights: {amadeus_result.get('error', 'Unknown error')}")
    
    def _search_via_serpapi(
        self,
        origin_iata: str,
        dest_iata: str,
        departure_date: str,
        return_date: Optional[str],
        passengers: int
    ) -> Dict[str, Any]:
        """
        Tìm kiếm qua SerpAPI (Google Flights)
        """
        if not self.serpapi or not self.serpapi.api_key:
            raise Exception("SerpAPI not configured")
        
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
                'route_type': 'roundtrip' if return_date else 'oneway',
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
        
        raise Exception(f"SerpAPI returned no valid flights: {serpapi_result.get('error', 'Unknown error')}")
    
    def _search_via_flightapi(
        self,
        origin_iata: str,
        dest_iata: str,
        departure_date: str,
        return_date: Optional[str],
        passengers: int,
        children: int = 0,
        infants: int = 0
    ) -> Dict[str, Any]:
        """
        Tìm kiếm giá vé máy bay qua FlightAPI.io
        
        Docs: https://docs.flightapi.io/flight-price-api
        
        API Endpoints:
        - Oneway: https://api.flightapi.io/oneway/{api_key}
        - Roundtrip: https://api.flightapi.io/roundtrip/{api_key}
        
        Parameters (theo tài liệu):
        - departure_airport_code: Mã IATA sân bay đi
        - arrival_airport_code: Mã IATA sân bay đến
        - departure_date: Ngày đi (YYYY-MM-DD)
        - return_date: Ngày về (YYYY-MM-DD, chỉ cho roundtrip)
        - number_of_adults: Số người lớn
        - number_of_childrens: Số trẻ em
        - number_of_infants: Số trẻ sơ sinh
        - cabin_class: Hạng ghế (Economy, Business, First)
        
        Lưu ý:
        - Mỗi request thành công tốn 2 credits
        - Gói free có giới hạn 30 lượt/tháng
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
            'children': children,
            'infants': infants,
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
            # FlightAPI sử dụng URL path parameters, không phải query string
            # Format: /{api_key}/{departure_airport}/{arrival_airport}/{departure_date}/...
            currency = 'USD'  # Mặc định USD, sẽ convert sang VND sau
            
            if return_date:
                # Roundtrip: /roundtrip/{api_key}/{departure}/{arrival}/{departure_date}/{return_date}/{adults}/{children}/{infants}/{cabin}/{currency}
                endpoint = (
                    f'https://api.flightapi.io/roundtrip/'
                    f'{self.flightapi_key}/'
                    f'{origin_iata}/'
                    f'{dest_iata}/'
                    f'{departure_date}/'
                    f'{return_date}/'
                    f'{passengers}/'  # number_of_adults
                    f'{children}/'  # number_of_childrens
                    f'{infants}/'  # number_of_infants
                    f'Economy/'  # cabin_class
                    f'{currency}'
                )
            else:
                # Oneway: /oneway/{api_key}/{departure}/{arrival}/{departure_date}/{adults}/{children}/{infants}/{cabin}/{currency}
                endpoint = (
                    f'https://api.flightapi.io/oneway/'
                    f'{self.flightapi_key}/'
                    f'{origin_iata}/'
                    f'{dest_iata}/'
                    f'{departure_date}/'
                    f'{passengers}/'  # number_of_adults
                    f'{children}/'  # number_of_childrens
                    f'{infants}/'  # number_of_infants
                    f'Economy/'  # cabin_class
                    f'{currency}'
                )
            
            # Gửi request (không có params, tất cả đã ở trong URL)
            logger.debug(f"FlightAPI endpoint: {endpoint}")
            response = requests.get(endpoint, timeout=EXTERNAL_API_TIMEOUT_SECONDS)
            
            if response.status_code == 200:
                try:
                    data = response.json()
                except json.JSONDecodeError:
                    logger.error(f"FlightAPI returned invalid JSON: {response.text[:200]}")
                    raise Exception("FlightAPI returned invalid JSON response")
                
                # Parse response từ FlightAPI
                # Cấu trúc response có thể khác nhau, cần kiểm tra
                if isinstance(data, dict):
                    # Kiểm tra lỗi trong response
                    if data.get('error') or data.get('status') == 'error':
                        error_msg = data.get('error', data.get('message', 'Unknown error'))
                        logger.warning(f"FlightAPI returned error: {error_msg}")
                        raise Exception(f"FlightAPI error: {error_msg}")
                    
                    # FlightAPI response có cấu trúc:
                    # - data.itineraries[].pricing_options[].price.amount
                    # - data.itineraries[].cheapest_price (có thể có)
                    # - data.price (nếu có price trực tiếp)
                    price = 0
                    
                    # Lấy currency từ query
                    query = data.get('query', {})
                    currency_from_query = query.get('currency', 'USD').upper() if query else 'USD'
                    
                    # Thử lấy từ itineraries (danh sách chuyến bay)
                    if 'itineraries' in data and isinstance(data['itineraries'], list) and len(data['itineraries']) > 0:
                        # Lấy chuyến bay rẻ nhất
                        itineraries = data['itineraries']
                        prices_list = []
                        
                        for itin in itineraries:
                            # Thử lấy từ cheapest_price trước
                            cheapest = itin.get('cheapest_price')
                            if cheapest:
                                if isinstance(cheapest, dict):
                                    total = cheapest.get('amount') or cheapest.get('total') or 0
                                else:
                                    total = cheapest
                                if total > 0:
                                    prices_list.append((total, itin))
                                    continue
                            
                            # Nếu không có cheapest_price, tìm trong pricing_options
                            pricing_options = itin.get('pricing_options', [])
                            if pricing_options:
                                for option in pricing_options:
                                    price_obj = option.get('price', {})
                                    if isinstance(price_obj, dict):
                                        total = price_obj.get('amount') or price_obj.get('total') or 0
                                        if total > 0:
                                            prices_list.append((total, itin))
                                            break  # Lấy giá đầu tiên của itinerary này
                        
                        if prices_list:
                            # Lấy giá thấp nhất
                            best_price, best_itinerary = min(prices_list, key=lambda x: x[0])
                            price = best_price
                            logger.info(f"FlightAPI found {len(itineraries)} itineraries, lowest price: {price} {currency_from_query}")
                    # Thử các key có thể có cho price
                    elif 'price' in data:
                        price_obj = data.get('price', {})
                        if isinstance(price_obj, dict):
                            price = price_obj.get('total') or price_obj.get('amount') or price_obj.get('raw') or 0
                        else:
                            price = price_obj
                    else:
                        # Thử các key khác
                        price = (
                            data.get('totalPrice') or
                            data.get('total_price') or
                            data.get('fare', {}).get('total') or
                            data.get('lowest_price') or
                            0
                        )
                    
                    # Lấy currency từ response (ưu tiên từ query, sau đó từ root)
                    currency = currency_from_query if 'currency_from_query' in locals() else data.get('currency', 'USD').upper()
                    
                    # Debug: log response structure
                    logger.debug(f"FlightAPI response structure - keys: {list(data.keys())}, price found: {price > 0}, currency: {currency}")
                    if 'itineraries' in data:
                        logger.debug(f"FlightAPI itineraries count: {len(data.get('itineraries', []))}")
                    
                    # Convert sang VND nếu cần
                    if price > 0:
                        if currency == 'USD':
                            # Convert USD sang VND (tỷ giá ~25,000 VND/USD)
                            price_vnd = int(price * 25000)
                        elif currency == 'VND':
                            price_vnd = int(price)
                        else:
                            # Nếu currency không rõ, thử đoán dựa trên giá trị
                            # Giá VND thường > 1,000,000 cho chuyến bay nội địa
                            if price < 100:
                                price_vnd = int(price * 25000)  # Giả sử là USD
                            else:
                                price_vnd = int(price)  # Giả sử là VND
                        
                        # FlightAPI thường trả về giá tổng cho số người đã chỉ định
                        # Nhưng để an toàn, kiểm tra nếu giá quá thấp thì có thể là giá 1 người
                        total_passengers = passengers + children + infants
                        if total_passengers > 1:
                            # Nếu giá < 5M VND cho roundtrip hoặc < 2.5M cho oneway, có thể là giá 1 người
                            threshold = 5000000 if return_date else 2500000
                            if price_vnd < threshold:
                                price_vnd = price_vnd * total_passengers
                        
                        result = {
                            'price_vnd': price_vnd,
                            'currency': 'VND',
                            'route_type': 'roundtrip' if return_date else 'oneway',
                            'origin_iata': origin_iata,
                            'destination_iata': dest_iata,
                            'passengers': total_passengers,
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
        """
        Tìm kiếm qua Travelpayouts API
        
        Raises:
            Exception: Nếu API call thất bại
        """
        if not self.travelpayouts_token:
            raise Exception("Travelpayouts token not configured")
        
        # TODO: Implement actual Travelpayouts API call
        # Hiện tại raise exception để fallback sang estimate
        raise Exception("Travelpayouts API not implemented yet")
    
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
        # Giá dựa trên khoảng cách bay thực tế giữa các sân bay
        BASE_PRICES = {
            # Các route chính
            ('HAN', 'SGN'): 2000000,  # Hà Nội - Sài Gòn: 2M (khoảng cách bay ~1200km)
            ('SGN', 'HAN'): 2000000,  # Sài Gòn - Hà Nội: 2M
            ('HAN', 'DAD'): 1500000,  # Hà Nội - Đà Nẵng: 1.5M (khoảng cách bay ~650km)
            ('DAD', 'HAN'): 1500000,  # Đà Nẵng - Hà Nội: 1.5M
            ('DAD', 'SGN'): 1500000,  # Đà Nẵng - Sài Gòn: 1.5M (khoảng cách bay ~600km)
            ('SGN', 'DAD'): 1500000,  # Sài Gòn - Đà Nẵng: 1.5M
            ('HAN', 'CXR'): 2500000,  # Hà Nội - Nha Trang: 2.5M (khoảng cách bay ~1100km)
            ('CXR', 'HAN'): 2500000,  # Nha Trang - Hà Nội: 2.5M
            ('SGN', 'PQC'): 2000000,  # Sài Gòn - Phú Quốc: 2M (khoảng cách bay ~300km)
            ('PQC', 'SGN'): 2000000,  # Phú Quốc - Sài Gòn: 2M
            ('HAN', 'HPH'): 800000,   # Hà Nội - Hải Phòng: 800k (khoảng cách bay ~100km)
            ('HPH', 'HAN'): 800000,   # Hải Phòng - Hà Nội: 800k
            ('SGN', 'VCA'): 1200000,  # Sài Gòn - Cần Thơ: 1.2M (khoảng cách bay ~200km)
            ('VCA', 'SGN'): 1200000,  # Cần Thơ - Sài Gòn: 1.2M
        }
        
        # Khoảng cách bay giữa các sân bay (km) - để ước tính giá cho route mới
        AIRPORT_DISTANCES = {
            ('HAN', 'SGN'): 1200,
            ('SGN', 'HAN'): 1200,
            ('HAN', 'DAD'): 650,
            ('DAD', 'HAN'): 650,
            ('DAD', 'SGN'): 600,
            ('SGN', 'DAD'): 600,
            ('HAN', 'CXR'): 1100,
            ('CXR', 'HAN'): 1100,
            ('SGN', 'PQC'): 300,
            ('PQC', 'SGN'): 300,
            ('HAN', 'HPH'): 100,
            ('HPH', 'HAN'): 100,
            ('SGN', 'VCA'): 200,
            ('VCA', 'SGN'): 200,
        }
        
        # Tìm giá trong bảng
        route_key = (origin_iata, dest_iata)
        reverse_key = (dest_iata, origin_iata)
        
        base_price = BASE_PRICES.get(route_key) or BASE_PRICES.get(reverse_key)
        
        if not base_price:
            # Ước tính dựa trên khoảng cách bay
            flight_distance = AIRPORT_DISTANCES.get(route_key) or AIRPORT_DISTANCES.get(reverse_key)
            
            if flight_distance:
                # Công thức: 1,200 VNĐ/km cho khoảng cách < 500km, 1,500 VNĐ/km cho >= 500km
                # Tối thiểu 1.5M, tối đa 5M cho 1 người
                if flight_distance < 500:
                    base_price = max(flight_distance * 1200, 1500000)
                else:
                    base_price = max(flight_distance * 1500, 2000000)
                base_price = min(base_price, 5000000)  # Tối đa 5M
            else:
                # Ước tính mặc định: 2M VNĐ cho route nội địa dài
                base_price = 2000000
        
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

