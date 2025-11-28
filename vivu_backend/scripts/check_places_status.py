"""Check status of places from row 58 onwards"""
import sqlite3
import os
import sys
from pathlib import Path

# Find database path - script is in scripts/ folder, db is in parent folder
script_dir = Path(__file__).resolve().parent
db_path = script_dir.parent / 'vivudb.sqlite3'

if not db_path.exists():
    # Try current directory
    db_path = Path('vivudb.sqlite3')
    if not db_path.exists():
        print(f"Error: Cannot find vivudb.sqlite3")
        print(f"Tried: {script_dir.parent / 'vivudb.sqlite3'}")
        print(f"Tried: {Path('vivudb.sqlite3').absolute()}")
        sys.exit(1)

db_path = str(db_path)
print(f"Using database: {db_path}")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Count places from row 58
cursor.execute('SELECT COUNT(*) FROM DIADIEM WHERE rowid >= 58')
total = cursor.fetchone()[0]

# Count places with missing coordinates
cursor.execute('SELECT COUNT(*) FROM DIADIEM WHERE rowid >= 58 AND (viDo = 0.0 OR viDo IS NULL OR kinhDo = 0.0 OR kinhDo IS NULL)')
missing_coords = cursor.fetchone()[0]

# Count places with missing amenities
cursor.execute('SELECT COUNT(*) FROM DIADIEM WHERE rowid >= 58 AND (tienNghi IS NULL OR tienNghi = "")')
missing_amenities = cursor.fetchone()[0]

# Count places with missing description
cursor.execute('SELECT COUNT(*) FROM DIADIEM WHERE rowid >= 58 AND (moTa IS NULL OR moTa = "" OR LENGTH(moTa) < 50)')
missing_desc = cursor.fetchone()[0]

# Count places with dia_danh that might be wrong
cursor.execute('SELECT COUNT(*) FROM DIADIEM WHERE rowid >= 58 AND loaiDiaDiem = "dia_danh" AND (tenDiaDiem LIKE "%khách sạn%" OR tenDiaDiem LIKE "%hotel%" OR tenDiaDiem LIKE "%resort%" OR tenDiaDiem LIKE "%nhà hàng%" OR tenDiaDiem LIKE "%restaurant%")')
wrong_type = cursor.fetchone()[0]

print("="*60)
print("STATUS OF PLACES FROM ROW 58 ONWARDS")
print("="*60)
print(f"Total places: {total:,}")
print(f"Missing coordinates: {missing_coords:,} ({missing_coords*100/total:.1f}%)")
print(f"Missing amenities: {missing_amenities:,} ({missing_amenities*100/total:.1f}%)")
print(f"Missing/weak description: {missing_desc:,} ({missing_desc*100/total:.1f}%)")
print(f"Potentially wrong type (dia_danh): {wrong_type:,} ({wrong_type*100/total:.1f}%)")
print("="*60)

conn.close()

