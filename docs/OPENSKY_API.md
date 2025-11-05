"""
OpenSky Network API Integration Guide
======================================

Tài liệu: https://openskynetwork.github.io/opensky-api/rest.html

1. ĐĂNG KÝ TÀI KHOẢN
--------------------
- Truy cập: https://opensky-network.org/
- Đăng ký tài khoản miễn phí
- Sau khi đăng ký, bạn có thể:
  a) Sử dụng username/password (Basic Auth)
  b) Tạo API client để lấy client_id và client_secret (OAuth2 - Recommended)

2. PHƯƠNG THỨC XÁC THỰC
-----------------------
Có 2 phương thức:

a) OAuth2 Client Credentials Flow (Khuyến nghị):
   - Tạo API client trong dashboard
   - Nhận client_id và client_secret
   - Token được tự động refresh khi cần
   
b) HTTP Basic Auth (Fallback):
   - Sử dụng username và password trực tiếp
   - Đơn giản hơn nhưng ít bảo mật hơn

3. THÊM CREDENTIALS VÀO .ENV
------------------------------
Cách 1: OAuth2 (Khuyến nghị)
```
OPENSKY_CLIENT_ID=your_client_id
OPENSKY_CLIENT_SECRET=your_client_secret
```

Cách 2: Basic Auth
```
OPENSKY_USERNAME=your_username
OPENSKY_PASSWORD=your_password
```

Lưu ý: Có thể dùng cả hai, OAuth2 sẽ được ưu tiên.

4. CÁC ENDPOINTS CHÍNH
-----------------------
a) Lấy chuyến bay từ/sẽ đến sân bay:
   - Departures: `/flights/departure?airport=VVNB&begin=<timestamp>&end=<timestamp>`
   - Arrivals: `/flights/arrival?airport=VVNB&begin=<timestamp>&end=<timestamp>`
   - Giới hạn: Khoảng thời gian không quá 2 ngày

b) Lấy tất cả chuyến bay trong khoảng thời gian:
   - `/flights/all?begin=<timestamp>&end=<timestamp>`
   - Giới hạn: Khoảng thời gian không quá 2 giờ

c) Lấy chuyến bay của một máy bay cụ thể:
   - `/flights/aircraft?icao24=<hex>&begin=<timestamp>&end=<timestamp>`
   - Giới hạn: Khoảng thời gian không quá 2 ngày

d) Lấy trajectory (quỹ đạo) của máy bay:
   - `/tracks?icao24=<hex>&time=<timestamp>`
   - time=0: Lấy live track

e) Lấy state vectors (thông tin real-time):
   - `/states/all` - Tất cả máy bay
   - `/states/own` - Chỉ máy bay của bạn (cần auth)

5. MÃ SÂN BAY VIỆT NAM (ICAO)
------------------------------
- VVNB: Sân bay Nội Bài (Hà Nội)
- VVTS: Sân bay Tân Sơn Nhất (TP.HCM)
- VVDN: Sân bay Đà Nẵng
- VVCA: Sân bay Cần Thơ
- VVCR: Sân bay Cam Ranh (Nha Trang)
- VVPQ: Sân bay Phú Quốc
- VVDL: Sân bay Đà Lạt (Liên Khương)
- VVPC: Sân bay Phù Cát (Quy Nhơn)

6. RATE LIMITS
--------------
- Anonymous users: Rất hạn chế
- OpenSky users: Nhiều lượt hơn (tùy plan)
- Khuyến nghị: Sử dụng caching để giảm số lượt gọi API

7. CÁCH SỬ DỤNG TRONG CODE
---------------------------
```python
from tools.opensky_tools import get_opensky_tools

opensky = get_opensky_tools()

# Lấy departures từ Nội Bài
departures = opensky.get_flights_by_airport(
    'VVNB',
    begin_time=datetime.now() - timedelta(hours=1),
    end_time=datetime.now(),
    flight_type='departure'
)

# Tìm chuyến bay giữa hai sân bay
flights = opensky.search_flights_by_route(
    'VVTS',  # Tân Sơn Nhất
    'VVNB',  # Nội Bài
    begin_time=datetime.now() - timedelta(hours=2),
    end_time=datetime.now()
)
```

8. LƯU Ý
---------
- API này dùng để theo dõi chuyến bay theo thời gian thực
- Không phải để tìm giá vé máy bay
- Dữ liệu historical chỉ có từ ngày hôm trước trở về trước
- Rate limit nghiêm ngặt với anonymous access
- Nên đăng ký tài khoản để có nhiều lượt hơn
- OAuth2 được khuyến nghị vì bảo mật cao hơn và tự động refresh token

