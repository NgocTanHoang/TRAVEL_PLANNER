"""
Script kiểm tra và cập nhật thông tin địa điểm trong database
"""
import os
import sys
import django
from pathlib import Path

# Setup Django
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vivu_core.settings')
django.setup()

from apps.places.models import DiaDiem
from django.db.models import Q


def check_and_update_place():
    """Kiểm tra và cập nhật thông tin địa điểm Chợ vải Ninh Hiệp"""
    
    # Tìm kiếm với các tên có thể có
    search_terms = [
        "Chơ Quân Áo",
        "Chợ vải Ninh Hiệp",
        "chợ Ninh Hiệp",
        "chợ Nành",
        "Ninh Hiệp"
    ]
    
    print("🔍 Đang tìm kiếm địa điểm trong database...")
    
    # Tìm kiếm với tên hoặc địa chỉ
    places = DiaDiem.objects.filter(
        Q(tenDiaDiem__icontains="Chơ Quân Áo") |
        Q(tenDiaDiem__icontains="Chợ vải Ninh Hiệp") |
        Q(tenDiaDiem__icontains="chợ Ninh Hiệp") |
        Q(tenDiaDiem__icontains="chợ Nành") |
        Q(diaChi__icontains="Ninh Hiệp") |
        Q(diaChi__icontains="Gia Lâm")
    ).distinct()
    
    print(f"📊 Tìm thấy {places.count()} địa điểm:")
    print()
    
    for place in places:
        print(f"ID: {place.maDiaDiem}")
        print(f"Tên: {place.tenDiaDiem}")
        print(f"Địa chỉ: {place.diaChi}")
        print(f"Loại: {place.loaiDiaDiem}")
        print(f"Tọa độ: {place.viDo}, {place.kinhDo}")
        print(f"Mô tả: {place.moTa[:100] if place.moTa else 'N/A'}...")
        print("-" * 80)
    
    # Kiểm tra xem có địa điểm nào cần cập nhật không
    places_to_update = places.filter(
        Q(tenDiaDiem__icontains="Chơ Quân Áo") |
        Q(diaChi__icontains="Bắc Ninh") & Q(diaChi__icontains="Gia Lâm")
    )
    
    if places_to_update.exists():
        print(f"\n✏️  Tìm thấy {places_to_update.count()} địa điểm cần cập nhật:")
        print()
        
        for place in places_to_update:
            print(f"Đang cập nhật: {place.tenDiaDiem} (ID: {place.maDiaDiem})")
            
            # Cập nhật thông tin
            place.tenDiaDiem = "Chợ vải Ninh Hiệp"
            place.moTa = "Chợ vải Ninh Hiệp còn có tên gọi khác là chợ Ninh Hiệp (phổ biến), chợ Nành Ninh Hiệp, chợ làng Nành hay chợ Nành là một chợ vải có quy mô lớn tại khu công nghiệp Ninh Hiệp, xã Ninh Hiệp, huyện Gia Lâm, thành phố Hà Nội. Chợ nằm cách trung tâm thành phố Hà Nội khoảng 12 km theo đường chim bay và khoảng 15 km đường bộ. Hiện nay, chợ được biết đến như là một trong những chợ đầu mối trung chuyển vải của Trung Quốc lớn nhất miền Bắc Việt Nam. Chợ vải Ninh Hiệp được báo chí gọi là \"con đường tơ lụa\" và đồng thời là một trong những chợ cổ nhất Việt Nam."
            place.diaChi = "Khu công nghiệp Ninh Hiệp, xã Ninh Hiệp, huyện Gia Lâm, thành phố Hà Nội"
            place.loaiDiaDiem = "shopping"  # Thay đổi từ sightseeing sang shopping
            
            # Cập nhật giờ mở cửa nếu cần
            if place.gioMoCua == "00:00" or not place.gioMoCua:
                place.gioMoCua = "06:00"
            if place.gioDongCua == "23:59" or not place.gioDongCua:
                place.gioDongCua = "18:00"
            
            # Lưu lại
            place.save()
            print(f"✅ Đã cập nhật: {place.tenDiaDiem}")
            print()
        
        print(f"✅ Hoàn tất! Đã cập nhật {places_to_update.count()} địa điểm.")
    else:
        print("\nℹ️  Không tìm thấy địa điểm nào cần cập nhật.")
        print("   (Có thể địa điểm này chưa có trong database hoặc đã có thông tin đúng)")
    
    return places_to_update


if __name__ == '__main__':
    check_and_update_place()

