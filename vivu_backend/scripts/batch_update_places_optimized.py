"""
Optimized batch update script for places from row 58 onwards
- Only geocode places with missing coordinates
- Batch process efficiently
- Better error handling and progress tracking
"""
import os
import sys
import django
import sqlite3
import json
import requests
import time
from typing import Optional, Dict, Any, Tuple
from datetime import datetime
from pathlib import Path

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    if sys.stderr.encoding != 'utf-8':
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)

# Setup Django - script is in scripts/ folder
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vivu_core.settings')
django.setup()

from django.conf import settings

# Database path
db_path = PROJECT_ROOT / 'vivudb.sqlite3'
if not db_path.exists():
    db_path = PROJECT_ROOT.parent / 'vivudb.sqlite3'
    if not db_path.exists():
        print(f"Error: Cannot find vivudb.sqlite3")
        print(f"Tried: {PROJECT_ROOT / 'vivudb.sqlite3'}")
        print(f"Tried: {PROJECT_ROOT.parent / 'vivudb.sqlite3'}")
        sys.exit(1)

db_path = str(db_path)
print(f"Using database: {db_path}")

# Configuration
GEOCODE_DELAY = 0.2  # Delay between geocoding requests (seconds) - increased for stability
BATCH_SIZE = 50  # Smaller batch size for better control
COMMIT_INTERVAL = 50  # Commit every N updates

# Statistics
stats = {
    'total': 0,
    'updated_coords': 0,
    'updated_type': 0,
    'updated_amenities': 0,
    'updated_description': 0,
    'updated_hours': 0,
    'errors': 0,
    'skipped': 0
}


def geocode_with_vietmap(address: str) -> Optional[Dict[str, float]]:
    """Geocode using VietMap API"""
    vietmap_api_key = getattr(settings, 'VIETMAP_API_KEY', None) or os.getenv('VIETMAP_API_KEY')
    if not vietmap_api_key:
        return None
    
    try:
        base_url = "https://maps.vietmap.vn/api"
        search_url = f"{base_url}/search/v3"
        params = {
            'apikey': vietmap_api_key,
            'text': address
        }
        response = requests.get(search_url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and data:
                first = data[0]
                ref_id = first.get('ref_id')
                if ref_id:
                    place_url = f"{base_url}/place/v3"
                    place_params = {
                        'apikey': vietmap_api_key,
                        'refid': ref_id
                    }
                    place_resp = requests.get(place_url, params=place_params, timeout=10)
                    if place_resp.status_code == 200:
                        place_data = place_resp.json()
                        lat = place_data.get('lat') or place_data.get('latitude') or place_data.get('y')
                        lon = place_data.get('lng') or place_data.get('lon') or place_data.get('longitude') or place_data.get('x')
                        if lat and lon:
                            return {'lat': float(lat), 'lon': float(lon)}
    except Exception as e:
        pass
    
    return None


def geocode_with_osm(address: str) -> Optional[Dict[str, float]]:
    """Geocode using OpenStreetMap Nominatim API"""
    try:
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': address,
            'format': 'json',
            'limit': 1,
            'countrycodes': 'vn'
        }
        headers = {
            'User-Agent': 'TravelPlanner/1.0'
        }
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                result = data[0]
                return {
                    'lat': float(result['lat']),
                    'lon': float(result['lon'])
                }
    except Exception as e:
        pass
    
    return None


def geocode_address(address: str, province_name: str = "") -> Optional[Dict[str, float]]:
    """Geocode address with fallback - only if really needed"""
    if not address or address.strip() == '':
        return None
    
    # Try with full address including province
    full_address = f"{address}, {province_name}, Việt Nam" if province_name else f"{address}, Việt Nam"
    
    # Try VietMap first
    coords = geocode_with_vietmap(full_address)
    if coords:
        time.sleep(GEOCODE_DELAY)
        return coords
    
    # Fallback to OSM
    time.sleep(GEOCODE_DELAY)
    coords = geocode_with_osm(full_address)
    if coords:
        return coords
    
    return None


