#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script để xóa các địa điểm kém chất lượng trong bảng DIADIEM
- Xóa các record từ maDiaDiem 105 đến 243
- Xóa các record từ maDiaDiem 257 đến hết
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

from apps.places.models import DiaDiem
from django.db.models import Max


def delete_low_quality_places():
    """Xóa các địa điểm kém chất lượng"""
    print("="*60)
    print("XÓA CÁC ĐỊA ĐIỂM KÉM CHẤT LƯỢNG TRONG BẢNG DIADIEM")
    print("="*60)
    print()
    
    # Lấy max ID để xác định phạm vi "đến hết"
    max_id = DiaDiem.objects.aggregate(max_id=Max('maDiaDiem'))['max_id']
    if max_id is None:
        print("[INFO] Không có địa điểm nào trong database.")
        return
    
    print(f"[INFO] ID lớn nhất trong database: {max_id}")
    print()
    
    # Xóa từ 105 đến 243
    print("Đang xóa các địa điểm từ ID 105 đến 243...")
    places_range1 = DiaDiem.objects.filter(maDiaDiem__gte=105, maDiaDiem__lte=243)
    count_range1 = places_range1.count()
    
    if count_range1 > 0:
        # Hiển thị danh sách trước khi xóa
        print(f"Tìm thấy {count_range1} địa điểm:")
        for place in places_range1.values_list('maDiaDiem', 'tenDiaDiem'):
            print(f"  - ID {place[0]}: {place[1]}")
        
        # Xác nhận
        print()
        places_range1.delete()
        print(f"[OK] Đã xóa {count_range1} địa điểm (ID 105-243)")
    else:
        print("[INFO] Không tìm thấy địa điểm nào trong khoảng 105-243")
    
    print()
    
    # Xóa từ 257 đến hết
    print(f"Đang xóa các địa điểm từ ID 257 đến {max_id}...")
    places_range2 = DiaDiem.objects.filter(maDiaDiem__gte=257)
    count_range2 = places_range2.count()
    
    if count_range2 > 0:
        # Hiển thị danh sách trước khi xóa
        print(f"Tìm thấy {count_range2} địa điểm:")
        for place in places_range2.values_list('maDiaDiem', 'tenDiaDiem'):
            print(f"  - ID {place[0]}: {place[1]}")
        
        # Xác nhận
        print()
        places_range2.delete()
        print(f"[OK] Đã xóa {count_range2} địa điểm (ID 257-{max_id})")
    else:
        print("[INFO] Không tìm thấy địa điểm nào trong khoảng 257-hết")
    
    print()
    print("="*60)
    print(f"KẾT QUẢ XÓA:")
    print(f"  - Đã xóa {count_range1} địa điểm (ID 105-243)")
    print(f"  - Đã xóa {count_range2} địa điểm (ID 257-{max_id})")
    print(f"  - Tổng cộng: {count_range1 + count_range2} địa điểm đã bị xóa")
    print("="*60)
    
    # Kiểm tra lại số lượng còn lại
    remaining_count = DiaDiem.objects.count()
    print(f"\n[INFO] Số địa điểm còn lại trong database: {remaining_count}")


if __name__ == '__main__':
    delete_low_quality_places()
    print("\n[OK] Hoàn thành!")
