#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script để chạy test và lưu output với UTF-8 encoding đúng cách
"""
import subprocess
import sys
from pathlib import Path

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
    if sys.stderr.encoding != 'utf-8':
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)

def run_test_and_save():
    """Chạy test script và lưu output với UTF-8"""
    script_path = Path(__file__).parent.parent / 'scripts' / 'test_travel_cost.py'
    output_path = Path(__file__).parent.parent / 'test_output.txt'
    
    print("Đang chạy test script...")
    
    # Chạy script và capture output
    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace'
    )
    
    # Combine stdout and stderr
    output = result.stdout + result.stderr
    
    # Ghi file với UTF-8 (không có BOM)
    with open(output_path, 'w', encoding='utf-8', errors='replace', newline='\n') as f:
        f.write(output)
    
    print(f"✅ Đã lưu kết quả vào {output_path} với encoding UTF-8")
    print(f"📊 Tổng số dòng: {len(output.splitlines())}")
    
    if result.returncode != 0:
        print(f"⚠️  Script trả về exit code: {result.returncode}")
    
    return result.returncode

if __name__ == '__main__':
    exit_code = run_test_and_save()
    sys.exit(exit_code)

