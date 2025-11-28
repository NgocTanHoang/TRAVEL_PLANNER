"""Seed sample favourites, reviews, and itinerary-place links for demo purposes."""
from __future__ import annotations

import os
import sys
from pathlib import Path

from django.utils import timezone
from django.db import transaction, IntegrityError


# Bootstrap Django environment when running as standalone script
ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR / "vivu_backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "vivu_core.settings")

import django

django.setup()

from datetime import timedelta

from apps.users.models import NguoiDung
from apps.places.models import DiaDiem, DiaDiemYeuThich, DanhGia, TinhThanh
from apps.itineraries.models import LichTrinh, LichTrinhDiaDiem


def ensure_seed_entities():
    user, created_user = NguoiDung.objects.get_or_create(
        username='seed_demo',
        defaults={
            'email': 'seed_demo@example.com',
            'hoTen': 'Seed Demo User',
            'soDienThoai': '0900000000',
            'vaiTro': 'user',
            'trangThai': 'active',
        }
    )
    if created_user:
        user.set_password('seed_demo_password')
        user.save(update_fields=['password'])

    province = TinhThanh.objects.order_by('maTinhThanh').first()
    if not province:
        raise RuntimeError('No provinces found. Please seed TINHTHANH first.')

    def ensure_place(index: int, lat: float, lng: float) -> DiaDiem:
        defaults = {
            'moTa': 'Dia diem mau cho seed du lieu.',
            'diaChi': f'{index} Demo Street, Viet Nam',
            'maTinhThanh': province,
            'loaiDiaDiem': 'dia_danh',
            'viDo': lat,
            'kinhDo': lng,
            'giaVe': 100000 + index * 50000,
            'gioMoCua': '08:00',
            'gioDongCua': '20:00',
            'dienThoai': '0281234567',
            'website': f'https://example.com/seed-demo-place-{index}',
            'trangThai': 'active',
            'dacDiem': '{}',
            'tienNghi': '{}',
        }
        place, _ = DiaDiem.objects.get_or_create(
            tenDiaDiem=f'Seed Demo Place {index}',
            defaults=defaults,
        )
        return place

    places = [
        ensure_place(1, 10.762622, 106.660172),
        ensure_place(2, 16.054407, 108.202167),
        ensure_place(3, 21.027764, 105.83416),
    ]

    start_date = timezone.now().date()
    itinerary, _ = LichTrinh.objects.get_or_create(
        maNguoiDung=user,
        tieuDe='Seed Demo Itinerary',
        defaults={
            'moTa': 'Lich trinh mau cho seed du lieu.',
            'ngayBatDau': start_date,
            'ngayKetThuc': start_date + timedelta(days=2),
            'soNgay': 3,
            'soNguoi': 2,
            'nganSach': 5000000,
            'chiPhiUocTinh': 4200000,
            'trangThai': 'draft',
            'laCongKhai': False,
        }
    )

    return user, itinerary, places


def main() -> None:
    try:
        user, itinerary, places = ensure_seed_entities()
    except RuntimeError as exc:
        print(f"[WARN] {exc}")
        return

    visit_start = itinerary.ngayBatDau or timezone.now().date()

    created_favorites = 0
    created_reviews = 0

    for place in places:
        try:
            with transaction.atomic():
                _, fav_created = DiaDiemYeuThich.objects.get_or_create(
                    maNguoiDung=user,
                    maDiaDiem=place,
                    defaults={'ghiChu': 'Seed data: favorite place sample'}
                )
                created_favorites += int(fav_created)
        except IntegrityError as exc:
            print(
                "[WARN] FK error when creating favorite",
                {
                    "place_id": place.pk,
                    "user_id": user.pk,
                    "error": str(exc),
                }
            )

        try:
            with transaction.atomic():
                _, review_created = DanhGia.objects.get_or_create(
                    maDiaDiem=place,
                    maNguoiDung=user,
                    defaults={
                        'diemDanhGia': 5,
                        'tieuDe': 'Trai nghiem tuyet voi',
                        'noiDung': 'Du lieu seed: review mau cho demo.',
                        'soLuotThich': 0,
                        'trangThai': 'active'
                    }
                )
                created_reviews += int(review_created)
        except IntegrityError as exc:
            print(
                "[WARN] FK error when creating review",
                {
                    "place_id": place.pk,
                    "user_id": user.pk,
                    "error": str(exc),
                }
            )

    created_itinerary_links = 0

    for index, place in enumerate(places, start=1):
        try:
            with transaction.atomic():
                _, link_created = LichTrinhDiaDiem.objects.get_or_create(
                    maLichTrinh=itinerary,
                    maDiaDiem=place,
                    ngayThamQuan=visit_start + timedelta(days=index - 1),
                    defaults={
                        'thoiGianThamQuan': '09:00-12:00',
                        'thuTu': index,
                        'ghiChu': 'Seed data: lich trinh mau',
                        'chiPhiUocTinh': 200_000,
                    }
                )
                created_itinerary_links += int(link_created)
        except IntegrityError as exc:
            print(
                "[WARN] FK error when creating itinerary link",
                {
                    "place_id": place.pk,
                    "itinerary_id": itinerary.pk,
                    "error": str(exc),
                }
            )

    print("[OK] Seed sample data completed:")
    print(f"  Nguoi dung: {user.tenDangNhap}")
    print(f"  Dia diem: {[place.tenDiaDiem for place in places]}")
    print(f"  Yeu thich moi: {created_favorites}")
    print(f"  Danh gia moi: {created_reviews}")
    if itinerary:
        print(f"  Lich trinh: {itinerary.tieuDe} (lien ket moi: {created_itinerary_links})")
    else:
        print("  Khong tim thay lich trinh de lien ket (bo qua buoc nay).")


if __name__ == '__main__':
    main()
