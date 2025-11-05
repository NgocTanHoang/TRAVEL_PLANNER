"""
Verify 5 địa điểm ở Đà Nẵng đã được thêm/cập nhật
"""
import sqlite3
from pathlib import Path

db_path = Path(__file__).resolve().parent / 'db.sqlite3'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=" * 70)
print("KIỂM TRA 5 ĐỊA ĐIỂM Ở ĐÀ NẴNG")
print("=" * 70)

places = [
    "Cầu Vàng (Golden Bridge) - Sun World Bà Nà Hills",
    "Ngũ Hành Sơn (Non Nước)",
    "Bán đảo Sơn Trà (Chùa Linh Ứng Bãi Bụt)",
    "Bãi biển Mỹ Khê",
    "Cầu Rồng"
]

for idx, ten_dia_diem in enumerate(places, start=1):
    print(f"\n[{idx}/5] {ten_dia_diem}")
    
    cursor.execute("""
        SELECT maDiaDiem, moTa, diaChi, loaiDiaDiem, danhGiaTrungBinh, trangThai
        FROM DIADIEM WHERE tenDiaDiem = ?
    """, (ten_dia_diem,))
    
    result = cursor.fetchone()
    if result:
        ma_dia_diem, mo_ta, dia_chi, loai, danh_gia, trang_thai = result
        print(f"   ✓ maDiaDiem: {ma_dia_diem}")
        print(f"   ✓ Loại: {loai}")
        print(f"   ✓ Đánh giá: {danh_gia}")
        print(f"   ✓ Trạng thái: {trang_thai}")
        print(f"   ✓ Mô tả: {mo_ta[:100]}...")
        
        # Kiểm tra hình ảnh
        cursor.execute("""
            SELECT COUNT(*) FROM HINHANHDIADIEM WHERE maDiaDiem = ?
        """, (ma_dia_diem,))
        img_count = cursor.fetchone()[0]
        print(f"   ✓ Số hình ảnh: {img_count}")
    else:
        print(f"   ✗ Không tìm thấy")

conn.close()

print("\n" + "=" * 70)
print("✅ Hoàn tất kiểm tra!")

