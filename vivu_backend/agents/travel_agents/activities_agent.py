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
        # Bỏ qua nếu có lỗi (như ChromaDB panic)
        self.vector_db = None
        try:
            from agents.travel_agents.vector_db import get_vector_db_agent
            self.vector_db = get_vector_db_agent()
            if self.vector_db and self.vector_db.collection:
                logger.info("Vector DB initialized for Activities Agent")
            else:
                self.vector_db = None
        except (Exception, BaseException) as e:
            # Bắt cả BaseException để catch panic từ Rust
            logger.warning(f"Vector DB not available for Activities Agent: {type(e).__name__}: {e}")
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
            
            # Tìm kiếm hoạt động - Ưu tiên Vector DB, fallback to database và tools
            activities = []
            
            if self.vector_db and self.vector_db.collection:
                try:
                    # Tìm địa điểm tham quan từ vector DB
                    query = f"Điểm tham quan du lịch tại {destination}. Hoạt động thú vị phù hợp phong cách {travel_style}"
                    if activity_type:
                        query += f". Loại: {activity_type}"
                    
                    # Sử dụng async method để tránh blocking và panic
                    vector_results = await self.vector_db.semantic_search_async(
                        query=query,
                        n_results=15,
                        city_filter=destination
                    )
                    
                    # Chuyển đổi format từ vector DB sang format của activities
                    vector_activities = []
                    for result in vector_results:
                        # Chỉ lấy địa điểm tham quan, không phải khách sạn/nhà hàng
                        category = result.get('category', '').lower()
                        if 'khách sạn' not in category and 'nhà hàng' not in category and 'restaurant' not in category and 'hotel' not in category:
                            vector_activities.append({
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
                    
                    activities = vector_activities
                    logger.info(f"Found {len(activities)} activities from vector DB")
                    
                    # Nếu không đủ, bổ sung từ database và tools
                    if len(activities) < 5:
                        # Query từ database (sync_to_async)
                        db_activities = await self._query_fallback_activities_from_db(destination)
                        if db_activities:
                            existing_names = {a.get('name', '').lower() for a in activities}
                            for act in db_activities:
                                if act.get('name', '').lower() not in existing_names:
                                    activities.append(act)
                        
                        # Nếu vẫn không đủ, bổ sung từ tools
                        if len(activities) < 5:
                            tools_activities = self.activities_tools.search_activities(
                                destination=destination,
                                activity_type=activity_type,
                                travel_style=travel_style
                            )
                            # Merge, tránh duplicate
                            existing_names = {a.get('name', '').lower() for a in activities}
                            for act in tools_activities:
                                if act.get('name', '').lower() not in existing_names:
                                    act['source'] = 'tools'
                                    activities.append(act)
                        
                except Exception as e:
                    logger.warning(f"Vector DB search failed, using database and tools fallback: {e}")
                    # Query từ database trước
                    db_activities = await self._query_fallback_activities_from_db(destination)
                    activities = db_activities if db_activities else []
                    
                    # Bổ sung từ tools
                    tools_activities = self.activities_tools.search_activities(
                        destination=destination,
                        activity_type=activity_type,
                        travel_style=travel_style
                    )
                    existing_names = {a.get('name', '').lower() for a in activities}
                    for act in tools_activities:
                        if act.get('name', '').lower() not in existing_names:
                            activities.append(act)
            else:
                # Fallback to database và tools
                db_activities = await self._query_fallback_activities_from_db(destination)
                activities = db_activities if db_activities else []
                
                # Nếu vẫn không có, thử tools
                if len(activities) < 3:
                    tools_activities = self.activities_tools.search_activities(
                        destination=destination,
                        activity_type=activity_type,
                        travel_style=travel_style
                    )
                    existing_names = {a.get('name', '').lower() for a in activities}
                    for act in tools_activities:
                        if act.get('name', '').lower() not in existing_names:
                            activities.append(act)
                
                # Nếu vẫn không có activities, đảm bảo có ít nhất generic fallback
                if len(activities) == 0:
                    logger.warning(f"No activities found for {destination}, ensuring generic fallback")
                    # Query lại database để lấy generic fallback
                    db_activities = await self._query_fallback_activities_from_db(destination)
                    if db_activities:
                        activities = db_activities
            
            # Đảm bảo có ít nhất 2 activities (generic fallback)
            # Đây là safety net cuối cùng - luôn có activities
            if len(activities) == 0:
                logger.error(f"CRITICAL: No activities at all for {destination}, creating emergency fallback")
                # Emergency fallback - tạo generic activities (không hardcode tên địa điểm)
                # Check travel_style để include wellness/spa activities nếu cần
                travel_style = state.get('travel_style', 'standard')
                travel_style_lower = str(travel_style).lower()
                has_wellness = 'wellness' in travel_style_lower or 'spa' in travel_style_lower
                has_romantic = 'romantic' in travel_style_lower
                
                activities = []
                
                # Add wellness/spa activity if needed
                if has_wellness:
                    activities.append({
                        'name': f'Spa & Wellness tại {destination}',
                        'description': f'Thư giãn và chăm sóc sức khỏe tại spa và trung tâm wellness tại {destination}',
                        'category': 'spa',
                        'type': 'wellness',
                        'price_per_person': 500000,  # Premium spa experience
                        'duration_hours': 2.0,
                        'rating': 4.5,
                        'address': destination,
                        'source': 'emergency_fallback',
                        'tags': ['spa', 'wellness', 'massage', 'relaxation']
                    })
                
                # Add romantic activity if needed
                if has_romantic:
                    activities.append({
                        'name': f'Trải nghiệm lãng mạn tại {destination}',
                        'description': f'Khám phá các điểm lãng mạn và view đẹp tại {destination}',
                        'category': 'romantic',
                        'type': 'sightseeing',
                        'price_per_person': 200000,
                        'duration_hours': 3.0,
                        'rating': 4.5,
                        'address': destination,
                        'source': 'emergency_fallback',
                        'tags': ['romantic', 'scenic', 'viewpoint']
                    })
                
                # Always add generic activities
                activities.extend([
                    {
                        'name': f'Tham quan {destination}',
                        'description': f'Khám phá các điểm tham quan nổi tiếng tại {destination}',
                        'category': 'dia_danh',
                        'type': 'sightseeing',
                        'price_per_person': 0,
                        'duration_hours': 2.0,
                        'rating': 0,
                        'address': destination,
                        'source': 'emergency_fallback',
                        'tags': ['sightseeing', 'exploration']
                    },
                    {
                        'name': f'Bảo tàng/Văn hóa {destination}',
                        'description': f'Tìm hiểu văn hóa và lịch sử địa phương tại {destination}',
                        'category': 'dia_danh',
                        'type': 'museum',
                        'price_per_person': 50000,
                        'duration_hours': 1.5,
                        'rating': 0,
                        'address': destination,
                        'source': 'emergency_fallback',
                        'tags': ['museum', 'cultural']
                    }
                ])
                logger.info(f"Created {len(activities)} emergency fallback activities for {destination}")
            
            logger.info(f"Final activities count: {len(activities)} for {destination}")
            
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
                    # Sử dụng async method để tránh blocking và panic
                    vector_results = await self.vector_db.semantic_search_async(
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
    
    async def _query_fallback_activities_from_db(self, destination: str) -> List[Dict[str, Any]]:
        """
        Query fallback activities từ database (sync_to_async)
        Không hardcode tên thành phố, query động từ database
        """
        try:
            from asgiref.sync import sync_to_async
            from apps.places.models import DiaDiem, TinhThanh
            from django.db.models import Q
            import json
            
            # Sync function để query database
            def _query_sync(dest: str):
                """Sync function để query database - không hardcode"""
                dest_lower = dest.lower().strip()
                
                # Tìm TinhThanh - query động, không hardcode tên thành phố
                # Tìm theo nhiều cách: exact, contains, và các từ khóa trong destination
                # Ví dụ: "Vũng Tàu" có thể match "Bà Rịa – Vũng Tàu"
                dest_keywords = [kw.strip() for kw in dest.split() if len(kw.strip()) > 2]
                
                # Xây dựng Q objects động
                q_objects = [
                    Q(tenTinhThanh__iexact=dest),
                    Q(tenTinhThanh__icontains=dest),
                    Q(tenTinhThanh__icontains=dest_lower)
                ]
                # Thêm Q objects cho từng từ khóa
                for kw in dest_keywords:
                    if len(kw) > 2:
                        q_objects.append(Q(tenTinhThanh__icontains=kw))
                
                # Combine với OR
                from functools import reduce
                from operator import or_
                combined_q = reduce(or_, q_objects)
                
                tinh_thanh = TinhThanh.objects.filter(combined_q).first()
                
                if not tinh_thanh:
                    logger.debug(f"No TinhThanh found for {dest}, returning empty list")
                    return []
                
                # Query fallback activities từ database - động, không hardcode
                fallback_dia_diems = list(
                    DiaDiem.objects.filter(
                        maTinhThanh=tinh_thanh,
                        trangThai='active',
                        loaiDiaDiem__in=['dia_danh', 'giai_tri']
                    )
                    .exclude(loaiDiaDiem__in=['nha_hang', 'khach_san'])
                    .order_by('-danhGiaTrungBinh', '-soLuotDanhGia')[:20]
                )
                
                logger.debug(f"Found {len(fallback_dia_diems)} DiaDiem for {tinh_thanh.tenTinhThanh}")
                
                # Chuyển đổi format
                fallback_activities = []
                for dia_diem in fallback_dia_diems:
                    try:
                        dac_diem = json.loads(dia_diem.dacDiem) if dia_diem.dacDiem else {}
                        
                        # Lấy tất cả địa điểm (không chỉ fallback) để đảm bảo có kết quả
                        # Ưu tiên fallback, nhưng nếu không có thì lấy tất cả
                        if dac_diem.get('is_fallback', False) or len(fallback_activities) < 5:
                            # Map category to type
                            activity_type_map = {
                                'dia_danh': 'sightseeing',
                                'giai_tri': 'entertainment',
                                'mua_sam': 'shopping'
                            }
                            activity_type = dac_diem.get('type', activity_type_map.get(dia_diem.loaiDiaDiem, 'sightseeing'))
                            
                            # Estimate duration
                            duration_map = {
                                'dia_danh': 2.0,
                                'giai_tri': 3.0,
                                'mua_sam': 2.0
                            }
                            duration_hours = dac_diem.get('duration_hours', duration_map.get(dia_diem.loaiDiaDiem, 2.0))
                            
                            fallback_activities.append({
                                'name': dia_diem.tenDiaDiem or '',
                                'description': dia_diem.moTa or '',
                                'category': dia_diem.loaiDiaDiem or 'dia_danh',
                                'type': activity_type,
                                'price_per_person': float(dia_diem.giaVe) if dia_diem.giaVe else 0,
                                'duration_hours': duration_hours,
                                'rating': float(dia_diem.danhGiaTrungBinh) if dia_diem.danhGiaTrungBinh else 0,
                                'address': dia_diem.diaChi or dest,
                                'latitude': float(dia_diem.viDo) if dia_diem.viDo else None,
                                'longitude': float(dia_diem.kinhDo) if dia_diem.kinhDo else None,
                                'source': 'database_fallback' if dac_diem.get('is_fallback') else 'database',
                                'tags': dac_diem.get('tags', [])
                            })
                    except (json.JSONDecodeError, AttributeError, ValueError, TypeError) as e:
                        logger.debug(f"Error parsing dia_diem {dia_diem.maDiaDiem}: {e}")
                        continue
                
                # Nếu không có địa điểm trong database, tạo generic activities
                # Đây là fallback cuối cùng, không hardcode tên địa điểm
                if not fallback_activities and tinh_thanh:
                    logger.debug(f"No activities in database for {tinh_thanh.tenTinhThanh}, creating generic suggestions")
                    # Tạo generic activities dựa trên loại địa điểm (có thể mở rộng sau)
                    # Không hardcode tên, chỉ tạo generic suggestions
                    fallback_activities = [
                        {
                            'name': f'Tham quan {tinh_thanh.tenTinhThanh}',
                            'description': f'Khám phá các điểm tham quan nổi tiếng tại {tinh_thanh.tenTinhThanh}',
                            'category': 'dia_danh',
                            'type': 'sightseeing',
                            'price_per_person': 0,
                            'duration_hours': 2.0,
                            'rating': 0,
                            'address': tinh_thanh.tenTinhThanh,
                            'latitude': float(tinh_thanh.viDo) if tinh_thanh.viDo else None,
                            'longitude': float(tinh_thanh.kinhDo) if tinh_thanh.kinhDo else None,
                            'source': 'generic_fallback',
                            'tags': ['sightseeing', 'exploration']
                        },
                        {
                            'name': f'Bảo tàng/Văn hóa {tinh_thanh.tenTinhThanh}',
                            'description': f'Tìm hiểu văn hóa và lịch sử địa phương tại {tinh_thanh.tenTinhThanh}',
                            'category': 'dia_danh',
                            'type': 'museum',
                            'price_per_person': 50000,
                            'duration_hours': 1.5,
                            'rating': 0,
                            'address': tinh_thanh.tenTinhThanh,
                            'latitude': float(tinh_thanh.viDo) if tinh_thanh.viDo else None,
                            'longitude': float(tinh_thanh.kinhDo) if tinh_thanh.kinhDo else None,
                            'source': 'generic_fallback',
                            'tags': ['museum', 'cultural']
                        }
                    ]
                
                return fallback_activities
            
            # Chạy sync function trong async context
            fallback_activities = await sync_to_async(_query_sync)(destination)
            
            if fallback_activities:
                logger.info(f"Found {len(fallback_activities)} fallback activities from database for {destination}")
            
            return fallback_activities
            
        except Exception as e:
            logger.warning(f"Failed to query fallback activities from database: {e}")
            return []

