#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script kiểm tra cấu trúc bảng TINHTHANH"""
import sqlite3
from pathlib import Path

db_path = Path(__file__).resolve().parent.parent / 'vivudb.sqlite3'

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# Lấy thông tin cấu trúc bảng
cursor.execute('PRAGMA table_info(TINHTHANH)')
columns = cursor.fetchall()

print('='*100)
print('CÁC TRƯỜNG CỦA BẢNG TINHTHANH (theo thứ tự trong database)')
print('='*100)
print(f'\n{"STT":<4} {"Tên trường":<25} {"Kiểu dữ liệu":<20} {"NOT NULL":<10} {"Default":<15} {"Primary Key":<12}')
print('-'*100)

for i, col in enumerate(columns, 1):
    cid, name, dtype, notnull, default, pk = col
    notnull_str = "YES" if notnull else "NO"
    default_str = str(default) if default else "NULL"
    pk_str = "YES" if pk else "NO"
    print(f'{i:<4} {name:<25} {dtype:<20} {notnull_str:<10} {default_str:<15} {pk_str:<12}')

print('\n' + '='*100)
print(f'Tổng số trường: {len(columns)}')
print('='*100)

# Lấy thông tin về foreign keys
cursor.execute("PRAGMA foreign_key_list(TINHTHANH)")
fks = cursor.fetchall()
if fks:
    print('\nForeign Keys:')
    for fk in fks:
        print(f"  - {fk[3]} -> {fk[2]}.{fk[4]} (ON DELETE {fk[6]})")
else:
    print('\nForeign Keys: Không có')

# Lấy thông tin về indexes
cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name='TINHTHANH'")
indexes = cursor.fetchall()
if indexes:
    print('\nIndexes:')
    for idx in indexes:
        print(f"  - {idx[0]}")
        if idx[1]:
            print(f"    SQL: {idx[1]}")
else:
    print('\nIndexes: Không có')

# Lấy số lượng bản ghi
cursor.execute("SELECT COUNT(*) FROM TINHTHANH")
count = cursor.fetchone()[0]
print(f'\nSố lượng bản ghi: {count}')

# Lấy một vài mẫu dữ liệu
print('\nMột số mẫu dữ liệu:')
cursor.execute("SELECT * FROM TINHTHANH LIMIT 5")
samples = cursor.fetchall()
if samples:
    # Lấy tên cột
    column_names = [description[0] for description in cursor.description]
    print(f"\n{' | '.join(column_names)}")
    print('-' * 100)
    for sample in samples:
        print(' | '.join(str(val) if val is not None else 'NULL' for val in sample))

conn.close()

