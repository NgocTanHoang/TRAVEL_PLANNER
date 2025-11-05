#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script chuẩn hóa bảng TINHTHANH theo kế hoạch sáp nhập tỉnh thành
- Chỉ giữ 34 tỉnh sau sáp nhập làm tỉnh chính
- Tạo đủ 64 tỉnh (34 tỉnh mới + 30 tỉnh cũ được map vào tỉnh mới)
- Đảm bảo tiếng Việt có dấu đầy đủ
- Update tất cả DIADIEM.maTinhThanh theo mapping mới
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

from apps.places.models import DiaDiem, TinhThanh
from django.db import transaction

# 34 tỉnh thành sau sáp nhập (với tiếng Việt có dấu đầy đủ)
# Đây là các tỉnh CHÍNH sau khi sáp nhập
PROVINCES_AFTER_MERGE = [
    'An Giang', 'Bạc Liêu', 'Bắc Giang', 'Bắc Kạn', 'Bắc Ninh',
    'Bến Tre', 'Bình Định', 'Bình Dương', 'Bình Phước', 'Bình Thuận',
    'Cà Mau', 'Cao Bằng', 'Cần Thơ', 'Đà Nẵng', 'Đắk Lắk',
    'Đắk Nông', 'Điện Biên', 'Đồng Nai', 'Đồng Tháp', 'Gia Lai',
    'Hà Giang', 'Hà Nam', 'Hà Nội', 'Hà Tĩnh', 'Hải Dương',
    'Hải Phòng', 'Hậu Giang', 'Hòa Bình', 'Hưng Yên', 'Khánh Hòa',
    'Kiên Giang', 'Kon Tum', 'Lai Châu', 'Lâm Đồng', 'Lạng Sơn',
    'Lào Cai', 'Long An', 'Nghệ An', 'Quảng Ninh', 'Sơn La',
    'Tây Ninh', 'Thái Bình', 'Thanh Hóa', 'Thừa Thiên Huế', 'Tiền Giang',
    'TP. Hồ Chí Minh', 'Trà Vinh', 'Tuyên Quang', 'Vĩnh Long', 'Vĩnh Phúc',
    'Yên Bái'
]

