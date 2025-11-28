#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Script kiểm tra cấu trúc bảng DIADIEM"""
import sqlite3
from pathlib import Path

db_path = Path(__file__).resolve().parent.parent / 'vivu_backend' / 'vivudb.sqlite3'

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

# Lấy thông tin cấu trúc bảng
cursor.execute('PRAGMA table_info(DIADIEM)')
columns = cursor.fetchall()

print('='*100)
print('CÁC TRƯỜNG CỦA BẢNG DIADIEM (theo thứ tự trong database)')
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
cursor.execute("PRAGMA foreign_key_list(DIADIEM)")
fks = cursor.fetchall()
if fks:
    print('\nForeign Keys:')
    for fk in fks:
        print(f"  - {fk[3]} -> {fk[2]}.{fk[4]} (ON DELETE {fk[6]})")

# Lấy thông tin về indexes
cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name='DIADIEM'")
indexes = cursor.fetchall()
if indexes:
    print('\nIndexes:')
    for idx in indexes:
        print(f"  - {idx[0]}")

conn.close()

