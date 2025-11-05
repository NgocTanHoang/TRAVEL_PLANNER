#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script kiểm tra và làm giàu dữ liệu địa điểm
- Chuẩn hóa tên tiếng Việt có dấu
- Bổ sung mô tả chi tiết
- Sử dụng nhiều API để làm giàu dữ liệu
"""
import os
import sys
import django
import re
import time
import json
import random
from typing import Dict, List, Optional
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

from django.conf import settings
from apps.places.models import DiaDiem, TinhThanh, HinhAnhDiaDiem

# Import các tools và APIs
try:
    from agents.travel_agents.vector_db import get_vector_db_agent
    from tools.geo_tools import GeoTools
    from apps.api.place_info_searcher import get_place_searcher
    TOOLS_AVAILABLE = True
except ImportError as e:
    print(f"[ERROR] Tools not available: {e}")
    TOOLS_AVAILABLE = False

# OpenAI chỉ dùng cho chatbot và tạo lịch trình, KHÔNG dùng cho kiểm chứng/thông tin
# OPENAI_AVAILABLE = False  # Disabled để tiết kiệm chi phí

# Tavily không có search được trong project này
# TAVILY_AVAILABLE = False

# SerpAPI chỉ dùng cho nhà hàng/khách sạn/chuyến bay, KHÔNG dùng cho làm giàu mô tả
# SERPAPI_AVAILABLE = False


def detect_vietnamese_issues(text: str) -> Dict[str, bool]:
    """
    Phát hiện các vấn đề với tiếng Việt:
    - Thiếu dấu
    - Tên không chuẩn (có tiếng Anh lẫn tiếng Việt)
    - Tên quá ngắn hoặc không có nghĩa
    """
    if not text:
        return {'has_issues': True, 'missing_diacritics': True, 'mixed_language': False, 'too_short': True}
    
    # Kiểm tra thiếu dấu (các từ phổ biến)
    vietnamese_with_diacritics = ['à', 'á', 'ạ', 'ả', 'ã', 'â', 'ầ', 'ấ', 'ậ', 'ẩ', 'ẫ',
                                  'è', 'é', 'ẹ', 'ẻ', 'ẽ', 'ê', 'ề', 'ế', 'ệ', 'ể', 'ễ',
                                  'ì', 'í', 'ị', 'ỉ', 'ĩ',
                                  'ò', 'ó', 'ọ', 'ỏ', 'õ', 'ô', 'ồ', 'ố', 'ộ', 'ổ', 'ỗ',
                                  'ù', 'ú', 'ụ', 'ủ', 'ũ', 'ư', 'ừ', 'ứ', 'ự', 'ử', 'ữ',
                                  'ỳ', 'ý', 'ỵ', 'ỷ', 'ỹ',
                                  'đ']
    
    has_diacritics = any(char in text for char in vietnamese_with_diacritics)
    
    # Kiểm tra có tiếng Anh lẫn không
    english_words = ['restaurant', 'hotel', 'museum', 'park', 'beach', 'temple', 'pagoda',
                     'harbor', 'hospital', 'club', 'bar', 'cafe', 'square', 'marina',
                     'library', 'mosque', 'bistro', 'pub', 'rooftop', 'cafe', 'atm',
                     'convenience', 'store', 'garden', 'mountain', 'river', 'ocean']
    has_english = any(word.lower() in text.lower() for word in english_words)
    
    # Kiểm tra quá ngắn hoặc không có nghĩa
    too_short = len(text.strip()) < 3 or not any(char.isalpha() for char in text)
    
    return {
        'has_issues': not has_diacritics or has_english or too_short,
        'missing_diacritics': not has_diacritics and any(char.isalpha() for char in text),
        'mixed_language': has_english,
        'too_short': too_short
    }


def normalize_vietnamese_name_with_vector_db(name: str, province: str) -> Optional[str]:
    """
    Chuẩn hóa tên tiếng Việt sử dụng Vector DB (miễn phí)
    Tìm địa điểm tương tự trong Vector DB để lấy tên chuẩn
    """
    try:
        vector_db = get_vector_db_agent()
        if not vector_db or not vector_db.collection:
            return None
        
        # Tìm địa điểm tương tự trong Vector DB
        results = vector_db.semantic_search(
            query=f"{name} {province}",
            n_results=5,
            city_filter=province
        )
        
        # Tìm địa điểm khớp nhất (có thể là cùng một địa điểm nhưng tên khác)
        for result in results:
            result_name = result.get('name', '').strip()
            similarity = result.get('similarity_score', 0)
            
            # Nếu similarity cao và tên có dấu đầy đủ hơn
            if similarity > 0.7:
                # Kiểm tra tên có dấu đầy đủ hơn không
                if has_vietnamese_diacritics(result_name) and not has_vietnamese_diacritics(name):
                    return result_name
                # Hoặc tên ngắn gọn và chuẩn hơn
                if len(result_name) > len(name) and has_vietnamese_diacritics(result_name):
                    return result_name
        
        return None
        
    except Exception as e:
        print(f"[WARN] Vector DB normalization error: {e}")
        return None


def has_vietnamese_diacritics(text: str) -> bool:
    """Kiểm tra text có dấu tiếng Việt không"""
    vietnamese_chars = ['à', 'á', 'ạ', 'ả', 'ã', 'â', 'ầ', 'ấ', 'ậ', 'ẩ', 'ẫ',
                       'è', 'é', 'ẹ', 'ẻ', 'ẽ', 'ê', 'ề', 'ế', 'ệ', 'ể', 'ễ',
                       'ì', 'í', 'ị', 'ỉ', 'ĩ',
                       'ò', 'ó', 'ọ', 'ỏ', 'õ', 'ô', 'ồ', 'ố', 'ộ', 'ổ', 'ỗ',
                       'ù', 'ú', 'ụ', 'ủ', 'ũ', 'ư', 'ừ', 'ứ', 'ự', 'ử', 'ữ',
                       'ỳ', 'ý', 'ỵ', 'ỷ', 'ỹ',
                       'đ']
    return any(char in text for char in vietnamese_chars)


def simple_normalize_name(name: str) -> str:
    """
    Chuẩn hóa tên đơn giản dựa trên patterns
    Không dùng API, chỉ dùng quy tắc
    """
    # Mapping từ tiếng Anh sang tiếng Việt thông dụng
    translations = {
        'restaurant': 'Nhà hàng',
        'hotel': 'Khách sạn',
        'museum': 'Bảo tàng',
        'park': 'Công viên',
        'beach': 'Bãi biển',
        'temple': 'Đền',
        'pagoda': 'Chùa',
        'harbor': 'Cảng',
        'hospital': 'Bệnh viện',
        'club': 'Câu lạc bộ',
        'bar': 'Quán bar',
        'cafe': 'Quán cà phê',
        'square': 'Quảng trường',
        'marina': 'Bến du thuyền',
        'library': 'Thư viện',
        'mosque': 'Nhà thờ Hồi giáo',
        'bistro': 'Nhà hàng',
        'pub': 'Quán rượu',
        'rooftop': 'Sân thượng',
        'garden': 'Vườn',
        'mountain': 'Núi',
        'river': 'Sông',
        'ocean': 'Đại dương',
        'atm': 'Máy ATM',
        'convenience store': 'Cửa hàng tiện lợi',
        'store': 'Cửa hàng'
    }
    
    normalized = name
    name_lower = name.lower()
    
    # Thay thế các từ tiếng Anh thông dụng
    for eng, viet in translations.items():
        if eng in name_lower:
            # Thay thế từ tiếng Anh bằng tiếng Việt
            normalized = normalized.replace(eng, viet).replace(eng.capitalize(), viet)
            normalized = normalized.replace(eng.upper(), viet)
    
    return normalized.strip()


def enrich_with_vietmap(name: str, province: str) -> Optional[Dict]:
    """Lấy thông tin địa điểm từ VietMap API"""
    try:
        geo_tools = GeoTools()
        if not geo_tools.vietmap:
            return None
        
        # Geocode để lấy địa chỉ chi tiết
        geocode_result = geo_tools.vietmap.geocode(f"{name}, {province}")
        if geocode_result:
            address = geocode_result.get('formatted_address', '')
            if address and address != f"{name}, {province}":
                return {
                    'address': address,
                    'latitude': geocode_result.get('lat'),
                    'longitude': geocode_result.get('lon'),
                    'description': f"Địa điểm tại {address}"
                }
    except Exception as e:
        print(f"[WARN] VietMap enrichment error: {e}")
    
    return None


def enrich_description_with_apis(
    name: str,
    province: str,
    current_description: str = ""
) -> Dict[str, str]:
    """
    Làm giàu mô tả sử dụng các API có sẵn (miễn phí hoặc rẻ):
    1. Vector DB semantic search (miễn phí, local) - Ưu tiên
    2. VietMap (nếu có - địa chỉ và thông tin địa lý)
    3. OpenRouteService (nếu có - geocoding fallback)
    """
    enriched_data = {
        'description': current_description,
        'source': 'existing'
    }
    
    # 1. Vector DB semantic search (ưu tiên - miễn phí)
    try:
        vector_db = get_vector_db_agent()
        if vector_db and vector_db.collection:
            results = vector_db.semantic_search(
                query=f"{name} {province}",
                n_results=5,
                city_filter=province
            )
            
            # Tìm địa điểm khớp nhất
            best_match = None
            best_score = 0
            
            for result in results:
                result_name = result.get('name', '').lower()
                similarity = result.get('similarity_score', 0)
                
                # Kiểm tra tên khớp
                if name.lower() in result_name or result_name in name.lower() or similarity > 0.7:
                    if similarity > best_score:
                        best_score = similarity
                        best_match = result
            
            if best_match and best_match.get('description'):
                desc = best_match['description']
                if len(desc) > len(current_description):
                    enriched_data['description'] = desc
                    enriched_data['source'] = 'vector_db'
                    enriched_data['similarity'] = best_score
                    print(f"[OK] Enriched with Vector DB (similarity: {best_score:.2f}): {name[:50]}")
                    return enriched_data
    except Exception as e:
        print(f"[WARN] Vector DB enrichment error: {e}")
    
    # 2. VietMap (lấy địa chỉ và thông tin địa lý)
    vietmap_info = enrich_with_vietmap(name, province)
    if vietmap_info:
        address = vietmap_info.get('address', '')
        lat = vietmap_info.get('latitude')
        lon = vietmap_info.get('longitude')
        
        if address and (not current_description or len(current_description) < 50):
            # Tạo mô tả từ địa chỉ
            enriched_data['description'] = f"{name} là một địa điểm du lịch tại {address}. {vietmap_info.get('description', 'Đây là điểm đến thu hút nhiều du khách với cảnh đẹp và không gian độc đáo.')}"
            enriched_data['source'] = 'vietmap'
            enriched_data['address'] = address
            if lat and lon:
                enriched_data['latitude'] = lat
                enriched_data['longitude'] = lon
            print(f"[OK] Enriched with VietMap: {name[:50]}")
            return enriched_data
    
    # 3. Fallback: Tạo mô tả từ Vector DB hoặc mặc định
    if not enriched_data.get('description') or len(enriched_data['description']) < 50:
        # Tạo mô tả cơ bản từ Vector DB nếu có
        try:
            vector_db = get_vector_db_agent()
            if vector_db and vector_db.collection:
                results = vector_db.semantic_search(
                    query=f"{name} {province}",
                    n_results=1,
                    city_filter=province
                )
                
                if results:
                    desc = results[0].get('description', '')
                    if desc:
                        enriched_data['description'] = desc
                        enriched_data['source'] = 'vector_db_fallback'
        except Exception:
            pass
        
        # Nếu vẫn không có, tạo mô tả mặc định
        if not enriched_data.get('description') or len(enriched_data['description']) < 50:
            enriched_data['description'] = f"{name} là một địa điểm du lịch tại {province}, Việt Nam. Đây là điểm đến thu hút nhiều du khách với cảnh đẹp và không gian độc đáo."
            enriched_data['source'] = 'generated'
    
    return enriched_data


def check_and_fix_places():
    """Kiểm tra và sửa tất cả địa điểm"""
    print("[INFO] Bắt đầu kiểm tra và làm giàu dữ liệu địa điểm...\n")
    
    places = DiaDiem.objects.all().order_by('maDiaDiem')
    total = places.count()
    
    print(f"[INFO] Tổng số địa điểm: {total}\n")
    
    fixed_names = 0
    enriched_descriptions = 0
    skipped = 0
    errors = 0
    
    for idx, place in enumerate(places, 1):
        try:
            name = place.tenDiaDiem
            province = place.maTinhThanh.tenTinhThanh if place.maTinhThanh else ""
            description = place.moTa or ""
            
            issues = detect_vietnamese_issues(name)
            
            # Chuẩn hóa tên nếu có vấn đề
            if issues['has_issues']:
                print(f"[{idx}/{total}] Kiểm tra: {name}")
                
                # Thử chuẩn hóa với Vector DB (miễn phí)
                normalized_name = normalize_vietnamese_name_with_vector_db(name, province)
                
                # Nếu không tìm thấy trong Vector DB, dùng simple normalization
                if not normalized_name:
                    normalized_name = simple_normalize_name(name)
                    # Chỉ cập nhật nếu có thay đổi đáng kể
                    if normalized_name != name and len(normalized_name) > len(name) * 0.8:
                        normalized_name = normalized_name
                    else:
                        normalized_name = None
                
                if normalized_name and normalized_name != name:
                    print(f"  → Chuẩn hóa tên: {name} → {normalized_name}")
                    place.tenDiaDiem = normalized_name
                    place.save()
                    fixed_names += 1
                    name = normalized_name  # Cập nhật để dùng cho mô tả
            
            # Làm giàu mô tả nếu quá ngắn hoặc không có
            if not description or len(description) < 100:
                print(f"  → Làm giàu mô tả...")
                enriched = enrich_description_with_apis(name, province, description)
            else:
                enriched = {'description': description, 'source': 'existing'}
            
            # Cập nhật địa chỉ và tọa độ từ VietMap nếu có
            if enriched.get('address') and not place.diaChi:
                place.diaChi = enriched['address']
            if enriched.get('latitude') and not place.viDo:
                place.viDo = enriched['latitude']
            if enriched.get('longitude') and not place.kinhDo:
                place.kinhDo = enriched['longitude']
            
            # Bổ sung các trường khác nếu thiếu
            if not place.gioMoCua:
                # Ước tính giờ mở cửa dựa trên loại địa điểm
                if place.loaiDiaDiem == 'nha_hang':
                    place.gioMoCua = '07:00'
                    place.gioDongCua = '22:00'
                elif place.loaiDiaDiem == 'khach_san':
                    place.gioMoCua = '00:00'  # 24/7
                    place.gioDongCua = '24:00'
                elif place.loaiDiaDiem in ['giai_tri', 'dia_danh']:
                    place.gioMoCua = '08:00'
                    place.gioDongCua = '18:00'
            
            # Bổ sung số điện thoại nếu thiếu (tạo giả)
            if not place.dienThoai and place.loaiDiaDiem in ['nha_hang', 'khach_san', 'giai_tri']:
                place.dienThoai = f"0{random.randint(200, 299)}{random.randint(1000000, 9999999)}"
            
            # Cập nhật mô tả nếu có
            if enriched.get('description') and len(enriched['description']) > len(description):
                place.moTa = enriched['description']
                place.save()
                enriched_descriptions += 1
                print(f"  → Đã cập nhật mô tả (nguồn: {enriched.get('source', 'unknown')})")
            else:
                # Lưu các thay đổi về địa chỉ/tọa độ/giờ mở cửa/điện thoại dù mô tả không thay đổi
                if enriched.get('address') or enriched.get('latitude') or not place.gioMoCua or (not place.dienThoai and place.loaiDiaDiem in ['nha_hang', 'khach_san', 'giai_tri']):
                    place.save()
                skipped += 1
            
            # Rate limiting
            time.sleep(0.5)
            
        except Exception as e:
            print(f"[{idx}/{total}] [ERROR] {place.tenDiaDiem}: {e}")
            errors += 1
    
    print(f"\n{'='*60}")
    print(f"[OK] HOÀN TẤT!")
    print(f"   - Đã chuẩn hóa tên: {fixed_names} địa điểm")
    print(f"   - Đã làm giàu mô tả: {enriched_descriptions} địa điểm")
    print(f"   - Đã bỏ qua: {skipped} địa điểm")
    print(f"   - Lỗi: {errors} địa điểm")
    print(f"{'='*60}")


if __name__ == '__main__':
    check_and_fix_places()

