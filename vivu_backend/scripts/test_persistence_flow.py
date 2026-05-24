"""Persistence smoke test for saving structured travel plans into SQLite."""
from __future__ import annotations

import argparse
import copy
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

import django
from django.utils import timezone

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent
PAYLOAD_PATH = REPO_ROOT / "agent_output_test.json"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "vivu_core.settings")
django.setup()

from apps.api.travel_plan_views import SaveTravelPlanView  # noqa: E402
from apps.itineraries.models import LichTrinh, LichTrinhDiaDiem  # noqa: E402
from apps.places.models import DiaDiem, TinhThanh  # noqa: E402
from apps.users.models import NguoiDung  # noqa: E402
from rest_framework.test import APIRequestFactory, force_authenticate  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Smoke test luồng lưu lịch trình vào SQLite.")
    parser.add_argument(
        "--province",
        default="Quảng Ninh",
        help="Tên tỉnh/thành dùng để resolve place_id cho payload mẫu.",
    )
    return parser.parse_args()


def load_sample_payload() -> Dict[str, Any]:
    with PAYLOAD_PATH.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def resolve_province(name: str) -> TinhThanh:
    province = TinhThanh.objects.filter(tenTinhThanh__iexact=name).first()
    if province:
        return province

    province = TinhThanh.objects.filter(tenTinhThanh__icontains=name).first()
    if province:
        return province

    raise SystemExit(f"Không tìm thấy tỉnh/thành phù hợp cho '{name}'.")


def ensure_test_user() -> NguoiDung:
    user, created = NguoiDung.objects.get_or_create(
        username="persistence_smoke_user",
        defaults={
            "email": "persistence-smoke@example.com",
            "hoTen": "Persistence Smoke",
            "vaiTro": "user",
            "trangThai": "active",
        },
    )
    if created or not user.email:
        user.email = "persistence-smoke@example.com"
    if created or not user.has_usable_password():
        user.set_password("PersistenceSmoke123!")
    user.hoTen = user.hoTen or "Persistence Smoke"
    user.vaiTro = user.vaiTro or "user"
    user.trangThai = user.trangThai or "active"
    user.save()
    return user


def count_timeline_items(plan_payload: Dict[str, Any]) -> int:
    total = 0
    for day in plan_payload.get("daily_itinerary", []):
        total += len(day.get("timeline", []))
    return total


def normalize_payload(plan_payload: Dict[str, Any], province: TinhThanh) -> Dict[str, Any]:
    normalized = copy.deepcopy(plan_payload)
    total_items = count_timeline_items(normalized)

    province_places = list(
        DiaDiem.objects.filter(maTinhThanh=province, trangThai="active")
        .order_by("maDiaDiem")[:total_items]
    )
    if len(province_places) < total_items:
        fallback_places = list(
            DiaDiem.objects.filter(trangThai="active")
            .exclude(maDiaDiem__in=[place.maDiaDiem for place in province_places])
            .order_by("maDiaDiem")[: total_items - len(province_places)]
        )
        province_places.extend(fallback_places)

    if len(province_places) < total_items:
        raise SystemExit(
            f"Không đủ DiaDiem active để map {total_items} timeline items. Chỉ có {len(province_places)}."
        )

    place_index = 0
    for day in normalized.get("daily_itinerary", []):
        for timeline_item in day.get("timeline", []):
            place = province_places[place_index]
            place_index += 1
            timeline_item["place_id"] = str(place.maDiaDiem)
            timeline_item["activity_name"] = place.tenDiaDiem

            fallback = timeline_item.get("plan_b_fallback")
            if isinstance(fallback, dict) and not fallback.get("name"):
                fallback["name"] = f"Phương án phụ gần {place.tenDiaDiem}"

    return normalized


def build_request_payload(plan_payload: Dict[str, Any], province: TinhThanh) -> Dict[str, Any]:
    itinerary_count = len(plan_payload.get("daily_itinerary", []))
    return {
        "plan": plan_payload,
        "destination": province.tenTinhThanh,
        "description": f"Smoke test save flow for {province.tenTinhThanh}",
        "travelers": 2,
        "title": f"Smoke Test {province.tenTinhThanh} {timezone.now().strftime('%Y%m%d%H%M%S')}",
        "budget": plan_payload.get("trip_overview", {}).get("total_estimated_cost", 0),
        "days": itinerary_count,
    }


def main() -> int:
    args = parse_args()
    province = resolve_province(args.province)
    user = ensure_test_user()

    raw_payload = load_sample_payload()
    normalized_plan = normalize_payload(raw_payload, province)
    expected_timeline_items = count_timeline_items(normalized_plan)
    request_payload = build_request_payload(normalized_plan, province)

    before_itineraries = LichTrinh.objects.count()
    before_itinerary_places = LichTrinhDiaDiem.objects.count()

    factory = APIRequestFactory()
    request = factory.post("/api/v1/travel-plans/save/", request_payload, format="json")
    force_authenticate(request, user=user)

    response = SaveTravelPlanView.as_view()(request)
    status_code = getattr(response, "status_code", None)
    response_data = getattr(response, "data", {})

    if status_code != 201:
        print("[ERROR] SaveTravelPlanView không trả về 201.")
        print(f"Status: {status_code}")
        print(f"Response: {response_data}")
        return 1

    after_itineraries = LichTrinh.objects.count()
    after_itinerary_places = LichTrinhDiaDiem.objects.count()

    itinerary_delta = after_itineraries - before_itineraries
    place_delta = after_itinerary_places - before_itinerary_places

    if itinerary_delta != 1:
        print(f"[ERROR] Bảng LichTrinh không tăng đúng +1. Delta hiện tại: {itinerary_delta}")
        return 1

    if place_delta != expected_timeline_items:
        print(
            "[ERROR] Bảng LichTrinhDiaDiem không tăng đúng theo số timeline items. "
            f"Kỳ vọng {expected_timeline_items}, thực tế {place_delta}."
        )
        return 1

    print(f"maLichTrinh mới: {response_data.get('maLichTrinh')}")
    print(f"soDiaDiemDaLuu: {response_data.get('soDiaDiemDaLuu')}")
    print("[SUCCESS] Luồng dữ liệu quan hệ từ AI gán vào SQLite hoạt động hoàn hảo!")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
