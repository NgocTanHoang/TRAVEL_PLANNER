# PowerShell script to run test and save with UTF-8 encoding
# Usage: .\scripts\run_test_with_utf8.ps1

# Set console to UTF-8
$PSDefaultParameterValues['*:Encoding'] = 'utf8'
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# Change to script directory
Set-Location $PSScriptRoot\..

# Run the test script and redirect to file with UTF-8
python scripts/test_travel_cost.py 2>&1 | Out-File -FilePath "test_output.txt" -Encoding utf8 -NoNewline

# Read and rewrite with UTF-8 without BOM
$content = Get-Content "test_output.txt" -Raw -Encoding UTF8
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText("test_output.txt", $content, $utf8NoBom)

Write-Host "Da luu ket qua vao test_output.txt voi encoding UTF-8" -ForegroundColor Green

