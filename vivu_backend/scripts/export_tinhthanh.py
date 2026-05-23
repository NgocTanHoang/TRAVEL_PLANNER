#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script xuất toàn bộ dữ liệu từ bảng TINHTHANH"""
import sqlite3
import csv
import json
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent
db_path = BACKEND_DIR / 'vivudb.sqlite3'
output_dir = REPO_ROOT / 'data'

# Tạo thư mục output nếu chưa có
output_dir.mkdir(exist_ok=True)

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# Lấy tất cả dữ liệu
cursor.execute("SELECT * FROM TINHTHANH ORDER BY tenTinhThanh")
rows = cursor.fetchall()

# Lấy tên cột
column_names = [description[0] for description in cursor.description]

print("="*100)
print("XUẤT DỮ LIỆU BẢNG TINHTHANH")
print("="*100)
print(f"\nTổng số bản ghi: {len(rows)}")
print(f"Các cột: {', '.join(column_names)}")
print("\n" + "="*100)

# Hiển thị trong terminal
print(f"\n{'STT':<5} {'maTinhThanh':<15} {'tenTinhThanh':<30} {'viDo':<12} {'kinhDo':<12} {'moTa':<50}")
print("-"*100)

for i, row in enumerate(rows, 1):
    maTinhThanh = row[0]
    tenTinhThanh = row[1]
    moTa = (row[2] or '')[:47] + '...' if row[2] and len(row[2]) > 50 else (row[2] or '')
    anhDaiDien = row[3] or ''
    viDo = f"{row[4]:.6f}" if row[4] is not None else 'NULL'
    kinhDo = f"{row[5]:.6f}" if row[5] is not None else 'NULL'
    created_at = row[6] or ''
    updated_at = row[7] or ''
    
    print(f"{i:<5} {maTinhThanh:<15} {tenTinhThanh:<30} {viDo:<12} {kinhDo:<12} {moTa:<50}")

# Xuất ra CSV
csv_path = output_dir / 'tinhthanh_export.csv'
with open(csv_path, 'w', newline='', encoding='utf-8-sig') as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(column_names)
    writer.writerows(rows)
print(f"\n✓ Đã xuất ra CSV: {csv_path}")

# Xuất ra JSON
json_data = []
for row in rows:
    json_data.append({
        column_names[i]: row[i] for i in range(len(column_names))
    })

json_path = output_dir / 'tinhthanh_export.json'
with open(json_path, 'w', encoding='utf-8') as jsonfile:
    json.dump(json_data, jsonfile, ensure_ascii=False, indent=2)
print(f"✓ Đã xuất ra JSON: {json_path}")

# Xuất ra SQL INSERT statements
sql_path = output_dir / 'tinhthanh_export.sql'
with open(sql_path, 'w', encoding='utf-8') as sqlfile:
    sqlfile.write("-- Export TINHTHANH table\n")
    sqlfile.write("-- Generated automatically\n\n")
    sqlfile.write("DELETE FROM TINHTHANH;\n\n")
    
    for row in rows:
        values = []
        for val in row:
            if val is None:
                values.append('NULL')
            elif isinstance(val, str):
                # Escape single quotes
                val_escaped = val.replace("'", "''")
                values.append(f"'{val_escaped}'")
            elif isinstance(val, (int, float)):
                values.append(str(val))
            else:
                values.append(f"'{str(val)}'")
        
        sql = f"INSERT INTO TINHTHANH ({', '.join(column_names)}) VALUES ({', '.join(values)});\n"
        sqlfile.write(sql)
print(f"✓ Đã xuất ra SQL: {sql_path}")

conn.close()

print("\n" + "="*100)
print("✓ Hoàn thành xuất dữ liệu!")
print("="*100)

