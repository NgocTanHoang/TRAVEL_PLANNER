"""
Tìm kinhDo đúng từ DIADIEM_OLD và cập nhật
"""
import sqlite3
from pathlib import Path

db_path = Path(__file__).resolve().parent / 'db.sqlite3'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=" * 100)
print("TÌM VÀ CẬP NHẬT kinhDo")
print("=" * 100)

# Kiểm tra DIADIEM_OLD để tìm kinhDo
cursor.execute("SELECT maDiaDiem, viDo, kinhDo, giaVe, gioMoCua, gioDongCua FROM DIADIEM_OLD ORDER BY maDiaDiem LIMIT 5")
samples = cursor.fetchall()

print("\nPhân tích DIADIEM_OLD để tìm kinhDo (khoảng 100-110):")
for sample in samples:
    ma, vi_do, kinh_do, gia_ve, gio_mo, gio_dong = sample
    print(f"\n  maDiaDiem={ma}:")
    print(f"    viDo (type={type(vi_do).__name__}, value={vi_do})")
    print(f"    kinhDo (type={type(kinh_do).__name__}, value={kinh_do})")
    print(f"    giaVe (type={type(gia_ve).__name__}, value={gia_ve})")
    print(f"    gioMoCua (type={type(gio_mo).__name__}, value={gio_mo})")
    print(f"    gioDongCua (type={type(gio_dong).__name__}, value={gio_dong})")
    
    # Tìm giá trị nào trong khoảng 100-110 (kinhDo hợp lý)
    for idx, val in enumerate([vi_do, kinh_do, gia_ve, gio_mo, gio_dong], start=6):
        if isinstance(val, (int, float)) and 100.0 <= float(val) <= 110.0:
            col_name = ['viDo', 'kinhDo', 'giaVe', 'gioMoCua', 'gioDongCua'][idx-6]
            print(f"      ✓ {col_name} = {val} (CÓ THỂ LÀ kinhDo)")

# Kiểm tra DIADIEM hiện tại
print("\n" + "=" * 100)
print("Kiểm tra DIADIEM hiện tại:")
cursor.execute("SELECT maDiaDiem, viDo, kinhDo FROM DIADIEM ORDER BY maDiaDiem LIMIT 5")
current = cursor.fetchall()
for ma, vi_do, kinh_do in current:
    print(f"  maDiaDiem={ma}: viDo={vi_do}, kinhDo={kinh_do}")

# Cập nhật kinhDo từ DIADIEM_OLD
# Dựa trên phân tích: kinhDo có thể ở cột gioMoCua (vị trí 9) hoặc gioDongCua (vị trí 10)
print("\n" + "=" * 100)
print("Cập nhật kinhDo từ DIADIEM_OLD:")
print("=" * 100)

cursor.execute("""
    UPDATE DIADIEM
    SET kinhDo = (
        SELECT 
            CASE 
                WHEN typeof(old.gioMoCua) = 'real' AND old.gioMoCua BETWEEN 100.0 AND 110.0 THEN old.gioMoCua
                WHEN typeof(old.gioDongCua) = 'real' AND old.gioDongCua BETWEEN 100.0 AND 110.0 THEN old.gioDongCua
                WHEN typeof(old.dienThoai) = 'real' AND old.dienThoai BETWEEN 100.0 AND 110.0 THEN old.dienThoai
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
cursor.execute("SELECT maDiaDiem, viDo, kinhDo FROM DIADIEM WHERE kinhDo != 0.0 ORDER BY maDiaDiem LIMIT 5")
updated_samples = cursor.fetchall()
if updated_samples:
    print("  Các bản ghi có kinhDo != 0:")
    for ma, vi_do, kinh_do in updated_samples:
        print(f"    maDiaDiem={ma}: viDo={vi_do}, kinhDo={kinh_do}")
else:
    print("  Không tìm thấy kinhDo hợp lý trong DIADIEM_OLD")

conn.close()

print("\n✅ Hoàn tất!")

