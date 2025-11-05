"""
Phân tích chi tiết để map đúng các trường từ DIADIEM_OLD
"""
import sqlite3
from pathlib import Path
import re

db_path = Path(__file__).resolve().parent / 'db.sqlite3'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=" * 100)
print("PHÂN TÍCH CHI TIẾT ĐỂ MAP ĐÚNG CÁC TRƯỜNG")
print("=" * 100)

# Lấy một vài bản ghi mẫu từ DIADIEM_OLD
cursor.execute("SELECT * FROM DIADIEM_OLD ORDER BY maDiaDiem LIMIT 3")
samples = cursor.fetchall()

cursor.execute("PRAGMA table_info(DIADIEM_OLD)")
old_columns = cursor.fetchall()
column_names = [col[1] for col in old_columns]

print("\n[1] Phân tích các bản ghi mẫu từ DIADIEM_OLD:")
print("=" * 100)

# Phân tích từng cột để tìm giá trị đúng
for sample_idx, sample in enumerate(samples, start=1):
    print(f"\nBản ghi {sample_idx} (maDiaDiem={sample[0]}):")
    print("-" * 100)
    
    # Tìm maTinhThanh đúng - cần là integer hợp lý
    print("\nTìm maTinhThanh (integer hợp lý):")
    for idx, (col, val) in enumerate(zip(old_columns, sample)):
        if isinstance(val, int) and 1 <= val <= 100:
            print(f"  [{idx}] {col[1]:<25} = {val} (có thể là maTinhThanh)")
    
    # Tìm loaiDiaDiem đúng - cần là một trong các giá trị hợp lý
    valid_loai = ['dia_danh', 'nha_hang', 'khach_san', 'giai_tri', 'mua_sam', 'khac']
    print("\nTìm loaiDiaDiem (một trong các giá trị hợp lý):")
    for idx, (col, val) in enumerate(zip(old_columns, sample)):
        if isinstance(val, str) and val in valid_loai:
            print(f"  [{idx}] {col[1]:<25} = {val} (CÓ THỂ LÀ loaiDiaDiem)")
    
    # Tìm viDo đúng - cần là số thực trong khoảng 8-24 (Việt Nam)
    print("\nTìm viDo (real trong khoảng 8-24):")
    for idx, (col, val) in enumerate(zip(old_columns, sample)):
        if isinstance(val, (int, float)) and 8.0 <= float(val) <= 24.0:
            print(f"  [{idx}] {col[1]:<25} = {val} (có thể là viDo)")
    
    # Tìm kinhDo đúng - cần là số thực trong khoảng 100-110 (Việt Nam)
    print("\nTìm kinhDo (real trong khoảng 100-110):")
    for idx, (col, val) in enumerate(zip(old_columns, sample)):
        if isinstance(val, (int, float)) and 100.0 <= float(val) <= 110.0:
            print(f"  [{idx}] {col[1]:<25} = {val} (có thể là kinhDo)")
    
    # Tìm giaVe đúng - có thể là số hoặc text
    print("\nTìm giaVe (số hoặc text về giá):")
    for idx, (col, val) in enumerate(zip(old_columns, sample)):
        if val and isinstance(val, (int, float)) and 0 <= float(val) < 10000000:
            print(f"  [{idx}] {col[1]:<25} = {val} (có thể là giaVe)")
    
    # Tìm gioMoCua, gioDongCua - text chứa thời gian
    print("\nTìm gioMoCua/gioDongCua (text chứa thời gian):")
    time_pattern = re.compile(r'\d{1,2}[:]\d{2}|\d{1,2}[:]\d{2}.*\d{1,2}[:]\d{2}|giờ|Giờ|AM|PM|AM|PM')
    for idx, (col, val) in enumerate(zip(old_columns, sample)):
        if isinstance(val, str) and time_pattern.search(val):
            print(f"  [{idx}] {col[1]:<25} = {val[:50]}... (có thể là giờ)")
    
    # Tìm dienThoai - text chứa số điện thoại
    print("\nTìm dienThoai (text chứa số điện thoại):")
    phone_pattern = re.compile(r'0\d{9,10}|\+84|028|024|0236')
    for idx, (col, val) in enumerate(zip(old_columns, sample)):
        if isinstance(val, str) and phone_pattern.search(val):
            print(f"  [{idx}] {col[1]:<25} = {val[:50]}... (có thể là dienThoai)")
    
    # Tìm website - text chứa URL
    print("\nTìm website (text chứa URL):")
    url_pattern = re.compile(r'http|www\.|\.com|\.vn|\.org')
    for idx, (col, val) in enumerate(zip(old_columns, sample)):
        if isinstance(val, str) and url_pattern.search(val):
            print(f"  [{idx}] {col[1]:<25} = {val[:50]}... (có thể là website)")
    
    # Tìm danhGiaTrungBinh - số thực trong khoảng 0-5
    print("\nTìm danhGiaTrungBinh (real trong khoảng 0-5):")
    for idx, (col, val) in enumerate(zip(old_columns, sample)):
        if isinstance(val, (int, float)) and 0.0 <= float(val) <= 5.0:
            print(f"  [{idx}] {col[1]:<25} = {val} (có thể là danhGiaTrungBinh)")
    
    # Tìm trangThai - một trong các giá trị hợp lý
    valid_trang_thai = ['active', 'inactive', 'pending']
    print("\nTìm trangThai (một trong các giá trị hợp lý):")
    for idx, (col, val) in enumerate(zip(old_columns, sample)):
        if isinstance(val, str) and val in valid_trang_thai:
            print(f"  [{idx}] {col[1]:<25} = {val} (CÓ THỂ LÀ trangThai)")
    
    # Tìm dacDiem, tienNghi - text dài
    print("\nTìm dacDiem/tienNghi (text dài):")
    for idx, (col, val) in enumerate(zip(old_columns, sample)):
        if isinstance(val, str) and len(val) > 30:
            preview = val[:60] + "..." if len(val) > 60 else val
            print(f"  [{idx}] {col[1]:<25} = {preview} (có thể là dacDiem/tienNghi)")

conn.close()

print("\n" + "=" * 100)
print("✅ Hoàn tất phân tích!")
print("=" * 100)

