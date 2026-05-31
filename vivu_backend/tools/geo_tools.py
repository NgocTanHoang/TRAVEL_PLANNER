"""
Geographic Tools - Cong cu dia ly
=================================
- Geocoding (chuyen doi ten dia diem -> toa do)
- Tinh khoang cach va thoi gian di chuyen
- Tim dia diem trong ban kinh

Ha tang duoc chuyen sang OpenStreetMap:
- Geocoding: Nominatim
- Routing: OSRM public API
- Fallback: Haversine + he so uon luon duong Viet Nam
"""
import logging
from typing import Dict, Any, Optional, Tuple, List

import requests

# Import caching utilities
try:
    from utils.cache import cache_get, cache_set, generate_cache_key, cached
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False
    cache_get = cache_set = generate_cache_key = cached = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

LEGACY_DONG_NAI_TOKEN = "Thành phố Đồng Nai"
NORMALIZED_DONG_NAI_TOKEN = "Tỉnh Đồng Nai"


def sanitize_external_address_text(value: Optional[str]) -> str:
    """Chuẩn hóa chuỗi địa chỉ trả về từ external API theo hierarchy hiện hành."""
    text = str(value or "").strip()
    if not text:
        return ""
    return text.replace(LEGACY_DONG_NAI_TOKEN, NORMALIZED_DONG_NAI_TOKEN)


def normalize_location_name(location: str) -> List[str]:
    """
    Normalize location name de xu ly cac bien the ten dia diem.

    Args:
        location: Ten dia diem goc

    Returns:
        Danh sach bien the ten de thu geocode
    """
    location = (location or "").strip()
    if not location:
        return []

    variants = [location]
    location_lower = location.lower()

    if location_lower.startswith("thanh pho "):
        city_name = location[len("thanh pho "):].strip()
        if city_name:
            variants.append(city_name)
            variants.append(f"TP. {city_name}")

    if location_lower.startswith("tp."):
        city_name = location[3:].strip()
        if city_name:
            variants.append(city_name)
            variants.append(f"Thanh pho {city_name}")
    elif location_lower.startswith("tp "):
        city_name = location[3:].strip()
        if city_name:
            variants.append(city_name)
            variants.append(f"Thanh pho {city_name}")

    if location_lower.startswith("tinh "):
        province_name = location[len("tinh "):].strip()
        if province_name:
            variants.append(province_name)

    if "thua thien" in location_lower and "hue" in location_lower:
        variants.extend(["Hue", "Thanh pho Hue"])

    if "ho chi minh" in location_lower:
        variants.extend(["TP. Ho Chi Minh", "TP HCM", "Sai Gon"])

    if "ha noi" in location_lower:
        variants.extend(["Ha Noi", "Thanh pho Ha Noi"])

    if "da nang" in location_lower:
        variants.extend(["Da Nang", "Thanh pho Da Nang"])

    if "can tho" in location_lower:
        variants.extend(["Can Tho", "Thanh pho Can Tho"])

    seen = set()
    unique_variants = []
    for variant in variants:
        key = variant.lower().strip()
        if key and key not in seen:
            seen.add(key)
            unique_variants.append(variant.strip())

    return unique_variants


