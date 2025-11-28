# Amadeus API - Tổng quan và Hướng dẫn

## 1. Giới thiệu về Amadeus API

Amadeus là một trong những nhà cung cấp GDS (Global Distribution System) hàng đầu thế giới, cung cấp các API mạnh mẽ cho ngành du lịch. Amadeus API cho phép tích hợp các dịch vụ:
- **Đặt vé máy bay** (Flight Booking)
- **Tìm kiếm và đặt khách sạn** (Hotel Search & Booking)
- **Thuê xe** (Car Rental)
- **Trải nghiệm điểm đến** (Destination Experiences)
- **Thông tin thị trường** (Market Insights)
- **Quản lý hành trình** (Trip Management)

## 2. Hai loại API chính

### 2.1. Self-Service APIs
- **Đối tượng**: Nhà phát triển độc lập, startup, công ty nhỏ
- **Ưu điểm**:
  - Bắt đầu nhanh chóng (chưa đầy 3 phút)
  - REST API với JSON format
  - Thanh toán theo mức sử dụng (pay-as-you-go)
  - Có môi trường test miễn phí
  - Tài liệu đầy đủ, SDK hỗ trợ nhiều ngôn ngữ
- **Ngôn ngữ hỗ trợ**: Ruby, Python, Java, Node.js, .NET, Kotlin (Android), Swift (iOS)
- **Link**: https://developers.amadeus.com/self-service/

### 2.2. Enterprise APIs
- **Đối tượng**: Công ty lớn, thương hiệu hàng đầu
- **Ưu điểm**:
  - Truy cập toàn bộ danh mục API
  - Hỗ trợ chuyên dụng từ Account Manager
  - Mô hình giá tùy chỉnh
  - Không giới hạn số lượng cuộc gọi (trong môi trường production)
- **Yêu cầu**: Phải đăng ký và được phê duyệt

## 3. Các API chính trong Self-Service

### 3.1. Flight APIs
- **Flight Inspiration Search**: Tìm kiếm chuyến bay với ngân sách cụ thể
- **Flight Cheapest Date Search**: Tìm ngày bay rẻ nhất
- **Flight Offers Search**: Tìm kiếm chặt chẽ theo tiêu chí
- **Flight Offers Price**: Lấy giá chính xác và đặt chỗ
- **Flight Create Orders**: Đặt vé máy bay
- **Flight Seatmap Display**: Hiển thị sơ đồ ghế ngồi
- **Airport & City Search**: Tìm kiếm sân bay và thành phố

### 3.2. Hotel APIs
- **Hotel Search**: Tìm kiếm khách sạn
- **Hotel Offers Search**: Tìm kiếm ưu đãi khách sạn
- **Hotel Offers by Hotel**: Lấy ưu đãi theo ID khách sạn
- **Hotel Booking**: Đặt phòng khách sạn

### 3.3. Car Rental APIs
- **Car Rental Search**: Tìm kiếm xe cho thuê
- **Car Rental Offers**: Lấy thông tin chi tiết về xe

### 3.4. Destination Content APIs
- **Points of Interest**: Điểm tham quan
- **Safety Rated Locations**: Đánh giá an toàn địa điểm
- **Tourist Activities**: Hoạt động du lịch

## 4. So sánh với các API hiện tại trong dự án

### 4.1. API hiện tại đang sử dụng

| API | Mục đích | Ưu điểm | Nhược điểm |
|-----|----------|---------|------------|
| **SerpAPI** | Google Flights, Google Hotels | Dữ liệu từ Google (chính xác), dễ tích hợp | Phí cao, giới hạn quota |
| **Travelpayouts** | Flights, Hotels | Miễn phí, affiliate links | Dữ liệu không chi tiết, không thể đặt trực tiếp |
| **FlightAPI** | Flights | Miễn phí (30 lượt/tháng) | Giới hạn nghiêm ngặt |

### 4.2. So sánh với Amadeus API

