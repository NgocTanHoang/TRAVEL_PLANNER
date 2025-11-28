"""
Django management command to add The Signature Hotel Nha Trang to database
"""
import os
import sys
import django
import requests
from pathlib import Path
from django.core.management.base import BaseCommand
from django.conf import settings
from apps.places.models import DiaDiem, TinhThanh, HinhAnhDiaDiem
import json


class Command(BaseCommand):
    help = 'Add The Signature Hotel Nha Trang to database'

    def handle(self, *args, **options):
        # Thông tin khách sạn
        hotel_data = {
            'tenDiaDiem': 'The Signature Hotel Nha Trang',
            'loaiDiaDiem': 'khach_san',
            'diaChi': '86A1 Trần Phú, Nha Trang, Khánh Hoà',
            'soPhong': 266,
            'dienThoai': '0258 3886 886',
            'email': 'dosm@hotelsignature.vn',
            'website': 'https://hotelsignature.vn',
            'moTa': '''Khách sạn The Signature Nha Trang (The Signature Hotel Nha Trang) được khai trương vào ngày 01.07.2024 với quy mô 27 tầng, 266 phòng được thiết kế theo phong cách xanh hài hòa kết hợp giữa truyền thống và hiện đại. Tất cả các phòng đều có ban công và vườn treo riêng với đầy đủ tiện nghi, tiện nghi đạt tiêu chuẩn quốc tế.

Bằng cách kết hợp cây xanh, các vật liệu tự nhiên như mây tre đan và ánh nắng tràn ngập khắp nơi, khách sạn đã tạo ra những căn phòng mộc mạc nhưng sang trọng, tỏa ra sự ấm áp và tiện nghi.

Khách sạn có nhiều không gian sảnh rộng dành cho các sự kiện quan trọng như đám cưới, sinh nhật, ngày kỷ niệm, hội nghị, họp mặt và thảo luận. Khách sạn được hỗ trợ bởi đội ngũ nhân viên kỹ thuật chuyên nghiệp, trang thiết bị hiện đại, màn hình LED rộng rãi, sắc nét. Ngoài ra, khách sạn còn cung cấp các dịch vụ đa dạng bao gồm các lớp học thiền Yoga, nhà hàng thuần Việt, vườn Babylon với tầm nhìn toàn cảnh thành phố, ba bể bơi đa năng lớn và khu vực Spa Jjim Ji Bang theo phong cách Hàn Quốc tiêu chuẩn.''',
            'tienNghi': 'Nhà hàng, Bar, Spa, Fitness Center, Bể bơi, Karaoke, Massage, Xông hơi, Sân vườn, Wifi, Truyền hình cáp, Giặt ủi, Quầy lưu niệm, Phòng hội thảo hội nghị, Dịch vụ văn phòng, Chỗ đỗ xe, Xe đưa đón sân bay, Đặt dịch vụ lữ hành và vận chuyển, Tiện nghi cho người khuyết tật',
            'image_url': 'https://csdl.vietnamtourism.gov.vn/uploads/logo/01_3/2025/CSLT2025/5sao/KhanhHoa/SignatureNhaTrang/Signature-.jpg',
            'maTinhThanh': 28  # Khánh Hòa
        }
        
        try:
            # Tìm TinhThanh
            tinh_thanh = TinhThanh.objects.get(maTinhThanh=hotel_data['maTinhThanh'])
            self.stdout.write(f"Found TinhThanh: {tinh_thanh.tenTinhThanh}")
            
            # Kiểm tra xem địa điểm đã tồn tại chưa
            existing = DiaDiem.objects.filter(
                tenDiaDiem__icontains='Signature',
                maTinhThanh=tinh_thanh
            ).first()
            
            if existing:
                self.stdout.write(self.style.WARNING(f"Địa điểm đã tồn tại: {existing.tenDiaDiem} (ID: {existing.maDiaDiem})"))
                # Cập nhật thông tin
                existing.tienNghi = hotel_data['tienNghi']
                existing.moTa = hotel_data['moTa']
                existing.diaChi = hotel_data['diaChi']
                existing.dienThoai = hotel_data['dienThoai']
                existing.website = hotel_data['website']
                # Cập nhật dacDiem với email và số phòng
                dac_diem = {
                    'email': hotel_data['email'],
                    'so_phong': hotel_data['soPhong'],
                    'ngay_khai_truong': '2024-07-01',
                    'so_tang': 27
                }
                existing.dacDiem = json.dumps(dac_diem, ensure_ascii=False)
                existing.save()
                self.stdout.write(self.style.SUCCESS(f"Updated DiaDiem: {existing.tenDiaDiem} (ID: {existing.maDiaDiem})"))
                dia_diem = existing
            else:
                # Tạo DiaDiem
                # Lưu email và số phòng vào dacDiem (JSON)
                dac_diem = {
                    'email': hotel_data['email'],
                    'so_phong': hotel_data['soPhong'],
                    'ngay_khai_truong': '2024-07-01',
                    'so_tang': 27
                }
                
                dia_diem = DiaDiem.objects.create(
                    tenDiaDiem=hotel_data['tenDiaDiem'],
                    maTinhThanh=tinh_thanh,
                    loaiDiaDiem=hotel_data['loaiDiaDiem'],
                    diaChi=hotel_data['diaChi'],
                    moTa=hotel_data['moTa'],
                    dienThoai=hotel_data['dienThoai'],
                    website=hotel_data['website'],
                    giaVe=0.0,  # Khách sạn không có giá vé, giá phòng thay đổi
                    tienNghi=hotel_data['tienNghi'],
                    dacDiem=json.dumps(dac_diem, ensure_ascii=False),
                    viDo=12.2388,  # Tọa độ Nha Trang (ước tính)
                    kinhDo=109.1967,
                    trangThai='active',
                    danhGiaTrungBinh=4.5,  # Giả định
                    soLuotDanhGia=0
                )
                self.stdout.write(self.style.SUCCESS(f"Created DiaDiem: {dia_diem.tenDiaDiem} (ID: {dia_diem.maDiaDiem})"))
            
            # Tải ảnh
            image_url = hotel_data['image_url']
            media_root = Path(settings.MEDIA_ROOT)
            places_dir = media_root / 'places' / str(dia_diem.maDiaDiem)
            places_dir.mkdir(parents=True, exist_ok=True)
            
            # Tên file ảnh
            image_filename = 'Signature-.jpg'
            image_path = places_dir / image_filename
            
            # Kiểm tra xem ảnh đã tồn tại chưa
            if not image_path.exists():
                try:
                    self.stdout.write(f"Downloading image from {image_url}...")
                    response = requests.get(image_url, timeout=30)
                    response.raise_for_status()
                    
                    with open(image_path, 'wb') as f:
                        f.write(response.content)
                    
                    self.stdout.write(self.style.SUCCESS(f"Downloaded image to {image_path}"))
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"Error downloading image: {e}"))
                    return
            else:
                self.stdout.write(f"Image already exists: {image_path}")
            
            # Tạo đường dẫn relative cho database
            relative_path = f'places/{dia_diem.maDiaDiem}/{image_filename}'
            
            # Kiểm tra xem ảnh đã có trong database chưa
            existing_image = HinhAnhDiaDiem.objects.filter(
                maDiaDiem=dia_diem,
                urlHinhAnh=relative_path
            ).first()
            
            if existing_image:
                self.stdout.write(self.style.WARNING(f"Image already exists in database: {existing_image.urlHinhAnh}"))
            else:
                # Tạo HinhAnhDiaDiem
                hinh_anh = HinhAnhDiaDiem.objects.create(
                    maDiaDiem=dia_diem,
                    urlHinhAnh=relative_path,
                    moTa='The Signature Hotel Nha Trang - Ảnh chính',
                    laChinh=True
                )
                self.stdout.write(self.style.SUCCESS(f"Created HinhAnhDiaDiem: {hinh_anh.urlHinhAnh}"))
            
            # Tóm tắt
            self.stdout.write(self.style.SUCCESS("\n" + "="*60))
            self.stdout.write(self.style.SUCCESS("TÓM TẮT:"))
            self.stdout.write(self.style.SUCCESS(f"  - Tên: {dia_diem.tenDiaDiem}"))
            self.stdout.write(self.style.SUCCESS(f"  - ID: {dia_diem.maDiaDiem}"))
            self.stdout.write(self.style.SUCCESS(f"  - Tỉnh thành: {tinh_thanh.tenTinhThanh}"))
            self.stdout.write(self.style.SUCCESS(f"  - Địa chỉ: {dia_diem.diaChi}"))
            self.stdout.write(self.style.SUCCESS(f"  - Số phòng: {hotel_data['soPhong']}"))
            self.stdout.write(self.style.SUCCESS(f"  - Ảnh: {relative_path}"))
            self.stdout.write(self.style.SUCCESS("="*60))
            
        except TinhThanh.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"TinhThanh với maTinhThanh={hotel_data['maTinhThanh']} không tồn tại"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {e}"))
            import traceback
            traceback.print_exc()

