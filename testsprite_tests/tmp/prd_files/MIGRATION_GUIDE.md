# Hướng dẫn Migration - Frontend/Backend Separation

## 📋 Tổng quan

Project Vi Vu đã được tách thành 2 phần riêng biệt:
- **Frontend**: `vivu_frontend/` - Templates, CSS, JS, Images
- **Backend**: `vivu_backend/` - Django apps, agents, tools, utils, ml, config

## ✅ Đã hoàn thành

### 1. Tạo cấu trúc mới
- ✅ Tạo thư mục `vivu_frontend/`
- ✅ Tạo subdirectories: `templates/`, `static/css/`, `static/js/`, `static/img/`

### 2. Di chuyển Frontend Files
- ✅ Templates: `vivu_backend/templates/` → `vivu_frontend/templates/`
- ✅ Static files: `vivu_backend/static/` → `vivu_frontend/static/`

### 3. Di chuyển Backend Code
- ✅ `agents/` → `vivu_backend/agents/`
- ✅ `tools/` → `vivu_backend/tools/`
- ✅ `utils/` → `vivu_backend/utils/`
- ✅ `ml/` → `vivu_backend/ml/`
- ✅ `config/` → `vivu_backend/config/`

### 4. Cập nhật Configuration
- ✅ `settings.py`: Cập nhật `TEMPLATES['DIRS']` và `STATICFILES_DIRS`
- ✅ `settings.py`: Thêm `BASE_DIR` vào `sys.path`
- ✅ API views: Cập nhật imports từ `PROJECT_ROOT` → `BACKEND_DIR`

### 5. Tạo __init__.py Files
- ✅ `vivu_backend/agents/__init__.py`
- ✅ `vivu_backend/tools/__init__.py`
- ✅ `vivu_backend/utils/__init__.py`
- ✅ `vivu_backend/ml/__init__.py`
- ✅ `vivu_backend/config/__init__.py`

## 🧪 Testing Checklist

Sau khi migration, cần test các phần sau:

### 1. Server Startup
```bash
cd vivu_backend
python manage.py runserver
```
- [ ] Server khởi động thành công
- [ ] Không có lỗi import
- [ ] Templates load được

### 2. Frontend Pages
- [ ] Home page (`/`) load được
- [ ] Travel plan page (`/travel-plan/`) load được
- [ ] AI chat page (`/ai-chat/`) load được
- [ ] Place search page load được
- [ ] Place detail page load được
- [ ] Admin pages load được

### 3. Static Files
- [ ] CSS files load được (`/static/css/index.css`)
- [ ] JavaScript files load được (`/static/js/index.js`)
- [ ] Images load được (`/static/img/logo.png`)
- [ ] Animations CSS load được (`/static/css/animations.css`)

### 4. API Endpoints
- [ ] Travel plan API hoạt động
- [ ] Chat API hoạt động
- [ ] Place search API hoạt động
- [ ] ML recommendation API hoạt động

### 5. Backend Functions
- [ ] Agents import được
- [ ] Tools import được
- [ ] Utils import được
- [ ] ML modules import được
- [ ] Config import được

## 🚀 Next Steps

### 1. Cleanup (Sau khi verify)
Sau khi đảm bảo mọi thứ hoạt động, có thể xóa các thư mục cũ:
```bash
# ⚠️ CHỈ XÓA SAU KHI ĐÃ VERIFY MỌI THỨ HOẠT ĐỘNG
# rm -rf agents/ tools/ utils/ ml/ config/
```

### 2. Update .gitignore
Đảm bảo `.gitignore` đã bao gồm:
- `vivu_backend/staticfiles/`
- `vivu_backend/__pycache__/`
- `vivu_backend/*.pyc`

### 3. Update Documentation
- [ ] Cập nhật README.md với cấu trúc mới
- [ ] Cập nhật API documentation nếu cần

## 🔧 Troubleshooting

### Lỗi Import
**Vấn đề**: `ModuleNotFoundError: No module named 'agents'`
**Giải pháp**: 
- Kiểm tra `settings.py` có add `BASE_DIR` vào `sys.path` chưa
- Kiểm tra `__init__.py` files đã được tạo chưa
- Kiểm tra Python path

### Templates không load được
**Vấn đề**: Template không tìm thấy
**Giải pháp**:
- Kiểm tra `TEMPLATES['DIRS']` trong `settings.py`
- Kiểm tra templates đã được copy vào `vivu_frontend/templates/` chưa
- Kiểm tra `APP_DIRS = True` trong settings

### Static files không load được
**Vấn đề**: CSS/JS/Images không load
**Giải pháp**:
- Kiểm tra `STATICFILES_DIRS` trong `settings.py`
- Chạy `python manage.py collectstatic`
- Kiểm tra `STATIC_URL` trong settings
- Kiểm tra WhiteNoise middleware

### Backend modules không import được
**Vấn đề**: `ImportError: cannot import name 'X' from 'agents'`
**Giải pháp**:
- Kiểm tra files đã được copy vào `vivu_backend/agents/` chưa
- Kiểm tra `__init__.py` files
- Kiểm tra Python path trong settings.py

## 📚 Tài liệu tham khảo

- [STRUCTURE.md](./STRUCTURE.md) - Cấu trúc chi tiết của project
- [Django Static Files](https://docs.djangoproject.com/en/5.0/howto/static-files/)
- [Django Templates](https://docs.djangoproject.com/en/5.0/topics/templates/)

## 📝 Notes

- Tất cả imports vẫn hoạt động vì `BASE_DIR` đã được add vào `sys.path`
- Frontend và backend có thể phát triển độc lập
- Có thể dễ dàng deploy frontend và backend riêng biệt trong tương lai

