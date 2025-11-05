#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script để tách file index.html thành 3 file riêng:
- HTML (index.html)
- CSS (static/css/index.css)
- JavaScript (static/js/index.js)
"""

import os
import re
from pathlib import Path

# Đường dẫn
BASE_DIR = Path(__file__).resolve().parent.parent
HTML_FILE = BASE_DIR / 'templates' / 'index.html'
CSS_FILE = BASE_DIR / 'static' / 'css' / 'index.css'
JS_FILE = BASE_DIR / 'static' / 'js' / 'index.js'

def split_html_file():
    """Tách file HTML thành CSS và JS riêng"""
    
    # Đọc file HTML
    with open(HTML_FILE, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Tìm và trích xuất CSS (bỏ thẻ <style> và </style>)
    style_match = re.search(r'<style>(.*?)</style>', content, re.DOTALL)
    if not style_match:
        print("❌ Không tìm thấy thẻ <style>")
        return False
    
    css_content = style_match.group(1).strip()
    
    # Tìm và trích xuất JavaScript (script chính có chứa "Navbar scroll")
    # Tìm tất cả các <script>...</script>
    script_matches = list(re.finditer(r'<script>(.*?)</script>', content, re.DOTALL))
    
    # Tìm script chính (có chứa "Navbar scroll")
    main_script = None
    for match in script_matches:
        if 'Navbar scroll' in match.group(1):
            main_script = match
            break
    
    if not main_script:
        print("❌ Không tìm thấy script chính")
        return False
    
    js_content = main_script.group(1).strip()
    
    # Ghi CSS file
    CSS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CSS_FILE, 'w', encoding='utf-8') as f:
        f.write(css_content)
    print(f"✅ Đã tạo CSS file: {CSS_FILE}")
    
    # Ghi JavaScript file
    JS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(JS_FILE, 'w', encoding='utf-8') as f:
        f.write(js_content)
    print(f"✅ Đã tạo JS file: {JS_FILE}")
    
    # Thay thế phần CSS trong HTML
    css_link = '    {% load static %}\n    <link rel="stylesheet" href="{% static \'css/index.css\' %}">'
    content = re.sub(r'<style>.*?</style>', css_link, content, flags=re.DOTALL)
    
    # Thay thế phần JavaScript trong HTML
    js_link = '    <script src="{% static \'js/index.js\' %}"></script>'
    content = re.sub(
        r'<script>.*?Navbar scroll.*?</script>',
        js_link,
        content,
        flags=re.DOTALL
    )
    
    # Ghi HTML file mới
    with open(HTML_FILE, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ Đã cập nhật HTML file: {HTML_FILE}")
    
    return True

if __name__ == '__main__':
    print("🚀 Đang tách file index.html...")
    if split_html_file():
        print("✅ Hoàn thành!")
    else:
        print("❌ Có lỗi xảy ra!")
