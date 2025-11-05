# 🔧 FIX LANGSMITH PROJECT ACCESS ISSUE

## ❌ Lỗi

```
Can't access tracing projects. Contact your administrator to give you the project:read access
```

## 🔍 Nguyên Nhân

Lỗi này xảy ra khi:
1. **Project name không tồn tại** trong LangSmith account của bạn
2. **API key không có quyền** truy cập project cụ thể
3. **Project name được set** nhưng project chưa được tạo trên LangSmith

## ✅ Giải Pháp

### Option 1: Để LangSmith Tự Động Tạo Project (Khuyến nghị)

**Đã được fix tự động!**

1. **Xóa LANGCHAIN_PROJECT từ .env**:
   ```bash
   python remove_project_name.py
   ```

2. **LangSmith sẽ tự động tạo project mới** khi chạy workflow lần đầu

3. **Xem project trên dashboard**:
   - Truy cập: https://smith.langchain.com/
   - Project sẽ được tạo tự động với tên ngẫu nhiên
   - Hoặc bạn có thể đổi tên project sau

### Option 2: Tạo Project Mới Trên LangSmith Dashboard

1. **Truy cập LangSmith Dashboard**:
   ```
   https://smith.langchain.com/
   ```

2. **Tạo project mới**:
   - Vào **Projects** → **Create New Project**
   - Đặt tên project (ví dụ: `vi-vu-dev` hoặc `travel-planner`)
   - Copy tên project

3. **Set project name vào .env**:
   ```bash
   # Thêm vào file .env:
   LANGCHAIN_PROJECT=your-project-name-here
   ```

### Option 3: Kiểm Tra API Key Permissions

1. **Vào Settings**:
   ```
   https://smith.langchain.com/settings
   ```

2. **Kiểm tra API Key**:
   - Vào **API Keys** section
   - Đảm bảo API key có quyền:
     - `project:read`
     - `project:write`
     - `run:read`
     - `run:write`

3. **Nếu không có quyền**:
   - Tạo API key mới với đầy đủ quyền
   - Hoặc liên hệ administrator để cấp quyền

## 📝 Các Thay Đổi Đã Thực Hiện

### 1. Updated `config/langsmith_config.py`

- **Project name chỉ được set nếu có trong .env**
- **Nếu không có, LangSmith sẽ tự động tạo project**
- **`get_runnable_config()` chỉ thêm project vào metadata nếu có**

### 2. Created `remove_project_name.py`

- Script để xóa `LANGCHAIN_PROJECT` từ .env
- Cho phép LangSmith tự động tạo project

### 3. Created `fix_langsmith_access.py`

- Interactive script để fix project access issue
- Hướng dẫn các options khác nhau

## 🧪 Test

Sau khi fix, chạy test:

```bash
# 1. Xóa project name (nếu cần)
python remove_project_name.py

# 2. Kiểm tra config
python check_tracing.py

# 3. Test workflow
python test_with_langsmith.py
```

## ✅ Kết Quả Mong Đợi

Sau khi fix:
- ✅ LangSmith sẽ tự động tạo project mới
- ✅ Không còn lỗi "Can't access tracing projects"
- ✅ Traces sẽ được gửi lên LangSmith thành công
- ✅ Có thể xem traces trên dashboard

## 💡 Lưu Ý

1. **Nếu vẫn gặp lỗi**:
   - Kiểm tra API key có đúng không
   - Kiểm tra API key có đủ quyền không
   - Thử tạo project mới trên dashboard trước

2. **Best Practice**:
   - Để LangSmith tự động tạo project cho development
   - Chỉ set project name cụ thể khi cần production

3. **Xem Traces**:
   - Sau khi workflow chạy, vào dashboard
   - Project sẽ được tạo tự động hoặc dùng project đã set
   - Xem runs mới nhất để thấy traces

---

**Status**: ✅ Đã fix
**Date**: 2025-11-05

