"""
Kiểm tra thứ tự các trường trong bảng DIADIEM
"""
import sqlite3
from pathlib import Path

db_path = Path(__file__).resolve().parent / 'db.sqlite3'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=" * 80)
print("KIỂM TRA THỨ TỰ CÁC TRƯỜNG TRONG BẢNG DIADIEM")
print("=" * 80)

# Lấy thông tin các cột
cursor.execute("PRAGMA table_info(DIADIEM)")
columns = cursor.fetchall()

print("\nThứ tự hiện tại trong database:")
print("-" * 80)
print(f"{'STT':<5} | {'Tên trường':<25} | {'Type':<20} | {'NOT NULL':<10} | {'Default':<15}")
print("-" * 80)

for idx, col in enumerate(columns, start=1):
    cid, name, col_type, not_null, default_value, pk = col
    null_str = "NOT NULL" if not_null else "NULL"
    default_str = str(default_value) if default_value else ""
    print(f"{idx:<5} | {name:<25} | {col_type:<20} | {null_str:<10} | {default_str:<15}")

# So sánh với thứ tự mong đợi từ model Django
print("\n" + "=" * 80)
print("THỨ TỰ MONG ĐỢI (theo model Django):")
print("-" * 80)

expected_order = [
    'maDiaDiem',
    'tenDiaDiem',
    'moTa',
    'diaChi',
    'maTinhThanh',
    'loaiDiaDiem',
    'viDo',
    'kinhDo',
    'giaVe',
    'gioMoCua',
    'gioDongCua',
    'dienThoai',
    'website',
    'danhGiaTrungBinh',
    'soLuotDanhGia',
    'soLuotXem',
    'maNguoiTao',
    'ngayTao',
    'lanCapNhatCuoi',
    'trangThai',
    'dacDiem',
    'tienNghi'
]

current_order = [col[1] for col in columns]

print(f"{'STT':<5} | {'Tên trường':<25}")
print("-" * 80)
for idx, field in enumerate(expected_order, start=1):
    print(f"{idx:<5} | {field:<25}")

print("\n" + "=" * 80)
print("SO SÁNH:")
print("-" * 80)

mismatches = []
for idx, (expected, actual) in enumerate(zip(expected_order, current_order), start=1):
    status = "✓" if expected == actual else "✗"
    if expected != actual:
        mismatches.append((idx, expected, actual))
    print(f"{status} Vị trí {idx:<3}: Mong đợi '{expected:<25}' | Thực tế '{actual:<25}'")

if len(current_order) != len(expected_order):
    print(f"\n⚠ Số lượng trường khác nhau:")
    print(f"   Mong đợi: {len(expected_order)} trường")
    print(f"   Thực tế: {len(current_order)} trường")
    
    if len(current_order) > len(expected_order):
        extra = set(current_order) - set(expected_order)
        print(f"   Trường thừa: {extra}")
    else:
        missing = set(expected_order) - set(current_order)
        print(f"   Trường thiếu: {missing}")

if mismatches:
    print(f"\n✗ Có {len(mismatches)} trường bị sai thứ tự:")
    for idx, expected, actual in mismatches:
        print(f"   - Vị trí {idx}: '{expected}' thay vì '{actual}'")
else:
    print("\n✅ Tất cả các trường đều đúng thứ tự!")

conn.close()