def fix_loai_dia_diem(ten_dia_diem: str, loai_hien_tai: str, dia_chi: str) -> str:
    """Fix incorrect loaiDiaDiem based on name and address"""
    ten_lower = ten_dia_diem.lower()
    dia_chi_lower = dia_chi.lower()
    
    # Keywords for different types
    khach_san_keywords = ['khách sạn', 'hotel', 'resort', 'condotel', 'homestay', 'nhà nghỉ', 'lưu trú']
    nha_hang_keywords = ['nhà hàng', 'restaurant', 'quán ăn', 'café', 'cafe', 'bar', 'pub', 'bistro']
    giai_tri_keywords = ['vui chơi', 'giải trí', 'công viên', 'park', 'khu vui chơi', 'amusement', 'entertainment']
    mua_sam_keywords = ['chợ', 'market', 'trung tâm thương mại', 'mall', 'siêu thị', 'supermarket', 'shopping']
    dia_danh_keywords = ['chùa', 'đền', 'lăng', 'bảo tàng', 'museum', 'temple', 'pagoda', 'di tích', 'lịch sử']
    
    # Check if current type seems wrong
    if loai_hien_tai == 'dia_danh':
        if any(kw in ten_lower or kw in dia_chi_lower for kw in khach_san_keywords):
            return 'khach_san'
        elif any(kw in ten_lower or kw in dia_chi_lower for kw in nha_hang_keywords):
            return 'nha_hang'
        elif any(kw in ten_lower or kw in dia_chi_lower for kw in giai_tri_keywords):
            return 'giai_tri'
        elif any(kw in ten_lower or kw in dia_chi_lower for kw in mua_sam_keywords):
            return 'mua_sam'
    
    return loai_hien_tai


def generate_amenities(loai_dia_diem: str, ten_dia_diem: str) -> str:
    """Generate basic amenities based on type"""
    ten_lower = ten_dia_diem.lower()
    
    if loai_dia_diem == 'khach_san':
        amenities = ['Wifi', 'Bãi đỗ xe', 'Điều hòa', 'TV', 'Tủ lạnh']
        if 'resort' in ten_lower:
            amenities.extend(['Hồ bơi', 'Spa', 'Nhà hàng', 'Phòng tập gym'])
        return ', '.join(amenities)
    elif loai_dia_diem == 'nha_hang':
        return 'Wifi, Bãi đỗ xe, Điều hòa, Phục vụ tại bàn'
    elif loai_dia_diem == 'giai_tri':
        return 'Bãi đỗ xe, Khu vui chơi, Dịch vụ giải trí'
    elif loai_dia_diem == 'mua_sam':
        return 'Bãi đỗ xe, Nhiều cửa hàng, Dịch vụ mua sắm'
    elif loai_dia_diem == 'dia_danh':
        return 'Bãi đỗ xe, Khu vực tham quan'
    
    return ''


def improve_description(ten_dia_diem: str, loai_dia_diem: str, dia_chi: str, mo_ta_hien_tai: str) -> str:
    """Improve description if it's too generic or missing"""
    if mo_ta_hien_tai and len(mo_ta_hien_tai.strip()) > 50:
        return mo_ta_hien_tai
    
    province = dia_chi.split(',')[-1].strip() if ',' in dia_chi else ''
    
    if loai_dia_diem == 'khach_san':
        return f"{ten_dia_diem} là một cơ sở lưu trú tại {province}, cung cấp dịch vụ nghỉ dưỡng và các tiện nghi hiện đại cho du khách."
    elif loai_dia_diem == 'nha_hang':
        return f"{ten_dia_diem} là nhà hàng tại {province}, phục vụ các món ăn đa dạng và hấp dẫn."
    elif loai_dia_diem == 'giai_tri':
        return f"{ten_dia_diem} là điểm vui chơi giải trí tại {province}, mang đến nhiều hoạt động thú vị cho du khách."
    elif loai_dia_diem == 'mua_sam':
        return f"{ten_dia_diem} là điểm mua sắm tại {province}, cung cấp nhiều sản phẩm và dịch vụ đa dạng."
    elif loai_dia_diem == 'dia_danh':
        return f"{ten_dia_diem} là địa danh nổi tiếng tại {province}, thu hút nhiều du khách đến tham quan."
    
    return mo_ta_hien_tai if mo_ta_hien_tai else f"{ten_dia_diem} tại {province}"


