param(
    [int]$Port = 8000
)

$projectRoot = 'd:\KLTN\MAS (1)\MAS\TRAVEL_PLANNER'
$backendDir  = Join-Path $projectRoot 'vivu_backend'

Write-Host 'Checking Redis in WSL...'
# Trả về '1' nếu redis-server đang chạy, '0' nếu chưa
$redisRunning = $null
try {
    $redisRunning = wsl -e sh -lc "pgrep redis-server >/dev/null 2>&1 && echo 1 || echo 0" 2>$null
} catch {
    Write-Host 'WSL command failed while checking Redis. Skipping Redis auto-start.'
}

if (-not $redisRunning) {
    Write-Host 'WSL/bash not available or returned no output. You may need to start Redis manually in Ubuntu.'
} elseif ($redisRunning.Trim() -ne '1') {
    Write-Host 'Redis is not running. Starting Redis in WSL...'
    # Lặp lại đúng flow bạn đang dùng: cd tới thư mục rồi chạy redis-server ở background
    wsl -e sh -lc "cd /mnt/c/redis-6.2.14/redis-6.2.14 && nohup redis-server >/dev/null 2>&1 &" 2>$null
    Start-Sleep -Seconds 2
} else {
    Write-Host 'Redis already running.'
}
$venvActivate = Join-Path $projectRoot '.venv\Scripts\Activate.ps1'
if (Test-Path $venvActivate) {
    Write-Host 'Activating virtual environment...'
    & $venvActivate
} else {
    Write-Host 'Virtual environment not found at' $venvActivate
}

$requirementsFile = Join-Path $projectRoot 'requirements.txt'
if (Test-Path $requirementsFile) {
    Write-Host 'Installing Python dependencies from requirements.txt...'
    pip install -r $requirementsFile
}

Write-Host 'Starting Django dev server...'
Set-Location $backendDir
python manage.py runserver 0.0.0.0:$Port
