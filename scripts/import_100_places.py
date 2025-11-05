#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script để tìm kiếm và import 100 địa điểm từ các vùng Việt Nam vào database
Sử dụng Vector DB, Geo Tools, và Place Info Searcher
"""
import os
import sys
import django
import time
import json
from typing import Dict, List, Optional
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

from django.conf import settings
from apps.places.models import DiaDiem, TinhThanh, HinhAnhDiaDiem

# Import tools
try:
    # Add project root to path for imports
    sys.path.insert(0, str(PROJECT_ROOT))
    from agents.travel_agents.vector_db import get_vector_db_agent
    from tools.geo_tools import GeoTools
    from apps.api.place_info_searcher import get_place_searcher
    TOOLS_AVAILABLE = True
except ImportError as e:
    print(f"[ERROR] Tools not available: {e}")
    import traceback
    traceback.print_exc()
    TOOLS_AVAILABLE = False
    sys.exit(1)

# Các vùng và tỉnh thành để tìm địa điểm
REGIONS = {
    'Miền Bắc': [
        'Hà Nội', 'Hải Phòng', 'Quảng Ninh', 'Hải Dương', 'Hưng Yên',
        'Hà Nam', 'Nam Định', 'Thái Bình', 'Ninh Bình', 'Vĩnh Phúc',
        'Bắc Ninh', 'Bắc Giang', 'Lạng Sơn', 'Cao Bằng', 'Hà Giang',
        'Lào Cai', 'Yên Bái', 'Tuyên Quang', 'Thái Nguyên', 'Bắc Kạn'
    ],
    'Miền Trung': [
        'Thanh Hóa', 'Nghệ An', 'Hà Tĩnh', 'Quảng Bình', 'Quảng Trị',
        'Thừa Thiên Huế', 'Đà Nẵng', 'Quảng Nam', 'Quảng Ngãi', 'Bình Định',
        'Phú Yên', 'Khánh Hòa', 'Ninh Thuận', 'Bình Thuận'
    ],
    'Miền Nam': [
        'TP. Hồ Chí Minh', 'Bình Dương', 'Đồng Nai', 'Bà Rịa - Vũng Tàu',
        'Tây Ninh', 'Bình Phước', 'Bình Thuận', 'Long An', 'Tiền Giang',
        'Bến Tre', 'Trà Vinh', 'Vĩnh Long', 'Đồng Tháp', 'An Giang',
        'Kiên Giang', 'Cà Mau', 'Bạc Liêu', 'Sóc Trăng', 'Cần Thơ'
    ],
    'Tây Nguyên': [
        'Đắk Lắk', 'Đắk Nông', 'Gia Lai', 'Kon Tum', 'Lâm Đồng'
    ]
}

# Categories để tìm địa điểm
CATEGORIES = [
    'Bảo tàng', 'Di tích lịch sử', 'Chùa', 'Đền', 'Nhà thờ',
    'Thác nước', 'Hồ', 'Biển', 'Núi', 'Đảo', 'Công viên',
    'Vườn quốc gia', 'Khu du lịch', 'Làng cổ', 'Phố cổ',
    'Công trình kiến trúc', 'Động', 'Hang', 'Sông', 'Đèo'
]

def get_or_create_province(ten_tinh_thanh: str, geo_tools: GeoTools) -> TinhThanh:
    """Lấy hoặc tạo tỉnh thành với geocoding"""
    province = TinhThanh.objects.filter(tenTinhThanh__icontains=ten_tinh_thanh).first()
    if not province:
        # Geocode để lấy coordinates
        geocode_result = geo_tools.geocode(f"{ten_tinh_thanh}, Việt Nam")
        latitude = geocode_result.get('latitude') if geocode_result else None
        longitude = geocode_result.get('longitude') if geocode_result else None
        
        province = TinhThanh.objects.create(
            tenTinhThanh=ten_tinh_thanh,
            viDo=latitude or 21.0,
            kinhDo=longitude or 105.0,
            moTa=f"Tỉnh thành {ten_tinh_thanh}"
        )
        print(f"[OK] Đã tạo tỉnh thành: {ten_tinh_thanh}")
    return province

def map_category_to_loai_dia_diem(category: str) -> str:
    """Map category sang loaiDiaDiem"""
    category_lower = category.lower()
    
    if any(word in category_lower for word in ['nhà hàng', 'restaurant']):
        return 'nha_hang'
    elif any(word in category_lower for word in ['khách sạn', 'hotel', 'resort']):
        return 'khach_san'
    elif any(word in category_lower for word in ['vui chơi', 'giải trí', 'amusement', 'entertainment']):
        return 'giai_tri'
    elif any(word in category_lower for word in ['mua sắm', 'chợ', 'shopping', 'market']):
        return 'mua_sam'
    else:
        return 'dia_danh'  # Mặc định

def estimate_price_from_category(category: str, name: str) -> Optional[float]:
    """Ước tính giá vé dựa trên category và tên"""
    category_lower = category.lower()
    name_lower = name.lower()
    
    # Bảo tàng: 20k - 100k
    if 'bảo tàng' in category_lower or 'museum' in category_lower:
        return 50000
    
    # Động, hang: 20k - 150k
    if 'động' in category_lower or 'hang' in category_lower or 'cave' in category_lower:
        return 80000
    
    # Vườn quốc gia: 50k - 200k
    if 'vườn quốc gia' in category_lower or 'national park' in category_lower:
        return 100000
    
    # Khu du lịch: 100k - 500k
    if 'khu du lịch' in category_lower or 'resort' in category_lower:
        return 200000
    
    # Thác nước: 10k - 50k
    if 'thác' in category_lower or 'waterfall' in category_lower:
        return 30000
    
    # Chùa, đền, nhà thờ: thường miễn phí
    if any(word in category_lower for word in ['chùa', 'đền', 'nhà thờ', 'temple', 'church']):
        return None
    
    # Công viên, bãi biển: thường miễn phí
    if any(word in category_lower for word in ['công viên', 'park', 'biển', 'beach']):
        return None
    
    return None

def enrich_place_data(
    place_data: Dict,
    geo_tools: GeoTools,
    place_searcher
) -> Dict:
    """Làm giàu dữ liệu địa điểm"""
    name = place_data.get('name', '')
    city = place_data.get('city', '')
    
    # Geocode để lấy địa chỉ và coordinates
    if not place_data.get('latitude') or not place_data.get('longitude'):
        try:
            geocode_result = geo_tools.geocode(f"{name}, {city}, Việt Nam")
            if geocode_result:
                place_data['latitude'] = geocode_result.get('latitude')
                place_data['longitude'] = geocode_result.get('longitude')
                place_data['address'] = geocode_result.get('address', '')
        except Exception as e:
            print(f"[WARN] Geocode error for {name}: {e}")
    
    # Tìm kiếm thông tin từ Place Info Searcher (chỉ nếu có)
    if place_searcher and hasattr(place_searcher, 'available') and place_searcher.available:
        try:
            searched_info = place_searcher.search_place_info(name, city)
            if searched_info.get('description'):
                place_data['description'] = searched_info['description']
            
            # Thêm thông tin bổ sung
            if searched_info.get('additional_info'):
                place_data['additional_info'] = searched_info['additional_info']
        except Exception as e:
            # Không in warning nếu không có Gemini API
            pass
    
    # Fallback: Tạo mô tả từ category và địa điểm
    if not place_data.get('description'):
        category = place_data.get('category', 'Địa danh')
        place_data['description'] = f"{name} là một {category.lower()} nổi tiếng tại {city}. Đây là điểm đến thu hút nhiều du khách với cảnh đẹp và không gian độc đáo."
    
    return place_data

def import_places_from_vector_db():
    """Import 100 địa điểm từ Vector DB"""
    print("[INFO] Bắt đầu tìm kiếm và import địa điểm từ Vector DB...\n")
    
    # Initialize tools
    vector_db = get_vector_db_agent()
    geo_tools = GeoTools()
    place_searcher = get_place_searcher() if hasattr(settings, 'GEMINI_API_KEY') else None
    
    if not vector_db or not vector_db.collection:
        print("[ERROR] Vector DB không khả dụng")
        return
    
    total_created = 0
    total_skipped = 0
    total_errors = 0
    
    # Tìm địa điểm từ các vùng khác nhau
    queries_per_region = 50  # Tăng lên để có nhiều địa điểm hơn
    all_places = []
    
    # Tìm với nhiều queries đa dạng hơn
    search_queries = [
        # Các loại địa điểm phổ biến
        'Địa điểm du lịch nổi tiếng',
        'Di tích lịch sử',
        'Danh lam thắng cảnh',
        'Bãi biển đẹp',
        'Núi cao',
        'Thác nước',
        'Chùa cổ',
        'Đền thờ',
        'Bảo tàng',
        'Vườn quốc gia',
        'Khu du lịch sinh thái',
        'Làng cổ',
        'Phố cổ',
        'Động đẹp',
        'Hồ nước',
        'Đảo du lịch',
        'Công viên',
        'Đèo đẹp',
        'Khu nghỉ dưỡng',
        'Nhà hàng nổi tiếng'
    ]
    
    print("[INFO] Đang tìm kiếm địa điểm từ Vector DB...\n")
    
    for region_name, provinces in REGIONS.items():
        print(f"\n[INFO] Tìm kiếm tại {region_name}...")
        
        for province in provinces[:8]:  # Limit provinces
            for query_base in search_queries[:10]:  # Limit queries
                if len(all_places) >= 150:  # Tìm nhiều hơn để có đủ 100 mới
                    break
                
                try:
                    query = f"{query_base} tại {province}"
                    results = vector_db.semantic_search(
                        query=query,
                        n_results=10,
                        city_filter=province
                    )
                    
                    for result in results:
                        name = result.get('name', '').strip()
                        if not name:
                            continue
                        
                        # Kiểm tra không trùng (theo tên)
                        if not any(p.get('name', '').strip().lower() == name.lower() for p in all_places):
                            all_places.append(result)
                    
                    time.sleep(0.1)  # Rate limiting
                    
                except Exception as e:
                    print(f"[WARN] Error searching {query_base} in {province}: {e}")
                    continue
            
            if len(all_places) >= 150:
                break
        
        if len(all_places) >= 150:
            break
    
    print(f"\n[INFO] Đã tìm thấy {len(all_places)} địa điểm. Bắt đầu import...\n")
    
    # Import vào database
    imported_count = 0
    for idx, place_data in enumerate(all_places[:150], 1):
        try:
            name = place_data.get('name', '').strip()
            city = place_data.get('city', '') or place_data.get('province', '')
            
            if not name:
                print(f"[{idx}/100] [SKIP] Không có tên địa điểm")
                total_skipped += 1
                continue
            
            # Tìm hoặc tạo tỉnh thành
            province_obj = None
            if city:
                province_obj = get_or_create_province(city, geo_tools)
            else:
                # Thử tìm trong các tỉnh đã biết
                for province_name in sum(REGIONS.values(), []):
                    province_obj = TinhThanh.objects.filter(
                        tenTinhThanh__icontains=province_name
                    ).first()
                    if province_obj:
                        break
            
            if not province_obj:
                # Tạo tỉnh mặc định
                province_obj = TinhThanh.objects.filter(tenTinhThanh='Hà Nội').first()
                if not province_obj:
                    province_obj = get_or_create_province('Hà Nội', geo_tools)
            
            # Kiểm tra đã tồn tại chưa
            existing = DiaDiem.objects.filter(
                tenDiaDiem__iexact=name,
                maTinhThanh=province_obj
            ).first()
            
            if existing:
                print(f"[{idx}/100] [SKIP] Đã tồn tại: {name} ({existing.maDiaDiem})")
                total_skipped += 1
                continue
            
            # Làm giàu dữ liệu
            enriched_data = enrich_place_data(place_data.copy(), geo_tools, place_searcher)
            
            # Map category
            category = place_data.get('category', 'Địa danh')
            loai_dia_diem = map_category_to_loai_dia_diem(category)
            
            # Ước tính giá vé
            gia_ve = place_data.get('price', 0)
            if not gia_ve or gia_ve == 0:
                gia_ve = estimate_price_from_category(category, name)
            
            # Tạo địa điểm
            place = DiaDiem.objects.create(
                tenDiaDiem=name,
                maTinhThanh=province_obj,
                moTa=enriched_data.get('description', '') or place_data.get('description', '') or f"Địa điểm {name} tại {city}",
                diaChi=enriched_data.get('address', '') or place_data.get('address', '') or f"{city}, Việt Nam",
                loaiDiaDiem=loai_dia_diem,
                viDo=enriched_data.get('latitude') or place_data.get('latitude'),
                kinhDo=enriched_data.get('longitude') or place_data.get('longitude'),
                giaVe=gia_ve,
                danhGiaTrungBinh=place_data.get('rating', 0.0) or 0.0,
                soLuotDanhGia=place_data.get('reviews', 0) or 0,
                trangThai='active',
                dacDiem=json.dumps({
                    'category': category,
                    'source': place_data.get('source', 'vector_db'),
                    'image_url': place_data.get('image_url'),
                    'province': place_data.get('province', city)
                }, ensure_ascii=False) if any([category, place_data.get('source'), place_data.get('image_url')]) else ''
            )
            
            # Thêm hình ảnh nếu có
            image_url = place_data.get('image_url')
            if image_url:
                try:
                    HinhAnhDiaDiem.objects.create(
                        maDiaDiem=place,
                        urlHinhAnh=image_url,
                        laChinh=True,
                        moTa=f"Hình ảnh {name}"
                    )
                except Exception as e:
                    print(f"[WARN] Không thể thêm hình ảnh: {e}")
            
            print(f"[{idx}/{len(all_places[:150])}] [OK] Đã tạo: {name} ({place.maDiaDiem}) - {city}")
            total_created += 1
            imported_count += 1
            
            # Đủ 100 địa điểm mới thì dừng
            if imported_count >= 100:
                print(f"\n[INFO] Đã đạt đủ 100 địa điểm mới!")
                break
            
            time.sleep(0.3)  # Rate limiting
            
        except Exception as e:
            print(f"[{idx}/100] [ERROR] {name}: {e}")
            total_errors += 1
    
    print(f"\n{'='*60}")
    print(f"[OK] HOÀN TẤT!")
    print(f"   - Đã tạo: {total_created} địa điểm")
    print(f"   - Đã bỏ qua: {total_skipped} địa điểm")
    print(f"   - Lỗi: {total_errors} địa điểm")
    print(f"{'='*60}")

if __name__ == '__main__':
    import_places_from_vector_db()

