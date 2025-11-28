"""
Phân tích chất lượng dữ liệu địa điểm
- Kiểm tra số lượng địa điểm theo tỉnh và loại
- Đánh giá mức độ hoàn chỉnh của dữ liệu
- Xác định tỉnh nào đủ dữ liệu để tạo lịch trình cho các phong cách du lịch
"""
import os
import sys
import django
import sqlite3
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    if sys.stderr.encoding != 'utf-8':
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)

# Setup Django
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vivu_core.settings')
django.setup()

from django.db import connection

# Database path
db_path = PROJECT_ROOT / 'vivudb.sqlite3'
if not db_path.exists():
    print(f"Error: Cannot find vivudb.sqlite3 at {db_path}")
    sys.exit(1)

# Các loại địa điểm cần thiết cho từng phong cách du lịch
TRAVEL_STYLE_REQUIREMENTS = {
    'standard': {
        'khach_san': 5,      # Tối thiểu 5 khách sạn
        'nha_hang': 10,      # Tối thiểu 10 nhà hàng
        'dia_danh': 15,      # Tối thiểu 15 điểm tham quan
        'giai_tri': 5,       # Tối thiểu 5 điểm giải trí
        'mua_sam': 3,        # Tối thiểu 3 điểm mua sắm
    },
    'budget': {
        'khach_san': 3,
        'nha_hang': 8,
        'dia_danh': 12,
        'giai_tri': 3,
        'mua_sam': 2,
    },
    'luxury': {
        'khach_san': 3,      # Ít hơn nhưng chất lượng cao
        'nha_hang': 8,
        'dia_danh': 10,
        'giai_tri': 5,
        'mua_sam': 3,
    },
    'adventure': {
        'khach_san': 3,
        'nha_hang': 5,
        'dia_danh': 20,      # Nhiều điểm tham quan hơn
        'giai_tri': 10,      # Nhiều hoạt động giải trí
        'mua_sam': 2,
    },
    'cultural': {
        'khach_san': 3,
        'nha_hang': 8,
        'dia_danh': 25,      # Rất nhiều điểm văn hóa
        'giai_tri': 5,
        'mua_sam': 3,
    },
    'gastronomy': {
        'khach_san': 3,
        'nha_hang': 20,      # Rất nhiều nhà hàng
        'dia_danh': 10,
        'giai_tri': 3,
        'mua_sam': 5,        # Chợ, điểm mua sắm đặc sản
    },
    'romantic': {
        'khach_san': 5,
        'nha_hang': 10,
        'dia_danh': 12,
        'giai_tri': 8,
        'mua_sam': 3,
    },
    'family': {
        'khach_san': 5,
        'nha_hang': 10,
        'dia_danh': 15,
        'giai_tri': 10,      # Nhiều hoạt động cho trẻ em
        'mua_sam': 5,
    },
}

# Tiêu chí dữ liệu hoàn chỉnh
COMPLETENESS_CRITERIA = {
    'basic': ['tenDiaDiem', 'diaChi', 'maTinhThanh'],  # Bắt buộc
    'good': ['viDo', 'kinhDo', 'moTa'],                # Tốt
    'excellent': ['tienNghi', 'gioMoCua', 'gioDongCua', 'giaVe'],  # Xuất sắc
}


def get_place_completeness_score(cursor, ma_dia_diem: int) -> Dict[str, bool]:
    """Tính điểm hoàn chỉnh của một địa điểm"""
    cursor.execute("""
        SELECT 
            tenDiaDiem, diaChi, maTinhThanh,
            viDo, kinhDo, moTa,
            tienNghi, gioMoCua, gioDongCua, giaVe
        FROM DIADIEM
        WHERE maDiaDiem = ?
    """, (ma_dia_diem,))
    
    row = cursor.fetchone()
    if not row:
        return {}
    
    (ten, dia_chi, ma_tinh, vi_do, kinh_do, mo_ta,
     tien_nghi, gio_mo, gio_dong, gia_ve) = row
    
    return {
        'has_name': bool(ten),
        'has_address': bool(dia_chi),
        'has_province': bool(ma_tinh),
        'has_coords': bool(vi_do and kinh_do and vi_do != 0.0 and kinh_do != 0.0),
        'has_description': bool(mo_ta and len(mo_ta) >= 50),
        'has_amenities': bool(tien_nghi and len(tien_nghi.strip()) > 0),
        'has_hours': bool(gio_mo and gio_dong),
        'has_price': bool(gia_ve is not None and gia_ve > 0),
    }


