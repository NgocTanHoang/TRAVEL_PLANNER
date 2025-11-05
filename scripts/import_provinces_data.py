#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script import dữ liệu tỉnh thành với thông tin đầy đủ
- Tên tỉnh trước sáp nhập
- Trạng thái sau 12/6/2025
- Thủ phủ
- Tọa độ (vĩ độ, kinh độ)
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

from apps.places.models import TinhThanh, DiaDiem
from django.db import transaction
import re

# Dữ liệu tỉnh thành từ bảng
PROVINCE_DATA = [
    {'ten': 'An Giang', 'trang_thai': 'còn tên (An Giang)', 'thu_phu': 'Long Xuyên', 'vi_do': 10.3696, 'kinh_do': 105.4345, 'map_to': 'An Giang'},
    {'ten': 'Bà Rịa – Vũng Tàu', 'trang_thai': '(thuộc Thành phố Hồ Chí Minh)', 'thu_phu': 'Bà Rịa', 'vi_do': 10.4297, 'kinh_do': 107.1363, 'map_to': 'TP. Hồ Chí Minh'},
    {'ten': 'Bạc Liêu', 'trang_thai': '(thuộc Cà Mau)', 'thu_phu': 'Bạc Liêu', 'vi_do': 9.2877, 'kinh_do': 105.7246, 'map_to': 'Cà Mau'},
    {'ten': 'Bắc Giang', 'trang_thai': '(thuộc Bắc Ninh)', 'thu_phu': 'Bắc Giang', 'vi_do': 21.2738, 'kinh_do': 106.1966, 'map_to': 'Bắc Ninh'},
    {'ten': 'Bắc Kạn', 'trang_thai': '(thuộc Thái Nguyên)', 'thu_phu': 'Bắc Kạn', 'vi_do': 22.1330, 'kinh_do': 105.8390, 'map_to': 'Thái Nguyên'},
    {'ten': 'Bắc Ninh', 'trang_thai': 'còn tên', 'thu_phu': 'Bắc Ninh', 'vi_do': 21.1868, 'kinh_do': 106.0718, 'map_to': 'Bắc Ninh'},
    {'ten': 'Bến Tre', 'trang_thai': '(thuộc Vĩnh Long)', 'thu_phu': 'Bến Tre', 'vi_do': 10.2361, 'kinh_do': 106.3741, 'map_to': 'Vĩnh Long'},
    {'ten': 'Bình Định', 'trang_thai': '(thuộc Gia Lai)', 'thu_phu': 'Quy Nhơn', 'vi_do': 13.7825, 'kinh_do': 109.2191, 'map_to': 'Gia Lai'},
    {'ten': 'Bình Dương', 'trang_thai': '(thuộc Thành phố Hồ Chí Minh)', 'thu_phu': 'Thủ Dầu Một', 'vi_do': 10.9690, 'kinh_do': 106.6550, 'map_to': 'TP. Hồ Chí Minh'},
    {'ten': 'Bình Phước', 'trang_thai': '(thuộc Đồng Nai)', 'thu_phu': 'Đồng Xoài', 'vi_do': 11.5364, 'kinh_do': 106.9864, 'map_to': 'Đồng Nai'},
    {'ten': 'Bình Thuận', 'trang_thai': '(thuộc Lâm Đồng)', 'thu_phu': 'Phan Thiết', 'vi_do': 10.9448, 'kinh_do': 108.0910, 'map_to': 'Lâm Đồng'},
    {'ten': 'Cà Mau', 'trang_thai': 'còn tên', 'thu_phu': 'Cà Mau', 'vi_do': 9.1766, 'kinh_do': 105.1526, 'map_to': 'Cà Mau'},
    {'ten': 'Cao Bằng', 'trang_thai': 'còn tên', 'thu_phu': 'Cao Bằng', 'vi_do': 22.6687, 'kinh_do': 106.2460, 'map_to': 'Cao Bằng'},
    {'ten': 'Cần Thơ', 'trang_thai': 'còn tên', 'thu_phu': 'Ninh Kiều (Cần Thơ)', 'vi_do': 10.0452, 'kinh_do': 105.7469, 'map_to': 'Cần Thơ'},
    {'ten': 'Đà Nẵng', 'trang_thai': 'còn tên', 'thu_phu': 'Hải Châu (Đà Nẵng)', 'vi_do': 16.0544, 'kinh_do': 108.2022, 'map_to': 'Đà Nẵng'},
    {'ten': 'Đắk Lắk', 'trang_thai': 'còn tên', 'thu_phu': 'Buôn Ma Thuột', 'vi_do': 12.6667, 'kinh_do': 108.0500, 'map_to': 'Đắk Lắk'},
    {'ten': 'Đắk Nông', 'trang_thai': '(thuộc Lâm Đồng)', 'thu_phu': 'Gia Nghĩa', 'vi_do': 12.0115, 'kinh_do': 107.5413, 'map_to': 'Lâm Đồng'},
    {'ten': 'Điện Biên', 'trang_thai': 'còn tên', 'thu_phu': 'Điện Biên Phủ', 'vi_do': 21.3869, 'kinh_do': 103.0211, 'map_to': 'Điện Biên'},
    {'ten': 'Đồng Nai', 'trang_thai': 'còn tên', 'thu_phu': 'Biên Hòa', 'vi_do': 10.9579, 'kinh_do': 106.8384, 'map_to': 'Đồng Nai'},
    {'ten': 'Đồng Tháp', 'trang_thai': 'còn tên', 'thu_phu': 'Cao Lãnh', 'vi_do': 10.4593, 'kinh_do': 105.6333, 'map_to': 'Đồng Tháp'},
    {'ten': 'Gia Lai', 'trang_thai': 'còn tên', 'thu_phu': 'Pleiku', 'vi_do': 13.9833, 'kinh_do': 108.0000, 'map_to': 'Gia Lai'},
    {'ten': 'Hà Giang', 'trang_thai': '(thuộc Tuyên Quang)', 'thu_phu': 'Hà Giang', 'vi_do': 22.7769, 'kinh_do': 104.9924, 'map_to': 'Tuyên Quang'},
    {'ten': 'Hà Nam', 'trang_thai': '(thuộc Ninh Bình)', 'thu_phu': 'Phủ Lý', 'vi_do': 20.5381, 'kinh_do': 105.9171, 'map_to': 'Ninh Bình'},
    {'ten': 'Hà Nội', 'trang_thai': 'còn tên', 'thu_phu': 'Hoàn Kiếm (Hà Nội)', 'vi_do': 21.0285, 'kinh_do': 105.8542, 'map_to': 'Hà Nội'},
    {'ten': 'Hà Tĩnh', 'trang_thai': 'còn tên', 'thu_phu': 'Hà Tĩnh', 'vi_do': 18.3409, 'kinh_do': 105.9055, 'map_to': 'Hà Tĩnh'},
    {'ten': 'Hải Dương', 'trang_thai': '(thuộc Hải Phòng)', 'thu_phu': 'Hải Dương', 'vi_do': 20.9408, 'kinh_do': 106.3240, 'map_to': 'Hải Phòng'},
    {'ten': 'Hải Phòng', 'trang_thai': 'còn tên', 'thu_phu': 'Hồng Bàng (Hải Phòng)', 'vi_do': 20.8449, 'kinh_do': 106.6881, 'map_to': 'Hải Phòng'},
    {'ten': 'Hậu Giang', 'trang_thai': '(thuộc Thành phố Cần Thơ)', 'thu_phu': 'Vị Thanh', 'vi_do': 9.7847, 'kinh_do': 105.4075, 'map_to': 'Cần Thơ'},
    {'ten': 'Hòa Bình', 'trang_thai': '(thuộc Phú Thọ)', 'thu_phu': 'Hòa Bình', 'vi_do': 20.8330, 'kinh_do': 105.3389, 'map_to': 'Phú Thọ'},
    {'ten': 'Hưng Yên', 'trang_thai': 'còn tên', 'thu_phu': 'Hưng Yên', 'vi_do': 20.5153, 'kinh_do': 106.0675, 'map_to': 'Hưng Yên'},
    {'ten': 'Khánh Hòa', 'trang_thai': 'còn tên', 'thu_phu': 'Nha Trang', 'vi_do': 12.2388, 'kinh_do': 109.1967, 'map_to': 'Khánh Hòa'},
    {'ten': 'Kiên Giang', 'trang_thai': '(thuộc An Giang)', 'thu_phu': 'Rạch Giá', 'vi_do': 10.0159, 'kinh_do': 105.0795, 'map_to': 'An Giang'},
    {'ten': 'Kon Tum', 'trang_thai': '(thuộc Quảng Ngãi)', 'thu_phu': 'Kon Tum', 'vi_do': 14.3494, 'kinh_do': 107.9774, 'map_to': 'Quảng Ngãi'},
    {'ten': 'Lai Châu', 'trang_thai': 'còn tên', 'thu_phu': 'Lai Châu', 'vi_do': 22.4032, 'kinh_do': 103.0873, 'map_to': 'Lai Châu'},
    {'ten': 'Lâm Đồng', 'trang_thai': 'còn tên', 'thu_phu': 'Đà Lạt', 'vi_do': 11.9404, 'kinh_do': 108.4583, 'map_to': 'Lâm Đồng'},
    {'ten': 'Lạng Sơn', 'trang_thai': 'còn tên', 'thu_phu': 'Lạng Sơn', 'vi_do': 21.8560, 'kinh_do': 106.7619, 'map_to': 'Lạng Sơn'},
    {'ten': 'Lào Cai', 'trang_thai': 'còn tên', 'thu_phu': 'Lào Cai', 'vi_do': 22.4833, 'kinh_do': 103.9833, 'map_to': 'Lào Cai'},
    {'ten': 'Long An', 'trang_thai': '(thuộc Tây Ninh)', 'thu_phu': 'Tân An', 'vi_do': 10.5350, 'kinh_do': 106.3976, 'map_to': 'Tây Ninh'},
    {'ten': 'Nam Định', 'trang_thai': '(thuộc Ninh Bình)', 'thu_phu': 'Nam Định', 'vi_do': 20.4258, 'kinh_do': 106.1766, 'map_to': 'Ninh Bình'},
    {'ten': 'Nghệ An', 'trang_thai': 'còn tên', 'thu_phu': 'Vinh', 'vi_do': 18.6714, 'kinh_do': 105.6972, 'map_to': 'Nghệ An'},
    {'ten': 'Ninh Bình', 'trang_thai': 'còn tên', 'thu_phu': 'Ninh Bình', 'vi_do': 20.2500, 'kinh_do': 105.9754, 'map_to': 'Ninh Bình'},
    {'ten': 'Ninh Thuận', 'trang_thai': '(thuộc Khánh Hòa)', 'thu_phu': 'Phan Rang–Tháp Chàm', 'vi_do': 11.5695, 'kinh_do': 108.9888, 'map_to': 'Khánh Hòa'},
    {'ten': 'Phú Thọ', 'trang_thai': 'còn tên', 'thu_phu': 'Việt Trì', 'vi_do': 21.3070, 'kinh_do': 105.4331, 'map_to': 'Phú Thọ'},
    {'ten': 'Phú Yên', 'trang_thai': '(thuộc Đắk Lắk)', 'thu_phu': 'Tuy Hòa', 'vi_do': 13.0956, 'kinh_do': 109.3206, 'map_to': 'Đắk Lắk'},
    {'ten': 'Quảng Bình', 'trang_thai': '(thuộc Quảng Trị)', 'thu_phu': 'Đồng Hới', 'vi_do': 17.4686, 'kinh_do': 106.6335, 'map_to': 'Quảng Trị'},
    {'ten': 'Quảng Nam', 'trang_thai': '(thuộc Đà Nẵng)', 'thu_phu': 'Tam Kỳ', 'vi_do': 15.5693, 'kinh_do': 108.4790, 'map_to': 'Đà Nẵng'},
    {'ten': 'Quảng Ngãi', 'trang_thai': 'còn tên', 'thu_phu': 'Quảng Ngãi', 'vi_do': 15.1210, 'kinh_do': 108.7976, 'map_to': 'Quảng Ngãi'},
    {'ten': 'Quảng Ninh', 'trang_thai': 'còn tên', 'thu_phu': 'Hạ Long', 'vi_do': 20.9601, 'kinh_do': 107.0550, 'map_to': 'Quảng Ninh'},
    {'ten': 'Quảng Trị', 'trang_thai': 'còn tên', 'thu_phu': 'Đông Hà', 'vi_do': 16.7866, 'kinh_do': 107.0976, 'map_to': 'Quảng Trị'},
    {'ten': 'Sóc Trăng', 'trang_thai': '(thuộc Thành phố Cần Thơ)', 'thu_phu': 'Sóc Trăng', 'vi_do': 9.6030, 'kinh_do': 105.9739, 'map_to': 'Cần Thơ'},
    {'ten': 'Sơn La', 'trang_thai': 'còn tên', 'thu_phu': 'Sơn La', 'vi_do': 21.3253, 'kinh_do': 103.8972, 'map_to': 'Sơn La'},
    {'ten': 'Tây Ninh', 'trang_thai': 'còn tên', 'thu_phu': 'Tây Ninh', 'vi_do': 11.3490, 'kinh_do': 106.1300, 'map_to': 'Tây Ninh'},
    {'ten': 'Thái Bình', 'trang_thai': '(thuộc Hưng Yên)', 'thu_phu': 'Thái Bình', 'vi_do': 20.4475, 'kinh_do': 106.3332, 'map_to': 'Hưng Yên'},
    {'ten': 'Thái Nguyên', 'trang_thai': 'còn tên', 'thu_phu': 'Thái Nguyên', 'vi_do': 21.5892, 'kinh_do': 105.8482, 'map_to': 'Thái Nguyên'},
    {'ten': 'Thanh Hóa', 'trang_thai': 'còn tên', 'thu_phu': 'Thanh Hóa', 'vi_do': 19.8077, 'kinh_do': 105.7667, 'map_to': 'Thanh Hóa'},
    {'ten': 'Thừa Thiên – Huế', 'trang_thai': 'còn tên (Huế)', 'thu_phu': 'Huế', 'vi_do': 16.4637, 'kinh_do': 107.5909, 'map_to': 'Thừa Thiên Huế'},
    {'ten': 'Tiền Giang', 'trang_thai': '(thuộc Đồng Tháp)', 'thu_phu': 'Mỹ Tho', 'vi_do': 10.3650, 'kinh_do': 106.3637, 'map_to': 'Đồng Tháp'},
    {'ten': 'Trà Vinh', 'trang_thai': '(thuộc Vĩnh Long)', 'thu_phu': 'Trà Vinh', 'vi_do': 9.9340, 'kinh_do': 106.3458, 'map_to': 'Vĩnh Long'},
    {'ten': 'Tuyên Quang', 'trang_thai': 'còn tên', 'thu_phu': 'Tuyên Quang', 'vi_do': 21.8217, 'kinh_do': 105.2198, 'map_to': 'Tuyên Quang'},
    {'ten': 'Vĩnh Long', 'trang_thai': 'còn tên', 'thu_phu': 'Vĩnh Long', 'vi_do': 10.2476, 'kinh_do': 105.9642, 'map_to': 'Vĩnh Long'},
    {'ten': 'Vĩnh Phúc', 'trang_thai': '(thuộc Phú Thọ)', 'thu_phu': 'Vĩnh Yên', 'vi_do': 21.3075, 'kinh_do': 105.6004, 'map_to': 'Phú Thọ'},
    {'ten': 'Yên Bái', 'trang_thai': '(thuộc Lào Cai)', 'thu_phu': 'Yên Bái', 'vi_do': 21.7121, 'kinh_do': 104.8947, 'map_to': 'Lào Cai'},
    {'ten': 'Thành phố Hồ Chí Minh', 'trang_thai': 'còn tên', 'thu_phu': 'Quận 1 (TPHCM)', 'vi_do': 10.7756, 'kinh_do': 106.7019, 'map_to': 'TP. Hồ Chí Minh'},
    {'ten': 'Thành phố Huế', 'trang_thai': 'còn tên', 'thu_phu': 'Huế (đã liệt kê ở 56)', 'vi_do': 16.4637, 'kinh_do': 107.5909, 'map_to': 'Thừa Thiên Huế'},
]


