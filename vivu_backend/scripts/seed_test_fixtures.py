"""Seed faux fixtures for backend integration tests without touching core POIs."""
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import django

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
django.setup()

from django.db import transaction  # noqa: E402
from django.utils import timezone  # noqa: E402

from apps.analytics.models import YeuCauLoTrinh  # noqa: E402
from apps.itineraries.models import (  # noqa: E402
    DongGop,
    LichTrinh,
    LichTrinhDiaDiem,
)
from apps.places.models import DanhGia, DiaDiem, DiaDiemYeuThich, TinhThanh  # noqa: E402
from apps.users.models import LichSuTimKiem, NguoiDung  # noqa: E402


FIXTURE_MARKER = "fixture_seed_test_v1"
DEFAULT_PASSWORD = "ViVuFixture123!"


@dataclass(frozen=True)
class FixtureUserSpec:
    username: str
    email: str
    full_name: str
    profile_note: str
    phone: str
    home_address: str
    birth_date: date
    gender: str


USER_SPECS: Sequence[FixtureUserSpec] = (
    FixtureUserSpec(
        username="test_backpacker",
        email="test_backpacker@vivu.local",
        full_name="Nguyễn Minh Phượt",
        profile_note="Ưa lịch trình linh hoạt, thích trải nghiệm bản địa và quãng đường vừa phải.",
        phone="0901000001",
        home_address="Chung cư nhỏ đường Nguyễn Hữu Cảnh, Thành phố Hồ Chí Minh",
        birth_date=date(1997, 4, 18),
        gender="Nam",
    ),
    FixtureUserSpec(
        username="test_family",
        email="test_family@vivu.local",
        full_name="Trần Gia Hân",
        profile_note="Ưu tiên địa điểm dễ đi lại, phù hợp trẻ nhỏ và có phương án dự phòng thời tiết.",
        phone="0901000002",
        home_address="Khu dân cư Hiệp Bình, Thành phố Hồ Chí Minh",
        birth_date=date(1991, 8, 24),
        gender="Nữ",
    ),
    FixtureUserSpec(
        username="test_luxury",
        email="test_luxury@vivu.local",
        full_name="Lê Quốc Bảo",
        profile_note="Ưa nghỉ dưỡng chất lượng cao, chú trọng khách sạn, ẩm thực và nhịp lịch trình thư thả.",
        phone="0901000003",
        home_address="Khu đô thị Sala, Thành phố Hồ Chí Minh",
        birth_date=date(1988, 12, 9),
        gender="Nam",
    ),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Seed fixture liên kết cho backend test suite của Vi Vu."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Thực thi ghi dữ liệu vào cơ sở dữ liệu. Nếu bỏ qua, script chỉ kiểm tra điều kiện seed.",
    )
    return parser.parse_args()


