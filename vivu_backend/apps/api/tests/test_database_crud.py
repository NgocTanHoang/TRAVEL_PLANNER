from __future__ import annotations

from datetime import date

from django.contrib.auth import get_user_model
from django.db import transaction
from django.test import TestCase
from rest_framework.test import APIRequestFactory, force_authenticate

from apps.analytics.models import YeuCauLoTrinh
from apps.api.travel_plan_views import SaveTravelPlanView
from apps.itineraries.models import (
    LichTrinh,
    LichTrinhDiaDiem,
)
from apps.places.models import DiaDiem, TinhThanh


class DatabaseCrudTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user_model = get_user_model()
        cls.province = TinhThanh.objects.create(
            tenTinhThanh="Tỉnh CRUD Đồng Nai",
            moTa="Tỉnh mẫu phục vụ kiểm thử CRUD tự động.",
            viDo=10.95,
            kinhDo=106.82,
        )
        cls.place_a = DiaDiem.objects.create(
            tenDiaDiem="Điểm đến CRUD A",
            moTa="Địa điểm active để kiểm thử truy vấn và liên kết.",
            diaChi="Khu trung tâm, Thành phố Biên Hòa, Tỉnh CRUD Đồng Nai",
            maTinhThanh=cls.province,
            loaiDiaDiem="dia_danh",
            viDo=10.951,
            kinhDo=106.821,
            giaVe=120000,
            gioMoCua="08:00",
            gioDongCua="20:00",
            danhGiaTrungBinh=4.7,
            soLuotDanhGia=14,
            trangThai="active",
        )
        cls.place_b = DiaDiem.objects.create(
            tenDiaDiem="Điểm đến CRUD B",
            moTa="Địa điểm active thứ hai để kiểm thử xóa cascade.",
            diaChi="Khu ven sông, Thành phố Biên Hòa, Tỉnh CRUD Đồng Nai",
            maTinhThanh=cls.province,
            loaiDiaDiem="dia_danh",
            viDo=10.952,
            kinhDo=106.822,
            giaVe=90000,
            gioMoCua="09:00",
            gioDongCua="21:00",
            danhGiaTrungBinh=4.2,
            soLuotDanhGia=8,
            trangThai="active",
        )
        cls.place_inactive = DiaDiem.objects.create(
            tenDiaDiem="Điểm đến CRUD Inactive",
            moTa="Địa điểm inactive để kiểm thử bộ lọc trạng thái.",
            diaChi="Khu cũ, Tỉnh CRUD Đồng Nai",
            maTinhThanh=cls.province,
            loaiDiaDiem="dia_danh",
            viDo=10.953,
            kinhDo=106.823,
            giaVe=0,
            gioMoCua="00:00",
            gioDongCua="00:00",
            danhGiaTrungBinh=2.0,
            soLuotDanhGia=1,
            trangThai="inactive",
        )

    def test_create_user_itinerary_and_analytics_inside_atomic(self):
        with transaction.atomic():
            user = self.user_model.objects.create_user(
                username="crud_create_user",
                password="CrudCreate123!",
                email="crud-create@example.com",
            )
            if hasattr(user, "hoTen"):
                user.hoTen = "Người dùng CRUD"
            if hasattr(user, "vaiTro"):
                user.vaiTro = "user"
            if hasattr(user, "trangThai"):
                user.trangThai = "active"
            user.save()

            itinerary = LichTrinh.objects.create(
                maNguoiDung=user,
                maTinhThanh=self.province,
                tieuDe="Lịch trình CRUD tạo mới",
                moTa="Bản ghi dùng để xác nhận luồng tạo dữ liệu.",
                ngayBatDau=date(2026, 8, 10),
                ngayKetThuc=date(2026, 8, 12),
                soNgay=3,
                soNguoi=2,
                nganSach=5500000,
                chiPhiUocTinh=5100000,
                trangThai="draft",
                laCongKhai=False,
            )

            analytics = YeuCauLoTrinh.objects.create(
                maNguoiDung=user,
                maTinhThanhDiemDi=self.province,
                maTinhThanhDiemDen=self.province,
                diemDi="Thành phố Biên Hòa",
                diemDen="Tỉnh CRUD Đồng Nai",
                ngayKhoiHanhDuKien=date(2026, 8, 10),
                soNgayDi=3,
                soNguoi=2,
                nganSachDuKien=5500000,
                loaiYeuCau=YeuCauLoTrinh.LoaiYeuCau.TAO_KE_HOACH,
                trangThai=YeuCauLoTrinh.TrangThaiXuLy.THANH_CONG,
                duLieuPhanHoi={"fixture": "crud_create"},
            )

        self.assertTrue(self.user_model.objects.filter(username="crud_create_user").exists())
        self.assertTrue(LichTrinh.objects.filter(pk=itinerary.pk, maTinhThanh=self.province).exists())
        self.assertTrue(YeuCauLoTrinh.objects.filter(pk=analytics.pk, maNguoiDung=user).exists())

    def test_read_active_diadiem_query_and_index_plan(self):
        queryset = DiaDiem.objects.filter(
            maTinhThanh=self.province,
            trangThai="active",
        ).order_by("-danhGiaTrungBinh")

        active_ids = list(queryset.values_list("maDiaDiem", flat=True))
        self.assertEqual(active_ids, [self.place_a.maDiaDiem, self.place_b.maDiaDiem])

        explain_plan = queryset.explain().upper()
        self.assertTrue("INDEX" in explain_plan or "SEARCH" in explain_plan)

    def test_update_lichtrinh_fields_inside_atomic(self):
        user = self.user_model.objects.create_user(
            username="crud_update_user",
            password="CrudUpdate123!",
            email="crud-update@example.com",
        )
        itinerary = LichTrinh.objects.create(
            maNguoiDung=user,
            maTinhThanh=self.province,
            tieuDe="Lịch trình CRUD cập nhật",
            moTa="Bản ghi trước khi cập nhật.",
            ngayBatDau=date(2026, 9, 1),
            ngayKetThuc=date(2026, 9, 3),
            soNgay=3,
            soNguoi=2,
            nganSach=4000000,
            chiPhiUocTinh=3500000,
            trangThai="draft",
            laCongKhai=False,
        )

        with transaction.atomic():
            itinerary.chiPhiUocTinh = 4800000
            itinerary.laCongKhai = True
            itinerary.save(update_fields=["chiPhiUocTinh", "laCongKhai"])

        itinerary.refresh_from_db()
        self.assertEqual(itinerary.chiPhiUocTinh, 4800000)
        self.assertTrue(itinerary.laCongKhai)

    def test_delete_lichtrinh_cascades_to_junction_rows(self):
        user = self.user_model.objects.create_user(
            username="crud_delete_user",
            password="CrudDelete123!",
            email="crud-delete@example.com",
        )
        itinerary = LichTrinh.objects.create(
            maNguoiDung=user,
            maTinhThanh=self.province,
            tieuDe="Lịch trình CRUD xóa",
            moTa="Bản ghi để kiểm thử cascade delete.",
            ngayBatDau=date(2026, 10, 5),
            ngayKetThuc=date(2026, 10, 6),
            soNgay=2,
            soNguoi=2,
            nganSach=3000000,
            chiPhiUocTinh=2800000,
            trangThai="draft",
            laCongKhai=False,
        )
        LichTrinhDiaDiem.objects.create(
            maLichTrinh=itinerary,
            maDiaDiem=self.place_a,
            ngayThamQuan=date(2026, 10, 5),
            thoiGianThamQuan="08:00 - 10:00",
            thuTu=1,
            ghiChu="Điểm mở đầu",
            chiPhiUocTinh=120000,
        )
        LichTrinhDiaDiem.objects.create(
            maLichTrinh=itinerary,
            maDiaDiem=self.place_b,
            ngayThamQuan=date(2026, 10, 6),
            thoiGianThamQuan="14:00 - 16:00",
            thuTu=2,
            ghiChu="Điểm kết thúc",
            chiPhiUocTinh=90000,
        )

        with transaction.atomic():
            itinerary.delete()

        self.assertFalse(LichTrinh.objects.filter(pk=itinerary.pk).exists())
        self.assertFalse(LichTrinhDiaDiem.objects.filter(maLichTrinh_id=itinerary.pk).exists())


class SaveTravelPlanParserTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.factory = APIRequestFactory()
        cls.user = get_user_model().objects.create_user(
            username="parser_fixture_user",
            password="ParserFixture123!",
            email="parser-fixture@example.com",
        )
        if hasattr(cls.user, "hoTen"):
            cls.user.hoTen = "Người dùng parser"
        if hasattr(cls.user, "vaiTro"):
            cls.user.vaiTro = "user"
        if hasattr(cls.user, "trangThai"):
            cls.user.trangThai = "active"
        cls.user.save()

        cls.province = TinhThanh.objects.create(
            tenTinhThanh="Tỉnh Parser Đồng Nai",
            moTa="Tỉnh mẫu phục vụ kiểm thử parser itinerary.",
            viDo=10.96,
            kinhDo=106.84,
        )
        cls.place = DiaDiem.objects.create(
            tenDiaDiem="Điểm parser Biên Hòa",
            moTa="Địa điểm dùng để test duplicate safeguard.",
            diaChi="Phường Thống Nhất, Thành phố Biên Hòa, Tỉnh Parser Đồng Nai",
            maTinhThanh=cls.province,
            loaiDiaDiem="dia_danh",
            viDo=10.961,
            kinhDo=106.841,
            giaVe=150000,
            gioMoCua="08:00",
            gioDongCua="20:00",
            danhGiaTrungBinh=4.8,
            soLuotDanhGia=10,
            trangThai="active",
        )

    def test_save_travel_plan_parses_daily_itinerary_into_junction_table(self):
        payload = {
            "destination": self.province.tenTinhThanh,
            "description": "Payload parser có duplicate để xác nhận unique safeguard.",
            "travelers": 2,
            "title": "Parser itinerary fixture",
            "budget": 6500000,
            "plan": {
                "trip_overview": {
                    "total_distance_km": 12.5,
                    "total_estimated_cost": 6500000,
                    "fitness_level_required": "Thấp",
                },
                "daily_itinerary": [
                    {
                        "day": 1,
                        "date": "2026-11-12",
                        "theme": "Ngày nhẹ ở Biên Hòa",
                        "route_flow": [str(self.place.maDiaDiem)],
                        "timeline": [
                            {
                                "time_start": "08:00",
                                "time_end": "10:00",
                                "place_id": str(self.place.maDiaDiem),
                                "activity_name": self.place.tenDiaDiem,
                                "cost": 150000,
                                "transport_to_next": {
                                    "mode": "Đi bộ",
                                    "duration_mins": 15,
                                    "distance_km": 0.8,
                                },
                                "local_hint": "Đến sớm để tránh đông.",
                                "plan_b_fallback": {
                                    "place_id": str(self.place.maDiaDiem),
                                    "name": "Phương án trong nhà",
                                    "reason": "Dùng khi mưa bất chợt.",
                                },
                            },
                            {
                                "time_start": "10:30",
                                "time_end": "11:30",
                                "place_id": str(self.place.maDiaDiem),
                                "activity_name": self.place.tenDiaDiem,
                                "cost": 150000,
                                "transport_to_next": {
                                    "mode": "Đi bộ",
                                    "duration_mins": 10,
                                    "distance_km": 0.5,
                                },
                                "local_hint": "Bản ghi trùng để test upsert mềm.",
                                "plan_b_fallback": {
                                    "place_id": str(self.place.maDiaDiem),
                                    "name": "Phương án trong nhà",
                                    "reason": "Dùng khi mưa bất chợt.",
                                },
                            },
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
                    "documents": ["Căn cước công dân"],
                    "clothing": ["Áo nhẹ", "Giày đi bộ"],
                    "medical": ["Thuốc cá nhân"],
                },
            },
        }

        request = self.factory.post("/api/v1/travel-plans/save/", payload, format="json")
        force_authenticate(request, user=self.user)

        with transaction.atomic():
            response = SaveTravelPlanView.as_view()(request)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["soDiaDiemDaLuu"], 1)

        lich_trinh = LichTrinh.objects.get(maLichTrinh=response.data["maLichTrinh"])
        self.assertTrue(lich_trinh.is_ai_generated)

        self.assertEqual(LichTrinhDiaDiem.objects.filter(maLichTrinh=lich_trinh).count(), 1)

        detail_row = LichTrinhDiaDiem.objects.get(maLichTrinh=lich_trinh)
        self.assertEqual(detail_row.ngayThamQuan.isoformat(), "2026-11-12")
        self.assertEqual(detail_row.thuTu, 2)
        self.assertEqual(int(detail_row.chiPhiUocTinh), 150000)
        self.assertIn("Ngày nhẹ ở Biên Hòa", detail_row.ghiChu)
        self.assertIn("Bản ghi trùng để test upsert mềm.", detail_row.ghiChu)
