"""
Planning Tools - Công cụ lập kế hoạch (Score-based, Geo-aware)
================================================================
- Tạo lịch trình hàng ngày với scoring và ranking thông minh
- Phân bổ hoạt động dựa trên khoảng cách, thời gian di chuyển
- Đề xuất nhà hàng theo địa điểm, giờ mở cửa, rating, giá
- Hỗ trợ 14+ phong cách du lịch với scoring profiles riêng
- Tích hợp với GeoTools, ActivitiesTools, VectorDB
- Cache để tối ưu performance
- Tương thích với mọi loại địa điểm (không gán cứng)
"""
import logging
from typing import Dict, Any, Optional, List, Tuple, Union
from datetime import datetime, timedelta
from math import exp, radians, sin, cos, sqrt, atan2
import os

logger = logging.getLogger(__name__)

# Import caching utilities
try:
    from utils.cache import cache_get, cache_set, generate_cache_key
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False
    logger.warning("Cache utilities not available")

# Import travel styles
try:
    from tools.travel_styles import (
        get_style_profile, get_combined_profile, 
        StyleProfile, TravelStyle, STYLE_PROFILES
    )
    TRAVEL_STYLES_AVAILABLE = True
except ImportError:
    TRAVEL_STYLES_AVAILABLE = False
    logger.warning("Travel styles module not available")

# OpenAI LLM - CHỈ dùng để format/combine thông tin cuối cùng (optional, có thể tắt)
# Không dùng để generate content hoặc cung cấp thông tin chính
_llm = None
_llm_enabled = os.getenv('PLANNING_USE_LLM', 'false').lower() == 'true'  # Tắt mặc định

def get_llm():
    """
    Get LLM instance với fallback: Groq -> GPT OSS 120B -> OpenAI
    
    ⚠️ LƯU Ý: Chỉ dùng khi thực sự cần format/combine thông tin thành văn bản mượt mà.
    KHÔNG dùng để generate content hoặc cung cấp thông tin chính.
    Chi phí API khá đắt, nên hạn chế sử dụng.
    """
    global _llm
    if not _llm_enabled:
        return None  # Tắt mặc định
    
    if _llm is None:
        # Priority 1: Try Groq
        try:
            GROQ_API_KEY = os.getenv('GROQ_API_KEY')
            if GROQ_API_KEY:
                from langchain_groq import ChatGroq
                groq_model = os.getenv('GROQ_MODEL', 'llama-3.3-70b-versatile')  # Updated model
                _llm = ChatGroq(
                    model=groq_model,
                    temperature=0.3,
                    groq_api_key=GROQ_API_KEY
                )
                logger.info(f"Groq LLM initialized for planning tools: {groq_model}")
                return _llm
        except ImportError:
            logger.debug("langchain-groq not available, trying fallback")
        except Exception as e:
            logger.warning(f"Failed to initialize Groq LLM: {e}, trying fallback")
        
        # Priority 2: Try GPT OSS 120B (fallback model)
        try:
            FALLBACK_MODEL = os.getenv('FALLBACK_MODEL', 'gpt-oss-120b')
            # GPT OSS 120B có thể được host qua OpenAI-compatible API
            # Hoặc có thể là một endpoint khác, tùy vào cấu hình
            OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
            if OPENAI_API_KEY and FALLBACK_MODEL:
                from langchain_openai import ChatOpenAI
                # Nếu GPT OSS 120B được host qua OpenAI-compatible endpoint
                # Có thể cần cấu hình base_url riêng
                _llm = ChatOpenAI(
                    model=FALLBACK_MODEL,
                    temperature=0.3,
                    api_key=OPENAI_API_KEY
                )
                logger.info(f"Fallback LLM initialized: {FALLBACK_MODEL}")
                return _llm
        except Exception as e:
            logger.warning(f"Failed to initialize fallback LLM: {e}, trying OpenAI")
        
        # Priority 3: Fallback to OpenAI
        try:
            OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
            if OPENAI_API_KEY:
                from langchain_openai import ChatOpenAI
                _llm = ChatOpenAI(
                    model=os.getenv('MODEL', 'gpt-4o-mini'),
                    temperature=0.3,
                    api_key=OPENAI_API_KEY
                )
                logger.info("OpenAI LLM initialized for planning tools (format only)")
            else:
                logger.warning("No LLM API keys found, LLM disabled")
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAI LLM: {e}")
    return _llm


