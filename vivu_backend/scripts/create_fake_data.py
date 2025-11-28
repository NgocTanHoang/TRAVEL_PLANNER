#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script tạo dữ liệu giả (fake data) cho các bảng để test project
Trừ bảng DIADIEM (đã có dữ liệu thực)
"""
import os
import sys
import django
import random
from datetime import datetime, timedelta
from pathlib import Path
from decimal import Decimal

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

from django.contrib.auth.hashers import make_password
from django.utils import timezone
from django.db import models
from apps.places.models import DiaDiem, TinhThanh, HinhAnhDiaDiem, DanhGia, DiaDiemYeuThich
from apps.users.models import NguoiDung, LichSuTimKiem
from apps.itineraries.models import LichTrinh, LichTrinhDiaDiem, DongGop

# Vietnamese names and data
VIETNAMESE_FIRST_NAMES = [
    'An', 'Anh', 'Bình', 'Dương', 'Hà', 'Hải', 'Hoa', 'Hùng', 'Lan', 'Linh',
    'Mai', 'Nam', 'Ngọc', 'Phương', 'Quang', 'Thảo', 'Thanh', 'Thành', 'Thu', 'Trang',
    'Tùng', 'Tú', 'Văn', 'Việt', 'Vũ', 'Xuân', 'Yến', 'Đức', 'Đăng', 'Huy'
]

VIETNAMESE_LAST_NAMES = [
    'Nguyễn', 'Trần', 'Lê', 'Phạm', 'Hoàng', 'Huỳnh', 'Phan', 'Vũ', 'Võ', 'Đặng',
    'Bùi', 'Đỗ', 'Hồ', 'Ngô', 'Dương', 'Lý', 'Đào', 'Đinh', 'Tôn', 'Trương'
]

REVIEW_TITLES = [
    'Địa điểm tuyệt vời!', 'Rất đáng để tham quan', 'Cảnh đẹp nhưng...',
    'Đáng giá với số tiền bỏ ra', 'Trải nghiệm tuyệt vời', 'Không như mong đợi',
    'Hoàn hảo cho chuyến đi', 'Rất thú vị', 'Địa điểm đẹp', 'Nên đến một lần'
]

REVIEW_CONTENTS = [
    'Địa điểm này thực sự rất đẹp và đáng để tham quan. Cảnh quan tuyệt vời và không gian rộng rãi.',
    'Giá vé hợp lý, dịch vụ tốt. Cảnh đẹp và nhiều góc chụp ảnh đẹp. Sẽ quay lại lần sau.',
    'Không gian rộng rãi, sạch sẽ. Nhân viên nhiệt tình. Đáng giá với số tiền bỏ ra.',
    'Địa điểm này có cảnh đẹp nhưng dịch vụ còn cần cải thiện. Vẫn đáng để đến một lần.',
    'Rất thú vị và hấp dẫn. Có nhiều hoạt động để tham gia. Phù hợp cho gia đình.',
    'Cảnh đẹp nhưng đông người vào cuối tuần. Nên đi vào ngày thường để tránh đông.',
    'Địa điểm này có giá trị lịch sử và văn hóa cao. Rất đáng để tìm hiểu thêm.',
    'Không gian đẹp, phù hợp cho các hoạt động ngoài trời. Có nhiều góc chụp ảnh đẹp.',
    'Dịch vụ tốt, giá cả hợp lý. Địa điểm sạch sẽ và được bảo trì tốt.',
    'Đáng để tham quan một lần. Cảnh đẹp và có nhiều điều thú vị để khám phá.'
]

ITINERARY_TITLES = [
    'Hành trình khám phá {city}',
    'Chuyến du lịch {city} {days} ngày',
    'Trải nghiệm {city} đầy đủ',
    'Tour {city} giá rẻ',
    '{city} - Điểm đến mơ ước',
    'Khám phá {city} cùng gia đình',
    '{city} trong tầm tay',
    'Chuyến đi {city} thú vị'
]

ITINERARY_DESCRIPTIONS = [
    'Lịch trình chi tiết cho chuyến đi {days} ngày đến {city}. Bao gồm các địa điểm nổi tiếng và hoạt động thú vị.',
    'Hành trình khám phá {city} với ngân sách hợp lý. Trải nghiệm văn hóa, ẩm thực và cảnh đẹp địa phương.',
    'Chuyến đi {days} ngày đến {city} với lịch trình được tối ưu hóa. Tham quan các điểm đến nổi tiếng và ẩm thực địa phương.',
    'Khám phá {city} với lịch trình linh hoạt. Phù hợp cho cả gia đình và nhóm bạn.',
    'Trải nghiệm đầy đủ về {city} trong {days} ngày. Từ văn hóa đến ẩm thực, từ lịch sử đến hiện đại.'
]


def create_fake_users(count=50):
    """Tạo người dùng giả"""
    print(f"\n[INFO] Tạo {count} người dùng giả...")
    
    created = 0
    for i in range(count):
        try:
            first_name = random.choice(VIETNAMESE_FIRST_NAMES)
            last_name = random.choice(VIETNAMESE_LAST_NAMES)
            ho_ten = f"{last_name} {first_name}"
            username = f"user_{i+1}_{first_name.lower()}"
            email = f"{username}@example.com"
            
            # Kiểm tra đã tồn tại chưa
            if NguoiDung.objects.filter(username=username).exists():
                continue
            
            user = NguoiDung.objects.create(
                username=username,
                email=email,
                hoTen=ho_ten,
                password=make_password('password123'),  # Default password
                soDienThoai=f"0{random.randint(900000000, 999999999)}",
                gioiTinh=random.choice(['Nam', 'Nữ', 'Khác']),
                ngaySinh=datetime.now() - timedelta(days=random.randint(18*365, 65*365)),
                diaChi=f"{random.randint(1, 200)} Đường {random.choice(['Nguyễn Huệ', 'Lê Lợi', 'Trần Hưng Đạo', 'Hoàng Diệu'])}",
                vaiTro=random.choice(['user', 'user', 'user', 'contributor']),  # Mostly users
                trangThai='active',
                is_active=True,
                is_staff=False,
                is_superuser=False
            )
            created += 1
            
            if (i + 1) % 10 == 0:
                print(f"  Đã tạo {i+1}/{count} người dùng...")
        
        except Exception as e:
            print(f"  [ERROR] Không thể tạo user {i+1}: {e}")
    
    print(f"[OK] Đã tạo {created} người dùng")
    return created


def create_fake_reviews(count_per_place=5):
    """Tạo đánh giá giả"""
    print(f"\n[INFO] Tạo đánh giá giả ({count_per_place} đánh giá mỗi địa điểm)...")
    
    places = DiaDiem.objects.all()[:50]  # Chỉ tạo cho 50 địa điểm đầu
    users = list(NguoiDung.objects.all())
    
    if not users:
        print("[WARN] Chưa có người dùng. Hãy chạy create_fake_users() trước.")
        return 0
    
    created = 0
    for place in places:
        # Lấy ngẫu nhiên users để review
        reviewers = random.sample(users, min(count_per_place, len(users)))
        
        for user in reviewers:
            try:
                # Kiểm tra đã review chưa
                if DanhGia.objects.filter(maDiaDiem=place, maNguoiDung=user).exists():
                    continue
                
                rating = random.randint(3, 5)  # Đa số rating tốt
                title = random.choice(REVIEW_TITLES)
                content = random.choice(REVIEW_CONTENTS)
                
                review = DanhGia.objects.create(
                    maDiaDiem=place,
                    maNguoiDung=user,
                    diemDanhGia=rating,
                    tieuDe=title,
                    noiDung=content,
                    soLuotThich=random.randint(0, 50),
                    trangThai='active'
                )
                created += 1
            
            except Exception as e:
                print(f"  [ERROR] Không thể tạo review: {e}")
        
        # Cập nhật rating trung bình cho địa điểm
        place_reviews = DanhGia.objects.filter(maDiaDiem=place, trangThai='active')
        if place_reviews.exists():
            avg_rating = place_reviews.aggregate(models.Avg('diemDanhGia'))['diemDanhGia__avg']
            place.danhGiaTrungBinh = round(avg_rating, 1)
            place.soLuotDanhGia = place_reviews.count()
            place.save()
    
    print(f"[OK] Đã tạo {created} đánh giá")
    return created


def create_fake_favorites(count_per_user=5):
    """Tạo địa điểm yêu thích giả"""
    print(f"\n[INFO] Tạo địa điểm yêu thích giả ({count_per_user} mỗi người dùng)...")
    
    users = list(NguoiDung.objects.all())
    places = list(DiaDiem.objects.all())
    
    if not users or not places:
        print("[WARN] Chưa có đủ dữ liệu.")
        return 0
    
    created = 0
    for user in users:
        # Chọn ngẫu nhiên places để yêu thích
        favorite_places = random.sample(places, min(count_per_user, len(places)))
        
        for place in favorite_places:
            try:
                # Kiểm tra đã yêu thích chưa
                if DiaDiemYeuThich.objects.filter(maNguoiDung=user, maDiaDiem=place).exists():
                    continue
                
                DiaDiemYeuThich.objects.create(
                    maNguoiDung=user,
                    maDiaDiem=place,
                    ghiChu=f"Địa điểm yêu thích tại {place.maTinhThanh.tenTinhThanh}"
                )
                created += 1
            
            except Exception as e:
                print(f"  [ERROR] Không thể tạo favorite: {e}")
    
    print(f"[OK] Đã tạo {created} địa điểm yêu thích")
    return created


def create_fake_itineraries(count=30):
    """Tạo lịch trình giả"""
    print(f"\n[INFO] Tạo {count} lịch trình giả...")
    
    users = list(NguoiDung.objects.all())
    places = list(DiaDiem.objects.all())
    
    if not users or not places:
        print("[WARN] Chưa có đủ dữ liệu.")
        return 0
    
    provinces = list(TinhThanh.objects.all())
    
    created = 0
    for i in range(count):
        try:
            user = random.choice(users)
            province = random.choice(provinces)
            days = random.randint(2, 7)
            
            # Chọn ngày bắt đầu ngẫu nhiên trong 30 ngày tới
            start_date = timezone.now().date() + timedelta(days=random.randint(1, 30))
            end_date = start_date + timedelta(days=days - 1)
            
            city_name = province.tenTinhThanh
            title = random.choice(ITINERARY_TITLES).format(city=city_name, days=days)
            description = random.choice(ITINERARY_DESCRIPTIONS).format(city=city_name, days=days)
            
            itinerary = LichTrinh.objects.create(
                maNguoiDung=user,
                tieuDe=title,
                moTa=description,
                ngayBatDau=start_date,
                ngayKetThuc=end_date,
                soNgay=days,
                soNguoi=random.randint(1, 4),
                nganSach=random.randint(5000000, 50000000),
                chiPhiUocTinh=random.randint(4000000, 45000000),
                trangThai=random.choice(['draft', 'published', 'published']),
                laCongKhai=random.choice([True, False]),
                soLuotXem=random.randint(0, 500),
                soLuotThich=random.randint(0, 50)
            )
            
            # Thêm địa điểm vào lịch trình
            province_places = [p for p in places if p.maTinhThanh == province]
            if not province_places:
                province_places = random.sample(places, min(5, len(places)))
            
            selected_places = random.sample(province_places, min(days * 2, len(province_places)))
            
            for day_offset, place in enumerate(selected_places[:days * 2]):
                visit_date = start_date + timedelta(days=day_offset // 2)
                time_slot = random.choice(['08:00-12:00', '13:00-17:00', '18:00-21:00'])
                
                LichTrinhDiaDiem.objects.create(
                    maLichTrinh=itinerary,
                    maDiaDiem=place,
                    ngayThamQuan=visit_date,
                    thoiGianThamQuan=time_slot,
                    thuTu=day_offset + 1,
                    chiPhiUocTinh=random.randint(50000, 500000)
                )
            
            created += 1
            
            if (i + 1) % 10 == 0:
                print(f"  Đã tạo {i+1}/{count} lịch trình...")
        
        except Exception as e:
            print(f"  [ERROR] Không thể tạo itinerary {i+1}: {e}")
    
    print(f"[OK] Đã tạo {created} lịch trình")
    return created


def create_fake_search_history(count_per_user=10):
    """Tạo lịch sử tìm kiếm giả"""
    print(f"\n[INFO] Tạo lịch sử tìm kiếm giả ({count_per_user} mỗi người dùng)...")
    
    users = list(NguoiDung.objects.all())
    places = list(DiaDiem.objects.all())
    
    if not users or not places:
        print("[WARN] Chưa có đủ dữ liệu.")
        return 0
    
    search_keywords = [
        'địa điểm du lịch', 'khách sạn', 'nhà hàng', 'bãi biển', 'núi',
        'thác nước', 'chùa', 'bảo tàng', 'vườn quốc gia', 'di tích lịch sử',
        'phố cổ', 'làng cổ', 'công viên', 'động', 'hang'
    ]
    
    created = 0
    for user in users:
        for _ in range(count_per_user):
            try:
                keyword = random.choice(search_keywords)
                # 70% tìm kiếm có kết quả (gắn với địa điểm)
                if random.random() < 0.7:
                    place = random.choice(places)
                    num_results = random.randint(1, 20)
                else:
                    place = None
                    num_results = 0
                
                # Ngày tìm kiếm trong 30 ngày qua
                search_date = timezone.now() - timedelta(days=random.randint(0, 30))
                
                LichSuTimKiem.objects.create(
                    maNguoiDung=user,
                    tuKhoa=keyword,
                    maDiaDiem=place,
                    soKetQua=num_results,
                    ngayTim=search_date
                )
                created += 1
            
            except Exception as e:
                print(f"  [ERROR] Không thể tạo search history: {e}")
    
    print(f"[OK] Đã tạo {created} lịch sử tìm kiếm")
    return created


def create_fake_contributions(count=20):
    """Tạo đóng góp/báo cáo giả"""
    print(f"\n[INFO] Tạo {count} đóng góp/báo cáo giả...")
    
    users = list(NguoiDung.objects.all())
    places = list(DiaDiem.objects.all())
    
    if not users or not places:
        print("[WARN] Chưa có đủ dữ liệu.")
        return 0
    
    contribution_types = [
        ('them_dia_diem', 'Thêm địa điểm mới: {place}'),
        ('sua_thong_tin', 'Sửa thông tin địa điểm: {place}'),
        ('bao_cao_loi', 'Báo cáo lỗi thông tin: {place}'),
        ('khac', 'Đề xuất cải thiện: {place}')
    ]
    
    created = 0
    for i in range(count):
        try:
            user = random.choice(users)
            place = random.choice(places) if random.random() < 0.8 else None
            loai, template = random.choice(contribution_types)
            
            content = template.format(place=place.tenDiaDiem if place else 'Địa điểm mới')
            content += f"\n\n{random.choice(REVIEW_CONTENTS)}"
            
            contribution = DongGop.objects.create(
                maNguoiDung=user,
                maDiaDiem=place,
                loaiDongGop=loai,
                noiDung=content,
                trangThai=random.choice(['pending', 'pending', 'approved', 'rejected']),
                phanHoi=random.choice(['', '', 'Cảm ơn bạn đã đóng góp!', 'Đã xử lý.']) if random.random() < 0.3 else '',
                ngayXuLy=timezone.now() - timedelta(days=random.randint(0, 7)) if random.random() < 0.5 else None
            )
            created += 1
        
        except Exception as e:
            print(f"  [ERROR] Không thể tạo contribution {i+1}: {e}")
    
    print(f"[OK] Đã tạo {created} đóng góp")
    return created


def create_fake_provinces():
    """Đảm bảo có đủ tỉnh thành"""
    print("\n[INFO] Kiểm tra và tạo tỉnh thành nếu thiếu...")
    
    provinces = [
        'Hà Nội', 'TP. Hồ Chí Minh', 'Đà Nẵng', 'Hải Phòng', 'Cần Thơ',
        'An Giang', 'Bà Rịa - Vũng Tàu', 'Bạc Liêu', 'Bắc Giang', 'Bắc Kạn',
        'Bắc Ninh', 'Bến Tre', 'Bình Định', 'Bình Dương', 'Bình Phước',
        'Bình Thuận', 'Cà Mau', 'Cao Bằng', 'Đắk Lắk', 'Đắk Nông',
        'Điện Biên', 'Đồng Nai', 'Đồng Tháp', 'Gia Lai', 'Hà Giang',
        'Hà Nam', 'Hà Tĩnh', 'Hải Dương', 'Hậu Giang', 'Hòa Bình',
        'Hưng Yên', 'Khánh Hòa', 'Kiên Giang', 'Kon Tum', 'Lai Châu',
        'Lâm Đồng', 'Lạng Sơn', 'Lào Cai', 'Long An', 'Nam Định',
        'Nghệ An', 'Ninh Bình', 'Ninh Thuận', 'Phú Thọ', 'Phú Yên',
        'Quảng Bình', 'Quảng Nam', 'Quảng Ngãi', 'Quảng Ninh', 'Quảng Trị',
        'Sóc Trăng', 'Sơn La', 'Tây Ninh', 'Thái Bình', 'Thái Nguyên',
        'Thanh Hóa', 'Thừa Thiên Huế', 'Tiền Giang', 'Trà Vinh', 'Tuyên Quang',
        'Vĩnh Long', 'Vĩnh Phúc', 'Yên Bái'
    ]
    
    created = 0
    for province_name in provinces:
        if not TinhThanh.objects.filter(tenTinhThanh=province_name).exists():
            try:
                TinhThanh.objects.create(
                    tenTinhThanh=province_name,
                    moTa=f"Tỉnh thành {province_name}"
                )
                created += 1
            except Exception as e:
                print(f"  [ERROR] Không thể tạo tỉnh {province_name}: {e}")
    
    print(f"[OK] Đã kiểm tra và tạo {created} tỉnh thành mới")
    return created


def main():
    """Tạo tất cả dữ liệu giả"""
    print("="*80)
    print("TẠO DỮ LIỆU GIẢ CHO TEST PROJECT")
    print("="*80)
    
    # Đảm bảo có tỉnh thành
    create_fake_provinces()
    
    # Tạo users
    user_count = create_fake_users(50)
    
    # Tạo reviews
    review_count = create_fake_reviews(5)
    
    # Tạo favorites
    favorite_count = create_fake_favorites(5)
    
    # Tạo itineraries
    itinerary_count = create_fake_itineraries(30)
    
    # Tạo search history
    search_count = create_fake_search_history(10)
    
    # Tạo contributions
    contribution_count = create_fake_contributions(20)
    
    # Tổng kết
    print("\n" + "="*80)
    print("HOÀN TẤT!")
    print("="*80)
    print(f"  ✓ Đã tạo {user_count} người dùng")
    print(f"  ✓ Đã tạo {review_count} đánh giá")
    print(f"  ✓ Đã tạo {favorite_count} địa điểm yêu thích")
    print(f"  ✓ Đã tạo {itinerary_count} lịch trình")
    print(f"  ✓ Đã tạo {search_count} lịch sử tìm kiếm")
    print(f"  ✓ Đã tạo {contribution_count} đóng góp")
    print("="*80)
    
    # Thống kê
    print("\n📊 THỐNG KÊ DATABASE:")
    print("-"*80)
    print(f"  TINHTHANH:           {TinhThanh.objects.count():6} records")
    print(f"  DIADIEM:             {DiaDiem.objects.count():6} records")
    print(f"  NGUOIDUNG:           {NguoiDung.objects.count():6} records")
    print(f"  DANHGIA:             {DanhGia.objects.count():6} records")
    print(f"  DIADIEM_YEUTHICH:    {DiaDiemYeuThich.objects.count():6} records")
    print(f"  LICHTRINH:           {LichTrinh.objects.count():6} records")
    print(f"  LICHTRINH_DIADIEM:   {LichTrinhDiaDiem.objects.count():6} records")
    print(f"  LICHSU_TIMKIEM:      {LichSuTimKiem.objects.count():6} records")
    print(f"  DONGGOP:             {DongGop.objects.count():6} records")
    print("="*80)


if __name__ == '__main__':
    main()