| Tiêu chí | Amadeus API | SerpAPI | Travelpayouts |
|----------|-------------|---------|---------------|
| **Độ chính xác** | ⭐⭐⭐⭐⭐ (Dữ liệu GDS chính thức) | ⭐⭐⭐⭐ (Từ Google) | ⭐⭐⭐ (Ước tính) |
| **Khả năng đặt chỗ** | ✅ Có (Flight & Hotel) | ❌ Không | ❌ Chỉ affiliate |
| **Chi phí** | 💰 Pay-as-you-go | 💰💰💰 Đắt | ✅ Miễn phí |
| **Quota** | Không giới hạn (production) | Giới hạn theo gói | Giới hạn |
| **Tốc độ** | ⚡⚡⚡ Nhanh | ⚡⚡ Trung bình | ⚡⚡ Trung bình |
| **Dữ liệu** | Đầy đủ, chi tiết | Đầy đủ | Hạn chế |
| **Hỗ trợ** | ✅ Tốt (Enterprise) | ⚠️ Email | ⚠️ Hạn chế |

## 5. Khi nào nên sử dụng Amadeus API?

### ✅ Nên sử dụng khi:
- Cần **đặt chỗ trực tiếp** (booking) trong ứng dụng
- Cần dữ liệu **chính xác và đầy đủ** từ GDS
- Ứng dụng có **lưu lượng lớn** (production)
- Cần **hỗ trợ chuyên nghiệp** và tùy chỉnh
- Muốn tích hợp **nhiều dịch vụ** (flight + hotel + car) trong một nền tảng

### ❌ Không nên sử dụng khi:
- Chỉ cần **tìm kiếm** (không cần đặt chỗ)
- Dự án **nhỏ**, **prototype**, hoặc **demo**
- Ngân sách **hạn chế** (SerpAPI có thể rẻ hơn cho use case đơn giản)
- Chỉ cần **affiliate links** (Travelpayouts đủ)

## 6. Cách bắt đầu với Amadeus API

### Bước 1: Đăng ký tài khoản
1. Truy cập: https://developers.amadeus.com/
2. Tạo tài khoản miễn phí
3. Xác nhận email

### Bước 2: Tạo App và lấy API Keys
1. Vào **My Self-Service** → **Create New App**
2. Chọn loại API cần sử dụng (Flight, Hotel, etc.)
3. Lấy **API Key** và **API Secret**

### Bước 3: Lấy Access Token
```python
import requests

# Lấy access token
url = "https://test.api.amadeus.com/v1/security/oauth2/token"
headers = {
    "Content-Type": "application/x-www-form-urlencoded"
}
data = {
    "grant_type": "client_credentials",
    "client_id": "YOUR_API_KEY",
    "client_secret": "YOUR_API_SECRET"
}

response = requests.post(url, headers=headers, data=data)
token = response.json()["access_token"]
```

### Bước 4: Sử dụng API
```python
# Ví dụ: Tìm kiếm chuyến bay
url = "https://test.api.amadeus.com/v2/shopping/flight-offers"
headers = {
    "Authorization": f"Bearer {token}"
}
params = {
    "originLocationCode": "SGN",
    "destinationLocationCode": "HAN",
    "departureDate": "2025-12-01",
    "adults": 1
}

response = requests.get(url, headers=headers, params=params)
flights = response.json()
```

## 7. SDK hỗ trợ

Amadeus cung cấp SDK cho nhiều ngôn ngữ:

### Python
```bash
pip install amadeus
```

```python
from amadeus import Client, ResponseError

amadeus = Client(
    client_id='YOUR_API_KEY',
    client_secret='YOUR_API_SECRET'
)

try:
    response = amadeus.shopping.flight_offers_search.get(
        originLocationCode='SGN',
        destinationLocationCode='HAN',
        departureDate='2025-12-01',
        adults=1
    )
    print(response.data)
except ResponseError as error:
    print(error)
```

### Node.js
```bash
npm install amadeus
```

```javascript
const Amadeus = require('amadeus');

const amadeus = new Amadeus({
  clientId: 'YOUR_API_KEY',
  clientSecret: 'YOUR_API_SECRET'
});

amadeus.shopping.flightOffersSearch.get({
  originLocationCode: 'SGN',
  destinationLocationCode: 'HAN',
  departureDate: '2025-12-01',
  adults: 1
}).then(response => {
  console.log(response.data);
}).catch(error => {
  console.error(error);
});
```

## 8. Pricing (Self-Service)

Amadeus Self-Service sử dụng mô hình **pay-as-you-go**:
- **Test Environment**: Miễn phí (với giới hạn)
- **Production**: Thanh toán theo số lượng API calls
- Giá cụ thể: Xem tại https://developers.amadeus.com/pricing

## 9. Tích hợp vào dự án hiện tại

### 9.1. Tạo file `tools/amadeus_tools.py`

