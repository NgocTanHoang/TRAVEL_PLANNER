"""
Script để import dữ liệu POI từ file Excel vào database.
Có khả năng hiểu ngữ nghĩa và tự động phân loại địa điểm.
"""
import os
import sys
import django
import pandas as pd
import json
import re
from typing import Dict, Optional, List, Tuple
from pathlib import Path

# Fix encoding for Windows - MUST be before Django setup
if sys.platform == 'win32':
    import io
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Setup Django
BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vivu_core.settings')
django.setup()

from apps.places.models import DiaDiem, TinhThanh
from django.db import transaction

# Import normalize_province_name - copy function để tránh circular import
def normalize_province_name(name: str) -> str:
    """Chuẩn hóa tên tỉnh thành"""
    if not name:
        return name
    
    name = str(name).strip()
    
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
        
        # Hà Nội
        'Ha Noi': 'Hà Nội',
        'Hanoi': 'Hà Nội',
        'Thành phố Hà Nội': 'Hà Nội',
        
        # Đà Nẵng
        'Da Nang': 'Đà Nẵng',
        'Danang': 'Đà Nẵng',
        
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
        'Thanh Hoa': 'Thanh Hóa',
        'Thua Thien Hue': 'Thừa Thiên Huế',
        'Hue': 'Thừa Thiên Huế',
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
        'An Giang': 'An Giang',
        'Ba Ria - Vung Tau': 'Bà Rịa - Vũng Tàu',
        'Ba Ria Vung Tau': 'Bà Rịa - Vũng Tàu',
        'BR-VT': 'Bà Rịa - Vũng Tàu',
        'Vung Tau': 'Bà Rịa - Vũng Tàu',
    }
    
    return normalization_map.get(name, name)


# Mapping từ types trong Excel sang loaiDiaDiem trong database
TYPE_MAPPING = {
    # Địa danh
    'attraction': 'dia_danh',
    'landmark': 'dia_danh',
    'monument': 'dia_danh',
    'temple': 'dia_danh',
    'pagoda': 'dia_danh',
    'church': 'dia_danh',
    'museum': 'dia_danh',
    'park': 'dia_danh',
    'beach': 'dia_danh',
    'mountain': 'dia_danh',
    'cave': 'dia_danh',
    'waterfall': 'dia_danh',
    'lake': 'dia_danh',
    'island': 'dia_danh',
    'bridge': 'dia_danh',
    'tower': 'dia_danh',
    'palace': 'dia_danh',
    'fortress': 'dia_danh',
    'ruin': 'dia_danh',
    'historical_site': 'dia_danh',
    'cultural_site': 'dia_danh',
    'natural_attraction': 'dia_danh',
    
    # Nhà hàng
    'restaurant': 'nha_hang',
    'cafe': 'nha_hang',
    'bar': 'nha_hang',
    'food_court': 'nha_hang',
    'street_food': 'nha_hang',
    'bakery': 'nha_hang',
    'fast_food': 'nha_hang',
    
    # Khách sạn
    'hotel': 'khach_san',
    'resort': 'khach_san',
    'hostel': 'khach_san',
    'homestay': 'khach_san',
    'guesthouse': 'khach_san',
    'apartment': 'khach_san',
    'villa': 'khach_san',
    
    # Giải trí
    'entertainment': 'giai_tri',
    'nightclub': 'giai_tri',
    'cinema': 'giai_tri',
    'theater': 'giai_tri',
    'amusement_park': 'giai_tri',
    'zoo': 'giai_tri',
    'aquarium': 'giai_tri',
    'spa': 'giai_tri',
    'massage': 'giai_tri',
    'karaoke': 'giai_tri',
    'bowling': 'giai_tri',
    'casino': 'giai_tri',
    
    # Mua sắm
    'shopping': 'mua_sam',
    'mall': 'mua_sam',
    'market': 'mua_sam',
    'supermarket': 'mua_sam',
    'convenience_store': 'mua_sam',
    'souvenir_shop': 'mua_sam',
    'boutique': 'mua_sam',
    
    # Khác
    'other': 'khac',
    'unknown': 'khac',
}

