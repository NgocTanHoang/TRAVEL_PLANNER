"""
Cập nhật kinhDo từ gioMoCua (string chứa số) trong DIADIEM_OLD
"""
import sqlite3
from pathlib import Path

db_path = Path(__file__).resolve().parent / 'db.sqlite3'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=" * 100)
print("CẬP NHẬT kinhDo TỪ gioMoCua (STRING)")
print("=" * 100)

# Cập nhật kinhDo từ gioMoCua trong DIADIEM_OLD (string chứa số)
cursor.execute("""
    UPDATE DIADIEM
    SET kinhDo = (
        SELECT 
            CASE 
                -- gioMoCua là string nhưng chứa số trong khoảng 100-110
                WHEN typeof(old.gioMoCua) = 'text' 
                     AND CAST(old.gioMoCua AS REAL) BETWEEN 100.0 AND 110.0 
                     THEN CAST(old.gioMoCua AS REAL)
                -- gioDongCua là string nhưng chứa số trong khoảng 100-110
                WHEN typeof(old.gioDongCua) = 'text' 
                     AND CAST(old.gioDongCua AS REAL) BETWEEN 100.0 AND 110.0 
                     THEN CAST(old.gioDongCua AS REAL)
                -- dienThoai là string nhưng chứa số trong khoảng 100-110
                WHEN typeof(old.dienThoai) = 'text' 
                     AND CAST(old.dienThoai AS REAL) BETWEEN 100.0 AND 110.0 
                     THEN CAST(old.dienThoai AS REAL)
                ELSE DIADIEM.kinhDo  -- Giữ nguyên nếu không tìm thấy
            END
        FROM DIADIEM_OLD as old
        WHERE old.maDiaDiem = DIADIEM.maDiaDiem
    )
    WHERE EXISTS (
        SELECT 1 FROM DIADIEM_OLD WHERE DIADIEM_OLD.maDiaDiem = DIADIEM.maDiaDiem
    )
""")

conn.commit()
updated = cursor.rowcount
print(f"✓ Đã cập nhật {updated} bản ghi")

# Kiểm tra lại
print("\nKiểm tra sau khi cập nhật:")
cursor.execute("SELECT maDiaDiem, viDo, kinhDo FROM DIADIEM WHERE kinhDo != 0.0 ORDER BY maDiaDiem LIMIT 10")
updated_samples = cursor.fetchall()
if updated_samples:
    print(f"  Các bản ghi có kinhDo != 0 ({len(updated_samples)} bản ghi đầu tiên):")
    for ma, vi_do, kinh_do in updated_samples:
        print(f"    maDiaDiem={ma}: viDo={vi_do}, kinhDo={kinh_do}")
else:
    print("  Không tìm thấy kinhDo hợp lý")

# Kiểm tra tổng số có kinhDo != 0
cursor.execute("SELECT COUNT(*) FROM DIADIEM WHERE kinhDo != 0.0")
count_with_kinhdo = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM DIADIEM")
total = cursor.fetchone()[0]
print(f"\n  Tổng số bản ghi có kinhDo != 0: {count_with_kinhdo}/{total}")

conn.close()

print("\n✅ Hoàn tất!")

