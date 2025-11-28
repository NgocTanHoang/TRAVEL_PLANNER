"""
Activities Tools - Công cụ hoạt động & ăn uống
===============================================
- Tìm kiếm địa điểm tham quan
- Tính chi phí hoạt động
- Đề xuất nhà hàng (sử dụng SerpAPI + Tavily)
- Tính chi phí ăn uống
"""
import logging
import os
from typing import Dict, Any, Optional, List
from tools.vietmap_tools import get_vietmap_tools

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
        
        # Tavily for web search and enrichment
        self.tavily_api_key = os.getenv('TAVILY_API_KEY', '')
        self.tavily = None
        if self.tavily_api_key:
            try:
                from tavily import TavilyClient
                self.tavily = TavilyClient(api_key=self.tavily_api_key)
                logger.info("Tavily client initialized for ActivitiesTools")
            except Exception as e:
                logger.warning(f"Tavily not available: {e}")
                self.tavily = None
    
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
        activities: List[Dict[str, Any]] = []
        
        # Ưu tiên sử dụng Vector DB để tìm kiếm semantic
        vector_db = None
        try:
            from agents.travel_agents.vector_db import get_vector_db_agent
            vector_db = get_vector_db_agent()
        except (Exception, SystemExit, KeyboardInterrupt) as e:
            # Bắt tất cả exceptions, kể cả panic từ Rust/ChromaDB
            logger.debug(f"Vector DB not available: {type(e).__name__}: {e}")
            vector_db = None
        except BaseException as e:
            # Bắt cả BaseException (bao gồm SystemExit, KeyboardInterrupt)
            logger.debug(f"Vector DB not available (BaseException): {type(e).__name__}: {e}")
            vector_db = None
        
        if vector_db and vector_db.collection:
            try:
                # Xây dựng query tự nhiên dựa trên destination và activity_type
                # Augment query for wellness/spa activities
                base_query = f"Điểm tham quan du lịch tại {destination}"
                
                # Check if travel_style includes wellness/spa keywords
                travel_style_lower = str(travel_style).lower()
                if 'wellness' in travel_style_lower or 'spa' in travel_style_lower:
                    base_query += " spa OR wellness OR 'massage' OR 'retreat' OR 'hot springs' OR 'therapeutic'"
                
                if activity_type:
                    query = f"{base_query} {activity_type}. Hoạt động du lịch thú vị, phù hợp phong cách {travel_style}"
                else:
                    query = f"{base_query}. Hoạt động thú vị, phù hợp phong cách {travel_style}. Địa điểm nổi tiếng, hấp dẫn"
                
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
                        activity_name = result.get('name', '')
                        description = result.get('description', '')
                        
                        # Enrich với Tavily nếu mô tả quá ngắn hoặc thiếu
                        if self.tavily and (not description or len(description) < 100):
                            try:
                                tavily_info = self._enrich_with_tavily(activity_name, destination)
                                if tavily_info:
                                    description = tavily_info.get('description', description)
                                    if result.get('rating', 0) == 0 and tavily_info.get('rating'):
                                        result['rating'] = tavily_info['rating']
                            except Exception as e:
                                logger.debug(f"Tavily enrichment failed for {activity_name}: {e}")
                        
                        activities.append({
                            'name': activity_name,
                            'description': description,
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
        
        # Fallback: Query từ database nếu không có Vector DB hoặc không đủ kết quả
        # Note: Function này được gọi từ async context, nên không thể query Django ORM trực tiếp
        # Query sẽ được thực hiện trong ActivitiesAgent với sync_to_async
        if len(activities) < 5:
            logger.debug(f"Insufficient activities ({len(activities)}), trying VietMap places API for real locations")
            try:
                vietmap = get_vietmap_tools()
            except Exception as e:
                logger.warning(f"VietMap tools not available in ActivitiesTools: {e}")
                vietmap = None

            if vietmap:
                try:
                    type_keyword_map = {
                        'beach': 'bãi biển',
                        'museum': 'bảo tàng',
                        'park': 'công viên',
                        'temple': 'chùa',
                        'mountain': 'núi',
                        'amusement_park': 'khu vui chơi',
                        'tour': 'khu du lịch',
                    }

                    base_query = 'địa điểm du lịch'
                    if activity_type:
                        base_query = type_keyword_map.get(activity_type, activity_type)

                    vietmap_query = f"{base_query} {destination}".strip()

                    vietmap_results = vietmap.search_places(
                        query=vietmap_query,
                        location=destination,
                        radius=10,
                        limit=15,
                    )

                    existing_names = {a.get('name', '').lower() for a in activities}

                    for item in vietmap_results:
                        name = (item.get('name') or item.get('address') or destination).strip()
                        if not name:
                            continue
                        key = name.lower()
                        if key in existing_names:
                            continue

                        category_raw = str(item.get('category') or '')
                        category_lower = category_raw.lower()
                        if 'restaurant' in category_lower or 'nhà hàng' in category_lower:
                            continue
                        if 'hotel' in category_lower or 'khách sạn' in category_lower:
                            continue

                        activity_type_mapped = self._map_category_to_type(category_raw)
                        price_per_person = self.ACTIVITY_COSTS.get(activity_type_mapped, 0)
                        duration_hours = self._estimate_duration(category_raw)

                        activities.append({
                            'name': name,
                            'description': item.get('address') or name,
                            'category': category_raw or 'sightseeing',
                            'type': activity_type_mapped,
                            'price_per_person': price_per_person,
                            'duration_hours': duration_hours,
                            'rating': item.get('rating') or 0,
                            'address': item.get('address') or destination,
                            'latitude': item.get('lat'),
                            'longitude': item.get('lon'),
                            'source': 'vietmap',
                            'similarity_score': 0,
                        })

                        existing_names.add(key)

                    if vietmap_results:
                        logger.info(f"Found {len(vietmap_results)} activities from VietMap places API for {destination}")
                except Exception as e:
                    logger.warning(f"VietMap activities search failed for {destination}: {e}")
        
        # Lọc theo type và price
        if activity_type:
            activities = [a for a in activities if a.get('type') == activity_type]
        
        if max_price:
            activities = [a for a in activities if a.get('price_per_person', 0) <= max_price]
        
        # Sắp xếp theo similarity_score hoặc rating
        activities.sort(key=lambda x: (x.get('similarity_score', 0) or x.get('rating', 0)), reverse=True)
        
        return activities
    
    def _enrich_with_tavily(
        self, 
        name: str, 
        location: str, 
        search_type: str = 'activity'
    ) -> Optional[Dict[str, Any]]:
        """
        Enrich thông tin với Tavily API
        
        Args:
            name: Tên địa điểm/hoạt động
            location: Địa điểm (thành phố)
            search_type: 'activity' hoặc 'restaurant'
            
        Returns:
            Dict với thông tin bổ sung hoặc None
        """
        if not self.tavily:
            return None
        
        try:
            # Xây dựng query
            if search_type == 'restaurant':
                query = f"{name} nhà hàng {location} Việt Nam review đánh giá"
            else:
                query = f"{name} {location} Việt Nam du lịch địa điểm tham quan"
            
            results = self.tavily.search(
                query=query,
                search_depth="basic",
                max_results=3
            )
            
            if results and results.get('results'):
                # Lấy thông tin từ kết quả đầu tiên
                first_result = results['results'][0]
                content = first_result.get('content', '')
                
                # Extract rating từ content nếu có
                rating = None
                if content:
                    # Tìm rating dạng "4.5/5" hoặc "4.5 stars"
                    import re
                    rating_match = re.search(r'(\d+\.?\d*)\s*/\s*5|(\d+\.?\d*)\s*star', content, re.IGNORECASE)
                    if rating_match:
                        rating = float(rating_match.group(1) or rating_match.group(2))
                
                return {
                    'description': content[:500] if content else '',  # Giới hạn 500 ký tự
                    'rating': rating,
                    'source_url': first_result.get('url', '')
                }
        except Exception as e:
            logger.debug(f"Tavily search error for {name}: {e}")
        
        return None

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
            # Ưu tiên price_per_person từ activity (giá thực tế từ database)
            price = activity.get('price_per_person', 0)
            
            # Nếu không có price_per_person, thử lấy từ 'price'
            if price == 0 or price is None:
                price = activity.get('price', 0)
            
            # Nếu vẫn không có giá từ database, estimate dựa trên category
            # (chỉ khi không có giá thực tế)
            source = activity.get('source', '').lower()
            if (price == 0 or price is None) and 'database' not in source:
                # Chỉ estimate nếu không phải từ database
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
            # Nếu từ database mà không có giá, giữ nguyên 0 (miễn phí)
            
            # Tính tổng chi phí
            total += price * travelers
        
        # Đảm bảo có ít nhất một ước tính cơ bản nếu không có giá
        # Nếu total = 0 và có activities, ước tính tối thiểu
        if total == 0 and len(activities) > 0:
            # Ước tính tối thiểu: 50,000 VNĐ/người/activity
            estimated_per_activity = 50000
            # Ước tính dựa trên số activities và số ngày (tối đa 2 activities/ngày)
            num_activities_to_charge = min(len(activities), max(1, len(activities) // 2))
            total = estimated_per_activity * travelers * num_activities_to_charge
            logger.debug(f"No activity prices found, using minimum estimate: {total:,} VNĐ for {len(activities)} activities")
        
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
                # Xây dựng query cụ thể hơn để tránh kết quả không liên quan
                query_parts = ['nhà hàng', 'quán ăn']
                if cuisine:
                    query_parts.append(cuisine)
                if meal_type:
                    meal_map = {
                        'breakfast': 'bữa sáng',
                        'lunch': 'bữa trưa',
                        'dinner': 'bữa tối'
                    }
                    query_parts.append(meal_map.get(meal_type, meal_type))
                
                # Đảm bảo query có từ khóa về ẩm thực
                query = ' '.join(query_parts) if len(query_parts) > 1 else 'nhà hàng quán ăn ẩm thực'
                
                serpapi_result = self.serpapi.search_restaurants(
                    destination, query=query, num_results=20
                )
                
                if serpapi_result.get('status') == 'success' and serpapi_result.get('restaurants'):
                    for restaurant in serpapi_result['restaurants']:
                        restaurant_name = restaurant.get('name', 'Unknown Restaurant')
                        description = restaurant.get('description', '')
                        
                        # Enrich với Tavily nếu mô tả quá ngắn hoặc thiếu
                        if self.tavily and (not description or len(description) < 100):
                            try:
                                tavily_info = self._enrich_with_tavily(
                                    restaurant_name, 
                                    destination, 
                                    search_type='restaurant'
                                )
                                if tavily_info:
                                    description = tavily_info.get('description', description)
                                    # Cập nhật rating nếu có
                                    if restaurant.get('rating', 0) == 0 and tavily_info.get('rating'):
                                        restaurant['rating'] = tavily_info['rating']
                            except Exception as e:
                                logger.debug(f"Tavily enrichment failed for {restaurant_name}: {e}")
                        
                        # Extract price từ price_level nếu có
                        price_level = restaurant.get('price_level', 'medium')
                        price_vnd = 0
                        
                        # Nếu price_level là string có chứa giá (ví dụ: "100.000 - 200.000 VNĐ")
                        if isinstance(price_level, str):
                            import re
                            # Tìm số trong price_level
                            numbers = re.findall(r'\d+', price_level.replace('.', '').replace(',', ''))
                            if numbers:
                                try:
                                    # Lấy số đầu tiên làm giá ước tính
                                    price_vnd = int(numbers[0])
                                    # Nếu có 2 số, lấy trung bình
                                    if len(numbers) >= 2:
                                        price_vnd = (int(numbers[0]) + int(numbers[1])) // 2
                                except ValueError:
                                    pass
                        
                        restaurants.append({
                            'name': restaurant_name,
                            'description': description,
                            'cuisine': cuisine or 'Vietnamese',
                            'price_range': price_level if isinstance(price_level, str) else 'medium',
                            'price': price_vnd,  # Thêm giá ước tính
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
    
    def _map_travel_style_to_base(self, travel_style: str) -> str:
        """
        Map extended travel styles về base styles (budget, standard, luxury)
        để tương thích với DINING_COSTS
        
        Args:
            travel_style: Travel style (có thể là extended style)
            
        Returns:
            Base style: 'budget', 'standard', hoặc 'luxury'
        """
        # Core styles
        if travel_style in ['budget', 'standard', 'luxury']:
            return travel_style
        
        # Extended styles mapping
        style_mapping = {
            # Gần budget
            'religious': 'budget',
            'eco': 'budget',
            
            # Gần standard
            'adventure': 'standard',
            'cultural': 'standard',
            'family': 'standard',
            'slow': 'standard',
            'digital_nomad': 'standard',
            'photography': 'standard',
            'extreme': 'standard',
            'festival': 'standard',
            
            # Gần luxury
            'gastronomy': 'luxury',
            'wellness': 'luxury',
            'romantic': 'luxury',
            'shop_leisure': 'luxury',
        }
        
        return style_mapping.get(travel_style, 'standard')
    
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
            travel_style: Travel style (có thể là extended style: 'budget', 'standard', 'luxury', 'cultural', 'gastronomy', etc.)
            
        Returns:
            Dict với breakdown chi tiết
        """
        # Map extended style về base style để tương thích với DINING_COSTS
        base_style = self._map_travel_style_to_base(travel_style)
        costs = self.DINING_COSTS
        
        # Đảm bảo base_style tồn tại trong costs
        if base_style not in costs['breakfast']:
            logger.warning(f"Unknown base style '{base_style}', using 'standard'")
            base_style = 'standard'
        
        breakfast_cost = costs['breakfast'][base_style] * days * travelers
        lunch_cost = costs['lunch'][base_style] * days * travelers
        dinner_cost = costs['dinner'][base_style] * days * travelers
        snack_cost = costs['snack'][base_style] * days * travelers * 1.5  # 1.5 snack/ngày
        drink_cost = costs['drink'][base_style] * days * travelers * 2  # 2 lần giải khát/ngày
        
        # Trà chiều chỉ cho standard và luxury
        afternoon_tea_cost = 0
        if base_style in ['standard', 'luxury']:
            afternoon_tea_cost = costs['afternoon_tea'][base_style] * days * travelers
        
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
            'per_person_per_day': round(total / (days * travelers)) if (days * travelers) > 0 else 0,
            'travel_style': travel_style,
            'base_style_used': base_style  # Log để debug
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