# Từ khóa để phân loại dựa trên tên và mô tả
SEMANTIC_KEYWORDS = {
    'dia_danh': [
        'chùa', 'đền', 'miếu', 'phủ', 'đình', 'lăng', 'mộ', 'tượng', 'tượng đài',
        'bảo tàng', 'di tích', 'lịch sử', 'văn hóa', 'cổ', 'xưa',
        'núi', 'đồi', 'đèo', 'hang', 'động', 'thác', 'suối', 'hồ', 'sông', 'biển', 'bãi biển',
        'vườn quốc gia', 'khu bảo tồn', 'rừng', 'công viên', 'quảng trường',
        'cầu', 'tháp', 'lâu đài', 'pháo đài', 'thành cổ', 'phố cổ',
        'đảo', 'quần đảo', 'bán đảo', 'mũi', 'vịnh',
        'nhà thờ', 'nhà nguyện', 'thánh đường',
        'đài tưởng niệm', 'tượng đài', 'khu tưởng niệm',
    ],
    'nha_hang': [
        'nhà hàng', 'quán ăn', 'quán cà phê', 'café', 'coffee', 'cafe',
        'bar', 'pub', 'bistro', 'buffet', 'steakhouse', 'grill',
        'phở', 'bún', 'bánh mì', 'bánh', 'chè', 'nước', 'trà',
        'food court', 'food center', 'ăn uống', 'ẩm thực',
        'bakery', 'tiệm bánh', 'bánh ngọt',
    ],
    'khach_san': [
        'khách sạn', 'hotel', 'resort', 'residence', 'apartment',
        'hostel', 'homestay', 'guesthouse', 'lodge', 'inn',
        'villa', 'bungalow', 'cabin', 'suite', 'room',
        'nghỉ dưỡng', 'lưu trú', 'chỗ ở', 'phòng',
    ],
    'giai_tri': [
        'khu vui chơi', 'giải trí', 'entertainment', 'amusement',
        'nightclub', 'club', 'disco', 'pub', 'bar',
        'cinema', 'rạp chiếu phim', 'movie theater',
        'theater', 'nhà hát', 'sân khấu',
        'spa', 'massage', 'thư giãn', 'relax',
        'karaoke', 'bowling', 'casino', 'sòng bạc',
        'zoo', 'sở thú', 'aquarium', 'thủy cung',
        'công viên giải trí', 'theme park',
    ],
    'mua_sam': [
        'trung tâm thương mại', 'shopping mall', 'mall', 'plaza',
        'chợ', 'market', 'siêu thị', 'supermarket', 'convenience store',
        'cửa hàng', 'shop', 'store', 'boutique', 'souvenir',
        'mua sắm', 'shopping', 'bán hàng',
    ],
}


