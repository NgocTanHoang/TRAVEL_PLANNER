"""
Activities Agent - Agent hoạt động & ăn uống
=============================================
Chịu trách nhiệm:
- Tìm kiếm địa điểm tham quan (sử dụng Vector Database)
- Tính chi phí hoạt động
- Đề xuất nhà hàng (sử dụng Vector Database)
- Tính chi phí ăn uống
"""
import logging
from typing import Dict, Any, Optional, List
from ..base_agent import BaseAgent
from tools.activities_tools import get_activities_tools

logger = logging.getLogger(__name__)


class ActivitiesAgent(BaseAgent):
    """Agent xử lý hoạt động và ăn uống"""
    
    def __init__(self):
        super().__init__(
            agent_name="activities_agent",
            description="Handles activities, dining, and entertainment"
        )
        self.activities_tools = get_activities_tools()
        
        # Vector Database Agent để tìm kiếm địa điểm
        try:
            from agents.travel_agents.vector_db import get_vector_db_agent
            self.vector_db = get_vector_db_agent()
            logger.info("Vector DB initialized for Activities Agent")
        except Exception as e:
            logger.warning(f"Vector DB not available for Activities Agent: {e}")
            self.vector_db = None
    
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Xử lý yêu cầu tìm hoạt động và tính chi phí
        
        Args:
            state: State dictionary với:
                - destination: Điểm đến
                - days: Số ngày
                - travelers: Số người
                - travel_style: 'budget', 'standard', 'luxury'
                - activity_type: Loại hoạt động (optional)
                
        Returns:
            Updated state với hoạt động và chi phí ăn uống
        """
        self.log_input(state)
        
        try:
            destination = state.get('destination')
            days = state.get('days', 1)
            travelers = state.get('travelers', 1)
            travel_style = state.get('travel_style', 'standard')
            activity_type = state.get('activity_type')
            
            if not destination:
                state['activities_error'] = 'Missing destination'
                return state
            
            # Tìm kiếm hoạt động - Ưu tiên Vector DB, fallback to tools
            if self.vector_db and self.vector_db.collection:
                try:
                    # Tìm địa điểm tham quan từ vector DB
                    query = f"Điểm tham quan du lịch tại {destination}. Hoạt động thú vị phù hợp phong cách {travel_style}"
                    if activity_type:
                        query += f". Loại: {activity_type}"
                    
                    vector_results = self.vector_db.semantic_search(
                        query=query,
                        n_results=15,
                        city_filter=destination
                    )
                    
                    # Chuyển đổi format từ vector DB sang format của activities
                    activities = []
                    for result in vector_results:
                        # Chỉ lấy địa điểm tham quan, không phải khách sạn/nhà hàng
                        category = result.get('category', '').lower()
                        if 'khách sạn' not in category and 'nhà hàng' not in category and 'restaurant' not in category and 'hotel' not in category:
                            activities.append({
                                'name': result.get('name', ''),
                                'description': result.get('description', ''),
                                'category': result.get('category', ''),
                                'rating': result.get('rating', 0),
                                'price': result.get('price', 0),
                                'price_per_person': result.get('price', 0),
                                'address': result.get('address', ''),
                                'latitude': result.get('latitude'),
                                'longitude': result.get('longitude'),
                                'image_url': result.get('image_url', ''),
                                'source': 'vector_db',
                                'similarity_score': result.get('similarity_score', 0)
                            })
                    
                    logger.info(f"Found {len(activities)} activities from vector DB")
                    
                    # Nếu không đủ, bổ sung từ tools
                    if len(activities) < 5:
                        tools_activities = self.activities_tools.search_activities(
                            destination=destination,
                            activity_type=activity_type,
                            travel_style=travel_style
                        )
                        # Merge, tránh duplicate
                        existing_names = {a.get('name', '') for a in activities}
                        for act in tools_activities:
                            if act.get('name', '') not in existing_names:
                                act['source'] = 'tools'
                                activities.append(act)
                        
                except Exception as e:
                    logger.warning(f"Vector DB search failed, using tools fallback: {e}")
                    activities = self.activities_tools.search_activities(
                        destination=destination,
                        activity_type=activity_type,
                        travel_style=travel_style
                    )
            else:
                # Fallback to tools
                activities = self.activities_tools.search_activities(
                    destination=destination,
                    activity_type=activity_type,
                    travel_style=travel_style
                )
            
            # Tính chi phí hoạt động
            activities_cost = self.activities_tools.calculate_activity_cost(
                activities=activities,
                travelers=travelers
            )
            
            # Tìm kiếm nhà hàng - Ưu tiên Vector DB, fallback to tools
            if self.vector_db and self.vector_db.collection:
                try:
                    # Tìm nhà hàng từ vector DB
                    query = f"Nhà hàng quán ăn ẩm thực tại {destination}"
                    vector_results = self.vector_db.semantic_search(
                        query=query,
                        n_results=10,
                        city_filter=destination
                    )
                    
                    restaurants = []
                    for result in vector_results:
                        category = result.get('category', '').lower()
                        if 'nhà hàng' in category or 'quán ăn' in category or 'ẩm thực' in category:
                            restaurants.append({
                                'name': result.get('name', ''),
                                'description': result.get('description', ''),
                                'rating': result.get('rating', 0),
                                'price': result.get('price', 0),
                                'price_level': result.get('price_level', 0),
                                'address': result.get('address', ''),
                                'latitude': result.get('latitude'),
                                'longitude': result.get('longitude'),
                                'image_url': result.get('image_url', ''),
                                'source': 'vector_db',
                                'similarity_score': result.get('similarity_score', 0)
                            })
                    
                    logger.info(f"Found {len(restaurants)} restaurants from vector DB")
                    
                    # Nếu không đủ, bổ sung từ tools với nhiều kết quả hơn
                    if len(restaurants) < 10:
                        tools_restaurants = self.activities_tools.search_restaurants(
                            destination=destination
                        )
                        existing_names = {r.get('name', '') for r in restaurants}
                        for rest in tools_restaurants:
                            if rest.get('name', '') not in existing_names:
                                rest['source'] = 'tools'
                                restaurants.append(rest)
                    
                except Exception as e:
                    logger.warning(f"Vector DB restaurant search failed, using tools fallback: {e}")
                    restaurants = self.activities_tools.search_restaurants(
                        destination=destination
                    )
            else:
                # Fallback to tools
                restaurants = self.activities_tools.search_restaurants(
                    destination=destination
                )
            
            # Tính chi phí ăn uống
            dining_cost = self.activities_tools.calculate_dining_cost(
                days=days,
                travelers=travelers,
                travel_style=travel_style
            )
            
            state['activities'] = activities
            state['activities_cost'] = activities_cost
            state['restaurants'] = restaurants
            state['dining_cost'] = dining_cost['total_vnd']
            state['dining_breakdown'] = dining_cost['breakdown']
            
            self.log_output(state)
            return state
            
        except Exception as e:
            self.log_error(e, context={'state': state})
            state['activities_error'] = str(e)
            return state

