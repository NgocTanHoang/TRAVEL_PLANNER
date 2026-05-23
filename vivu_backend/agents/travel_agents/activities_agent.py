"""
Activities Agent - Agent hoạt động & ăn uống
=============================================
Chịu trách nhiệm:
- Tìm kiếm địa điểm tham quan (sử dụng Vector Database)
- Tính chi phí hoạt động
- Đề xuất nhà hàng (sử dụng Vector Database)
- Tính chi phí ăn uống
- Hiểu ngữ nghĩa và phân loại địa điểm thông minh
"""
import logging
import unicodedata
import re
from typing import Dict, Any, Optional, List
from ..base_agent import BaseAgent
from tools.activities_tools import get_activities_tools
from utils.location_resolver import resolve_best_province, text_matches_province
from utils.semantic_place_classifier import (
    understand_place_semantics,
    is_suitable_for_travel_style,
    classify_place_by_semantics
)

logger = logging.getLogger(__name__)


# Helper functions for robust location normalization/matching
_LOCATION_STOPWORDS = {"thanh", "pho", "thanhpho", "tp", "tinh"}


def _normalize_location_name(name: str) -> str:
    """Normalize Vietnamese location names for comparison.

    Removes diacritics, lowercases, and strips non-alphanumeric characters.
    Example: "Thành phố Đà Nẵng" -> "thanh pho da nang".
    """
    if not name:
        return ""
    # Remove diacritics
    name = unicodedata.normalize("NFKD", str(name))
    name = "".join(c for c in name if not unicodedata.combining(c))
    # Lowercase and keep only letters/digits as space-separated tokens
    name = name.lower()
    name = re.sub(r"[^a-z0-9]+", " ", name)
    return name.strip()


def _tokenize_normalized_name(norm: str) -> set:
    """Tokenize a normalized location string, removing generic stopwords.

    Example: "thanh pho da nang" -> {"da", "nang"}.
    """
    if not norm:
        return set()
    tokens = []
    for token in norm.split():
        if not token:
            continue
        if token in _LOCATION_STOPWORDS:
            continue
        tokens.append(token)
    return set(tokens)


