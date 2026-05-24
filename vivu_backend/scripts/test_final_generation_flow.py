"""Ultimate end-to-end integration test for the real travel generation flow."""
from __future__ import annotations

import json
import os
import sys
from datetime import timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import django
from django.test import Client
from django.utils import timezone

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "vivu_core.settings")

try:
    from dotenv import load_dotenv

    load_dotenv(REPO_ROOT / ".env", override=False, encoding="utf-8-sig")
except Exception:
    pass

django.setup()

from agents.state import FullTravelPlanOutput  # noqa: E402
from apps.itineraries.models import LichTrinh, LichTrinhDiaDiem  # noqa: E402
from apps.places.models import DiaDiem, TinhThanh  # noqa: E402
from apps.users.models import NguoiDung  # noqa: E402
from rest_framework_simplejwt.tokens import AccessToken  # noqa: E402
from tools.geo_tools import get_geo_tools  # noqa: E402


PROVINCE_ID = 45
GENERATE_ENDPOINT = "/api/v1/travel-plans/"
SAVE_ENDPOINT = "/api/v1/travel-plans/save/"
WEATHER_ENDPOINT = "/api/v1/weather/"


def ensure_test_user() -> NguoiDung:
    user, created = NguoiDung.objects.get_or_create(
        username="final_generation_e2e_user",
        defaults={
            "email": "final-generation-e2e@example.com",
            "hoTen": "Final Generation E2E",
            "vaiTro": "user",
            "trangThai": "active",
        },
    )
    if created or not user.email:
        user.email = "final-generation-e2e@example.com"
    if created or not user.has_usable_password():
        user.set_password("FinalGenerationE2E123!")
    user.hoTen = user.hoTen or "Final Generation E2E"
    user.vaiTro = user.vaiTro or "user"
    user.trangThai = user.trangThai or "active"
    user.save()
    return user


def get_quang_ninh() -> TinhThanh:
    province = TinhThanh.objects.filter(maTinhThanh=PROVINCE_ID).first()
    if province is None:
        raise SystemExit(f"Không tìm thấy TinhThanh với mã {PROVINCE_ID}.")
    return province


def build_payload(province: TinhThanh) -> Dict[str, Any]:
    start_date = (timezone.localdate() + timedelta(days=14)).strftime("%Y-%m-%d")
    return {
        "origin": "Hà Nội",
        "destination": province.tenTinhThanh,
        "start_date": start_date,
        "days": 3,
        "travelers": 2,
        "travel_style": "standard",
        "budget": 4_500_000,
        "rooms": 1,
        "interests": [
            "Khám phá danh thắng",
            "Trải nghiệm hải sản",
            "Nghỉ dưỡng",
        ],
    }


def parse_json_response(response) -> Dict[str, Any]:
    try:
        return response.json()
    except Exception:
        try:
            return json.loads(response.content.decode("utf-8"))
        except Exception:
            return {"raw": response.content.decode("utf-8", errors="replace")}


def validate_plan_payload(payload: Dict[str, Any]) -> FullTravelPlanOutput:
    if hasattr(FullTravelPlanOutput, "model_validate"):
        return FullTravelPlanOutput.model_validate(payload)
    return FullTravelPlanOutput.parse_obj(payload)


def dump_plan_payload(plan: FullTravelPlanOutput) -> Dict[str, Any]:
    if hasattr(plan, "model_dump"):
        return plan.model_dump()
    return plan.dict()