class PlanningTools:
    """Công cụ lập kế hoạch với score-based ranking và geo-awareness"""
    
    # Khung giờ hoạt động trong ngày
    TIME_SLOTS = {
        'morning': {'start': 8, 'end': 12, 'label': 'Sáng (8h-12h)'},
        'afternoon': {'start': 12, 'end': 17, 'label': 'Chiều (12h-17h)'},
        'evening': {'start': 17, 'end': 21, 'label': 'Tối (17h-21h)'},
        'night': {'start': 21, 'end': 23, 'label': 'Đêm (21h-23h)'}
    }
    
    def __init__(self):
        """Initialize PlanningTools with dependencies"""
        # Lazy load tools to avoid circular imports
        self._geo_tools = None
        self._activities_tools = None
        self._vector_db = None
        # In-memory cache for routes within the same request to avoid duplicate API calls
        self._route_cache = {}
    
    def get_llm(self):
        """Get LLM instance for description generation"""
        return get_llm()
    
    def _get_geo_tools(self):
        """Lazy load GeoTools"""
        if self._geo_tools is None:
            try:
                from tools.geo_tools import get_geo_tools
                self._geo_tools = get_geo_tools()
            except Exception as e:
                logger.warning(f"GeoTools not available: {e}")
        return self._geo_tools
    
    def _get_activities_tools(self):
        """Lazy load ActivitiesTools"""
        if self._activities_tools is None:
            try:
                from tools.activities_tools import get_activities_tools
                self._activities_tools = get_activities_tools()
            except Exception as e:
                logger.warning(f"ActivitiesTools not available: {e}")
        return self._activities_tools
    
    def _get_vector_db(self):
        """Lazy load VectorDB"""
        if self._vector_db is None:
            try:
                from agents.travel_agents.vector_db import get_vector_db_agent
                self._vector_db = get_vector_db_agent()
            except Exception as e:
                logger.debug(f"VectorDB not available: {e}")
        return self._vector_db
    
    def _calculate_distance_km(self, loc1: Tuple[float, float], loc2: Tuple[float, float]) -> float:
        """
        Tính khoảng cách giữa 2 điểm (Haversine formula)
        
        Args:
            loc1: (lat, lon) của điểm 1
            loc2: (lat, lon) của điểm 2
            
        Returns:
            Khoảng cách (km)
        """
        if not loc1 or not loc2:
            return float('inf')
        
        lat1, lon1 = radians(loc1[0]), radians(loc1[1])
        lat2, lon2 = radians(loc2[0]), radians(loc2[1])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return 6371 * c  # Earth radius in km
    
    def _normalize_price_level(self, price_range: Any) -> int:
        """
        Chuẩn hóa price_range thành integer (1-4)
        
        Args:
            price_range: String ('low', 'medium', 'high') hoặc integer
            
        Returns:
            Integer 1-4 (1=budget, 2=standard, 3=premium, 4=luxury)
        """
        if isinstance(price_range, int):
            return max(1, min(4, price_range))
        
        if isinstance(price_range, str):
            price_lower = price_range.lower()
            if price_lower in ['low', 'budget', 'cheap', '1', 'one']:
                return 1
            elif price_lower in ['medium', 'moderate', 'standard', '2', 'two']:
                return 2
            elif price_lower in ['high', 'premium', '3', 'three']:
                return 3
            elif price_lower in ['luxury', 'fine', '4', 'four']:
                return 4
        
        return 2  # Default to standard
    
    def _extract_coordinates(self, place: Dict) -> Optional[Tuple[float, float]]:
        """
        Trích xuất tọa độ từ place dict
        
        Args:
            place: Dict với lat/lon hoặc viDo/kinhDo
            
        Returns:
            (lat, lon) hoặc None
        """
        # Try multiple field names
        lat = place.get('latitude') or place.get('lat') or place.get('viDo')
        lon = place.get('longitude') or place.get('lon') or place.get('kinhDo') or place.get('lng')
        
        if lat is not None and lon is not None:
            try:
                return (float(lat), float(lon))
            except (ValueError, TypeError):
                pass
        
        return None
    
    def _get_style_profile(self, travel_style: Union[str, List[str]]) -> StyleProfile:
        """
        Lấy style profile từ travel_style (có thể là string hoặc list)
        
        Args:
            travel_style: String hoặc list các phong cách
            
        Returns:
            StyleProfile
        """
        if not TRAVEL_STYLES_AVAILABLE:
            # Fallback to basic styles
            if isinstance(travel_style, list):
                travel_style = travel_style[0] if travel_style else 'standard'
            return None
        
        if isinstance(travel_style, list):
            if len(travel_style) == 1:
                return get_style_profile(travel_style[0]) or STYLE_PROFILES[TravelStyle.STANDARD]
            else:
                return get_combined_profile(travel_style)
        else:
            return get_style_profile(travel_style) or STYLE_PROFILES[TravelStyle.STANDARD]
    
    def score_restaurant(
        self,
        restaurant: Dict,
        meal_type: str,
        travel_style: Union[str, List[str]],
        reference_loc: Optional[Tuple[float, float]] = None,
        max_distance_km: Optional[float] = None,
        geo_tools = None
    ) -> float:
        """
        Tính điểm cho nhà hàng (0.0 - 1.0) với style-aware scoring
        
        Args:
            restaurant: Dict nhà hàng
            meal_type: Loại bữa ăn (breakfast, lunch, dinner, snack, drink)
            travel_style: String hoặc list các phong cách ('budget', 'gastronomy', ['romantic', 'luxury'], ...)
            reference_loc: (lat, lon) của khách sạn hoặc activity gần đó
            max_distance_km: Khoảng cách tối đa (km) - sẽ dùng từ style profile nếu None
            geo_tools: GeoTools instance (optional)
            
        Returns:
            Score từ 0.0 đến 1.0
        """
        # Get style profile
        style_profile = self._get_style_profile(travel_style)
        
        if style_profile:
            # Use style-specific weights
            weights = {
                'meal': 0.35,  # Base weight for meal relevance
                'style': style_profile.weights.get('price', 0.20),
                'rating': style_profile.weights.get('rating', 0.25),
                'distance': style_profile.weights.get('distance', 0.20),
                'cuisine': style_profile.weights.get('cuisine', 0.15)
            }
            # Normalize weights to sum to 1.0
            total = sum(weights.values())
            weights = {k: v/total for k, v in weights.items()}
            
            max_distance_km = max_distance_km or style_profile.preferred_radius_km
        else:
            # Fallback to default weights
            weights = {
                'meal': 0.35,
                'style': 0.20,
                'rating': 0.25,
                'distance': 0.20
            }
            max_distance_km = max_distance_km or 5.0
        
        # 1) Meal relevance (keyword / tags / cuisine)
        meal_keywords = {
            'breakfast': ['breakfast', 'café', 'cafe', 'phở', 'bún', 'morning', 'ăn sáng', 'bữa sáng', 'sáng'],
            'lunch': ['lunch', 'rice', 'com', 'noodle', 'cơm', 'bữa trưa', 'trưa', 'nhà hàng'],
            'dinner': ['dinner', 'fine dining', 'restaurant', 'seafood', 'nhà hàng', 'bữa tối', 'tối'],
            'snack': ['snack', 'street food', 'ăn vặt', 'quán vỉa hè', 'chè', 'bánh', 'vặt'],
            'drink': ['cà phê', 'coffee', 'trà', 'tea', 'drink', 'nước giải khát', 'café', 'cafe'],
            'afternoon_tea': ['trà chiều', 'afternoon tea', 'high tea', 'tea house', 'trà']
        }
        
        meal_score = 0.0
        keywords = meal_keywords.get(meal_type, [])
        
        # Combine all text fields
        text_fields = [
            restaurant.get('name', ''),
            ' '.join(restaurant.get('tags', [])),
            restaurant.get('cuisine', ''),
            restaurant.get('description', ''),
            restaurant.get('category', '')
        ]
        combined_text = ' '.join(str(f) for f in text_fields).lower()
        
        # Check for keyword matches
        for kw in keywords:
            if kw.lower() in combined_text:
                meal_score = 1.0
                break
        
        # If no exact match, give partial score based on partial matches
        if meal_score == 0.0:
            partial_matches = sum(1 for kw in keywords if any(kw_part in combined_text for kw_part in kw.split()))
            if partial_matches > 0:
                meal_score = 0.5
        
        # 2) Style match (price_level or price_avg)
        price_level = self._normalize_price_level(
            restaurant.get('price_level') or 
            restaurant.get('price_range') or 
            restaurant.get('price_avg_vnd', 0)
        )
        
        style_score = 0.5  # Default neutral
        if style_profile:
            # Use style profile price range
            min_price, max_price = style_profile.preferred_price_range
            if min_price <= price_level <= max_price:
                style_score = 1.0
            elif price_level < min_price:
                style_score = 0.7  # Slightly below preferred
            elif price_level > max_price:
                # Penalize if too expensive for style
                if style_profile.name in ['Tiết kiệm', 'Budget']:
                    style_score = 0.1
                else:
                    style_score = 0.4
        else:
            # Fallback to old logic
            if isinstance(travel_style, list):
                travel_style = travel_style[0] if travel_style else 'standard'
            
            if travel_style == 'budget':
                style_score = 1.0 if price_level <= 2 else (0.3 if price_level == 3 else 0.1)
            elif travel_style == 'standard':
                style_score = 1.0 if price_level == 2 else (0.8 if price_level in [1, 3] else 0.4)
            else:  # luxury
                style_score = 1.0 if price_level >= 3 else (0.6 if price_level == 2 else 0.2)
        
        # Cuisine match (if style profile has cuisine preference)
        cuisine_score = 0.5
        if style_profile and style_profile.preferred_meal_types:
            restaurant_cuisine = (restaurant.get('cuisine', '') + ' ' + 
                                ' '.join(restaurant.get('tags', []))).lower()
            for preferred_type in style_profile.preferred_meal_types:
                if preferred_type.lower() in restaurant_cuisine:
                    cuisine_score = 1.0
                    break
        
        # 3) Rating normalized (maps 3.0->0, 5.0->1)
        rating = restaurant.get('rating') or restaurant.get('review_rating') or 0
        if isinstance(rating, str):
            try:
                rating = float(rating)
            except (ValueError, TypeError):
                rating = 0
        
        rating_score = min(max((rating - 3.0) / 2.0, 0.0), 1.0) if rating > 0 else 0.3
        
        # 4) Distance: compute using geo_tools or haversine
        dist_score = 0.5  # Default neutral
        rest_coords = self._extract_coordinates(restaurant)
        
        if reference_loc and rest_coords:
            # Use Haversine first (free, fast) - only call API if distance is reasonable
            dist_km_haversine = self._calculate_distance_km(reference_loc, rest_coords)
            
            # Only use geo_tools API if distance is reasonable (< 50km) to avoid unnecessary API calls
            # For longer distances, Haversine is good enough for scoring
            if geo_tools and dist_km_haversine < 50:
                try:
                    # Check in-memory cache first
                    route_key = f"{reference_loc[0]:.7f},{reference_loc[1]:.7f}|{rest_coords[0]:.7f},{rest_coords[1]:.7f}"
                    if route_key in self._route_cache:
                        route_info = self._route_cache[route_key]
                    else:
                        # Try to get route info (cached in Redis/global cache)
                        route_info = geo_tools.calculate_distance_time(
                            f"{reference_loc[0]},{reference_loc[1]}",
                            f"{rest_coords[0]},{rest_coords[1]}",
                            profile='driving-car'
                        )
                        # Cache in memory for this request
                        if route_info:
                            self._route_cache[route_key] = route_info
                    
                    if route_info:
                        dist_km = route_info.get('distance_km', dist_km_haversine)
                    else:
                        dist_km = dist_km_haversine
                except Exception as e:
                    logger.debug(f"Geo routing failed, using haversine: {e}")
                    dist_km = dist_km_haversine
            else:
                dist_km = dist_km_haversine
            
            # Gaussian decay: closer = higher score
            if dist_km < max_distance_km:
                dist_score = exp(-(dist_km / max_distance_km) ** 2)
            else:
                # Penalty for far distances
                dist_score = max(0.1, exp(-(dist_km / (max_distance_km * 2)) ** 2))
        elif not reference_loc:
            # No reference location -> neutral score
            dist_score = 0.5
        
        # Weighted sum
        total_score = (
            weights['meal'] * meal_score +
            weights['style'] * style_score +
            weights['rating'] * rating_score +
            weights['distance'] * dist_score
        )
        
        # Add cuisine score if available
        if 'cuisine' in weights:
            total_score += weights['cuisine'] * cuisine_score
            # Renormalize
            total_score = total_score / (1.0 + weights['cuisine'])
        
        return float(min(1.0, total_score))
    
    def _is_open_for_meal(self, opening_hours: Dict, meal_type: str, current_time: Optional[str] = None) -> bool:
        """
        Kiểm tra nhà hàng có mở cửa cho meal_type không
        
        Args:
            opening_hours: Dict với format {'mon': ['07:00-14:00', '17:00-22:00'], ...}
            meal_type: 'breakfast', 'lunch', 'dinner', 'snack', 'drink'
            current_time: Thời gian hiện tại (HH:MM) - optional, default dùng meal_type
            
        Returns:
            True nếu có khả năng mở cửa
        """
        if not opening_hours:
            return True  # Unknown -> assume open
        
        # Map meal_type to time ranges
        meal_times = {
            'breakfast': (7, 10),   # 7h-10h
            'lunch': (11, 14),      # 11h-14h
            'dinner': (17, 21),     # 17h-21h
            'snack': (14, 18),      # 14h-18h
            'drink': (7, 23),       # 7h-23h (flexible)
            'afternoon_tea': (14, 17)  # 14h-17h
        }
        
        target_hour = meal_times.get(meal_type, (8, 22))[0]  # Default to morning
        
        # Get current day of week (0=Monday, 6=Sunday)
        if current_time:
            # Parse current_time if provided
            try:
                hour = int(current_time.split(':')[0])
            except:
                hour = target_hour
        else:
            hour = target_hour
        
        # Check if any time slot covers the target hour
        # Try current day first, then any day
        day_keys = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
        for day_key in day_keys:
            if day_key in opening_hours:
                time_slots = opening_hours[day_key]
                if isinstance(time_slots, str):
                    time_slots = [time_slots]
                
                for slot in time_slots:
                    if isinstance(slot, str) and '-' in slot:
                        try:
                            start_str, end_str = slot.split('-')
                            start_hour = int(start_str.split(':')[0])
                            end_hour = int(end_str.split(':')[0])
                            
                            # Check if target hour is within range
                            if start_hour <= hour <= end_hour:
                                return True
                        except (ValueError, IndexError):
                            continue
        
        # If no specific match, assume open (graceful degradation)
        return True
    
    def _suggest_restaurant(
        self,
        restaurants: Optional[List[Dict]],
        meal_type: str,
        travel_style: Union[str, List[str]] = 'standard',
        day: int = 1,
        reference_loc: Optional[Tuple[float, float]] = None,
        geo_tools = None
    ) -> Optional[Dict]:
        """
        Đề xuất nhà hàng với score-based ranking
        
        Args:
            restaurants: Danh sách nhà hàng
            meal_type: Loại bữa ăn
            travel_style: 'budget', 'standard', 'luxury'
            day: Số ngày (để đa dạng hóa)
            reference_loc: (lat, lon) của khách sạn hoặc activity
            geo_tools: GeoTools instance
            
        Returns:
            Dict nhà hàng được đề xuất hoặc None
        """
        if not restaurants:
            return None
        
        # Get style profile for max_distance
        style_profile = self._get_style_profile(travel_style)
        max_dist = style_profile.preferred_radius_km if style_profile else (
            5.0 if (isinstance(travel_style, str) and travel_style != 'luxury') else 10.0
        )
        
        # Score all restaurants
        scored = []
        for r in restaurants:
            # Skip if no coordinates (but still score, just with distance penalty)
            score = self.score_restaurant(
                r, meal_type, travel_style, reference_loc,
                max_distance_km=max_dist,
                geo_tools=geo_tools
            )
            
            # Check opening hours and penalize if likely closed
            opening_hours = r.get('opening_hours') or r.get('openingHours') or r.get('hours')
            if opening_hours:
                if not self._is_open_for_meal(opening_hours, meal_type):
                    score *= 0.6  # Penalize if likely closed
            
            scored.append((score, r))
        
        if not scored:
            return None
        
        # Sort by score descending
        scored.sort(key=lambda x: x[0], reverse=True)
        
        # Choose top N and pick one by deterministic rotation for diversity
        top_k = min(8, len(scored))
        top_restaurants = [r for _, r in scored[:top_k]]
        
        # Deterministic selection based on day and meal_type for diversity
        meal_offsets = {
            'breakfast': 0, 'lunch': 1, 'dinner': 2,
            'snack': 3, 'drink': 4, 'afternoon_tea': 5
        }
        offset = meal_offsets.get(meal_type, 0)
        seed_index = ((day - 1) * 7 + offset) % len(top_restaurants)
        
        selected = top_restaurants[seed_index]
        logger.debug(f"Selected restaurant '{selected.get('name')}' for {meal_type} (score: {scored[seed_index][0]:.2f})")
        
        return selected
    
    def score_activity(
        self,
        activity: Dict,
        travel_style: Union[str, List[str]],
        reference_loc: Optional[Tuple[float, float]] = None,
        max_distance_km: Optional[float] = None,
        geo_tools = None
    ) -> float:
        """
        Tính điểm cho hoạt động (0.0 - 1.0) với style-aware scoring
        
        Args:
            activity: Dict hoạt động
            travel_style: String hoặc list các phong cách
            reference_loc: (lat, lon) của khách sạn
            max_distance_km: Khoảng cách tối đa - sẽ dùng từ style profile nếu None
            geo_tools: GeoTools instance
            
        Returns:
            Score từ 0.0 đến 1.0
        """
        # Get style profile
        style_profile = self._get_style_profile(travel_style)
        
        if style_profile:
            # Use style-specific weights
            weights = {
                'popularity': style_profile.weights.get('rating', 0.40),
                'style': style_profile.weights.get('price', 0.20),
                'distance': style_profile.weights.get('distance', 0.30),
                'category': 0.10,
                'difficulty': style_profile.weights.get('difficulty', 0.10)
            }
            # Normalize weights
            total = sum(weights.values())
            weights = {k: v/total for k, v in weights.items()}
            
            max_distance_km = max_distance_km or style_profile.preferred_radius_km
        else:
            # Fallback to default weights
            weights = {
                'popularity': 0.40,
                'style': 0.20,
                'distance': 0.30,
                'category': 0.10
            }
            max_distance_km = max_distance_km or 10.0
        
        # 1) Popularity (rating + review count)
        rating = activity.get('rating') or activity.get('danhGiaTrungBinh') or 0
        if isinstance(rating, str):
            try:
                rating = float(rating)
            except (ValueError, TypeError):
                rating = 0
        
        review_count = activity.get('reviews') or activity.get('soLuotDanhGia') or 0
        if isinstance(review_count, str):
            try:
                review_count = int(review_count)
            except (ValueError, TypeError):
                review_count = 0
        
        # Normalize rating (3.0->0, 5.0->1)
        rating_score = min(max((rating - 3.0) / 2.0, 0.0), 1.0) if rating > 0 else 0.3
        
        # Normalize review count (log scale: 0->0, 100+->1)
        review_score = min(1.0, (review_count / 100.0) ** 0.5) if review_count > 0 else 0.2
        
        popularity_score = 0.7 * rating_score + 0.3 * review_score
        
        # 2) Style match (price/cost)
        cost = activity.get('cost_vnd') or activity.get('giaVe') or 0
        if isinstance(cost, str):
            try:
                cost = float(cost)
            except (ValueError, TypeError):
                cost = 0
        
        style_score = 0.5  # Default neutral
        if style_profile:
            # Use style profile price range
            min_price, max_price = style_profile.preferred_price_range
            # Map price_level to cost range (rough estimate)
            cost_level = 1 if cost == 0 else (2 if cost < 100000 else (3 if cost < 500000 else 4))
            
            if min_price <= cost_level <= max_price:
                style_score = 1.0
            elif cost_level < min_price:
                style_score = 0.7
            elif cost_level > max_price:
                style_score = 0.3
        else:
            # Fallback to old logic
            if isinstance(travel_style, list):
                travel_style = travel_style[0] if travel_style else 'standard'
            
            if travel_style == 'budget':
                if cost == 0:
                    style_score = 1.0
                elif cost < 50000:
                    style_score = 0.8
                elif cost < 200000:
                    style_score = 0.5
                else:
                    style_score = 0.2
            elif travel_style == 'standard':
                if cost < 300000:
                    style_score = 1.0
                elif cost < 500000:
                    style_score = 0.7
                else:
                    style_score = 0.4
            else:  # luxury
                style_score = 1.0 if cost < 1000000 else 0.8
        
        # Category/Activity type match
        category_score = 0.5
        if style_profile and style_profile.preferred_activity_types:
            activity_type = (activity.get('category', '') + ' ' + 
                           activity.get('loaiDiaDiem', '') + ' ' +
                           ' '.join(activity.get('tags', []))).lower()
            for preferred_type in style_profile.preferred_activity_types:
                if preferred_type.lower() in activity_type:
                    category_score = 1.0
                    break
        
        # Difficulty match (for adventure/extreme styles)
        difficulty_score = 0.5
        if style_profile and 'difficulty' in style_profile.weights:
            activity_difficulty = activity.get('difficulty', 'medium')
            if style_profile.name in ['Phiêu lưu', 'Adventure', 'Extreme']:
                # Prefer higher difficulty
                if activity_difficulty in ['hard', 'extreme', 'challenging']:
                    difficulty_score = 1.0
                elif activity_difficulty in ['medium', 'moderate']:
                    difficulty_score = 0.6
                else:
                    difficulty_score = 0.3
            else:
                # Prefer lower difficulty
                if activity_difficulty in ['easy', 'low']:
                    difficulty_score = 1.0
                elif activity_difficulty in ['medium', 'moderate']:
                    difficulty_score = 0.7
                else:
                    difficulty_score = 0.4
        
        # 3) Distance
        dist_score = 0.5
        activity_coords = self._extract_coordinates(activity)
        
        if reference_loc and activity_coords:
            if geo_tools:
                try:
                    route_info = geo_tools.calculate_distance_time(
                        f"{reference_loc[0]},{reference_loc[1]}",
                        f"{activity_coords[0]},{activity_coords[1]}",
                        profile='driving-car'
                    )
                    if route_info:
                        dist_km = route_info.get('distance_km', float('inf'))
                    else:
                        dist_km = self._calculate_distance_km(reference_loc, activity_coords)
                except Exception as e:
                    logger.debug(f"Geo routing failed, using haversine: {e}")
                    dist_km = self._calculate_distance_km(reference_loc, activity_coords)
            else:
                dist_km = self._calculate_distance_km(reference_loc, activity_coords)
            
            # Gaussian decay
            if dist_km < max_distance_km:
                dist_score = exp(-(dist_km / max_distance_km) ** 2)
            else:
                dist_score = max(0.1, exp(-(dist_km / (max_distance_km * 2)) ** 2))
        elif not reference_loc:
            dist_score = 0.5
        
        # Weighted sum
        total_score = (
            weights['popularity'] * popularity_score +
            weights['style'] * style_score +
            weights['distance'] * dist_score +
            weights['category'] * category_score
        )
        
        # Add difficulty score if available
        if 'difficulty' in weights:
            total_score += weights['difficulty'] * difficulty_score
            # Renormalize
            total_score = total_score / (1.0 + weights['difficulty'])
        
        return float(min(1.0, total_score))
    
    def _distribute_activities(
        self,
        activities: Optional[List[Dict]],
        day: int,
        travel_style: Union[str, List[str]] = 'standard',
        hotel_loc: Optional[Tuple[float, float]] = None,
        geo_tools = None
    ) -> List[Dict[str, Any]]:
        """
        Phân bổ hoạt động với score-based selection và travel time optimization
        
        Đảm bảo:
        - Mỗi ngày có hoạt động khác nhau
        - Hoạt động gần khách sạn hoặc gần nhau
        - Tối ưu thời gian di chuyển
        """
        if not activities:
            return []
        
        # Get style profile for max_distance
        style_profile = self._get_style_profile(travel_style)
        max_dist = style_profile.preferred_radius_km if style_profile else 15.0
        
        # Score all activities
        scored_activities = []
        for act in activities:
            score = self.score_activity(act, travel_style, hotel_loc, max_distance_km=max_dist, geo_tools=geo_tools)
            scored_activities.append((score, act))
        
        # Sort by score
        scored_activities.sort(key=lambda x: x[0], reverse=True)
        
        # Select 2 activities per day (morning + afternoon)
        num_activities_per_day = min(2, len(activities))
        
        # For diversity: use day-based offset
        offset_per_day = max(1, len(activities) // 3)
        start_idx = ((day - 1) * offset_per_day) % len(scored_activities)
        
        selected_activities = []
        used_indices = set()
        
        # Pick first activity (morning) - highest score from offset position
        for i in range(len(scored_activities)):
            idx = (start_idx + i) % len(scored_activities)
            if idx not in used_indices:
                selected_activities.append(scored_activities[idx][1])
                used_indices.add(idx)
                break
        
        if not selected_activities:
            return []
        
        morning_activity = selected_activities[0]
        morning_coords = self._extract_coordinates(morning_activity)
        
        # Pick second activity (afternoon) - minimize travel time from morning activity
        if len(scored_activities) > 1 and morning_coords:
            # Score candidates by: base_score + proximity to morning activity
            afternoon_candidates = []
            for score, act in scored_activities:
                if act not in selected_activities:
                    act_coords = self._extract_coordinates(act)
                    if act_coords:
                        # Use Haversine first (free, fast)
                        travel_dist_haversine = self._calculate_distance_km(morning_coords, act_coords)
                        
                        # Only call API if distance is reasonable (< 50km) to avoid unnecessary API calls
                        if geo_tools and travel_dist_haversine < 50:
                            try:
                                # Check in-memory cache first
                                route_key = f"{morning_coords[0]:.7f},{morning_coords[1]:.7f}|{act_coords[0]:.7f},{act_coords[1]:.7f}"
                                if route_key in self._route_cache:
                                    route_info = self._route_cache[route_key]
                                else:
                                    route_info = geo_tools.calculate_distance_time(
                                        f"{morning_coords[0]},{morning_coords[1]}",
                                        f"{act_coords[0]},{act_coords[1]}",
                                        profile='driving-car'
                                    )
                                    # Cache in memory for this request
                                    if route_info:
                                        self._route_cache[route_key] = route_info
                                
                                travel_time = route_info.get('duration_minutes', 60) if route_info else 60
                                travel_dist = route_info.get('distance_km', travel_dist_haversine) if route_info else travel_dist_haversine
                            except:
                                travel_time = travel_dist_haversine * 2  # Rough estimate: 2 min/km
                                travel_dist = travel_dist_haversine
                        else:
                            travel_dist = travel_dist_haversine
                            travel_time = travel_dist * 2  # Rough estimate: 2 min/km
                        
                        # Combined score: base score + proximity bonus
                        proximity_bonus = exp(-travel_dist / 5.0)  # Decay with distance
                        combined_score = score * 0.7 + proximity_bonus * 0.3
                        
                        afternoon_candidates.append((combined_score, travel_time, travel_dist, act))
                    else:
                        # No coordinates -> use base score
                        afternoon_candidates.append((score, 60, 10, act))
            
            if afternoon_candidates:
                # Sort by combined score, prefer shorter travel time
                afternoon_candidates.sort(key=lambda x: (x[0], -x[1]), reverse=True)
                best_afternoon = afternoon_candidates[0][3]
                selected_activities.append(best_afternoon)
                
                # Store travel time info
                travel_time = afternoon_candidates[0][1]
                travel_dist = afternoon_candidates[0][2]
        elif len(scored_activities) > 1:
            # No coordinates for morning activity -> just pick second best
            for score, act in scored_activities:
                if act not in selected_activities:
                    selected_activities.append(act)
                    break
        
        # Build distributed activities with time slots
        distributed = []
        slots = ['morning', 'afternoon']
        
        for i, slot in enumerate(slots):
            if i < len(selected_activities):
                activity = selected_activities[i]
                activity_with_style = activity.copy()
                activity_with_style['recommended_for'] = travel_style
                
                distributed_item = {
                    'time_slot': slot,
                    'time': self.TIME_SLOTS[slot]['label'],
                    'activity': activity_with_style,
                    'description': self._get_activity_description(activity, slot, travel_style, use_ai=False)
                }
                
                # Add travel time info for afternoon activity
                # Use cached result if available (already calculated above)
                if slot == 'afternoon' and i > 0 and morning_coords:
                    afternoon_coords = self._extract_coordinates(activity)
                    if afternoon_coords:
                        # Check in-memory cache first (already calculated when selecting afternoon activity)
                        route_key = f"{morning_coords[0]:.7f},{morning_coords[1]:.7f}|{afternoon_coords[0]:.7f},{afternoon_coords[1]:.7f}"
                        if route_key in self._route_cache:
                            route_info = self._route_cache[route_key]
                            if route_info:
                                distributed_item['travel_time_minutes'] = route_info.get('duration_minutes', 30)
                                distributed_item['travel_distance_km'] = route_info.get('distance_km', 5)
                        elif geo_tools:
                            # Only call API if not in cache and distance is reasonable
                            travel_dist_haversine = self._calculate_distance_km(morning_coords, afternoon_coords)
                            if travel_dist_haversine < 50:
                                try:
                                    route_info = geo_tools.calculate_distance_time(
                                        f"{morning_coords[0]},{morning_coords[1]}",
                                        f"{afternoon_coords[0]},{afternoon_coords[1]}",
                                        profile='driving-car'
                                    )
                                    if route_info:
                                        self._route_cache[route_key] = route_info
                                        distributed_item['travel_time_minutes'] = route_info.get('duration_minutes', 30)
                                        distributed_item['travel_distance_km'] = route_info.get('distance_km', 5)
                                except:
                                    pass
                
                distributed.append(distributed_item)
        
        return distributed
    
    def _get_activity_description(self, activity: Dict, time_slot: str, travel_style: str, use_ai: bool = False) -> str:
        """Tạo mô tả hoạt động - rule-based để giảm AI calls"""
        activity_name = activity.get('name', 'Hoạt động')
        activity_desc = activity.get('description', '')
        
        # Rule-based descriptions - đa dạng hơn
        time_descriptions = {
            'morning': [
                f"Hãy cùng tôi khám phá vẻ đẹp cổ kính của {activity_name} vào buổi sáng",
                f"Bắt đầu ngày mới với hành trình khám phá {activity_name}",
                f"Tham quan {activity_name} vào buổi sáng, nơi bạn sẽ được trải nghiệm văn hóa địa phương"
            ],
            'afternoon': [
                f"Tiếp tục khám phá {activity_name} vào buổi chiều",
                f"Khám phá {activity_name} vào buổi chiều, nơi bạn sẽ đắm chìm trong kho tàng văn hóa",
                f"Tham quan {activity_name} vào buổi chiều để tìm hiểu lịch sử và văn hóa địa phương"
            ],
            'evening': [
                f"Kết thúc ngày với {activity_name}",
                f"Thưởng thức không khí buổi tối tại {activity_name}",
                f"Khám phá {activity_name} vào buổi tối để trải nghiệm văn hóa địa phương"
            ]
        }
        
        # Chọn mô tả dựa trên hash để đa dạng
        desc_options = time_descriptions.get(time_slot, [f"Tham quan {activity_name}"])
        desc_index = hash(f"{activity_name}_{time_slot}") % len(desc_options)
        base_desc = desc_options[desc_index]
        
        # Thêm style prefix
        if travel_style == 'budget':
            base_desc += " mà không lo về chi phí!"
        elif travel_style == 'luxury':
            base_desc += " với trải nghiệm đặc biệt!"
        
        return base_desc
    
    def _suggest_theme(self, day: int, destination: str, travel_style: str = 'standard') -> str:
        """Đề xuất chủ đề cho ngày - adaptive dựa trên destination type"""
        # Try to detect destination type from activities/context (if available)
        # For now, use rule-based with destination-aware themes
        
        theme_templates = {
            1: [
                f'Khám phá {destination}',
                f'Làm quen với {destination}',
                f'Tham quan trung tâm {destination}'
            ],
            2: [
                f'Văn hóa & Lịch sử {destination}',
                f'Khám phá di tích tại {destination}',
                f'Tham quan các điểm nổi tiếng'
            ],
            3: [
                f'Thiên nhiên & Giải trí',
                f'Khám phá cảnh quan {destination}',
                f'Trải nghiệm địa phương'
            ],
            4: [
                f'Thư giãn & Mua sắm',
                f'Ẩm thực & Trải nghiệm',
                f'Khám phá ẩm thực {destination}'
            ],
            5: [
                'Ẩm thực & Trải nghiệm',
                'Thiên nhiên & Ngoại ô',
                'Văn hóa & Nghệ thuật'
            ]
        }
        
        themes = theme_templates.get(day, [f'Du lịch {destination}'])
        theme_index = hash(f"{destination}_{day}") % len(themes)
        return themes[theme_index]
    
    def _generate_tips(self, destination: str, day: int, travel_style: str = 'standard') -> List[str]:
        """Tạo mẹo du lịch - rule-based"""
        base_tips = [
            f'Mang theo nước uống và kem chống nắng khi tham quan {destination}',
            'Kiểm tra thời tiết trước khi ra ngoài',
            'Giữ giấy tờ tùy thân và tiền mặt an toàn'
        ]
        
        if day == 1:
            base_tips.append('Ngày đầu nên tham quan nhẹ nhàng để làm quen với địa điểm')
        elif day >= 3:
            base_tips.append('Lên kế hoạch cho các ngày còn lại để tận dụng tối đa thời gian')
        
        style_tips = {
            'budget': [
                'Chọn ở tại các homestay hoặc hostel để tiết kiệm chi phí',
                'Sử dụng xe buýt công cộng hoặc xe máy thuê để di chuyển',
                'Ghé thăm các điểm du lịch miễn phí để trải nghiệm văn hóa địa phương',
                'Tìm các quán ăn địa phương để tiết kiệm chi phí',
                'Mua vé combo để được giảm giá'
            ],
            'standard': [
                'Sử dụng xe buýt công cộng hoặc xe ôm công nghệ để tiết kiệm chi phí di chuyển',
                'Tìm hiểu và tham gia vào các tour đi bộ miễn phí để khám phá các điểm du lịch',
                'Thưởng thức ẩm thực đường phố tại các khu chợ địa phương',
                'Đặt bàn trước tại nhà hàng nổi tiếng',
                'Thử các món ăn đặc sản địa phương'
            ],
            'luxury': [
                'Sử dụng dịch vụ taxi hoặc thuê xe để linh hoạt di chuyển',
                'Tham gia tour cao cấp để trải nghiệm tốt nhất',
                'Thưởng thức ẩm thực cao cấp tại nhà hàng nổi tiếng',
                'Đặt dịch vụ VIP để có trải nghiệm đặc biệt',
                'Sử dụng dịch vụ concierge của khách sạn'
            ]
        }
        
        tips = base_tips + style_tips.get(travel_style, [])
        
        # Rotate tips dựa trên day để đa dạng
        tip_offset = (day - 1) % len(tips)
        rotated_tips = tips[tip_offset:] + tips[:tip_offset]
        
        return rotated_tips[:5]
    
    def _create_timeline(
        self,
        distributed_activities: List[Dict],
        restaurants: Optional[List[Dict]],
        travel_style: str,
        day: int,
        hotel_loc: Optional[Tuple[float, float]] = None,
        geo_tools = None
    ) -> List[Dict[str, Any]]:
        """
        Tạo timeline chi tiết với travel time được tính toán
        """
        timeline = []
        current_time = 8 * 60  # Start at 8:00 (in minutes)
        
        geo_tools = geo_tools or self._get_geo_tools()
        
        # Morning preparation
        timeline.append({
            'time': '08:00',
            'label': 'Sáng sớm',
            'activity': 'Thức dậy và chuẩn bị',
            'type': 'preparation',
            'description': 'Bắt đầu ngày mới, chuẩn bị hành trang du lịch'
        })
        current_time = 8 * 60 + 30  # 08:30
        
        # Breakfast
        breakfast = self._suggest_restaurant(
            restaurants, 'breakfast', travel_style, day,
            reference_loc=hotel_loc, geo_tools=geo_tools
        ) if restaurants else None
        
        breakfast_coords = None
        if breakfast:
            breakfast_coords = self._extract_coordinates(breakfast)
            travel_time = 0
            if hotel_loc and breakfast_coords and geo_tools:
                try:
                    route_info = geo_tools.calculate_distance_time(
                        f"{hotel_loc[0]},{hotel_loc[1]}",
                        f"{breakfast_coords[0]},{breakfast_coords[1]}",
                        profile='driving-car'
                    )
                    if route_info:
                        travel_time = int(route_info.get('duration_minutes', 10))
                except:
                    travel_time = 10
            
            timeline.append({
                'time': f"{int(current_time) // 60:02d}:{int(current_time) % 60:02d}",
                'label': 'Bữa sáng',
                'activity': breakfast.get('name', 'Bữa sáng'),
                'type': 'meal',
                'restaurant': breakfast,
                'travel_time_minutes': travel_time,
                'description': f"Thưởng thức bữa sáng tại {breakfast.get('name', 'nhà hàng địa phương')}"
            })
            current_time += 60  # 1 hour for breakfast
        
        # Morning activity
        morning_activity = next((a for a in distributed_activities if a.get('time_slot') == 'morning'), None)
        if morning_activity:
            activity = morning_activity.get('activity', {})
            activity_coords = self._extract_coordinates(activity)
            travel_time = 0
            
            # Calculate travel time from breakfast or hotel
            reference = breakfast_coords if breakfast_coords else hotel_loc
            if reference and activity_coords and geo_tools:
                try:
                    route_info = geo_tools.calculate_distance_time(
                        f"{reference[0]},{reference[1]}",
                        f"{activity_coords[0]},{activity_coords[1]}",
                        profile='driving-car'
                    )
                    if route_info:
                        travel_time = int(route_info.get('duration_minutes', 15))
                except:
                    travel_time = 15
            
            current_time += travel_time
            
            timeline.append({
                'time': f"{int(current_time) // 60:02d}:{int(current_time) % 60:02d}",
                'label': morning_activity.get('time', 'Sáng'),
                'activity': activity.get('name', 'Hoạt động'),
                'type': 'activity',
                'activity_details': activity,
                'travel_time_minutes': travel_time,
                'description': morning_activity.get('description', '')
            })
            current_time += 180  # 3 hours for morning activity
        
        # Lunch (around 12:00)
        lunch_time = max(12 * 60, current_time)
        morning_activity_coords = self._extract_coordinates(morning_activity.get('activity', {})) if morning_activity else None
        lunch = self._suggest_restaurant(
            restaurants, 'lunch', travel_style, day,
            reference_loc=morning_activity_coords if morning_activity_coords else hotel_loc,
            geo_tools=geo_tools
        ) if restaurants else None
        
        if lunch:
            lunch_coords = self._extract_coordinates(lunch)
            travel_time = 0
            reference = morning_activity_coords if morning_activity_coords else hotel_loc
            if reference and lunch_coords and geo_tools:
                try:
                    route_info = geo_tools.calculate_distance_time(
                        f"{reference[0]},{reference[1]}",
                        f"{lunch_coords[0]},{lunch_coords[1]}",
                        profile='driving-car'
                    )
                    if route_info:
                        travel_time = int(route_info.get('duration_minutes', 10))
                except:
                    travel_time = 10
            
            lunch_time += travel_time
            timeline.append({
                'time': f"{lunch_time // 60:02d}:{lunch_time % 60:02d}",
                'label': 'Bữa trưa',
                'activity': lunch.get('name', 'Bữa trưa'),
                'type': 'meal',
                'restaurant': lunch,
                'travel_time_minutes': travel_time,
                'description': f"Thưởng thức bữa trưa tại {lunch.get('name', 'nhà hàng địa phương')}"
            })
            current_time = lunch_time + 60  # 1 hour for lunch
        else:
            timeline.append({
                'time': '12:00',
                'label': 'Bữa trưa',
                'activity': 'Bữa trưa tại nhà hàng địa phương',
                'type': 'meal',
                'description': 'Thưởng thức bữa trưa'
            })
            current_time = 13 * 60
        
        # Afternoon activity
        afternoon_activity = next((a for a in distributed_activities if a.get('time_slot') == 'afternoon'), None)
        if afternoon_activity:
            activity = afternoon_activity.get('activity', {})
            activity_coords = self._extract_coordinates(activity)
            travel_time = afternoon_activity.get('travel_time_minutes', 15)
            
            current_time += travel_time
            
            timeline.append({
                'time': f"{int(current_time) // 60:02d}:{int(current_time) % 60:02d}",
                'label': afternoon_activity.get('time', 'Chiều'),
                'activity': activity.get('name', 'Hoạt động'),
                'type': 'activity',
                'activity_details': activity,
                'travel_time_minutes': travel_time,
                'description': afternoon_activity.get('description', '')
            })
            current_time += 180  # 3 hours for afternoon activity
        
        # Dinner (around 18:30)
        dinner_time = max(18 * 60 + 30, current_time)
        afternoon_activity_coords = self._extract_coordinates(afternoon_activity.get('activity', {})) if afternoon_activity else None
        dinner = self._suggest_restaurant(
            restaurants, 'dinner', travel_style, day,
            reference_loc=afternoon_activity_coords if afternoon_activity_coords else hotel_loc,
            geo_tools=geo_tools
        ) if restaurants else None
        
        if dinner:
            dinner_coords = self._extract_coordinates(dinner)
            travel_time = 0
            reference = afternoon_activity_coords if afternoon_activity_coords else hotel_loc
            if reference and dinner_coords and geo_tools:
                try:
                    route_info = geo_tools.calculate_distance_time(
                        f"{reference[0]},{reference[1]}",
                        f"{dinner_coords[0]},{dinner_coords[1]}",
                        profile='driving-car'
                    )
                    if route_info:
                        travel_time = int(route_info.get('duration_minutes', 15))
                except:
                    travel_time = 15
            
            dinner_time += travel_time
            timeline.append({
                'time': f"{int(dinner_time) // 60:02d}:{int(dinner_time) % 60:02d}",
                'label': 'Bữa tối',
                'activity': dinner.get('name', 'Bữa tối'),
                'type': 'meal',
                'restaurant': dinner,
                'travel_time_minutes': travel_time,
                'description': f"Thưởng thức bữa tối tại {dinner.get('name', 'nhà hàng địa phương')}"
            })
        else:
            timeline.append({
                'time': '18:30',
                'label': 'Bữa tối',
                'activity': 'Bữa tối tại nhà hàng địa phương',
                'type': 'meal',
                'description': 'Thưởng thức bữa tối'
            })
        
        # Rest
        timeline.append({
            'time': '22:00',
            'label': 'Nghỉ ngơi',
            'activity': 'Về khách sạn nghỉ ngơi',
            'type': 'rest',
            'description': 'Kết thúc ngày, nghỉ ngơi để chuẩn bị cho ngày mai'
        })
        
        # Thêm tùy chọn thời gian cho hoạt động cá nhân (free time slots)
        # Thêm 1-2 khoảng thời gian trống để người dùng tự chọn hoạt động
        free_time_slots = []
        
        # Tìm khoảng trống giữa các hoạt động để thêm free time
        if len(timeline) > 1:
            for i in range(len(timeline) - 1):
                current_item = timeline[i]
                next_item = timeline[i + 1]
                
                # Parse thời gian
                try:
                    current_time_str = current_item.get('time', '')
                    next_time_str = next_item.get('time', '')
                    
                    if current_time_str and next_time_str and ':' in current_time_str and ':' in next_time_str:
                        current_hour, current_min = map(int, current_time_str.split(':'))
                        next_hour, next_min = map(int, next_time_str.split(':'))
                        
                        current_minutes = current_hour * 60 + current_min
                        next_minutes = next_hour * 60 + next_min
                        
                        # Nếu có khoảng trống >= 2 giờ, thêm free time slot
                        gap_minutes = next_minutes - current_minutes
                        if gap_minutes >= 120:  # 2 giờ
                            # Tính thời gian bắt đầu free time (sau hoạt động hiện tại + 30 phút)
                            free_start_minutes = current_minutes + 30
                            free_start_hour = free_start_minutes // 60
                            free_start_min = free_start_minutes % 60
                            
                            # Thời gian kết thúc free time (trước hoạt động tiếp theo - 30 phút)
                            free_end_minutes = next_minutes - 30
                            free_end_hour = free_end_minutes // 60
                            free_end_min = free_end_minutes % 60
                            
                            if free_end_minutes > free_start_minutes:
                                free_time_slots.append({
                                    'time': f"{free_start_hour:02d}:{free_start_min:02d}",
                                    'label': 'Thời gian tự do',
                                    'activity': 'Hoạt động cá nhân / Tự chọn',
                                    'type': 'free_time',
                                    'description': f'Khoảng thời gian tự do từ {free_start_hour:02d}:{free_start_min:02d} đến {free_end_hour:02d}:{free_end_min:02d} để bạn tự chọn hoạt động theo sở thích',
                                    'end_time': f"{free_end_hour:02d}:{free_end_min:02d}",
                                    'duration_minutes': free_end_minutes - free_start_minutes
                                })
                except:
                    pass
        
        # Chèn free time slots vào timeline (sắp xếp theo thời gian)
        if free_time_slots:
            # Chỉ thêm tối đa 2 free time slots mỗi ngày
            for free_slot in free_time_slots[:2]:
                timeline.append(free_slot)
            
            # Sắp xếp lại timeline theo thời gian
            def get_time_minutes(item):
                time_str = item.get('time', '00:00')
                try:
                    if ':' in time_str:
                        hour, minute = map(int, time_str.split(':'))
                        return hour * 60 + minute
                except:
                    pass
                return 0
            
            timeline.sort(key=get_time_minutes)
        
        return timeline
    
    def _generate_daily_summary(
        self,
        day: int,
        destination: str,
        activities: List[Dict],
        travel_style: str
    ) -> str:
        """
        Tạo tóm tắt ngắn gọn cho ngày - Rule-based, KHÔNG dùng AI
        
        ⚠️ LƯU Ý: Function này KHÔNG dùng OpenAI để tiết kiệm chi phí.
        Chỉ dùng rule-based templates với rotation để đa dạng.
        """
        activity_count = len(activities)
        if activity_count == 0:
            templates = [
                f"Ngày {day} tại {destination} - Ngày thư giãn và khám phá tự do",
                f"Ngày {day} tại {destination} - Thời gian nghỉ ngơi và tận hưởng không gian",
                f"Ngày {day} tại {destination} - Khám phá theo nhịp độ riêng của bạn"
            ]
            return templates[hash(f"{destination}_{day}") % len(templates)]
        
        activity_names = [a.get('activity', {}).get('name', '') for a in activities if a.get('activity')]
        if activity_names:
            main_activities = ', '.join(activity_names[:2])
            # Rule-based templates - đa dạng hơn
            templates = [
                f"Ngày {day} tại {destination} - Khám phá {main_activities} và các điểm tham quan thú vị",
                f"Ngày {day} tại {destination} - Hành trình đến {main_activities} với nhiều trải nghiệm đáng nhớ",
                f"Ngày {day} tại {destination} - Tham quan {main_activities} và tìm hiểu văn hóa địa phương",
                f"Ngày {day} tại {destination} - Trải nghiệm {main_activities} cùng những khoảnh khắc tuyệt vời"
            ]
            template_idx = hash(f"{destination}_{day}") % len(templates)
            return templates[template_idx]
        
        return f"Ngày {day} tại {destination} - Trải nghiệm đầy đủ các hoạt động du lịch"
    
    def create_daily_schedule(
        self,
        day: int,
        date: str,
        destination: str,
        hotels: List[Dict] = None,
        restaurants: List[Dict] = None,
        activities: List[Dict] = None,
        travel_style: Union[str, List[str]] = 'standard',
        selected_hotel: Dict = None
    ) -> Dict[str, Any]:
        """
        Tạo lịch trình cho một ngày với score-based selection
        
        Args:
            day: Số thứ tự ngày (1, 2, 3...)
            date: Ngày (YYYY-MM-DD)
            destination: Điểm đến
            hotels: Danh sách khách sạn
            restaurants: Danh sách nhà hàng
            activities: Danh sách hoạt động
            travel_style: 'budget', 'standard', 'luxury'
            selected_hotel: Khách sạn đã chọn (nếu có)
            
        Returns:
            Dict với lịch trình chi tiết
        """
        # Get hotel location
        hotel = selected_hotel if selected_hotel else (hotels[0] if hotels else None)
        hotel_loc = self._extract_coordinates(hotel) if hotel else None
        
        # Get tools
        geo_tools = self._get_geo_tools()
        
        # Phân bổ hoạt động với scoring và travel time optimization
        distributed_activities = self._distribute_activities(
            activities, day, travel_style, hotel_loc, geo_tools
        )
        
        # Tạo timeline chi tiết với travel time
        timeline = self._create_timeline(
            distributed_activities, restaurants, travel_style, day,
            hotel_loc, geo_tools
        )
        
        # Tính toán start_time và end_time từ timeline
        start_time = '08:00'  # Default
        end_time = '22:00'    # Default
        
        if timeline:
            # Lấy thời gian đầu tiên và cuối cùng từ timeline
            first_item = timeline[0]
            last_item = timeline[-1]
            
            if first_item.get('time'):
                start_time = first_item['time']
            if last_item.get('time'):
                end_time = last_item['time']
        
        schedule = {
            'day': day,
            'date': date,
            'start_time': start_time,
            'end_time': end_time,
            'theme': self._suggest_theme(day, destination, travel_style),
            'accommodation': hotel,
            'meals': {
                'breakfast': self._suggest_restaurant(
                    restaurants, 'breakfast', travel_style, day,
                    reference_loc=hotel_loc, geo_tools=geo_tools
                ),
                'lunch': self._suggest_restaurant(
                    restaurants, 'lunch', travel_style, day,
                    reference_loc=hotel_loc, geo_tools=geo_tools
                ),
                'dinner': self._suggest_restaurant(
                    restaurants, 'dinner', travel_style, day,
                    reference_loc=hotel_loc, geo_tools=geo_tools
                ),
                'snacks': self._suggest_restaurant(
                    restaurants, 'snack', travel_style, day,
                    reference_loc=hotel_loc, geo_tools=geo_tools
                ),
                'drinks': self._suggest_restaurant(
                    restaurants, 'drink', travel_style, day,
                    reference_loc=hotel_loc, geo_tools=geo_tools
                ),
                'afternoon_tea': self._suggest_restaurant(
                    restaurants, 'afternoon_tea', travel_style, day,
                    reference_loc=hotel_loc, geo_tools=geo_tools
                ) if travel_style in ['standard', 'luxury'] else None
            },
            'activities': distributed_activities,
            'timeline': timeline,
            'tips': self._generate_tips(destination, day, travel_style),
            'summary': self._generate_daily_summary(day, destination, distributed_activities, travel_style)
        }
        
        return schedule
    
    def create_full_itinerary(
        self,
        start_date: str,
        days: int,
        destination: str,
        hotels: List[Dict] = None,
        restaurants: List[Dict] = None,
        activities: List[Dict] = None,
        travel_style: Union[str, List[str]] = 'standard',
        selected_hotel: Dict = None
    ) -> Dict[str, Any]:
        """
        Tạo lịch trình đầy đủ cho toàn bộ chuyến đi
        
        Args:
            start_date: Ngày bắt đầu (YYYY-MM-DD)
            days: Số ngày
            destination: Điểm đến
            hotels: Danh sách khách sạn
            restaurants: Danh sách nhà hàng
            activities: Danh sách hoạt động
            travel_style: Phong cách du lịch
            selected_hotel: Khách sạn đã chọn (nếu có)
            
        Returns:
            Dict với lịch trình đầy đủ
        """
        start = datetime.strptime(start_date, '%Y-%m-%d')
        itinerary = []
        
        for day in range(1, days + 1):
            date = (start + timedelta(days=day - 1)).strftime('%Y-%m-%d')
            daily_schedule = self.create_daily_schedule(
                day, date, destination, hotels, restaurants, activities, travel_style, selected_hotel
            )
            itinerary.append(daily_schedule)
        
        return {
            'destination': destination,
            'start_date': start_date,
            'end_date': (start + timedelta(days=days - 1)).strftime('%Y-%m-%d'),
            'total_days': days,
            'itinerary': itinerary,
            'summary': self._generate_trip_summary(destination, days, travel_style)
        }
    
    def _generate_trip_summary(self, destination: str, days: int, travel_style: str) -> str:
        """Tạo tóm tắt tổng quan cho toàn bộ chuyến đi"""
        style_labels = {
            'budget': 'tiết kiệm',
            'standard': 'tiêu chuẩn',
            'luxury': 'cao cấp'
        }
        style_label = style_labels.get(travel_style, 'tiêu chuẩn')
        return f"Chuyến đi {style_label} {days} ngày đến {destination} với lịch trình đầy đủ và chi tiết"


# Singleton instance
_planning_tools = None

def get_planning_tools() -> PlanningTools:
    """Get singleton PlanningTools instance"""
    global _planning_tools
    if _planning_tools is None:
        _planning_tools = PlanningTools()
    return _planning_tools
