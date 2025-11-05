"""
Xuất toàn bộ dữ liệu từ bảng DIADIEM ra file markdown
"""
import sqlite3
from pathlib import Path
from datetime import datetime

db_path = Path(__file__).resolve().parent / 'db.sqlite3'
output_path = Path(__file__).resolve().parent / 'diadiem.md'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=" * 100)
print("XUẤT DỮ LIỆU BẢNG DIADIEM RA FILE MARKDOWN")
print("=" * 100)

# Lấy tất cả dữ liệu từ DIADIEM kèm thông tin TINHTHANH
cursor.execute("""
    SELECT 
        d.maDiaDiem,
        d.tenDiaDiem,
        d.moTa,
        d.diaChi,
        d.maTinhThanh,
        t.tenTinhThanh,
        d.loaiDiaDiem,
        d.viDo,
        d.kinhDo,
        d.giaVe,
        d.gioMoCua,
        d.gioDongCua,
        d.dienThoai,
        d.website,
        d.danhGiaTrungBinh,
        d.soLuotDanhGia,
        d.soLuotXem,
        d.maNguoiTao,
        d.ngayTao,
        d.lanCapNhatCuoi,
        d.trangThai,
        d.dacDiem,
        d.tienNghi
    FROM DIADIEM d
    LEFT JOIN TINHTHANH t ON d.maTinhThanh = t.maTinhThanh
    ORDER BY d.maDiaDiem
""")

all_records = cursor.fetchall()
total = len(all_records)

print(f"\n✓ Đã lấy {total} bản ghi từ bảng DIADIEM")

# Tạo nội dung markdown
md_content = []
md_content.append("# DỮ LIỆU BẢNG DIADIEM\n")
md_content.append(f"**Tổng số địa điểm:** {total}\n")
md_content.append(f"**Ngày xuất:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
md_content.append("---\n")

# Xuất từng bản ghi
for idx, record in enumerate(all_records, start=1):
    (ma_dd, ten_dd, mo_ta, dia_chi, ma_tt, ten_tt, loai_dd, vi_do, kinh_do, 
     gia_ve, gio_mo, gio_dong, dien_thoai, website, danh_gia, so_luot_dg, 
     so_luot_xem, ma_nguoi_tao, ngay_tao, lan_cap_nhat, trang_thai, dac_diem, tien_nghi) = record
    
    md_content.append(f"## {idx}. {ten_dd}\n")
    md_content.append(f"**Mã địa điểm:** {ma_dd}\n")
    md_content.append(f"**Tỉnh thành:** {ten_tt} (maTinhThanh: {ma_tt})\n")
    md_content.append(f"**Loại địa điểm:** {loai_dd}\n")
    md_content.append(f"**Trạng thái:** {trang_thai}\n")
    md_content.append("\n")
    
    # Thông tin cơ bản
    md_content.append("### Thông tin cơ bản\n")
    if dia_chi:
        md_content.append(f"- **Địa chỉ:** {dia_chi}\n")
    if vi_do and vi_do != 0:
        md_content.append(f"- **Vĩ độ:** {vi_do}\n")
    if kinh_do and kinh_do != 0:
        md_content.append(f"- **Kinh độ:** {kinh_do}\n")
    md_content.append("\n")
    
    # Mô tả
    if mo_ta:
        md_content.append("### Mô tả\n")
        md_content.append(f"{mo_ta}\n\n")
    
    # Thông tin chi tiết
    md_content.append("### Thông tin chi tiết\n")
    if gia_ve and gia_ve != 0:
        md_content.append(f"- **Giá vé:** {gia_ve:,.0f} VNĐ\n")
    else:
        md_content.append("- **Giá vé:** Miễn phí\n")
    
    if gio_mo:
        md_content.append(f"- **Giờ mở cửa:** {gio_mo}\n")
    if gio_dong:
        md_content.append(f"- **Giờ đóng cửa:** {gio_dong}\n")
    if dien_thoai:
        md_content.append(f"- **Điện thoại:** {dien_thoai}\n")
    if website:
        md_content.append(f"- **Website:** {website}\n")
    
    md_content.append(f"- **Đánh giá trung bình:** {danh_gia}/5.0\n")
    md_content.append(f"- **Số lượt đánh giá:** {so_luot_dg}\n")
    md_content.append(f"- **Số lượt xem:** {so_luot_xem}\n")
    md_content.append("\n")
    
    # Đặc điểm
    if dac_diem:
        md_content.append("### Đặc điểm\n")
        md_content.append(f"{dac_diem}\n\n")
    
    # Tiện nghi
    if tien_nghi:
        md_content.append("### Tiện nghi\n")
        md_content.append(f"{tien_nghi}\n\n")
    
    # Thông tin hệ thống
    md_content.append("### Thông tin hệ thống\n")
    if ngay_tao:
        md_content.append(f"- **Ngày tạo:** {ngay_tao}\n")
    if lan_cap_nhat:
        md_content.append(f"- **Lần cập nhật cuối:** {lan_cap_nhat}\n")
    if ma_nguoi_tao:
        md_content.append(f"- **Mã người tạo:** {ma_nguoi_tao}\n")
    md_content.append("\n")
    
    md_content.append("---\n\n")

# Ghi vào file
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(''.join(md_content))

conn.close()

print(f"✓ Đã xuất {total} bản ghi ra file: {output_path}")
print(f"✓ File size: {output_path.stat().st_size:,} bytes")

# Hiển thị một vài dòng đầu của file
print("\n" + "=" * 100)
print("PREVIEW FILE (100 dòng đầu):")
print("=" * 100)
with open(output_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()
    for i, line in enumerate(lines[:100], start=1):
        print(f"{i:3}: {line.rstrip()}")

print("\n✅ Hoàn tất!")

