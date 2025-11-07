# Script để chạy Redis server trên Windows
# Chạy: powershell -ExecutionPolicy Bypass -File start_redis.ps1

$redisPath = ""

# Tìm Redis binary
$possiblePaths = @(
    "C:\Program Files\Redis\redis-server.exe",
    "C:\redis\redis-server.exe",
    "$env:USERPROFILE\redis\redis-server.exe",
    "D:\KLTN\MAS (1)\MAS\redis-8.0.0\redis-server.exe"
)

foreach ($path in $possiblePaths) {
    if (Test-Path $path) {
        $redisPath = $path
        break
    }
}

if (-not $redisPath) {
    Write-Host "❌ Không tìm thấy redis-server.exe" -ForegroundColor Red
    Write-Host "Vui lòng cài đặt Redis trước" -ForegroundColor Yellow
    Write-Host "Xem hướng dẫn trong setup_redis_windows.ps1" -ForegroundColor Yellow
    exit 1
}

# Kiểm tra Redis đã chạy chưa
$redisProcess = Get-Process -Name "redis-server" -ErrorAction SilentlyContinue
if ($redisProcess) {
    Write-Host "✅ Redis đã đang chạy (PID: $($redisProcess.Id))" -ForegroundColor Green
    Write-Host "Kết nối tại: localhost:6379" -ForegroundColor Green
    exit 0
}

Write-Host "🚀 Đang khởi động Redis server..." -ForegroundColor Cyan
Write-Host "Redis path: $redisPath" -ForegroundColor Gray
Write-Host ""

# Chạy Redis
try {
    Start-Process -FilePath $redisPath -WindowStyle Normal
    Write-Host "✅ Redis đã được khởi động!" -ForegroundColor Green
    Write-Host "Kết nối tại: localhost:6379" -ForegroundColor Green
    Write-Host ""
    Write-Host "Để dừng Redis, đóng cửa sổ Redis hoặc chạy: stop_redis.ps1" -ForegroundColor Yellow
} catch {
    Write-Host "❌ Lỗi khi khởi động Redis: $_" -ForegroundColor Red
    exit 1
}

