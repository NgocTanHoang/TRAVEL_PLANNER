"""
Script để cập nhật thông tin cho 5 địa điểm ở Đà Nẵng đã có
"""
import os
import sys
import django
from pathlib import Path

# Setup Django
backend_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(backend_dir))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vivu_core.settings')
os.chdir(backend_dir)
django.setup()

from apps.places.models import TinhThanh, DiaDiem, HinhAnhDiaDiem

# Dữ liệu cập nhật từ JSON
places_update = [
    {
        "tenDiaDiem": "Cầu Vàng (Golden Bridge) - Sun World Bà Nà Hills",
        "moTa": "Cây cầu đi bộ độc đáo, nằm ở độ cao 1.400m so với mực nước biển, được nâng đỡ bởi đôi bàn tay đá khổng lồ. Là kiệt tác kiến trúc tạo nên danh tiếng toàn cầu cho du lịch Đà Nẵng. Cầu nằm trong khu phức hợp Bà Nà Hills, nổi bật với thiết kế như dải lụa vàng mềm mại.",
        "diaChi": "Khu du lịch Sun World Bà Nà Hills, Xã Hòa Ninh, Huyện Hòa Vang, Đà Nẵng",
        "loaiDiaDiem": "giai_tri",
        "viDo": 15.996111,
        "kinhDo": 108.033611,
        "giaVe": None,
        "gioMoCua": "07:30",
        "gioDongCua": "17:30",
        "dienThoai": "090 537 66 37",
        "website": "https://banahills.sunworld.vn/",
        "danhGiaTrungBinh": 4.6,
        "dacDiem": "Kiến trúc bàn tay khổng lồ, công trình kỷ lục, nằm trong khu du lịch",
        "tienNghi": "Cáp treo, nhà hàng, khu vui chơi Fantasy Park",
        "hinhAnh": {
            "urlHinhAnh": "/media/places/DaNang/caudao-banahills.jpg",
            "moTa": "Hình ảnh Cầu Vàng với bàn tay khổng lồ",
            "laChinh": True
        }
    },
    {
        "tenDiaDiem": "Ngũ Hành Sơn (Non Nước)",
        "moTa": "Quần thể danh thắng quốc gia đặc biệt gồm 5 ngọn núi đá vôi (Kim, Mộc, Thủy, Hỏa, Thổ) nằm ven biển. Nổi tiếng với hệ thống hang động tự nhiên huyền bí và các công trình tâm linh cổ kính, đặc biệt là núi Thủy Sơn.",
        "diaChi": "Phường Hòa Hải, Quận Ngũ Hành Sơn, Đà Nẵng",
        "loaiDiaDiem": "dia_danh",
        "viDo": 16.002800,
        "kinhDo": 108.270800,
        "giaVe": None,
        "gioMoCua": "07:00",
        "gioDongCua": "17:30",
        "dienThoai": "0236 3968 737",
        "website": None,
        "danhGiaTrungBinh": 4.5,
        "dacDiem": "Danh thắng quốc gia, hang động tự nhiên, làng nghề điêu khắc đá",
        "tienNghi": "Thang máy, hướng dẫn viên, khu vực bán đá mỹ nghệ",
        "hinhAnh": {
            "urlHinhAnh": "/media/places/DaNang/nguhanhson-toan.jpg",
            "moTa": "Hình ảnh toàn cảnh Ngũ Hành Sơn",
            "laChinh": True
        }
    },
    {
        "tenDiaDiem": "Bán đảo Sơn Trà (Chùa Linh Ứng Bãi Bụt)",
        "moTa": "Khu dự trữ sinh quyển rộng lớn, được mệnh danh là 'lá phổi xanh' của Đà Nẵng. Nơi đây có hệ sinh thái rừng phong phú và Chùa Linh Ứng nổi tiếng với bức tượng Phật Quan Thế Âm cao 67m hướng ra biển Đông.",
        "diaChi": "Bán đảo Sơn Trà, Phường Thọ Quang, Quận Sơn Trà, Đà Nẵng",
        "loaiDiaDiem": "dia_danh",
        "viDo": 16.108300,
        "kinhDo": 108.281800,
        "giaVe": None,
        "gioMoCua": "06:00",
        "gioDongCua": "21:00",
        "dienThoai": None,
        "website": None,
        "danhGiaTrungBinh": 4.6,
        "dacDiem": "Rừng nguyên sinh, tượng Phật Quan Âm khổng lồ, Đỉnh Bàn Cờ",
        "tienNghi": "Đường đi bộ/xe máy ngắm cảnh, điểm dừng chân, nhà hàng hải sản",
        "hinhAnh": {
            "urlHinhAnh": "/media/places/DaNang/chualinhung-sontra.jpg",
            "moTa": "Hình ảnh Tượng Phật Quan Âm tại Chùa Linh Ứng",
            "laChinh": True
        }
    },
    {
        "tenDiaDiem": "Bãi biển Mỹ Khê",
        "moTa": "Một trong những bãi biển quyến rũ nhất hành tinh (theo Forbes), nổi tiếng với bờ cát trắng mịn, nước biển sạch và ấm áp, độ dốc thoải, an toàn cho du khách. Khu vực tập trung nhiều resort và hoạt động thể thao dưới nước.",
        "diaChi": "Đường Võ Nguyên Giáp, Phường Phước Mỹ, Quận Sơn Trà, Đà Nẵng",
        "loaiDiaDiem": "giai_tri",
        "viDo": 16.059400,
        "kinhDo": 108.243500,
        "giaVe": None,
        "gioMoCua": "00:00",
        "gioDongCua": "23:59",
        "dienThoai": None,
        "website": None,
        "danhGiaTrungBinh": 4.5,
        "dacDiem": "Cát trắng, nước ấm, bãi tắm an toàn, có dịch vụ cứu hộ",
        "tienNghi": "Dịch vụ thuê dù/ghế, khu vực tắm tráng, nhà hàng hải sản",
        "hinhAnh": {
            "urlHinhAnh": "/media/places/DaNang/bienmykhe-danang.jpg",
            "moTa": "Hình ảnh bãi biển Mỹ Khê",
            "laChinh": True
        }
    },
    {
        "tenDiaDiem": "Cầu Rồng",
        "moTa": "Cây cầu độc đáo bắc qua sông Hàn, được thiết kế mô phỏng hình dáng con Rồng thời Lý vươn ra biển Đông. Là biểu tượng giao thông và du lịch hiện đại. Nổi tiếng với màn trình diễn phun lửa và phun nước ấn tượng vào cuối tuần.",
        "diaChi": "Đường Nguyễn Văn Linh, Phường Phước Ninh, Quận Hải Châu, Đà Nẵng",
        "loaiDiaDiem": "giai_tri",
        "viDo": 16.061000,
        "kinhDo": 108.225500,
        "giaVe": None,
        "gioMoCua": "00:00",
        "gioDongCua": "23:59",
        "dienThoai": None,
        "website": None,
        "danhGiaTrungBinh": 4.6,
        "dacDiem": "Phun lửa và phun nước lúc 21:00 Thứ Bảy, Chủ Nhật; Thiết kế chiếu sáng ấn tượng",
        "tienNghi": "Khu vực khán đài nhân tạo dọc bờ sông, dịch vụ thuê thuyền ngắm cảnh",
        "hinhAnh": {
            "urlHinhAnh": "/media/places/DaNang/caurong-danang.jpg",
            "moTa": "Hình ảnh Cầu Rồng phun lửa và phun nước",
            "laChinh": True
        }
    }
]