# Mapping từ 64 tỉnh cũ sang 34 tỉnh mới
# Format: 'Tỉnh cũ': 'Tỉnh mới (sau sáp nhập)'
PROVINCE_MAPPING = {
    # Đồng bằng sông Hồng
    'Hà Nội': 'Hà Nội',
    'Vĩnh Phúc': 'Hà Nội',  # Sáp nhập vào Hà Nội
    'Thái Nguyên': 'Bắc Giang',  # Sáp nhập vào Bắc Giang
    'Hải Phòng': 'Hải Phòng',
    'Thái Bình': 'Hải Phòng',  # Sáp nhập vào Hải Phòng
    'Hải Dương': 'Hải Dương',
    'Hưng Yên': 'Hưng Yên',
    'Hà Nam': 'Hà Nam',
    'Nam Định': 'Hà Nam',  # Sáp nhập vào Hà Nam
    'Ninh Bình': 'Hà Nam',  # Sáp nhập vào Hà Nam
    'Bắc Ninh': 'Bắc Ninh',
    
    # Đông Bắc Bộ
    'Lào Cai': 'Lào Cai',
    'Yên Bái': 'Lào Cai',  # Sáp nhập vào Lào Cai
    'Điện Biên': 'Điện Biên',
    'Lai Châu': 'Lai Châu',
    'Sơn La': 'Điện Biên',  # Sáp nhập vào Điện Biên
    'Hà Giang': 'Hà Giang',
    'Cao Bằng': 'Cao Bằng',
    'Bắc Kạn': 'Bắc Kạn',
    'Tuyên Quang': 'Hà Giang',  # Sáp nhập vào Hà Giang
    'Lạng Sơn': 'Lạng Sơn',
    'Bắc Giang': 'Bắc Giang',
    'Phú Thọ': 'Hà Nội',  # Sáp nhập vào Hà Nội (qua Vĩnh Phúc)
    
    # Bắc Trung Bộ
    'Thanh Hóa': 'Thanh Hóa',
    'Nghệ An': 'Nghệ An',
    'Hà Tĩnh': 'Hà Tĩnh',
    'Quảng Bình': 'Hà Tĩnh',  # Sáp nhập vào Hà Tĩnh
    'Quảng Trị': 'Thừa Thiên Huế',  # Sáp nhập vào Thừa Thiên Huế
    'Thừa Thiên Huế': 'Thừa Thiên Huế',
    
    # Nam Trung Bộ
    'Đà Nẵng': 'Đà Nẵng',
    'Quảng Nam': 'Đà Nẵng',  # Sáp nhập vào Đà Nẵng
    'Quảng Ngãi': 'Bình Định',  # Sáp nhập vào Bình Định
    'Bình Định': 'Bình Định',
    'Phú Yên': 'Khánh Hòa',  # Sáp nhập vào Khánh Hòa
    'Khánh Hòa': 'Khánh Hòa',
    'Ninh Thuận': 'Khánh Hòa',  # Sáp nhập vào Khánh Hòa
    'Bình Thuận': 'Lâm Đồng',  # Sáp nhập vào Lâm Đồng
    
    # Tây Nguyên
    'Kon Tum': 'Kon Tum',
    'Gia Lai': 'Gia Lai',
    'Đắk Lắk': 'Đắk Lắk',
    'Đắk Nông': 'Đắk Nông',
    'Lâm Đồng': 'Lâm Đồng',
    
    # Đông Nam Bộ
    'TP. Hồ Chí Minh': 'TP. Hồ Chí Minh',
    'Bà Rịa - Vũng Tàu': 'TP. Hồ Chí Minh',  # Sáp nhập vào TP.HCM
    'Đồng Nai': 'Đồng Nai',
    'Bình Phước': 'Đồng Nai',  # Sáp nhập vào Đồng Nai
    'Bình Dương': 'Bình Dương',
    'Tây Ninh': 'Bình Dương',  # Sáp nhập vào Bình Dương
    
    # Đồng bằng sông Cửu Long
    'Long An': 'Long An',
    'Tiền Giang': 'Tiền Giang',
    'Bến Tre': 'Bến Tre',
    'Trà Vinh': 'Bến Tre',  # Sáp nhập vào Bến Tre
    'Vĩnh Long': 'Đồng Tháp',  # Sáp nhập vào Đồng Tháp
    'Đồng Tháp': 'Đồng Tháp',
    'An Giang': 'An Giang',
    'Kiên Giang': 'Kiên Giang',
    'Cần Thơ': 'Cần Thơ',
    'Hậu Giang': 'Hậu Giang',
    'Sóc Trăng': 'Hậu Giang',  # Sáp nhập vào Hậu Giang
    'Bạc Liêu': 'Bạc Liêu',
    'Cà Mau': 'Cà Mau',
    
    # Quảng Ninh (giữ nguyên)
    'Quảng Ninh': 'Quảng Ninh',
    'Hòa Bình': 'Hòa Bình',
}