class GeoTools:
    """Cong cu dia ly cho cac agents - OSM Nominatim + OSRM."""

    def __init__(self):
        self.osrm_base_url = "http://router.project-osrm.org"
        self.nominatim_url = "https://nominatim.openstreetmap.org/search"
        self.default_headers = {
            "User-Agent": "ViVuTravelPlanner/1.0 (OSM routing)",
            "Accept": "application/json",
        }

    def _parse_coordinate_string(self, value: str) -> Optional[Tuple[float, float]]:
        """Parse chuoi 'lat,lon' thanh tuple float."""
        if not value or "," not in value:
            return None

        parts = value.split(",")
        if len(parts) != 2:
            return None

        try:
            lat = float(parts[0].strip())
            lon = float(parts[1].strip())
        except ValueError:
            return None

        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            return None
        return (lat, lon)

    def _normalize_coord_string(self, value: str) -> str:
        parsed = self._parse_coordinate_string(value)
        if parsed:
            return f"{parsed[0]:.7f},{parsed[1]:.7f}"
        return (value or "").strip()

    def _route_profile_name(self, profile: str) -> str:
        profile_map = {
            "driving-car": "driving",
            "car": "driving",
            "cycling-regular": "bike",
            "bike": "bike",
            "foot-walking": "foot",
            "walking": "foot",
            "foot": "foot",
        }
        return profile_map.get(profile, "driving")

    def _estimate_profile_fallback(
        self,
        haversine_dist_km: float,
        profile: str,
    ) -> Dict[str, float]:
        """Fallback profile-aware khi OSRM timeout/lỗi mạng."""
        route_profile = self._route_profile_name(profile)
        if route_profile == "foot":
            road_multiplier = 1.12
            avg_speed = 4.5
        elif route_profile == "bike":
            road_multiplier = 1.18
            avg_speed = 15.0
        else:
            road_multiplier = 1.25 if haversine_dist_km <= 100 else 1.30
            avg_speed = 35.0 if haversine_dist_km <= 100 else 45.0

        distance_km = haversine_dist_km * road_multiplier
        duration_minutes = (distance_km / avg_speed) * 60 if avg_speed > 0 else 0
        return {
            "distance_km": round(distance_km, 2),
            "duration_minutes": round(duration_minutes, 1),
        }

    def _resolve_coordinates(
        self,
        value: str,
        country: str = "VN",
    ) -> Optional[Dict[str, Any]]:
        parsed = self._parse_coordinate_string(value)
        if parsed:
            return {
                "lat": parsed[0],
                "lon": parsed[1],
                "formatted_address": sanitize_external_address_text((value or "").strip()),
                "confidence": 1.0,
            }
        return self.geocode(value, country=country)

    def geocode(self, location: str, country: str = "VN", use_vietmap: bool = True) -> Optional[Dict[str, Any]]:
        """
        Chuyen doi ten dia diem thanh toa do bang Nominatim.

        Args:
            location: Ten dia diem
            country: Ma quoc gia
            use_vietmap: giu de backward-compatibility, khong con duoc dung

        Returns:
            Dict voi lat/lon/formatted_address hoac None
        """
        direct_coords = self._parse_coordinate_string(location)
        if direct_coords:
            return {
                "lat": direct_coords[0],
                "lon": direct_coords[1],
                "formatted_address": sanitize_external_address_text((location or "").strip()),
                "confidence": 1.0,
            }

        if CACHE_AVAILABLE:
            cache_key = generate_cache_key("geocode", location, country, use_vietmap)
            cached_result = cache_get(cache_key)
            if cached_result:
                logger.debug(f"Cache hit for geocode: {location}")
                return cached_result

        for variant in normalize_location_name(location):
            try:
                response = requests.get(
                    self.nominatim_url,
                    params={
                        "q": variant,
                        "format": "jsonv2",
                        "limit": 1,
                        "countrycodes": country.lower(),
                        "addressdetails": 0,
                    },
                    headers=self.default_headers,
                    timeout=10,
                )
                response.raise_for_status()
                payload = response.json()
                if isinstance(payload, list) and payload:
                    item = payload[0]
                    result = {
                        "lat": float(item["lat"]),
                        "lon": float(item["lon"]),
                        "formatted_address": sanitize_external_address_text(
                            item.get("display_name", location)
                        ),
                        "confidence": 1.0,
                    }
                    if CACHE_AVAILABLE:
                        cache_key = generate_cache_key("geocode", location, country, use_vietmap)
                        cache_set(cache_key, result, ttl=604800)
                        variant_key = generate_cache_key("geocode", variant, country, use_vietmap)
                        cache_set(variant_key, result, ttl=604800)
                    return result
            except Exception as exc:
                logger.debug(f"Nominatim geocoding failed for '{variant}': {exc}")

        logger.debug(f"Geocoding failed for {location}")
        return None

    def calculate_distance_time(
        self,
        origin: str,
        destination: str,
        profile: str = "driving-car",
        use_vietmap: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """
        Tinh khoang cach va thoi gian di chuyen.

        Dau vao/dau ra giu nguyen de cac agent khac khong bi gay:
        - Input: origin, destination, profile, use_vietmap
        - Output: dict distance_km, duration_minutes, route, source
        """
        normalized_origin = self._normalize_coord_string(origin)
        normalized_destination = self._normalize_coord_string(destination)

        if CACHE_AVAILABLE:
            cache_key = generate_cache_key(
                "route",
                normalized_origin,
                normalized_destination,
                profile,
                use_vietmap,
            )
            cached_result = cache_get(cache_key)
            if cached_result:
                logger.debug(f"Cache hit for route: {normalized_origin} -> {normalized_destination}")
                return cached_result

        origin_coords = self._resolve_coordinates(origin)
        dest_coords = self._resolve_coordinates(destination)
        if not origin_coords or not dest_coords:
            logger.debug(f"Cannot resolve coordinates for routing: {origin}, {destination}")
            return None

        route_profile = self._route_profile_name(profile)
        osrm_url = (
            f"{self.osrm_base_url}/route/v1/{route_profile}/"
            f"{origin_coords['lon']},{origin_coords['lat']};"
            f"{dest_coords['lon']},{dest_coords['lat']}"
        )

        try:
            response = requests.get(
                osrm_url,
                params={"overview": "false"},
                headers=self.default_headers,
                timeout=10,
            )
            response.raise_for_status()
            payload = response.json()
            if payload.get("routes"):
                route = payload["routes"][0]
                distance_km = round(route["distance"] / 1000, 2)
                duration_minutes = round(route["duration"] / 60, 1)
                if duration_minutes <= 0:
                    duration_minutes = 1.0

                if route_profile == "foot":
                    implied_speed = distance_km / (duration_minutes / 60)
                    if implied_speed > 7:
                        duration_minutes = round((distance_km / 4.5) * 60, 1)

                result = {
                    "distance_km": distance_km,
                    "duration_minutes": duration_minutes,
                    "route": [],
                    "source": "osrm",
                }
                if CACHE_AVAILABLE:
                    cache_key = generate_cache_key(
                        "route",
                        normalized_origin,
                        normalized_destination,
                        profile,
                        use_vietmap,
                    )
                    cache_set(cache_key, result, ttl=604800)
                return result
        except Exception as exc:
            logger.debug(f"OSRM routing failed for {origin} -> {destination}: {exc}")

        try:
            haversine_dist = self._haversine_distance(
                origin_coords["lat"],
                origin_coords["lon"],
                dest_coords["lat"],
                dest_coords["lon"],
            )
            estimate = self._estimate_profile_fallback(haversine_dist, profile)
            return {
                "distance_km": estimate["distance_km"],
                "duration_minutes": estimate["duration_minutes"],
                "route": [],
                "source": "haversine_estimate",
            }
        except Exception as exc:
            logger.error(f"Haversine calculation failed: {exc}")
            return None

    def _haversine_distance(self, lat1, lon1, lat2, lon2):
        """Calculate haversine distance between two points in km."""
        import math

        radius = 6371
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (
            math.sin(dlat / 2) * math.sin(dlat / 2)
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(dlon / 2)
            * math.sin(dlon / 2)
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return radius * c

    def find_nearby_places(
        self,
        location: str,
        radius_km: float = 10.0,
        categories: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Tim dia diem trong ban kinh.

        Hien tai chua co nearby provider OSM on dinh trong repo nay,
        nen giu interface va tra ve empty list.
        """
        coords = self.geocode(location)
        if not coords:
            return []
        return []


_geo_tools = None


def get_geo_tools() -> GeoTools:
    """Get singleton GeoTools instance."""
    global _geo_tools
    if _geo_tools is None:
        _geo_tools = GeoTools()
    return _geo_tools
