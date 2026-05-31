"""
SerpAPI Tools - Công cụ search Google qua SerpAPI
==================================================
- Tìm kiếm chuyến bay (Google Flights)
- Tìm kiếm khách sạn (Google Hotels)
- Tìm kiếm nhà hàng (Google Search)
"""

import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import concurrent.futures

logger = logging.getLogger(__name__)
EXTERNAL_API_TIMEOUT_SECONDS = 5.0

# Lazy import để tránh lỗi nếu chưa cài đặt
try:
    from serpapi import GoogleSearch
    SERPAPI_AVAILABLE = True
except ImportError:
    SERPAPI_AVAILABLE = False
    logger.warning("serpapi not installed. Install with: pip install google-search-results")

# Import cache utility
try:
    from utils.cache import cache_get, cache_set, generate_cache_key
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False
    logger.warning("Cache utility not available, SerpAPI calls will not be cached")


class SerpAPITools:
    """Công cụ sử dụng SerpAPI để search Google"""
    
    def __init__(self):
        self.api_key = os.getenv('SERPAPI_API_KEY', '')
        
        if not self.api_key:
            logger.warning("SERPAPI_API_KEY not set. SerpAPI tools will be disabled.")
        
        if not SERPAPI_AVAILABLE:
            logger.warning("serpapi package not installed. SerpAPI tools will be disabled.")

    def _run_search_with_timeout(self, params: Dict[str, Any]) -> Dict[str, Any]:
        def _execute() -> Dict[str, Any]:
            search = GoogleSearch(params)
            return search.get_dict()

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(_execute)
            return future.result(timeout=EXTERNAL_API_TIMEOUT_SECONDS)
    
    def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str] = None,
        currency: str = "VND",
        language: str = "vi",
        country: str = "vn"
    ) -> Dict[str, Any]:
        """
        Tìm kiếm chuyến bay qua Google Flights (SerpAPI)
        
        Args:
            origin: Mã sân bay đi (IATA code, e.g., 'SGN', 'HAN')
            destination: Mã sân bay đến (IATA code)
            departure_date: Ngày đi (YYYY-MM-DD)
            return_date: Ngày về (YYYY-MM-DD, optional)
            currency: Tiền tệ (default: VND)
            language: Ngôn ngữ (default: vi)
            country: Quốc gia (default: vn)
            
        Returns:
            Dict với flights data từ SerpAPI
        """
        if not self.api_key or not SERPAPI_AVAILABLE:
            return {
                'error': 'SerpAPI not configured',
                'flights': []
            }
        
        # Check cache first (cache for 6 hours - flight prices change frequently)
        if CACHE_AVAILABLE:
            cache_key = generate_cache_key('serpapi_flights', origin, destination, departure_date, return_date)
            cached_result = cache_get(cache_key)
            if cached_result:
                logger.debug(f"Cache hit for flights: {origin} -> {destination} on {departure_date}")
                return cached_result
        
        try:
            params = {
                "engine": "google_flights",
                "departure_id": origin,
                "arrival_id": destination,
                "outbound_date": departure_date,
                "currency": currency,
                "hl": language,
                "gl": country,
                "api_key": self.api_key
            }
            
            if return_date:
                params["return_date"] = return_date
            
            results = self._run_search_with_timeout(params)
            
            # Parse results
            flights_data = {
                'best_flights': results.get('best_flights', []),
                'other_flights': results.get('other_flights', []),
                'price_insights': results.get('price_insights', {}),
                'airports': results.get('airports', []),
                'search_metadata': results.get('search_metadata', {})
            }
            
            # Extract best flight info (fallback to other_flights if best_flights is empty)
            raw_best_flights = flights_data.get('best_flights') or []
            raw_other_flights = flights_data.get('other_flights') or []
            candidate_flights = raw_best_flights or raw_other_flights

            best_flights = []
            for flight in candidate_flights[:5]:  # Top 5
                # Extract airline name - có thể là string hoặc dict
                airline = flight.get('airline', 'Unknown')
                if isinstance(airline, dict):
                    airline = airline.get('name', airline.get('title', 'Unknown'))
                elif not airline or airline == 'Unknown':
                    # Thử lấy từ flights segments
                    flights_list = flight.get('flights', [])
                    if flights_list:
                        first_flight = flights_list[0]
                        airline = first_flight.get('airline', {}).get('name', 'Unknown') if isinstance(first_flight.get('airline'), dict) else first_flight.get('airline', 'Unknown')
                
                # Nếu vẫn Unknown, thử nhận diện từ flight number
                if airline == 'Unknown' or not airline:
                    flights_list = flight.get('flights', [])
                    if flights_list:
                        first_flight = flights_list[0]
                        flight_number = first_flight.get('flight_number', '')
                        if flight_number:
                            # Nhận diện từ mã IATA airline code
                            airline_codes = {
                                'VJ': 'VietJet',
                                'VN': 'Vietnam Airlines',
                                'QH': 'Bamboo Airways',
                                'BL': 'Pacific Airlines',
                                'JQ': 'Jetstar Pacific'
                            }
                            # Lấy 2 ký tự đầu của flight number (có thể có space: "VJ 312" -> "VJ")
                            code = flight_number.replace(' ', '')[:2].upper()
                            if code in airline_codes:
                                airline = airline_codes[code]
                
                # Extract flight number
                flight_number = ''
                flights_list = flight.get('flights', [])
                if flights_list:
                    first_flight = flights_list[0]
                    flight_number = first_flight.get('flight_number', '')
                
                # Extract departure/arrival info
                dep_airport = {}
                arr_airport = {}
                if flights_list:
                    first_flight = flights_list[0]
                    dep_airport = first_flight.get('departure_airport', {})
                    arr_airport = first_flight.get('arrival_airport', {})
                
                best_flights.append({
                    'price': flight.get('price', 0),
                    'airline': airline,
                    'airline_logo': flight.get('airline_logo', ''),
                    'duration': flight.get('total_duration', 0),
                    'flight_number': flight_number,
                    'departure_time': dep_airport.get('time', ''),
                    'arrival_time': arr_airport.get('time', ''),
                    'departure_airport': dep_airport,
                    'arrival_airport': arr_airport,
                    'type': flight.get('type', 'Round trip'),
                    'carbon_emissions': flight.get('carbon_emissions', {}),
                    'source': 'serpapi',
                    'raw_flight': flight  # Lưu raw để parse thêm nếu cần
                })
            
            result = {
                'status': 'success',
                'flights': best_flights,
                'lowest_price': flights_data.get('price_insights', {}).get('lowest_price', 0),
                'typical_price_range': flights_data.get('price_insights', {}).get('typical_price_range', []),
                'raw_data': flights_data
            }
            
            # Cache result for 6 hours
            if CACHE_AVAILABLE:
                cache_key = generate_cache_key('serpapi_flights', origin, destination, departure_date, return_date)
                cache_set(cache_key, result, ttl=21600)
            
            return result
            
        except concurrent.futures.TimeoutError:
            logger.error("SerpAPI flights timeout sau %.1f giây", EXTERNAL_API_TIMEOUT_SECONDS)
            return {
                'error': f'SerpAPI timeout sau {EXTERNAL_API_TIMEOUT_SECONDS:.1f} giây',
                'flights': []
            }
        except Exception as e:
            logger.error(f"SerpAPI flights search error: {e}", exc_info=True)
            return {
                'error': str(e),
                'flights': []
            }
    
    def search_hotels(
        self,
        location: str,
        check_in: str,
        check_out: str,
        adults: int = 2,
        currency: str = "VND",
        language: str = "vi",
        country: str = "vn"
    ) -> Dict[str, Any]:
        """
        Tìm kiếm khách sạn qua Google Hotels (SerpAPI)
        
        Args:
            location: Địa điểm (tên thành phố hoặc địa chỉ)
            check_in: Ngày nhận phòng (YYYY-MM-DD)
            check_out: Ngày trả phòng (YYYY-MM-DD)
            adults: Số người lớn (default: 2)
            currency: Tiền tệ (default: VND)
            language: Ngôn ngữ (default: vi)
            country: Quốc gia (default: vn)
            
        Returns:
            Dict với hotels data từ SerpAPI
        """
        # Check cache first (cache for 6 hours - hotel prices change frequently)
        if CACHE_AVAILABLE:
            cache_key = generate_cache_key('serpapi_hotels', location, check_in, check_out, adults)
            cached_result = cache_get(cache_key)
            if cached_result:
                logger.debug(f"Cache hit for hotels: {location} from {check_in} to {check_out}")
                return cached_result
        if not self.api_key or not SERPAPI_AVAILABLE:
            return {
                'error': 'SerpAPI not configured',
                'hotels': []
            }
        
        try:
            params = {
                "engine": "google_hotels",
                "q": location,
                "check_in_date": check_in,
                "check_out_date": check_out,
                "adults": adults,
                "currency": currency,
                "hl": language,
                "gl": country,
                "api_key": self.api_key
            }
            
            results = self._run_search_with_timeout(params)
            
            # Debug: Log available keys in first hotel to see what data is available
            hotels_list = results.get('properties', [])
            if hotels_list and len(hotels_list) > 0:
                first_hotel = hotels_list[0]
                logger.debug(f"SerpAPI hotel data keys: {list(first_hotel.keys())}")
                logger.debug(f"Sample hotel data: {first_hotel}")
            
            # Parse hotels from results
            
            hotels = []
            for idx, hotel in enumerate(hotels_list[:10]):  # Top 10
                price_info = hotel.get('rate_per_night', {}) or {}

                # SerpAPI schema có thể dùng các key khác nhau cho tên khách sạn
                # Ưu tiên title -> name -> property_name, sau đó mới fallback sang các field khác
                hotel_name = (
                    hotel.get('title')
                    or hotel.get('name')
                    or hotel.get('property_name')
                    or hotel.get('address')
                    or hotel.get('link')
                )

                # Nếu vẫn không có tên rõ ràng, log lại để debug và dùng tên fallback thân thiện
                if not hotel_name:
                    try:
                        logger.warning(
                            "SerpAPI hotel without name fields: keys=%s", list(hotel.keys())
                        )
                    except Exception:
                        # Tránh làm hỏng response nếu logger gặp vấn đề
                        pass
                    hotel_name = f"Khách sạn {idx + 1} - {location}"

                # Giá phòng: ưu tiên extracted_lowest (numeric), fallback parse từ lowest (string)
                price_per_night = 0
                if isinstance(price_info, dict):
                    extracted_lowest = price_info.get('extracted_lowest')
                    if isinstance(extracted_lowest, (int, float)):
                        price_per_night = extracted_lowest
                    else:
                        lowest_str = price_info.get('lowest')
                        if isinstance(lowest_str, str):
                            digits = ''.join(ch for ch in lowest_str if ch.isdigit())
                            if digits:
                                try:
                                    price_per_night = int(digits)
                                except ValueError:
                                    price_per_night = 0

                # Rating: docs dùng overall_rating, fallback về rating nếu có
                rating_value = hotel.get('overall_rating')
                if rating_value is None:
                    rating_value = hotel.get('rating', 0)

                # Ảnh thumbnail: ưu tiên field thumbnail, fallback ảnh đầu tiên trong images
                thumbnail = hotel.get('thumbnail', '')
                images = hotel.get('images') or []
                if not thumbnail and images and isinstance(images, list):
                    first_image = images[0] or {}
                    thumbnail = first_image.get('thumbnail') or first_image.get('original_image', '')
                
                # Lấy tất cả ảnh (nếu có)
                all_images = []
                if images and isinstance(images, list):
                    for img in images:
                        if isinstance(img, dict):
                            img_url = img.get('original_image') or img.get('thumbnail') or img.get('image')
                            if img_url:
                                all_images.append(img_url)
                        elif isinstance(img, str):
                            all_images.append(img)
                if thumbnail and thumbnail not in all_images:
                    all_images.insert(0, thumbnail)

                gps = hotel.get('gps_coordinates') or {}
                
                # Lấy thông tin bổ sung từ SerpAPI
                # Phone có thể ở trong hotel data hoặc trong extensions
                phone = hotel.get('phone') or hotel.get('phone_number') or ''
                if not phone:
                    extensions = hotel.get('extensions') or []
                    for ext in extensions:
                        if isinstance(ext, str) and any(char.isdigit() for char in ext):
                            # Có thể là số điện thoại
                            phone = ext
                            break
                
                # Website/URL
                website = hotel.get('website') or hotel.get('link') or ''
                
                # Description
                description = hotel.get('description') or hotel.get('snippet') or ''
                
                # Email (thường không có trong SerpAPI do privacy)
                email = hotel.get('email') or ''

                hotels.append({
                    'name': hotel_name,
                    'price_per_night': price_per_night,
                    'rating': rating_value or 0,
                    'reviews': hotel.get('reviews', 0),
                    'address': hotel.get('address', ''),
                    'thumbnail': thumbnail,
                    'images': all_images,  # Tất cả ảnh
                    'link': hotel.get('link', ''),
                    'website': website,
                    'phone': phone,
                    'email': email,
                    'description': description,
                    'amenities': hotel.get('amenities', []),
                    'hotel_class': hotel.get('extracted_hotel_class') or hotel.get('hotel_class'),
                    'latitude': gps.get('latitude'),
                    'longitude': gps.get('longitude'),
                    'source': 'serpapi'
                })
            
            result = {
                'status': 'success',
                'hotels': hotels,
                'location': location,
                'raw_data': results
            }
            
            # Cache result for 6 hours
            if CACHE_AVAILABLE:
                cache_key = generate_cache_key('serpapi_hotels', location, check_in, check_out, adults)
                cache_set(cache_key, result, ttl=21600)
            
            return result
            
        except concurrent.futures.TimeoutError:
            logger.error("SerpAPI hotels timeout sau %.1f giây", EXTERNAL_API_TIMEOUT_SECONDS)
            return {
                'error': f'SerpAPI timeout sau {EXTERNAL_API_TIMEOUT_SECONDS:.1f} giây',
                'hotels': []
            }
        except Exception as e:
            logger.error(f"SerpAPI hotels search error: {e}", exc_info=True)
            return {
                'error': str(e),
                'hotels': []
            }
    
    def search_restaurants(
        self,
        location: str,
        query: Optional[str] = None,
        language: str = "vi",
        country: str = "vn",
        num_results: int = 10
    ) -> Dict[str, Any]:
        """
        Tìm kiếm nhà hàng qua Google Search (SerpAPI)
        
        Args:
            location: Địa điểm (tên thành phố)
            query: Từ khóa tìm kiếm (optional, default: "nhà hàng")
            language: Ngôn ngữ (default: vi)
            country: Quốc gia (default: vn)
            num_results: Số kết quả (default: 10)
            
        Returns:
            Dict với restaurants data từ SerpAPI
        """
        if not self.api_key or not SERPAPI_AVAILABLE:
            return {
                'error': 'SerpAPI not configured',
                'restaurants': []
            }
        
        # Check cache first (cache for 12 hours - restaurants don't change often)
        if CACHE_AVAILABLE:
            search_query = query or f"nhà hàng quán ăn ẩm thực {location}"
            cache_key = generate_cache_key('serpapi_restaurants', location, search_query, num_results)
            cached_result = cache_get(cache_key)
            if cached_result:
                logger.debug(f"Cache hit for restaurants: {location} - {search_query}")
                return cached_result
        
        try:
            # Cải thiện query để cụ thể hơn và tránh kết quả không liên quan
            if not query:
                search_query = f"nhà hàng quán ăn ẩm thực {location}"
            else:
                # Đảm bảo query có từ khóa về nhà hàng/ăn uống
                query_lower = query.lower()
                if not any(keyword in query_lower for keyword in ['nhà hàng', 'quán', 'ăn', 'ẩm thực', 'restaurant', 'food']):
                    search_query = f"nhà hàng {query} {location}"
                else:
                    search_query = f"{query} {location}"
            
            # Từ khóa cần loại bỏ (bệnh viện, cơ sở y tế, v.v.)
            exclude_keywords = [
                'bệnh viện', 'hospital', 'phòng khám', 'clinic', 'y tế', 'medical',
                'nhà thuốc', 'pharmacy', 'dược', 'drugstore',
                'trường học', 'school', 'đại học', 'university',
                'ngân hàng', 'bank', 'atm',
                'công ty', 'company', 'doanh nghiệp', 'enterprise'
            ]
            
            params = {
                "engine": "google",
                "q": search_query,
                "location": location,
                "hl": language,
                "gl": country,
                "api_key": self.api_key,
                "num": num_results * 2  # Lấy nhiều hơn để filter
            }
            
            results = self._run_search_with_timeout(params)
            
            restaurants = []

            # Prefer local_results (Google Local / map pack) when available
            local_results = results.get('local_results', []) or []
            for local in local_results:
                if len(restaurants) >= num_results:
                    break
                    
                title = local.get('title', '').lower()
                description = (local.get('description') or local.get('snippet', '')).lower()
                
                # Filter: Loại bỏ các kết quả không phải nhà hàng
                if any(exclude in title or exclude in description for exclude in exclude_keywords):
                    logger.debug(f"Filtered out non-restaurant result: {local.get('title', '')}")
                    continue
                
                gps = local.get('gps_coordinates') or {}
                links = local.get('links') or {}
                
                # Extract price level và convert sang format chuẩn
                price_level = local.get('price') or local.get('price_level', '')
                price_level_str = str(price_level).lower()
                if '₫' in price_level_str or 'đồng' in price_level_str:
                    # Có thể có giá trong price_level
                    price_level = price_level_str
                elif not price_level:
                    price_level = 'medium'  # Default
                
                restaurants.append({
                    'name': local.get('title', ''),
                    'description': local.get('description') or local.get('snippet', ''),
                    'link': local.get('website') or links.get('website', ''),
                    'rating': local.get('rating', 0),
                    'reviews': local.get('reviews', 0),
                    'address': local.get('address', location),
                    'phone': local.get('phone') or links.get('phone', ''),
                    'price_level': price_level,
                    'thumbnail': local.get('thumbnail', ''),
                    'latitude': gps.get('latitude'),
                    'longitude': gps.get('longitude'),
                    'source': 'serpapi_local'
                })

            # Parse restaurants from organic results as secondary source
            organic_results = results.get('organic_results', []) or []
            existing_names = {r.get('name', '').lower() for r in restaurants}
            
            for result in organic_results:
                if len(restaurants) >= num_results:
                    break
                    
                # Extract restaurant info
                title = result.get('title', '')
                if not title:
                    continue
                    
                title_lower = title.lower()
                if title_lower in existing_names:
                    continue
                
                snippet = (result.get('snippet', '') or '').lower()
                
                # Filter: Loại bỏ các kết quả không phải nhà hàng
                if any(exclude in title_lower or exclude in snippet for exclude in exclude_keywords):
                    logger.debug(f"Filtered out non-restaurant result: {title}")
                    continue
                
                link = result.get('link', '')
                
                # Try to extract rating if available
                rating = None
                reviews = None
                
                # Check in rich_snippet if available
                rich_snippet = result.get('rich_snippet', {})
                if rich_snippet:
                    top = rich_snippet.get('top', {})
                    if top:
                        extensions = top.get('extensions') or []
                        first_ext = extensions[0] if extensions else None
                        rating = first_ext
                        if isinstance(rating, str) and '★' in rating:
                            try:
                                rating = float(rating.split('★')[0].strip())
                            except Exception:
                                rating = None
                
                restaurants.append({
                    'name': title,
                    'description': result.get('snippet', ''),
                    'link': link,
                    'rating': rating,
                    'reviews': reviews,
                    'address': location,
                    'price_level': 'medium',  # Default nếu không có
                    'source': 'serpapi'
                })
                existing_names.add(title_lower)

            result = {
                'status': 'success',
                'restaurants': restaurants[:num_results],
                'location': location,
                'query': search_query
            }
            
            # Cache result for 12 hours
            if CACHE_AVAILABLE:
                cache_key = generate_cache_key('serpapi_restaurants', location, search_query, num_results)
                cache_set(cache_key, result, ttl=43200)
            
            return result
            
        except concurrent.futures.TimeoutError:
            logger.error("SerpAPI restaurants timeout sau %.1f giây", EXTERNAL_API_TIMEOUT_SECONDS)
            return {
                'error': f'SerpAPI timeout sau {EXTERNAL_API_TIMEOUT_SECONDS:.1f} giây',
                'restaurants': []
            }
        except Exception as e:
            logger.error(f"SerpAPI restaurants search error: {e}", exc_info=True)
            return {
                'error': str(e),
                'restaurants': []
            }


# Singleton instance
_serpapi_tools = None

def get_serpapi_tools() -> SerpAPITools:
    """Get singleton SerpAPITools instance"""
    global _serpapi_tools
    if _serpapi_tools is None:
        _serpapi_tools = SerpAPITools()
    return _serpapi_tools