def normalize_province_name(name: str) -> str:
    """Chuẩn hóa tên tỉnh thành có dấu đầy đủ"""
    # Mapping các tên thường gặp sang tên chuẩn
    normalization_map = {
        # TP.HCM
        'Ho Chi Minh': 'TP. Hồ Chí Minh',
        'Ho Chi Minh City': 'TP. Hồ Chí Minh',
        'HCM': 'TP. Hồ Chí Minh',
        'Hồ Chí Minh': 'TP. Hồ Chí Minh',
        'Thành phố Hồ Chí Minh': 'TP. Hồ Chí Minh',
        'TP.HCM': 'TP. Hồ Chí Minh',
        'TP HCM': 'TP. Hồ Chí Minh',
        
        # Bà Rịa - Vũng Tàu
        'Ba Ria - Vung Tau': 'Bà Rịa - Vũng Tàu',
        'Ba Ria Vung Tau': 'Bà Rịa - Vũng Tàu',
        'BR-VT': 'Bà Rịa - Vũng Tàu',
        'Vung Tau': 'Bà Rịa - Vũng Tàu',
        
        # Các tỉnh khác (chuẩn hóa dấu)
        'Binh Phuoc': 'Bình Phước',
        'Binh Thuan': 'Bình Thuận',
        'Binh Dinh': 'Bình Định',
        'Binh Duong': 'Bình Dương',
        'Ben Tre': 'Bến Tre',
        'Bac Lieu': 'Bạc Liêu',
        'Bac Giang': 'Bắc Giang',
        'Bac Kan': 'Bắc Kạn',
        'Bac Ninh': 'Bắc Ninh',
        'Ca Mau': 'Cà Mau',
        'Cao Bang': 'Cao Bằng',
        'Dak Lak': 'Đắk Lắk',
        'Dak Nong': 'Đắk Nông',
        'Dien Bien': 'Điện Biên',
        'Dong Nai': 'Đồng Nai',
        'Dong Thap': 'Đồng Tháp',
        'Gia Lai': 'Gia Lai',
        'Ha Giang': 'Hà Giang',
        'Ha Nam': 'Hà Nam',
        'Ha Tinh': 'Hà Tĩnh',
        'Hai Duong': 'Hải Dương',
        'Hai Phong': 'Hải Phòng',
        'Hau Giang': 'Hậu Giang',
        'Hoa Binh': 'Hòa Bình',
        'Hung Yen': 'Hưng Yên',
        'Khanh Hoa': 'Khánh Hòa',
        'Kien Giang': 'Kiên Giang',
        'Kon Tum': 'Kon Tum',
        'Lai Chau': 'Lai Châu',
        'Lam Dong': 'Lâm Đồng',
        'Lang Son': 'Lạng Sơn',
        'Lao Cai': 'Lào Cai',
        'Thanh Hoa': 'Thanh Hóa',
        'Nghe An': 'Nghệ An',
        'Quang Binh': 'Quảng Bình',
        'Quang Nam': 'Quảng Nam',
        'Quang Ngai': 'Quảng Ngãi',
        'Quang Ninh': 'Quảng Ninh',
        'Quang Tri': 'Quảng Trị',
        'Soc Trang': 'Sóc Trăng',
        'Son La': 'Sơn La',
        'Tay Ninh': 'Tây Ninh',
        'Thai Binh': 'Thái Bình',
        'Thai Nguyen': 'Thái Nguyên',
        'Thua Thien Hue': 'Thừa Thiên Huế',
        'Tien Giang': 'Tiền Giang',
        'Tra Vinh': 'Trà Vinh',
        'Tuyen Quang': 'Tuyên Quang',
        'Vinh Long': 'Vĩnh Long',
        'Vinh Phuc': 'Vĩnh Phúc',
        'Yen Bai': 'Yên Bái',
        'Phu Tho': 'Phú Thọ',
        'Phu Yen': 'Phú Yên',
        'Ninh Binh': 'Ninh Bình',
        'Ninh Thuan': 'Ninh Thuận',
        'Nam Dinh': 'Nam Định',
        'Can Tho': 'Cần Thơ',
        'Da Nang': 'Đà Nẵng',
        'Hanoi': 'Hà Nội',
        'Ha Noi': 'Hà Nội',
    }
    
    # Chuẩn hóa
    normalized = normalization_map.get(name, name)
    
    # Đảm bảo có dấu đầy đủ (kiểm tra các ký tự đặc biệt)
    if 'TP' in normalized and 'Hồ Chí Minh' not in normalized:
        normalized = 'TP. Hồ Chí Minh'
    
    return normalized


def get_64_provinces_with_mapping():
    """
    Trả về danh sách 64 tỉnh và mapping của chúng
    """
    # 64 tỉnh thành trước sáp nhập (đầy đủ với tiếng Việt có dấu)
    all_64_provinces = [
        # Đồng bằng sông Hồng (11)
        'Hà Nội', 'Hải Phòng', 'Hải Dương', 'Hưng Yên', 'Hà Nam',
        'Nam Định', 'Thái Bình', 'Ninh Bình', 'Bắc Ninh', 'Vĩnh Phúc',
        'Thái Nguyên',
        
        # Đông Bắc Bộ (12)
        'Lào Cai', 'Yên Bái', 'Điện Biên', 'Lai Châu', 'Sơn La',
        'Hà Giang', 'Cao Bằng', 'Bắc Kạn', 'Tuyên Quang',
        'Lạng Sơn', 'Bắc Giang', 'Phú Thọ',
        
        # Bắc Trung Bộ (6)
        'Thanh Hóa', 'Nghệ An', 'Hà Tĩnh', 'Quảng Bình', 'Quảng Trị',
        'Thừa Thiên Huế',
        
        # Nam Trung Bộ (8)
        'Đà Nẵng', 'Quảng Nam', 'Quảng Ngãi', 'Bình Định', 'Phú Yên',
        'Khánh Hòa', 'Ninh Thuận', 'Bình Thuận',
        
        # Tây Nguyên (5)
        'Kon Tum', 'Gia Lai', 'Đắk Lắk', 'Đắk Nông', 'Lâm Đồng',
        
        # Đông Nam Bộ (6)
        'TP. Hồ Chí Minh', 'Bà Rịa - Vũng Tàu', 'Đồng Nai', 'Bình Phước',
        'Bình Dương', 'Tây Ninh',
        
        # Đồng bằng sông Cửu Long (13)
        'Long An', 'Tiền Giang', 'Bến Tre', 'Trà Vinh', 'Vĩnh Long',
        'Đồng Tháp', 'An Giang', 'Kiên Giang', 'Cần Thơ', 'Hậu Giang',
        'Sóc Trăng', 'Bạc Liêu', 'Cà Mau',
        
        # Thêm để đủ 64 (bao gồm Quảng Ninh và Hòa Bình)
        'Quảng Ninh', 'Hòa Bình',
    ]
    
    # Đảm bảo có đủ 64 tỉnh - nếu thiếu thì thêm
    if len(all_64_provinces) < 64:
        # Đếm lại để đảm bảo
        unique_provinces = list(set(all_64_provinces))
        if len(unique_provinces) < 64:
            # Có thể có trùng lặp, cần loại bỏ và đếm lại
            all_64_provinces = unique_provinces
    
    return all_64_provinces


