"""
VietMap Tools - Công cụ địa lý từ VietMap API
==============================================
VietMap là dịch vụ bản đồ chuyên biệt cho Việt Nam với:
- Geocoding chính xác cho địa chỉ Việt Nam
- Reverse Geocoding (tọa độ → địa chỉ)
- Routing với dữ liệu đường phố Việt Nam cập nhật
- Autocomplete cho tìm kiếm địa chỉ
- TSP/VRP cho tối ưu hóa lộ trình
- Isochrone cho phân tích vùng tiếp cận
- Search places (tìm kiếm địa điểm)

API Documentation:
- Overview: https://maps.vietmap.vn/docs/map-api/overview/
- Geocoding: https://maps.vietmap.vn/docs/map-api/geocoding/
- Routing: https://maps.vietmap.vn/docs/map-api/routing/
- Search: https://maps.vietmap.vn/docs/map-api/search/

Đăng ký API key: https://maps.vietmap.vn/
Hỗ trợ: 089.616.4567 hoặc maps.info@vietmap.vn
"""
import logging
from typing import Dict, Any, Optional, List
import requests
import os
from functools import lru_cache

logger = logging.getLogger(__name__)


class VietMapTools:
    """Công cụ địa lý từ VietMap API"""
    
    def __init__(self):
        # Try to get from Django settings first (if running in Django context)
        try:
            from django.conf import settings
            self.vietmap_api_key = getattr(settings, 'VIETMAP_API_KEY', '')
        except (ImportError, AttributeError):
            # Fallback to environment variable
            self.vietmap_api_key = os.getenv('VIETMAP_API_KEY', '')
        
        # VietMap API base URL
        self.base_url = "https://maps.vietmap.vn/api"

    def _should_log_raw_response(self, location: str) -> bool:
        """Determine whether to log raw VietMap responses for this location."""
        try:
            loc = (location or "").lower().strip()
        except Exception:
            return False
        keywords = [
            "hồ chí minh", "ho chi minh", "tphcm", "tp. hồ chí minh", "thành phố hồ chí minh",
            "hà nội", "ha noi", "thành phố hà nội",
            "huế", "hue", "thành phố huế",
            "cần thơ", "can tho", "thành phố cần thơ",
        ]
        return any(k in loc for k in keywords)

    def _score_geocode_result(self, result: dict, query: str) -> float:
        """
        Tính điểm cho một kết quả geocoding để chọn kết quả tốt nhất
        
        Args:
            result: Kết quả từ VietMap search
            query: Query gốc của người dùng
            
        Returns:
            Điểm số (cao hơn = tốt hơn)
        """
        score = 0.0
        query_lower = query.lower().strip()
        query_words = set(query_lower.split())
        
        # Lấy thông tin từ result
        name = result.get('name', '').lower()
        display = result.get('display', '').lower()
        address = result.get('address', '').lower()
        full_text = f"{name} {display} {address}".lower()
        
        # Kiểm tra khớp chính xác tên - ưu tiên khớp với tên thành phố
        if query_lower == name or query_lower == display:
            score += 30.0  # Khớp chính xác = điểm cao nhất
        elif query_lower in name or name in query_lower:
            # Nếu query là tên thành phố đơn giản (như "Huế", "Hà Nội") và result là POI
            if 'POI' in ref_id and len(query_lower.split()) <= 2:
                score += 5.0  # Giảm điểm cho POI khi query là tên thành phố
            else:
                score += 15.0
        elif query_lower in display or display in query_lower:
            if 'POI' in ref_id and len(query_lower.split()) <= 2:
                score += 3.0  # Giảm điểm cho POI
            else:
                score += 12.0
        elif query_lower in address or address in query_lower:
            score += 8.0
        
        # Kiểm tra khớp từng từ
        name_words = set(name.split())
        display_words = set(display.split())
        common_words = query_words & (name_words | display_words)
        if common_words:
            score += len(common_words) * 3.0
        
        # Ưu tiên các địa điểm nổi tiếng (có từ khóa đặc biệt)
        famous_keywords = ['thánh địa', 'di tích', 'khu du lịch', 'khu bảo tồn', 'vườn quốc gia', 'sanctuary']
        for keyword in famous_keywords:
            if keyword in full_text:
                score += 10.0  # Tăng điểm cho địa điểm nổi tiếng
        
        # Ưu tiên CITY hơn POI (thành phố quan trọng hơn địa điểm cụ thể)
        ref_id = result.get('ref_id', '')
        if 'CITY' in ref_id:
            score += 10.0  # Tăng điểm cho CITY
        elif 'POI' in ref_id:
            score += 1.0  # Giảm điểm cho POI (tránh chọn POI khi tìm thành phố)
        
        # Phạt nếu tên quá khác (không có từ nào chung)
        if name_words and display_words:
            if len(query_words & (name_words | display_words)) == 0:
                score -= 10.0  # Phạt nặng nếu không có từ nào chung
        
        # Kiểm tra boundaries để ưu tiên kết quả có thông tin địa lý đầy đủ
        boundaries = result.get('boundaries', [])
        if boundaries:
            # Ưu tiên kết quả có thông tin tỉnh/thành phố
            for boundary in boundaries:
                if isinstance(boundary, dict):
                    boundary_type = boundary.get('type', -1)
                    if boundary_type == 0:  # Tỉnh/thành phố
                        score += 2.0
        
        return score

    @lru_cache(maxsize=1000)
    def geocode(self, location: str, limit: int = 1) -> Optional[Dict[str, Any]]:
        """
        Geocoding - Chuyển đổi địa chỉ/tên địa điểm thành tọa độ
        Cải thiện: Chọn kết quả tốt nhất từ danh sách kết quả
        
        Args:
            location: Địa chỉ hoặc tên địa điểm (ví dụ: "Hà Nội", "123 Nguyễn Huệ, Quận 1, TP.HCM")
            limit: Số kết quả tối đa để xem xét (mặc định: 1, nhưng sẽ xem nhiều hơn để chọn tốt nhất)
            
        Returns:
            Dict với 'lat', 'lon', 'formatted_address' hoặc None
        """
        if not self.vietmap_api_key:
            logger.warning("VIETMAP_API_KEY not set")
            return None
        
        # Ưu tiên Geocode v3: search/v3 -> place/v3
        try:
            search_v3_url = f"{self.base_url}/search/v3"
            search_params = {
                'apikey': self.vietmap_api_key,
                'text': location
            }
            search_resp = requests.get(search_v3_url, params=search_params, timeout=10)
            if search_resp.status_code == 401:
                logger.warning("VietMap API 401 Unauthorized for /search/v3 - check API key")
            else:
                search_resp.raise_for_status()
                search_data = search_resp.json()

                if self._should_log_raw_response(location):
                    try:
                        text_preview = str(search_data)
                    except Exception as e:
                        text_preview = f"<unserializable {type(search_data)}: {e}>"
                    if len(text_preview) > 2000:
                        text_preview = text_preview[:2000] + "..."
                    logger.warning(f"VietMap /search/v3 response for '{location}': {text_preview}")

                # Lấy danh sách kết quả - hỗ trợ cả GeoJSON format
                results = []
                if isinstance(search_data, list):
                    results = search_data[:10]  # Xem tối đa 10 kết quả
                elif isinstance(search_data, dict):
                    # Format GeoJSON: { "code": "OK", "data": { "features": [...] } }
                    if search_data.get('code') == 'OK':
                        data_obj = search_data.get('data', {})
                        if isinstance(data_obj, dict):
                            features = data_obj.get('features', [])
                            # Convert GeoJSON features sang format chuẩn
                            for feature in features[:10]:
                                if isinstance(feature, dict):
                                    props = feature.get('properties', {})
                                    geometry = feature.get('geometry', {})
                                    coords = geometry.get('coordinates', [])
                                    # Convert GeoJSON feature sang format chuẩn
                                    result_item = {
                                        'name': props.get('name', ''),
                                        'display': props.get('label', props.get('name', '')),
                                        'address': props.get('label', ''),
                                        'ref_id': feature.get('Id', ''),
                                        'lat': coords[1] if len(coords) >= 2 else None,
                                        'lon': coords[0] if len(coords) >= 2 else None,
                                        'region': props.get('region', ''),
                                        'county': props.get('county', ''),
                                        'locality': props.get('locality', '')
                                    }
                                    results.append(result_item)
                    else:
                        # Format cũ: { "data": [...] }
                        data = search_data.get('data', [])
                        if isinstance(data, list):
                            results = data[:10]
                
                if not results:
                    return None
                
                # Tính điểm cho từng kết quả và chọn tốt nhất
                scored_results = []
                for result in results:
                    score = self._score_geocode_result(result, location)
                    scored_results.append((score, result))
                
                # Sắp xếp theo điểm (cao nhất trước)
                scored_results.sort(key=lambda x: x[0], reverse=True)
                best_result = scored_results[0][1]
                
                if len(scored_results) > 1:
                    logger.debug(f"Selected best geocode result for '{location}' (score: {scored_results[0][0]:.1f} vs {scored_results[1][0]:.1f})")
                    # Log thông tin kết quả được chọn
                    best_name = best_result.get('name', 'N/A')
                    best_display = best_result.get('display', 'N/A')
                    logger.debug(f"  Selected: {best_name} / {best_display}")

                ref_id = best_result.get('ref_id') if isinstance(best_result, dict) else None
                
                # Ưu tiên CITY hơn POI - nếu best_result là POI, thử tìm CITY trong danh sách
                if ref_id and 'POI' in ref_id:
                    # Tìm CITY trong danh sách kết quả
                    for score, result_item in scored_results:
                        item_ref_id = result_item.get('ref_id', '')
                        if 'CITY' in item_ref_id:
                            # Tìm thấy CITY, dùng nó thay vì POI
                            best_result = result_item
                            ref_id = item_ref_id
                            logger.debug(f"Switched from POI to CITY for '{location}'")
                            break
                
                if ref_id:
                    place_v3_url = f"{self.base_url}/place/v3"
                    place_params = {
                        'apikey': self.vietmap_api_key,
                        'refid': ref_id
                    }
                    place_resp = requests.get(place_v3_url, params=place_params, timeout=10)
                    if place_resp.status_code == 401:
                        logger.warning("VietMap API 401 Unauthorized for /place/v3 - check API key")
                    else:
                        place_resp.raise_for_status()
                        place_data = place_resp.json()

                        if self._should_log_raw_response(location):
                            try:
                                text_preview = str(place_data)
                            except Exception as e:
                                text_preview = f"<unserializable {type(place_data)}: {e}>"
                            if len(text_preview) > 2000:
                                text_preview = text_preview[:2000] + "..."
                            logger.warning(f"VietMap /place/v3 response for '{location}': {text_preview}")

                        lat = place_data.get('lat') or place_data.get('latitude') or place_data.get('y')
                        lon = place_data.get('lng') or place_data.get('lon') or place_data.get('longitude') or place_data.get('x')
                        if lat is not None and lon is not None:
                            return {
                                'lat': float(lat),
                                'lon': float(lon),
                                'formatted_address': place_data.get('display') or place_data.get('address') or place_data.get('name') or location,
                                'confidence': 0.9
                            }
        except requests.exceptions.RequestException as e:
            logger.debug(f"VietMap /search/v3 or /place/v3 failed: {e}")
        except Exception as e:
            logger.debug(f"VietMap v3 geocode error: {e}")

        # Thử các endpoint khác nhau - ưu tiên migrate-address/v3 vì nó trả về thành phố chính xác hơn
        endpoints_to_try = [
            ('/migrate-address/v3', {'apikey': self.vietmap_api_key, 'text': location}),
            ('/search', {'apikey': self.vietmap_api_key, 'text': location, 'limit': limit}),
            ('/geocoding', {'apikey': self.vietmap_api_key, 'text': location}),
        ]
        
        for endpoint, params in endpoints_to_try:
            try:
                url = f"{self.base_url}{endpoint}"
                response = requests.get(url, params=params, timeout=10)
                
                # Nếu 401 Unauthorized, có thể là API key sai hoặc endpoint không đúng
                if response.status_code == 401:
                    logger.warning(f"VietMap API 401 Unauthorized for {endpoint} - check API key")
                    continue
                
                response.raise_for_status()
                data = response.json()
                
                # Log raw response for key cities to inspect current VietMap schema
                if self._should_log_raw_response(location):
                    try:
                        text_preview = str(data)
                    except Exception as e:
                        text_preview = f"<unserializable {type(data)}: {e}>"
                    if len(text_preview) > 2000:
                        text_preview = text_preview[:2000] + "..."
                    logger.warning(f"VietMap {endpoint} response for '{location}': {text_preview}")
                
                # Parse response - thử nhiều format
                result = None
                
                # Format 1: migrate-address/v3 - có boundaries với type 0 (thành phố)
                if endpoint == '/migrate-address/v3' and isinstance(data, dict):
                    boundaries = data.get('boundaries', [])
                    if boundaries and isinstance(boundaries, list):
                        # Tìm boundary có type 0 (tỉnh/thành phố)
                        for boundary in boundaries:
                            if isinstance(boundary, dict) and boundary.get('type') == 0:
                                # Lấy tọa độ từ geometry nếu có
                                geometry = boundary.get('geometry', {})
                                if geometry and geometry.get('coordinates'):
                                    coords = geometry.get('coordinates', [])
                                    if len(coords) >= 2:
                                        return {
                                            'lat': float(coords[1]),
                                            'lon': float(coords[0]),
                                            'formatted_address': data.get('display', data.get('address', boundary.get('full_name', location))),
                                            'confidence': 0.9
                                        }
                        
                        # Nếu không có geometry trong boundary, thử geocode lại với tên thành phố từ boundary
                        for boundary in boundaries:
                            if isinstance(boundary, dict) and boundary.get('type') == 0:
                                city_name = boundary.get('full_name') or boundary.get('name')
                                if city_name and city_name != location:
                                    # Geocode lại với tên thành phố chính xác hơn (nhưng tránh infinite loop)
                                    logger.debug(f"Trying to geocode city from boundary: {city_name}")
                                    # Sử dụng search/v3 để tìm CITY với tên chính xác
                                    try:
                                        city_search_url = f"{self.base_url}/search/v3"
                                        city_search_params = {
                                            'apikey': self.vietmap_api_key,
                                            'text': city_name
                                        }
                                        city_search_resp = requests.get(city_search_url, params=city_search_params, timeout=10)
                                        if city_search_resp.status_code == 200:
                                            city_search_data = city_search_resp.json()
                                            city_results = []
                                            if isinstance(city_search_data, list):
                                                city_results = city_search_data
                                            elif isinstance(city_search_data, dict):
                                                city_results = city_search_data.get('data', [])
                                            
                                            # Tìm CITY trong kết quả
                                            for city_result in city_results:
                                                city_ref_id = city_result.get('ref_id', '')
                                                if 'CITY' in city_ref_id:
                                                    # Lấy place details
                                                    city_place_url = f"{self.base_url}/place/v3"
                                                    city_place_params = {
                                                        'apikey': self.vietmap_api_key,
                                                        'refid': city_ref_id
                                                    }
                                                    city_place_resp = requests.get(city_place_url, params=city_place_params, timeout=10)
                                                    if city_place_resp.status_code == 200:
                                                        city_place_data = city_place_resp.json()
                                                        lat = city_place_data.get('lat') or city_place_data.get('latitude') or city_place_data.get('y')
                                                        lon = city_place_data.get('lng') or city_place_data.get('lon') or city_place_data.get('longitude') or city_place_data.get('x')
                                                        if lat is not None and lon is not None:
                                                            return {
                                                                'lat': float(lat),
                                                                'lon': float(lon),
                                                                'formatted_address': city_place_data.get('display', city_place_data.get('address', city_name)),
                                                                'confidence': 0.9
                                                            }
                                                    break
                                    except Exception as e:
                                        logger.debug(f"Failed to geocode city from boundary: {e}")
                
                # Format 2: /search endpoint - GeoJSON format với features array
                if endpoint == '/search' and isinstance(data, dict):
                    # GeoJSON format: { "code": "OK", "data": { "features": [...] } }
                    if data.get('code') == 'OK':
                        data_obj = data.get('data', {})
                        if isinstance(data_obj, dict):
                            features = data_obj.get('features', [])
                            if features and len(features) > 0:
                                # Chọn feature tốt nhất (ưu tiên thành phố)
                                best_feature = None
                                best_score = -1
                                
                                for feature in features:
                                    if not isinstance(feature, dict):
                                        continue
                                    
                                    props = feature.get('properties', {})
                                    geometry = feature.get('geometry', {})
                                    
                                    # Tính điểm cho feature này
                                    score = 0.0
                                    region = props.get('region', '').lower()
                                    name = props.get('name', '').lower()
                                    label = props.get('label', '').lower()
                                    location_lower = location.lower()
                                    
                                    # Ưu tiên thành phố (có "Thành Phố" trong region và tên khớp)
                                    if 'thành phố' in region:
                                        if location_lower in region or location_lower in name:
                                            score += 30.0  # Điểm cao cho thành phố
                                    elif location_lower in region:
                                        score += 15.0
                                    
                                    # Ưu tiên tên khớp chính xác
                                    if location_lower == name:
                                        score += 20.0
                                    elif location_lower in name:
                                        score += 10.0
                                    
                                    # Kiểm tra label
                                    if location_lower in label:
                                        score += 5.0
                                    
                                    if score > best_score:
                                        best_score = score
                                        best_feature = feature
                                
                                if best_feature:
                                    geometry = best_feature.get('geometry', {})
                                    coords = geometry.get('coordinates', [])
                                    props = best_feature.get('properties', {})
                                    
                                    if coords and len(coords) >= 2:
                                        return {
                                            'lat': float(coords[1]),  # GeoJSON: [lon, lat]
                                            'lon': float(coords[0]),
                                            'formatted_address': props.get('label', props.get('name', location)),
                                            'confidence': 0.8
                                        }
                
                # Format 3: List of results
                if isinstance(data, list) and len(data) > 0:
                    result = data[0]
                    lat = result.get('lat') or result.get('latitude') or result.get('y')
                    lon = result.get('lon') or result.get('longitude') or result.get('lng') or result.get('x')
                    
                    if lat is not None and lon is not None:
                        return {
                            'lat': float(lat),
                            'lon': float(lon),
                            'formatted_address': result.get('display_name') or result.get('address') or result.get('name') or location,
                            'confidence': result.get('confidence', 0.8)
                        }
                
                # Format 4: Dict with 'data' key (format cũ)
                elif isinstance(data, dict):
                    results = data.get('data', [])
                    if isinstance(results, list) and len(results) > 0:
                        result = results[0]
                    elif isinstance(data.get('data'), dict):
                        result = data.get('data')
                    
                    if result:
                        lat = result.get('lat') or result.get('latitude') or result.get('y')
                        lon = result.get('lon') or result.get('longitude') or result.get('lng') or result.get('x')
                        
                        if lat is not None and lon is not None:
                            return {
                                'lat': float(lat),
                                'lon': float(lon),
                                'formatted_address': result.get('display_name') or result.get('address') or result.get('name') or data.get('display', location),
                                'confidence': result.get('confidence', 0.7)
                            }
                
                # Nếu không parse được coordinates, log và tiếp tục thử endpoint khác
                logger.debug(f"VietMap {endpoint} returned data but no coordinates found: {type(data)}")
                
            except requests.exceptions.RequestException as e:
                logger.debug(f"VietMap {endpoint} failed: {e}")
                continue
            except Exception as e:
                logger.debug(f"VietMap {endpoint} error: {e}")
                continue
        
        # Nếu tất cả endpoints đều fail, return None để fallback về OpenRouteService
        logger.warning(f"VietMap geocoding failed for all endpoints: {location}")
        return None
    
    def reverse_geocode(self, lat: float, lon: float) -> Optional[Dict[str, Any]]:
        """
        Reverse Geocoding - Chuyển đổi tọa độ thành địa chỉ
        
        Args:
            lat: Vĩ độ
            lon: Kinh độ
            
        Returns:
            Dict với 'formatted_address' hoặc None
        """
        if not self.vietmap_api_key:
            logger.warning("VIETMAP_API_KEY not set")
            return None
        
        try:
            url = f"{self.base_url}/reverse"
            headers = {
                'api-key': self.vietmap_api_key
            }
            params = {
                'lat': lat,
                'lon': lon
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Parse response
            if isinstance(data, dict):
                result = data.get('data') or data
                return {
                    'formatted_address': result.get('display_name') or result.get('address'),
                    'lat': lat,
                    'lon': lon
                }
        except Exception as e:
            logger.error(f"VietMap reverse geocoding error for ({lat}, {lon}): {e}")
            
        return None
    
    def calculate_distance_time(
        self,
        origin: str,
        destination: str,
        profile: str = "car"  # car, bike, foot
    ) -> Optional[Dict[str, Any]]:
        """
        Tính khoảng cách và thời gian di chuyển giữa 2 điểm
        
        Args:
            origin: Điểm xuất phát (địa chỉ hoặc "lat,lon")
            destination: Điểm đến (địa chỉ hoặc "lat,lon")
            profile: Loại phương tiện (car, bike, foot)
            
        Returns:
            Dict với 'distance_km', 'duration_minutes', 'route' hoặc None
        """
        # Geocode cả 2 điểm nếu cần
        if ',' not in origin or ',' not in destination:
            origin_coords = self.geocode(origin)
            dest_coords = self.geocode(destination)
            
            if not origin_coords or not origin_coords.get('lat') or not origin_coords.get('lon'):
                logger.warning(f"Cannot geocode origin: {origin}")
                return None
            
            if not dest_coords or not dest_coords.get('lat') or not dest_coords.get('lon'):
                logger.warning(f"Cannot geocode destination: {destination}")
                return None
            
            origin = f"{origin_coords['lat']},{origin_coords['lon']}"
            destination = f"{dest_coords['lat']},{dest_coords['lon']}"
        
        if not self.vietmap_api_key:
            logger.warning("VIETMAP_API_KEY not set")
            return None
        
        try:
            # Sử dụng endpoint v3 mới với API key trong query parameter
            url = f"{self.base_url}/route/v3"
            
            # Parse origin and destination coordinates
            origin_parts = origin.split(',')
            dest_parts = destination.split(',')
            
            if len(origin_parts) != 2 or len(dest_parts) != 2:
                logger.error(f"Invalid coordinate format: origin={origin}, destination={destination}")
                return None
            
            origin_lat = origin_parts[0].strip()
            origin_lon = origin_parts[1].strip()
            dest_lat = dest_parts[0].strip()
            dest_lon = dest_parts[1].strip()
            
            # Map profile to vehicle (car, bike, foot, motorcycle)
            vehicle_map = {
                'car': 'car',
                'bike': 'bike',
                'bicycle': 'bike',
                'foot': 'foot',
                'walk': 'foot',
                'motorcycle': 'motorcycle',
                'motor': 'motorcycle'
            }
            vehicle = vehicle_map.get(profile.lower(), 'car')
            
            # Build params với API key trong query parameter và point riêng biệt
            # requests library không hỗ trợ duplicate keys trong dict, nên dùng list of tuples
            from urllib.parse import urlencode
            
            # Build params list để hỗ trợ multiple 'point' parameters
            params_list = [
                ('apikey', self.vietmap_api_key),
                ('point', f"{origin_lat},{origin_lon}"),  # Point đầu tiên
                ('point', f"{dest_lat},{dest_lon}"),      # Point thứ hai
                ('points_encoded', 'false'),  # Không encode để lấy geometry dễ parse
                ('vehicle', vehicle)
            ]
            
            # Encode URL với list of tuples để giữ multiple 'point' parameters
            query_string = urlencode(params_list)
            url_with_params = f"{url}?{query_string}"
            
            response = requests.get(url_with_params, timeout=10)
            
            # Nếu 401, log và return None để fallback
            if response.status_code == 401:
                logger.error(f"VietMap API 401 Unauthorized - Check API key: {self.vietmap_api_key[:10]}...")
                return None
            
            response.raise_for_status()
            data = response.json()
            
            # Parse routing response từ Route API v3
            # Format theo tài liệu: { "code": "OK", "paths": [{ "distance": ..., "time": ... }] }
            route = None
            distance_m = 0
            duration_s = 0
            
            # Kiểm tra status code
            code = data.get('code', '')
            if code != 'OK':
                error_msg = data.get('messages', 'Unknown error')
                logger.error(f"VietMap Route API v3 returned error: code={code}, message={error_msg}")
                return None
            
            # Format chính: Có 'paths' array (Route API v3) - ƯU TIÊN
            if isinstance(data, dict) and data.get('paths'):
                paths = data['paths']
                if paths and len(paths) > 0:
                    path = paths[0]  # Lấy path đầu tiên
                    # distance: meters (số thực)
                    distance_m = path.get('distance', 0)
                    # time: milliseconds (số nguyên) - theo tài liệu
                    time_ms = path.get('time', 0)
                    duration_s = time_ms / 1000.0  # Convert milliseconds to seconds
                    route = path
                    logger.debug(f"VietMap Route v3: distance={distance_m}m, time={time_ms}ms ({duration_s}s)")
                else:
                    logger.warning("VietMap Route API v3 returned empty paths array")
                    return None
            
            # Fallback: Format cũ (nếu có)
            elif isinstance(data, dict) and data.get('routes'):
                route = data['routes'][0]
                summary = route.get('summary', {})
                
                if isinstance(summary, dict):
                    distance_m = summary.get('distance', 0)
                    duration_s = summary.get('duration', 0)
                else:
                    distance_m = route.get('distance', 0)
                    duration_s = route.get('duration', 0)
            
            # Fallback: Response trực tiếp có distance/duration
            elif isinstance(data, dict):
                if 'distance' in data:
                    distance_m = data.get('distance', 0)
                if 'duration' in data:
                    duration_s = data.get('duration', 0)
                route = data
            else:
                logger.error(f"VietMap Route API v3 returned unexpected format: {type(data)}")
                return None
            
            # Validate kết quả
            if distance_m <= 0 or duration_s <= 0:
                logger.warning(f"VietMap Route API v3 returned invalid values: distance={distance_m}m, duration={duration_s}s")
                return None
            
            return {
                'distance_km': round(distance_m / 1000, 2) if distance_m else 0,
                'duration_minutes': round(duration_s / 60, 1) if duration_s else 0,
                'distance_meters': int(distance_m) if distance_m else 0,
                'duration_seconds': int(duration_s) if duration_s else 0,
                'route': route.get('geometry', {}) if route else {}
            }
        except requests.exceptions.HTTPError as e:
            logger.error(f"VietMap routing HTTP error: {e} - Status: {e.response.status_code if hasattr(e, 'response') else 'Unknown'}")
            if hasattr(e, 'response') and e.response.status_code == 401:
                logger.error("VietMap API key may be invalid or expired")
        except Exception as e:
            logger.error(f"VietMap routing error: {e}")
            
        return None
    
    def autocomplete(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Autocomplete - Tìm kiếm gợi ý địa chỉ khi người dùng gõ
        
        Args:
            query: Từ khóa tìm kiếm
            limit: Số kết quả tối đa
            
        Returns:
            List các địa chỉ gợi ý
        """
        if not self.vietmap_api_key:
            logger.warning("VIETMAP_API_KEY not set")
            return []
        
        try:
            url = f"{self.base_url}/autocomplete"
            headers = {
                'api-key': self.vietmap_api_key
            }
            params = {
                'text': query,
                'limit': limit
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Parse autocomplete response
            results = []
            if isinstance(data, list):
                results = data
            elif isinstance(data, dict) and data.get('data'):
                results = data['data'] if isinstance(data['data'], list) else [data['data']]
            
            formatted_results = []
            for item in results[:limit]:
                formatted_results.append({
                    'display_name': item.get('display_name') or item.get('address') or item.get('name'),
                    'lat': item.get('lat') or item.get('latitude'),
                    'lon': item.get('lon') or item.get('longitude') or item.get('lng'),
                    'address': item.get('address') or item.get('display_name')
                })
            
            return formatted_results
        except Exception as e:
            logger.error(f"VietMap autocomplete error for {query}: {e}")
            
        return []
    
    def optimize_route(
        self,
        points: List[str],  # List of addresses or "lat,lon"
        optimize: bool = True
    ) -> Optional[Dict[str, Any]]:
        """
        Tối ưu hóa lộ trình (TSP/VRP) - Tìm lộ trình ngắn nhất qua nhiều điểm
        
        Args:
            points: Danh sách các điểm cần đi qua
            optimize: Có tối ưu hóa thứ tự không
            
        Returns:
            Dict với lộ trình tối ưu hoặc None
        """
        if not self.vietmap_api_key or len(points) < 2:
            return None
        
        try:
            # Geocode points if needed
            coords = []
            for point in points:
                if ',' in point:
                    coords.append(point)
                else:
                    geocoded = self.geocode(point)
                    if geocoded:
                        coords.append(f"{geocoded['lat']},{geocoded['lon']}")
            
            if len(coords) < 2:
                return None
            
            url = f"{self.base_url}/optimize"
            headers = {
                'api-key': self.vietmap_api_key
            }
            params = {
                'point': ';'.join(coords),
                'optimize': 'true' if optimize else 'false'
            }
            
            response = requests.get(url, headers=headers, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            return data
        except Exception as e:
            logger.error(f"VietMap route optimization error: {e}")
            
        return None
    
    def search_places(
        self,
        query: str,
        location: Optional[str] = None,  # "lat,lon" hoặc địa chỉ
        radius: Optional[float] = None,  # Bán kính tìm kiếm (km)
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Tìm kiếm địa điểm (places) - Nhà hàng, khách sạn, địa điểm du lịch, etc.
        
        Args:
            query: Từ khóa tìm kiếm (ví dụ: "nhà hàng", "khách sạn", "bảo tàng")
            location: Vị trí trung tâm (tọa độ "lat,lon" hoặc địa chỉ)
            radius: Bán kính tìm kiếm (km) - chỉ áp dụng khi có location
            limit: Số kết quả tối đa
            
        Returns:
            List các địa điểm tìm được
        """
        if not self.vietmap_api_key:
            logger.warning("VIETMAP_API_KEY not set")
            return []
        
        try:
            # Sử dụng search endpoint với các tham số
            url = f"{self.base_url}/search"
            params = {
                'apikey': self.vietmap_api_key,
                'text': query,
                'limit': limit
            }
            
            # Nếu có location, thêm vào params
            if location:
                # Nếu location là địa chỉ, geocode trước
                if ',' not in location:
                    geocoded = self.geocode(location)
                    if geocoded:
                        location = f"{geocoded['lat']},{geocoded['lon']}"
                
                if ',' in location:
                    try:
                        parts = location.split(',')
                        if len(parts) >= 2:
                            lat_str = parts[0].strip()
                            lon_str = parts[1].strip()
                            # Validate và parse coordinates
                            lat = float(lat_str)
                            lon = float(lon_str)
                            # Validate range (Vietnam: lat ~8-23, lon ~102-110)
                            if 8 <= lat <= 23 and 102 <= lon <= 110:
                                params['lat'] = lat
                                params['lon'] = lon
                            else:
                                logger.warning(f"Coordinates out of Vietnam range: lat={lat}, lon={lon}")
                        else:
                            logger.warning(f"Invalid location format (not enough parts): {location}")
                    except (ValueError, IndexError) as e:
                        logger.error(f"VietMap parse location error: {e}, location={location}")
                        # Fallback: try geocoding again
                        geocoded = self.geocode(location)
                        if geocoded:
                            params['lat'] = geocoded['lat']
                            params['lon'] = geocoded['lon']
                    
                    if radius:
                        params['radius'] = radius * 1000  # Convert km to meters
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Parse search results
            results = []
            if isinstance(data, list):
                results = data
            elif isinstance(data, dict):
                results = data.get('data', [])
                if not isinstance(results, list):
                    results = [results] if results else []
            
            formatted_results = []
            for item in results[:limit]:
                # Safe coordinate parsing
                lat = None
                lon = None
                try:
                    lat_val = item.get('lat') or item.get('latitude') or item.get('y')
                    lon_val = item.get('lon') or item.get('longitude') or item.get('lng') or item.get('x')
                    if lat_val is not None:
                        lat = float(lat_val)
                    if lon_val is not None:
                        lon = float(lon_val)
                except (ValueError, TypeError) as e:
                    logger.debug(f"Could not parse coordinates from item: {item.get('name', 'unknown')}, error: {e}")
                
                formatted_results.append({
                    'name': item.get('name') or item.get('display_name') or item.get('address'),
                    'address': item.get('address') or item.get('display_name'),
                    'lat': lat,
                    'lon': lon,
                    'category': item.get('category') or item.get('type'),
                    'rating': item.get('rating'),
                    'phone': item.get('phone'),
                    'website': item.get('website'),
                    'distance': item.get('distance'),  # Khoảng cách nếu có location
                    'source': 'vietmap'
                })
            
            return formatted_results
        except Exception as e:
            logger.error(f"VietMap search places error for '{query}': {e}")
        
        return []
    
    def nearby_places(
        self,
        lat: float,
        lon: float,
        query: Optional[str] = None,  # Loại địa điểm (ví dụ: "nhà hàng", "khách sạn")
        radius: float = 5.0,  # Bán kính (km)
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Tìm địa điểm gần đây (Nearby Places)
        
        Args:
            lat: Vĩ độ
            lon: Kinh độ
            query: Loại địa điểm (optional, ví dụ: "nhà hàng", "khách sạn", "bảo tàng")
            radius: Bán kính tìm kiếm (km, mặc định: 5km)
            limit: Số kết quả tối đa
            
        Returns:
            List các địa điểm gần đây
        """
        if not self.vietmap_api_key:
            logger.warning("VIETMAP_API_KEY not set")
            return []
        
        # Sử dụng search với location và radius
        search_query = query or "địa điểm"
        return self.search_places(
            query=search_query,
            location=f"{lat},{lon}",
            radius=radius,
            limit=limit
        )
    
    def isochrone(
        self,
        lat: float,
        lon: float,
        profile: str = "car",  # car, bike, foot
        time_limit: int = 30,  # Thời gian tối đa (phút)
        distance_limit: Optional[float] = None  # Khoảng cách tối đa (km)
    ) -> Optional[Dict[str, Any]]:
        """
        Phân tích vùng tiếp cận (Isochrone) - Tìm vùng có thể đến được trong thời gian/khoảng cách nhất định
        
        Args:
            lat: Vĩ độ điểm xuất phát
            lon: Kinh độ điểm xuất phát
            profile: Loại phương tiện (car, bike, foot)
            time_limit: Thời gian tối đa (phút)
            distance_limit: Khoảng cách tối đa (km, optional)
            
        Returns:
            Dict với thông tin vùng tiếp cận hoặc None
        """
        if not self.vietmap_api_key:
            logger.warning("VIETMAP_API_KEY not set")
            return None
        
        try:
            url = f"{self.base_url}/isochrone"
            headers = {
                'api-key': self.vietmap_api_key
            }
            params = {
                'point': f"{lat},{lon}",
                'profile': profile,
                'time_limit': time_limit * 60  # Convert minutes to seconds
            }
            
            if distance_limit:
                params['distance_limit'] = distance_limit * 1000  # Convert km to meters
            
            response = requests.get(url, headers=headers, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()
            
            return data
        except Exception as e:
            logger.error(f"VietMap isochrone error for ({lat}, {lon}): {e}")
        
        return None


# Singleton instance
_vietmap_tools = None

def get_vietmap_tools() -> VietMapTools:
    """Get singleton VietMapTools instance"""
    global _vietmap_tools
    if _vietmap_tools is None:
        _vietmap_tools = VietMapTools()
    return _vietmap_tools

