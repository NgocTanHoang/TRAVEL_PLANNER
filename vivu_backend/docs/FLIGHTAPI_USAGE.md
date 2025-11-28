# FlightAPI.io - Hướng dẫn sử dụng

## Tổng quan

FlightAPI.io cung cấp API để tìm kiếm giá vé máy bay từ hơn 700 hãng hàng không và OTA (Online Travel Agencies).

**Tài liệu chính thức:** https://docs.flightapi.io/flight-price-api

## API Endpoints

### 1. Oneway Trip API
- **Endpoint:** `https://api.flightapi.io/oneway/{api_key}`
- **Method:** GET
- **Cost:** 2 credits/request

### 2. Round Trip API
- **Endpoint:** `https://api.flightapi.io/roundtrip/{api_key}`
- **Method:** GET
- **Cost:** 2 credits/request

## Parameters

### Bắt buộc:
- `departure_airport_code` (string): Mã IATA sân bay khởi hành (ví dụ: "SGN", "HAN")
- `arrival_airport_code` (string): Mã IATA sân bay đến
- `departure_date` (string): Ngày khởi hành (format: YYYY-MM-DD)
- `number_of_adults` (integer): Số lượng người lớn

### Tùy chọn:
- `return_date` (string): Ngày về (chỉ cho Round Trip API, format: YYYY-MM-DD)
- `number_of_childrens` (integer): Số lượng trẻ em (mặc định: 0)
- `number_of_infants` (integer): Số lượng trẻ sơ sinh (mặc định: 0)
- `cabin_class` (string): Hạng ghế - "Economy", "Business", "First" (mặc định: "Economy")

## Ví dụ Request

### Oneway Trip:
```
GET https://api.flightapi.io/oneway/{api_key}?departure_airport_code=SGN&arrival_airport_code=HUI&departure_date=2025-11-29&number_of_adults=2&cabin_class=Economy
```

### Round Trip:
```
GET https://api.flightapi.io/roundtrip/{api_key}?departure_airport_code=SGN&arrival_airport_code=HUI&departure_date=2025-11-29&return_date=2025-12-02&number_of_adults=2&number_of_childrens=1&cabin_class=Economy
```

## Response Format

API trả về JSON với cấu trúc:
```json
{
  "price": 150.00,
  "currency": "USD",
  "flights": [...],
  ...
}
```

**Lưu ý:** 
- Giá có thể trả về bằng USD hoặc VND tùy theo cấu hình
- Cần kiểm tra `currency` field để xác định đơn vị tiền tệ
- Giá có thể là tổng cho tất cả hành khách hoặc giá 1 người, cần kiểm tra response

## Pricing & Credits

- **Mỗi request thành công:** 2 credits
- **Gói Free:** 30 requests/tháng
- **Caching:** Nên cache kết quả 24 giờ để tiết kiệm credits

## Implementation trong Project

Code được implement trong `tools/flight_tools.py`:
- Method: `_search_via_flightapi()`
- Sử dụng caching với Redis
- Tự động convert USD sang VND nếu cần
- Fallback sang API khác nếu FlightAPI fail

## Cấu hình

Thêm vào `.env`:
```env
FLIGHTAPI_KEY=your_api_key_here
```

## Tham khảo

- [FlightAPI Documentation](https://docs.flightapi.io/flight-price-api)
- [Oneway Trip API](https://docs.flightapi.io/oneway-trip-api)
- [Round Trip API](https://docs.flightapi.io/round-trip-api)

