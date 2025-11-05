"""
Kiểm tra bảng TINHTHANH và map maTinhThanh dựa trên diaChi
"""
import sqlite3
from pathlib import Path

db_path = Path(__file__).resolve().parent / 'db.sqlite3'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=" * 100)
print("KIỂM TRA BẢNG TINHTHANH VÀ MAP maTinhThanh")
print("=" * 100)

# Lấy danh sách TINHTHANH
cursor.execute("SELECT maTinhThanh, tenTinhThanh FROM TINHTHANH ORDER BY maTinhThanh")
tinh_thanh_list = cursor.fetchall()

print("\nDanh sách TINHTHANH:")
print("-" * 100)
for ma, ten in tinh_thanh_list:
    print(f"  {ma:>3}: {ten}")

# Lấy một vài bản ghi từ DIADIEM_OLD để xem diaChi
print("\n" + "=" * 100)
print("KIỂM TRA diaChi TRONG DIADIEM_OLD:")
print("=" * 100)

cursor.execute("SELECT maDiaDiem, tenDiaDiem, diaChi FROM DIADIEM_OLD ORDER BY maDiaDiem LIMIT 10")
samples = cursor.fetchall()

print("\nBản ghi mẫu:")
for ma, ten, dia_chi in samples:
    print(f"\n  maDiaDiem={ma}")
    print(f"  tenDiaDiem={ten[:50]}...")
    print(f"  diaChi={dia_chi}")

conn.close()