def parse_status(status: str) -> tuple:
    """
    Parse trạng thái để lấy tỉnh chính sau sáp nhập
    
    Returns:
        (is_main, parent_province)
    """
    if 'còn tên' in status.lower():
        return (True, None)
    
    # Extract parent province from "(thuộc ...)"
    match = re.search(r'\(thuộc\s+(.+?)\)', status)
    if match:
        parent = match.group(1).strip()
        # Normalize parent name
        parent = parent.replace('Thành phố ', 'TP. ')
        return (False, parent)
    
    return (False, None)


def import_provinces():
    """Import dữ liệu tỉnh thành vào database"""
    print("="*80)
    print("IMPORT DỮ LIỆU TỈNH THÀNH")
    print("="*80)
    
    with transaction.atomic():
        # Bước 1: Tạo/cập nhật các tỉnh chính (còn tên sau sáp nhập)
        print("\n[1/3] Tạo/cập nhật các tỉnh chính (còn tên)...")
        
        main_provinces = {}
        for prov in PROVINCE_DATA:
            is_main, parent = parse_status(prov['trang_thai'])
            if is_main:
                province, created = TinhThanh.objects.get_or_create(
                    tenTinhThanh=prov['ten'],
                    defaults={
                        'moTa': f"Tỉnh thành {prov['ten']}. Thủ phủ: {prov['thu_phu']}",
                        'viDo': prov['vi_do'],
                        'kinhDo': prov['kinh_do']
                    }
                )
                
                # Cập nhật thông tin nếu đã tồn tại
                if not created:
                    province.moTa = f"Tỉnh thành {prov['ten']}. Thủ phủ: {prov['thu_phu']}"
                    province.viDo = prov['vi_do']
                    province.kinhDo = prov['kinh_do']
                    province.save()
                
                main_provinces[prov['ten']] = province
                if created:
                    print(f"  ✓ Đã tạo: {prov['ten']} ({prov['thu_phu']})")
                else:
                    print(f"  ↻ Đã cập nhật: {prov['ten']}")
        
        print(f"\n  Tổng số tỉnh chính: {len(main_provinces)}")
        
        # Bước 2: Tạo các tỉnh sẽ sáp nhập
        print("\n[2/3] Tạo các tỉnh sẽ sáp nhập...")
        
        merged_provinces = {}
        for prov in PROVINCE_DATA:
            is_main, parent = parse_status(prov['trang_thai'])
            if not is_main and parent:
                # Normalize parent name để tìm
                parent_normalized = parent.replace('TP. ', 'Thành phố ')
                if parent_normalized not in main_provinces:
                    # Thử tìm với các biến thể
                    for main_name, main_prov in main_provinces.items():
                        if parent_normalized in main_name or main_name in parent_normalized:
                            parent_normalized = main_name
                            break
                
                # Tạo tỉnh sẽ sáp nhập
                province, created = TinhThanh.objects.get_or_create(
                    tenTinhThanh=prov['ten'],
                    defaults={
                        'moTa': f"Tỉnh thành {prov['ten']}. Thủ phủ: {prov['thu_phu']}. {prov['trang_thai']}",
                        'viDo': prov['vi_do'],
                        'kinhDo': prov['kinh_do']
                    }
                )
                
                # Cập nhật thông tin nếu đã tồn tại
                if not created:
                    province.moTa = f"Tỉnh thành {prov['ten']}. Thủ phủ: {prov['thu_phu']}. {prov['trang_thai']}"
                    province.viDo = prov['vi_do']
                    province.kinhDo = prov['kinh_do']
                    province.save()
                
                merged_provinces[prov['ten']] = {
                    'province': province,
                    'parent': parent_normalized,
                    'map_to': prov['map_to']
                }
                
                if created:
                    print(f"  ✓ Đã tạo: {prov['ten']} → {prov['map_to']}")
        
        print(f"\n  Tổng số tỉnh sẽ sáp nhập: {len(merged_provinces)}")
        
        # Bước 3: Cập nhật DIADIEM theo mapping mới
        print("\n[3/3] Cập nhật DIADIEM theo mapping mới...")
        
        updated_count = 0
        for prov_name, info in merged_provinces.items():
            # Tìm tỉnh cha
            parent_name = info['map_to']
            parent_province = main_provinces.get(parent_name)
            
            if not parent_province:
                # Tìm với các biến thể
                for main_name, main_prov in main_provinces.items():
                    if parent_name in main_name or main_name in parent_name:
                        parent_province = main_prov
                        break
            
            if parent_province:
                # Cập nhật địa điểm từ tỉnh cũ sang tỉnh mới
                places_count = DiaDiem.objects.filter(maTinhThanh=info['province']).count()
                if places_count > 0:
                    DiaDiem.objects.filter(maTinhThanh=info['province']).update(maTinhThanh=parent_province)
                    updated_count += places_count
                    print(f"  ✓ Đã chuyển {places_count} địa điểm: {prov_name} → {parent_name}")
        
        # Xóa các tỉnh không có trong danh sách 64 và xử lý trùng lặp
        print("\n[4/3] Xóa các tỉnh không hợp lệ và xử lý trùng lặp...")
        
        # Xử lý trùng lặp trước
        # 1. "Thành phố Huế" vs "Thừa Thiên – Huế" → giữ "Thừa Thiên – Huế"
        thanh_pho_hue = TinhThanh.objects.filter(tenTinhThanh='Thành phố Huế').first()
        thua_thien_hue = TinhThanh.objects.filter(tenTinhThanh='Thừa Thiên – Huế').first()
        thua_thien_hue_alt = TinhThanh.objects.filter(tenTinhThanh='Thừa Thiên Huế').first()
        
        if thanh_pho_hue:
            if thua_thien_hue:
                places_count = DiaDiem.objects.filter(maTinhThanh=thanh_pho_hue).count()
                if places_count > 0:
                    DiaDiem.objects.filter(maTinhThanh=thanh_pho_hue).update(maTinhThanh=thua_thien_hue)
                    print(f"  ✓ Đã chuyển {places_count} địa điểm từ Thành phố Huế sang Thừa Thiên – Huế")
                thanh_pho_hue.delete()
                print(f"  ✓ Đã xóa trùng lặp: Thành phố Huế")
        
        # Xóa "Thừa Thiên Huế" nếu có (giữ lại "Thừa Thiên – Huế")
        if thua_thien_hue_alt and thua_thien_hue:
            places_count = DiaDiem.objects.filter(maTinhThanh=thua_thien_hue_alt).count()
            if places_count > 0:
                DiaDiem.objects.filter(maTinhThanh=thua_thien_hue_alt).update(maTinhThanh=thua_thien_hue)
                print(f"  ✓ Đã chuyển {places_count} địa điểm từ Thừa Thiên Huế sang Thừa Thiên – Huế")
            thua_thien_hue_alt.delete()
            print(f"  ✓ Đã xóa trùng lặp: Thừa Thiên Huế")
        
        # 2. "TP. Hồ Chí Minh" vs "Thành phố Hồ Chí Minh" → giữ "Thành phố Hồ Chí Minh"
        tp_hcm = TinhThanh.objects.filter(tenTinhThanh='TP. Hồ Chí Minh').first()
        thanh_pho_hcm = TinhThanh.objects.filter(tenTinhThanh='Thành phố Hồ Chí Minh').first()
        
        if tp_hcm and thanh_pho_hcm:
            places_count = DiaDiem.objects.filter(maTinhThanh=tp_hcm).count()
            if places_count > 0:
                DiaDiem.objects.filter(maTinhThanh=tp_hcm).update(maTinhThanh=thanh_pho_hcm)
                print(f"  ✓ Đã chuyển {places_count} địa điểm từ TP. Hồ Chí Minh sang Thành phố Hồ Chí Minh")
            tp_hcm.delete()
            print(f"  ✓ Đã xóa trùng lặp: TP. Hồ Chí Minh")
        
        # Xóa các tỉnh không có trong danh sách hợp lệ
        valid_provinces = set([p['ten'] for p in PROVINCE_DATA])
        all_provinces = list(TinhThanh.objects.all())
        deleted_count = 0
        
        for province in all_provinces:
            if province.tenTinhThanh not in valid_provinces:
                places_count = DiaDiem.objects.filter(maTinhThanh=province).count()
                if places_count == 0:
                    province.delete()
                    deleted_count += 1
        
        print(f"  ✓ Đã xóa {deleted_count} tỉnh không hợp lệ")
        
        # Tổng kết
        total_provinces = TinhThanh.objects.count()
        print(f"\n{'='*80}")
        print(f"[OK] HOÀN TẤT!")
        print(f"  - Tổng số tỉnh thành: {total_provinces}")
        print(f"  - Tỉnh chính (còn tên): {len(main_provinces)}")
        print(f"  - Tỉnh sẽ sáp nhập: {len(merged_provinces)}")
        print(f"  - Đã cập nhật {updated_count} địa điểm theo mapping")
        print(f"{'='*80}")
        
        # Hiển thị danh sách
        print("\n📋 DANH SÁCH 64 TỈNH THÀNH:")
        print("-"*80)
        provinces_list = sorted(TinhThanh.objects.values_list('tenTinhThanh', flat=True))
        for i, province_name in enumerate(provinces_list, 1):
            # Tìm trong PROVINCE_DATA
            prov_info = next((p for p in PROVINCE_DATA if p['ten'] == province_name), None)
            if prov_info:
                is_main, parent = parse_status(prov_info['trang_thai'])
                if is_main:
                    marker = ""
                else:
                    marker = f" → {prov_info['map_to']}"
                print(f"  {i:2}. {province_name:35} {marker}")
        
        print(f"\n{'='*80}")


if __name__ == '__main__':
    import_provinces()

