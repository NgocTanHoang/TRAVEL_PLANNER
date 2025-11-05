"""
Phân tích và sửa lại dữ liệu DIADIEM từ DIADIEM_OLD bằng cách map đúng các trường
"""
import sqlite3
from pathlib import Path
import re

db_path = Path(__file__).resolve().parent / 'db.sqlite3'

print("=" * 100)
print("PHÂN TÍCH VÀ SỬA LẠI DỮ LIỆU DIADIEM")
print("=" * 100)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Lấy cấu trúc của DIADIEM_OLD
cursor.execute("PRAGMA table_info(DIADIEM_OLD)")
old_columns = cursor.fetchall()
old_column_map = {col[1]: idx for idx, col in enumerate(old_columns)}

print(f"\nCấu trúc DIADIEM_OLD ({len(old_columns)} cột):")
for col in old_columns:
    print(f"  {col[0]}: {col[1]} ({col[2]})")

# Lấy một bản ghi mẫu để phân tích
cursor.execute("SELECT * FROM DIADIEM_OLD WHERE maDiaDiem = 1")
sample = cursor.fetchall()[0]

print(f"\nBản ghi mẫu (maDiaDiem=1):")
for idx, (col, val) in enumerate(zip(old_columns, sample)):
    val_str = str(val)[:60] if val is not None else "NULL"
    print(f"  [{idx}] {col[1]:<25} = {val_str}")

# Phân tích: Tìm các giá trị hợp lý từ dữ liệu
print("\n" + "=" * 100)
print("PHÂN TÍCH VÀ MAP DỮ LIỆU:")
print("=" * 100)

# Tìm maTinhThanh hợp lý - cần là integer
cursor.execute("SELECT DISTINCT maTinhThanh FROM DIADIEM_OLD WHERE typeof(maTinhThanh) = 'integer' LIMIT 5")
valid_ma_tinh_thanh = cursor.fetchall()
print(f"\nCác giá trị maTinhThanh hợp lý (integer): {[x[0] for x in valid_ma_tinh_thanh]}")

# Tìm loaiDiaDiem hợp lý
valid_loai = ['dia_danh', 'nha_hang', 'khach_san', 'giai_tri', 'mua_sam', 'khac']
cursor.execute(f"SELECT DISTINCT loaiDiaDiem FROM DIADIEM_OLD WHERE loaiDiaDiem IN ({','.join(['?' for _ in valid_loai])})", valid_loai)
valid_loai_values = cursor.fetchall()
print(f"Các giá trị loaiDiaDiem hợp lý: {[x[0] for x in valid_loai_values]}")

# Kiểm tra xem có cột nào chứa loaiDiaDiem đúng không
for col_idx, col in enumerate(old_columns):
    col_name = col[1]
    # Kiểm tra giá trị trong cột này
    cursor.execute(f"SELECT DISTINCT {col_name} FROM DIADIEM_OLD WHERE {col_name} IN ({','.join(['?' for _ in valid_loai])}) LIMIT 3", valid_loai)
    matches = cursor.fetchall()
    if matches:
        print(f"  ✓ Cột '{col_name}' có giá trị loaiDiaDiem hợp lý: {[x[0] for x in matches]}")

# Tìm viDo, kinhDo hợp lý (số thực trong khoảng hợp lý cho Việt Nam)
cursor.execute("SELECT viDo FROM DIADIEM_OLD WHERE typeof(viDo) = 'real' AND viDo BETWEEN 8.0 AND 24.0 LIMIT 3")
valid_vi_do = cursor.fetchall()
print(f"\nCác giá trị viDo hợp lý (8-24): {[x[0] for x in valid_vi_do]}")

cursor.execute("SELECT kinhDo FROM DIADIEM_OLD WHERE typeof(kinhDo) = 'real' AND kinhDo BETWEEN 100.0 AND 110.0 LIMIT 3")
valid_kinh_do = cursor.fetchall()
print(f"Các giá trị kinhDo hợp lý (100-110): {[x[0] for x in valid_kinh_do]}")

# Tìm trangThai hợp lý
valid_trang_thai = ['active', 'inactive', 'pending']
cursor.execute(f"SELECT DISTINCT trangThai FROM DIADIEM_OLD WHERE trangThai IN ({','.join(['?' for _ in valid_trang_thai])})", valid_trang_thai)
valid_trang_thai_values = cursor.fetchall()
print(f"Các giá trị trangThai hợp lý: {[x[0] for x in valid_trang_thai_values]}")

conn.close()

print("\n" + "=" * 100)
print("KẾT LUẬN:")
print("=" * 100)
print("Dữ liệu trong DIADIEM_OLD đã bị sai thứ tự từ trước.")
print("Cần restore từ backup hoặc sửa lại từng trường dựa trên logic.")

