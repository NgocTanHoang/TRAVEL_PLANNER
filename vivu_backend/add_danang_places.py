"""
Script để thêm 5 địa điểm ở Đà Nẵng vào database
"""
import os
import sys
import django
from pathlib import Path

# Setup Django
backend_dir = Path(__file__).resolve().parent
project_root = backend_dir.parent
sys.path.insert(0, str(backend_dir))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vivu_core.settings')
os.chdir(backend_dir)
django.setup()

from apps.places.models import TinhThanh, DiaDiem, HinhAnhDiaDiem
import sqlite3

# Dữ liệu 5 địa điểm ở Đà Nẵng
places_data = [
    {
        "tenDiaDiem": "Cầu Vàng (Golden Bridge) - Sun World Bà Nà Hills",
        "moTa": "Cây cầu đi bộ độc đáo, nằm ở độ cao 1.400m so với mực nước biển, được nâng đỡ bởi đôi bàn tay đá khổng lồ. Là kiệt tác kiến trúc tạo nên danh tiếng toàn cầu cho du lịch Đà Nẵng. Cầu nằm trong khu phức hợp Bà Nà Hills, nổi bật với thiết kế như dải lụa vàng mềm mại.",
        "diaChi": "Khu du lịch Sun World Bà Nà Hills, Xã Hòa Ninh, Huyện Hòa Vang, Đà Nẵng",
        "loaiDiaDiem": "giai_tri",
        "viDo": 15.996111,
        "kinhDo": 108.033611,
        "giaVe": None,  # Sẽ parse từ chuỗi
        "gioMoCua": "07:30",
        "gioDongCua": "17:30",
        "dienThoai": "090 537 66 37",
        "website": "https://banahills.sunworld.vn/",
        "danhGiaTrungBinh": 4.6,
        "trangThai": "active",
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
        "trangThai": "active",
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
        "trangThai": "active",
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
        "trangThai": "active",
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
        "trangThai": "active",
        "dacDiem": "Phun lửa và phun nước lúc 21:00 Thứ Bảy, Chủ Nhật; Thiết kế chiếu sáng ấn tượng",
        "tienNghi": "Khu vực khán đài nhân tạo dọc bờ sông, dịch vụ thuê thuyền ngắm cảnh",
        "hinhAnh": {
            "urlHinhAnh": "/media/places/DaNang/caurong-danang.jpg",
            "moTa": "Hình ảnh Cầu Rồng phun lửa và phun nước",
            "laChinh": True
        }
    }
]

def parse_gia_ve(gia_ve_str):
    """Parse giá vé từ string sang số"""
    if not gia_ve_str or gia_ve_str.lower() == "miễn phí":
        return None
    
    # Extract số từ chuỗi
    import re
    numbers = re.findall(r'\d+', gia_ve_str.replace(',', '').replace('.', ''))
    if numbers:
        # Lấy số đầu tiên (giá trị lớn nhất)
        return float(numbers[0])
    return None

def get_ma_tinh_thanh():
    """Tìm maTinhThanh cho Đà Nẵng"""
    try:
        tinh_thanh = TinhThanh.objects.get(tenTinhThanh__icontains="Đà Nẵng")
        return tinh_thanh.maTinhThanh
    except TinhThanh.DoesNotExist:
        # Thử tìm với tên khác
        try:
            tinh_thanh = TinhThanh.objects.get(tenTinhThanh__icontains="Da Nang")
            return tinh_thanh.maTinhThanh
        except:
            # Sử dụng maTinhThanh = 48 từ JSON data
            return 48

def get_next_ma_dia_diem():
    """Lấy maDiaDiem tiếp theo"""
    try:
        last_place = DiaDiem.objects.order_by('-maDiaDiem').first()
        if last_place:
            return last_place.maDiaDiem + 1
        return 1
    except:
        return 1

def check_place_exists(ten_dia_diem):
    """Kiểm tra địa điểm đã tồn tại chưa"""
    return DiaDiem.objects.filter(tenDiaDiem__iexact=ten_dia_diem).exists()

