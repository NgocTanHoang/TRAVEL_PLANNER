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

logger = logging.getLogger(__name__)

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
            
            search = GoogleSearch(params)
            results = search.get_dict()
            
            # Parse results
            flights_data = {
                'best_flights': results.get('best_flights', []),
                'other_flights': results.get('other_flights', []),
                'price_insights': results.get('price_insights', {}),
                'airports': results.get('airports', []),
                'search_metadata': results.get('search_metadata', {})
            }
            
            # Extract best flight info
            best_flights = []
            for flight in flights_data['best_flights'][:5]:  # Top 5
                best_flights.append({
                    'price': flight.get('price', 0),
                    'airline': flight.get('airline', 'Unknown'),
                    'airline_logo': flight.get('airline_logo', ''),
                    'duration': flight.get('total_duration', 0),
                    'flight_number': flight.get('flights', [{}])[0].get('flight_number', ''),
                    'departure_time': flight.get('flights', [{}])[0].get('departure_airport', {}).get('time', ''),
                    'arrival_time': flight.get('flights', [{}])[0].get('arrival_airport', {}).get('time', ''),
                    'type': flight.get('type', 'Round trip'),
                    'carbon_emissions': flight.get('carbon_emissions', {}),
                    'source': 'serpapi'
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
            
            search = GoogleSearch(params)
            results = search.get_dict()
            
            # Parse hotels from results
            hotels_list = results.get('properties', [])
            
            hotels = []
            for hotel in hotels_list[:10]:  # Top 10
                price_info = hotel.get('rate_per_night', {})
                hotels.append({
                    'name': hotel.get('title', 'Unknown Hotel'),
                    'price_per_night': price_info.get('low', 0) if isinstance(price_info, dict) else 0,
                    'rating': hotel.get('rating', 0),
                    'reviews': hotel.get('reviews', 0),
                    'address': hotel.get('address', ''),
                    'thumbnail': hotel.get('thumbnail', ''),
                    'link': hotel.get('link', ''),
                    'amenities': hotel.get('amenities', []),
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
            search_query = query or f"nhà hàng {location}"
            cache_key = generate_cache_key('serpapi_restaurants', location, search_query, num_results)
            cached_result = cache_get(cache_key)
            if cached_result:
                logger.debug(f"Cache hit for restaurants: {location} - {search_query}")
                return cached_result
        
        try:
            search_query = query or f"nhà hàng {location}"
            
            params = {
                "engine": "google",
                "q": search_query,
                "location": location,
                "hl": language,
                "gl": country,
                "api_key": self.api_key,
                "num": num_results
            }
            
            search = GoogleSearch(params)
            results = search.get_dict()
            
            # Parse restaurants from organic results
            organic_results = results.get('organic_results', [])
            
            restaurants = []
            for result in organic_results[:num_results]:
                # Extract restaurant info
                title = result.get('title', '')
                snippet = result.get('snippet', '')
                link = result.get('link', '')
                
                # Try to extract rating if available
                rating = None
                reviews = None
                
                # Check in rich_snippet if available
                rich_snippet = result.get('rich_snippet', {})
                if rich_snippet:
                    top = rich_snippet.get('top', {})
                    if top:
                        rating = top.get('extensions', [{}])[0] if top.get('extensions') else None
                        if isinstance(rating, str) and '★' in rating:
                            try:
                                rating = float(rating.split('★')[0].strip())
                            except:
                                pass
                
                restaurants.append({
                    'name': title,
                    'description': snippet,
                    'link': link,
                    'rating': rating,
                    'reviews': reviews,
                    'address': location,
                    'source': 'serpapi'
                })
            
            # Also check for local pack (map results)
            local_results = results.get('local_results', [])
            for local in local_results[:5]:
                restaurants.append({
                    'name': local.get('title', ''),
                    'description': local.get('snippet', ''),
                    'link': local.get('website', ''),
                    'rating': local.get('rating', 0),
                    'reviews': local.get('reviews', 0),
                    'address': local.get('address', location),
                    'phone': local.get('phone', ''),
                    'price_level': local.get('price_level', ''),
                    'source': 'serpapi_local'
                })
            
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

