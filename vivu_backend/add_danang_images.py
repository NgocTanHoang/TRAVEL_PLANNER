"""
Thêm hình ảnh cho 5 địa điểm ở Đà Nẵng bằng SQL trực tiếp
"""
import sqlite3
from pathlib import Path

db_path = Path(__file__).resolve().parent / 'db.sqlite3'

print("=" * 70)
print("THÊM HÌNH ẢNH CHO 5 ĐỊA ĐIỂM Ở ĐÀ NẴNG")
print("=" * 70)

# Mapping tên địa điểm -> hình ảnh
images_data = {
    "Cầu Vàng (Golden Bridge) - Sun World Bà Nà Hills": {
        "urlHinhAnh": "/media/places/DaNang/caudao-banahills.jpg",
        "moTa": "Hình ảnh Cầu Vàng với bàn tay khổng lồ",
        "laChinh": 1
    },
    "Ngũ Hành Sơn (Non Nước)": {
        "urlHinhAnh": "/media/places/DaNang/nguhanhson-toan.jpg",
        "moTa": "Hình ảnh toàn cảnh Ngũ Hành Sơn",
        "laChinh": 1
    },
    "Bán đảo Sơn Trà (Chùa Linh Ứng Bãi Bụt)": {
        "urlHinhAnh": "/media/places/DaNang/chualinhung-sontra.jpg",
        "moTa": "Hình ảnh Tượng Phật Quan Âm tại Chùa Linh Ứng",
        "laChinh": 1
    },
    "Bãi biển Mỹ Khê": {
        "urlHinhAnh": "/media/places/DaNang/bienmykhe-danang.jpg",
        "moTa": "Hình ảnh bãi biển Mỹ Khê",
        "laChinh": 1
    },
    "Cầu Rồng": {
        "urlHinhAnh": "/media/places/DaNang/caurong-danang.jpg",
        "moTa": "Hình ảnh Cầu Rồng phun lửa và phun nước",
        "laChinh": 1
    }
}

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

added_count = 0
skipped_count = 0

for ten_dia_diem, img_data in images_data.items():
    print(f"\nXử lý: {ten_dia_diem}")
    
    # Tìm maDiaDiem
    cursor.execute("SELECT maDiaDiem FROM DIADIEM WHERE tenDiaDiem = ?", (ten_dia_diem,))
    result = cursor.fetchone()
    
    if not result:
        print(f"   ✗ Không tìm thấy địa điểm")
        continue
    
    ma_dia_diem = result[0]
    
    # Kiểm tra hình ảnh đã tồn tại chưa
    cursor.execute(
        "SELECT maHinhAnh FROM HINHANHDIADIEM WHERE maDiaDiem = ? AND urlHinhAnh = ?",
        (ma_dia_diem, img_data['urlHinhAnh'])
    )
    if cursor.fetchone():
        print(f"   ⚠ Hình ảnh đã tồn tại")
        skipped_count += 1
        continue
    
    # Lấy maHinhAnh tiếp theo
    cursor.execute("SELECT MAX(maHinhAnh) FROM HINHANHDIADIEM")
    result = cursor.fetchone()
    next_ma_hinh_anh = (result[0] or 0) + 1
    
    # Thêm hình ảnh
    try:
        cursor.execute("""
            INSERT INTO HINHANHDIADIEM (maHinhAnh, maDiaDiem, urlHinhAnh, moTa, laChinh, ngayTao)
            VALUES (?, ?, ?, ?, ?, datetime('now'))
        """, (
            next_ma_hinh_anh,
            ma_dia_diem,
            img_data['urlHinhAnh'],
            img_data['moTa'],
            img_data['laChinh']
        ))
        conn.commit()
        print(f"   ✓ Đã thêm hình ảnh (maHinhAnh: {next_ma_hinh_anh})")
        added_count += 1
    except Exception as e:
        print(f"   ✗ Lỗi: {e}")
        conn.rollback()

conn.close()

print("\n" + "=" * 70)
print("KẾT QUẢ")
print("=" * 70)
print(f"✓ Đã thêm: {added_count} hình ảnh")
print(f"⚠ Đã bỏ qua: {skipped_count} hình ảnh (đã tồn tại)")
print("\n✅ Hoàn tất!")

