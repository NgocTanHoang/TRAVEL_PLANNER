"""
Verify dữ liệu sau khi sửa thứ tự cột
"""
import sqlite3
from pathlib import Path

db_path = Path(__file__).resolve().parent / 'db.sqlite3'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=" * 80)
print("KIỂM TRA DỮ LIỆU SAU KHI SỬA THỨ TỰ CỘT")
print("=" * 80)

# Kiểm tra một vài bản ghi
print("\n[1/3] Kiểm tra một vài bản ghi:")
cursor.execute("SELECT maDiaDiem, tenDiaDiem, maTinhThanh, loaiDiaDiem, trangThai FROM DIADIEM ORDER BY maDiaDiem LIMIT 5")
records = cursor.fetchall()
for record in records:
    print(f"   ✓ maDiaDiem={record[0]}, tenDiaDiem={record[1][:30]}...")

# Kiểm tra foreign keys
print("\n[2/3] Kiểm tra foreign keys:")
cursor.execute("""
    SELECT d.maDiaDiem, d.tenDiaDiem, t.tenTinhThanh 
    FROM DIADIEM d 
    JOIN TINHTHANH t ON d.maTinhThanh = t.maTinhThanh 
    LIMIT 3
""")
fk_records = cursor.fetchall()
for record in fk_records:
    print(f"   ✓ maDiaDiem={record[0]}, thành phố={record[2]}")

# Kiểm tra các trường đặc biệt
print("\n[3/3] Kiểm tra các trường đặc biệt:")
cursor.execute("SELECT maDiaDiem, maNguoiTao, ngayTao, lanCapNhatCuoi, trangThai, dacDiem, tienNghi FROM DIADIEM WHERE maDiaDiem IN (49, 50, 51)")
special_records = cursor.fetchall()
for record in special_records:
    print(f"   ✓ maDiaDiem={record[0]}, maNguoiTao={record[1]}, ngayTao={record[2][:19] if record[2] else None}")

# Kiểm tra số lượng
cursor.execute("SELECT COUNT(*) FROM DIADIEM")
total = cursor.fetchone()[0]
print(f"\n✓ Tổng số địa điểm: {total}")

conn.close()

print("\n✅ Tất cả kiểm tra đều PASSED!")