def classify_place_by_semantics(name: str, description: str = '', type_hint: str = '') -> str:
    """
    Phân loại địa điểm dựa trên ngữ nghĩa (tên, mô tả, type hint).
    Trả về loaiDiaDiem phù hợp nhất.
    """
    # Chuẩn hóa text để so sánh
    text = f"{name} {description} {type_hint}".lower()
    
    # Loại bỏ dấu để so sánh tốt hơn
    def remove_accents(text: str) -> str:
        accents = {
            'à': 'a', 'á': 'a', 'ạ': 'a', 'ả': 'a', 'ã': 'a',
            'â': 'a', 'ầ': 'a', 'ấ': 'a', 'ậ': 'a', 'ẩ': 'a', 'ẫ': 'a',
            'ă': 'a', 'ằ': 'a', 'ắ': 'a', 'ặ': 'a', 'ẳ': 'a', 'ẵ': 'a',
            'è': 'e', 'é': 'e', 'ẹ': 'e', 'ẻ': 'e', 'ẽ': 'e',
            'ê': 'e', 'ề': 'e', 'ế': 'e', 'ệ': 'e', 'ể': 'e', 'ễ': 'e',
            'ì': 'i', 'í': 'i', 'ị': 'i', 'ỉ': 'i', 'ĩ': 'i',
            'ò': 'o', 'ó': 'o', 'ọ': 'o', 'ỏ': 'o', 'õ': 'o',
            'ô': 'o', 'ồ': 'o', 'ố': 'o', 'ộ': 'o', 'ổ': 'o', 'ỗ': 'o',
            'ơ': 'o', 'ờ': 'o', 'ớ': 'o', 'ợ': 'o', 'ở': 'o', 'ỡ': 'o',
            'ù': 'u', 'ú': 'u', 'ụ': 'u', 'ủ': 'u', 'ũ': 'u',
            'ư': 'u', 'ừ': 'u', 'ứ': 'u', 'ự': 'u', 'ử': 'u', 'ữ': 'u',
            'ỳ': 'y', 'ý': 'y', 'ỵ': 'y', 'ỷ': 'y', 'ỹ': 'y',
            'đ': 'd',
        }
        for accented, unaccented in accents.items():
            text = text.replace(accented, unaccented)
        return text
    
    text_no_accent = remove_accents(text)
    
    # Đếm điểm cho mỗi loại
    scores = {
        'dia_danh': 0,
        'nha_hang': 0,
        'khach_san': 0,
        'giai_tri': 0,
        'mua_sam': 0,
        'khac': 0,
    }
    
    # Kiểm tra từ khóa
    for category, keywords in SEMANTIC_KEYWORDS.items():
        for keyword in keywords:
            keyword_no_accent = remove_accents(keyword)
            if keyword_no_accent in text_no_accent or keyword in text:
                scores[category] += 1
    
    # Nếu có type_hint, map nó
    if type_hint:
        type_lower = type_hint.lower().strip()
        mapped_type = TYPE_MAPPING.get(type_lower)
        if mapped_type:
            scores[mapped_type] += 3  # Tăng điểm cho type hint
    
    # Tìm loại có điểm cao nhất
    max_score = max(scores.values())
    if max_score == 0:
        return 'khac'  # Mặc định là "Khác"
    
    # Trả về loại có điểm cao nhất
    for category, score in scores.items():
        if score == max_score:
            return category
    
    return 'khac'


