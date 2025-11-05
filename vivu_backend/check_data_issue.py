"""
Kiểm tra chi tiết vấn đề dữ liệu trong DIADIEM
"""
import sqlite3
from pathlib import Path

db_path = Path(__file__).resolve().parent / 'db.sqlite3'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=" * 100)
print("KIỂM TRA CHI TIẾT VẤN ĐỀ DỮ LIỆU")
print("=" * 100)

# Kiểm tra bảng cũ (DIADIEM_OLD)
print("\n[1] Kiểm tra bảng DIADIEM_OLD:")
try:
    cursor.execute("PRAGMA table_info(DIADIEM_OLD)")
    old_columns = cursor.fetchall()
    old_column_names = [col[1] for col in old_columns]
    print(f"   ✓ Bảng DIADIEM_OLD có {len(old_columns)} cột")
    print(f"   Thứ tự cột: {', '.join(old_column_names)}")
    
    # Lấy một bản ghi từ bảng cũ
    cursor.execute("SELECT * FROM DIADIEM_OLD ORDER BY maDiaDiem LIMIT 1")
    old_record = cursor.fetchone()
    print(f"\n   Bản ghi mẫu từ DIADIEM_OLD:")
    for idx, (col, value) in enumerate(zip(old_columns, old_record)):
        if value is not None and isinstance(value, str) and len(str(value)) > 50:
            display_value = str(value)[:50] + "..."
        else:
            display_value = str(value)
        print(f"     {col[1]:<25}: {display_value}")
        
except Exception as e:
    print(f"   ✗ Không tìm thấy DIADIEM_OLD hoặc lỗi: {e}")

# Kiểm tra bảng mới (DIADIEM)
print("\n[2] Kiểm tra bảng DIADIEM (hiện tại):")
cursor.execute("PRAGMA table_info(DIADIEM)")
new_columns = cursor.fetchall()
new_column_names = [col[1] for col in new_columns]
print(f"   ✓ Bảng DIADIEM có {len(new_columns)} cột")
print(f"   Thứ tự cột: {', '.join(new_column_names)}")

# Lấy một bản ghi từ bảng mới
cursor.execute("SELECT * FROM DIADIEM ORDER BY maDiaDiem LIMIT 1")
new_record = cursor.fetchone()
print(f"\n   Bản ghi mẫu từ DIADIEM:")
for idx, (col, value) in enumerate(zip(new_columns, new_record)):
    if value is not None and isinstance(value, str) and len(str(value)) > 50:
        display_value = str(value)[:50] + "..."
    else:
        display_value = str(value)
    print(f"     {col[1]:<25}: {display_value}")

# So sánh
print("\n[3] So sánh:")
if old_record and new_record:
    print("   So sánh giá trị tại cùng vị trí cột:")
    min_len = min(len(old_columns), len(new_columns))
    for idx in range(min_len):
        old_col_name = old_columns[idx][1]
        new_col_name = new_columns[idx][1]
        old_val = old_record[idx]
        new_val = new_record[idx]
        
        if old_col_name == new_col_name:
            match = "✓" if old_val == new_val else "✗"
            print(f"   {match} {old_col_name:<25}: Cũ={str(old_val)[:30]:<30} | Mới={str(new_val)[:30]:<30}")
        else:
            print(f"   ✗ Khác tên cột: {old_col_name} vs {new_col_name}")

conn.close()