def extract_timeline_items(plan_payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for day in plan_payload.get("daily_itinerary", []):
        for item in day.get("timeline", []):
            if isinstance(item, dict):
                items.append(item)
    return items


def count_unique_day_place_pairs(plan_payload: Dict[str, Any]) -> int:
    unique_pairs = set()
    for day in plan_payload.get("daily_itinerary", []):
        day_date = str(day.get("date") or "").strip()
        for item in day.get("timeline", []):
            place_id = str(item.get("place_id") or "").strip()
            if day_date and place_id:
                unique_pairs.add((day_date, place_id))
    return len(unique_pairs)


def validate_rag_and_geography(
    structured_payload: Dict[str, Any],
    province: TinhThanh,
) -> Tuple[List[DiaDiem], List[str]]:
    province_places = list(DiaDiem.objects.filter(maTinhThanh=province).only("maDiaDiem", "viDo", "kinhDo", "tenDiaDiem"))
    province_ids = {str(place.maDiaDiem) for place in province_places}
    place_by_id = {str(place.maDiaDiem): place for place in province_places}

    invalid_items: List[str] = []
    resolved_places: List[DiaDiem] = []

    for index, item in enumerate(extract_timeline_items(structured_payload), start=1):
        place_id = str(item.get("place_id") or "").strip()
        activity_name = str(item.get("activity_name") or "").strip()
        if place_id not in province_ids:
            invalid_items.append(f"#{index} place_id={place_id} activity={activity_name}")
            continue
        resolved_places.append(place_by_id[place_id])

    return resolved_places, invalid_items


def validate_walking_segments(structured_payload: Dict[str, Any]) -> Tuple[List[str], int]:
    errors: List[str] = []
    walking_segments = 0

    for index, item in enumerate(extract_timeline_items(structured_payload), start=1):
        transport = item.get("transport_to_next") or {}
        mode = str(transport.get("mode") or "").strip().lower()
        if mode not in {"di bo", "walking", "walk", "foot"}:
            continue
        walking_segments += 1
        distance_km = float(transport.get("distance_km") or 0.0)
        duration_mins = float(transport.get("duration_mins") or 0.0)
        if distance_km <= 0 or duration_mins <= 0:
            errors.append(f"Walking segment #{index} có distance/duration không hợp lệ.")
            continue
        speed_kmh = distance_km / (duration_mins / 60)
        if not (4.0 <= speed_kmh <= 5.0):
            errors.append(
                f"Walking segment #{index} có vận tốc {speed_kmh:.2f} km/h, ngoài ngưỡng 4.0-5.0 km/h."
            )

    return errors, walking_segments


def probe_real_osrm_route(resolved_places: Iterable[DiaDiem]) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    geo_tools = get_geo_tools()
    valid_places = [
        place for place in resolved_places
        if place.viDo is not None and place.kinhDo is not None
    ]
    for origin, destination in zip(valid_places, valid_places[1:]):
        origin_coords = f"{origin.viDo},{origin.kinhDo}"
        destination_coords = f"{destination.viDo},{destination.kinhDo}"
        route = geo_tools.calculate_distance_time(
            origin=origin_coords,
            destination=destination_coords,
            profile="foot-walking",
        )
        if not route:
            continue
        duration = float(route.get("duration_minutes") or 0.0)
        distance = float(route.get("distance_km") or 0.0)
        if duration <= 0 or distance <= 0:
            return route, "OSRM foot-walking trả distance/duration không hợp lệ."
        speed = distance / (duration / 60)
        if not (3.5 <= speed <= 6.0):
            return route, f"OSRM foot-walking trả vận tốc phi thực tế {speed:.2f} km/h."
        return route, None
    return None, "Không tìm được cặp địa điểm liên tiếp đủ tọa độ để probe OSRM."


def validate_weather(client: Client, province: TinhThanh, weather_snapshot: Dict[str, Any]) -> Optional[str]:
    if not weather_snapshot:
        return "Response tạo plan không chứa weather snapshot."
    if province.viDo is None or province.kinhDo is None:
        return "Tỉnh Quảng Ninh chưa có tọa độ ở bảng TINHTHANH để đối chiếu weather."

    proxy_response = client.get(
        WEATHER_ENDPOINT,
        {"lat": province.viDo, "lon": province.kinhDo},
    )
    if proxy_response.status_code != 200:
        return f"Weather proxy trả status {proxy_response.status_code}."

    proxy_payload = parse_json_response(proxy_response)
    snapshot_coord = weather_snapshot.get("coord") or {}
    proxy_coord = proxy_payload.get("coord") or {}
    try:
        lat_diff = abs(float(snapshot_coord.get("lat")) - float(proxy_coord.get("lat")))
        lon_diff = abs(float(snapshot_coord.get("lon")) - float(proxy_coord.get("lon")))
    except Exception:
        return "Weather payload không có coord hợp lệ để đối chiếu."

    if lat_diff > 0.2 or lon_diff > 0.2:
        return (
            "Weather snapshot trong plan lệch so với Weather Proxy "
            f"(lat diff={lat_diff:.4f}, lon diff={lon_diff:.4f})."
        )

    snapshot_weather = ((weather_snapshot.get("weather") or [{}])[0] or {}).get("main")
    proxy_weather = ((proxy_payload.get("weather") or [{}])[0] or {}).get("main")
    if snapshot_weather and proxy_weather and snapshot_weather != proxy_weather:
        return (
            "Weather condition trong plan không khớp proxy "
            f"({snapshot_weather} != {proxy_weather})."
        )

    return None


def build_save_payload(
    structured_payload: Dict[str, Any],
    generation_payload: Dict[str, Any],
    province: TinhThanh,
) -> Dict[str, Any]:
    return {
        "plan": structured_payload,
        "destination": province.tenTinhThanh,
        "description": "Ultimate end-to-end persistence verification",
        "travelers": generation_payload["travelers"],
        "title": f"E2E Quảng Ninh {timezone.now().strftime('%Y%m%d%H%M%S')}",
        "budget": generation_payload["budget"],
        "days": generation_payload["days"],
    }


def assert_persistence(
    client: Client,
    save_payload: Dict[str, Any],
    expected_items: int,
    access_token: str,
) -> Tuple[Optional[int], Optional[str]]:
    before_itineraries = LichTrinh.objects.count()
    before_items = LichTrinhDiaDiem.objects.count()

    response = client.post(
        SAVE_ENDPOINT,
        data=json.dumps(save_payload, ensure_ascii=False),
        content_type="application/json",
        HTTP_AUTHORIZATION=f"Bearer {access_token}",
    )
    response_data = parse_json_response(response)
    if response.status_code != 201:
        return None, f"SaveTravelPlanView trả {response.status_code}: {response_data}"

    after_itineraries = LichTrinh.objects.count()
    after_items = LichTrinhDiaDiem.objects.count()

    if after_itineraries - before_itineraries != 1:
        return None, f"Bảng LichTrinh không tăng đúng +1 (delta={after_itineraries - before_itineraries})."
    if after_items - before_items != expected_items:
        return None, (
            "Bảng LichTrinhDiaDiem không tăng đúng theo timeline "
            f"(kỳ vọng {expected_items}, thực tế {after_items - before_items})."
        )

    return int(response_data.get("maLichTrinh")), None


def main() -> int:
    province = get_quang_ninh()
    payload = build_payload(province)

    anonymous_client = Client()
    print("[SETUP] Bắt đầu generate lịch trình thật cho Quảng Ninh...")
    generation_response = anonymous_client.post(
        GENERATE_ENDPOINT,
        data=json.dumps(payload, ensure_ascii=False),
        content_type="application/json",
    )
    generation_data = parse_json_response(generation_response)
    if generation_response.status_code != 201:
        print(f"[ERROR] Generate endpoint trả {generation_response.status_code}")
        print(json.dumps(generation_data, ensure_ascii=False, indent=2))
        return 1

    plan_data = generation_data.get("plan") or {}
    structured_payload = plan_data.get("structured_output")
    if not isinstance(structured_payload, dict):
        print("[ERROR] Response không chứa structured_output hợp lệ.")
        print(json.dumps(generation_data, ensure_ascii=False, indent=2))
        return 1

    validated_plan = validate_plan_payload(structured_payload)
    normalized_payload = dump_plan_payload(validated_plan)
    timeline_items = extract_timeline_items(normalized_payload)
    print(f"[LLM] Nhận được structured output hợp lệ với {len(timeline_items)} timeline items.")

    resolved_places, invalid_items = validate_rag_and_geography(normalized_payload, province)
    if invalid_items:
        print("[RAG] Thất bại: có địa điểm ngoài Quảng Ninh hoặc không resolve được.")
        for item in invalid_items[:10]:
            print(f"  - {item}")
        return 1
    print(f"[RAG] 100% place_id thuộc tập {len(resolved_places)} POI Quảng Ninh dùng trong itinerary.")

    walking_errors, walking_count = validate_walking_segments(normalized_payload)
    if walking_errors:
        print("[ROUTING] Thất bại ở transport_to_next walking.")
        for error in walking_errors:
            print(f"  - {error}")
        return 1
    print(f"[ROUTING] Walking segments trong plan: {walking_count}.")

    osrm_probe, osrm_error = probe_real_osrm_route(resolved_places)
    if osrm_error:
        print(f"[ROUTING] {osrm_error}")
        return 1
    assert osrm_probe is not None
    probe_speed = osrm_probe["distance_km"] / (osrm_probe["duration_minutes"] / 60)
    print(
        "[ROUTING] OSRM foot-walking OK: "
        f"{osrm_probe['distance_km']} km / {osrm_probe['duration_minutes']} phút "
        f"(~{probe_speed:.2f} km/h, source={osrm_probe.get('source')})."
    )

    weather_error = validate_weather(anonymous_client, province, plan_data.get("weather") or {})
    if weather_error:
        print(f"[WEATHER] {weather_error}")
        return 1
    print("[WEATHER] Weather snapshot trong plan khớp với Weather Proxy nội bộ.")

    user = ensure_test_user()
    save_client = Client()
    access_token = str(AccessToken.for_user(user))
    save_payload = build_save_payload(normalized_payload, payload, province)
    expected_saved_items = count_unique_day_place_pairs(normalized_payload)
    new_itinerary_id, save_error = assert_persistence(
        save_client,
        save_payload,
        expected_items=expected_saved_items,
        access_token=access_token,
    )
    if save_error:
        print(f"[SAVE] {save_error}")
        return 1

    print(
        f"[SAVE] Đã lưu lịch trình mới với maLichTrinh={new_itinerary_id} "
        f"và {expected_saved_items} điểm theo ràng buộc unique của SQLite."
    )
    print("[SUCCESS] RAG, Weather, Routing và Persistence đều vượt qua bài test tích hợp cuối cùng.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