def validate_and_clean_data(row: pd.Series) -> Optional[Dict]:
    """
    Validate và làm sạch dữ liệu từ một dòng Excel.
    Trả về dict với dữ liệu đã được validate, hoặc None nếu không hợp lệ.
    """
    data = {}
    
    # Tên địa điểm (bắt buộc)
    if pd.isna(row.get('name', '')) or str(row.get('name', '')).strip() == '':
        return None
    data['tenDiaDiem'] = str(row.get('name', '')).strip()[:255]
    
    # Địa chỉ
    data['diaChi'] = str(row.get('address', '') or '').strip()[:500]
    
    # Mô tả
    data['moTa'] = str(row.get('description', '') or row.get('moTa', '') or '').strip()
    
    # Tỉnh thành (bắt buộc)
    province_name = str(row.get('province', '') or row.get('city', '') or row.get('tinhThanh', '') or '').strip()
    if not province_name:
        # Thử extract từ địa chỉ
        if data['diaChi']:
            # Logic đơn giản: lấy từ cuối địa chỉ
            parts = data['diaChi'].split(',')
            if len(parts) > 0:
                province_name = parts[-1].strip()
    
    if not province_name:
        return None  # Không có tỉnh thành thì bỏ qua
    
    # Chuẩn hóa tên tỉnh thành
    normalized_province = normalize_province_name(province_name)
    data['province_normalized'] = normalized_province
    
    # Tọa độ
    try:
        data['viDo'] = float(row.get('latitude', 0) or row.get('lat', 0) or 0)
        data['kinhDo'] = float(row.get('longitude', 0) or row.get('lng', 0) or row.get('lon', 0) or 0)
    except (ValueError, TypeError):
        data['viDo'] = None
        data['kinhDo'] = None
    
    # Giá vé
    try:
        data['giaVe'] = float(row.get('price', 0) or row.get('giaVe', 0) or 0)
    except (ValueError, TypeError):
        data['giaVe'] = None
    
    # Giờ mở/đóng cửa
    data['gioMoCua'] = str(row.get('opening_hours', '') or row.get('open_time', '') or row.get('gioMoCua', '') or '').strip()[:50]
    data['gioDongCua'] = str(row.get('closing_hours', '') or row.get('close_time', '') or row.get('gioDongCua', '') or '').strip()[:50]
    
    # Điện thoại
    phone = str(row.get('phone', '') or row.get('dienThoai', '') or '').strip()
    # Làm sạch số điện thoại
    phone = re.sub(r'[^\d+\-() ]', '', phone)[:20]
    data['dienThoai'] = phone
    
    # Website
    website = str(row.get('website', '') or '').strip()
    if website and not website.startswith('http'):
        website = 'http://' + website
    data['website'] = website[:200] if website else ''
    
    # Đánh giá
    try:
        data['danhGiaTrungBinh'] = float(row.get('rating', 0) or row.get('danhGia', 0) or 0)
        if data['danhGiaTrungBinh'] < 0:
            data['danhGiaTrungBinh'] = 0
        if data['danhGiaTrungBinh'] > 5:
            data['danhGiaTrungBinh'] = 5
    except (ValueError, TypeError):
        data['danhGiaTrungBinh'] = 0.0
    
    try:
        data['soLuotDanhGia'] = int(row.get('review_count', 0) or row.get('soLuotDanhGia', 0) or 0)
        if data['soLuotDanhGia'] < 0:
            data['soLuotDanhGia'] = 0
    except (ValueError, TypeError):
        data['soLuotDanhGia'] = 0
    
    # Phân loại địa điểm
    type_hint = str(row.get('type', '') or row.get('types', '') or row.get('category', '') or '').strip()
    
    # Nếu types đã đúng format của database, sử dụng trực tiếp
    valid_types = ['dia_danh', 'nha_hang', 'khach_san', 'giai_tri', 'mua_sam', 'khac']
    type_hint_lower = type_hint.lower() if type_hint else ''
    if type_hint_lower in valid_types:
        data['loaiDiaDiem'] = type_hint_lower
    else:
        # Nếu không, dùng semantic classification
        data['loaiDiaDiem'] = classify_place_by_semantics(
            data['tenDiaDiem'],
            data['moTa'],
            type_hint
        )
    
    # Đặc điểm (JSON)
    features = {}
    if type_hint and type_hint_lower not in valid_types:
        features['original_type'] = type_hint
    if row.get('place_id'):
        features['place_id'] = str(row.get('place_id', ''))
    if row.get('tags'):
        features['tags'] = str(row.get('tags', ''))
    data['dacDiem'] = json.dumps(features, ensure_ascii=False) if features else ''
    
    # Tiện nghi (JSON)
    amenities = {}
    if row.get('amenities'):
        amenities['amenities'] = str(row.get('amenities', ''))
    data['tienNghi'] = json.dumps(amenities, ensure_ascii=False) if amenities else ''
    
    return data