def main():
    print("=" * 70)
    print("THÊM 5 ĐỊA ĐIỂM Ở ĐÀ NẴNG VÀO DATABASE")
    print("=" * 70)
    
    # Tìm maTinhThanh
    ma_tinh_thanh = get_ma_tinh_thanh()
    print(f"\n✓ Tìm thấy maTinhThanh cho Đà Nẵng: {ma_tinh_thanh}")
    
    # Kiểm tra tỉnh thành có tồn tại không
    try:
        tinh_thanh = TinhThanh.objects.get(maTinhThanh=ma_tinh_thanh)
        print(f"✓ Tỉnh thành: {tinh_thanh.tenTinhThanh}")
    except TinhThanh.DoesNotExist:
        print(f"✗ Không tìm thấy tỉnh thành với maTinhThanh={ma_tinh_thanh}")
        return
    
    # Lấy maDiaDiem tiếp theo
    next_ma_dia_diem = get_next_ma_dia_diem()
    print(f"\n✓ maDiaDiem tiếp theo: {next_ma_dia_diem}")
    
    # Thêm từng địa điểm
    added_count = 0
    skipped_count = 0
    
    for idx, place_data in enumerate(places_data, start=1):
        ten_dia_diem = place_data['tenDiaDiem']
        
        print(f"\n[{idx}/5] Xử lý: {ten_dia_diem}")
        
        # Kiểm tra đã tồn tại chưa
        if check_place_exists(ten_dia_diem):
            print(f"   ⚠ Đã tồn tại, bỏ qua")
            skipped_count += 1
            continue
        
        try:
            # Parse giá vé (nếu None thì set 0.0 vì database có NOT NULL constraint)
            gia_ve = parse_gia_ve(place_data.get('giaVe'))
            if gia_ve is None:
                gia_ve = 0.0
            
            # Tạo địa điểm
            dia_diem = DiaDiem.objects.create(
                maTinhThanh_id=ma_tinh_thanh,
                tenDiaDiem=ten_dia_diem,
                moTa=place_data.get('moTa', ''),
                diaChi=place_data.get('diaChi', ''),
                loaiDiaDiem=place_data.get('loaiDiaDiem', 'khac'),
                viDo=place_data.get('viDo'),
                kinhDo=place_data.get('kinhDo'),
                giaVe=gia_ve,
                gioMoCua=place_data.get('gioMoCua', ''),
                gioDongCua=place_data.get('gioDongCua', ''),
                dienThoai=place_data.get('dienThoai') or '',
                website=place_data.get('website') or '',
                danhGiaTrungBinh=place_data.get('danhGiaTrungBinh', 0.0),
                soLuotDanhGia=0,
                soLuotXem=0,
                trangThai=place_data.get('trangThai', 'active'),
                dacDiem=place_data.get('dacDiem', ''),
                tienNghi=place_data.get('tienNghi', '')
            )
            
            print(f"   ✓ Đã thêm địa điểm (maDiaDiem: {dia_diem.maDiaDiem})")
            
            # Thêm hình ảnh
            if 'hinhAnh' in place_data:
                try:
                    hinh_anh_data = place_data['hinhAnh']
                    HinhAnhDiaDiem.objects.create(
                        maDiaDiem=dia_diem,
                        urlHinhAnh=hinh_anh_data['urlHinhAnh'],
                        moTa=hinh_anh_data.get('moTa', ''),
                        laChinh=hinh_anh_data.get('laChinh', False)
                    )
                    print(f"   ✓ Đã thêm hình ảnh")
                except Exception as img_error:
                    print(f"   ⚠ Không thể thêm hình ảnh: {img_error}")
                    # Bỏ qua lỗi hình ảnh, địa điểm đã được thêm thành công
            
            added_count += 1
            
        except Exception as e:
            print(f"   ✗ Lỗi: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("KẾT QUẢ")
    print("=" * 70)
    print(f"✓ Đã thêm: {added_count} địa điểm")
    print(f"⚠ Đã bỏ qua: {skipped_count} địa điểm (đã tồn tại)")
    print(f"✗ Lỗi: {5 - added_count - skipped_count} địa điểm")
    print("\n✅ Hoàn tất!")

if __name__ == '__main__':
    main()

