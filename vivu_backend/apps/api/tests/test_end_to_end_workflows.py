from __future__ import annotations

import asyncio
from datetime import date
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.api.chat_views import ChatView
from apps.api.travel_plan_step_views import (
    Step1LocationSelectionView,
    Step2TravelInfoView,
    Step3BudgetSuggestionView,
    Step4ConfirmAndPlanView,
    Step4SaveItineraryView,
)
from apps.itineraries.models import DongGop, LichTrinh, LichTrinhDiaDiem
from apps.places.models import DiaDiem, TinhThanh
from apps.places.contribution_service import approve_contribution
from agents.state import FullTravelPlanOutput
from agents.travel_agents.planning_agent import PlanningAgent


def _sample_full_travel_plan_output() -> dict:
    return {
        "trip_overview": {
            "total_distance_km": 42.0,
            "total_estimated_cost": 3200000,
            "fitness_level_required": "Thap",
        },
        "daily_itinerary": [
            {
                "day": 1,
                "date": "2026-06-20",
                "theme": "Bien Hoa trung tam",
                "route_flow": [],
                "timeline": [
                    {
                        "time_start": "08:30",
                        "time_end": "10:00",
                        "place_id": "",
                        "activity_name": "Cong vien Bien Hoa",
                        "cost": 100000,
                        "transport_to_next": {
                            "mode": "Xe may",
                            "duration_mins": 15,
                            "distance_km": 4.5,
                        },
                        "local_hint": "Uu tien buoi sang thoang mat.",
                        "plan_b_fallback": {
                            "place_id": None,
                            "name": "Quan ca phe gan do",
                            "reason": "Dung khi troi mua.",
                        },
                    },
                    {
                        "time_start": "10:30",
                        "time_end": "12:00",
                        "place_id": "",
                        "activity_name": "Nha hang Dong Nai",
                        "cost": 220000,
                        "transport_to_next": {
                            "mode": "Di bo",
                            "duration_mins": 8,
                            "distance_km": 0.6,
                        },
                        "local_hint": "Thu mon dac san dia phuong.",
                        "plan_b_fallback": {
                            "place_id": None,
                            "name": "Quan an du phong",
                            "reason": "Thay the khi het cho.",
                        },
                    },
                ],
            }
        ],
        "budget_analytics": {
            "accommodation_total": 1200000,
            "transportation_total": 700000,
            "food_total": 500000,
            "activities_total": 500000,
            "emergency_buffer": 300000,
        },
        "packing_checklist": {
            "documents": ["Can cuoc cong dan"],
            "clothing": ["Do thoang"],
            "medical": ["Thuoc ca nhan"],
        },
    }


class StubTravelChatbot:
    llm = True
    vector_db = None

    def chat(self, user_message, use_rag=False, destination=None):
        return {
            "response": f"Da ghi nho hoi thoai cho {destination or 'khach'}: {user_message[:40]}",
            "destination": destination,
        }


class EndToEndWorkflowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.factory = APIRequestFactory()
        cls.user_model = get_user_model()
        cls.user = cls.user_model.objects.create_user(
            username="e2e_user",
            password="E2ePass123!",
            email="e2e-user@example.com",
            vaiTro="user",
            trangThai="active",
        )
        cls.admin_user = cls.user_model.objects.create_user(
            username="e2e_admin",
            password="E2eAdmin123!",
            email="e2e-admin@example.com",
            vaiTro="admin",
            trangThai="active",
            is_staff=True,
        )
        cls.province = TinhThanh.objects.create(
            tenTinhThanh="Tỉnh Đồng Nai",
            moTa="Fixture phục vụ kiểm thử tích hợp Đồng Nai.",
            viDo=10.95,
            kinhDo=106.82,
        )
        cls.poi_park = DiaDiem.objects.create(
            tenDiaDiem="Cong vien Bien Hoa",
            moTa="Điểm dừng buổi sáng tại Biên Hòa.",
            diaChi="Biên Hòa, Tỉnh Đồng Nai",
            maTinhThanh=cls.province,
            loaiDiaDiem="dia_danh",
            viDo=10.95,
            kinhDo=106.84,
            trangThai="active",
        )
        cls.poi_food = DiaDiem.objects.create(
            tenDiaDiem="Nha hang Dong Nai",
            moTa="Điểm ăn trưa tại Biên Hòa.",
            diaChi="Biên Hòa, Tỉnh Đồng Nai",
            maTinhThanh=cls.province,
            loaiDiaDiem="nha_hang",
            viDo=10.96,
            kinhDo=106.83,
            trangThai="active",
        )

    def setUp(self):
        cache.clear()
        self.client.force_login(self.user)

    def test_user_contribution_submission_defaults_to_pending(self):
        response = self.client.post(
            "/places/submit/",
            data={
                "tenDiaDiem": "Thac Giang Dien Fixture",
                "maTinhThanh": self.province.pk,
                "diaChi": "Trang Bom, Tỉnh Đồng Nai",
                "moTa": "Đề xuất mới trong khu vực Đồng Nai.",
                "viDo": "10.999999",
                "kinhDo": "106.912345",
                "soDienThoai": "0909123456",
                "website": "https://fixture.example.com",
                "moTa": "Đề xuất mới trong khu vực Đồng Nai.",
            },
            follow=False,
        )

        self.assertEqual(response.status_code, 302)
        contribution = DongGop.objects.get(maNguoiDung=self.user, loaiDongGop="THEM_MOI_POI")
        self.assertEqual(contribution.trangThai, "pending")
        self.assertIsInstance(contribution.duLieuBoSung, dict)
        self.assertEqual(contribution.duLieuBoSung["ten_tinh_thanh"], "Tỉnh Đồng Nai")

    def test_admin_approval_pushes_contribution_into_diadiem(self):
        contribution = DongGop.objects.create(
            maNguoiDung=self.user,
            maDiaDiem=None,
            loaiDongGop="THEM_MOI_POI",
            noiDung="Đề xuất điểm mới tại Đồng Nai",
            trangThai="pending",
            duLieuBoSung={
                "ten_dia_diem": "Vuon trai cay Long Khanh",
                "ma_tinh_thanh": self.province.pk,
                "ten_tinh_thanh": self.province.tenTinhThanh,
                "dia_chi": "Long Khánh, Tỉnh Đồng Nai",
                "mo_ta": "Điểm tham quan thử nghiệm.",
                "toa_do": {"vi_do": 10.922, "kinh_do": 107.158},
                "de_xuat_hinh_anh": [{"file_name": "mock.jpg", "la_chinh": True}],
            },
        )

        with patch("apps.places.contribution_service.sync_place_to_chroma") as sync_mock:
            place = approve_contribution(contribution, approver=self.admin_user)

        contribution.refresh_from_db()
        self.assertEqual(contribution.trangThai, "approved")
        self.assertIsNotNone(contribution.maDiaDiem)
        self.assertEqual(place.maTinhThanh.tenTinhThanh, "Tỉnh Đồng Nai")
        sync_mock.assert_called_once()

    def test_four_step_flow_and_save_persists_junction_rows(self):
        geo_stub = SimpleNamespace(
            geocode=lambda name: {
                "formatted_address": name if "Tỉnh Đồng Nai" in name else f"{name}, Tỉnh Đồng Nai",
                "latitude": 10.95,
                "longitude": 106.82,
            },
            calculate_distance_time=lambda origin, destination: {
                "distance_km": 32.5,
                "duration_minutes": 55,
            },
        )
        transport_stub = SimpleNamespace(
            compare_all_transport_options=lambda origin, destination, travelers: {
                "distance_km": 32.5,
                "duration_minutes": 55,
                "options": [{"method": "car", "cost_vnd": 450000}],
            }
        )
        orchestrator_result = {
            "transport": {"method": "car", "estimated_cost_vnd": 450000},
            "hotels": [{"name": "Khach san Bien Hoa", "price_vnd": 1200000}],
            "selected_hotel": {"name": "Khach san Bien Hoa", "price_vnd": 1200000},
            "budget": {"total_vnd": 3200000},
            "activities": [{"name": self.poi_park.tenDiaDiem}],
            "restaurants": [{"name": self.poi_food.tenDiaDiem}],
            "itinerary": {"summary": "Fixture itinerary"},
            "itinerary_json": _sample_full_travel_plan_output(),
            "transport_cost": 450000,
            "accommodation_cost": 1200000,
            "activities_cost": 500000,
            "dining_cost": 500000,
        }

        request = self.factory.post(
            "/api/v1/travel-plans/step1/",
            {"origin": "Thành phố Hồ Chí Minh", "destination": "Tỉnh Đồng Nai"},
            format="json",
        )
        force_authenticate(request, user=self.user)
        with patch("tools.geo_tools.get_geo_tools", return_value=geo_stub):
            response = Step1LocationSelectionView.as_view()(request)
        self.assertEqual(response.status_code, 200)

        request = self.factory.post(
            "/api/v1/travel-plans/step2/",
            {
                "origin": "Thành phố Hồ Chí Minh",
                "destination": "Tỉnh Đồng Nai",
                "start_date": "2026-06-20",
                "days": 2,
                "travelers": 2,
            },
            format="json",
        )
        force_authenticate(request, user=self.user)
        with patch("tools.geo_tools.get_geo_tools", return_value=geo_stub), patch(
            "tools.transport_tools.get_transport_tools",
            return_value=transport_stub,
        ):
            response = Step2TravelInfoView.as_view()(request)
        self.assertEqual(response.status_code, 200)

        request = self.factory.post(
            "/api/v1/travel-plans/step3/",
            {
                "origin": "Thành phố Hồ Chí Minh",
                "destination": "Tỉnh Đồng Nai",
                "start_date": "2026-06-20",
                "days": 2,
                "travelers": 2,
                "travel_style": "standard",
                "rooms": 1,
                "selected_transport": {"method": "car", "cost_vnd": 450000},
            },
            format="json",
        )
        force_authenticate(request, user=self.user)
        with patch(
            "agents.travel_agents.orchestrator_agent.OrchestratorAgent.execute",
            new=AsyncMock(return_value=orchestrator_result),
        ):
            response = Step3BudgetSuggestionView.as_view()(request)
        self.assertEqual(response.status_code, 200)

        request = self.factory.post(
            "/api/v1/travel-plans/step4/",
            {
                "origin": "Thành phố Hồ Chí Minh",
                "destination": "Tỉnh Đồng Nai",
                "start_date": "2026-06-20",
                "days": 2,
                "travelers": 2,
                "travel_style": "standard",
                "rooms": 1,
                "selected_hotel": {"name": "Khach san Bien Hoa", "price_vnd": 1200000},
                "budget": 3200000,
                "interests": ["am thuc", "thu gian"],
            },
            format="json",
        )
        force_authenticate(request, user=self.user)
        with patch(
            "agents.travel_agents.orchestrator_agent.OrchestratorAgent.execute",
            new=AsyncMock(return_value=orchestrator_result),
        ), patch(
            "agents.travel_agents.activities_agent._normalize_destination_name_for_display",
            return_value="Tỉnh Đồng Nai",
        ):
            response = Step4ConfirmAndPlanView.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertIn("itinerary_json", response.data["plan"])

        request = self.factory.post(
            "/api/v1/travel-plans/step4/save/",
            {
                "origin": "Thành phố Hồ Chí Minh",
                "destination": "Tỉnh Đồng Nai",
                "start_date": "2026-06-20",
                "days": 2,
                "travelers": 2,
                "plan": response.data["plan"],
            },
            format="json",
        )
        force_authenticate(request, user=self.user)
        response = Step4SaveItineraryView.as_view()(request)
        self.assertEqual(response.status_code, 201)

        itinerary = LichTrinh.objects.latest("maLichTrinh")
        self.assertTrue(itinerary.is_ai_generated)
        self.assertEqual(itinerary.maTinhThanh.tenTinhThanh, "Tỉnh Đồng Nai")
        self.assertEqual(
            LichTrinhDiaDiem.objects.filter(maLichTrinh=itinerary).count(),
            2,
        )

    def test_chat_retains_context_for_ten_rounds(self):
        def fake_initialize_agents(instance):
            instance.rag_agent = None
            instance.travel_chatbot = StubTravelChatbot()

        conversation_id = "fixture-chat-10-rounds"
        with patch.object(ChatView, "_initialize_agents", fake_initialize_agents), patch.object(
            ChatView,
            "_get_context_from_multiple_sources",
            return_value="Biên Hòa có món nướng và khách sạn trung tâm.",
        ):
            view = ChatView.as_view()
            last_response = None
            for message in [
                "Tôi muốn đi Biên Hòa",
                "Ở đó đi đâu chơi buổi sáng?",
                "Ở đó có đặc sản gì ngon?",
                "Có chỗ nào cho gia đình không?",
                "Khách sạn nào ở trung tâm?",
                "Đi lại nội thành có tiện không?",
                "Còn về chỗ khách sạn đã chọn ở Bước 3 thì sao?",
                "Nếu trời mưa thì đổi hoạt động nào?",
                "Tổng chi phí khoảng bao nhiêu?",
                "Chốt giúp tôi lịch trình ngắn gọn.",
            ]:
                request = self.factory.post(
                    "/api/v1/chat/",
                    {
                        "message": message,
                        "destination": "Tỉnh Đồng Nai",
                        "conversation_id": conversation_id,
                        "use_chatbot": True,
                    },
                    format="json",
                )
                request.user = self.user
                last_response = view(request)

        self.assertIsNotNone(last_response)
        self.assertEqual(last_response.status_code, 200)
        self.assertEqual(last_response.data["conversation_id"], conversation_id)
        self.assertEqual(last_response.data["conversation_turns"], 20)

    def test_fallback_chain_moves_from_groq_to_gemini(self):
        candidate_calls = []
        validated_plan = FullTravelPlanOutput.model_validate(_sample_full_travel_plan_output())
        agent = PlanningAgent()

        def fake_invoke(candidate, prompt, schema):
            candidate_calls.append(candidate["name"])
            if candidate["name"] == "groq":
                raise RuntimeError("Groq timeout")
            return validated_plan

        async def run_case():
            with patch("agents.travel_agents.planning_agent.get_llm_candidates", return_value=[
                {"name": "groq", "type": "gemini", "api_key": "x", "model": "groq-mock"},
                {"name": "gemini", "type": "gemini", "api_key": "y", "model": "gemini-mock"},
            ]), patch(
                "agents.travel_agents.planning_agent.invoke_candidate_structured",
                side_effect=fake_invoke,
            ), patch.object(
                PlanningAgent,
                "_post_process_structured_output",
                side_effect=lambda result, state: result,
            ):
                return await agent._build_structured_output(
                    state={"destination": "Tỉnh Đồng Nai", "days": 1, "start_date": date.today().isoformat()},
                    itinerary={"days": []},
                )

        result = asyncio.run(run_case())
        self.assertEqual(candidate_calls, ["groq", "gemini"])
        self.assertEqual(result.trip_overview.total_estimated_cost, 3200000)
