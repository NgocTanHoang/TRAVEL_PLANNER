#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script import fallback activities vào database
Thay vì hardcode trong code, lưu vào database để dễ quản lý và mở rộng
"""
import os
import sys
import django
import json
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

from apps.places.models import DiaDiem, TinhThanh

# Fallback activities data
FALLBACK_ACTIVITIES = {
    'Vũng Tàu': [
        {
            'tenDiaDiem': 'Bãi Sau',
            'moTa': 'Bãi biển đẹp, lãng mạn với cát trắng và nước trong xanh, phù hợp cho cặp đôi. Bãi biển dài, rộng, có nhiều hoạt động giải trí như lướt sóng, chơi thể thao biển.',
            'diaChi': 'Bãi Sau, Vũng Tàu',
            'loaiDiaDiem': 'giai_tri',
            'giaVe': 0,
            'viDo': 10.34599,
            'kinhDo': 107.08426,
            'danhGiaTrungBinh': 4.5,
            'soLuotDanhGia': 100,
            'dacDiem': json.dumps({
                'type': 'beach',
                'duration_hours': 3,
                'is_fallback': True,
                'tags': ['beach', 'romantic', 'swimming', 'sunset']
            })
        },
        {
            'tenDiaDiem': 'Bãi Trước',
            'moTa': 'Bãi biển trung tâm, gần các nhà hàng và quán cà phê lãng mạn. View đẹp, không gian thoáng đãng, phù hợp cho buổi tối đi dạo.',
            'diaChi': 'Bãi Trước, Vũng Tàu',
            'loaiDiaDiem': 'giai_tri',
            'giaVe': 0,
            'viDo': 10.34699,
            'kinhDo': 107.08526,
            'danhGiaTrungBinh': 4.3,
            'soLuotDanhGia': 80,
            'dacDiem': json.dumps({
                'type': 'beach',
                'duration_hours': 2,
                'is_fallback': True,
                'tags': ['beach', 'romantic', 'walking', 'dining']
            })
        },
        {
            'tenDiaDiem': 'Tượng Chúa Kitô Vua',
            'moTa': 'Tượng Chúa Kitô Vua trên núi Nhỏ, view đẹp ra biển, điểm check-in lãng mạn. Từ đây có thể ngắm toàn cảnh Vũng Tàu, đặc biệt đẹp vào lúc hoàng hôn.',
            'diaChi': 'Núi Nhỏ, Vũng Tàu',
            'loaiDiaDiem': 'dia_danh',
            'giaVe': 0,
            'viDo': 10.35000,
            'kinhDo': 107.09000,
            'danhGiaTrungBinh': 4.7,
            'soLuotDanhGia': 150,
            'dacDiem': json.dumps({
                'type': 'sightseeing',
                'duration_hours': 1.5,
                'is_fallback': True,
                'tags': ['sightseeing', 'romantic', 'viewpoint', 'sunset', 'religious']
            })
        },
        {
            'tenDiaDiem': 'Lâu đài Trắng (Villa Blanche)',
            'moTa': 'Lâu đài cổ đẹp, kiến trúc Pháp, điểm check-in lãng mạn. Công trình kiến trúc độc đáo, phù hợp cho các cặp đôi chụp ảnh.',
            'diaChi': 'Lâu đài Trắng, Vũng Tàu',
            'loaiDiaDiem': 'dia_danh',
            'giaVe': 50000,
            'viDo': 10.34800,
            'kinhDo': 107.08800,
            'danhGiaTrungBinh': 4.4,
            'soLuotDanhGia': 90,
            'dacDiem': json.dumps({
                'type': 'sightseeing',
                'duration_hours': 1,
                'is_fallback': True,
                'tags': ['sightseeing', 'romantic', 'photography', 'architecture']
            })
        },
        {
            'tenDiaDiem': 'Hải đăng Vũng Tàu',
            'moTa': 'Hải đăng cổ, view 360 độ ra biển và thành phố, lãng mạn vào buổi tối. Một trong những hải đăng lâu đời nhất Việt Nam.',
            'diaChi': 'Hải đăng Vũng Tàu',
            'loaiDiaDiem': 'dia_danh',
            'giaVe': 30000,
            'viDo': 10.34700,
            'kinhDo': 107.08600,
            'danhGiaTrungBinh': 4.6,
            'soLuotDanhGia': 120,
            'dacDiem': json.dumps({
                'type': 'sightseeing',
                'duration_hours': 1,
                'is_fallback': True,
                'tags': ['sightseeing', 'romantic', 'viewpoint', 'historical']
            })
        },
        {
            'tenDiaDiem': 'Núi Minh Đạm',
            'moTa': 'Núi với view đẹp, không gian yên tĩnh, phù hợp cho cặp đôi. Có thể leo núi, ngắm cảnh, tham quan di tích lịch sử.',
            'diaChi': 'Núi Minh Đạm, Vũng Tàu',
            'loaiDiaDiem': 'dia_danh',
            'giaVe': 0,
            'viDo': 10.36000,
            'kinhDo': 107.10000,
            'danhGiaTrungBinh': 4.2,
            'soLuotDanhGia': 60,
            'dacDiem': json.dumps({
                'type': 'sightseeing',
                'duration_hours': 2,
                'is_fallback': True,
                'tags': ['sightseeing', 'romantic', 'hiking', 'viewpoint']
            })
        }
    ],
    'Hà Nội': [
        {
            'tenDiaDiem': 'Hồ Hoàn Kiếm',
            'moTa': 'Hồ nước đẹp ở trung tâm Hà Nội, biểu tượng của thủ đô. Xung quanh có nhiều di tích lịch sử, phù hợp cho đi dạo, chụp ảnh.',
            'diaChi': 'Hồ Hoàn Kiếm, Hoàn Kiếm, Hà Nội',
            'loaiDiaDiem': 'dia_danh',
            'giaVe': 0,
            'viDo': 21.0285,
            'kinhDo': 105.8542,
            'danhGiaTrungBinh': 4.6,
            'soLuotDanhGia': 500,
            'dacDiem': json.dumps({
                'type': 'sightseeing',
                'duration_hours': 2,
                'is_fallback': True,
                'tags': ['sightseeing', 'walking', 'historical', 'photography']
            })
        },
        {
            'tenDiaDiem': 'Văn Miếu - Quốc Tử Giám',
            'moTa': 'Di tích lịch sử quan trọng, trường đại học đầu tiên của Việt Nam. Kiến trúc cổ kính, không gian yên tĩnh, phù hợp tìm hiểu văn hóa.',
            'diaChi': 'Văn Miếu, Đống Đa, Hà Nội',
            'loaiDiaDiem': 'dia_danh',
            'giaVe': 30000,
            'viDo': 21.0265,
            'kinhDo': 105.8362,
            'danhGiaTrungBinh': 4.5,
            'soLuotDanhGia': 400,
            'dacDiem': json.dumps({
                'type': 'museum',
                'duration_hours': 2,
                'is_fallback': True,
                'tags': ['museum', 'historical', 'cultural', 'education']
            })
        },
        {
            'tenDiaDiem': 'Phố cổ Hà Nội',
            'moTa': 'Khu phố cổ với 36 phố phường, nơi lưu giữ nét văn hóa truyền thống Hà Nội. Nhiều cửa hàng, quán ăn, điểm tham quan thú vị.',
            'diaChi': 'Phố cổ Hà Nội, Hoàn Kiếm, Hà Nội',
            'loaiDiaDiem': 'dia_danh',
            'giaVe': 0,
            'viDo': 21.0333,
            'kinhDo': 105.8500,
            'danhGiaTrungBinh': 4.4,
            'soLuotDanhGia': 350,
            'dacDiem': json.dumps({
                'type': 'sightseeing',
                'duration_hours': 3,
                'is_fallback': True,
                'tags': ['sightseeing', 'walking', 'shopping', 'dining', 'cultural']
            })
        },
        {
            'tenDiaDiem': 'Lăng Chủ tịch Hồ Chí Minh',
            'moTa': 'Di tích lịch sử quan trọng, nơi an nghỉ của Chủ tịch Hồ Chí Minh. Kiến trúc trang nghiêm, không gian rộng lớn.',
            'diaChi': 'Lăng Chủ tịch Hồ Chí Minh, Ba Đình, Hà Nội',
            'loaiDiaDiem': 'dia_danh',
            'giaVe': 0,
            'viDo': 21.0367,
            'kinhDo': 105.8344,
            'danhGiaTrungBinh': 4.7,
            'soLuotDanhGia': 600,
            'dacDiem': json.dumps({
                'type': 'sightseeing',
                'duration_hours': 1.5,
                'is_fallback': True,
                'tags': ['sightseeing', 'historical', 'cultural', 'monument']
            })
        },
        {
            'tenDiaDiem': 'Chùa Một Cột',
            'moTa': 'Ngôi chùa có kiến trúc độc đáo, biểu tượng của Hà Nội. Chùa được xây dựng trên một cột đá, kiến trúc độc đáo hiếm có.',
            'diaChi': 'Chùa Một Cột, Ba Đình, Hà Nội',
            'loaiDiaDiem': 'dia_danh',
            'giaVe': 25000,
            'viDo': 21.0356,
            'kinhDo': 105.8322,
            'danhGiaTrungBinh': 4.3,
            'soLuotDanhGia': 300,
            'dacDiem': json.dumps({
                'type': 'temple',
                'duration_hours': 1,
                'is_fallback': True,
                'tags': ['temple', 'historical', 'architecture', 'religious']
            })
        }
    ],
    'Thành phố Hồ Chí Minh': [
        {
            'tenDiaDiem': 'Bến Nhà Rồng',
            'moTa': 'Bảo tàng Hồ Chí Minh, nơi Bác Hồ ra đi tìm đường cứu nước. Di tích lịch sử quan trọng, có nhiều hiện vật và tài liệu quý giá.',
            'diaChi': 'Bến Nhà Rồng, Quận 4, TP.HCM',
            'loaiDiaDiem': 'dia_danh',
            'giaVe': 30000,
            'viDo': 10.7689,
            'kinhDo': 106.7042,
            'danhGiaTrungBinh': 4.5,
            'soLuotDanhGia': 400,
            'dacDiem': json.dumps({
                'type': 'museum',
                'duration_hours': 1.5,
                'is_fallback': True,
                'tags': ['museum', 'historical', 'cultural', 'education']
            })
        },
        {
            'tenDiaDiem': 'Dinh Độc Lập',
            'moTa': 'Di tích lịch sử quan trọng, nơi đánh dấu sự kiện 30/4/1975. Kiến trúc độc đáo, có nhiều phòng trưng bày và hiện vật lịch sử.',
            'diaChi': 'Dinh Độc Lập, Quận 1, TP.HCM',
            'loaiDiaDiem': 'dia_danh',
            'giaVe': 40000,
            'viDo': 10.7769,
            'kinhDo': 106.6950,
            'danhGiaTrungBinh': 4.6,
            'soLuotDanhGia': 500,
            'dacDiem': json.dumps({
                'type': 'museum',
                'duration_hours': 2,
                'is_fallback': True,
                'tags': ['museum', 'historical', 'cultural', 'monument']
            })
        },
        {
            'tenDiaDiem': 'Chợ Bến Thành',
            'moTa': 'Chợ truyền thống nổi tiếng, nơi mua sắm và thưởng thức ẩm thực. Có nhiều gian hàng, quán ăn, đặc sản địa phương.',
            'diaChi': 'Chợ Bến Thành, Quận 1, TP.HCM',
            'loaiDiaDiem': 'mua_sam',
            'giaVe': 0,
            'viDo': 10.7720,
            'kinhDo': 106.6980,
            'danhGiaTrungBinh': 4.2,
            'soLuotDanhGia': 350,
            'dacDiem': json.dumps({
                'type': 'sightseeing',
                'duration_hours': 2,
                'is_fallback': True,
                'tags': ['shopping', 'dining', 'cultural', 'market']
            })
        },
        {
            'tenDiaDiem': 'Nhà thờ Đức Bà',
            'moTa': 'Nhà thờ cổ kính, biểu tượng của Sài Gòn. Kiến trúc Pháp đẹp, không gian trang nghiêm, điểm check-in nổi tiếng.',
            'diaChi': 'Nhà thờ Đức Bà, Quận 1, TP.HCM',
            'loaiDiaDiem': 'dia_danh',
            'giaVe': 0,
            'viDo': 10.7797,
            'kinhDo': 106.6990,
            'danhGiaTrungBinh': 4.4,
            'soLuotDanhGia': 400,
            'dacDiem': json.dumps({
                'type': 'temple',
                'duration_hours': 1,
                'is_fallback': True,
                'tags': ['temple', 'architecture', 'photography', 'religious']
            })
        },
        {
            'tenDiaDiem': 'Landmark 81',
            'moTa': 'Tòa nhà cao nhất Việt Nam, có đài quan sát và khu mua sắm. View đẹp ra toàn thành phố, nhiều nhà hàng và giải trí.',
            'diaChi': 'Landmark 81, Bình Thạnh, TP.HCM',
            'loaiDiaDiem': 'giai_tri',
            'giaVe': 200000,
            'viDo': 10.7947,
            'kinhDo': 106.7219,
            'danhGiaTrungBinh': 4.5,
            'soLuotDanhGia': 450,
            'dacDiem': json.dumps({
                'type': 'sightseeing',
                'duration_hours': 2,
                'is_fallback': True,
                'tags': ['sightseeing', 'viewpoint', 'shopping', 'dining', 'modern']
            })
        }
    ]
}


def import_fallback_activities():
    """Import fallback activities vào database"""
    print("="*80)
    print("IMPORT FALLBACK ACTIVITIES VÀO DATABASE")
    print("="*80)
    
    total_imported = 0
    total_updated = 0
    total_skipped = 0
    
    for city_name, activities in FALLBACK_ACTIVITIES.items():
        print(f"\n📍 Đang xử lý: {city_name}")
        
        # Lấy hoặc tạo TinhThanh
        tinh_thanh, created = TinhThanh.objects.get_or_create(
            tenTinhThanh=city_name,
            defaults={'moTa': f'Thông tin về {city_name}'}
        )
        if created:
            tinh_thanh.save()  # Đảm bảo đã lưu vào DB
        print(f"   ✅ Tỉnh thành: {tinh_thanh.tenTinhThanh} (ID: {tinh_thanh.maTinhThanh})")
        
        for activity_data in activities:
            ten_dia_diem = activity_data['tenDiaDiem']
            
            # Kiểm tra xem đã tồn tại chưa
            existing = DiaDiem.objects.filter(
                tenDiaDiem=ten_dia_diem,
                maTinhThanh=tinh_thanh
            ).first()
            
            if existing:
                # Cập nhật nếu là fallback activity
                dac_diem = json.loads(activity_data.get('dacDiem', '{}'))
                if dac_diem.get('is_fallback'):
                    # Cập nhật thông tin
                    for key, value in activity_data.items():
                        if key != 'tenDiaDiem' and hasattr(existing, key):
                            setattr(existing, key, value)
                    existing.trangThai = 'active'
                    existing.save()
                    total_updated += 1
                    print(f"   🔄 Cập nhật: {ten_dia_diem}")
                else:
                    total_skipped += 1
                    print(f"   ⏭️  Bỏ qua (không phải fallback): {ten_dia_diem}")
            else:
                # Tạo mới
                # Refresh tinh_thanh từ database để đảm bảo có ID
                tinh_thanh.refresh_from_db()
                
                # Tạo DiaDiem với các field cần thiết
                dia_diem = DiaDiem(
                    tenDiaDiem=activity_data['tenDiaDiem'],
                    moTa=activity_data.get('moTa', ''),
                    diaChi=activity_data.get('diaChi', ''),
                    maTinhThanh=tinh_thanh,
                    loaiDiaDiem=activity_data.get('loaiDiaDiem', 'dia_danh'),
                    viDo=activity_data.get('viDo'),
                    kinhDo=activity_data.get('kinhDo'),
                    giaVe=activity_data.get('giaVe', 0),
                    danhGiaTrungBinh=activity_data.get('danhGiaTrungBinh', 0),
                    soLuotDanhGia=activity_data.get('soLuotDanhGia', 0),
                    dacDiem=activity_data.get('dacDiem', '{}'),
                    trangThai='active'
                )
                dia_diem.save()
                total_imported += 1
                print(f"   ✅ Tạo mới: {ten_dia_diem}")
    
    print("\n" + "="*80)
    print("KẾT QUẢ")
    print("="*80)
    print(f"✅ Đã tạo mới: {total_imported} địa điểm")
    print(f"🔄 Đã cập nhật: {total_updated} địa điểm")
    print(f"⏭️  Đã bỏ qua: {total_skipped} địa điểm")
    print(f"📊 Tổng cộng: {total_imported + total_updated} địa điểm")
    print("="*80)

if __name__ == '__main__':
    import_fallback_activities()

