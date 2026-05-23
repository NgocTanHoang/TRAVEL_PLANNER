# Hướng dẫn cào dữ liệu từ Cơ sở dữ liệu du lịch Việt Nam

## Tổng quan

Script `scrape_vietnam_tourism_db.py` được thiết kế để cào toàn bộ dữ liệu từ website https://csdl.vietnamtourism.gov.vn/

## Thông tin danh mục

- **Cơ sở lưu trú (cslt)**: 14,327 kết quả (~955 trang)
- Mỗi trang có 15 items
- Mỗi item có link chi tiết: `/cslt/?item=XXX`

## Cách sử dụng

### Chạy script cào dữ liệu

```bash
cd TRAVEL_PLANNER
python vivu_backend/scripts/scrape_vietnam_tourism_db.py
```

### Chạy ở background (Windows PowerShell)

```powershell
cd TRAVEL_PLANNER
python vivu_backend/scripts/scrape_vietnam_tourism_db.py > scrape_log.txt 2>&1
```

### Kiểm tra tiến trình

```bash
# Xem log
tail -f scrape_log.txt

# Hoặc trên Windows
Get-Content scrape_log.txt -Wait -Tail 50
```

## Tính năng

1. **Cào danh sách**: Lấy thông tin cơ bản từ trang danh sách
2. **Cào chi tiết**: Tự động cào trang chi tiết của mỗi item để lấy thông tin đầy đủ
3. **Lưu database**: Tự động lưu vào database Django
4. **Tránh duplicate**: Sử dụng item_id để tracking
5. **Error handling**: Xử lý lỗi và tiếp tục cào

## Cấu trúc dữ liệu

Mỗi item sẽ có:
- `tenDiaDiem`: Tên địa điểm
- `diaChi`: Địa chỉ
- `dienThoai`: Điện thoại
- `email`: Email
- `website`: Website
- `moTa`: Mô tả (từ trang chi tiết)
- `item_id`: ID từ source
- `detail_url`: URL trang chi tiết

## Lưu ý

- Script có delay 0.5s giữa các request detail page để tránh bị block
- Script có delay 2s giữa các trang danh sách
- Với 14,327 items, thời gian ước tính: ~2-3 giờ
- Script tự động lưu dữ liệu sau mỗi trang để tránh mất dữ liệu nếu bị gián đoạn

## Troubleshooting

### Script bị dừng giữa chừng

Script sẽ tự động lưu dữ liệu đã cào được. Bạn có thể chạy lại script, nó sẽ tiếp tục từ đầu (có thể có duplicate, nhưng sẽ được xử lý bởi `update_or_create`).

### Lỗi NOT NULL constraint

Đã được xử lý bằng cách set giá trị mặc định cho các trường bắt buộc.

### Lỗi kết nối

Script có retry logic và sẽ tiếp tục với trang tiếp theo nếu một trang bị lỗi.



