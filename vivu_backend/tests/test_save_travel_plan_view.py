from __future__ import annotations

import copy
import json
from pathlib import Path

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.api.travel_plan_views import SaveTravelPlanView
from apps.itineraries.models import LichTrinh, LichTrinhDiaDiem
from apps.places.models import DiaDiem, TinhThanh


REPO_ROOT = Path(__file__).resolve().parents[2]
PAYLOAD_PATH = REPO_ROOT / "vivu_backend" / "scripts" / "artifacts" / "agent_output_test.json"


class SaveTravelPlanViewFixtureTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.factory = APIRequestFactory()
        cls.user = get_user_model().objects.create_user(
            username="save_view_fixture_user",
            password="FixturePass123!",
            email="fixture-save@example.com",
        )
        if hasattr(cls.user, "hoTen"):
            cls.user.hoTen = "Fixture Save User"
        if hasattr(cls.user, "vaiTro"):
            cls.user.vaiTro = getattr(cls.user, "vaiTro", None) or "user"
        if hasattr(cls.user, "trangThai"):
            cls.user.trangThai = getattr(cls.user, "trangThai", None) or "active"
        cls.user.save()

        cls.province = TinhThanh.objects.create(
            tenTinhThanh="Tỉnh Fixture Save View",
            moTa="Tỉnh phục vụ fixture kiểm thử SaveTravelPlanView.",
            viDo=10.123,
            kinhDo=106.456,
        )

        with PAYLOAD_PATH.open("r", encoding="utf-8") as handle:
            cls.raw_payload = json.load(handle)

    def _count_timeline_items(self, payload):
        return sum(len(day.get("timeline", [])) for day in payload.get("daily_itinerary", []))

    def _ensure_places(self, required_count: int):
        for index in range(required_count):
            ordinal = index + 1
            DiaDiem.objects.create(
                tenDiaDiem=f"Fixture Save Place {ordinal}",
                moTa="Dữ liệu fixture kiểm thử lưu lịch trình.",
                diaChi=f"Số {ordinal} Đường Fixture, {self.province.tenTinhThanh}",
                maTinhThanh=self.province,
                loaiDiaDiem="dia_danh",
                viDo=10.0 + ordinal / 1000,
                kinhDo=106.0 + ordinal / 1000,
                giaVe=0,
                gioMoCua="08:00",
                gioDongCua="21:00",
                website="https://example.com",
                danhGiaTrungBinh=4.2,
                soLuotDanhGia=1,
                soLuotXem=1,
                trangThai="active",
                dacDiem=json.dumps({"fixture": True}, ensure_ascii=False),
            )

    def _build_payload(self):
        normalized = copy.deepcopy(self.raw_payload)
        total_items = self._count_timeline_items(normalized)
        self._ensure_places(total_items)
        places = list(
            DiaDiem.objects.filter(maTinhThanh=self.province, trangThai="active")
            .order_by("maDiaDiem")[:total_items]
        )

        index = 0
        for day in normalized.get("daily_itinerary", []):
            for timeline_item in day.get("timeline", []):
                place = places[index]
                index += 1
                timeline_item["place_id"] = str(place.maDiaDiem)
                timeline_item["activity_name"] = place.tenDiaDiem

        return {
            "plan": normalized,
            "destination": self.province.tenTinhThanh,
            "description": "Fixture test payload cho SaveTravelPlanView",
            "travelers": 2,
            "title": f"Fixture Save Test {timezone.now().strftime('%Y%m%d%H%M%S')}",
            "budget": normalized.get("trip_overview", {}).get("total_estimated_cost", 0),
            "days": len(normalized.get("daily_itinerary", [])),
        }, total_items

    def test_save_travel_plan_view_persists_fixture_payload(self):
        request_payload, expected_timeline_items = self._build_payload()
        before_itineraries = LichTrinh.objects.count()
        before_places = LichTrinhDiaDiem.objects.count()

        request = self.factory.post("/api/v1/travel-plans/save/", request_payload, format="json")
        force_authenticate(request, user=self.user)
        response = SaveTravelPlanView.as_view()(request)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(LichTrinh.objects.count(), before_itineraries + 1)
        self.assertEqual(LichTrinhDiaDiem.objects.count(), before_places + expected_timeline_items)
