#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script trích xuất toàn bộ dữ liệu bảng DIADIEM
Export ra CSV và JSON
"""
import os
import sys
import django
import json
import csv
from pathlib import Path
from datetime import datetime

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

from apps.places.models import DiaDiem, TinhThanh


def export_to_csv(data, filename):
    """Export dữ liệu ra CSV"""
    if not data:
        print(f"  ⚠ Không có dữ liệu để export")
        return
    
    # Lấy tất cả các keys từ record đầu tiên
    fieldnames = list(data[0].keys())
    
    with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)
    
    print(f"  ✓ Đã export {len(data)} records ra {filename}")


def export_to_json(data, filename):
    """Export dữ liệu ra JSON"""
    with open(filename, 'w', encoding='utf-8') as jsonfile:
        json.dump(data, jsonfile, ensure_ascii=False, indent=2)
    
    print(f"  ✓ Đã export {len(data)} records ra {filename}")


def extract_all_places():
    """Trích xuất toàn bộ dữ liệu địa điểm"""
    print("="*80)
    print("TRÍCH XUẤT DỮ LIỆU BẢNG DIADIEM")
    print("="*80)
    
    # Lấy tất cả địa điểm
    places = DiaDiem.objects.select_related('maTinhThanh', 'maNguoiTao').all()
    total = places.count()
    
    print(f"\n[INFO] Tổng số địa điểm: {total}")
    
    if total == 0:
        print("  ⚠ Không có dữ liệu địa điểm!")
        return
    
    # Chuẩn bị dữ liệu
    data = []
    for place in places:
        record = {
            'maDiaDiem': place.maDiaDiem,
            'tenDiaDiem': place.tenDiaDiem,
            'moTa': place.moTa or '',
            'diaChi': place.diaChi or '',
            'maTinhThanh': place.maTinhThanh.maTinhThanh if place.maTinhThanh else '',
            'tenTinhThanh': place.maTinhThanh.tenTinhThanh if place.maTinhThanh else '',
            'loaiDiaDiem': place.loaiDiaDiem,
            'viDo': place.viDo if place.viDo is not None else '',
            'kinhDo': place.kinhDo if place.kinhDo is not None else '',
            'giaVe': place.giaVe if place.giaVe is not None else '',
            'gioMoCua': place.gioMoCua or '',
            'gioDongCua': place.gioDongCua or '',
            'dienThoai': place.dienThoai or '',
            'website': place.website or '',
            'danhGiaTrungBinh': place.danhGiaTrungBinh,
            'soLuotDanhGia': place.soLuotDanhGia,
            'soLuotXem': place.soLuotXem,
            'maNguoiTao': place.maNguoiTao.id if place.maNguoiTao else '',
            'tenNguoiTao': place.maNguoiTao.username if place.maNguoiTao else '',
            'ngayTao': place.ngayTao.strftime('%Y-%m-%d %H:%M:%S') if place.ngayTao else '',
            'lanCapNhatCuoi': place.lanCapNhatCuoi.strftime('%Y-%m-%d %H:%M:%S') if place.lanCapNhatCuoi else '',
            'trangThai': place.trangThai,
            'dacDiem': place.dacDiem or '',
            'tienNghi': place.tienNghi or '',
        }
        data.append(record)
    
    # Tạo thư mục export nếu chưa có
    export_dir = PROJECT_ROOT / 'data' / 'exports'
    export_dir.mkdir(parents=True, exist_ok=True)
    
    # Tạo tên file với timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Export CSV
    csv_filename = export_dir / f'diadiem_export_{timestamp}.csv'
    print(f"\n[1/2] Export CSV...")
    export_to_csv(data, csv_filename)
    
    # Export JSON
    json_filename = export_dir / f'diadiem_export_{timestamp}.json'
    print(f"\n[2/2] Export JSON...")
    export_to_json(data, json_filename)
    
    # Thống kê
    print(f"\n{'='*80}")
    print(f"[OK] HOÀN TẤT!")
    print(f"  - Tổng số địa điểm: {total}")
    print(f"  - CSV: {csv_filename}")
    print(f"  - JSON: {json_filename}")
    
    # Thống kê theo loại địa điểm
    print(f"\n📊 THỐNG KÊ THEO LOẠI ĐỊA ĐIỂM:")
    print("-"*80)
    from collections import Counter
    loai_counter = Counter([p.loaiDiaDiem for p in places])
    for loai, count in loai_counter.most_common():
        print(f"  {loai:20} - {count:4} địa điểm")
    
    # Thống kê theo tỉnh thành
    print(f"\n📊 THỐNG KÊ THEO TỈNH THÀNH (Top 10):")
    print("-"*80)
    from collections import Counter
    tinh_counter = Counter([p.maTinhThanh.tenTinhThanh if p.maTinhThanh else 'Không xác định' for p in places])
    for tinh, count in tinh_counter.most_common(10):
        print(f"  {tinh:30} - {count:4} địa điểm")
    
    print(f"{'='*80}")


if __name__ == '__main__':
    extract_all_places()

