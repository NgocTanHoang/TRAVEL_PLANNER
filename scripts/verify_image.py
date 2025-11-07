#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script để kiểm tra xem ảnh đã được thêm chưa
"""
import os
import sys
import django
from pathlib import Path

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Setup Django
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'vivu_backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vivu_core.settings')
django.setup()

from apps.places.models import DiaDiem, HinhAnhDiaDiem

image_url = "https://dynamic-media-cdn.tripadvisor.com/media/photo-o/0f/4a/6a/7d/exterior.jpg?w=1800&h=-1&s=1"

place = DiaDiem.objects.filter(tenDiaDiem__icontains="Park Hyatt Saigon").first()
if place:
    print(f"Địa điểm: {place.tenDiaDiem} (ID: {place.maDiaDiem})")
    images = place.hinh_anhs.all()
    print(f"Số lượng ảnh: {images.count()}")
    for img in images:
        print(f"  - {img.urlHinhAnh} (Chính: {img.laChinh})")
    
    # Kiểm tra ảnh cụ thể
    target_image = place.hinh_anhs.filter(urlHinhAnh=image_url).first()
    if target_image:
        print(f"\n[OK] Ảnh đã tồn tại trong database!")
        print(f"    URL: {target_image.urlHinhAnh}")
        print(f"    Là ảnh chính: {target_image.laChinh}")
    else:
        print(f"\n[INFO] Ảnh chưa có trong database")
else:
    print("[ERROR] Không tìm thấy Park Hyatt Saigon")

