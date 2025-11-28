#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script cào dữ liệu từ Cơ sở dữ liệu du lịch Việt Nam
URL: https://csdl.vietnamtourism.gov.vn/csdt

Các danh mục:
- Cơ sở lưu trú (khach_san)
- Doanh nghiệp lữ hành
- Hướng dẫn viên
- Nhà hàng (nha_hang)
- Điểm đến (dia_danh)
- Điểm mua sắm (mua_sam)
- Vận tải khách du lịch
- Vui chơi giải trí (giai_tri)
- Thể thao
- Chăm sóc sức khỏe
- Hiệp hội
- Cơ sở đào tạo
- Nhân lực du lịch
- Xúc tiến du lịch
"""
import os
import sys
import django
import re
import time
import json
import requests
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Setup Django
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'vivu_backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vivu_core.settings')
django.setup()

from django.conf import settings
from apps.places.models import DiaDiem, TinhThanh

# Mapping từ URL/slug danh mục sang loaiDiaDiem
CATEGORY_MAPPING = {
    'cslt': 'khach_san',  # Cơ sở lưu trú
    'rest': 'nha_hang',   # Nhà hàng
    'dest': 'dia_danh',   # Điểm đến
    'shop': 'mua_sam',    # Điểm mua sắm
    'vcgt': 'giai_tri',   # Vui chơi giải trí
    'ctyluhanh': 'khac',  # Doanh nghiệp lữ hành
    'huongdanvien': 'khac',  # Hướng dẫn viên
    'vantai': 'khac',     # Vận tải khách du lịch
    'thethao': 'giai_tri',  # Thể thao
    'cssk': 'khac',       # Chăm sóc sức khỏe
    'hiephoi': 'khac',    # Hiệp hội
    'daotao': 'khac',     # Cơ sở đào tạo
    'nhanluc': 'khac',    # Nhân lực du lịch
    'xuctien': 'khac',    # Xúc tiến du lịch
}

# URL mapping cho các danh mục
CATEGORY_URLS = {
    'cslt': '/cslt',           # Cơ sở lưu trú
    'rest': '/rest',           # Nhà hàng
    'dest': '/dest',           # Điểm đến
    'shop': '/shop',           # Điểm mua sắm
    'vcgt': '/vcgt',           # Vui chơi giải trí
    'ctyluhanh': '/ctyluhanh', # Doanh nghiệp lữ hành
    'huongdanvien': '/huongdanvien',  # Hướng dẫn viên
    'vantai': '/vantai',       # Vận tải khách du lịch
    'thethao': '/thethao',     # Thể thao
    'cssk': '/cssk',           # Chăm sóc sức khỏe
    'hiephoi': '/hiephoi',     # Hiệp hội
    'daotao': '/daotao',       # Cơ sở đào tạo
    'nhanluc': '/nhanluc',     # Nhân lực du lịch
    'xuctien': '/xuctien',     # Xúc tiến du lịch
}

BASE_URL = "https://csdl.vietnamtourism.gov.vn"

# Headers để tránh bị block
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
}

def normalize_province_name(name: str) -> Optional[str]:
    """Chuẩn hóa tên tỉnh thành để match với database"""
    # Mapping các tên tỉnh có thể khác nhau
    province_mapping = {
        'Thành phố Hà Nội': 'Hà Nội',
        'Thành phố Hải Phòng': 'Hải Phòng',
        'Thành phố Đà Nẵng': 'Đà Nẵng',
        'Thành phố Hồ Chí Minh': 'Hồ Chí Minh',
        'Thành phố Cần Thơ': 'Cần Thơ',
    }
    
    # Loại bỏ "Thành phố" hoặc "Tỉnh" ở đầu
    name = name.replace('Thành phố ', '').replace('Tỉnh ', '').strip()
    
    # Check mapping
    for key, value in province_mapping.items():
        if name in key or key in name:
            return value
    
    return name

def get_province_from_address(address: str) -> Optional[TinhThanh]:
    """Tìm tỉnh thành từ địa chỉ"""
    if not address:
        return None
    
    # Lấy tên tỉnh từ cuối địa chỉ (thường là format: ..., Tỉnh/TP XXX)
    parts = address.split(',')
    if parts:
        province_name = parts[-1].strip()
        province_name = normalize_province_name(province_name)
        
        try:
            return TinhThanh.objects.get(tenTinhThanh__icontains=province_name)
        except TinhThanh.DoesNotExist:
            # Thử tìm không phân biệt hoa thường
            try:
                return TinhThanh.objects.filter(tenTinhThanh__iexact=province_name).first()
            except:
                pass
    
    return None

def extract_phone(text: str) -> str:
    """Trích xuất số điện thoại từ text"""
    if not text:
        return ""
    
    # Tìm pattern số điện thoại Việt Nam
    phone_pattern = r'(\d{3,4}[\s\.\-]?\d{3,4}[\s\.\-]?\d{3,4})'
    match = re.search(phone_pattern, text)
    if match:
        return re.sub(r'[\s\.\-]', '', match.group(1))
    return ""

def extract_email(text: str) -> str:
    """Trích xuất email từ text"""
    if not text:
        return ""
    
    email_pattern = r'[\w\.-]+@[\w\.-]+\.\w+'
    match = re.search(email_pattern, text)
    if match:
        return match.group(0)
    return ""

def extract_website(text: str) -> str:
    """Trích xuất website từ text"""
    if not text:
        return ""
    
    # Tìm URL
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
    match = re.search(url_pattern, text)
    if match:
        return match.group(0)
    
    # Tìm domain đơn giản
    domain_pattern = r'[a-zA-Z0-9][a-zA-Z0-9-]{1,61}[a-zA-Z0-9]\.[a-zA-Z]{2,}'
    match = re.search(domain_pattern, text)
    if match:
        domain = match.group(0)
        if not domain.startswith('http'):
            return f"https://{domain}"
        return domain
    
    return ""

def parse_place_item(item_html) -> Optional[Dict]:
    """Parse một item địa điểm từ HTML - cấu trúc: cslt-items > verticle-listing-caption"""
    try:
        # Tìm container chứa thông tin
        caption = item_html.find('div', class_='verticle-listing-caption')
        if not caption:
            # Thử tìm trực tiếp trong item
            caption = item_html
        
        # Tìm tên - thường là h3, h4, h5 hoặc strong trong caption
        name = None
        name_elem = (caption.find('h3') or 
                    caption.find('h4') or 
                    caption.find('h5') or
                    caption.find('strong') or
                    caption.find('b') or
                    caption.find('a', class_=re.compile(r'title|name', re.I)))
        
        if name_elem:
            name = name_elem.get_text(strip=True)
        
        if not name:
            return None
        
        # Tìm link chi tiết (href="/cslt/?item=8960")
        detail_link = None
        detail_url = None
        item_id = None
        if name_elem and name_elem.name == 'a':
            detail_link = name_elem.get('href', '')
        elif name_elem:
            # Tìm link trong caption
            link_elem = caption.find('a', href=re.compile(r'item=\d+', re.I))
            if link_elem:
                detail_link = link_elem.get('href', '')
        
        if detail_link:
            detail_url = urljoin(BASE_URL, detail_link)
            # Extract item ID từ URL
            match = re.search(r'item=(\d+)', detail_link)
            if match:
                item_id = match.group(1)
        
        data = {
            'tenDiaDiem': name,
            'diaChi': '',
            'dienThoai': '',
            'email': '',
            'website': '',
            'moTa': '',
            'detail_url': detail_url,
            'item_id': item_id,
        }
        
        # Tìm tất cả các span.d-block chứa thông tin
        info_spans = caption.find_all('span', class_='d-block')
        
        for span in info_spans:
            text = span.get_text(strip=True)
            if not text:
                continue
            
            text_lower = text.lower()
            
            # Địa chỉ
            if 'địa chỉ:' in text_lower:
                address = text.split(':', 1)[1].strip() if ':' in text else text.replace('Địa chỉ', '').strip()
                if address and len(address) > 5:
                    data['diaChi'] = address
            
            # Điện thoại
            elif 'điện thoại' in text_lower or 'phone' in text_lower or 'tel' in text_lower:
                phone = extract_phone(text)
                if phone:
                    data['dienThoai'] = phone
            
            # Email
            elif '@' in text and 'email' in text_lower:
                email = extract_email(text)
                if email:
                    data['email'] = email
            elif '@' in text and not data['email']:
                email = extract_email(text)
                if email:
                    data['email'] = email
            
            # Website
            elif 'website' in text_lower or 'web' in text_lower:
                website = extract_website(text)
                if website:
                    data['website'] = website
            elif ('http' in text_lower or 'www.' in text_lower) and not data['website']:
                website = extract_website(text)
                if website:
                    data['website'] = website
        
        # Nếu không tìm thấy qua span, thử parse từ toàn bộ text
        if not data['diaChi'] or not data['dienThoai']:
            text_content = caption.get_text(separator='\n', strip=True)
            lines = [line.strip() for line in text_content.split('\n') if line.strip()]
            
            for line in lines:
                line_lower = line.lower()
                
                # Địa chỉ
                if not data['diaChi'] and 'địa chỉ:' in line_lower:
                    address = line.split(':', 1)[1].strip() if ':' in line else line.replace('Địa chỉ', '').strip()
                    if address and len(address) > 5:
                        data['diaChi'] = address
                
                # Điện thoại
                elif not data['dienThoai'] and ('điện thoại' in line_lower or 'phone' in line_lower):
                    phone = extract_phone(line)
                    if phone:
                        data['dienThoai'] = phone
                
                # Email
                elif not data['email'] and '@' in line:
                    email = extract_email(line)
                    if email:
                        data['email'] = email
                
                # Website
                elif not data['website'] and ('http' in line_lower or 'www.' in line_lower):
                    website = extract_website(line)
                    if website:
                        data['website'] = website
        
        return data
        
    except Exception as e:
        print(f"  [ERROR] Lỗi parse item: {e}")
        import traceback
        traceback.print_exc()
        return None

def scrape_detail_page(detail_url: str) -> Optional[Dict]:
    """Cào thông tin chi tiết từ trang detail của một item"""
    if not detail_url:
        return None
    
    try:
        response = requests.get(detail_url, headers=HEADERS, timeout=30)
        if response.status_code != 200:
            return None
        
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        
        detail_data = {}
        
        # Tìm tất cả các thông tin chi tiết
        # Có thể có các trường như: mô tả, hình ảnh, đánh giá, v.v.
        
        # Tìm mô tả chi tiết
        description_elem = soup.find('div', class_=re.compile(r'description|mo-ta|content', re.I))
        if not description_elem:
            # Thử tìm trong các div khác
            description_elem = soup.find('div', id=re.compile(r'description|content', re.I))
        
        if description_elem:
            detail_data['moTa'] = description_elem.get_text(separator='\n', strip=True)
        
        # Tìm thông tin bổ sung từ các thẻ span, div chứa thông tin
        info_sections = soup.find_all(['div', 'span', 'p'], class_=re.compile(r'info|detail|field', re.I))
        for section in info_sections:
            text = section.get_text(strip=True)
            text_lower = text.lower()
            
            # Tìm các thông tin bổ sung
            if 'địa chỉ' in text_lower and not detail_data.get('diaChi'):
                detail_data['diaChi'] = text.split(':', 1)[1].strip() if ':' in text else text
            elif 'điện thoại' in text_lower and not detail_data.get('dienThoai'):
                phone = extract_phone(text)
                if phone:
                    detail_data['dienThoai'] = phone
            elif '@' in text and not detail_data.get('email'):
                email = extract_email(text)
                if email:
                    detail_data['email'] = email
            elif ('http' in text_lower or 'www.' in text_lower) and not detail_data.get('website'):
                website = extract_website(text)
                if website:
                    detail_data['website'] = website
        
        # Tìm hình ảnh
        images = []
        img_tags = soup.find_all('img', src=re.compile(r'uploads|images', re.I))
        for img in img_tags[:5]:  # Lấy tối đa 5 hình ảnh
            img_src = img.get('src', '')
            if img_src:
                if not img_src.startswith('http'):
                    img_src = urljoin(BASE_URL, img_src)
                images.append(img_src)
        
        if images:
            detail_data['hinhAnh'] = images
        
        return detail_data if detail_data else None
        
    except Exception as e:
        print(f"  [ERROR] Lỗi cào trang chi tiết {detail_url}: {e}")
        return None

def scrape_category(category_slug: str, category_name: str, max_pages: int = 10000, max_items: int = None) -> List[Dict]:
    """Cào dữ liệu từ một danh mục"""
    print(f"\n{'='*60}")
    print(f"Đang cào danh mục: {category_name} ({category_slug})")
    print(f"{'='*60}")
    
    places = []
    page = 1
    
    # Lấy URL cho danh mục
    category_url = CATEGORY_URLS.get(category_slug, f'/{category_slug}')
    
    while page <= max_pages:
        try:
            # Xây dựng URL với pagination
            if page == 1:
                url = f"{BASE_URL}{category_url}"
            else:
                # Thử nhiều format pagination
                if '?' in category_url:
                    url = f"{BASE_URL}{category_url}&page={page}"
                else:
                    url = f"{BASE_URL}{category_url}?page={page}"
            
            print(f"  [Page {page}] Đang tải: {url}")
            
            response = requests.get(url, headers=HEADERS, timeout=30)
            
            if response.status_code != 200:
                print(f"  [Page {page}] HTTP {response.status_code}, dừng lại")
                break
            
            response.encoding = 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Tìm các item địa điểm - cấu trúc: div.cslt-items hoặc tương tự
            items = []
            
            # Cách 1: Tìm theo class cslt-items (hoặc tương tự cho các danh mục khác)
            item_classes = [
                'cslt-items',      # Cơ sở lưu trú
                'rest-items',      # Nhà hàng
                'dest-items',      # Điểm đến
                'shop-items',      # Điểm mua sắm
                'vcgt-items',      # Vui chơi giải trí
                'items',           # Generic
            ]
            
            for item_class in item_classes:
                items = soup.find_all('div', class_=re.compile(item_class, re.I))
                if items:
                    print(f"  [Page {page}] Tìm thấy {len(items)} items bằng class: {item_class}")
                    break
            
            # Cách 2: Tìm các div có chứa verticle-listing-caption
            if not items:
                captions = soup.find_all('div', class_='verticle-listing-caption')
                if captions:
                    # Lấy parent div chứa caption
                    for caption in captions:
                        parent = caption.find_parent('div', class_=re.compile(r'items|row', re.I))
                        if parent and parent not in items:
                            items.append(parent)
                    if items:
                        print(f"  [Page {page}] Tìm thấy {len(items)} items qua verticle-listing-caption")
            
            # Cách 3: Tìm các div có chứa h3/h4 và span.d-block với "Địa chỉ"
            if not items:
                all_divs = soup.find_all('div', class_=re.compile(r'row|item|card', re.I))
                for div in all_divs:
                    has_heading = div.find(['h3', 'h4', 'h5'])
                    has_address_span = div.find('span', class_='d-block', string=re.compile(r'địa chỉ', re.I))
                    if has_heading and has_address_span:
                        items.append(div)
                
                if items:
                    print(f"  [Page {page}] Tìm thấy {len(items)} items bằng cách tìm theo structure")
            
            if not items:
                print(f"  [Page {page}] Không tìm thấy item nào")
                # Kiểm tra xem có thông báo "không có kết quả" không
                no_result = soup.find(string=re.compile(r'không.*kết quả|không.*dữ liệu|no.*result', re.I))
                if no_result:
                    print(f"  [Page {page}] Không còn dữ liệu")
                    break
                
                # Lưu HTML để debug (chỉ lưu trang đầu tiên)
                if page == 1:
                    debug_file = f'debug_page_{category_slug}_{page}.html'
                    with open(debug_file, 'w', encoding='utf-8') as f:
                        f.write(soup.prettify())
                    print(f"  [DEBUG] Đã lưu HTML vào: {debug_file}")
                break
            
            print(f"  [Page {page}] Tìm thấy {len(items)} items")
            
            page_places = []
            for idx, item in enumerate(items, 1):
                place_data = parse_place_item(item)
                if place_data and place_data.get('tenDiaDiem'):
                    place_data['category'] = category_slug
                    
                    # Cào thông tin chi tiết từ trang detail
                    if place_data.get('detail_url'):
                        detail_data = scrape_detail_page(place_data['detail_url'])
                        if detail_data:
                            # Merge thông tin chi tiết vào place_data
                            for key, value in detail_data.items():
                                if value and (not place_data.get(key) or place_data.get(key) == ''):
                                    place_data[key] = value
                        
                        # Delay nhỏ giữa các request để tránh bị block
                        time.sleep(0.5)
                    
                    page_places.append(place_data)
                    
                    # Progress indicator
                    if idx % 5 == 0:
                        print(f"    [Progress] Đã parse {idx}/{len(items)} items...")
            
            if not page_places:
                print(f"  [Page {page}] Không parse được item nào")
                break
            
            places.extend(page_places)
            print(f"  [Page {page}] Đã parse {len(page_places)} địa điểm (Tổng: {len(places)} địa điểm)")
            
            # Kiểm tra nếu đã đạt giới hạn số địa điểm
            if max_items and len(places) >= max_items:
                places = places[:max_items]  # Chỉ lấy đúng số lượng cần thiết
                print(f"  [STOP] Đã đạt giới hạn {max_items} địa điểm")
                break
            print(f"  [Tổng cộng] Đã cào được {len(places)} địa điểm")
            
            # Kiểm tra nếu đã đủ số lượng cần cào
            if max_items and len(places) >= max_items:
                places = places[:max_items]  # Chỉ lấy đúng số lượng cần
                print(f"  [Đã đủ] Đã cào đủ {max_items} địa điểm, dừng lại")
                break
            
            # Kiểm tra xem còn trang tiếp theo không
            # Tìm pagination - có thể là ul.pagination hoặc div.pagination
            next_link = None
            pagination = soup.find(['ul', 'div'], class_=re.compile(r'pagination|pager', re.I))
            
            if pagination:
                # Tìm link "Trang sau", "Next", ">", "»"
                next_link = pagination.find('a', string=re.compile(r'trang sau|tiếp|next|>|»', re.I))
                if not next_link:
                    # Tìm link có rel="next"
                    next_link = pagination.find('a', {'rel': 'next'})
                if not next_link:
                    # Tìm link có href chứa page lớn hơn
                    all_links = pagination.find_all('a', href=True)
                    for link in all_links:
                        href = link.get('href', '')
                        # Kiểm tra data-ci-pagination-page
                        data_page = link.get('data-ci-pagination-page')
                        if data_page and int(data_page) == page + 1:
                            next_link = link
                            break
                        if f'page={page + 1}' in href or f'page/{page + 1}' in href:
                            next_link = link
                            break
                
                # Nếu không tìm thấy next_link, kiểm tra xem có link nào có page lớn hơn không
                if not next_link:
                    all_links = pagination.find_all('a', href=True)
                    for link in all_links:
                        href = link.get('href', '')
                        data_page = link.get('data-ci-pagination-page')
                        if data_page:
                            try:
                                if int(data_page) > page:
                                    next_link = link
                                    break
                            except:
                                pass
            
            # Kiểm tra số trang hiện tại và tổng số trang
            page_info = soup.find(string=re.compile(r'trang\s+\d+.*\d+|page\s+\d+.*\d+', re.I))
            if page_info:
                print(f"  [Page {page}] {page_info.strip()}")
            
            # Nếu không tìm thấy next_link, kiểm tra xem có còn dữ liệu không
            if not next_link:
                # Nếu không có items hoặc số items < 15 (thường là trang cuối), dừng lại
                if len(page_places) == 0:
                    print(f"  [Page {page}] Không còn dữ liệu, dừng lại")
                    break
                elif len(page_places) < 15:
                    # Có thể là trang cuối, nhưng vẫn lưu dữ liệu
                    print(f"  [Page {page}] Có {len(page_places)} items (có thể là trang cuối)")
                    # Tiếp tục thử trang tiếp theo để chắc chắn
                    if page < max_pages:
                        page += 1
                        continue
                    else:
                        break
                else:
                    # Có 15 items, có thể vẫn còn trang tiếp theo, thử tiếp
                    print(f"  [Page {page}] Không tìm thấy next link, nhưng vẫn thử trang tiếp theo...")
                    if page < max_pages:
                        page += 1
                        continue
                    else:
                        break
            
            page += 1
            time.sleep(2)  # Delay để tránh bị block
            
        except requests.RequestException as e:
            print(f"  [ERROR] Lỗi request page {page}: {e}")
            break
        except Exception as e:
            print(f"  [ERROR] Lỗi xử lý page {page}: {e}")
            import traceback
            traceback.print_exc()
            break
    
    print(f"  [Tổng kết] Đã cào được {len(places)} địa điểm từ danh mục {category_name}")
    return places

def save_to_database(places: List[Dict], category_slug: str):
    """Lưu dữ liệu vào database"""
    if not places:
        return
    
    loai_dia_diem = CATEGORY_MAPPING.get(category_slug, 'khac')
    created_count = 0
    updated_count = 0
    error_count = 0
    
    print(f"\nĐang lưu {len(places)} địa điểm vào database (loại: {loai_dia_diem})...")
    
    for place_data in places:
        try:
            # Tìm tỉnh thành
            province = get_province_from_address(place_data.get('diaChi', ''))
            if not province:
                print(f"  [SKIP] Không tìm thấy tỉnh thành cho: {place_data['tenDiaDiem']}")
                error_count += 1
                continue
            
            # Tạo hoặc cập nhật địa điểm
            # Sử dụng item_id nếu có để tránh duplicate
            # Lưu ý: Database schema yêu cầu nhiều trường NOT NULL, nên set giá trị mặc định
            defaults = {
                'loaiDiaDiem': loai_dia_diem,
                'diaChi': place_data.get('diaChi', '') or '',
                'dienThoai': place_data.get('dienThoai', '') or '',
                'website': place_data.get('website', '') or '',
                'moTa': place_data.get('moTa', '') or '',
                'viDo': 0.0,  # Giá trị mặc định, sẽ được cập nhật sau nếu có tọa độ
                'kinhDo': 0.0,  # Giá trị mặc định, sẽ được cập nhật sau nếu có tọa độ
                'giaVe': 0.0,  # Giá trị mặc định
                'gioMoCua': '',  # Giá trị mặc định
                'gioDongCua': '',  # Giá trị mặc định
                'trangThai': 'active',
            }
            
            # Lưu item_id vào dacDiem (JSON field) để tracking
            if place_data.get('item_id'):
                import json as json_lib
                dac_diem = {'item_id': place_data['item_id'], 'source': 'vietnam_tourism_db'}
                if place_data.get('detail_url'):
                    dac_diem['detail_url'] = place_data['detail_url']
                defaults['dacDiem'] = json_lib.dumps(dac_diem, ensure_ascii=False)
            
            dia_diem, created = DiaDiem.objects.update_or_create(
                tenDiaDiem=place_data['tenDiaDiem'],
                maTinhThanh=province,
                defaults=defaults
            )
            
            if created:
                created_count += 1
            else:
                updated_count += 1
            
            # In progress mỗi 10 items
            if (created_count + updated_count) % 10 == 0:
                print(f"  [Progress] Đã xử lý {created_count + updated_count}/{len(places)}...")
                
        except Exception as e:
            print(f"  [ERROR] Lỗi lưu {place_data.get('tenDiaDiem', 'Unknown')}: {e}")
            error_count += 1
    
    print(f"\n[Tổng kết lưu database]")
    print(f"  - Tạo mới: {created_count}")
    print(f"  - Cập nhật: {updated_count}")
    print(f"  - Lỗi: {error_count}")

def main():
    """Hàm main"""
    print("="*60)
    print("SCRIPT CÀO DỮ LIỆU TỪ CƠ SỞ DỮ LIỆU DU LỊCH VIỆT NAM")
    print("URL: https://csdl.vietnamtourism.gov.vn/csdt")
    print("="*60)
    
    # Danh sách các danh mục cần cào (theo URL slug thực tế)
    categories = [
        ('cslt', 'Cơ sở lưu trú'),
        ('rest', 'Nhà hàng'),
        ('dest', 'Điểm đến'),
        ('shop', 'Điểm mua sắm'),
        ('vcgt', 'Vui chơi giải trí'),
        ('ctyluhanh', 'Doanh nghiệp lữ hành'),
        ('huongdanvien', 'Hướng dẫn viên'),
        ('vantai', 'Vận tải khách du lịch'),
        ('thethao', 'Thể thao'),
        ('cssk', 'Chăm sóc sức khỏe'),
        ('hiephoi', 'Hiệp hội'),
        ('daotao', 'Cơ sở đào tạo'),
        ('nhanluc', 'Nhân lực du lịch'),
        ('xuctien', 'Xúc tiến du lịch'),
    ]
    
    all_places = []
    
    # Chỉ cào danh mục cslt (Cơ sở lưu trú) - 1000 địa điểm đầu tiên
    # Tính toán số trang: 1000 / 15 = ~67 trang
    target_category = ('cslt', 'Cơ sở lưu trú')
    category_slug, category_name = target_category
    max_items = 1000
    max_pages = (max_items // 15) + 1  # 67 trang
    
    try:
        print(f"\n{'='*60}")
        print(f"Bắt đầu cào danh mục: {category_name}")
        print(f"Số địa điểm cần cào: {max_items}")
        print(f"Số trang ước tính: {max_pages} trang (15 items/trang)")
        print(f"{'='*60}\n")
        
        places = scrape_category(category_slug, category_name, max_pages=max_pages, max_items=max_items)
        if places:
            all_places.extend(places)
            # Lưu vào database
            save_to_database(places, category_slug)
    except KeyboardInterrupt:
        print("\n[INTERRUPTED] Người dùng dừng script. Đang lưu dữ liệu đã cào...")
        if all_places:
            save_to_database(all_places, category_slug)
    except Exception as e:
        print(f"[ERROR] Lỗi khi cào danh mục {category_name}: {e}")
        import traceback
        traceback.print_exc()
        # Vẫn lưu dữ liệu đã cào được
        if all_places:
            save_to_database(all_places, category_slug)
    
    # Lưu tổng hợp vào file JSON
    output_file = PROJECT_ROOT / 'data' / 'vietnam_tourism_db_scraped.json'
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_places, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*60}")
    print(f"HOÀN TẤT!")
    print(f"Tổng số địa điểm đã cào: {len(all_places)}")
    print(f"Dữ liệu đã lưu vào: {output_file}")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()