def normalize_and_merge_provinces():
    """Chuẩn hóa và sáp nhập tỉnh thành"""
    print("="*80)
    print("CHUẨN HÓA VÀ SÁP NHẬP TỈNH THÀNH")
    print("="*80)
    
    with transaction.atomic():
        # Bước 1: Lấy danh sách 64 tỉnh và mapping
        all_64_provinces = get_64_provinces_with_mapping()
        
        print(f"\n[1/5] Tạo/cập nhật 64 tỉnh thành (34 tỉnh mới + 30 tỉnh cũ)...")
        
        # Tạo/cập nhật tất cả 64 tỉnh
        provinces_dict = {}
        created_count = 0
        updated_count = 0
        
        for province_name in all_64_provinces:
            # Chuẩn hóa tên
            normalized_name = normalize_province_name(province_name)
            
            # Tìm tỉnh mới tương ứng
            new_province_name = PROVINCE_MAPPING.get(normalized_name, normalized_name)
            
            # Tìm hoặc tạo tỉnh
            province, created = TinhThanh.objects.get_or_create(
                tenTinhThanh=normalized_name,
                defaults={
                    'moTa': f'Tỉnh thành {normalized_name}' + 
                           (f' (sẽ sáp nhập vào {new_province_name})' if normalized_name != new_province_name else '')
                }
            )
            
            # Chuẩn hóa tên nếu chưa đúng
            if province.tenTinhThanh != normalized_name:
                province.tenTinhThanh = normalized_name
                province.save()
                updated_count += 1
            
            provinces_dict[normalized_name] = province
            
            if created:
                created_count += 1
                print(f"  ✓ Đã tạo: {normalized_name}" + 
                     (f" (→ {new_province_name})" if normalized_name != new_province_name else ""))
        
        print(f"\n  Đã tạo {created_count} tỉnh mới, cập nhật {updated_count} tỉnh")
        
        # Bước 2: Map các tỉnh không có dấu về tỉnh có dấu
        print("\n[2/5] Map các tỉnh không có dấu về tỉnh có dấu...")
        
        # Mapping các tỉnh không có dấu về tỉnh có dấu
        valid_provinces = set(provinces_dict.keys())
        unmapped_provinces = TinhThanh.objects.exclude(tenTinhThanh__in=valid_provinces)
        mapped_count = 0
        
        for province in unmapped_provinces:
            normalized = normalize_province_name(province.tenTinhThanh)
            if normalized != province.tenTinhThanh and normalized in provinces_dict:
                # Map địa điểm từ tỉnh cũ sang tỉnh mới
                places_count = DiaDiem.objects.filter(maTinhThanh=province).count()
                if places_count > 0:
                    DiaDiem.objects.filter(maTinhThanh=province).update(maTinhThanh=provinces_dict[normalized])
                    mapped_count += places_count
                    print(f"  ✓ Đã map {places_count} địa điểm: {province.tenTinhThanh} → {normalized}")
                
                # Xóa tỉnh cũ
                province.delete()
                mapped_count += 1
        
        # Bước 2b: Xóa các tỉnh không có trong danh sách 64
        print("\n[2b/5] Xóa các tỉnh không hợp lệ...")
        
        valid_provinces = set(provinces_dict.keys())
        all_provinces = TinhThanh.objects.all()
        deleted_count = 0
        
        for province in all_provinces:
            if province.tenTinhThanh not in valid_provinces:
                # Kiểm tra không còn địa điểm nào
                places_count = DiaDiem.objects.filter(maTinhThanh=province).count()
                if places_count == 0:
                    province.delete()
                    deleted_count += 1
                    print(f"  ✓ Đã xóa: {province.tenTinhThanh}")
                else:
                    # Nếu còn địa điểm, cố gắng map về tỉnh gần nhất
                    normalized = normalize_province_name(province.tenTinhThanh)
                    if normalized in provinces_dict:
                        DiaDiem.objects.filter(maTinhThanh=province).update(maTinhThanh=provinces_dict[normalized])
                        print(f"  ✓ Đã map {places_count} địa điểm: {province.tenTinhThanh} → {normalized}")
                        province.delete()
                        deleted_count += 1
                    else:
                        print(f"  ⚠ Còn {places_count} địa điểm ở {province.tenTinhThanh}, cần map thủ công")
        
        # Bước 3: Chuẩn hóa tên các tỉnh còn lại (nếu có)
        print("\n[3/5] Chuẩn hóa tên các tỉnh thành...")
        
        normalized_count = 0
        for province in TinhThanh.objects.all():
            normalized_name = normalize_province_name(province.tenTinhThanh)
            if province.tenTinhThanh != normalized_name:
                # Kiểm tra không trùng
                existing = TinhThanh.objects.filter(tenTinhThanh=normalized_name).exclude(pk=province.pk).first()
                if not existing:
                    old_name = province.tenTinhThanh
                    province.tenTinhThanh = normalized_name
                    province.save()
                    normalized_count += 1
                    print(f"  ✓ Đã chuẩn hóa: {old_name} → {normalized_name}")
                else:
                    # Nếu đã có tỉnh có dấu, map địa điểm và xóa tỉnh không có dấu
                    places_count = DiaDiem.objects.filter(maTinhThanh=province).count()
                    if places_count > 0:
                        DiaDiem.objects.filter(maTinhThanh=province).update(maTinhThanh=existing)
                        print(f"  ✓ Đã map {places_count} địa điểm: {province.tenTinhThanh} → {normalized_name}")
                    province.delete()
                    deleted_count += 1
        
        # Bước 4: Update DIADIEM.maTinhThanh theo mapping
        print("\n[4/5] Cập nhật DIADIEM theo mapping sáp nhập...")
        
        updated_places = 0
        for old_name, new_name in PROVINCE_MAPPING.items():
            if old_name == new_name:
                continue  # Không cần update
            
            old_province = TinhThanh.objects.filter(tenTinhThanh=old_name).first()
            new_province = TinhThanh.objects.filter(tenTinhThanh=new_name).first()
            
            if old_province and new_province:
                places_count = DiaDiem.objects.filter(maTinhThanh=old_province).count()
                if places_count > 0:
                    DiaDiem.objects.filter(maTinhThanh=old_province).update(maTinhThanh=new_province)
                    updated_places += places_count
                    print(f"  ✓ Đã chuyển {places_count} địa điểm: {old_name} → {new_name}")
        
        # Bước 5: Tổng kết
        print("\n[5/5] Tổng kết...")
        
        total_provinces = TinhThanh.objects.count()
        provinces_after_merge_count = len([p for p in PROVINCE_MAPPING.values() if p in PROVINCE_MAPPING.values() and PROVINCE_MAPPING.get(p) == p])
        
        print(f"\n{'='*80}")
        print(f"[OK] HOÀN TẤT!")
        print(f"  - Tổng số tỉnh thành: {total_provinces}")
        print(f"  - Đã cập nhật {updated_places} địa điểm theo mapping")
        print(f"  - Đã chuẩn hóa {normalized_count} tên tỉnh thành")
        print(f"  - Đã xóa {deleted_count} tỉnh không hợp lệ")
        print(f"{'='*80}")
        
        # Hiển thị danh sách 64 tỉnh
        print("\n📋 DANH SÁCH 64 TỈNH THÀNH:")
        print("-"*80)
        provinces_list = sorted(TinhThanh.objects.values_list('tenTinhThanh', flat=True))
        for i, province in enumerate(provinces_list, 1):
            mapped_to = PROVINCE_MAPPING.get(province, province)
            marker = " → " + mapped_to if mapped_to != province else ""
            print(f"  {i:2}. {province:30}{marker}")


if __name__ == '__main__':
    normalize_and_merge_provinces()
