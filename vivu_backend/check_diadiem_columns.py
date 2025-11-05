"""
Kiểm tra các cột từ maTinhThanh đến hết trong bảng DIADIEM và nội dung của chúng
"""
import sqlite3
from pathlib import Path

db_path = Path(__file__).resolve().parent / 'db.sqlite3'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=" * 100)
print("KIỂM TRA CÁC CỘT TỪ maTinhThanh ĐẾN HẾT TRONG BẢNG DIADIEM")
print("=" * 100)

# Lấy thông tin các cột
cursor.execute("PRAGMA table_info(DIADIEM)")
all_columns = cursor.fetchall()

# Tìm vị trí maTinhThanh
ma_tinh_thanh_index = None
for idx, col in enumerate(all_columns):
    if col[1] == 'maTinhThanh':
        ma_tinh_thanh_index = idx
        break

if ma_tinh_thanh_index is None:
    print("✗ Không tìm thấy cột maTinhThanh")
    conn.close()
    exit(1)

# Lấy các cột từ maTinhThanh đến hết
columns_to_check = all_columns[ma_tinh_thanh_index:]

print(f"\nCác cột từ maTinhThanh đến hết (tổng {len(columns_to_check)} cột):")
print("=" * 100)
print(f"{'STT':<5} | {'Tên trường':<25} | {'Type':<20} | {'NOT NULL':<10} | {'Default':<20}")
print("-" * 100)

for idx, col in enumerate(columns_to_check, start=ma_tinh_thanh_index + 1):
    cid, name, col_type, not_null, default_value, pk = col
    null_str = "NOT NULL" if not_null else "NULL"
    default_str = str(default_value) if default_value else ""
    print(f"{idx:<5} | {name:<25} | {col_type:<20} | {null_str:<10} | {default_str:<20}")

# Lấy một vài bản ghi mẫu để xem nội dung
print("\n" + "=" * 100)
print("NỘI DUNG MẪU CỦA CÁC CỘT (lấy 3 bản ghi đầu tiên):")
print("=" * 100)

# Lấy tên các cột từ maTinhThanh đến hết
column_names = [col[1] for col in columns_to_check]

# Query để lấy dữ liệu
columns_str = ', '.join(column_names)
cursor.execute(f"SELECT {columns_str} FROM DIADIEM ORDER BY maDiaDiem LIMIT 3")
records = cursor.fetchall()

print("\nBản ghi 1:")
print("-" * 100)
for idx, (col, value) in enumerate(zip(columns_to_check, records[0] if records else [])):
    col_name = col[1]
    # Format giá trị
    if value is None:
        display_value = "NULL"
    elif isinstance(value, str) and len(value) > 50:
        display_value = value[:47] + "..."
    else:
        display_value = str(value)
    print(f"  {col_name:<25}: {display_value}")

if len(records) > 1:
    print("\nBản ghi 2:")
    print("-" * 100)
    for idx, (col, value) in enumerate(zip(columns_to_check, records[1])):
        col_name = col[1]
        if value is None:
            display_value = "NULL"
        elif isinstance(value, str) and len(value) > 50:
            display_value = value[:47] + "..."
        else:
            display_value = str(value)
        print(f"  {col_name:<25}: {display_value}")

if len(records) > 2:
    print("\nBản ghi 3:")
    print("-" * 100)
    for idx, (col, value) in enumerate(zip(columns_to_check, records[2])):
        col_name = col[1]
        if value is None:
            display_value = "NULL"
        elif isinstance(value, str) and len(value) > 50:
            display_value = value[:47] + "..."
        else:
            display_value = str(value)
        print(f"  {col_name:<25}: {display_value}")

# Kiểm tra thống kê cho một số cột quan trọng
print("\n" + "=" * 100)
print("THỐNG KÊ MỘT SỐ CỘT QUAN TRỌNG:")
print("=" * 100)

# Thống kê maTinhThanh
cursor.execute("SELECT maTinhThanh, COUNT(*) FROM DIADIEM GROUP BY maTinhThanh ORDER BY COUNT(*) DESC LIMIT 5")
print("\nTop 5 maTinhThanh (số lượng địa điểm):")
for ma_tinh_thanh, count in cursor.fetchall():
    cursor.execute("SELECT tenTinhThanh FROM TINHTHANH WHERE maTinhThanh = ?", (ma_tinh_thanh,))
    ten_tinh_thanh = cursor.fetchone()
    ten = ten_tinh_thanh[0] if ten_tinh_thanh else "Unknown"
    print(f"  {ma_tinh_thanh} ({ten}): {count} địa điểm")

# Thống kê loaiDiaDiem
cursor.execute("SELECT loaiDiaDiem, COUNT(*) FROM DIADIEM GROUP BY loaiDiaDiem")
print("\nPhân bố theo loaiDiaDiem:")
for loai, count in cursor.fetchall():
    print(f"  {loai:<20}: {count} địa điểm")

# Thống kê trangThai
cursor.execute("SELECT trangThai, COUNT(*) FROM DIADIEM GROUP BY trangThai")
print("\nPhân bố theo trangThai:")
for trang_thai, count in cursor.fetchall():
    print(f"  {trang_thai:<20}: {count} địa điểm")

# Kiểm tra NULL values
print("\nKiểm tra NULL values:")
for col in columns_to_check:
    col_name = col[1]
    if col[3] == 0:  # Có thể NULL
        cursor.execute(f"SELECT COUNT(*) FROM DIADIEM WHERE {col_name} IS NULL")
        null_count = cursor.fetchone()[0]
        if null_count > 0:
            print(f"  {col_name:<25}: {null_count} NULL values")

conn.close()

print("\n" + "=" * 100)
print("✅ Hoàn tất kiểm tra!")

