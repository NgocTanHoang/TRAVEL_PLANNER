"""
Sửa lại thứ tự các trường trong bảng DIADIEM
"""
import sqlite3
from pathlib import Path
from datetime import datetime

db_path = Path(__file__).resolve().parent / 'db.sqlite3'

print("=" * 80)
print("SỬA LẠI THỨ TỰ CÁC TRƯỜNG TRONG BẢNG DIADIEM")
print("=" * 80)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Backup dữ liệu
print("\n[1/5] Backup dữ liệu...")
cursor.execute("SELECT COUNT(*) FROM DIADIEM")
count = cursor.fetchone()[0]
print(f"   ✓ Có {count} bản ghi trong DIADIEM")

# Tạo bảng mới với thứ tự đúng
print("\n[2/5] Tạo bảng DIADIEM_NEW với thứ tự đúng...")
cursor.execute("""
    CREATE TABLE IF NOT EXISTS DIADIEM_NEW (
        maDiaDiem INTEGER PRIMARY KEY AUTOINCREMENT,
        tenDiaDiem varchar(255) NOT NULL,
        moTa TEXT NOT NULL,
        diaChi varchar(500) NOT NULL,
        maTinhThanh INTEGER NOT NULL,
        loaiDiaDiem varchar(50) NOT NULL,
        viDo REAL NOT NULL DEFAULT 0.0,
        kinhDo REAL NOT NULL DEFAULT 0.0,
        giaVe REAL NOT NULL DEFAULT 0.0,
        gioMoCua varchar(50) NOT NULL,
        gioDongCua varchar(50) NOT NULL,
        dienThoai varchar(20) NOT NULL,
        website varchar(200) NOT NULL,
        danhGiaTrungBinh REAL NOT NULL DEFAULT 0.0,
        soLuotDanhGia INTEGER NOT NULL DEFAULT 0,
        soLuotXem INTEGER NOT NULL DEFAULT 0,
        maNguoiTao INTEGER NULL,
        ngayTao datetime NOT NULL,
        lanCapNhatCuoi datetime NOT NULL,
        trangThai varchar(20) NOT NULL DEFAULT 'active',
        dacDiem TEXT NOT NULL,
        tienNghi TEXT NOT NULL,
        FOREIGN KEY (maTinhThanh) REFERENCES TINHTHANH(maTinhThanh),
        FOREIGN KEY (maNguoiTao) REFERENCES NGUOIDUNG(maNguoiDung)
    )
""")
print("   ✓ Đã tạo bảng DIADIEM_NEW")

# Copy dữ liệu với thứ tự cột đúng
print("\n[3/5] Copy dữ liệu với thứ tự đúng...")
cursor.execute("""
    INSERT INTO DIADIEM_NEW (
        maDiaDiem, tenDiaDiem, moTa, diaChi, maTinhThanh, loaiDiaDiem,
        viDo, kinhDo, giaVe, gioMoCua, gioDongCua, dienThoai, website,
        danhGiaTrungBinh, soLuotDanhGia, soLuotXem,
        maNguoiTao, ngayTao, lanCapNhatCuoi, trangThai, dacDiem, tienNghi
    )
    SELECT 
        maDiaDiem, tenDiaDiem, moTa, diaChi, maTinhThanh, loaiDiaDiem,
        viDo, kinhDo, giaVe, gioMoCua, gioDongCua, dienThoai, website,
        danhGiaTrungBinh, soLuotDanhGia, soLuotXem,
        maNguoiTao, ngayTao, lanCapNhatCuoi, trangThai, dacDiem, tienNghi
    FROM DIADIEM
""")
conn.commit()
print(f"   ✓ Đã copy {count} bản ghi")

# Verify dữ liệu
print("\n[4/5] Kiểm tra dữ liệu...")
cursor.execute("SELECT COUNT(*) FROM DIADIEM_NEW")
new_count = cursor.fetchone()[0]
if new_count == count:
    print(f"   ✓ Số lượng bản ghi khớp: {new_count}")
else:
    print(f"   ✗ Số lượng không khớp: {new_count} vs {count}")
    conn.rollback()
    conn.close()
    exit(1)

# Kiểm tra một vài bản ghi
cursor.execute("SELECT maDiaDiem, tenDiaDiem FROM DIADIEM_NEW ORDER BY maDiaDiem LIMIT 3")
samples = cursor.fetchall()
print(f"   ✓ Sample records: {samples}")

# Backup bảng cũ và thay thế
print("\n[5/5] Thay thế bảng cũ...")
cursor.execute("ALTER TABLE DIADIEM RENAME TO DIADIEM_OLD")
print("   ✓ Đã rename DIADIEM -> DIADIEM_OLD")

cursor.execute("ALTER TABLE DIADIEM_NEW RENAME TO DIADIEM")
print("   ✓ Đã rename DIADIEM_NEW -> DIADIEM")

# Recreate indexes
print("\n[6/6] Tạo lại indexes...")
cursor.execute("CREATE INDEX IF NOT EXISTS DIADIEM_maTinhT_58a390_idx ON DIADIEM(maTinhThanh, loaiDiaDiem)")
cursor.execute("CREATE INDEX IF NOT EXISTS DIADIEM_danhGiaTrungBinh_idx ON DIADIEM(danhGiaTrungBinh DESC)")
cursor.execute("CREATE INDEX IF NOT EXISTS DIADIEM_trangThai_idx ON DIADIEM(trangThai)")
cursor.execute("CREATE INDEX IF NOT EXISTS DIADIEM_tenDiaDiem_idx ON DIADIEM(tenDiaDiem)")
print("   ✓ Đã tạo lại indexes")

conn.commit()

# Verify thứ tự mới
print("\n" + "=" * 80)
print("KIỂM TRA THỨ TỰ MỚI:")
print("=" * 80)

cursor.execute("PRAGMA table_info(DIADIEM)")
columns = cursor.fetchall()

expected_order = [
    'maDiaDiem', 'tenDiaDiem', 'moTa', 'diaChi', 'maTinhThanh', 'loaiDiaDiem',
    'viDo', 'kinhDo', 'giaVe', 'gioMoCua', 'gioDongCua', 'dienThoai', 'website',
    'danhGiaTrungBinh', 'soLuotDanhGia', 'soLuotXem',
    'maNguoiTao', 'ngayTao', 'lanCapNhatCuoi', 'trangThai', 'dacDiem', 'tienNghi'
]

current_order = [col[1] for col in columns]

all_match = True
for idx, (expected, actual) in enumerate(zip(expected_order, current_order), start=1):
    status = "✓" if expected == actual else "✗"
    if expected != actual:
        all_match = False
    print(f"{status} Vị trí {idx:<3}: {expected:<25} | {actual:<25}")

if all_match:
    print("\n✅ Tất cả các trường đã đúng thứ tự!")
    print("\n💡 Bảng cũ đã được backup thành DIADIEM_OLD")
    print("   Có thể xóa DIADIEM_OLD sau khi xác nhận mọi thứ hoạt động tốt")
else:
    print("\n⚠ Vẫn còn một số trường sai thứ tự")

conn.close()

print("\n✅ Hoàn tất!")