def ensure(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def resolve_province(keyword: str) -> TinhThanh:
    province = (
        TinhThanh.objects.filter(tenTinhThanh__iexact=keyword).first()
        or TinhThanh.objects.filter(tenTinhThanh__icontains=keyword).order_by("maTinhThanh").first()
    )
    if not province:
        raise RuntimeError(f"Không tìm thấy tỉnh/thành chứa từ khóa '{keyword}'.")
    return province


def pick_active_places(
    province: TinhThanh,
    *,
    limit: int,
    preferred_terms: Optional[Sequence[str]] = None,
) -> List[DiaDiem]:
    preferred_terms = preferred_terms or ()
    base_qs = DiaDiem.objects.filter(maTinhThanh=province, trangThai="active").order_by(
        "-danhGiaTrungBinh",
        "-soLuotDanhGia",
        "maDiaDiem",
    )
    selected: List[DiaDiem] = []
    seen_ids = set()

    for term in preferred_terms:
        for place in base_qs.filter(diaChi__icontains=term)[:limit]:
            if place.maDiaDiem not in seen_ids:
                selected.append(place)
                seen_ids.add(place.maDiaDiem)
            if len(selected) >= limit:
                return selected

    for place in base_qs[: limit * 3]:
        if place.maDiaDiem not in seen_ids:
            selected.append(place)
            seen_ids.add(place.maDiaDiem)
        if len(selected) >= limit:
            return selected

    raise RuntimeError(
        f"Không đủ địa điểm active ở {province.tenTinhThanh}. Cần {limit}, hiện có {len(selected)}."
    )


def upsert_single(model, lookup: Dict[str, Any], defaults: Dict[str, Any]):
    instance = model.objects.filter(**lookup).order_by("pk").first()
    if instance:
        changed = False
        for field, value in defaults.items():
            if getattr(instance, field) != value:
                setattr(instance, field, value)
                changed = True
        if changed:
            instance.save()
        return instance, False
    return model.objects.create(**lookup, **defaults), True


def ensure_user(spec: FixtureUserSpec) -> Tuple[NguoiDung, bool]:
    user, created = NguoiDung.objects.get_or_create(
        username=spec.username,
        defaults={
            "email": spec.email,
            "hoTen": spec.full_name,
            "soDienThoai": spec.phone,
            "diaChi": spec.home_address,
            "ngaySinh": spec.birth_date,
            "gioiTinh": spec.gender,
            "vaiTro": "user",
            "trangThai": "active",
            "is_active": True,
        },
    )

    changed = created
    user.email = spec.email
    user.hoTen = spec.full_name
    user.soDienThoai = spec.phone
    user.diaChi = spec.home_address
    user.ngaySinh = spec.birth_date
    user.gioiTinh = spec.gender
    user.vaiTro = "user"
    user.trangThai = "active"
    user.is_active = True
    if created or not user.check_password(DEFAULT_PASSWORD):
        user.set_password(DEFAULT_PASSWORD)
        changed = True

    if changed:
        user.save()
    return user, created


def build_full_plan_output(
    *,
    theme_name: str,
    dates: Sequence[date],
    places_by_day: Sequence[Sequence[DiaDiem]],
    transport_modes: Sequence[Sequence[str]],
    total_cost: int,
    fitness_level: str,
) -> Dict[str, Any]:
    daily_itinerary: List[Dict[str, Any]] = []
    estimated_distance = 0.0

    for day_index, current_date in enumerate(dates):
        places = list(places_by_day[day_index])
        modes = list(transport_modes[day_index])
        route_flow = [str(place.maDiaDiem) for place in places]
        timeline: List[Dict[str, Any]] = []
        start_hour = 8

        for visit_index, place in enumerate(places):
            next_mode = modes[visit_index] if visit_index < len(modes) else "Đi bộ"
            duration_minutes = 20 if next_mode == "Đi bộ" else 35
            distance_km = 1.2 if next_mode == "Đi bộ" else 6.5
            estimated_distance += distance_km

            start_time = f"{start_hour + visit_index * 3:02d}:00"
            end_time = f"{start_hour + visit_index * 3 + 2:02d}:00"
            timeline.append(
                {
                    "time_start": start_time,
                    "time_end": end_time,
                    "place_id": str(place.maDiaDiem),
                    "activity_name": place.tenDiaDiem,
                    "cost": int(place.giaVe or 0),
                    "transport_to_next": {
                        "mode": next_mode,
                        "duration_mins": duration_minutes,
                        "distance_km": round(distance_km, 1),
                    },
                    "local_hint": (
                        f"Ưu tiên khung giờ mát, mang theo nước cá nhân và giữ nguyên nhịp "
                        f"tham quan phù hợp tại {place.maTinhThanh.tenTinhThanh}."
                    ),
                    "plan_b_fallback": {
                        "place_id": str(place.maDiaDiem),
                        "name": f"Phương án trong nhà gần {place.tenDiaDiem}",
                        "reason": "Kích hoạt khi trời mưa lớn hoặc nhóm cần nghỉ ngắn giữa hành trình.",
                    },
                }
            )

        daily_itinerary.append(
            {
                "day": day_index + 1,
                "date": current_date.isoformat(),
                "theme": f"{theme_name} - ngày {day_index + 1}",
                "route_flow": route_flow,
                "timeline": timeline,
            }
        )

    return {
        "trip_overview": {
            "total_distance_km": round(estimated_distance, 1),
            "total_estimated_cost": int(total_cost),
            "fitness_level_required": fitness_level,
        },
        "daily_itinerary": daily_itinerary,
        "budget_analytics": {
            "accommodation_total": int(total_cost * 0.35),
            "transportation_total": int(total_cost * 0.2),
            "food_total": int(total_cost * 0.2),
            "activities_total": int(total_cost * 0.15),
            "emergency_buffer": int(total_cost * 0.1),
        },
        "packing_checklist": {
            "documents": [
                "Căn cước công dân hoặc giấy tờ tùy thân còn hiệu lực",
                "Xác nhận đặt phòng và vé di chuyển điện tử",
            ],
            "clothing": [
                "Trang phục thoải mái, giày đi bộ chống trơn",
                "Áo khoác mỏng và đồ dự phòng cho buổi tối",
            ],
            "medical": [
                "Thuốc cá nhân, băng cá nhân và kem chống côn trùng",
                "Dung dịch bù nước và khẩu trang dự phòng",
            ],
        },
    }


def seed_search_history(user: NguoiDung, entries: Sequence[Dict[str, Any]]) -> int:
    created_count = 0
    for entry in entries:
        lookup = {
            "maNguoiDung": user,
            "tuKhoa": entry["tu_khoa"],
            "maDiaDiem": entry["place"],
        }
        _, created = upsert_single(
            LichSuTimKiem,
            lookup=lookup,
            defaults={
                "soKetQua": entry["so_ket_qua"],
            },
        )
        created_count += int(created)
    return created_count


def seed_favorites(user: NguoiDung, entries: Sequence[Dict[str, Any]]) -> int:
    created_count = 0
    for entry in entries:
        _, created = DiaDiemYeuThich.objects.get_or_create(
            maNguoiDung=user,
            maDiaDiem=entry["place"],
            defaults={"ghiChu": entry["ghi_chu"]},
        )
        if not created:
            favorite = DiaDiemYeuThich.objects.get(maNguoiDung=user, maDiaDiem=entry["place"])
            if favorite.ghiChu != entry["ghi_chu"]:
                favorite.ghiChu = entry["ghi_chu"]
                favorite.save(update_fields=["ghiChu"])
        created_count += int(created)
    return created_count


def seed_reviews(entries: Sequence[Dict[str, Any]]) -> int:
    created_count = 0
    for entry in entries:
        _, created = DanhGia.objects.get_or_create(
            maDiaDiem=entry["place"],
            maNguoiDung=entry["user"],
            defaults={
                "diemDanhGia": entry["rating"],
                "tieuDe": entry["title"],
                "noiDung": entry["content"],
                "soLuotThich": entry["likes"],
                "trangThai": "active",
            },
        )
        if not created:
            review = DanhGia.objects.get(maDiaDiem=entry["place"], maNguoiDung=entry["user"])
            review.diemDanhGia = entry["rating"]
            review.tieuDe = entry["title"]
            review.noiDung = entry["content"]
            review.soLuotThich = entry["likes"]
            review.trangThai = "active"
            review.save()
        created_count += int(created)
    return created_count


def seed_contributions(entries: Sequence[Dict[str, Any]]) -> int:
    created_count = 0
    for entry in entries:
        lookup = {
            "maNguoiDung": entry["user"],
            "maDiaDiem": entry["place"],
            "loaiDongGop": entry["loai"],
        }
        defaults = {
            "noiDung": entry["noi_dung"],
            "duLieuBoSung": entry.get("du_lieu_bo_sung"),
            "trangThai": entry["trang_thai"],
            "phanHoi": entry["phan_hoi"],
            "ngayXuLy": entry["ngay_xu_ly"],
        }
        _, created = upsert_single(DongGop, lookup=lookup, defaults=defaults)
        created_count += int(created)
    return created_count


def seed_analytics(entries: Sequence[Dict[str, Any]]) -> int:
    created_count = 0
    for index, entry in enumerate(entries, start=1):
        lookup = {
            "maNguoiDung": entry["user"],
            "diemDi": entry["diem_di"],
            "diemDen": entry["diem_den"],
            "loaiYeuCau": entry["loai"],
        }
        defaults = {
            "maTinhThanhDiemDi": entry["province_origin"],
            "maTinhThanhDiemDen": entry["province_destination"],
            "ngayKhoiHanhDuKien": entry["ngay_khoi_hanh"],
            "soNgayDi": entry["so_ngay"],
            "soNguoi": entry["so_nguoi"],
            "nganSachDuKien": entry["ngan_sach"],
            "trangThai": entry["trang_thai"],
            "duLieuPhanHoi": {
                "fixture_marker": FIXTURE_MARKER,
                "fixture_slot": index,
                "workflow": entry["workflow"],
                "thread_id": entry["thread_id"],
                "note": entry["note"],
            },
        }
        record, created = upsert_single(YeuCauLoTrinh, lookup=lookup, defaults=defaults)
        YeuCauLoTrinh.objects.filter(pk=record.pk).update(
            ngayTao=entry["timestamp"],
            lanCapNhatCuoi=entry["timestamp"],
        )
        created_count += int(created)
    return created_count


def seed_itinerary(
    *,
    user: NguoiDung,
    province: TinhThanh,
    title: str,
    description: str,
    plan_payload: Dict[str, Any],
    starts_at: date,
    travelers: int,
    budget: int,
    is_public: bool,
    is_ai_generated: bool = False,
) -> Tuple[LichTrinh, bool]:
    days = len(plan_payload["daily_itinerary"])
    itinerary, created = upsert_single(
        LichTrinh,
        lookup={
            "maNguoiDung": user,
            "tieuDe": title,
        },
        defaults={
            "maTinhThanh": province,
            "moTa": description,
            "ngayBatDau": starts_at,
            "ngayKetThuc": starts_at + timedelta(days=days - 1),
            "soNgay": days,
            "soNguoi": travelers,
            "nganSach": float(budget),
            "chiPhiUocTinh": float(plan_payload["trip_overview"]["total_estimated_cost"]),
            "trangThai": "published",
            "laCongKhai": is_public,
            "is_ai_generated": is_ai_generated,
            "soLuotXem": 48 if is_public else 12,
            "soLuotThich": 9 if is_public else 3,
            "chiTiet": json.dumps(plan_payload, ensure_ascii=False),
        },
    )

    for day in plan_payload["daily_itinerary"]:
        visit_date = datetime.strptime(day["date"], "%Y-%m-%d").date()
        for order, timeline_item in enumerate(day["timeline"], start=1):
            place = DiaDiem.objects.get(maDiaDiem=int(timeline_item["place_id"]))
            LichTrinhDiaDiem.objects.update_or_create(
                maLichTrinh=itinerary,
                maDiaDiem=place,
                ngayThamQuan=visit_date,
                defaults={
                    "thoiGianThamQuan": f"{timeline_item['time_start']}-{timeline_item['time_end']}",
                    "thuTu": order,
                    "ghiChu": (
                        f"{FIXTURE_MARKER}: chặng ngày {day['day']} cho '{title}' "
                        f"theo nhịp đi {timeline_item['transport_to_next']['mode'].lower()}."
                    ),
                    "chiPhiUocTinh": float(timeline_item["cost"]),
                },
            )
    return itinerary, created


def build_seed_payload() -> Dict[str, Any]:
    dong_nai = resolve_province("Đồng Nai")
    ho_chi_minh = resolve_province("Hồ Chí Minh")
    ha_noi = resolve_province("Hà Nội")

    dong_nai_places = pick_active_places(
        dong_nai,
        limit=8,
        preferred_terms=("Biên Hòa", "Long Khánh", "Long Thành"),
    )
    hcm_places = pick_active_places(
        ho_chi_minh,
        limit=4,
        preferred_terms=("Quận 1", "Thủ Đức", "Quận 3"),
    )

    family_dates = [date(2026, 6, 14), date(2026, 6, 15)]
    family_plan = build_full_plan_output(
        theme_name="Gia đình thư giãn ở Đồng Nai",
        dates=family_dates,
        places_by_day=(
            dong_nai_places[:3],
            dong_nai_places[3:6],
        ),
        transport_modes=(
            ("Taxi", "Đi bộ", "Taxi"),
            ("Taxi", "Đi bộ", "Taxi"),
        ),
        total_cost=6_800_000,
        fitness_level="Thấp",
    )

    luxury_dates = [date(2026, 7, 5), date(2026, 7, 6)]
    luxury_plan = build_full_plan_output(
        theme_name="Nghỉ dưỡng nhịp chậm tại Đồng Nai",
        dates=luxury_dates,
        places_by_day=(
            (dong_nai_places[0], dong_nai_places[1], dong_nai_places[6]),
            (dong_nai_places[2], dong_nai_places[4], dong_nai_places[7]),
        ),
        transport_modes=(
            ("Xe riêng", "Taxi", "Đi bộ"),
            ("Xe riêng", "Taxi", "Đi bộ"),
        ),
        total_cost=11_500_000,
        fitness_level="Trung bình",
    )

    return {
        "provinces": {
            "dong_nai": dong_nai,
            "ho_chi_minh": ho_chi_minh,
            "ha_noi": ha_noi,
        },
        "places": {
            "dong_nai": dong_nai_places,
            "ho_chi_minh": hcm_places,
        },
        "plans": {
            "family": family_plan,
            "luxury": luxury_plan,
        },
    }


def apply_seed() -> Dict[str, int]:
    payload = build_seed_payload()
    provinces = payload["provinces"]
    places = payload["places"]

    summary = {
        "users_created": 0,
        "searches_created": 0,
        "favorites_created": 0,
        "reviews_created": 0,
        "itineraries_created": 0,
        "ai_generated_itineraries_created": 0,
        "contributions_created": 0,
        "analytics_created": 0,
    }

    users: Dict[str, NguoiDung] = {}
    for spec in USER_SPECS:
        user, created = ensure_user(spec)
        users[spec.username] = user
        summary["users_created"] += int(created)

    summary["searches_created"] += seed_search_history(
        users["test_backpacker"],
        (
            {
                "tu_khoa": "quán ăn tối ở Thành phố Biên Hòa, Tỉnh Đồng Nai",
                "place": places["dong_nai"][1],
                "so_ket_qua": 6,
            },
            {
                "tu_khoa": "điểm dừng chân gần Thành phố Long Khánh, Tỉnh Đồng Nai",
                "place": places["dong_nai"][4],
                "so_ket_qua": 4,
            },
        ),
    )
    summary["searches_created"] += seed_search_history(
        users["test_family"],
        (
            {
                "tu_khoa": "khách sạn gia đình ở Thành phố Biên Hòa, Tỉnh Đồng Nai",
                "place": places["dong_nai"][0],
                "so_ket_qua": 8,
            },
            {
                "tu_khoa": "địa điểm đi cùng trẻ nhỏ tại Tỉnh Đồng Nai",
                "place": places["dong_nai"][6],
                "so_ket_qua": 5,
            },
        ),
    )
    summary["searches_created"] += seed_search_history(
        users["test_luxury"],
        (
            {
                "tu_khoa": "lưu trú cao cấp gần Thành phố Long Khánh, Tỉnh Đồng Nai",
                "place": places["dong_nai"][3],
                "so_ket_qua": 7,
            },
            {
                "tu_khoa": "điểm hẹn ăn tối riêng tư từ Thành phố Hồ Chí Minh đến Đồng Nai",
                "place": places["dong_nai"][2],
                "so_ket_qua": 3,
            },
        ),
    )

    summary["favorites_created"] += seed_favorites(
        users["test_backpacker"],
        (
            {
                "place": places["dong_nai"][1],
                "ghi_chu": "Ưu tiên điểm ăn uống dễ ghé khi chạy cung Biên Hòa - Long Khánh.",
            },
            {
                "place": places["dong_nai"][4],
                "ghi_chu": "Điểm dừng phù hợp buổi chiều, có thể gắn vào hành trình khám phá Đồng Nai.",
            },
        ),
    )
    summary["favorites_created"] += seed_favorites(
        users["test_family"],
        (
            {
                "place": places["dong_nai"][0],
                "ghi_chu": "Chọn vì thuận tiện nghỉ ngơi cho gia đình tại Tỉnh Đồng Nai.",
            },
            {
                "place": places["dong_nai"][6],
                "ghi_chu": "Điểm phù hợp cho buổi tham quan ngắn, di chuyển nhẹ nhàng.",
            },
        ),
    )
    summary["favorites_created"] += seed_favorites(
        users["test_luxury"],
        (
            {
                "place": places["dong_nai"][3],
                "ghi_chu": "Giữ lại để kiểm tra flow gợi ý lưu trú và bữa tối chất lượng cao.",
            },
            {
                "place": places["ho_chi_minh"][0],
                "ghi_chu": "Điểm neo khởi hành khi tạo hành trình từ Thành phố Hồ Chí Minh.",
            },
        ),
    )

    summary["reviews_created"] += seed_reviews(
        (
            {
                "user": users["test_backpacker"],
                "place": places["dong_nai"][1],
                "rating": 4,
                "title": "Điểm dừng ăn tối ổn định",
                "content": "Không gian dễ vào, món lên nhanh và phù hợp khi cần một chặng nghỉ gọn trên hành trình ở Đồng Nai.",
                "likes": 5,
            },
            {
                "user": users["test_family"],
                "place": places["dong_nai"][0],
                "rating": 5,
                "title": "Phù hợp cho gia đình nghỉ cuối tuần",
                "content": "Phòng sạch, di chuyển thuận tiện trong Thành phố Biên Hòa và dễ xoay lịch khi đi cùng trẻ nhỏ.",
                "likes": 8,
            },
            {
                "user": users["test_luxury"],
                "place": places["dong_nai"][3],
                "rating": 5,
                "title": "Dịch vụ ổn và nhịp nghỉ dưỡng dễ chịu",
                "content": "Không gian riêng tư hơn mong đợi, đủ tốt để dùng làm fixture cho các trường hợp lọc theo đánh giá cao.",
                "likes": 11,
            },
            {
                "user": users["test_backpacker"],
                "place": places["dong_nai"][6],
                "rating": 3,
                "title": "Ghép lịch ngắn khá ổn",
                "content": "Phù hợp cho chặng mua sắm hoặc nghỉ chân nhanh, chưa phải điểm nhấn nhưng đủ hữu ích trong itinerary kiểm thử.",
                "likes": 2,
            },
        )
    )

    family_itinerary, family_created = seed_itinerary(
        user=users["test_family"],
        province=provinces["dong_nai"],
        title="Cuối tuần gia đình ở Tỉnh Đồng Nai",
        description=(
            "Hành trình mẫu cho gia đình với nhịp di chuyển nhẹ, bám đúng địa chỉ "
            "Thành phố Biên Hòa và Tỉnh Đồng Nai để phục vụ kiểm thử lưu lịch trình."
        ),
        plan_payload=payload["plans"]["family"],
        starts_at=date(2026, 6, 14),
        travelers=4,
        budget=7_200_000,
        is_public=False,
    )
    summary["itineraries_created"] += int(family_created)

    luxury_itinerary, luxury_created = seed_itinerary(
        user=users["test_luxury"],
        province=provinces["dong_nai"],
        title="Nghỉ dưỡng hai ngày tại Tỉnh Đồng Nai",
        description=(
            "Lịch trình mẫu thiên về lưu trú và ẩm thực, dùng để test persistence và "
            "các payload FullTravelPlanOutput trong khu vực Đồng Nai."
        ),
        plan_payload=payload["plans"]["luxury"],
        starts_at=date(2026, 7, 5),
        travelers=2,
        budget=12_500_000,
        is_public=True,
    )
    summary["itineraries_created"] += int(luxury_created)

    _, family_ai_created = seed_itinerary(
        user=users["test_family"],
        province=provinces["dong_nai"],
        title="AI gợi ý gia đình tại Tỉnh Đồng Nai",
        description="Bản lịch trình AI hợp nhất vào bảng LICHTRINH để kiểm thử cờ is_ai_generated.",
        plan_payload=payload["plans"]["family"],
        starts_at=date(2026, 6, 14),
        travelers=4,
        budget=7_200_000,
        is_public=False,
        is_ai_generated=True,
    )
    summary["ai_generated_itineraries_created"] += int(family_ai_created)

    _, luxury_ai_created = seed_itinerary(
        user=users["test_luxury"],
        province=provinces["dong_nai"],
        title="AI gợi ý nghỉ dưỡng tại Tỉnh Đồng Nai",
        description="Bản AI dùng để so khớp payload Pydantic và kiểm tra mapping ngày giờ trên hành trình cao cấp.",
        plan_payload=payload["plans"]["luxury"],
        starts_at=date(2026, 7, 5),
        travelers=2,
        budget=12_500_000,
        is_public=False,
        is_ai_generated=True,
    )
    summary["ai_generated_itineraries_created"] += int(luxury_ai_created)

    summary["contributions_created"] += seed_contributions(
        (
            {
                "user": users["test_backpacker"],
                "place": places["dong_nai"][4],
                "loai": "SUA_DOI_POI",
                "noi_dung": (
                    "Đề nghị chuẩn hóa mô tả địa chỉ để luôn hiển thị 'Tỉnh Đồng Nai' "
                    "ở cuối chuỗi khi xuất sang telemetry."
                ),
                "du_lieu_bo_sung": {
                    "truong_cap_nhat": ["dia_chi", "telemetry"],
                    "de_xuat": {"dia_chi_chuan_hoa": "..., Tỉnh Đồng Nai"},
                },
                "trang_thai": "approved",
                "phan_hoi": "Đã ghi nhận cho bộ dữ liệu kiểm thử nội bộ.",
                "ngay_xu_ly": timezone.now(),
            },
            {
                "user": users["test_family"],
                "place": places["dong_nai"][0],
                "loai": "BAO_CAO_LOI",
                "noi_dung": "Kiểm tra lại ghi chú tiện nghi để giao diện gia đình có thể đọc nhanh hơn trong màn hình xác nhận.",
                "du_lieu_bo_sung": {
                    "muc_do_uu_tien": "trung_binh",
                    "nguon": "fixture",
                },
                "trang_thai": "pending",
                "phan_hoi": "",
                "ngay_xu_ly": None,
            },
        )
    )

    now = timezone.now()
    summary["analytics_created"] += seed_analytics(
        (
            {
                "user": users["test_backpacker"],
                "province_origin": provinces["ho_chi_minh"],
                "province_destination": provinces["dong_nai"],
                "diem_di": "Thành phố Hồ Chí Minh",
                "diem_den": "Tỉnh Đồng Nai",
                "ngay_khoi_hanh": date(2026, 6, 14),
                "so_ngay": 2,
                "so_nguoi": 2,
                "ngan_sach": 4_500_000,
                "loai": YeuCauLoTrinh.LoaiYeuCau.BUOC_4,
                "trang_thai": YeuCauLoTrinh.TrangThaiXuLy.THANH_CONG,
                "workflow": "four_step_streaming",
                "thread_id": "fixture-rate-limit-01",
                "note": "Dấu chân mẫu thứ nhất cho cửa sổ 10 phút.",
                "timestamp": now - timedelta(minutes=8),
            },
            {
                "user": users["test_backpacker"],
                "province_origin": provinces["ho_chi_minh"],
                "province_destination": provinces["dong_nai"],
                "diem_di": "Thành phố Hồ Chí Minh",
                "diem_den": "Tỉnh Đồng Nai",
                "ngay_khoi_hanh": date(2026, 6, 21),
                "so_ngay": 2,
                "so_nguoi": 2,
                "ngan_sach": 4_800_000,
                "loai": YeuCauLoTrinh.LoaiYeuCau.TAO_KE_HOACH,
                "trang_thai": YeuCauLoTrinh.TrangThaiXuLy.THANH_CONG,
                "workflow": "langgraph_streaming",
                "thread_id": "fixture-rate-limit-02",
                "note": "Dấu chân mẫu thứ hai cho cửa sổ 10 phút.",
                "timestamp": now - timedelta(minutes=4),
            },
            {
                "user": users["test_backpacker"],
                "province_origin": provinces["ha_noi"],
                "province_destination": provinces["dong_nai"],
                "diem_di": "Thành phố Hà Nội",
                "diem_den": "Tỉnh Đồng Nai",
                "ngay_khoi_hanh": date(2026, 7, 5),
                "so_ngay": 2,
                "so_nguoi": 1,
                "ngan_sach": 8_200_000,
                "loai": YeuCauLoTrinh.LoaiYeuCau.PREVIEW,
                "trang_thai": YeuCauLoTrinh.TrangThaiXuLy.TU_CACHE,
                "workflow": "preview_rate_limit_probe",
                "thread_id": "fixture-rate-limit-03",
                "note": "Dấu chân mẫu thứ ba để kiểm tra ngưỡng 3 yêu cầu trong 10 phút.",
                "timestamp": now - timedelta(minutes=1),
            },
        )
    )

    return summary


def main() -> int:
    args = parse_args()

    build_seed_payload()
    if not args.apply:
        print(
            "Seed script đã kiểm tra xong điều kiện dữ liệu nguồn. "
            "Chạy lại với --apply để ghi fixture vào cơ sở dữ liệu."
        )
        return 0

    with transaction.atomic():
        summary = apply_seed()

    print("Đã seed xong fixture backend.")
    for key, value in summary.items():
        print(f"- {key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
