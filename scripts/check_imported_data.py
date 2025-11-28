#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script kiểm tra dữ liệu đã import"""
import os
import sys
import django
from pathlib import Path

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Setup Django
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'vivu_backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vivu_core.settings')
django.setup()

from apps.places.models import DiaDiem, TinhThanh
from django.db.models import Count

print("="*80)
print("KIỂM TRA DỮ LIỆU ĐÃ IMPORT")
print("="*80)

print(f"\nTổng số địa điểm: {DiaDiem.objects.count()}")
print(f"Tổng số tỉnh thành: {TinhThanh.objects.count()}")

print("\nPhân loại theo loaiDiaDiem:")
for item in DiaDiem.objects.values('loaiDiaDiem').annotate(count=Count('loaiDiaDiem')).order_by('-count'):
    print(f"  {item['loaiDiaDiem']}: {item['count']}")

print("\nTop 10 tỉnh thành có nhiều địa điểm nhất:")
for item in DiaDiem.objects.values('maTinhThanh__tenTinhThanh').annotate(count=Count('maDiaDiem')).order_by('-count')[:10]:
    print(f"  {item['maTinhThanh__tenTinhThanh']}: {item['count']}")

print("\nMẫu dữ liệu đã import (5 địa điểm đầu tiên):")
for d in DiaDiem.objects.all()[:5]:
    print(f"\n- {d.tenDiaDiem}")
    print(f"  Loại: {d.loaiDiaDiem}")
    print(f"  Tỉnh: {d.maTinhThanh.tenTinhThanh}")
    print(f"  Địa chỉ: {d.diaChi[:80]}..." if len(d.diaChi) > 80 else f"  Địa chỉ: {d.diaChi}")
    print(f"  Đánh giá: {d.danhGiaTrungBinh} ({d.soLuotDanhGia} lượt)")
    print(f"  Tọa độ: ({d.viDo}, {d.kinhDo})" if d.viDo and d.kinhDo else "  Tọa độ: (N/A)")

print("\n✓ Hoàn thành kiểm tra!")

