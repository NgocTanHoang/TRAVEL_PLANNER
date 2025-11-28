# Script hướng dẫn cài đặt Redis trên Windows
# Chạy: powershell -ExecutionPolicy Bypass -File scripts/install_redis_windows.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "HƯỚNG DẪN CÀI ĐẶT REDIS TRÊN WINDOWS" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Có 3 cách để cài Redis trên Windows:" -ForegroundColor Yellow
Write-Host ""

# Cách 1: Redis binary
Write-Host "CÁCH 1: Tải Redis binary (Khuyến nghị - Đơn giản nhất)" -ForegroundColor Green
Write-Host "─────────────────────────────────────────────────────" -ForegroundColor Gray
Write-Host "1. Tải Redis từ một trong các link sau:" -ForegroundColor White
Write-Host "   - https://github.com/tporadowski/redis/releases" -ForegroundColor Cyan
Write-Host "   - https://github.com/microsoftarchive/redis/releases" -ForegroundColor Cyan
Write-Host ""
Write-Host "2. Tải file .zip (ví dụ: Redis-x64-5.0.14.1.zip)" -ForegroundColor White
Write-Host ""
Write-Host "3. Giải nén vào thư mục (ví dụ: C:\redis)" -ForegroundColor White
Write-Host ""
Write-Host "4. Chạy Redis:" -ForegroundColor White
Write-Host "   cd C:\redis" -ForegroundColor Cyan
Write-Host "   .\redis-server.exe" -ForegroundColor Cyan
Write-Host ""
Write-Host "5. Hoặc sử dụng script tự động:" -ForegroundColor White
Write-Host "   powershell -ExecutionPolicy Bypass -File scripts/start_redis.ps1" -ForegroundColor Cyan
Write-Host ""

# Cách 2: Memurai
Write-Host "CÁCH 2: Memurai (Redis-compatible, chạy như Windows Service)" -ForegroundColor Green
Write-Host "─────────────────────────────────────────────────────────────" -ForegroundColor Gray
Write-Host "1. Tải từ: https://www.memurai.com/get-memurai" -ForegroundColor Cyan
Write-Host "2. Cài đặt (sẽ tự động chạy như Windows Service)" -ForegroundColor White
Write-Host "3. Redis sẽ tự động khởi động khi Windows khởi động" -ForegroundColor White
Write-Host ""

# Cách 3: Docker
Write-Host "CÁCH 3: Docker (Nếu đã cài Docker Desktop)" -ForegroundColor Green
Write-Host "───────────────────────────────────────────" -ForegroundColor Gray
Write-Host "Chạy lệnh sau trong PowerShell:" -ForegroundColor White
Write-Host "  docker run -d -p 6379:6379 --name redis redis:latest" -ForegroundColor Cyan
Write-Host ""

# Kiểm tra Redis
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "KIỂM TRA SAU KHI CÀI ĐẶT" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Sau khi cài đặt, chạy lệnh sau để kiểm tra:" -ForegroundColor Yellow
Write-Host "  python scripts/test_redis_connection.py" -ForegroundColor Cyan
Write-Host ""
Write-Host "Hoặc test kết nối trực tiếp:" -ForegroundColor Yellow
Write-Host "  redis-cli ping" -ForegroundColor Cyan
Write-Host "  (Kết quả: PONG)" -ForegroundColor Gray
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "LƯU Ý" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "- Redis chạy trên port 6379 (mặc định)" -ForegroundColor White
Write-Host "- Neu port 6379 da duoc su dung, doi port trong .env:" -ForegroundColor White
Write-Host "  REDIS_PORT=6380" -ForegroundColor Cyan
Write-Host "- Redis data se mat khi tat server (tru khi cau hinh persistence)" -ForegroundColor White
Write-Host ""

