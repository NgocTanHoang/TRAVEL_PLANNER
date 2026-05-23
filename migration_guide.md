# Migration Guide

## Mục tiêu

Hướng dẫn này giúp tạo migration ban đầu cho app `users`, kiểm tra trạng thái migration, và áp dụng migration cho `analytics` an toàn trên môi trường local đã có sẵn dữ liệu.

## 1. Đi tới đúng thư mục backend

```powershell
cd D:\cv\project\TRAVEL_PLANNER\vivu_backend
```

## 2. Tạo migration ban đầu cho app `users` nếu chưa có

Kiểm tra nhanh trước:

```powershell
Get-ChildItem .\apps\users\migrations
```

Nếu thư mục `migrations` chưa tồn tại hoặc chưa có `0001_initial.py`, tạo thư mục và file migration:

```powershell
New-Item -ItemType Directory -Force .\apps\users\migrations
New-Item -ItemType File -Force .\apps\users\migrations\__init__.py
py -3.11 manage.py makemigrations users
```

## 3. Kiểm tra toàn bộ trạng thái migration

```powershell
py -3.11 manage.py showmigrations users places itineraries analytics
```

## 4. Kiểm tra database local đã có bảng người dùng hay chưa

Nếu database local đã tồn tại từ trước, cần kiểm tra bảng `NGUOIDUNG`:

```powershell
py -3.11 manage.py shell -c "from django.db import connection; print(connection.introspection.table_names())"
```

Nếu bạn thấy bảng `NGUOIDUNG` đã tồn tại nhưng Django chưa đánh dấu migration `users` là applied, dùng `--fake` để đồng bộ lịch sử migration mà không tạo lại bảng:

```powershell
py -3.11 manage.py migrate users 0001 --fake
```

Sau đó kiểm tra lại:

```powershell
py -3.11 manage.py showmigrations users
```

Kỳ vọng:

```text
users
 [X] 0001_initial
```

## 5. Tạo hoặc rà lại migration cho `analytics`

Nếu file migration cho `analytics` đã có sẵn, chỉ cần kiểm tra:

```powershell
Get-ChildItem .\apps\analytics\migrations
```

Nếu chưa có:

```powershell
py -3.11 manage.py makemigrations analytics
```

## 6. Áp dụng migration cho `analytics`

Chỉ chạy sau khi `users` đã được đánh dấu đúng trạng thái:

```powershell
py -3.11 manage.py migrate analytics
```

Hoặc migrate toàn bộ phần liên quan:

```powershell
py -3.11 manage.py migrate
```

## 7. Kiểm tra lại bảng analytics đã được tạo

```powershell
py -3.11 manage.py showmigrations analytics
py -3.11 manage.py shell -c "from apps.analytics.models import YeuCauLoTrinh; print(YeuCauLoTrinh._meta.db_table)"
```

## 8. Nếu local DB cũ có schema lệch

Khi local DB đã có bảng thật nhưng migration history chưa khớp:

1. Tuyệt đối không xóa DB ngay.
2. Dùng `showmigrations` để xác định app nào chưa được đánh dấu.
3. Dùng `migrate <app> <migration> --fake` cho đúng migration đầu tiên của app đó.
4. Chỉ sau khi history khớp mới chạy `migrate analytics`.

Ví dụ an toàn:

```powershell
py -3.11 manage.py migrate users 0001 --fake
py -3.11 manage.py migrate analytics
```

## 9. Kiểm tra nhanh sau migrate

```powershell
py -3.11 manage.py check
py -3.11 -m py_compile .\apps\analytics\models.py .\apps\analytics\services.py .\apps\api\travel_plan_views.py .\apps\api\travel_plan_step_views.py
```
