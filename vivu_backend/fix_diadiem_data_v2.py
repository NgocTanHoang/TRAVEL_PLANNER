"""
Sửa lại dữ liệu DIADIEM bằng cách map đúng từ DIADIEM_OLD dựa trên phân tích
"""
import sqlite3
from pathlib import Path

db_path = Path(__file__).resolve().parent / 'db.sqlite3'

print("=" * 100)
print("SỬA LẠI DỮ LIỆU DIADIEM - MAP ĐÚNG TỪ DIADIEM_OLD")
print("=" * 100)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Xóa bảng DIADIEM hiện tại
print("\n[1/5] Xóa bảng DIADIEM hiện tại...")
cursor.execute("DROP TABLE IF EXISTS DIADIEM")
print("   ✓ Đã xóa")

# Tạo lại bảng DIADIEM
print("\n[2/5] Tạo lại bảng DIADIEM...")
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
print("   ✓ Đã tạo")

# Copy dữ liệu với mapping đúng
# Dựa trên phân tích:
# - maTinhThanh ở [4] có text -> cần tìm từ diaChi hoặc dùng default
# - loaiDiaDiem ở [5] có địa chỉ -> dùng giá trị từ [7] (kinhDo) nếu hợp lý
# - viDo ở [6] = 139.0 (sai) -> dùng từ [8] (giaVe) nếu trong khoảng hợp lý
# - kinhDo ở [7] = "giai_tri" (sai) -> dùng từ [9] (gioMoCua) nếu trong khoảng hợp lý
# - giaVe ở [8] = 10.777085 (có vẻ là viDo) -> dùng nếu hợp lý
# - gioMoCua ở [9] = 106.703215 (có vẻ là kinhDo) -> dùng nếu hợp lý
# - v.v.

