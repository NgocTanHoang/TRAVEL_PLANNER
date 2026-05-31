from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.api.travel_plan_step_views import Step1LocationSelectionView
from apps.api.travel_plan_views import SaveTravelPlanView, TravelPlanStreamView
from apps.api.views import ItineraryDetailView
from apps.itineraries.models import LichTrinh
from apps.places.models import DiaDiem, TinhThanh
from utils.travel_plan_streaming import initialize_run


class TravelPlanAuthTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.factory = APIRequestFactory()
        cls.user = get_user_model().objects.create_user(
            username="travel_auth_user",
            password="TravelAuth123!",
            email="travel-auth@example.com",
        )
        cls.other_user = get_user_model().objects.create_user(
            username="travel_auth_other_user",
            password="TravelAuth456!",
            email="travel-auth-other@example.com",
        )
        if hasattr(cls.user, "vaiTro"):
            cls.user.vaiTro = "user"
        if hasattr(cls.user, "trangThai"):
            cls.user.trangThai = "active"
        cls.user.save()
        if hasattr(cls.other_user, "vaiTro"):
            cls.other_user.vaiTro = "user"
        if hasattr(cls.other_user, "trangThai"):
            cls.other_user.trangThai = "active"
        cls.other_user.save()

        cls.province = TinhThanh.objects.create(
            tenTinhThanh="Tinh Auth Dong Nai",
            moTa="Tinh phuc vu test auth cho luong travel plan.",
            viDo=10.95,
            kinhDo=106.82,
        )
        cls.place = DiaDiem.objects.create(
            tenDiaDiem="Diem Auth Bien Hoa",
            moTa="Dia diem active de kiem thu IDOR save flow.",
            diaChi="Bien Hoa, Tinh Auth Dong Nai",
            maTinhThanh=cls.province,
            loaiDiaDiem="dia_danh",
            viDo=10.951,
            kinhDo=106.821,
            giaVe=100000,
            gioMoCua="08:00",
            gioDongCua="18:00",
            danhGiaTrungBinh=4.5,
            soLuotDanhGia=5,
            trangThai="active",
        )

    def _build_plan_payload(self) -> dict:
        return {
            "maNguoiDung": 999999,
            "destination": self.province.tenTinhThanh,
            "description": "Payload test auth va IDOR.",
            "travelers": 2,
            "title": "Auth guard itinerary",
            "budget": 6500000,
            "plan": {
                "trip_overview": {
                    "total_distance_km": 12.5,
                    "total_estimated_cost": 6500000,
                    "fitness_level_required": "Thap",
                },
                "daily_itinerary": [
                    {
                        "day": 1,
                        "date": "2026-11-13",
                        "theme": "Ngay bao mat",
                        "route_flow": [str(self.place.maDiaDiem)],
                        "timeline": [
                            {
                                "time_start": "08:00",
                                "time_end": "09:00",
                                "place_id": str(self.place.maDiaDiem),
                                "activity_name": self.place.tenDiaDiem,
                                "cost": 100000,
                                "transport_to_next": {
                                    "mode": "Di bo",
                                    "duration_mins": 10,
                                    "distance_km": 0.4,
                                },
                                "local_hint": "Chi duoc gan vao request.user.",
                                "plan_b_fallback": {
                                    "place_id": str(self.place.maDiaDiem),
                                    "name": "Diem du phong",
                                    "reason": "Phong mua",
                                },
                            }
                        ],
                    }
                ],
                "budget_analytics": {
                    "accommodation_total": 2000000,
                    "transportation_total": 1200000,
                    "food_total": 900000,
                    "activities_total": 1500000,
                    "emergency_buffer": 900000,
                },
                "packing_checklist": {
                    "documents": ["CCCD"],
                    "clothing": ["Ao nhe"],
                    "medical": ["Thuoc ca nhan"],
                },
            },
        }

    def test_step1_requires_authenticated_user(self):
        request = self.factory.post(
            "/api/v1/travel-plans/step1/",
            {
                "origin": "Thanh pho Ho Chi Minh",
                "destination": "Tinh Dong Nai",
            },
            format="json",
        )

        response = Step1LocationSelectionView.as_view()(request)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data["error"], "Bạn cần đăng nhập để sử dụng tính năng này.")

    def test_save_travel_plan_requires_authenticated_user(self):
        request = self.factory.post(
            "/api/v1/travel-plans/save/",
            self._build_plan_payload(),
            format="json",
        )

        response = SaveTravelPlanView.as_view()(request)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data["error"], "Bạn cần đăng nhập để sử dụng tính năng này.")

    def test_save_travel_plan_ignores_payload_user_override(self):
        request = self.factory.post(
            "/api/v1/travel-plans/save/",
            self._build_plan_payload(),
            format="json",
        )
        force_authenticate(request, user=self.user)

        response = SaveTravelPlanView.as_view()(request)

        self.assertEqual(response.status_code, 201)
        lich_trinh = LichTrinh.objects.get(maLichTrinh=response.data["maLichTrinh"])
        self.assertEqual(lich_trinh.maNguoiDung_id, self.user.pk)

    def test_stream_rejects_other_user_thread_access(self):
        thread_id = "travel-plan-auth-guard"
        initialize_run(
            thread_id=thread_id,
            owner_key=f"user:{self.user.pk}",
            request_payload={"origin": "A", "destination": "B"},
            workflow_engine="langgraph",
        )
        request = self.factory.get(f"/api/v1/travel-plans/stream/{thread_id}/")
        force_authenticate(request, user=self.other_user)

        response = TravelPlanStreamView.as_view()(request, thread_id=thread_id)
        self.assertEqual(response.status_code, 403)

    def test_itinerary_detail_rejects_non_owner_access(self):
        itinerary = LichTrinh.objects.create(
            maNguoiDung=self.user,
            maTinhThanh=self.province,
            tieuDe="Owner itinerary",
            moTa="Owner-only resource",
            ngayBatDau="2026-11-13",
            ngayKetThuc="2026-11-13",
            soNgay=1,
            soNguoi=2,
            nganSach=1000000,
            chiPhiUocTinh=1000000,
            trangThai="draft",
            laCongKhai=False,
        )
        request = self.factory.get(f"/api/v1/itineraries/{itinerary.maLichTrinh}/")
        force_authenticate(request, user=self.other_user)

        response = ItineraryDetailView.as_view()(request, id=itinerary.maLichTrinh)
        self.assertEqual(response.status_code, 404)