```python
import os
import logging
from typing import Dict, List, Optional, Any
from amadeus import Client, ResponseError

logger = logging.getLogger(__name__)

class AmadeusTools:
    """Công cụ sử dụng Amadeus API"""
    
    def __init__(self):
        self.api_key = os.getenv('AMADEUS_API_KEY', '')
        self.api_secret = os.getenv('AMADEUS_API_SECRET', '')
        
        if not self.api_key or not self.api_secret:
            logger.warning("Amadeus API credentials not set")
            self.client = None
        else:
            self.client = Client(
                client_id=self.api_key,
                client_secret=self.api_secret
            )
    
    def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str] = None,
        adults: int = 1,
        children: int = 0,
        infants: int = 0
    ) -> Dict[str, Any]:
        """Tìm kiếm chuyến bay"""
        if not self.client:
            return {'error': 'Amadeus API not configured', 'flights': []}
        
        try:
            params = {
                'originLocationCode': origin,
                'destinationLocationCode': destination,
                'departureDate': departure_date,
                'adults': adults
            }
            
            if return_date:
                params['returnDate'] = return_date
            
            if children > 0:
                params['children'] = children
            
            if infants > 0:
                params['infants'] = infants
            
            response = self.client.shopping.flight_offers_search.get(**params)
            
            return {
                'status': 'success',
                'flights': response.data,
                'source': 'amadeus'
            }
        except ResponseError as error:
            logger.error(f"Amadeus API error: {error}")
            return {'error': str(error), 'flights': []}
    
    def search_hotels(
        self,
        city_code: str,
        check_in: str,
        check_out: str,
        adults: int = 2
    ) -> Dict[str, Any]:
        """Tìm kiếm khách sạn"""
        if not self.client:
            return {'error': 'Amadeus API not configured', 'hotels': []}
        
        try:
            # Bước 1: Tìm hotel IDs
            hotel_ids_response = self.client.reference_data.locations.hotels.by_city.get(
                cityCode=city_code
            )
            
            hotel_ids = [hotel['hotelId'] for hotel in hotel_ids_response.data[:10]]
            
            # Bước 2: Tìm offers
            offers_response = self.client.shopping.hotel_offers_search.get(
                hotelIds=','.join(hotel_ids),
                checkInDate=check_in,
                checkOutDate=check_out,
                adults=adults
            )
            
            return {
                'status': 'success',
                'hotels': offers_response.data,
                'source': 'amadeus'
            }
        except ResponseError as error:
            logger.error(f"Amadeus API error: {error}")
            return {'error': str(error), 'hotels': []}
```

### 9.2. Cập nhật `flight_tools.py` để ưu tiên Amadeus

```python
# Thêm vào FlightTools.__init__
self.amadeus = AmadeusTools() if AMADEUS_AVAILABLE else None

# Trong search_flight_prices, thêm Amadeus làm ưu tiên đầu tiên
if self.amadeus and self.amadeus.client:
    amadeus_result = self.amadeus.search_flights(...)
    if amadeus_result.get('flights'):
        return self._format_amadeus_result(amadeus_result)
```

## 10. Tài liệu tham khảo

- **Trang chủ**: https://developers.amadeus.com/
- **Tài liệu API**: https://developers.amadeus.com/self-service/apis-docs
- **GitHub SDKs**: https://github.com/amadeus4dev
- **Hướng dẫn**: https://developers.amadeus.com/self-service/apis-docs/guides/developer-guides
- **Pricing**: https://developers.amadeus.com/pricing

## 11. Kết luận

Amadeus API là một giải pháp mạnh mẽ và chuyên nghiệp cho các ứng dụng du lịch cần:
- Đặt chỗ trực tiếp
- Dữ liệu chính xác từ GDS
- Hỗ trợ đầy đủ các dịch vụ du lịch

Tuy nhiên, với dự án hiện tại (chủ yếu là tìm kiếm và đề xuất lịch trình), việc sử dụng SerpAPI và Travelpayouts có thể đủ và tiết kiệm chi phí hơn.

**Khuyến nghị**: 
- Nếu chỉ cần **tìm kiếm và đề xuất** → Giữ nguyên SerpAPI + Travelpayouts
- Nếu cần **tính năng đặt chỗ** → Xem xét tích hợp Amadeus API
- Nếu dự án **mở rộng quy mô lớn** → Nên chuyển sang Amadeus Enterprise





