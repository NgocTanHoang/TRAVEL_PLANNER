#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script để import 5 địa điểm TP.HCM chất lượng cao vào bảng DIADIEM
"""
import os
import sys
import django
import re
from typing import Optional
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

# Dữ liệu 5 địa điểm TP.HCM chất lượng cao
PLACES_DATA = [
    {
        "tenDiaDiem": "Dinh Độc Lập (Hội trường Thống Nhất)",
        "moTa": "Dinh thự lịch sử chứng kiến nhiều sự kiện quan trọng trong lịch sử Việt Nam, nổi tiếng với kiến trúc độc đáo và ý nghĩa chính trị.",
        "moTaChiTiet": "Ý nghĩa Lịch sử: Là Di tích lịch sử cấp quốc gia đặc biệt, nơi chứng kiến sự kiện lịch sử trọng đại vào ngày 30/04/1975. Từng là nơi làm việc và sinh sống của Tổng thống Việt Nam Cộng hòa. Kiến trúc: Được xây dựng theo phong cách kiến trúc hiện đại, mang đậm dấu ấn kiến trúc phương Đông, với các phòng chức năng được giữ nguyên như phòng khánh tiết, phòng làm việc, phòng ngủ, hầm chỉ huy, và sân thượng có bãi đáp trực thăng. Trải nghiệm: Du khách có thể tham quan các căn phòng lịch sử và chiêm ngưỡng kiến trúc độc đáo, hiểu rõ hơn về giai đoạn lịch sử cận đại của Việt Nam.",
        "diaChi": "135 Nam Kỳ Khởi Nghĩa, Phường Bến Thành, Quận 1, TPHCM",
        "loaiDiaDiem": "lịch sử, kiến trúc",
        "viDo": 10.778735,
        "kinhDo": 106.695349,
        "giaVe": "Khoảng 40.000 VNĐ/người lớn",
        "gioMoCua": "08:00 - 16:30 (Trừ giờ nghỉ trưa)",
        "dienThoai": "028 3822 3652",
        "website": "http://www.dinhdoclap.gov.vn/",
        "danhGiaTrungBinh": 4.6,
        "dacDiem": "Di tích lịch sử cấp quốc gia đặc biệt, kiến trúc độc đáo",
        "tienNghi": "Khu vực trưng bày, quầy lưu niệm"
    },
    {
        "tenDiaDiem": "Nhà thờ Đức Bà Sài Gòn",
        "moTa": "Công trình kiến trúc Gothic tuyệt đẹp xây dựng từ thời Pháp thuộc, là biểu tượng văn hóa và du lịch của thành phố.",
        "moTaChiTiet": "Ý nghĩa & Kiến trúc: Là một trong những nhà thờ đẹp nhất Việt Nam, được xây dựng từ năm 1877 đến 1880 bởi người Pháp. Toàn bộ gạch xây đều được vận chuyển từ Marseille, Pháp sang. Kiến trúc theo phong cách Roman cải tiến và Gothic, nổi bật với hai tháp chuông cao 58 mét. Lưu ý: Hiện nhà thờ đang trong quá trình trùng tu lớn và kéo dài (dự kiến hoàn thành vào năm 2027), du khách chỉ có thể tham quan và chụp ảnh từ bên ngoài khuôn viên.",
        "diaChi": "01 Công xã Paris, Phường Bến Nghé, Quận 1, TPHCM",
        "loaiDiaDiem": "công trình kiến trúc, văn hóa, tâm linh",
        "viDo": 10.7797855,
        "kinhDo": 106.6990189,
        "giaVe": "Miễn phí tham quan bên ngoài",
        "gioMoCua": "Tham quan bên ngoài: Cả ngày (Hiện đang trong giai đoạn trùng tu)",
        "dienThoai": "0914 122 229",
        "website": "https://www.tgpsaigon.net/",
        "danhGiaTrungBinh": 4.7,
        "dacDiem": "Kiến trúc Gothic, gạch Pháp, tháp đôi 58m",
        "tienNghi": "Quảng trường xung quanh"
    },
    {
        "tenDiaDiem": "Bưu điện Trung tâm Sài Gòn",
        "moTa": "Công trình kiến trúc độc đáo mang phong cách châu Âu, vẫn còn hoạt động, là nơi lý tưởng để chụp ảnh và gửi thư.",
        "moTaChiTiet": "Ý nghĩa & Kiến trúc: Hoàn thành năm 1891, là một trong những công trình kiến trúc phương Tây tiêu biểu nhất tại TP.HCM. Thiết kế thường được gán cho kiến trúc sư Gustave Eiffel. Điểm nổi bật: Trần nhà cao, mái vòm bằng sắt, sàn gạch cổ, và hai tấm bản đồ lịch sử lớn ở hai bên tường chính. Trải nghiệm: Ngoài dịch vụ bưu chính, đây còn là nơi du khách ghé thăm để chiêm ngưỡng kiến trúc cổ kính, mua quà lưu niệm và chụp ảnh.",
        "diaChi": "02 Công xã Paris, Phường Bến Nghé, Quận 1, TPHCM",
        "loaiDiaDiem": "công trình kiến trúc, lịch sử",
        "viDo": 10.779956,
        "kinhDo": 106.700142,
        "giaVe": "Miễn phí",
        "gioMoCua": "07:00 - 18:00",
        "dienThoai": "028 3924 1000",
        "website": None,
        "danhGiaTrungBinh": 4.6,
        "dacDiem": "Thiết kế Eiffel, bản đồ cổ, quầy lưu niệm",
        "tienNghi": "Dịch vụ bưu chính, quầy đổi tiền, quầy quà lưu niệm"
    },
    {
        "tenDiaDiem": "Bảo tàng Chứng tích Chiến tranh",
        "moTa": "Nơi trưng bày các hiện vật, hình ảnh về cuộc chiến tranh Việt Nam, mang tính lịch sử và giáo dục sâu sắc.",
        "moTaChiTiet": "Ý nghĩa: Là bảo tàng chuyên đề về hậu quả của chiến tranh Việt Nam, trưng bày khoảng 20.000 hiện vật, tài liệu và phim ảnh về tội ác chiến tranh và hậu quả của nó đối với người dân. Trưng bày: Gồm các khu vực trưng bày chuyên đề như \"Chất độc màu da cam\", \"Tội ác chiến tranh\", và khu vực trưng bày ngoài trời với các hiện vật quân sự lớn (máy bay, xe tăng, pháo). Lưu ý: Là một nơi mang tính lịch sử sâu sắc và có thể gây xúc động mạnh.",
        "diaChi": "28 Võ Văn Tần, Phường Võ Thị Sáu, Quận 3, TPHCM",
        "loaiDiaDiem": "lịch sử, bảo tàng",
        "viDo": 10.777085,
        "kinhDo": 106.692298,
        "giaVe": "Khoảng 40.000 VNĐ/người lớn",
        "gioMoCua": "07:30 - 17:30 (Không nghỉ trưa)",
        "dienThoai": "028 3930 5587",
        "website": "http://www.warremnantsmuseum.com/",
        "danhGiaTrungBinh": 4.5,
        "dacDiem": "Trưng bày hiện vật chiến tranh, máy bay, xe tăng",
        "tienNghi": "Khu vực trưng bày ngoài trời và trong nhà"
    },
    {
        "tenDiaDiem": "Chợ Bến Thành",
        "moTa": "Chợ truyền thống lâu đời nhất TP.HCM, là trung tâm mua sắm, ẩm thực và quà lưu niệm.",
        "moTaChiTiet": "Ý nghĩa & Trải nghiệm: Là biểu tượng giao thương và văn hóa ẩm thực lâu đời của Sài Gòn. Nổi bật với Cửa Nam (tháp đồng hồ) là điểm nhận dạng kiến trúc. Hoạt động: Chợ ban ngày (6h - 18h) chủ yếu bán hàng hóa, quần áo, vải vóc, và đặc sản; Chợ đêm (sau 18h) là khu ẩm thực sầm uất với các món ăn đường phố nổi tiếng của Việt Nam. Lưu ý: Đây là một khu vực sầm uất, du khách nên mặc cả khi mua hàng.",
        "diaChi": "Lê Lợi, Phường Bến Thành, Quận 1, TPHCM",
        "loaiDiaDiem": "chợ, mua sắm, ẩm thực",
        "viDo": 10.772590,
        "kinhDo": 106.698097,
        "giaVe": "Miễn phí (Mua sắm: Tùy sản phẩm)",
        "gioMoCua": "Chợ ngày: 06:00 - 18:00 | Chợ đêm: 18:00 - 22:00",
        "dienThoai": "028 3829 9370",
        "website": None,
        "danhGiaTrungBinh": 4.3,
        "dacDiem": "Kiến trúc cổ, chợ đêm ẩm thực",
        "tienNghi": "Khu ẩm thực, quầy hàng đa dạng"
    }
]


def parse_gia_ve(gia_ve_str: str) -> Optional[float]:
    """Parse giá vé từ string sang số"""
    if not gia_ve_str or "miễn phí" in gia_ve_str.lower() or "free" in gia_ve_str.lower():
        return None
    
    # Loại bỏ dấu phẩy và dấu chấm (thường dùng để phân cách hàng nghìn)
    cleaned = gia_ve_str.replace(',', '').replace('.', '')
    
    # Tìm số trong chuỗi
    numbers = re.findall(r'\d+', cleaned)
    if numbers:
        try:
            # Lấy số lớn nhất (trong trường hợp có nhiều số)
            value = float(max(numbers, key=len))
            return value
        except (ValueError, TypeError):
            pass
    return None


def extract_gio_dong_cua(gio_mo_cua: str) -> str:
    """Extract giờ đóng cửa từ giờ mở cửa"""
    if not gio_mo_cua:
        return ''
    
    # Tìm pattern "HH:MM - HH:MM"
    match = re.search(r'(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})', gio_mo_cua)
    if match:
        return match.group(2)
    
    # Tìm tất cả các giờ trong chuỗi
    times = re.findall(r'(\d{1,2}:\d{2})', gio_mo_cua)
    if len(times) >= 2:
        return times[-1]  # Lấy giờ cuối cùng
    
    return ''


def map_loai_dia_diem(loai_str: str) -> str:
    """Map loại địa điểm từ string sang choice"""
    loai_lower = loai_str.lower()
    
    if any(word in loai_lower for word in ['nhà hàng', 'nha hang', 'restaurant']):
        return 'nha_hang'
    elif any(word in loai_lower for word in ['khách sạn', 'khach san', 'hotel']):
        return 'khach_san'
    elif any(word in loai_lower for word in ['chợ', 'cho', 'mua sắm', 'mua sam', 'market', 'shopping']):
        return 'mua_sam'
    elif any(word in loai_lower for word in ['giải trí', 'giai tri', 'entertainment', 'vui chơi']):
        return 'giai_tri'
    elif any(word in loai_lower for word in ['bảo tàng', 'bao tang', 'museum']):
        return 'dia_danh'
    else:
        return 'dia_danh'  # Mặc định là địa danh


def import_places():
    """Import các địa điểm vào database"""
    # Tìm tỉnh thành TP.HCM
    tinh_thanh_names = [
        'Thành phố Hồ Chí Minh',
        'TP. Hồ Chí Minh',
        'TPHCM',
        'Hồ Chí Minh',
        'Sài Gòn'
    ]
    
    tinh_thanh = None
    for name in tinh_thanh_names:
        tinh_thanh = TinhThanh.objects.filter(tenTinhThanh__icontains=name).first()
        if tinh_thanh:
            break
    
    if not tinh_thanh:
        print("[ERROR] Không tìm thấy tỉnh thành TP.HCM trong database!")
        print("Vui lòng import tỉnh thành trước.")
        return
    
    print(f"[OK] Tìm thấy tỉnh thành: {tinh_thanh.tenTinhThanh} (ID: {tinh_thanh.maTinhThanh})")
    print()
    
    imported_count = 0
    updated_count = 0
    error_count = 0
    
    for place_data in PLACES_DATA:
        try:
            # Parse giá vé
            gia_ve = parse_gia_ve(place_data.get('giaVe', ''))
            
            # Extract giờ đóng cửa (đảm bảo luôn có giá trị, không được None)
            gio_dong_cua = extract_gio_dong_cua(place_data.get('gioMoCua', '')) or ''
            
            # Map loại địa điểm
            loai_dia_diem = map_loai_dia_diem(place_data.get('loaiDiaDiem', ''))
            
            # Kết hợp mô tả ngắn và chi tiết
            mo_ta = place_data.get('moTa', '')
            mo_ta_chi_tiet = place_data.get('moTaChiTiet', '')
            if mo_ta_chi_tiet:
                mo_ta_full = f"{mo_ta}\n\n{mo_ta_chi_tiet}"
            else:
                mo_ta_full = mo_ta
            
            # Lấy đặc điểm và tiện nghi riêng (không thêm vào mô tả)
            dac_diem = place_data.get('dacDiem', '')
            tien_nghi = place_data.get('tienNghi', '')
            
                                    # Tìm địa điểm theo tên
            existing_place = DiaDiem.objects.filter(
                tenDiaDiem__iexact=place_data['tenDiaDiem']
            ).first()
            
            place_dict = {
                'tenDiaDiem': place_data['tenDiaDiem'],
                'moTa': mo_ta_full.strip(),
                'diaChi': place_data.get('diaChi', ''),
                'maTinhThanh': tinh_thanh,
                'loaiDiaDiem': loai_dia_diem,
                'viDo': place_data.get('viDo'),
                'kinhDo': place_data.get('kinhDo'),
                'giaVe': gia_ve,
                'gioMoCua': place_data.get('gioMoCua', ''),
                'gioDongCua': gio_dong_cua,
                'dienThoai': place_data.get('dienThoai', ''),
                'website': place_data.get('website') or '',
                'danhGiaTrungBinh': place_data.get('danhGiaTrungBinh', 0.0),
                'dacDiem': dac_diem or '',
                'tienNghi': tien_nghi or '',
                'trangThai': 'active',
            }
            
            if existing_place:
                # Cập nhật
                for key, value in place_dict.items():
                    setattr(existing_place, key, value)
                existing_place.save()
                updated_count += 1
                print(f"[UPDATE] Đã cập nhật: {place_data['tenDiaDiem']} (ID: {existing_place.maDiaDiem})")
            else:
                # Tạo mới
                new_place = DiaDiem.objects.create(**place_dict)
                imported_count += 1
                print(f"[CREATE] Đã tạo mới: {place_data['tenDiaDiem']} (ID: {new_place.maDiaDiem})")
                
        except Exception as e:
            error_count += 1
            print(f"[ERROR] Lỗi khi import {place_data.get('tenDiaDiem', 'Unknown')}: {e}")
            import traceback
            traceback.print_exc()
    
    print()
    print("="*60)
    print(f"KẾT QUẢ IMPORT:")
    print(f"  - Đã tạo mới: {imported_count} địa điểm")
    print(f"  - Đã cập nhật: {updated_count} địa điểm")
    print(f"  - Lỗi: {error_count} địa điểm")
    print("="*60)
    
    # Kiểm tra tổng số địa điểm
    total_count = DiaDiem.objects.count()
    print(f"\n[INFO] Tổng số địa điểm trong database: {total_count}")


if __name__ == '__main__':
    print("="*60)
    print("IMPORT 5 ĐỊA ĐIỂM TP.HCM CHẤT LƯỢNG CAO VÀO BẢNG DIADIEM")
    print("="*60)
    print()
    
    import_places()
    
    print("\n[OK] Hoàn thành!")
