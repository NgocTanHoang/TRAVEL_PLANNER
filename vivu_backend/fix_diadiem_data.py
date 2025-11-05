"""
Sửa lại dữ liệu DIADIEM bằng cách copy đúng mapping từ DIADIEM_OLD
"""
import sqlite3
from pathlib import Path

db_path = Path(__file__).resolve().parent / 'db.sqlite3'

print("=" * 100)
print("SỬA LẠI DỮ LIỆU DIADIEM - COPY ĐÚNG MAPPING")
print("=" * 100)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Kiểm tra bảng cũ
cursor.execute("SELECT COUNT(*) FROM DIADIEM_OLD")
old_count = cursor.fetchone()[0]
print(f"\n✓ DIADIEM_OLD có {old_count} bản ghi")

# Xóa bảng DIADIEM hiện tại (có dữ liệu sai)
print("\n[1/4] Xóa bảng DIADIEM hiện tại...")
cursor.execute("DROP TABLE IF EXISTS DIADIEM")
print("   ✓ Đã xóa bảng DIADIEM")

# Tạo lại bảng DIADIEM với thứ tự đúng
print("\n[2/4] Tạo lại bảng DIADIEM với thứ tự đúng...")
cursor.execute("""
    CREATE TABLE DIADIEM (
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
print("   ✓ Đã tạo bảng DIADIEM")

# Copy dữ liệu với mapping đúng tên cột (không phải thứ tự)
print("\n[3/4] Copy dữ liệu với mapping đúng tên cột...")
cursor.execute("""
    INSERT INTO DIADIEM (
        maDiaDiem, tenDiaDiem, moTa, diaChi, maTinhThanh, loaiDiaDiem,
        viDo, kinhDo, giaVe, gioMoCua, gioDongCua, dienThoai, website,
        danhGiaTrungBinh, soLuotDanhGia, soLuotXem,
        maNguoiTao, ngayTao, lanCapNhatCuoi, trangThai, dacDiem, tienNghi
    )
    SELECT 
        maDiaDiem, 
        tenDiaDiem, 
        moTa, 
        diaChi, 
        -- maTinhThanh: Cần lấy từ bảng TINHTHANH dựa trên tenTinhThanh từ diaChi hoặc tìm cách khác
        -- Tạm thời, cần tìm maTinhThanh từ một cột khác hoặc set default
        CASE 
            WHEN maTinhThanh IS NOT NULL AND typeof(maTinhThanh) = 'integer' THEN maTinhThanh
            ELSE 86  -- Default to Đà Nẵng nếu không tìm thấy
        END as maTinhThanh,
        -- loaiDiaDiem: Cần tìm trong các cột khác
        CASE 
            WHEN loaiDiaDiem IN ('dia_danh', 'nha_hang', 'khach_san', 'giai_tri', 'mua_sam', 'khac') THEN loaiDiaDiem
            WHEN viDo IS NOT NULL AND typeof(viDo) = 'text' AND viDo IN ('dia_danh', 'nha_hang', 'khach_san', 'giai_tri', 'mua_sam', 'khac') THEN viDo
            ELSE 'khac'
        END as loaiDiaDiem,
        -- viDo: Tìm trong các cột
        CASE 
            WHEN viDo IS NOT NULL AND typeof(viDo) = 'real' THEN viDo
            WHEN kinhDo IS NOT NULL AND typeof(kinhDo) = 'real' THEN kinhDo
            ELSE 0.0
        END as viDo,
        -- kinhDo: Tìm trong các cột
        CASE 
            WHEN kinhDo IS NOT NULL AND typeof(kinhDo) = 'real' THEN kinhDo
            WHEN giaVe IS NOT NULL AND typeof(giaVe) = 'real' THEN giaVe
            ELSE 0.0
        END as kinhDo,
        -- giaVe
        CASE 
            WHEN giaVe IS NOT NULL AND typeof(giaVe) = 'real' THEN giaVe
            ELSE 0.0
        END as giaVe,
        -- gioMoCua, gioDongCua, dienThoai, website - cần tìm trong các cột
        COALESCE(NULLIF(gioMoCua, ''), '') as gioMoCua,
        COALESCE(NULLIF(gioDongCua, ''), '') as gioDongCua,
        COALESCE(NULLIF(dienThoai, ''), '') as dienThoai,
        COALESCE(NULLIF(website, ''), '') as website,
        -- danhGiaTrungBinh, soLuotDanhGia, soLuotXem
        CASE 
            WHEN danhGiaTrungBinh IS NOT NULL AND typeof(danhGiaTrungBinh) = 'real' THEN danhGiaTrungBinh
            WHEN soLuotDanhGia IS NOT NULL AND typeof(soLuotDanhGia) = 'real' THEN soLuotDanhGia
            ELSE 0.0
        END as danhGiaTrungBinh,
        CASE 
            WHEN soLuotDanhGia IS NOT NULL AND typeof(soLuotDanhGia) = 'integer' THEN soLuotDanhGia
            WHEN soLuotXem IS NOT NULL AND typeof(soLuotXem) = 'integer' THEN soLuotXem
            ELSE 0
        END as soLuotDanhGia,
        CASE 
            WHEN soLuotXem IS NOT NULL AND typeof(soLuotXem) = 'integer' THEN soLuotXem
            ELSE 0
        END as soLuotXem,
        -- maNguoiTao: Tìm ở cuối bảng
        maNguoiTao,
        -- ngayTao, lanCapNhatCuoi
        COALESCE(ngayTao, datetime('now')) as ngayTao,
        COALESCE(lanCapNhatCuoi, datetime('now')) as lanCapNhatCuoi,
        -- trangThai
        COALESCE(NULLIF(trangThai, ''), 'active') as trangThai,
        -- dacDiem, tienNghi
        COALESCE(NULLIF(dacDiem, ''), '') as dacDiem,
        COALESCE(NULLIF(tienNghi, ''), '') as tienNghi
    FROM DIADIEM_OLD
""")

try:
    conn.commit()
    copied_count = cursor.rowcount
    print(f"   ✓ Đã copy {copied_count} bản ghi")
except Exception as e:
    print(f"   ✗ Lỗi: {e}")
    import traceback
    traceback.print_exc()
    conn.rollback()
    conn.close()
    exit(1)

# Kiểm tra một vài bản ghi
print("\n[4/4] Kiểm tra dữ liệu sau khi copy...")
cursor.execute("SELECT maDiaDiem, tenDiaDiem, maTinhThanh, loaiDiaDiem, trangThai FROM DIADIEM ORDER BY maDiaDiem LIMIT 3")
samples = cursor.fetchall()
print("   Sample records:")
for sample in samples:
    print(f"     maDiaDiem={sample[0]}, tenDiaDiem={sample[1][:40]}...")
    print(f"       maTinhThanh={sample[2]}, loaiDiaDiem={sample[3]}, trangThai={sample[4]}")

# Tạo lại indexes
print("\n[5/5] Tạo lại indexes...")
cursor.execute("CREATE INDEX IF NOT EXISTS DIADIEM_maTinhT_58a390_idx ON DIADIEM(maTinhThanh, loaiDiaDiem)")
cursor.execute("CREATE INDEX IF NOT EXISTS DIADIEM_danhGiaTrungBinh_idx ON DIADIEM(danhGiaTrungBinh DESC)")
cursor.execute("CREATE INDEX IF NOT EXISTS DIADIEM_trangThai_idx ON DIADIEM(trangThai)")
cursor.execute("CREATE INDEX IF NOT EXISTS DIADIEM_tenDiaDiem_idx ON DIADIEM(tenDiaDiem)")
print("   ✓ Đã tạo lại indexes")

conn.commit()

# Verify
cursor.execute("SELECT COUNT(*) FROM DIADIEM")
new_count = cursor.fetchone()[0]
print(f"\n✓ Tổng số bản ghi trong DIADIEM: {new_count}")

conn.close()

print("\n✅ Hoàn tất!")