def update_places():
    print("=" * 70)
    print("CẬP NHẬT THÔNG TIN 5 ĐỊA ĐIỂM Ở ĐÀ NẴNG")
    print("=" * 70)
    
    updated_count = 0
    image_added_count = 0
    
    for idx, place_data in enumerate(places_update, start=1):
        ten_dia_diem = place_data['tenDiaDiem']
        print(f"\n[{idx}/5] Cập nhật: {ten_dia_diem}")
        
        try:
            # Tìm địa điểm
            dia_diem = DiaDiem.objects.get(tenDiaDiem=ten_dia_diem)
            
            # Cập nhật thông tin
            dia_diem.moTa = place_data.get('moTa', dia_diem.moTa)
            dia_diem.diaChi = place_data.get('diaChi', dia_diem.diaChi)
            dia_diem.loaiDiaDiem = place_data.get('loaiDiaDiem', dia_diem.loaiDiaDiem)
            dia_diem.viDo = place_data.get('viDo', dia_diem.viDo)
            dia_diem.kinhDo = place_data.get('kinhDo', dia_diem.kinhDo)
            dia_diem.gioMoCua = place_data.get('gioMoCua', dia_diem.gioMoCua) or ''
            dia_diem.gioDongCua = place_data.get('gioDongCua', dia_diem.gioDongCua) or ''
            dia_diem.dienThoai = place_data.get('dienThoai') or ''
            dia_diem.website = place_data.get('website') or ''
            dia_diem.danhGiaTrungBinh = place_data.get('danhGiaTrungBinh', dia_diem.danhGiaTrungBinh)
            dia_diem.dacDiem = place_data.get('dacDiem', dia_diem.dacDiem)
            dia_diem.tienNghi = place_data.get('tienNghi', dia_diem.tienNghi)
            
            dia_diem.save()
            print(f"   ✓ Đã cập nhật địa điểm (maDiaDiem: {dia_diem.maDiaDiem})")
            
            # Thêm hình ảnh nếu chưa có
            if 'hinhAnh' in place_data:
                hinh_anh_data = place_data['hinhAnh']
                # Kiểm tra xem đã có hình ảnh này chưa
                existing_image = HinhAnhDiaDiem.objects.filter(
                    maDiaDiem=dia_diem,
                    urlHinhAnh=hinh_anh_data['urlHinhAnh']
                ).first()
                
                if not existing_image:
                    try:
                        HinhAnhDiaDiem.objects.create(
                            maDiaDiem=dia_diem,
                            urlHinhAnh=hinh_anh_data['urlHinhAnh'],
                            moTa=hinh_anh_data.get('moTa', ''),
                            laChinh=hinh_anh_data.get('laChinh', False)
                        )
                        print(f"   ✓ Đã thêm hình ảnh")
                        image_added_count += 1
                    except Exception as img_error:
                        print(f"   ⚠ Không thể thêm hình ảnh: {str(img_error)[:100]}")
                else:
                    print(f"   ✓ Hình ảnh đã tồn tại")
            
            updated_count += 1
            
        except DiaDiem.DoesNotExist:
            print(f"   ✗ Không tìm thấy địa điểm")
        except Exception as e:
            print(f"   ✗ Lỗi: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("KẾT QUẢ")
    print("=" * 70)
    print(f"✓ Đã cập nhật: {updated_count} địa điểm")
    print(f"✓ Đã thêm: {image_added_count} hình ảnh")
    print("\n✅ Hoàn tất!")

if __name__ == '__main__':
    update_places()

