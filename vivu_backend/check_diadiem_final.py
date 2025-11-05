"""
Kiểm tra lại các cột từ maTinhThanh đến hết trong DIADIEM và so sánh với backup
"""
import sqlite3
import json
from pathlib import Path

db_path = Path(__file__).resolve().parent / 'db.sqlite3'
backup_path = Path(__file__).resolve().parent.parent / 'data' / 'exports' / 'diadiem_export_20251104_213742.json'

print("=" * 100)
print("KIỂM TRA CÁC CỘT TỪ maTinhThanh ĐẾN HẾT")
print("=" * 100)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

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

print(f"\n[1] Cấu trúc các cột từ maTinhThanh đến hết (tổng {len(columns_to_check)} cột):")
print("-" * 100)
print(f"{'STT':<5} | {'Tên trường':<25} | {'Type':<20} | {'NOT NULL':<10}")
print("-" * 100)

for idx, col in enumerate(columns_to_check, start=ma_tinh_thanh_index + 1):
    cid, name, col_type, not_null, default_value, pk = col
    null_str = "NOT NULL" if not_null else "NULL"
    print(f"{idx:<5} | {name:<25} | {col_type:<20} | {null_str:<10}")

# Lấy một vài bản ghi mẫu
print("\n[2] Nội dung mẫu của các cột (3 bản ghi đầu tiên):")
print("=" * 100)

column_names = [col[1] for col in columns_to_check]
columns_str = ', '.join(column_names)
cursor.execute(f"SELECT {columns_str} FROM DIADIEM ORDER BY maDiaDiem LIMIT 3")
records = cursor.fetchall()

for rec_idx, record in enumerate(records, start=1):
    print(f"\nBản ghi {rec_idx}:")
    print("-" * 100)
    for idx, (col, value) in enumerate(zip(columns_to_check, record)):
        col_name = col[1]
        if value is None:
            display_value = "NULL"
        elif isinstance(value, str) and len(value) > 60:
            display_value = value[:57] + "..."
        else:
            display_value = str(value)
        print(f"  {col_name:<25}: {display_value}")

# Kiểm tra backup JSON
print("\n" + "=" * 100)
print("[3] So sánh với backup JSON:")
print("=" * 100)

if backup_path.exists():
    with open(backup_path, 'r', encoding='utf-8') as f:
        backup_data = json.load(f)
    
    print(f"✓ Tìm thấy backup JSON với {len(backup_data)} bản ghi")
    
    # Tìm các bản ghi trong backup có maDiaDiem trùng với database
    cursor.execute("SELECT maDiaDiem FROM DIADIEM ORDER BY maDiaDiem LIMIT 5")
    db_ids = [row[0] for row in cursor.fetchall()]
    
    print(f"\nKiểm tra các bản ghi có maDiaDiem trong database ({db_ids[:3]}...):")
    for db_id in db_ids[:3]:
        backup_record = next((r for r in backup_data if r.get('maDiaDiem') == db_id), None)
        if backup_record:
            print(f"\n  Backup record maDiaDiem={db_id}:")
            for col_name in column_names:
                value = backup_record.get(col_name, 'N/A')
                if isinstance(value, str) and len(value) > 50:
                    value = value[:47] + "..."
                print(f"    {col_name:<25}: {value}")
        else:
            print(f"  ✗ Không tìm thấy maDiaDiem={db_id} trong backup")
else:
    print(f"✗ Không tìm thấy backup tại {backup_path}")

conn.close()

print("\n" + "=" * 100)
print("✅ Hoàn tất kiểm tra!")
print("=" * 100)

