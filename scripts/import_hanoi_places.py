#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script để import 30 địa điểm Hà Nội vào bảng DIADIEM
"""
import os
import sys
import django
import re
import json
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

# JSON data - 30 địa điểm Hà Nội
JSON_DATA = {
    "ngayCapNhat": "2025-11-03T12:49:00+07:00",
    "tinhThanh": "Hà Nội",
    "maTinhThanh": 79,
    "tongSoDiaDiem": 30,
    "danhSachDiaDiem": [
        {"maDiaDiem": 101, "tenDiaDiem": "Hồ Hoàn Kiếm và Đền Ngọc Sơn", "moTa": "Trái tim của Thủ đô, gắn liền với truyền thuyết trả gươm thần. Là khu vực di tích lịch sử, văn hóa và không gian đi bộ cuối tuần.", "diaChi": "Phố Đinh Tiên Hoàng, Hoàn Kiếm, Hà Nội", "loaiDiaDiem": "văn hóa, lịch sử, giải trí", "viDo": 21.028511, "kinhDo": 105.854167, "giaVe": "Miễn phí (Đền Ngọc Sơn: khoảng 30.000 VNĐ)", "gioMoCua": "Cả ngày (Đền Ngọc Sơn: 07:30 - 18:00)", "dienThoai": None, "website": None, "danhGiaTrungBinh": 4.6, "dacDiem": "Di tích lịch sử, không gian đi bộ, Tháp Rùa", "tienNghi": "Phố đi bộ, dịch vụ xung quanh"},
        {"maDiaDiem": 102, "tenDiaDiem": "Lăng Chủ tịch Hồ Chí Minh và Quảng trường Ba Đình", "moTa": "Nơi an nghỉ của Chủ tịch Hồ Chí Minh, là biểu tượng lịch sử và chính trị quan trọng nhất của Việt Nam.", "diaChi": "Số 2 Hùng Vương, Điện Biên, Ba Đình, Hà Nội", "loaiDiaDiem": "lịch sử, văn hóa", "viDo": 21.03673, "kinhDo": 105.834689, "giaVe": "Miễn phí (Phải tuân theo quy định nghiêm ngặt)", "gioMoCua": "7:30 - 10:30 (Thay đổi theo mùa và ngày lễ)", "dienThoai": None, "website": None, "danhGiaTrungBinh": 4.7, "dacDiem": "Công trình kiến trúc vĩ đại, nghi lễ thượng cờ", "tienNghi": None},
        {"maDiaDiem": 103, "tenDiaDiem": "Văn Miếu - Quốc Tử Giám", "moTa": "Trường đại học đầu tiên của Việt Nam, nơi thờ Khổng Tử và các bậc hiền triết, là biểu tượng của tinh thần hiếu học.", "diaChi": "58 Phố Quốc Tử Giám, Văn Miếu, Đống Đa, Hà Nội", "loaiDiaDiem": "lịch sử, văn hóa", "viDo": 21.028906, "kinhDo": 105.834017, "giaVe": "Khoảng 30.000 VNĐ", "gioMoCua": "07:30 - 17:30", "dienThoai": "+84 24 3845 2928", "website": None, "danhGiaTrungBinh": 4.5, "dacDiem": "Bia đá tiến sĩ, Khuê Văn Các", "tienNghi": "Hướng dẫn viên, bãi đỗ xe"},
        {"maDiaDiem": 104, "tenDiaDiem": "Phố Cổ Hà Nội (Khu 36 phố phường)", "moTa": "Khu vực buôn bán sầm uất với kiến trúc cổ kính, là nơi tập trung tinh hoa ẩm thực và văn hóa truyền thống Hà Nội.", "diaChi": "Các phố Hàng Ngang, Hàng Đào, Mã Mây, Tạ Hiện (Quận Hoàn Kiếm)", "loaiDiaDiem": "văn hóa, lịch sử, giải trí, ẩm thực", "viDo": 21.033575, "kinhDo": 105.851944, "giaVe": "Miễn phí", "gioMoCua": "Cả ngày", "dienThoai": None, "website": None, "danhGiaTrungBinh": 4.5, "dacDiem": "Kiến trúc nhà ống cổ, chợ đêm, phố bia Tạ Hiện", "tienNghi": "Ẩm thực đường phố, mua sắm"},
        {"maDiaDiem": 105, "tenDiaDiem": "Nhà tù Hỏa Lò", "moTa": "Di tích lịch sử ghi dấu những năm tháng đấu tranh kiên cường của các chiến sĩ cách mạng Việt Nam.", "diaChi": "1 Hỏa Lò, Trần Hưng Đạo, Hoàn Kiếm, Hà Nội", "loaiDiaDiem": "lịch sử", "viDo": 21.023223, "kinhDo": 105.845459, "giaVe": "Khoảng 30.000 VNĐ", "gioMoCua": "08:00 - 17:00", "dienThoai": "+84 24 3934 2253", "website": "https://hoalo.vn/", "danhGiaTrungBinh": 4.4, "dacDiem": "Di tích kiến trúc Pháp, trưng bày hiện vật chiến tranh", "tienNghi": "Phòng trưng bày, quầy lưu niệm"},
        {"maDiaDiem": 106, "tenDiaDiem": "Bảo tàng Dân tộc học Việt Nam", "moTa": "Nơi lưu giữ, trưng bày các hiện vật về văn hóa 54 dân tộc Việt Nam, với kiến trúc độc đáo và khu vực ngoài trời rộng lớn.", "diaChi": "Nguyễn Văn Huyên, Quan Hoa, Cầu Giấy, Hà Nội", "loaiDiaDiem": "văn hóa", "viDo": 21.05047, "kinhDo": 105.798151, "giaVe": "Khoảng 40.000 VNĐ", "gioMoCua": "08:30 - 17:30 (Đóng cửa thứ Hai)", "dienThoai": "+84 24 3756 2194", "website": "http://www.vme.org.vn/", "danhGiaTrungBinh": 4.6, "dacDiem": "Trưng bày nhà cửa dân tộc, rối nước", "tienNghi": "Bãi đỗ xe, quầy hàng thủ công"},
        {"maDiaDiem": 107, "tenDiaDiem": "Hồ Tây và Phủ Tây Hồ", "moTa": "Hồ lớn nhất Hà Nội, mang vẻ đẹp lãng mạn, thanh bình. Phủ Tây Hồ là di tích thờ Bà Chúa Liễu Hạnh, linh thiêng và cổ kính.", "diaChi": "Đường Thanh Niên, Tây Hồ, Hà Nội (và khu vực xung quanh)", "loaiDiaDiem": "văn hóa, giải trí, nghỉ dưỡng", "viDo": 21.054359, "kinhDo": 105.823908, "giaVe": "Miễn phí (Phủ Tây Hồ: Miễn phí)", "gioMoCua": "Cả ngày", "dienThoai": None, "website": None, "danhGiaTrungBinh": 4.5, "dacDiem": "Đạp xe, ngắm hoàng hôn, Phủ Tây Hồ, Chùa Trấn Quốc", "tienNghi": "Quán cà phê, nhà hàng ven hồ"},
        {"maDiaDiem": 108, "tenDiaDiem": "Nhà thờ Lớn Hà Nội", "moTa": "Công trình kiến trúc Gothic cổ kính được xây dựng từ cuối thế kỷ 19, là nơi sinh hoạt tôn giáo và điểm check-in nổi tiếng.", "diaChi": "40 Nhà Chung, Hàng Trống, Hoàn Kiếm, Hà Nội", "loaiDiaDiem": "văn hóa, lịch sử", "viDo": 21.026362, "kinhDo": 105.851083, "giaVe": "Miễn phí", "gioMoCua": "Tham quan bên ngoài: Cả ngày (Giờ lễ: Thay đổi)", "dienThoai": None, "website": None, "danhGiaTrungBinh": 4.5, "dacDiem": "Kiến trúc Gothic, khu vực cà phê", "tienNghi": "Các dịch vụ giải trí xung quanh"},
        {"maDiaDiem": 109, "tenDiaDiem": "Hoàng thành Thăng Long", "moTa": "Di sản Văn hóa Thế giới, khu di tích lịch sử quan trọng, chứng kiến thăng trầm của các triều đại phong kiến Việt Nam.", "diaChi": "19 Hoàng Diệu, Điện Biên, Ba Đình, Hà Nội", "loaiDiaDiem": "lịch sử, văn hóa", "viDo": 21.037861, "kinhDo": 105.836066, "giaVe": "Khoảng 30.000 VNĐ", "gioMoCua": "08:00 - 17:00 (Đóng cửa thứ Hai)", "dienThoai": "+84 24 3734 5440", "website": "http://www.hoangthanhthanglong.vn/", "danhGiaTrungBinh": 4.5, "dacDiem": "Khu di tích khảo cổ, Cột cờ Hà Nội, Đoan Môn", "tienNghi": "Khu vực trưng bày"},
        {"maDiaDiem": 110, "tenDiaDiem": "Làng Gốm Bát Tràng", "moTa": "Làng nghề truyền thống nổi tiếng với các sản phẩm gốm sứ tinh xảo, du khách có thể tự tay làm gốm và mua sắm.", "diaChi": "Xã Bát Tràng, Gia Lâm, Hà Nội (cách trung tâm khoảng 13km)", "loaiDiaDiem": "văn hóa, vui chơi, giải trí", "viDo": 20.975416, "kinhDo": 105.901584, "giaVe": "Miễn phí (Trải nghiệm làm gốm: từ 50.000 VNĐ)", "gioMoCua": "08:00 - 18:00", "dienThoai": None, "website": None, "danhGiaTrungBinh": 4.3, "dacDiem": "Làng nghề truyền thống, trải nghiệm thủ công", "tienNghi": "Chợ gốm, quán ăn"},
        {"maDiaDiem": 111, "tenDiaDiem": "Vườn Quốc gia Ba Vì", "moTa": "Khu du lịch sinh thái nổi tiếng gần Hà Nội, với không khí mát mẻ, trong lành, thích hợp cho trekking, cắm trại và nghỉ dưỡng.", "diaChi": "Xã Tản Lĩnh, Ba Vì, Hà Nội (cách trung tâm khoảng 50km)", "loaiDiaDiem": "nghỉ dưỡng, mạo hiểm, thể thao, sinh thái", "viDo": 21.056073, "kinhDo": 105.321798, "giaVe": "Khoảng 60.000 VNĐ/người lớn", "gioMoCua": "07:30 - 17:00", "dienThoai": "+84 24 3388 1205", "website": "https://vuonquocgiabavi.com.vn/", "danhGiaTrungBinh": 4.4, "dacDiem": "Leo núi, nhà thờ đổ, vườn xương rồng, đỉnh Vua", "tienNghi": "Homestay, cắm trại, nhà hàng"},
        {"maDiaDiem": 112, "tenDiaDiem": "Chùa Một Cột", "moTa": "Ngôi chùa có kiến trúc độc đáo, hình dáng như một đóa sen vươn lên từ mặt nước, là biểu tượng Phật giáo của Thủ đô.", "diaChi": "Phố Chùa Một Cột, Đội Cấn, Ba Đình, Hà Nội", "loaiDiaDiem": "văn hóa, lịch sử", "viDo": 21.036139, "kinhDo": 105.834079, "giaVe": "Miễn phí", "gioMoCua": "08:00 - 17:00", "dienThoai": None, "website": None, "danhGiaTrungBinh": 4.3, "dacDiem": "Kiến trúc độc đáo", "tienNghi": None},
        {"maDiaDiem": 113, "tenDiaDiem": "Công viên Nước Hồ Tây", "moTa": "Khu vui chơi giải trí dưới nước lớn và lâu đời nhất tại Hà Nội, với nhiều trò chơi mạo hiểm và thư giãn.", "diaChi": "614 Lạc Long Quân, Nhật Tân, Tây Hồ, Hà Nội", "loaiDiaDiem": "vui chơi, giải trí", "viDo": 21.066455, "kinhDo": 105.807857, "giaVe": "Khoảng 170.000 - 190.000 VNĐ", "gioMoCua": "09:00 - 20:00 (Thay đổi theo mùa)", "dienThoai": "+84 24 3718 4198", "website": "http://www.hoangminhmedia.com/", "danhGiaTrungBinh": 3.8, "dacDiem": "Trò chơi mạo hiểm dưới nước, bể bơi tạo sóng", "tienNghi": "Nhà hàng, khu thay đồ"},
        {"maDiaDiem": 114, "tenDiaDiem": "Grand World Hà Nội (Ocean Park 3)", "moTa": "Tổ hợp vui chơi giải trí và mua sắm theo phong cách Venice, có kênh đào lãng mạn, quảng trường sôi động và khu phố thương mại.", "diaChi": "Đường Đại Dương, Văn Giang, Hưng Yên (Khu vực Đông Hà Nội)", "loaiDiaDiem": "vui chơi, giải trí, mua sắm", "viDo": 20.938889, "kinhDo": 105.975000, "giaVe": "Miễn phí tham quan (Trò chơi, show: Tính phí)", "gioMoCua": "10:00 - 22:00", "dienThoai": None, "website": None, "danhGiaTrungBinh": 4.2, "dacDiem": "Đi thuyền Gondola, show The Grand Voyage", "tienNghi": "Nhà hàng, cafe, khu mua sắm"},
        {"maDiaDiem": 115, "tenDiaDiem": "Làng cổ Đường Lâm", "moTa": "Làng cổ đầu tiên được Nhà nước công nhận là Di tích lịch sử văn hóa quốc gia, nổi tiếng với kiến trúc nhà cổ bằng đá ong.", "diaChi": "Thị xã Sơn Tây, Hà Nội (cách trung tâm khoảng 44km)", "loaiDiaDiem": "lịch sử, văn hóa, nghỉ dưỡng", "viDo": 21.146914, "kinhDo": 105.421596, "giaVe": "Khoảng 20.000 VNĐ", "gioMoCua": "08:00 - 17:00", "dienThoai": None, "website": None, "danhGiaTrungBinh": 4.5, "dacDiem": "Nhà cổ đá ong, Đình Mông Phụ, chùa Mía", "tienNghi": "Homestay, dịch vụ ăn uống"},
        {"maDiaDiem": 116, "tenDiaDiem": "Thủy cung Vinpearl Aquarium Times City", "moTa": "Thủy cung hiện đại nằm trong lòng đất, trưng bày hàng ngàn loài sinh vật biển và có khu vực sinh vật nước ngọt, bò sát.", "diaChi": "Tầng B1, TTTM Vincom Mega Mall, 458 Minh Khai, Hai Bà Trưng", "loaiDiaDiem": "giải trí, vui chơi", "viDo": 21.002811, "kinhDo": 105.862417, "giaVe": "Khoảng 170.000 - 250.000 VNĐ", "gioMoCua": "09:30 - 22:00", "dienThoai": None, "website": "https://aquarium.vinpearlland.com/", "danhGiaTrungBinh": 4.4, "dacDiem": "Đường hầm đại dương, show nàng tiên cá", "tienNghi": "Nhà hàng, khu mua sắm"},
        {"maDiaDiem": 117, "tenDiaDiem": "Lotte Observation Deck (Lotte Sky 72)", "moTa": "Đài quan sát trên tầng 65 của tòa nhà Lotte Center, là nơi lý tưởng để ngắm toàn cảnh thành phố Hà Nội từ trên cao.", "diaChi": "54 Liễu Giai, Cống Vị, Ba Đình, Hà Nội", "loaiDiaDiem": "giải trí, check-in", "viDo": 21.037805, "kinhDo": 105.815049, "giaVe": "Khoảng 230.000 - 250.000 VNĐ", "gioMoCua": "09:00 - 22:00", "dienThoai": "+84 24 3333 6000", "website": "https://www.lottecenterhanoi.com/", "danhGiaTrungBinh": 4.3, "dacDiem": "Kính thiên văn, sàn kính, sky bar", "tienNghi": "Nhà hàng, khu mua sắm"},
        {"maDiaDiem": 118, "tenDiaDiem": "Cầu Long Biên", "moTa": "Cây cầu lịch sử do Pháp xây dựng, là biểu tượng kiến trúc gắn liền với lịch sử kháng chiến và vẻ đẹp cổ kính của Hà Nội.", "diaChi": "Giữa các quận Hoàn Kiếm và Long Biên", "loaiDiaDiem": "lịch sử, văn hóa, check-in", "viDo": 21.050519, "kinhDo": 105.864784, "giaVe": "Miễn phí", "gioMoCua": "Cả ngày", "dienThoai": None, "website": None, "danhGiaTrungBinh": 4.4, "dacDiem": "Kiến trúc thép cổ, ngắm sông Hồng", "tienNghi": "Quán cà phê, dịch vụ nhỏ"},
        {"maDiaDiem": 119, "tenDiaDiem": "Chùa Hương", "moTa": "Quần thể văn hóa - tôn giáo lớn, nổi tiếng với chuyến đi thuyền qua suối Yến và lễ hội chùa Hương đầu năm.", "diaChi": "Xã Hương Sơn, huyện Mỹ Đức, Hà Nội (cách trung tâm khoảng 60km)", "loaiDiaDiem": "văn hóa, lịch sử, nghỉ dưỡng", "viDo": 20.672937, "kinhDo": 105.748366, "giaVe": "Khoảng 80.000 VNĐ/người (chưa bao gồm thuyền và cáp treo)", "gioMoCua": "06:00 - 18:00", "dienThoai": None, "website": None, "danhGiaTrungBinh": 4.5, "dacDiem": "Du thuyền trên suối Yến, lễ hội đầu năm", "tienNghi": "Nhà hàng, cáp treo"},
        {"maDiaDiem": 120, "tenDiaDiem": "Hồ Quan Sơn", "moTa": "Được ví là 'Hạ Long trên cạn' của Hà Nội, với cảnh quan non nước hữu tình, thích hợp cho chèo thuyền và thư giãn.", "diaChi": "Huyện Mỹ Đức, Hà Nội (cách trung tâm khoảng 50km)", "loaiDiaDiem": "nghỉ dưỡng, sinh thái", "viDo": 20.730331, "kinhDo": 105.745427, "giaVe": "Khoảng 15.000 VNĐ (chưa bao gồm thuyền)", "gioMoCua": "07:00 - 18:00", "dienThoai": None, "website": None, "danhGiaTrungBinh": 4.3, "dacDiem": "Chèo thuyền, ngắm cảnh, cắm trại", "tienNghi": "Dịch vụ thuyền bè"},
        {"maDiaDiem": 121, "tenDiaDiem": "Công viên Thống Nhất", "moTa": "Một trong những công viên lớn nhất Hà Nội, với Hồ Bảy Mẫu, thích hợp cho các hoạt động thể thao, giải trí nhẹ nhàng.", "diaChi": "Trần Nhân Tông, Lê Đại Hành, Hai Bà Trưng, Hà Nội", "loaiDiaDiem": "giải trí, thể thao", "viDo": 21.006935, "kinhDo": 105.845941, "giaVe": "Miễn phí", "gioMoCua": "05:00 - 22:00", "dienThoai": None, "website": None, "danhGiaTrungBinh": 4.3, "dacDiem": "Chạy bộ, đạp vịt, khu vui chơi trẻ em", "tienNghi": "Quán nước, khu tập thể thao"},
        {"maDiaDiem": 122, "tenDiaDiem": "Bảo tàng Phụ nữ Việt Nam", "moTa": "Nơi trưng bày các hiện vật, hình ảnh về vai trò và đóng góp của phụ nữ Việt Nam trong lịch sử và đời sống.", "diaChi": "36 Lý Thường Kiệt, Hàng Bài, Hoàn Kiếm, Hà Nội", "loaiDiaDiem": "văn hóa, lịch sử", "viDo": 21.018861, "kinhDo": 105.854298, "giaVe": "Khoảng 40.000 VNĐ", "gioMoCua": "08:00 - 17:00", "dienThoai": "+84 24 3825 9180", "website": "http://www.vnwm.org.vn/", "danhGiaTrungBinh": 4.5, "dacDiem": "Trưng bày theo chủ đề: Gia đình, Phụ nữ trong chiến tranh", "tienNghi": "Quầy lưu niệm, quán cà phê"},
        {"maDiaDiem": 123, "tenDiaDiem": "Nhà Hát Lớn Hà Nội", "moTa": "Công trình kiến trúc tân cổ điển tuyệt đẹp, là trung tâm biểu diễn nghệ thuật lớn của thủ đô.", "diaChi": "1 Tràng Tiền, Phan Chu Trinh, Hoàn Kiếm, Hà Nội", "loaiDiaDiem": "văn hóa, giải trí", "viDo": 21.021021, "kinhDo": 105.856012, "giaVe": "Thay đổi theo chương trình", "gioMoCua": "Thay đổi theo chương trình", "dienThoai": "+84 24 3933 0100", "website": "http://hanoioperahouse.org.vn/", "danhGiaTrungBinh": 4.5, "dacDiem": "Kiến trúc Pháp, biểu diễn Opera, múa, hòa nhạc", "tienNghi": "Quầy bar, phòng chờ"},
        {"maDiaDiem": 124, "tenDiaDiem": "Bảo tàng Mỹ thuật Việt Nam", "moTa": "Nơi lưu giữ các tác phẩm nghệ thuật tiêu biểu từ thời tiền sử đến hiện đại, đặc biệt là nghệ thuật dân gian và tranh sơn mài.", "diaChi": "66 Nguyễn Thái Học, Điện Biên, Ba Đình, Hà Nội", "loaiDiaDiem": "văn hóa", "viDo": 21.031572, "kinhDo": 105.839818, "giaVe": "Khoảng 40.000 VNĐ", "gioMoCua": "08:30 - 17:00", "dienThoai": "+84 24 3823 3084", "website": "http://vnfineartmuseum.org.vn/", "danhGiaTrungBinh": 4.4, "dacDiem": "Tranh sơn mài, điêu khắc, hội họa", "tienNghi": "Phòng trưng bày, quầy lưu niệm"},
        {"maDiaDiem": 125, "tenDiaDiem": "Đền Quán Thánh", "moTa": "Một trong Tứ trấn Thăng Long, thờ Huyền Thiên Trấn Vũ, bảo vệ phía Bắc kinh thành.", "diaChi": "Đường Thanh Niên, Quán Thánh, Ba Đình, Hà Nội", "loaiDiaDiem": "văn hóa, lịch sử", "viDo": 21.045431, "kinhDo": 105.836366, "giaVe": "Khoảng 10.000 VNĐ", "gioMoCua": "08:00 - 17:00", "dienThoai": None, "website": None, "danhGiaTrungBinh": 4.5, "dacDiem": "Kiến trúc đền cổ, tượng Trấn Vũ bằng đồng", "tienNghi": None},
        {"maDiaDiem": 126, "tenDiaDiem": "Công viên Thủ Lệ (Vườn Bách Thảo)", "moTa": "Khu vực vườn thú và vui chơi giải trí quen thuộc của người dân Hà Nội.", "diaChi": "Đường Bưởi, Ngọc Khánh, Ba Đình, Hà Nội", "loaiDiaDiem": "giải trí, vui chơi", "viDo": 21.030588, "kinhDo": 105.801646, "giaVe": "Khoảng 30.000 VNĐ", "gioMoCua": "08:00 - 18:00", "dienThoai": "+84 24 3834 7226", "website": None, "danhGiaTrungBinh": 4.0, "dacDiem": "Khu vực nuôi thú, trò chơi thiếu nhi", "tienNghi": "Quán nước, khu ẩm thực"},
        {"maDiaDiem": 127, "tenDiaDiem": "Thiên Đường Bảo Sơn", "moTa": "Tổ hợp du lịch, giải trí và ẩm thực lớn với khu vui chơi, công viên nước, safari và làng nghề truyền thống.", "diaChi": "Km 5.8 Đường Lê Trọng Tấn, An Khánh, Hoài Đức, Hà Nội", "loaiDiaDiem": "vui chơi, giải trí, văn hóa", "viDo": 21.000787, "kinhDo": 105.733526, "giaVe": "Khoảng 150.000 - 300.000 VNĐ", "gioMoCua": "08:00 - 18:00 (Đóng cửa thứ Ba)", "dienThoai": "+84 985 892 277", "website": "http://baosonparadise.vn/", "danhGiaTrungBinh": 4.1, "dacDiem": "Safari, thủy cung, làng nghề truyền thống", "tienNghi": "Nhà hàng, khu ẩm thực"},
        {"maDiaDiem": 128, "tenDiaDiem": "Đồi Bù (Sóc Sơn/Lương Sơn)", "moTa": "Địa điểm du lịch mạo hiểm nổi tiếng gần Hà Nội, nơi tổ chức các hoạt động dù lượn và cắm trại ngắm cảnh.", "diaChi": "Xã Nam Phương Tiến, Chương Mỹ, Hà Nội (Gần khu vực Hoà Bình)", "loaiDiaDiem": "mạo hiểm, thể thao, nghỉ dưỡng", "viDo": 20.90045, "kinhDo": 105.51352, "giaVe": "Miễn phí (Trải nghiệm dù lượn: từ 1.200.000 VNĐ)", "gioMoCua": "Cả ngày", "dienThoai": None, "website": None, "danhGiaTrungBinh": 4.3, "dacDiem": "Dù lượn, cắm trại, ngắm mây", "tienNghi": "Dịch vụ cho thuê lều trại"},
        {"maDiaDiem": 129, "tenDiaDiem": "Làng Văn hóa - Du lịch các dân tộc Việt Nam", "moTa": "Nơi tái hiện kiến trúc và văn hóa của 54 dân tộc, thích hợp cho việc tìm hiểu văn hóa và nghỉ dưỡng.", "diaChi": "Đồng Mô, Sơn Tây, Hà Nội (cách trung tâm khoảng 40km)", "loaiDiaDiem": "văn hóa, nghỉ dưỡng", "viDo": 21.077618, "kinhDo": 105.353396, "giaVe": "Khoảng 30.000 VNĐ", "gioMoCua": "08:00 - 17:00", "dienThoai": "+84 24 3837 3110", "website": "http://langvanhoa.gov.vn/", "danhGiaTrungBinh": 4.4, "dacDiem": "Khu làng dân tộc, Biển Hồ Đồng Mô", "tienNghi": "Nhà sàn nghỉ dưỡng, nhà hàng"},
        {"maDiaDiem": 130, "tenDiaDiem": "Phố Sách Đinh Lễ", "moTa": "Con phố nhỏ nổi tiếng với các nhà sách lớn và nhỏ, là địa điểm lý tưởng cho những người yêu thích đọc sách.", "diaChi": "Phố Đinh Lễ, Tràng Tiền, Hoàn Kiếm, Hà Nội", "loaiDiaDiem": "văn hóa, giải trí", "viDo": 21.026402, "kinhDo": 105.855322, "giaVe": "Miễn phí", "gioMoCua": "08:00 - 21:00", "dienThoai": None, "website": None, "danhGiaTrungBinh": 4.5, "dacDiem": "Đa dạng các loại sách, không gian yên tĩnh", "tienNghi": "Quán cà phê, tiện ích xung quanh"},
        {"maDiaDiem": 131, "tenDiaDiem": "Khu Bảo tồn Thiên nhiên Sóc Sơn", "moTa": "Khu rừng nguyên sinh gần Hà Nội, nơi có nhiều đỉnh núi và các đền thờ linh thiêng như Đền Sóc, Chùa Non Nước.", "diaChi": "Huyện Sóc Sơn, Hà Nội", "loaiDiaDiem": "sinh thái, mạo hiểm, văn hóa", "viDo": 21.282914, "kinhDo": 105.855216, "giaVe": "Miễn phí", "gioMoCua": "Cả ngày", "dienThoai": None, "website": None, "danhGiaTrungBinh": 4.4, "dacDiem": "Trekking, cắm trại, đền Gióng", "tienNghi": "Các homestay, dịch vụ ăn uống nhỏ"},
        {"maDiaDiem": 132, "tenDiaDiem": "Cột cờ Hà Nội", "moTa": "Di tích lịch sử nằm trong khuôn viên Bảo tàng Lịch sử Quân sự Việt Nam, là biểu tượng kiên cường của Thủ đô.", "diaChi": "Điện Biên Phủ, Điện Bàn, Ba Đình, Hà Nội", "loaiDiaDiem": "lịch sử", "viDo": 21.033611, "kinhDo": 105.842778, "giaVe": "Khoảng 30.000 VNĐ (Bảo tàng)", "gioMoCua": "08:00 - 17:00", "dienThoai": "+84 24 3734 3291", "website": None, "danhGiaTrungBinh": 4.5, "dacDiem": "Kiến trúc độc đáo", "tienNghi": None},
        {"maDiaDiem": 133, "tenDiaDiem": "Khu di tích Thành Cổ Loa", "moTa": "Kinh đô của nhà nước Âu Lạc thời An Dương Vương, nổi tiếng với kiến trúc thành lũy xoáy trôn ốc cổ kính.", "diaChi": "Xã Cổ Loa, Đông Anh, Hà Nội", "loaiDiaDiem": "lịch sử, văn hóa", "viDo": 21.139000, "kinhDo": 105.879000, "giaVe": "Khoảng 10.000 VNĐ", "gioMoCua": "08:00 - 17:00", "dienThoai": None, "website": None, "danhGiaTrungBinh": 4.3, "dacDiem": "Thành lũy, đền thờ An Dương Vương", "tienNghi": None}
    ]
}

def parse_gia_ve(gia_ve_str: str) -> Optional[float]:
    """Parse giá vé từ string sang số"""
    if not gia_ve_str or "miễn phí" in gia_ve_str.lower() or "free" in gia_ve_str.lower():
        return None
    cleaned = gia_ve_str.replace(',', '').replace('.', '')
    numbers = re.findall(r'\d+', cleaned)
    if numbers:
        try:
            value = float(max(numbers, key=len))
            return value
        except (ValueError, TypeError):
            pass
    return None

def extract_gio_dong_cua(gio_mo_cua: str) -> str:
    """Extract giờ đóng cửa từ giờ mở cửa"""
    if not gio_mo_cua:
        return ''
    match = re.search(r'(\d{1,2}:\d{2})\s*-\s*(\d{1,2}:\d{2})', gio_mo_cua)
    if match:
        return match.group(2)
    times = re.findall(r'(\d{1,2}:\d{2})', gio_mo_cua)
    if len(times) >= 2:
        return times[-1]
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
    elif any(word in loai_lower for word in ['giải trí', 'giai tri', 'entertainment', 'vui chơi', 'check-in']):
        return 'giai_tri'
    elif any(word in loai_lower for word in ['bảo tàng', 'bao tang', 'museum']):
        return 'dia_danh'
    elif any(word in loai_lower for word in ['nghỉ dưỡng', 'nghi duong', 'resort', 'sinh thái', 'sinh thai']):
        return 'dia_danh'
    elif any(word in loai_lower for word in ['mạo hiểm', 'mao hiem', 'adventure', 'thể thao', 'the thao']):
        return 'giai_tri'
    else:
        return 'dia_danh'

def import_places():
    """Import các địa điểm vào database"""
    tinh_thanh_names = ['Hà Nội', 'Ha Noi', 'Hanoi', 'Thành phố Hà Nội']
    tinh_thanh = None
    for name in tinh_thanh_names:
        tinh_thanh = TinhThanh.objects.filter(tenTinhThanh__icontains=name).first()
        if tinh_thanh:
            break
    
    if not tinh_thanh:
        print("[ERROR] Không tìm thấy tỉnh thành Hà Nội trong database!")
        return
    
    print(f"[OK] Tìm thấy tỉnh thành: {tinh_thanh.tenTinhThanh} (ID: {tinh_thanh.maTinhThanh})")
    print()
    
    imported_count = 0
    updated_count = 0
    error_count = 0
    
    places_data = JSON_DATA.get('danhSachDiaDiem', [])
    
    for place_data in places_data:
        try:
            gia_ve = parse_gia_ve(place_data.get('giaVe', ''))
            gio_dong_cua = extract_gio_dong_cua(place_data.get('gioMoCua', '')) or ''
            loai_dia_diem = map_loai_dia_diem(place_data.get('loaiDiaDiem', ''))
            
            mo_ta = place_data.get('moTa', '')
            dac_diem = place_data.get('dacDiem', '')
            tien_nghi = place_data.get('tienNghi', '')
            
            # Giữ nguyên moTa, không thêm dacDiem và tienNghi vào đây
            mo_ta_full = mo_ta
            
            existing_place = None
            if place_data.get('maDiaDiem'):
                existing_place = DiaDiem.objects.filter(maDiaDiem=place_data['maDiaDiem']).first()
            if not existing_place:
                existing_place = DiaDiem.objects.filter(tenDiaDiem__iexact=place_data['tenDiaDiem']).first()
            
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
                'dienThoai': place_data.get('dienThoai') or '',
                'website': place_data.get('website') or '',
                'danhGiaTrungBinh': place_data.get('danhGiaTrungBinh', 0.0),
                'dacDiem': dac_diem or '',
                'tienNghi': tien_nghi or '',
                'trangThai': 'active',
            }
            
            if existing_place:
                for key, value in place_dict.items():
                    setattr(existing_place, key, value)
                existing_place.save()
                updated_count += 1
                print(f"[UPDATE] {place_data['tenDiaDiem']} (ID: {existing_place.maDiaDiem})")
            else:
                new_place = DiaDiem.objects.create(**place_dict)
                imported_count += 1
                print(f"[CREATE] {place_data['tenDiaDiem']} (ID: {new_place.maDiaDiem})")
                
        except Exception as e:
            error_count += 1
            print(f"[ERROR] {place_data.get('tenDiaDiem', 'Unknown')}: {e}")
    
    print("\n" + "="*60)
    print(f"KẾT QUẢ: Tạo mới {imported_count}, Cập nhật {updated_count}, Lỗi {error_count}")
    print(f"Tổng số địa điểm: {DiaDiem.objects.count()}")
    print("="*60)

if __name__ == '__main__':
    print("="*60)
    print("IMPORT 30 ĐỊA ĐIỂM HÀ NỘI VÀO BẢNG DIADIEM")
    print("="*60)
    print()
    
    # JSON data được embed trực tiếp trong script
    # Nếu cần, có thể load từ file external
    if not JSON_DATA.get('danhSachDiaDiem'):
        print("[ERROR] JSON_DATA chưa được khởi tạo!")
        print("Vui lòng thêm dữ liệu JSON vào biến JSON_DATA trong script.")
        sys.exit(1)
    
    import_places()
    
    print("\n[OK] Hoàn thành!")
