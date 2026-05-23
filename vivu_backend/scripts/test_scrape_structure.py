#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script test để kiểm tra cấu trúc HTML của trang csdl.vietnamtourism.gov.vn
"""
import requests
from bs4 import BeautifulSoup
import sys

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

BASE_URL = "https://csdl.vietnamtourism.gov.vn/csdt"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
}

def test_page_structure():
    """Test cấu trúc của trang"""
    print("Đang tải trang chủ...")
    try:
        response = requests.get(BASE_URL, headers=HEADERS, timeout=30)
        response.raise_for_status()
        response.encoding = 'utf-8'
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        print("\n" + "="*60)
        print("PHÂN TÍCH CẤU TRÚC TRANG")
        print("="*60)
        
        # Tìm các link danh mục
        print("\n1. Tìm các link danh mục:")
        category_links = soup.find_all('a', href=True)
        categories = []
        for link in category_links:
            href = link.get('href', '')
            text = link.get_text(strip=True)
            if any(keyword in text.lower() for keyword in ['lưu trú', 'nhà hàng', 'điểm đến', 'mua sắm', 'giải trí']):
                categories.append((text, href))
                print(f"  - {text}: {href}")
        
        # Tìm các item kết quả (nếu có)
        print("\n2. Tìm các item kết quả:")
        # Thử các selector phổ biến
        selectors = [
            ('div.item', soup.select('div.item')),
            ('div.result', soup.select('div.result')),
            ('div.card', soup.select('div.card')),
            ('li.item', soup.select('li.item')),
            ('article', soup.find_all('article')),
            ('div[class*="item"]', soup.select('div[class*="item"]')),
            ('div[class*="result"]', soup.select('div[class*="result"]')),
        ]
        
        for selector_name, elements in selectors:
            if elements:
                print(f"  - {selector_name}: {len(elements)} elements")
                if len(elements) > 0:
                    print(f"    Ví dụ HTML (100 ký tự đầu):")
                    print(f"    {str(elements[0])[:100]}...")
        
        # Tìm các thẻ h3, h4 (thường chứa tên)
        print("\n3. Tìm các thẻ heading (h3, h4):")
        headings = soup.find_all(['h3', 'h4'])
        print(f"  - Tìm thấy {len(headings)} headings")
        for i, h in enumerate(headings[:5]):  # Chỉ hiển thị 5 đầu tiên
            print(f"    {i+1}. {h.get_text(strip=True)[:50]}")
        
        # Tìm text chứa "Địa chỉ"
        print("\n4. Tìm các text chứa 'Địa chỉ':")
        address_elements = soup.find_all(string=lambda text: text and 'địa chỉ' in text.lower())
        print(f"  - Tìm thấy {len(address_elements)} elements")
        for i, elem in enumerate(address_elements[:5]):
            parent = elem.parent
            print(f"    {i+1}. {elem.strip()[:50]}")
            print(f"       Parent tag: {parent.name if parent else 'None'}")
            print(f"       Parent class: {parent.get('class') if parent else 'None'}")
        
        # Lưu HTML để phân tích
        output_file = 'test_page_structure.html'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(soup.prettify())
        print(f"\n5. Đã lưu HTML vào: {output_file}")
        
        # Tìm form search hoặc filter
        print("\n6. Tìm form search/filter:")
        forms = soup.find_all('form')
        print(f"  - Tìm thấy {len(forms)} forms")
        for i, form in enumerate(forms):
            print(f"    Form {i+1}: action={form.get('action')}, method={form.get('method')}")
            inputs = form.find_all(['input', 'select'])
            for inp in inputs:
                print(f"      - {inp.name}: name={inp.get('name')}, type={inp.get('type')}")
        
    except Exception as e:
        print(f"Lỗi: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_page_structure()



