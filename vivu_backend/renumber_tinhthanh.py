"""
Đánh lại maTinhThanh trong bảng TINHTHANH từ 1
"""
import sqlite3
from pathlib import Path

db_path = Path(__file__).resolve().parent / 'db.sqlite3'

print("=" * 100)
print("ĐÁNH LẠI maTinhThanh TRONG BẢNG TINHTHANH TỪ 1")
print("=" * 100)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Kiểm tra dữ liệu hiện tại
print("\n[1/6] Kiểm tra dữ liệu hiện tại:")
cursor.execute("SELECT COUNT(*) FROM TINHTHANH")
total = cursor.fetchone()[0]
print(f"   ✓ Tổng số tỉnh thành: {total}")

cursor.execute("SELECT maTinhThanh, tenTinhThanh FROM TINHTHANH ORDER BY maTinhThanh LIMIT 10")
samples = cursor.fetchall()
print(f"\n   Một vài bản ghi hiện tại:")
for ma, ten in samples:
    print(f"     maTinhThanh={ma}: {ten}")

# Tạo mapping table để lưu mapping cũ -> mới
print("\n[2/6] Tạo bảng mapping...")
cursor.execute("DROP TABLE IF EXISTS TINHTHANH_MAPPING")
cursor.execute("""
    CREATE TABLE TINHTHANH_MAPPING (
        maTinhThanhCu INTEGER PRIMARY KEY,
        maTinhThanhMoi INTEGER,
        tenTinhThanh TEXT
    )
""")

# Tạo mapping từ cũ sang mới
cursor.execute("""
    INSERT INTO TINHTHANH_MAPPING (maTinhThanhCu, maTinhThanhMoi, tenTinhThanh)
    SELECT maTinhThanh, ROW_NUMBER() OVER (ORDER BY maTinhThanh), tenTinhThanh
    FROM TINHTHANH
""")
conn.commit()
print("   ✓ Đã tạo bảng mapping")

# Kiểm tra mapping
cursor.execute("SELECT maTinhThanhCu, maTinhThanhMoi, tenTinhThanh FROM TINHTHANH_MAPPING ORDER BY maTinhThanhMoi LIMIT 10")
mapping_samples = cursor.fetchall()
print(f"\n   Mapping mẫu:")
for cu, moi, ten in mapping_samples:
    print(f"     {cu} -> {moi}: {ten}")

# Backup bảng TINHTHANH
print("\n[3/6] Backup bảng TINHTHANH...")
cursor.execute("DROP TABLE IF EXISTS TINHTHANH_OLD")
cursor.execute("ALTER TABLE TINHTHANH RENAME TO TINHTHANH_OLD")
print("   ✓ Đã backup thành TINHTHANH_OLD")

# Tạo bảng TINHTHANH mới với maTinhThanh từ 1
print("\n[4/6] Tạo bảng TINHTHANH mới với maTinhThanh từ 1...")
cursor.execute("""
    CREATE TABLE TINHTHANH (
        maTinhThanh INTEGER PRIMARY KEY AUTOINCREMENT,
        tenTinhThanh varchar(255) NOT NULL UNIQUE,
        moTa TEXT,
        anhDaiDien varchar(500),
        viDo REAL,
        kinhDo REAL,
        created_at datetime NOT NULL,
        updated_at datetime NOT NULL
    )
""")

# Copy dữ liệu với maTinhThanh mới
cursor.execute("""
    INSERT INTO TINHTHANH (maTinhThanh, tenTinhThanh, moTa, anhDaiDien, viDo, kinhDo, created_at, updated_at)
    SELECT 
        m.maTinhThanhMoi,
        o.tenTinhThanh,
        o.moTa,
        o.anhDaiDien,
        o.viDo,
        o.kinhDo,
        o.created_at,
        o.updated_at
    FROM TINHTHANH_OLD o
    JOIN TINHTHANH_MAPPING m ON o.maTinhThanh = m.maTinhThanhCu
    ORDER BY m.maTinhThanhMoi
""")
conn.commit()

cursor.execute("SELECT COUNT(*) FROM TINHTHANH")
new_total = cursor.fetchone()[0]
print(f"   ✓ Đã copy {new_total} bản ghi")

# Kiểm tra bảng mới
cursor.execute("SELECT maTinhThanh, tenTinhThanh FROM TINHTHANH ORDER BY maTinhThanh LIMIT 10")
new_samples = cursor.fetchall()
print(f"\n   Một vài bản ghi mới:")
for ma, ten in new_samples:
    print(f"     maTinhThanh={ma}: {ten}")

# Cập nhật DIADIEM.maTinhThanh theo mapping mới
print("\n[5/6] Cập nhật DIADIEM.maTinhThanh theo mapping mới...")
cursor.execute("""
    UPDATE DIADIEM
    SET maTinhThanh = (
        SELECT m.maTinhThanhMoi
        FROM TINHTHANH_MAPPING m
        WHERE m.maTinhThanhCu = DIADIEM.maTinhThanh
    )
    WHERE EXISTS (
        SELECT 1 FROM TINHTHANH_MAPPING m WHERE m.maTinhThanhCu = DIADIEM.maTinhThanh
    )
""")
conn.commit()

updated_count = cursor.rowcount
print(f"   ✓ Đã cập nhật {updated_count} bản ghi trong DIADIEM")

# Kiểm tra foreign key
cursor.execute("""
    SELECT d.maDiaDiem, d.tenDiaDiem, d.maTinhThanh, t.tenTinhThanh 
    FROM DIADIEM d 
    JOIN TINHTHANH t ON d.maTinhThanh = t.maTinhThanh 
    ORDER BY d.maDiaDiem LIMIT 5
""")
fk_check = cursor.fetchall()
print(f"\n   Kiểm tra foreign key:")
for ma_dd, ten_dd, ma_tt, ten_tt in fk_check:
    print(f"     maDiaDiem={ma_dd}, maTinhThanh={ma_tt} ({ten_tt})")

# Xóa bảng mapping và backup
print("\n[6/6] Dọn dẹp...")
cursor.execute("DROP TABLE IF EXISTS TINHTHANH_MAPPING")
print("   ✓ Đã xóa bảng mapping")

# Kiểm tra thống kê cuối cùng
print("\n" + "=" * 100)
print("THỐNG KÊ CUỐI CÙNG:")
print("=" * 100)

cursor.execute("SELECT COUNT(*) FROM TINHTHANH")
final_total = cursor.fetchone()[0]
print(f"✓ Tổng số tỉnh thành: {final_total}")

cursor.execute("SELECT MIN(maTinhThanh), MAX(maTinhThanh) FROM TINHTHANH")
min_max = cursor.fetchone()
print(f"✓ maTinhThanh: MIN={min_max[0]}, MAX={min_max[1]}")

cursor.execute("SELECT maTinhThanh, COUNT(*) FROM DIADIEM GROUP BY maTinhThanh ORDER BY COUNT(*) DESC LIMIT 5")
stats = cursor.fetchall()
print(f"\n✓ Phân bố DIADIEM theo maTinhThanh:")
for ma, count in stats:
    cursor.execute("SELECT tenTinhThanh FROM TINHTHANH WHERE maTinhThanh = ?", (ma,))
    ten = cursor.fetchone()
    ten_str = ten[0] if ten else "Unknown"
    print(f"   {ma} ({ten_str}): {count} địa điểm")

conn.commit()
conn.close()

print("\n" + "=" * 100)
print("✅ Hoàn tất!")
print("💡 Bảng cũ đã được backup thành TINHTHANH_OLD")
print("=" * 100)

