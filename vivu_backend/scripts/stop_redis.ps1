# Script để dừng Redis server trên Windows
# Chạy: powershell -ExecutionPolicy Bypass -File stop_redis.ps1

Write-Host "Đang dừng Redis server..." -ForegroundColor Yellow

try {
    $redisProcesses = Get-Process -Name "redis-server" -ErrorAction SilentlyContinue
    if ($redisProcesses) {
        foreach ($process in $redisProcesses) {
            Stop-Process -Id $process.Id -Force
            Write-Host "✅ Đã dừng Redis (PID: $($process.Id))" -ForegroundColor Green
        }
    } else {
        Write-Host "⚠️  Redis không đang chạy" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Lỗi khi dừng Redis: $_" -ForegroundColor Red
}