def update_place(cursor: sqlite3.Cursor, rowid: int, row_data: Tuple, province_name: str) -> bool:
    """Update a single place"""
    try:
        ma_dia_diem, ten_dia_diem, dia_chi, ma_tinh_thanh, loai_dia_diem, vi_do, kinh_do, \
        dien_thoai, website, mo_ta, gio_mo_cua, gio_dong_cua, gia_ve, danh_gia, so_luot_danh_gia, \
        tien_nghi, dac_diem = row_data
        
        updates = {}
        needs_update = False
        
        # 1. Fix coordinates if missing or zero (ONLY geocode if needed)
        if not vi_do or vi_do == 0.0 or not kinh_do or kinh_do == 0.0:
            if dia_chi and dia_chi.strip():
                coords = geocode_address(dia_chi, province_name)
                if coords:
                    updates['viDo'] = coords['lat']
                    updates['kinhDo'] = coords['lon']
                    stats['updated_coords'] += 1
                    needs_update = True
        
        # 2. Fix loaiDiaDiem if seems incorrect
        fixed_loai = fix_loai_dia_diem(ten_dia_diem, loai_dia_diem, dia_chi)
        if fixed_loai != loai_dia_diem:
            updates['loaiDiaDiem'] = fixed_loai
            stats['updated_type'] += 1
            needs_update = True
            loai_dia_diem = fixed_loai
        
        # 3. Add amenities if missing
        if not tien_nghi or tien_nghi.strip() == '':
            amenities = generate_amenities(loai_dia_diem, ten_dia_diem)
            if amenities:
                updates['tienNghi'] = amenities
                stats['updated_amenities'] += 1
                needs_update = True
        
        # 4. Improve description if too generic
        if not mo_ta or len(mo_ta.strip()) < 50:
            new_mo_ta = improve_description(ten_dia_diem, loai_dia_diem, dia_chi, mo_ta or '')
            if new_mo_ta != mo_ta:
                updates['moTa'] = new_mo_ta
                stats['updated_description'] += 1
                needs_update = True
        
        # 5. Set default values for missing fields
        if not gio_mo_cua or gio_mo_cua.strip() == '':
            if loai_dia_diem == 'khach_san':
                updates['gioMoCua'] = '14:00'
            elif loai_dia_diem == 'nha_hang':
                updates['gioMoCua'] = '10:00'
            else:
                updates['gioMoCua'] = '08:00'
            stats['updated_hours'] += 1
            needs_update = True
        
        if not gio_dong_cua or gio_dong_cua.strip() == '':
            if loai_dia_diem == 'khach_san':
                updates['gioDongCua'] = '12:00'
            elif loai_dia_diem == 'nha_hang':
                updates['gioDongCua'] = '22:00'
            else:
                updates['gioDongCua'] = '18:00'
            if 'gioMoCua' not in updates:
                stats['updated_hours'] += 1
            needs_update = True
        
        if gia_ve is None:
            updates['giaVe'] = 0.0
            needs_update = True
        
        if danh_gia is None:
            updates['danhGiaTrungBinh'] = 0.0
            needs_update = True
        
        if so_luot_danh_gia is None:
            updates['soLuotDanhGia'] = 0
            needs_update = True
        
        # Execute update if needed
        if needs_update:
            set_clause = ', '.join([f"{k} = ?" for k in updates.keys()])
            values = list(updates.values()) + [rowid]
            cursor.execute(f"UPDATE DIADIEM SET {set_clause} WHERE rowid = ?", values)
            return True
        
        return False
        
    except Exception as e:
        print(f"Error updating rowid {rowid}: {e}")
        stats['errors'] += 1
        return False