def import_pois_from_excel(excel_path: str, max_rows: Optional[int] = None) -> Dict:
    """
    Import POIs từ file Excel vào database.
    
    Args:
        excel_path: Đường dẫn đến file Excel
        max_rows: Số dòng tối đa để import (None = tất cả)
    
    Returns:
        Dict với thống kê import
    """
    print("="*80)
    print("IMPORT POIs TỪ EXCEL VÀO DATABASE")
    print("="*80)
    print(f"\nFile: {excel_path}")
    
    # Đọc file Excel
    try:
        df = pd.read_excel(excel_path)
        print(f"Đã đọc {len(df)} dòng từ file Excel")
        print(f"Các cột: {', '.join(df.columns.tolist())}")
    except Exception as e:
        print(f"Lỗi đọc file Excel: {e}")
        return {'error': str(e)}
    
    if max_rows:
        df = df.head(max_rows)
        print(f"Giới hạn import {max_rows} dòng đầu tiên")
    
    # Thống kê
    stats = {
        'total_rows': len(df),
        'valid_rows': 0,
        'invalid_rows': 0,
        'created': 0,
        'updated': 0,
        'skipped': 0,
        'errors': [],
        'province_not_found': [],
    }
    
    # Import với transaction
    with transaction.atomic():
        for idx, row in df.iterrows():
            try:
                # Validate và clean data
                data = validate_and_clean_data(row)
                if not data:
                    stats['invalid_rows'] += 1
                    continue
                
                stats['valid_rows'] += 1
                
                # Tìm hoặc tạo tỉnh thành
                try:
                    province = TinhThanh.objects.get(tenTinhThanh=data['province_normalized'])
                except TinhThanh.DoesNotExist:
                    # Tạo tỉnh thành mới
                    province = TinhThanh.objects.create(
                        tenTinhThanh=data['province_normalized'],
                        moTa=f'Tỉnh thành {data["province_normalized"]}'
                    )
                    print(f"  ✓ Đã tạo tỉnh thành mới: {data['province_normalized']}")
                
                # Tìm hoặc tạo địa điểm
                # Sử dụng tenDiaDiem + maTinhThanh làm unique key
                dia_diem, created = DiaDiem.objects.update_or_create(
                    tenDiaDiem=data['tenDiaDiem'],
                    maTinhThanh=province,
                    defaults={
                        'diaChi': data['diaChi'],
                        'moTa': data['moTa'],
                        'loaiDiaDiem': data['loaiDiaDiem'],
                        'viDo': data['viDo'],
                        'kinhDo': data['kinhDo'],
                        'giaVe': data['giaVe'],
                        'gioMoCua': data['gioMoCua'],
                        'gioDongCua': data['gioDongCua'],
                        'dienThoai': data['dienThoai'],
                        'website': data['website'],
                        'danhGiaTrungBinh': data['danhGiaTrungBinh'],
                        'soLuotDanhGia': data['soLuotDanhGia'],
                        'dacDiem': data['dacDiem'],
                        'tienNghi': data['tienNghi'],
                        'trangThai': 'active',
                    }
                )
                
                if created:
                    stats['created'] += 1
                else:
                    stats['updated'] += 1
                
                # Log progress
                if (idx + 1) % 100 == 0:
                    print(f"  Đã xử lý {idx + 1}/{len(df)} dòng...")
                
            except Exception as e:
                stats['errors'].append({
                    'row': idx + 1,
                    'error': str(e),
                    'data': str(row.get('name', 'N/A'))
                })
                stats['skipped'] += 1
                print(f"  ✗ Lỗi ở dòng {idx + 1}: {e}")
    
    # In thống kê
    print("\n" + "="*80)
    print("THỐNG KÊ IMPORT")
    print("="*80)
    print(f"Tổng số dòng: {stats['total_rows']}")
    print(f"Dòng hợp lệ: {stats['valid_rows']}")
    print(f"Dòng không hợp lệ: {stats['invalid_rows']}")
    print(f"Đã tạo mới: {stats['created']}")
    print(f"Đã cập nhật: {stats['updated']}")
    print(f"Đã bỏ qua (lỗi): {stats['skipped']}")
    
    if stats['errors']:
        print(f"\nCác lỗi gặp phải ({len(stats['errors'])} lỗi):")
        for error in stats['errors'][:10]:  # Chỉ hiển thị 10 lỗi đầu
            print(f"  - Dòng {error['row']} ({error['data']}): {error['error']}")
        if len(stats['errors']) > 10:
            print(f"  ... và {len(stats['errors']) - 10} lỗi khác")
    
    return stats


if __name__ == '__main__':
    excel_path = r'D:\KLTN\MAS (1)\MAS\TRAVEL_PLANNER\data\22_cities_pois_complete.xlsx'
    
    if not os.path.exists(excel_path):
        print(f"File không tồn tại: {excel_path}")
        sys.exit(1)
    
    # Import tất cả dữ liệu
    stats = import_pois_from_excel(excel_path)
    
    print("\n✓ Hoàn thành import!")

