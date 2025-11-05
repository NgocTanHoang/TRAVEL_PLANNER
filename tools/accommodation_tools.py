"""
Accommodation Tools - Công cụ lưu trú
======================================
- Tìm kiếm khách sạn
- Tính giá phòng
- Lọc theo tiêu chí (giá, sao, vị trí)
"""
import logging
from typing import Dict, Any, Optional, List
import requests
import os
import json
from pathlib import Path

# Import caching utilities
try:
    from utils.cache import cache_get, cache_set, generate_cache_key, cached
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False

logger = logging.getLogger(__name__)


class AccommodationTools:
    """Công cụ lưu trú cho Accommodation Agent"""
    
    def __init__(self):
        self.travelpayouts_token = os.getenv('TRAVELPAYOUTS_TOKEN', '')
        self.base_url = "https://api.travelpayouts.com"
        
        # SerpAPI for Google Hotels
        try:
            from tools.serpapi_tools import get_serpapi_tools
            self.serpapi = get_serpapi_tools()
        except Exception as e:
            logger.warning(f"SerpAPI tools not available: {e}")
            self.serpapi = None
        
        # Load fallback data từ traveloka_hotels_data.json nếu có
        self.fallback_data = self._load_fallback_data()
    
    def _load_fallback_data(self) -> Dict[str, List[Dict]]:
        """Load dữ liệu khách sạn từ file JSON"""
        try:
            json_path = Path(__file__).parent.parent / 'traveloka_hotels_data.json'
            if json_path.exists():
                with open(json_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Cannot load fallback hotel data: {e}")
        return {}
    
    def search_hotels(
        self,
        city: str,
        check_in: str,
        check_out: str,
        guests: int = 2,
        rooms: int = 1,
        min_price: Optional[int] = None,
        max_price: Optional[int] = None,
        stars: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Tìm kiếm khách sạn
        
        Args:
            city: Tên thành phố
            check_in: Ngày nhận phòng (YYYY-MM-DD)
            check_out: Ngày trả phòng (YYYY-MM-DD)
            guests: Số khách
            rooms: Số phòng
            min_price: Giá tối thiểu (VNĐ)
            max_price: Giá tối đa (VNĐ)
            stars: Số sao (1-5)
            
        Returns:
            List các khách sạn
        """
        hotels = []
        
        # Ưu tiên SerpAPI (Google Hotels) - chính xác nhất
        if self.serpapi and self.serpapi.api_key:
            try:
                serpapi_result = self.serpapi.search_hotels(
                    city, check_in, check_out, guests
                )
                
                if serpapi_result.get('status') == 'success' and serpapi_result.get('hotels'):
                    # Convert format từ SerpAPI sang format chuẩn
                    for hotel in serpapi_result['hotels']:
                        hotels.append({
                            'name': hotel.get('name', 'Unknown'),
                            'price_per_night': hotel.get('price_per_night', 0),
                            'stars': self._extract_stars_from_name(hotel.get('name', '')),
                            'rating': hotel.get('rating', 0),
                            'reviews': hotel.get('reviews', 0),
                            'address': hotel.get('address', city),
                            'image_url': hotel.get('thumbnail', ''),
                            'link': hotel.get('link', ''),
                            'amenities': hotel.get('amenities', []),
                            'source': 'serpapi'
                        })
                    logger.info(f"Found {len(hotels)} hotels from SerpAPI")
            except Exception as e:
                logger.warning(f"SerpAPI hotels search failed: {e}")
        
        # Fallback: Travelpayouts API
        if len(hotels) < 5 and self.travelpayouts_token:
            api_hotels = self._search_via_api(city, check_in, check_out, guests, rooms)
            hotels.extend(api_hotels)
        
        # Fallback cuối: Từ fallback data
        if len(hotels) < 5:
            fallback_hotels = self._search_fallback_data(
                city, min_price, max_price, stars
            )
            hotels.extend(fallback_hotels)
        
        # Lọc theo tiêu chí
        hotels = self._filter_hotels(hotels, min_price, max_price, stars)
        
        # Sắp xếp theo giá
        hotels.sort(key=lambda x: x.get('price_per_night', float('inf')))
        
        return hotels[:20]  # Trả về tối đa 20 kết quả
    
    def _search_via_api(
        self,
        city: str,
        check_in: str,
        check_out: str,
        guests: int,
        rooms: int
    ) -> List[Dict[str, Any]]:
        """Tìm kiếm qua Travelpayouts API (Hotellook)"""
        # TODO: Implement actual API call
        return []
    
    def _search_fallback_data(
        self,
        city: str,
        min_price: Optional[int],
        max_price: Optional[int],
        stars: Optional[int]
    ) -> List[Dict[str, Any]]:
        """Tìm kiếm trong fallback data"""
        city_key = city.lower().strip()
        hotels = self.fallback_data.get(city_key, [])
        
        result = []
        for hotel in hotels:
            # Convert sang format chuẩn
            hotel_data = {
                'name': hotel.get('name', 'Unknown'),
                'price_per_night': hotel.get('price', 0),
                'stars': hotel.get('stars', 0),
                'rating': hotel.get('rating', 0),
                'address': hotel.get('address', ''),
                'source': 'fallback'
            }
            result.append(hotel_data)
        
        return result
    
    def _extract_stars_from_name(self, name: str) -> int:
        """Extract số sao từ tên khách sạn (nếu có)"""
        # Tìm pattern như "5 sao", "5-star", "5*"
        import re
        patterns = [
            r'(\d+)\s*sao',
            r'(\d+)\s*star',
            r'(\d+)\s*\*'
        ]
        for pattern in patterns:
            match = re.search(pattern, name, re.IGNORECASE)
            if match:
                return int(match.group(1))
        return 0
    
    def _filter_hotels(
        self,
        hotels: List[Dict],
        min_price: Optional[int],
        max_price: Optional[int],
        stars: Optional[int]
    ) -> List[Dict]:
        """Lọc khách sạn theo tiêu chí"""
        filtered = []
        
        for hotel in hotels:
            price = hotel.get('price_per_night', 0)
            hotel_stars = hotel.get('stars', 0)
            
            # Lọc giá
            if min_price and price < min_price:
                continue
            if max_price and price > max_price:
                continue
            
            # Lọc sao
            if stars and hotel_stars != stars:
                continue
            
            filtered.append(hotel)
        
        return filtered
    
    def calculate_total_accommodation_cost(
        self,
        price_per_night: float,
        nights: int,
        rooms: int = 1
    ) -> float:
        """
        Tính tổng chi phí lưu trú
        
        Args:
            price_per_night: Giá một đêm (VNĐ)
            nights: Số đêm
            rooms: Số phòng
            
        Returns:
            Tổng chi phí (VNĐ)
        """
        return round(price_per_night * nights * rooms)


# Singleton instance
_accommodation_tools = None

def get_accommodation_tools() -> AccommodationTools:
    """Get singleton AccommodationTools instance"""
    global _accommodation_tools
    if _accommodation_tools is None:
        _accommodation_tools = AccommodationTools()
    return _accommodation_tools