def analyze_province_data(cursor, ma_tinh_thanh: int, ten_tinh: str) -> Dict:
    """Phân tích dữ liệu của một tỉnh"""
    # Đếm theo loại địa điểm
    cursor.execute("""
        SELECT loaiDiaDiem, COUNT(*) as count
        FROM DIADIEM
        WHERE maTinhThanh = ? AND trangThai = 'active'
        GROUP BY loaiDiaDiem
    """, (ma_tinh_thanh,))
    
    counts_by_type = dict(cursor.fetchall())
    
    # Đếm chất lượng dữ liệu
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN viDo IS NOT NULL AND viDo != 0.0 AND kinhDo IS NOT NULL AND kinhDo != 0.0 THEN 1 ELSE 0 END) as has_coords,
            SUM(CASE WHEN moTa IS NOT NULL AND LENGTH(moTa) >= 50 THEN 1 ELSE 0 END) as has_desc,
            SUM(CASE WHEN tienNghi IS NOT NULL AND LENGTH(tienNghi) > 0 THEN 1 ELSE 0 END) as has_amenities,
            SUM(CASE WHEN gioMoCua IS NOT NULL AND gioDongCua IS NOT NULL THEN 1 ELSE 0 END) as has_hours,
            SUM(CASE WHEN giaVe IS NOT NULL AND giaVe > 0 THEN 1 ELSE 0 END) as has_price
        FROM DIADIEM
        WHERE maTinhThanh = ? AND trangThai = 'active'
    """, (ma_tinh_thanh,))
    
    quality = cursor.fetchone()
    total, has_coords, has_desc, has_amenities, has_hours, has_price = quality
    
    # Kiểm tra hình ảnh
    cursor.execute("""
        SELECT COUNT(DISTINCT maDiaDiem)
        FROM HINHANHDIADIEM
        WHERE maDiaDiem IN (SELECT maDiaDiem FROM DIADIEM WHERE maTinhThanh = ?)
    """, (ma_tinh_thanh,))
    has_images = cursor.fetchone()[0]
    
    # Tính điểm hoàn chỉnh
    completeness_score = 0
    if total > 0:
        completeness_score = (
            (has_coords / total * 0.3) +
            (has_desc / total * 0.25) +
            (has_amenities / total * 0.2) +
            (has_hours / total * 0.15) +
            (has_price / total * 0.1)
        )
    
    # Kiểm tra phong cách du lịch có thể hỗ trợ
    supported_styles = []
    for style, requirements in TRAVEL_STYLE_REQUIREMENTS.items():
        can_support = True
        for loai, min_count in requirements.items():
            count = counts_by_type.get(loai, 0)
            if count < min_count:
                can_support = False
                break
        if can_support:
            supported_styles.append(style)
    
    return {
        'maTinhThanh': ma_tinh_thanh,
        'tenTinhThanh': ten_tinh,
        'total': total,
        'by_type': counts_by_type,
        'quality': {
            'has_coords': has_coords,
            'has_desc': has_desc,
            'has_amenities': has_amenities,
            'has_hours': has_hours,
            'has_price': has_price,
            'has_images': has_images,
        },
        'completeness_score': completeness_score,
        'supported_styles': supported_styles,
    }


def main():
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    print("="*80)
    print("PHÂN TÍCH CHẤT LƯỢNG DỮ LIỆU ĐỊA ĐIỂM")
    print("="*80)
    print()
    
    # Lấy danh sách tỉnh
    cursor.execute("""
        SELECT maTinhThanh, tenTinhThanh
        FROM TINHTHANH
        ORDER BY tenTinhThanh
    """)
    provinces = cursor.fetchall()
    
    print(f"Tổng số tỉnh: {len(provinces)}")
    print()
    
    # Phân tích từng tỉnh
    province_data = []
    for ma_tinh, ten_tinh in provinces:
        data = analyze_province_data(cursor, ma_tinh, ten_tinh)
        province_data.append(data)
    
    # Sắp xếp theo số lượng địa điểm
    province_data.sort(key=lambda x: x['total'], reverse=True)
    
    # Thống kê tổng quan
    print("="*80)
    print("THỐNG KÊ TỔNG QUAN")
    print("="*80)
    
    total_places = sum(p['total'] for p in province_data)
    total_with_coords = sum(p['quality']['has_coords'] for p in province_data)
    total_with_desc = sum(p['quality']['has_desc'] for p in province_data)
    total_with_amenities = sum(p['quality']['has_amenities'] for p in province_data)
    total_with_images = sum(p['quality']['has_images'] for p in province_data)
    
    print(f"Tổng số địa điểm: {total_places:,}")
    print(f"  - Có tọa độ: {total_with_coords:,} ({total_with_coords*100/total_places:.1f}%)")
    print(f"  - Có mô tả đầy đủ: {total_with_desc:,} ({total_with_desc*100/total_places:.1f}%)")
    print(f"  - Có tiện nghi: {total_with_amenities:,} ({total_with_amenities*100/total_places:.1f}%)")
    print(f"  - Có hình ảnh: {total_with_images:,} ({total_with_images*100/total_places:.1f}%)")
    print()
    
    # Thống kê theo loại địa điểm
    print("="*80)
    print("THỐNG KÊ THEO LOẠI ĐỊA ĐIỂM")
    print("="*80)
    
    type_totals = defaultdict(int)
    for p in province_data:
        for loai, count in p['by_type'].items():
            type_totals[loai] += count
    
    type_names = {
        'khach_san': 'Khách sạn',
        'nha_hang': 'Nhà hàng',
        'dia_danh': 'Địa danh',
        'giai_tri': 'Giải trí',
        'mua_sam': 'Mua sắm',
        'khac': 'Khác',
    }
    
    for loai, count in sorted(type_totals.items(), key=lambda x: x[1], reverse=True):
        name = type_names.get(loai, loai)
        print(f"  {name:20s}: {count:6,} ({count*100/total_places:.1f}%)")
    print()
    
    # Top 20 tỉnh có nhiều địa điểm nhất
    print("="*80)
    print("TOP 20 TỈNH CÓ NHIỀU ĐỊA ĐIỂM NHẤT")
    print("="*80)
    print(f"{'Tỉnh':<30} {'Tổng':>8} {'Tọa độ':>10} {'Mô tả':>10} {'Tiện nghi':>12} {'Hình ảnh':>12} {'Điểm':>8} {'Phong cách':<30}")
    print("-"*80)
    
    for p in province_data[:20]:
        if p['total'] == 0:
            continue
        coords_pct = p['quality']['has_coords']*100/p['total']
        desc_pct = p['quality']['has_desc']*100/p['total']
        amenities_pct = p['quality']['has_amenities']*100/p['total']
        images_pct = p['quality']['has_images']*100/p['total'] if p['total'] > 0 else 0
        score = p['completeness_score']*100
        styles = ', '.join(p['supported_styles'][:3])  # Hiển thị tối đa 3 phong cách
        
        print(f"{p['tenTinhThanh']:<30} {p['total']:>8,} "
              f"{coords_pct:>9.1f}% {desc_pct:>9.1f}% {amenities_pct:>11.1f}% "
              f"{images_pct:>11.1f}% {score:>7.1f}% {styles:<30}")
    print()
    
    # Tỉnh đủ dữ liệu cho từng phong cách du lịch
    print("="*80)
    print("TỈNH ĐỦ DỮ LIỆU CHO TỪNG PHONG CÁCH DU LỊCH")
    print("="*80)
    
    style_names = {
        'standard': 'Tiêu chuẩn',
        'budget': 'Tiết kiệm',
        'luxury': 'Sang trọng',
        'adventure': 'Phiêu lưu',
        'cultural': 'Văn hóa',
        'gastronomy': 'Ẩm thực',
        'romantic': 'Lãng mạn',
        'family': 'Gia đình',
    }
    
    for style, style_name in style_names.items():
        supported = [p for p in province_data if style in p['supported_styles']]
        supported.sort(key=lambda x: x['total'], reverse=True)
        
        print(f"\n{style_name} ({style}): {len(supported)} tỉnh")
        if supported:
            print("  Top 10:")
            for i, p in enumerate(supported[:10], 1):
                print(f"    {i:2d}. {p['tenTinhThanh']:<30} ({p['total']:>5,} địa điểm)")
    print()
    
    # Tỉnh có dữ liệu hoàn chỉnh nhất (completeness score > 70%)
    print("="*80)
    print("TỈNH CÓ DỮ LIỆU HOÀN CHỈNH NHẤT (Điểm > 70%)")
    print("="*80)
    
    complete_provinces = [p for p in province_data if p['completeness_score'] > 0.7 and p['total'] >= 50]
    complete_provinces.sort(key=lambda x: x['completeness_score'], reverse=True)
    
    if complete_provinces:
        print(f"{'Tỉnh':<30} {'Điểm':>8} {'Tổng':>8} {'Phong cách hỗ trợ':<50}")
        print("-"*80)
        for p in complete_provinces[:20]:
            styles = ', '.join(p['supported_styles'])
            print(f"{p['tenTinhThanh']:<30} {p['completeness_score']*100:>7.1f}% {p['total']:>8,} {styles:<50}")
    else:
        print("  Không có tỉnh nào đạt điểm > 70%")
    print()
    
    # Tỉnh thiếu dữ liệu nhất
    print("="*80)
    print("TỈNH THIẾU DỮ LIỆU NHẤT (Cần cải thiện)")
    print("="*80)
    
    incomplete_provinces = [p for p in province_data if p['total'] > 0 and p['completeness_score'] < 0.5]
    incomplete_provinces.sort(key=lambda x: (x['completeness_score'], -x['total']))
    
    if incomplete_provinces:
        print(f"{'Tỉnh':<30} {'Điểm':>8} {'Tổng':>8} {'Thiếu':<40}")
        print("-"*80)
        for p in incomplete_provinces[:20]:
            missing = []
            if p['quality']['has_coords']/p['total'] < 0.7:
                missing.append('tọa độ')
            if p['quality']['has_desc']/p['total'] < 0.7:
                missing.append('mô tả')
            if p['quality']['has_amenities']/p['total'] < 0.7:
                missing.append('tiện nghi')
            missing_str = ', '.join(missing) if missing else 'OK'
            print(f"{p['tenTinhThanh']:<30} {p['completeness_score']*100:>7.1f}% {p['total']:>8,} {missing_str:<40}")
    print()
    
    conn.close()
    
    print("="*80)
    print("KẾT LUẬN")
    print("="*80)
    print(f"- Tổng số tỉnh: {len(provinces)}")
    print(f"- Tổng số địa điểm: {total_places:,}")
    print(f"- Tỉnh có dữ liệu hoàn chỉnh (>70%): {len(complete_provinces)}")
    print(f"- Tỉnh đủ dữ liệu cho phong cách 'standard': {len([p for p in province_data if 'standard' in p['supported_styles']])}")
    print(f"- Tỉnh đủ dữ liệu cho phong cách 'budget': {len([p for p in province_data if 'budget' in p['supported_styles']])}")
    print(f"- Tỉnh đủ dữ liệu cho phong cách 'luxury': {len([p for p in province_data if 'luxury' in p['supported_styles']])}")
    print("="*80)


if __name__ == '__main__':
    main()





