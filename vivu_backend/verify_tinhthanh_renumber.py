"""
Kiểm tra lại maTinhThanh sau khi renumber
"""
import sqlite3
from pathlib import Path

db_path = Path(__file__).resolve().parent / 'db.sqlite3'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=" * 100)
print("KIỂM TRA LẠI maTinhThanh SAU KHI RENUMBER")
print("=" * 100)

# Kiểm tra TINHTHANH
print("\n[1] Kiểm tra bảng TINHTHANH:")
cursor.execute("SELECT maTinhThanh, tenTinhThanh FROM TINHTHANH ORDER BY maTinhThanh")
all_tinh_thanh = cursor.fetchall()

print(f"   Tổng số: {len(all_tinh_thanh)}")
print(f"\n   Danh sách đầy đủ (maTinhThanh từ 1):")
for idx, (ma, ten) in enumerate(all_tinh_thanh, start=1):
    if idx != ma:
        print(f"     ✗ Vị trí {idx}: maTinhThanh={ma} - {ten} (SAI)")
    else:
        if idx <= 10 or idx >= len(all_tinh_thanh) - 2:
            print(f"     ✓ Vị trí {idx}: maTinhThanh={ma} - {ten}")

# Kiểm tra DIADIEM
print("\n[2] Kiểm tra bảng DIADIEM:")
cursor.execute("""
    SELECT d.maDiaDiem, d.tenDiaDiem, d.maTinhThanh, t.tenTinhThanh 
    FROM DIADIEM d 
    JOIN TINHTHANH t ON d.maTinhThanh = t.maTinhThanh 
    ORDER BY d.maDiaDiem LIMIT 10
""")
diadiem_samples = cursor.fetchall()

print(f"   Sample records:")
for ma_dd, ten_dd, ma_tt, ten_tt in diadiem_samples:
    print(f"     maDiaDiem={ma_dd}, maTinhThanh={ma_tt} ({ten_tt})")

# Kiểm tra foreign key integrity
print("\n[3] Kiểm tra foreign key integrity:")
cursor.execute("""
    SELECT COUNT(*) 
    FROM DIADIEM d 
    LEFT JOIN TINHTHANH t ON d.maTinhThanh = t.maTinhThanh 
    WHERE t.maTinhThanh IS NULL
""")
orphaned = cursor.fetchone()[0]

if orphaned == 0:
    print(f"   ✓ Tất cả foreign key hợp lệ (không có orphaned records)")
else:
    print(f"   ✗ Có {orphaned} orphaned records")

# Thống kê phân bố
print("\n[4] Thống kê phân bố:")
cursor.execute("""
    SELECT d.maTinhThanh, t.tenTinhThanh, COUNT(*) as count
    FROM DIADIEM d
    JOIN TINHTHANH t ON d.maTinhThanh = t.maTinhThanh
    GROUP BY d.maTinhThanh, t.tenTinhThanh
    ORDER BY count DESC
""")
distribution = cursor.fetchall()

print(f"   Phân bố địa điểm theo tỉnh thành:")
for ma, ten, count in distribution:
    print(f"     maTinhThanh={ma} ({ten}): {count} địa điểm")

conn.close()

print("\n" + "=" * 100)
print("✅ Hoàn tất kiểm tra!")
print("=" * 100)

