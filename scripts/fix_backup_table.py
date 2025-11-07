#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script để tạo bảng DIADIEM_BACKUP nếu chưa có
"""
import os
import sys
import django
from pathlib import Path

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Setup Django
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'vivu_backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vivu_core.settings')
django.setup()

from django.db import connection

def create_backup_table():
    """Tạo bảng DIADIEM_BACKUP nếu chưa có"""
    with connection.cursor() as cursor:
        # Kiểm tra xem bảng đã tồn tại chưa
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='DIADIEM_BACKUP'
        """)
        if cursor.fetchone():
            print("[INFO] Bảng DIADIEM_BACKUP đã tồn tại")
            return
        
        # Tạo bảng backup với cấu trúc giống DIADIEM
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS DIADIEM_BACKUP (
                maDiaDiem INTEGER PRIMARY KEY,
                tenDiaDiem TEXT,
                moTa TEXT,
                diaChi TEXT,
                maTinhThanh INTEGER,
                loaiDiaDiem TEXT,
                viDo REAL,
                kinhDo REAL,
                giaVe REAL,
                gioMoCua TEXT,
                gioDongCua TEXT,
                dienThoai TEXT,
                website TEXT,
                danhGiaTrungBinh REAL,
                soLuotDanhGia INTEGER,
                soLuotXem INTEGER,
                maNguoiTao INTEGER,
                ngayTao TEXT,
                lanCapNhatCuoi TEXT,
                trangThai TEXT,
                dacDiem TEXT,
                tienNghi TEXT
            )
        """)
        print("[OK] Đã tạo bảng DIADIEM_BACKUP")

if __name__ == '__main__':
    print("="*60)
    print("Tạo bảng DIADIEM_BACKUP")
    print("="*60)
    create_backup_table()
    print("="*60)

