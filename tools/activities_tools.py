"""
Activities Tools - Công cụ hoạt động & ăn uống
===============================================
- Tìm kiếm địa điểm tham quan
- Tính chi phí hoạt động
- Đề xuất nhà hàng (sử dụng SerpAPI)
- Tính chi phí ăn uống
"""
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class ActivitiesTools:
    """Công cụ hoạt động cho Activities Agent"""
    
    def __init__(self):
        # SerpAPI for Google Restaurants search
        try:
            from tools.serpapi_tools import get_serpapi_tools
            self.serpapi = get_serpapi_tools()
        except Exception as e:
            logger.warning(f"SerpAPI tools not available: {e}")
            self.serpapi = None
    
    # Chi phí tham quan ước tính (VNĐ/người)
    ACTIVITY_COSTS = {
        'museum': 50000,
        'temple': 30000,
        'park': 0,  # Miễn phí
        'beach': 0,
        'mountain': 0,
        'amusement_park': 300000,
        'zoo': 100000,
        'aquarium': 150000,
        'show': 500000,
        'tour': 500000
    }
    
    # Chi phí ăn uống ước tính (VNĐ/người/bữa)
    DINING_COSTS = {
        'breakfast': {'budget': 50000, 'standard': 100000, 'luxury': 200000},
        'lunch': {'budget': 100000, 'standard': 200000, 'luxury': 400000},
        'dinner': {'budget': 150000, 'standard': 300000, 'luxury': 600000},
        'snack': {'budget': 30000, 'standard': 50000, 'luxury': 100000},
        'drink': {'budget': 20000, 'standard': 40000, 'luxury': 80000},
        'afternoon_tea': {'budget': 50000, 'standard': 100000, 'luxury': 200000}
    }
    
    def search_activities(
        self,
        destination: str,
        activity_type: Optional[str] = None,
        max_price: Optional[float] = None,
        travel_style: str = 'standard'
    ) -> List[Dict[str, Any]]:
        """
        Tìm kiếm hoạt động/địa điểm tham quan
        
        Sử dụng Vector DB với semantic search để tìm hoạt động phù hợp nhất
        
        Args:
            destination: Điểm đến
            activity_type: Loại hoạt động (optional)
            max_price: Giá tối đa (VNĐ, optional)
            travel_style: Phong cách du lịch
            
        Returns:
            List các hoạt động
        """
        activities = []
        
        # Ưu tiên sử dụng Vector DB để tìm kiếm semantic
        try:
            from agents.travel_agents.vector_db import get_vector_db_agent
            vector_db = get_vector_db_agent()
            
            if vector_db and vector_db.collection:
                # Xây dựng query tự nhiên dựa trên destination và activity_type
                if activity_type:
                    query = f"Điểm tham quan {activity_type} tại {destination}. Hoạt động du lịch thú vị, phù hợp phong cách {travel_style}"
                else:
                    query = f"Điểm tham quan du lịch tại {destination}. Hoạt động thú vị, phù hợp phong cách {travel_style}. Địa điểm nổi tiếng, hấp dẫn"
                
                # Semantic search với Vector DB
                vector_results = vector_db.semantic_search(
                    query=query,
                    n_results=15,
                    city_filter=destination
                )
                
                # Chuyển đổi format từ vector DB
                for result in vector_results:
                    category = result.get('category', '').lower()
                    # Chỉ lấy địa điểm tham quan, không phải khách sạn/nhà hàng
                    if 'khách sạn' not in category and 'nhà hàng' not in category and 'restaurant' not in category and 'hotel' not in category:
                        activities.append({
                            'name': result.get('name', ''),
                            'description': result.get('description', ''),
                            'category': result.get('category', ''),
                            'type': self._map_category_to_type(result.get('category', '')),
                            'price_per_person': result.get('price', 0),
                            'duration_hours': self._estimate_duration(result.get('category', '')),
                            'rating': result.get('rating', 0),
                            'address': result.get('address', destination),
                            'latitude': result.get('latitude'),
                            'longitude': result.get('longitude'),
                            'image_url': result.get('image_url'),  # Thêm image_url từ dataset
                            'province': result.get('province'),  # Thêm province từ dataset
                            'source': 'vector_db',
                            'similarity_score': result.get('similarity_score', 0)
                        })
                
                logger.info(f"Found {len(activities)} activities from Vector DB")
        except Exception as e:
            logger.warning(f"Vector DB search failed: {e}")
        
        # Fallback: Sample data nếu không có Vector DB hoặc không đủ kết quả
        if len(activities) < 3:
            fallback_activities = [
                {
                    'name': f'Tham quan {destination}',
                    'type': 'sightseeing',
                    'price_per_person': 0,
                    'duration_hours': 2,
                    'description': f'Khám phá {destination}',
                    'source': 'fallback'
                },
                {
                    'name': 'Bảo tàng địa phương',
                    'type': 'museum',
                    'price_per_person': 50000,
                    'duration_hours': 1.5,
                    'description': 'Tìm hiểu văn hóa và lịch sử địa phương',
                    'source': 'fallback'
                }
            ]
            # Merge, tránh duplicate
            existing_names = {a.get('name', '') for a in activities}
            for act in fallback_activities:
                if act.get('name', '') not in existing_names:
                    activities.append(act)
        
        # Lọc theo type và price
        if activity_type:
            activities = [a for a in activities if a.get('type') == activity_type]
        
        if max_price:
            activities = [a for a in activities if a.get('price_per_person', 0) <= max_price]
        
        # Sắp xếp theo similarity_score hoặc rating
        activities.sort(key=lambda x: (x.get('similarity_score', 0) or x.get('rating', 0)), reverse=True)
        
        return activities
    
    def _map_category_to_type(self, category: str) -> str:
        """Map category từ DB sang activity type"""
        category_lower = category.lower()
        
        if 'bảo tàng' in category_lower or 'museum' in category_lower:
            return 'museum'
        elif 'chùa' in category_lower or 'đền' in category_lower or 'temple' in category_lower:
            return 'temple'
        elif 'công viên' in category_lower or 'park' in category_lower:
            return 'park'
        elif 'bãi biển' in category_lower or 'beach' in category_lower:
            return 'beach'
        elif 'núi' in category_lower or 'mountain' in category_lower:
            return 'mountain'
        elif 'vui chơi' in category_lower or 'amusement' in category_lower:
            return 'amusement_park'
        elif 'sở thú' in category_lower or 'zoo' in category_lower:
            return 'zoo'
        elif 'thủy cung' in category_lower or 'aquarium' in category_lower:
            return 'aquarium'
        elif 'show' in category_lower or 'biểu diễn' in category_lower:
            return 'show'
        elif 'tour' in category_lower:
            return 'tour'
        else:
            return 'sightseeing'
    
    def _estimate_duration(self, category: str) -> float:
        """Ước tính thời gian tham quan dựa trên category"""
        category_lower = category.lower()
        
        if 'bảo tàng' in category_lower or 'museum' in category_lower:
            return 1.5
        elif 'chùa' in category_lower or 'đền' in category_lower:
            return 1.0
        elif 'công viên' in category_lower or 'park' in category_lower:
            return 2.0
        elif 'bãi biển' in category_lower or 'beach' in category_lower:
            return 3.0
        elif 'núi' in category_lower or 'mountain' in category_lower:
            return 4.0
        elif 'vui chơi' in category_lower or 'amusement' in category_lower:
            return 4.0
        else:
            return 2.0
    
    def calculate_activity_cost(
        self,
        activities: List[Dict],
        travelers: int = 1
    ) -> float:
        """
        Tính tổng chi phí hoạt động
        
        Args:
            activities: Danh sách hoạt động
            travelers: Số người
            
        Returns:
            Tổng chi phí (VNĐ)
        """
        total = 0
        for activity in activities:
            price = activity.get('price_per_person', 0)
            
            # Nếu không có giá, tính dựa trên loại hoạt động
            if price == 0 or price is None:
                activity_type = activity.get('type', 'sightseeing')
                price = self.ACTIVITY_COSTS.get(activity_type, 0)
            
            # Nếu vẫn là 0, kiểm tra category để tính giá vé
            if price == 0:
                category = activity.get('category', '').lower()
                name = activity.get('name', '').lower()
                
                # Tính giá vé cho các địa điểm có phí
                if any(keyword in category or keyword in name for keyword in ['bảo tàng', 'museum']):
                    price = self.ACTIVITY_COSTS['museum']
                elif any(keyword in category or keyword in name for keyword in ['lăng', 'đền', 'chùa', 'temple']):
                    price = self.ACTIVITY_COSTS['temple']
                elif any(keyword in category or keyword in name for keyword in ['vui chơi', 'amusement', 'công viên giải trí']):
                    price = self.ACTIVITY_COSTS['amusement_park']
                elif any(keyword in category or keyword in name for keyword in ['sở thú', 'zoo']):
                    price = self.ACTIVITY_COSTS['zoo']
                elif any(keyword in category or keyword in name for keyword in ['thủy cung', 'aquarium']):
                    price = self.ACTIVITY_COSTS['aquarium']
                elif any(keyword in category or keyword in name for keyword in ['show', 'biểu diễn']):
                    price = self.ACTIVITY_COSTS['show']
                elif any(keyword in category or keyword in name for keyword in ['tour', 'du lịch']):
                    price = self.ACTIVITY_COSTS['tour']
                # Các địa điểm như công viên, bãi biển, núi thường miễn phí
            
            total += price * travelers
        
        return round(total)
    
    def search_restaurants(
        self,
        destination: str,
        meal_type: Optional[str] = None,
        max_price: Optional[float] = None,
        cuisine: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Tìm kiếm nhà hàng
        
        Args:
            destination: Điểm đến
            meal_type: Loại bữa ăn (breakfast, lunch, dinner)
            max_price: Giá tối đa (VNĐ/người, optional)
            cuisine: Loại ẩm thực (optional)
            
        Returns:
            List các nhà hàng
        """
        restaurants = []
        
        # Ưu tiên SerpAPI (Google Search) - tìm nhà hàng thực tế
        if self.serpapi and self.serpapi.api_key:
            try:
                # Xây dựng query dựa trên meal_type và cuisine
                query_parts = ['nhà hàng']
                if cuisine:
                    query_parts.append(cuisine)
                if meal_type:
                    meal_map = {
                        'breakfast': 'bữa sáng',
                        'lunch': 'bữa trưa',
                        'dinner': 'bữa tối'
                    }
                    query_parts.append(meal_map.get(meal_type, meal_type))
                
                query = ' '.join(query_parts) if len(query_parts) > 1 else 'nhà hàng'
                
                serpapi_result = self.serpapi.search_restaurants(
                    destination, query=query, num_results=20
                )
                
                if serpapi_result.get('status') == 'success' and serpapi_result.get('restaurants'):
                    for restaurant in serpapi_result['restaurants']:
                        restaurants.append({
                            'name': restaurant.get('name', 'Unknown Restaurant'),
                            'description': restaurant.get('description', ''),
                            'cuisine': cuisine or 'Vietnamese',
                            'price_range': restaurant.get('price_level', 'medium'),
                            'rating': restaurant.get('rating', 0),
                            'reviews': restaurant.get('reviews', 0),
                            'address': restaurant.get('address', destination),
                            'link': restaurant.get('link', ''),
                            'phone': restaurant.get('phone', ''),
                            'source': restaurant.get('source', 'serpapi')
                        })
                    logger.info(f"Found {len(restaurants)} restaurants from SerpAPI")
            except Exception as e:
                logger.warning(f"SerpAPI restaurants search failed: {e}")
        
        # Fallback: Sample data nếu không có SerpAPI
        if not restaurants:
            restaurants = [
                {
                    'name': f'Nhà hàng địa phương {destination}',
                    'cuisine': cuisine or 'Vietnamese',
                    'price_range': 'medium',
                    'rating': 4.5,
                    'address': destination,
                    'source': 'sample'
                }
            ]
        
        # Lọc theo max_price nếu có
        if max_price:
            # Ước tính giá từ price_range hoặc rating
            filtered = []
            for rest in restaurants:
                # Ước tính giá dựa trên rating (giả sử rating cao = giá cao)
                estimated_price = rest.get('rating', 0) * 100000  # Ước tính đơn giản
                if estimated_price <= max_price:
                    filtered.append(rest)
            restaurants = filtered if filtered else restaurants
        
        return restaurants
    
    def calculate_dining_cost(
        self,
        days: int,
        travelers: int,
        travel_style: str = 'standard'
    ) -> Dict[str, Any]:
        """
        Tính tổng chi phí ăn uống
        
        Args:
            days: Số ngày
            travelers: Số người
            travel_style: 'budget', 'standard', 'luxury'
            
        Returns:
            Dict với breakdown chi tiết
        """
        costs = self.DINING_COSTS
        
        breakfast_cost = costs['breakfast'][travel_style] * days * travelers
        lunch_cost = costs['lunch'][travel_style] * days * travelers
        dinner_cost = costs['dinner'][travel_style] * days * travelers
        snack_cost = costs['snack'][travel_style] * days * travelers * 1.5  # 1.5 snack/ngày
        drink_cost = costs['drink'][travel_style] * days * travelers * 2  # 2 lần giải khát/ngày
        
        # Trà chiều chỉ cho standard và luxury
        afternoon_tea_cost = 0
        if travel_style in ['standard', 'luxury']:
            afternoon_tea_cost = costs['afternoon_tea'][travel_style] * days * travelers
        
        total = breakfast_cost + lunch_cost + dinner_cost + snack_cost + drink_cost + afternoon_tea_cost
        
        return {
            'total_vnd': round(total),
            'breakdown': {
                'breakfast': round(breakfast_cost),
                'lunch': round(lunch_cost),
                'dinner': round(dinner_cost),
                'snacks': round(snack_cost),
                'drinks': round(drink_cost),
                'afternoon_tea': round(afternoon_tea_cost)
            },
            'per_person_per_day': round(total / (days * travelers)),
            'travel_style': travel_style
        }
    
    def suggest_activities_for_day(
        self,
        destination: str,
        day: int,
        time_slot: str = 'morning'
    ) -> List[Dict[str, Any]]:
        """
        Đề xuất hoạt động cho một khung giờ trong ngày
        
        Args:
            destination: Điểm đến
            day: Số thứ tự ngày
            time_slot: 'morning', 'afternoon', 'evening', 'night'
            
        Returns:
            List hoạt động đề xuất
        """
        # Logic đề xuất theo time slot
        suggestions = {
            'morning': ['sightseeing', 'museum', 'park'],
            'afternoon': ['beach', 'mountain', 'tour'],
            'evening': ['restaurant', 'show', 'walking'],
            'night': ['restaurant', 'night_market', 'bar']
        }
        
        activity_types = suggestions.get(time_slot, ['sightseeing'])
        activities = []
        
        for activity_type in activity_types[:2]:  # Lấy 2 hoạt động
            activity_list = self.search_activities(destination, activity_type)
            if activity_list:
                activities.append(activity_list[0])
        
        return activities


# Singleton instance
_activities_tools = None

def get_activities_tools() -> ActivitiesTools:
    """Get singleton ActivitiesTools instance"""
    global _activities_tools
    if _activities_tools is None:
        _activities_tools = ActivitiesTools()
    return _activities_tools