print("\n[3/5] Copy dữ liệu với mapping đúng...")
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
        -- maTinhThanh: Tìm từ diaChi hoặc dùng default
        CASE 
            WHEN diaChi LIKE '%Hà Nội%' OR diaChi LIKE '%Hanoi%' THEN (SELECT maTinhThanh FROM TINHTHANH WHERE tenTinhThanh LIKE '%Hà Nội%' LIMIT 1)
            WHEN diaChi LIKE '%Đà Nẵng%' OR diaChi LIKE '%Da Nang%' THEN (SELECT maTinhThanh FROM TINHTHANH WHERE tenTinhThanh LIKE '%Đà Nẵng%' LIMIT 1)
            WHEN diaChi LIKE '%TPHCM%' OR diaChi LIKE '%Hồ Chí Minh%' OR diaChi LIKE '%Ho Chi Minh%' THEN (SELECT maTinhThanh FROM TINHTHANH WHERE tenTinhThanh LIKE '%Hồ Chí Minh%' LIMIT 1)
            ELSE 86  -- Default Đà Nẵng
        END as maTinhThanh,
        -- loaiDiaDiem: Tìm từ cột kinhDo (vị trí 7) nếu hợp lý, nếu không thì khac
        CASE 
            WHEN typeof(kinhDo) = 'text' AND kinhDo IN ('dia_danh', 'nha_hang', 'khach_san', 'giai_tri', 'mua_sam', 'khac') THEN kinhDo
            WHEN typeof(giaVe) = 'text' AND giaVe IN ('dia_danh', 'nha_hang', 'khach_san', 'giai_tri', 'mua_sam', 'khac') THEN giaVe
            ELSE 'khac'
        END as loaiDiaDiem,
        -- viDo: Tìm từ giaVe (vị trí 8) nếu trong khoảng hợp lý (8-24)
        CASE 
            WHEN typeof(giaVe) = 'real' AND giaVe BETWEEN 8.0 AND 24.0 THEN giaVe
            WHEN typeof(gioMoCua) = 'real' AND gioMoCua BETWEEN 8.0 AND 24.0 THEN gioMoCua
            ELSE 0.0
        END as viDo,
        -- kinhDo: Tìm từ gioMoCua (vị trí 9) nếu trong khoảng hợp lý (100-110)
        CASE 
            WHEN typeof(gioMoCua) = 'real' AND gioMoCua BETWEEN 100.0 AND 110.0 THEN gioMoCua
            WHEN typeof(gioDongCua) = 'real' AND gioDongCua BETWEEN 100.0 AND 110.0 THEN gioDongCua
            ELSE 0.0
        END as kinhDo,
        -- giaVe: Tìm từ gioDongCua hoặc dienThoai nếu là số
        CASE 
            WHEN typeof(gioDongCua) = 'real' AND gioDongCua > 0 AND gioDongCua < 1000000 THEN gioDongCua
            ELSE 0.0
        END as giaVe,
        -- gioMoCua: Tìm từ dienThoai hoặc website nếu là time format
        COALESCE(NULLIF(
            CASE 
                WHEN typeof(dienThoai) = 'text' AND dienThoai LIKE '%:%' THEN dienThoai
                WHEN typeof(dienThoai) = 'text' AND dienThoai LIKE '%giờ%' THEN dienThoai
                ELSE ''
            END, ''
        ), '') as gioMoCua,
        -- gioDongCua: Tìm từ website hoặc danhGiaTrungBinh nếu là time format
        COALESCE(NULLIF(
            CASE 
                WHEN typeof(website) = 'text' AND website LIKE '%:%' THEN website
                WHEN typeof(danhGiaTrungBinh) = 'text' AND danhGiaTrungBinh LIKE '%:%' THEN danhGiaTrungBinh
                ELSE ''
            END, ''
        ), '') as gioDongCua,
        -- dienThoai: Tìm từ website hoặc danhGiaTrungBinh nếu là phone format
        COALESCE(NULLIF(
            CASE 
                WHEN typeof(website) = 'text' AND (website LIKE '%0%' OR website LIKE '%+84%') AND LENGTH(website) BETWEEN 8 AND 15 THEN website
                WHEN typeof(danhGiaTrungBinh) = 'text' AND (danhGiaTrungBinh LIKE '%0%' OR danhGiaTrungBinh LIKE '%+84%') AND LENGTH(danhGiaTrungBinh) BETWEEN 8 AND 15 THEN danhGiaTrungBinh
                ELSE ''
            END, ''
        ), '') as dienThoai,
        -- website: Tìm từ soLuotDanhGia nếu là URL
        COALESCE(NULLIF(
            CASE 
                WHEN typeof(soLuotDanhGia) = 'text' AND (soLuotDanhGia LIKE 'http%' OR soLuotDanhGia LIKE 'www.%') THEN soLuotDanhGia
                ELSE ''
            END, ''
        ), '') as website,
        -- danhGiaTrungBinh: Tìm từ soLuotXem nếu là số trong khoảng 0-5
        CASE 
            WHEN typeof(soLuotXem) = 'real' AND soLuotXem BETWEEN 0.0 AND 5.0 THEN soLuotXem
            ELSE 0.0
        END as danhGiaTrungBinh,
        -- soLuotDanhGia: Mặc định 0
        0 as soLuotDanhGia,
        -- soLuotXem: Mặc định 0
        0 as soLuotXem,
        -- maNguoiTao: Giữ nguyên
        maNguoiTao,
        -- ngayTao: Tìm từ trangThai nếu là datetime, nếu không thì now
        CASE 
            WHEN typeof(trangThai) = 'text' AND trangThai LIKE '202%' THEN trangThai
            ELSE datetime('now')
        END as ngayTao,
        -- lanCapNhatCuoi: Tìm từ dacDiem nếu là datetime, nếu không thì now
        CASE 
            WHEN typeof(dacDiem) = 'text' AND dacDiem LIKE '202%' THEN dacDiem
            ELSE datetime('now')
        END as lanCapNhatCuoi,
        -- trangThai: Tìm từ tienNghi nếu hợp lý
        CASE 
            WHEN typeof(tienNghi) = 'text' AND tienNghi IN ('active', 'inactive', 'pending') THEN tienNghi
            ELSE 'active'
        END as trangThai,
        -- dacDiem: Tìm từ maNguoiTao hoặc ngayTao nếu là text dài
        COALESCE(NULLIF(
            CASE 
                WHEN typeof(maNguoiTao) = 'text' AND LENGTH(maNguoiTao) > 20 THEN maNguoiTao
                WHEN typeof(ngayTao) = 'text' AND LENGTH(ngayTao) > 20 THEN ngayTao
                ELSE ''
            END, ''
        ), '') as dacDiem,
        -- tienNghi: Tìm từ maTinhThanh (vị trí 4) nếu là text
        COALESCE(NULLIF(
            CASE 
                WHEN typeof(maTinhThanh) = 'text' THEN maTinhThanh
                WHEN typeof(loaiDiaDiem) = 'text' AND LENGTH(loaiDiaDiem) > 20 THEN loaiDiaDiem
                ELSE ''
            END, ''
        ), '') as tienNghi
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

# Kiểm tra kết quả
print("\n[4/5] Kiểm tra kết quả...")
cursor.execute("SELECT maDiaDiem, tenDiaDiem, maTinhThanh, loaiDiaDiem, viDo, kinhDo, trangThai FROM DIADIEM ORDER BY maDiaDiem LIMIT 5")
samples = cursor.fetchall()
print("   Sample records:")
for sample in samples:
    print(f"     maDiaDiem={sample[0]}, tenDiaDiem={sample[1][:40]}...")
    print(f"       maTinhThanh={sample[2]}, loaiDiaDiem={sample[3]}, viDo={sample[4]}, kinhDo={sample[5]}, trangThai={sample[6]}")

# Tạo indexes
print("\n[5/5] Tạo lại indexes...")
cursor.execute("CREATE INDEX IF NOT EXISTS DIADIEM_maTinhT_58a390_idx ON DIADIEM(maTinhThanh, loaiDiaDiem)")
cursor.execute("CREATE INDEX IF NOT EXISTS DIADIEM_danhGiaTrungBinh_idx ON DIADIEM(danhGiaTrungBinh DESC)")
cursor.execute("CREATE INDEX IF NOT EXISTS DIADIEM_trangThai_idx ON DIADIEM(trangThai)")
cursor.execute("CREATE INDEX IF NOT EXISTS DIADIEM_tenDiaDiem_idx ON DIADIEM(tenDiaDiem)")
conn.commit()

cursor.execute("SELECT COUNT(*) FROM DIADIEM")
total = cursor.fetchone()[0]
print(f"\n✓ Tổng số bản ghi: {total}")

conn.close()

print("\n✅ Hoàn tất!")