def batch_update_places(start_rowid: int = 58, limit: Optional[int] = None):
    """Batch update places from start_rowid onwards"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get total count
    cursor.execute('SELECT COUNT(*) FROM DIADIEM WHERE rowid >= ?', (start_rowid,))
    total_count = cursor.fetchone()[0]
    
    if limit:
        total_count = min(total_count, limit)
    
    print("="*60)
    print(f"OPTIMIZED BATCH UPDATE PLACES")
    print("="*60)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Starting from rowid: {start_rowid}")
    print(f"Total places to process: {total_count:,}")
    print(f"Batch size: {BATCH_SIZE}")
    print(f"Commit interval: {COMMIT_INTERVAL}")
    print("="*60)
    
    # Pre-load province names
    cursor.execute('SELECT maTinhThanh, tenTinhThanh FROM TINHTHANH')
    provinces = {row[0]: row[1] for row in cursor.fetchall()}
    
    processed = 0
    updated = 0
    last_commit = 0
    
    try:
        offset = 0
        while True:
            # Get batch with rowid
            query = '''
                SELECT rowid, maDiaDiem, tenDiaDiem, diaChi, maTinhThanh, loaiDiaDiem, 
                       viDo, kinhDo, dienThoai, website, moTa, gioMoCua, gioDongCua,
                       giaVe, danhGiaTrungBinh, soLuotDanhGia, tienNghi, dacDiem
                FROM DIADIEM 
                WHERE rowid >= ?
                ORDER BY rowid
                LIMIT ? OFFSET ?
            '''
            cursor.execute(query, (start_rowid, BATCH_SIZE, offset))
            batch = cursor.fetchall()
            
            if not batch:
                break
            
            # Process batch
            for row in batch:
                rowid = row[0]
                row_data = row[1:]  # Skip rowid
                ma_tinh_thanh = row_data[3]
                province_name = provinces.get(ma_tinh_thanh, "")
                
                processed += 1
                stats['total'] += 1
                
                if update_place(cursor, rowid, row_data, province_name):
                    updated += 1
                    last_commit += 1
                
                # Commit periodically
                if last_commit >= COMMIT_INTERVAL:
                    conn.commit()
                    last_commit = 0
                
                # Progress update
                if processed % 100 == 0:
                    elapsed = time.time() - start_time if 'start_time' in locals() else 0
                    rate = processed / elapsed if elapsed > 0 else 0
                    remaining = (total_count - processed) / rate if rate > 0 else 0
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Processed: {processed:,}/{total_count:,} ({processed*100/total_count:.1f}%) | "
                          f"Updated: {updated:,} | Coords: {stats['updated_coords']:,} | Type: {stats['updated_type']:,} | "
                          f"Amenities: {stats['updated_amenities']:,} | Desc: {stats['updated_description']:,} | "
                          f"Hours: {stats['updated_hours']:,} | Errors: {stats['errors']:,} | "
                          f"Rate: {rate:.1f}/s | ETA: {remaining/60:.1f}min")
            
            # Commit batch
            conn.commit()
            last_commit = 0
            offset += BATCH_SIZE
            
            if limit and processed >= limit:
                break
            
            # Small delay between batches
            time.sleep(0.1)
    
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Committing progress...")
        conn.commit()
    except Exception as e:
        print(f"\n\nError in batch processing: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
    finally:
        conn.commit()
        conn.close()
        
        print("\n" + "="*60)
        print("BATCH UPDATE COMPLETED")
        print("="*60)
        print(f"End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total processed: {stats['total']:,}")
        print(f"Total updated: {updated:,}")
        print(f"Coordinates updated: {stats['updated_coords']:,}")
        print(f"Type fixed: {stats['updated_type']:,}")
        print(f"Amenities added: {stats['updated_amenities']:,}")
        print(f"Descriptions improved: {stats['updated_description']:,}")
        print(f"Hours updated: {stats['updated_hours']:,}")
        print(f"Errors: {stats['errors']:,}")
        print("="*60)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Optimized batch update places from row 58 onwards')
    parser.add_argument('--start', type=int, default=58, help='Starting rowid (default: 58)')
    parser.add_argument('--limit', type=int, default=None, help='Limit number of places to process')
    parser.add_argument('--test', action='store_true', help='Test mode: process only 100 places')
    
    args = parser.parse_args()
    
    start_time = time.time()
    
    if args.test:
        print("TEST MODE: Processing only 100 places")
        batch_update_places(start_rowid=args.start, limit=100)
    else:
        batch_update_places(start_rowid=args.start, limit=args.limit)