def _normalize_destination_name_for_display(dest: str) -> str:
    """
    Normalize destination name để loại bỏ duplicate và format sai cho display
    
    Args:
        dest: Tên địa điểm có thể bị duplicate hoặc format sai
        
    Returns:
        Tên địa điểm đã được normalize
    """
    if not dest:
        return ""
    
    import re
    
    # Loại bỏ các ký tự đặc biệt và normalize khoảng trắng
    dest = re.sub(r'\s+', ' ', dest.strip())
    
    # Tách các phần bằng dấu phẩy hoặc các ký tự đặc biệt
    parts = re.split(r'[,;|]', dest)
    
    # Lấy phần đầu tiên (thường là tên chính)
    if parts:
        main_part = parts[0].strip()
        
        # Loại bỏ các từ khóa lặp lại
        # Ví dụ: "Xã Kim Trung Huyện Hưng Hà Tỉnh Thái Bình Xã Kim Chung" 
        # -> "Xã Kim Chung, Huyện Hưng Hà, Tỉnh Thái Bình"
        words = main_part.split()
        seen_words = set()
        cleaned_words = []
        
        for word in words:
            word_lower = word.lower()
            # Bỏ qua các từ đã xuất hiện (tránh duplicate), nhưng giữ lại các từ địa danh
            if word_lower not in seen_words or word_lower in ['xã', 'huyện', 'tỉnh', 'thành', 'phố', 'quận', 'phường']:
                cleaned_words.append(word)
                seen_words.add(word_lower)
        
        result = ' '.join(cleaned_words)
        
        # Nếu có các phần khác, thêm vào (nhưng đã được format)
        if len(parts) > 1:
            # Lấy phần cuối cùng (thường là địa chỉ đầy đủ)
            last_part = parts[-1].strip()
            if last_part and last_part != result:
                # Chỉ thêm nếu khác với phần chính
                result = f"{result}, {last_part}"
        
        return result
    
    return dest.strip()


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
            
            # Normalize destination name để loại bỏ duplicate và format sai
            destination_normalized = _normalize_destination_name_for_display(destination)
            if destination_normalized != destination:
                logger.info(f"Normalized destination: '{destination}' -> '{destination_normalized}'")
                destination = destination_normalized
                state['destination'] = destination  # Update state với normalized destination

            resolved_province = await self._resolve_destination_province(destination)
            if not resolved_province:
                state['activities_error'] = f"Khong the map destination '{destination}' vao TINHTHANH."
                return state
            state['resolved_destination_province'] = resolved_province
            
            # Tìm kiếm hoạt động - Ưu tiên Database, sau đó Tools, cuối cùng Vector DB (nếu cần)
            activities = []
            
            # Normalize destination để so sánh
            dest_normalized = _normalize_location_name(destination)
            dest_tokens = _tokenize_normalized_name(dest_normalized)
            
            # Bước 1: Query từ database (ưu tiên cao nhất)
            db_activities = await self._query_fallback_activities_from_db(destination, resolved_province)
            if db_activities:
                # Filter activities: loại bỏ những activity có tên giống destination
                filtered_db_activities = []
                for act in db_activities:
                    act_name = act.get('name', '')
                    if not act_name:
                        continue
                    
                    # Bỏ qua nếu tên quá dài (có thể là địa chỉ đầy đủ)
                    if len(act_name) > 100:
                        continue
                    
                    # Bỏ qua nếu tên giống destination
                    act_normalized = _normalize_location_name(act_name)
                    act_tokens = _tokenize_normalized_name(act_normalized)
                    
                    # Kiểm tra xem activity name có giống destination không
                    if act_tokens and dest_tokens:
                        # Nếu activity name chứa quá nhiều tokens giống destination, bỏ qua
                        common_tokens = act_tokens & dest_tokens
                        if len(common_tokens) >= min(3, len(dest_tokens)) and len(act_tokens) <= len(dest_tokens) + 2:
                            logger.debug(f"Filtered out activity '{act_name}' - too similar to destination")
                            continue
                    
                    # Bỏ qua nếu tên chính xác giống destination (case-insensitive)
                    if act_name.lower().strip() == destination.lower().strip():
                        logger.debug(f"Filtered out activity '{act_name}' - exact match with destination")
                        continue
                    
                    filtered_db_activities.append(act)
                
                activities = filtered_db_activities
                logger.info(f"Found {len(activities)} activities from database for {destination} (filtered from {len(db_activities)})")
            
            # Bước 2: Bổ sung từ tools nếu chưa đủ
            if len(activities) < 10:
                tools_activities = self.activities_tools.search_activities(
                    destination=destination,
                    activity_type=activity_type,
                    travel_style=travel_style
                )
                if tools_activities:
                    existing_names = {a.get('name', '').lower() for a in activities}
                    for act in tools_activities:
                        act_name = act.get('name', '')
                        if not act_name or act_name.lower() in existing_names:
                            continue
                        if not self._belongs_to_province(act, resolved_province):
                            continue
                        
                        # Filter: bỏ qua nếu tên quá dài hoặc giống destination
                        if len(act_name) > 100:
                            continue
                        
                        act_normalized = _normalize_location_name(act_name)
                        act_tokens = _tokenize_normalized_name(act_normalized)
                        
                        if act_tokens and dest_tokens:
                            common_tokens = act_tokens & dest_tokens
                            if len(common_tokens) >= min(3, len(dest_tokens)) and len(act_tokens) <= len(dest_tokens) + 2:
                                continue
                        
                        if act_name.lower().strip() == destination.lower().strip():
                            continue
                        
                        act['source'] = 'tools'
                        activities.append(act)
                    logger.info(f"Added {len([a for a in activities if a.get('source') == 'tools'])} activities from tools")
            
            # Bước 3: Vector DB chỉ dùng làm fallback cuối cùng (nếu vẫn chưa đủ và vector DB available)
            if len(activities) < 5 and self.vector_db and self.vector_db.collection:
                try:
                    # Tìm địa điểm tham quan từ vector DB (fallback cuối)
                    query = f"Điểm tham quan du lịch tại {destination}. Hoạt động thú vị phù hợp phong cách {travel_style}"
                    if activity_type:
                        query += f". Loại: {activity_type}"
                    
                    # Sử dụng async method để tránh blocking và panic
                    vector_results = await self.vector_db.semantic_search_async(
                        query=query,
                        n_results=10,
                        city_filter=resolved_province['tenTinhThanh']
                    )
                    
                    # Chuyển đổi format từ vector DB sang format của activities
                    existing_names = {a.get('name', '').lower() for a in activities}
                    for result in vector_results:
                        name = result.get('name', '')
                        if not name or name.lower() in existing_names:
                            continue
                        if not self._belongs_to_province(result, resolved_province):
                            continue
                        
                        # Filter: bỏ qua nếu tên quá dài hoặc giống destination
                        if len(name) > 100:
                            continue
                        
                        name_normalized = _normalize_location_name(name)
                        name_tokens = _tokenize_normalized_name(name_normalized)
                        
                        if name_tokens and dest_tokens:
                            common_tokens = name_tokens & dest_tokens
                            if len(common_tokens) >= min(3, len(dest_tokens)) and len(name_tokens) <= len(dest_tokens) + 2:
                                continue
                        
                        if name.lower().strip() == destination.lower().strip():
                            continue
                        
                        description = result.get('description', '')
                        category = result.get('category', '')
                        type_hint = result.get('type', '')
                        
                        # Sử dụng semantic classifier để hiểu địa điểm
                        semantics = understand_place_semantics(
                            name=name,
                            description=description,
                            type_hint=type_hint,
                            category=category
                        )
                        
                        loai_dia_diem = semantics['loaiDiaDiem']
                        features = semantics['features']
                        
                        # Chỉ lấy địa điểm tham quan, không phải khách sạn/nhà hàng
                        if loai_dia_diem not in ['khach_san', 'nha_hang']:
                            # Kiểm tra phù hợp với travel_style
                            if travel_style and not is_suitable_for_travel_style(features, travel_style):
                                continue  # Bỏ qua nếu không phù hợp
                            
                            # Lấy giá từ result, nếu không có thì từ database
                            price = result.get('price', 0)
                            if price == 0 and result.get('name'):
                                # Thử tìm trong database để lấy giá thực tế
                                try:
                                    from asgiref.sync import sync_to_async
                                    from apps.places.models import DiaDiem
                                    
                                    async def get_price_from_db(place_name: str):
                                        def _get_price_sync():
                                            dia_diem = DiaDiem.objects.filter(
                                                tenDiaDiem__icontains=place_name,
                                                trangThai='active'
                                            ).first()
                                            return float(dia_diem.giaVe) if dia_diem and dia_diem.giaVe else 0
                                        
                                        return await sync_to_async(_get_price_sync)()
                                    
                                    price = await get_price_from_db(name)
                                except Exception as e:
                                    logger.debug(f"Could not get price from DB for {name}: {e}")
                            
                            activities.append({
                                'name': name,
                                'description': description,
                                'category': loai_dia_diem,
                                'original_category': category,
                                'rating': result.get('rating', 0),
                                'price': price,
                                'price_per_person': price,
                                'address': result.get('address', ''),
                                'latitude': result.get('latitude'),
                                'longitude': result.get('longitude'),
                                'image_url': result.get('image_url', ''),
                                'source': 'vector_db',
                                'similarity_score': result.get('similarity_score', 0),
                                'semantic_features': features,
                                'semantic_confidence': semantics['confidence'],
                                'suitable_for': features.get('suitable_for', []),
                                'best_time': features.get('best_time', ['anytime']),
                                'duration_hours': features.get('duration_hours', 2.0),
                                'tags': features.get('tags', [])
                            })
                            existing_names.add(name.lower())
                    
                    if activities:
                        vector_count = len([a for a in activities if a.get('source') == 'vector_db'])
                        if vector_count > 0:
                            logger.info(f"Added {vector_count} activities from vector DB (fallback)")
                        
                except Exception as e:
                    logger.warning(f"Vector DB search failed (fallback): {e}")
            
            # Nếu vẫn không có activities, log warning
            if len(activities) == 0:
                logger.warning(f"No activities found for {destination} from database, tools, or vector DB. Returning empty list.")
            
            logger.info(f"Final activities count: {len(activities)} for {destination}")
            
            # Tính chi phí hoạt động
            activities_cost = self.activities_tools.calculate_activity_cost(
                activities=activities,
                travelers=travelers
            )
            
            # Tìm kiếm nhà hàng - Ưu tiên Tools (SerpAPI), Vector DB chỉ làm fallback
            restaurants = []
            
            # Normalize destination để filter restaurants (reuse từ activities)
            # dest_normalized và dest_tokens đã được tính ở trên
            
            # Bước 1: Tìm từ tools (SerpAPI) - ưu tiên cao nhất
            tools_restaurants = self.activities_tools.search_restaurants(
                destination=destination
            )
            if tools_restaurants:
                # Filter restaurants: loại bỏ những restaurant có tên giống destination
                filtered_restaurants = []
                for rest in tools_restaurants:
                    rest_name = rest.get('name', '')
                    if not rest_name:
                        continue
                    if not self._belongs_to_province(rest, resolved_province):
                        continue
                    
                    # Bỏ qua nếu tên quá dài (có thể là địa chỉ đầy đủ)
                    if len(rest_name) > 100:
                        continue
                    
                    # Bỏ qua nếu tên giống destination
                    rest_normalized = _normalize_location_name(rest_name)
                    rest_tokens = _tokenize_normalized_name(rest_normalized)
                    
                    # Kiểm tra xem restaurant name có giống destination không
                    if rest_tokens and dest_tokens:
                        common_tokens = rest_tokens & dest_tokens
                        if len(common_tokens) >= min(3, len(dest_tokens)) and len(rest_tokens) <= len(dest_tokens) + 2:
                            logger.debug(f"Filtered out restaurant '{rest_name}' - too similar to destination")
                            continue
                    
                    # Bỏ qua nếu tên chính xác giống destination (case-insensitive)
                    if rest_name.lower().strip() == destination.lower().strip():
                        logger.debug(f"Filtered out restaurant '{rest_name}' - exact match with destination")
                        continue
                    
                    filtered_restaurants.append(rest)
                
                restaurants = filtered_restaurants
                logger.info(f"Found {len(restaurants)} restaurants from tools (SerpAPI) for {destination} (filtered from {len(tools_restaurants)})")
            
            # Bước 2: Vector DB chỉ dùng làm fallback nếu tools không đủ kết quả
            if len(restaurants) < 5 and self.vector_db and self.vector_db.collection:
                try:
                    # Tìm nhà hàng từ vector DB (fallback)
                    query = f"Nhà hàng quán ăn ẩm thực tại {destination}"
                    vector_results = await self.vector_db.semantic_search_async(
                        query=query,
                        n_results=10,
                        city_filter=resolved_province['tenTinhThanh']
                    )
                    
                    existing_names = {r.get('name', '').lower() for r in restaurants}
                    for result in vector_results:
                        name = result.get('name', '')
                        if not name or name.lower() in existing_names:
                            continue
                        if not self._belongs_to_province(result, resolved_province):
                            continue
                        
                        # Filter: bỏ qua nếu tên quá dài hoặc giống destination
                        if len(name) > 100:
                            continue
                        
                        name_normalized = _normalize_location_name(name)
                        name_tokens = _tokenize_normalized_name(name_normalized)
                        
                        if name_tokens and dest_tokens:
                            common_tokens = name_tokens & dest_tokens
                            if len(common_tokens) >= min(3, len(dest_tokens)) and len(name_tokens) <= len(dest_tokens) + 2:
                                continue
                        
                        if name.lower().strip() == destination.lower().strip():
                            continue
                        
                        description = result.get('description', '')
                        category = result.get('category', '')
                        type_hint = result.get('type', '')
                        
                        # Sử dụng semantic classifier để xác nhận đây là nhà hàng
                        semantics = understand_place_semantics(
                            name=name,
                            description=description,
                            type_hint=type_hint,
                            category=category
                        )
                        
                        loai_dia_diem = semantics['loaiDiaDiem']
                        
                        # Chỉ lấy nhà hàng (đã được phân loại chính xác)
                        if loai_dia_diem == 'nha_hang':
                            features = semantics['features']
                            restaurants.append({
                                'name': name,
                                'description': description,
                                'rating': result.get('rating', 0),
                                'price': result.get('price', 0),
                                'price_level': result.get('price_level', features.get('price_level', 'moderate')),
                                'address': result.get('address', ''),
                                'latitude': result.get('latitude'),
                                'longitude': result.get('longitude'),
                                'image_url': result.get('image_url', ''),
                                'source': 'vector_db',
                                'similarity_score': result.get('similarity_score', 0),
                                'semantic_features': features,
                                'semantic_confidence': semantics['confidence'],
                                'tags': features.get('tags', [])
                            })
                            existing_names.add(name.lower())
                    
                    if restaurants:
                        vector_count = len([r for r in restaurants if r.get('source') == 'vector_db'])
                        if vector_count > 0:
                            logger.info(f"Added {vector_count} restaurants from vector DB (fallback)")
                        
                except Exception as e:
                    logger.warning(f"Vector DB restaurant search failed (fallback): {e}")
            
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
    
    async def _resolve_destination_province(self, destination: str) -> Optional[Dict[str, Any]]:
        """Resolve destination ve tinh thanh chuan trong DB."""
        try:
            from asgiref.sync import sync_to_async
            from apps.places.models import TinhThanh

            def _resolve_sync(dest: str) -> Optional[Dict[str, Any]]:
                provinces = list(
                    TinhThanh.objects.values_list("maTinhThanh", "tenTinhThanh")
                )
                match = resolve_best_province(dest, provinces)
                if not match:
                    return None
                return {
                    "maTinhThanh": int(match[0]),
                    "tenTinhThanh": str(match[1]),
                    "match_score": float(match[2]),
                }

            return await sync_to_async(_resolve_sync)(destination)
        except Exception as e:
            logger.warning(f"Failed to resolve destination province for {destination}: {e}")
            return None

    def _belongs_to_province(self, place: Dict[str, Any], resolved_province: Dict[str, Any]) -> bool:
        """Chi giu ket qua nam trong dung tinh thanh da resolve."""
        province_name = resolved_province.get("tenTinhThanh", "")
        candidates = [
            place.get("province"),
            place.get("city"),
            place.get("address"),
            place.get("diaChi"),
            place.get("description"),
        ]
        if isinstance(place.get("maTinhThanh"), dict):
            candidates.append(place["maTinhThanh"].get("tenTinhThanh"))
        return text_matches_province(candidates, province_name)

    async def _query_fallback_activities_from_db(
        self,
        destination: str,
        resolved_province: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Query fallback activities từ database (sync_to_async)
        Không hardcode tên thành phố, query động từ database
        """
        try:
            from asgiref.sync import sync_to_async
            from apps.places.models import DiaDiem
            import json
            
            # Sync function để query database
            def _query_sync(dest: str, province: Optional[Dict[str, Any]]):
                if not province:
                    return []
                province_id = province["maTinhThanh"]
                province_name = province["tenTinhThanh"]
                
                # Query fallback activities từ database - động, không hardcode
                # Loại bỏ tất cả các loại lưu trú, nhà hàng, và các địa điểm không phù hợp du lịch
                # Lọc các từ khóa không phù hợp: store, shop, cửa hàng, siêu thị, bệnh viện, trường học, ngân hàng
                fallback_dia_diems = list(
                    DiaDiem.objects.filter(
                        maTinhThanh_id=province_id,
                        trangThai='active',
                        loaiDiaDiem__in=['dia_danh', 'giai_tri']
                    )
                    .exclude(loaiDiaDiem__in=['nha_hang', 'khach_san', 'co_so_luu_tru'])
                    .exclude(tenDiaDiem__icontains='nhà nghỉ')
                    .exclude(tenDiaDiem__icontains='khách sạn')
                    .exclude(tenDiaDiem__icontains='hotel')
                    .exclude(tenDiaDiem__icontains='resort')
                    .exclude(tenDiaDiem__icontains='homestay')
                    # Loại bỏ các địa điểm không phù hợp du lịch
                    .exclude(tenDiaDiem__icontains='store')
                    .exclude(tenDiaDiem__icontains='shop')
                    .exclude(tenDiaDiem__icontains='cửa hàng')
                    .exclude(tenDiaDiem__icontains='siêu thị')
                    .exclude(tenDiaDiem__icontains='bệnh viện')
                    .exclude(tenDiaDiem__icontains='hospital')
                    .exclude(tenDiaDiem__icontains='trường học')
                    .exclude(tenDiaDiem__icontains='school')
                    .exclude(tenDiaDiem__icontains='ngân hàng')
                    .exclude(tenDiaDiem__icontains='bank')
                    .exclude(tenDiaDiem__icontains='công ty')
                    .exclude(tenDiaDiem__icontains='company')
                    .exclude(tenDiaDiem__icontains='phòng khám')
                    .exclude(tenDiaDiem__icontains='clinic')
                    .order_by('-danhGiaTrungBinh', '-soLuotDanhGia')[:20]
                )
                
                logger.debug(f"Found {len(fallback_dia_diems)} DiaDiem for {province_name}")
                
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
                            
                            # Sử dụng giá thực tế từ database (giaVe)
                            price_per_person = float(dia_diem.giaVe) if dia_diem.giaVe else 0
                            
                            fallback_activities.append({
                                'name': dia_diem.tenDiaDiem or '',
                                'description': dia_diem.moTa or '',
                                'category': dia_diem.loaiDiaDiem or 'dia_danh',
                                'type': activity_type,
                                'price_per_person': price_per_person,  # Giá thực tế từ database
                                'price': price_per_person,  # Alias for compatibility
                                'duration_hours': duration_hours,
                                'rating': float(dia_diem.danhGiaTrungBinh) if dia_diem.danhGiaTrungBinh else 0,
                                'address': dia_diem.diaChi or dest,
                                'latitude': float(dia_diem.viDo) if dia_diem.viDo else None,
                                'longitude': float(dia_diem.kinhDo) if dia_diem.kinhDo else None,
                                'source': 'database',  # Luôn là database, không phải fallback
                                'maDiaDiem': dia_diem.maDiaDiem,  # Lưu ID để reference
                                'province': province_name,
                                'city': province_name,
                                'tags': dac_diem.get('tags', [])
                            })
                    except (json.JSONDecodeError, AttributeError, ValueError, TypeError) as e:
                        logger.debug(f"Error parsing dia_diem {dia_diem.maDiaDiem}: {e}")
                        continue
                
                # KHÔNG tạo generic activities - chỉ lấy từ database
                # Nếu không có địa điểm trong database, trả về empty list
                if not fallback_activities:
                    logger.warning(f"No activities found in database for {province_name}. Returning empty list to avoid fake data.")
                    return []
                
                return fallback_activities
            
            # Chạy sync function trong async context
            fallback_activities = await sync_to_async(_query_sync)(destination, resolved_province)
            
            if fallback_activities:
                logger.info(f"Found {len(fallback_activities)} fallback activities from database for {destination}")
            
            return fallback_activities
            
        except Exception as e:
            logger.warning(f"Failed to query fallback activities from database: {e}")
            return []

