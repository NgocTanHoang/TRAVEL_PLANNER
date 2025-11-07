#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script để thêm ảnh cho La Siesta Premium Saigon Central
"""
import os
import sys
import django
import json
from pathlib import Path

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Setup Django
PROJECT_ROOT = Path(__file__).resolve().parent.parent  # Go up from scripts/ to TRAVEL_PLANNER/
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'vivu_backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vivu_core.settings')
django.setup()

from apps.places.models import DiaDiem, TinhThanh, HinhAnhDiaDiem

def add_la_siesta_image():
    """Thêm ảnh cho La Siesta Premium Saigon Central"""
    
    image_url = "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/2e/09/ac/22/hotel-facade.jpg?w=1400&h=-1&s=1"
    
    # Tìm La Siesta Premium Saigon Central
    place_names = [
        "La Siesta Premium Saigon Central",
        "La Siesta Premium",
        "La Siesta Saigon",
        "La Siesta",
    ]
    
    place = None
    for name in place_names:
        place = DiaDiem.objects.filter(tenDiaDiem__icontains=name).first()
        if place:
            print(f"[OK] Tìm thấy địa điểm: {place.tenDiaDiem} (ID: {place.maDiaDiem})")
            break
    
    if not place:
        print("[ERROR] Không tìm thấy La Siesta Premium Saigon Central trong database!")
        print("[INFO] Đang tìm kiếm các khách sạn tại Ho Chi Minh City...")
        hcm = TinhThanh.objects.filter(tenTinhThanh__icontains="Ho Chi Minh").first()
        if hcm:
            hotels = DiaDiem.objects.filter(
                maTinhThanh=hcm,
                loaiDiaDiem='khach_san',
                tenDiaDiem__icontains="Siesta"
            )
            print(f"[INFO] Tìm thấy {hotels.count()} khách sạn có chứa 'Siesta':")
            for hotel in hotels:
                print(f"  - {hotel.tenDiaDiem} (ID: {hotel.maDiaDiem})")
        return
    
    # Kiểm tra xem đã có ảnh chưa
    existing_image = place.hinh_anhs.filter(urlHinhAnh=image_url).first()
    if existing_image:
        print(f"[INFO] Ảnh đã tồn tại: {image_url}")
        if not existing_image.laChinh:
            existing_image.laChinh = True
            existing_image.save()
            print("[OK] Đã đặt làm ảnh chính")
        return
    
    # Kiểm tra xem đã có ảnh chính chưa
    main_image = place.hinh_anhs.filter(laChinh=True).first()
    
    # Thêm ảnh mới - thử với Django ORM đơn giản
    try:
        # Tắt foreign key checks tạm thời cho SQLite
        from django.db import connection
        
        with connection.cursor() as cursor:
            # Tắt foreign key checks
            cursor.execute("PRAGMA foreign_keys = OFF")
            
            try:
                new_image = HinhAnhDiaDiem(
                    maDiaDiem=place,
                    urlHinhAnh=image_url,
                    laChinh=not main_image,
                    moTa="Hình ảnh ngoại thất La Siesta Premium Saigon Central"
                )
                new_image.save()
                print(f"[OK] Đã thêm ảnh: {image_url}")
                if new_image.laChinh:
                    print("[OK] Đã đặt làm ảnh chính")
            finally:
                # Bật lại foreign key checks
                cursor.execute("PRAGMA foreign_keys = ON")
                
    except Exception as e:
        print(f"[ERROR] Không thể thêm ảnh: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Cập nhật dacDiem JSON nếu có
    try:
        dac_diem = json.loads(place.dacDiem) if place.dacDiem else {}
        if isinstance(dac_diem, dict):
            dac_diem['image_url'] = image_url
            place.dacDiem = json.dumps(dac_diem, ensure_ascii=False)
            place.save(update_fields=['dacDiem'])
            print("[OK] Đã cập nhật dacDiem với image_url")
    except Exception as e:
        print(f"[WARN] Không thể cập nhật dacDiem: {e}")

if __name__ == '__main__':
    print("="*60)
    print("Thêm ảnh cho La Siesta Premium Saigon Central")
    print("="*60)
    add_la_siesta_image()
    print("="*60)

