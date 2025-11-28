"""
Tải ảnh từ URL và lưu vào media/places/{maDiaDiem}/ và tạo record trong HINHANHDIADIEM
"""
import os
import sys
import django
import sqlite3
import requests
import re
from pathlib import Path
from urllib.parse import urlparse, unquote
from datetime import datetime

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    if sys.stdout.encoding != 'utf-8':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)

# Setup Django
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vivu_core.settings')
django.setup()

from django.conf import settings

# Database path
db_path = PROJECT_ROOT / 'vivudb.sqlite3'
if not db_path.exists():
    print(f"Error: Cannot find vivudb.sqlite3 at {db_path}")
    sys.exit(1)

# Media root
MEDIA_ROOT = getattr(settings, 'MEDIA_ROOT', PROJECT_ROOT / 'media')
PLACES_MEDIA_DIR = Path(MEDIA_ROOT) / 'places'


def extract_image_url_from_google_maps(google_maps_url: str) -> str:
    """
    Trích xuất URL ảnh từ Google Maps link
    """
    # Decode URL trước
    decoded_url = unquote(google_maps_url)
    
    # Tìm URL ảnh trong link (thường có dạng https://lh3.googleusercontent.com/...)
    # Pattern 1: Tìm trong phần 6shttps://...
    pattern1 = r'6shttps://lh3\.googleusercontent\.com/[^!]+'
    matches1 = re.findall(pattern1, decoded_url)
    
    if matches1:
        # Lấy URL đầu tiên và loại bỏ prefix "6s"
        image_url = matches1[0].replace('6s', '')
        # Thay thế kích thước nhỏ bằng kích thước lớn hơn
        image_url = re.sub(r'=w\d+-h\d+-k-no', '=w1200-h800', image_url)
        image_url = re.sub(r'=w\d+-h\d+', '=w1200-h800', image_url)
        return image_url
    
    # Pattern 2: Tìm trực tiếp trong URL đã decode
    pattern2 = r'https://lh3\.googleusercontent\.com/[^!]+'
    matches2 = re.findall(pattern2, decoded_url)
    
    if matches2:
        image_url = matches2[0]
        # Thay thế kích thước nhỏ bằng kích thước lớn hơn
        image_url = re.sub(r'=w\d+-h\d+-k-no', '=w1200-h800', image_url)
        image_url = re.sub(r'=w\d+-h\d+', '=w1200-h800', image_url)
        return image_url
    
    return None


def download_image(image_url: str, ma_dia_diem: int, description: str = ""):
    """
    Tải ảnh từ URL và lưu vào media/places/{maDiaDiem}/
    
    Returns:
        (success, message)
    """
    try:
        # Tạo thư mục nếu chưa có
        place_dir = PLACES_MEDIA_DIR / str(ma_dia_diem)
        place_dir.mkdir(parents=True, exist_ok=True)
        
        # Lấy extension từ URL hoặc mặc định là .jpg
        parsed_url = urlparse(image_url)
        path = parsed_url.path
        ext = os.path.splitext(path)[1] or '.jpg'
        
        # Tạo tên file (sử dụng timestamp để tránh trùng)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}{ext}"
        filepath = place_dir / filename
        
        # Tải ảnh
        print(f"Đang tải ảnh từ: {image_url}")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(image_url, headers=headers, timeout=30, stream=True)
        response.raise_for_status()
        
        # Lưu file
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # Tạo đường dẫn relative cho database (media/places/{maDiaDiem}/{filename})
        relative_path = f"places/{ma_dia_diem}/{filename}"
        
        # Lưu vào database
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        try:
            # Kiểm tra xem đã có ảnh chính chưa
            cursor.execute("""
                SELECT COUNT(*) FROM HINHANHDIADIEM 
                WHERE maDiaDiem = ? AND laChinh = 1
            """, (ma_dia_diem,))
            has_main_image = cursor.fetchone()[0] > 0
            
            # Lấy ID tiếp theo
            cursor.execute("SELECT COALESCE(MAX(maHinhAnh), 0) + 1 FROM HINHANHDIADIEM")
            next_id = cursor.fetchone()[0] or 1
            
            # Insert vào database
            cursor.execute("""
                INSERT INTO HINHANHDIADIEM 
                (maHinhAnh, maDiaDiem, urlHinhAnh, moTa, laChinh, ngayTao)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                next_id,
                ma_dia_diem,
                relative_path,  # Lưu đường dẫn relative
                description or f"Ảnh của {filename}",
                0 if has_main_image else 1,  # Nếu chưa có ảnh chính thì đặt làm ảnh chính
                datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            ))
            
            conn.commit()
            
            return True, f"Đã tải và lưu ảnh thành công! (ID: {next_id}, File: {filepath}, DB: {relative_path})"
            
        except sqlite3.Error as e:
            conn.rollback()
            # Xóa file nếu insert database thất bại
            if filepath.exists():
                filepath.unlink()
            return False, f"Lỗi database: {e}"
        finally:
            conn.close()
            
    except requests.RequestException as e:
        return False, f"Lỗi khi tải ảnh: {e}"
    except Exception as e:
        return False, f"Lỗi: {e}"


def main():
    if len(sys.argv) < 3:
        print("Usage: python download_place_image.py <maDiaDiem> <image_url1> [image_url2] ... [description]")
        print("Example: python download_place_image.py 123 https://example.com/image.jpg 'Mô tả ảnh'")
        print("Example: python download_place_image.py 123 'https://maps.google.com/...' 'https://maps.google.com/...'")
        sys.exit(1)
    
    try:
        ma_dia_diem = int(sys.argv[1])
    except ValueError:
        print(f"Error: maDiaDiem phải là số nguyên. Nhận được: {sys.argv[1]}")
        sys.exit(1)
    
    # Lấy tất cả các URL (có thể là nhiều link)
    image_urls = sys.argv[2:]
    description = ""
    
    # Nếu tham số cuối cùng không phải là URL (không có http), coi như là description
    if image_urls and not image_urls[-1].startswith('http'):
        description = image_urls.pop()
    
    # Kiểm tra địa điểm có tồn tại không
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute("SELECT tenDiaDiem FROM DIADIEM WHERE maDiaDiem = ?", (ma_dia_diem,))
    result = cursor.fetchone()
    conn.close()
    
    if not result:
        print(f"Error: Không tìm thấy địa điểm với maDiaDiem = {ma_dia_diem}")
        sys.exit(1)
    
    ten_dia_diem = result[0]
    print(f"Địa điểm: {ten_dia_diem} (ID: {ma_dia_diem})")
    print(f"Số lượng ảnh sẽ tải: {len(image_urls)}")
    print()
    
    # Xử lý từng URL
    success_count = 0
    fail_count = 0
    
    for idx, image_url in enumerate(image_urls, 1):
        print(f"[{idx}/{len(image_urls)}] Đang xử lý...")
        
        # Kiểm tra nếu là Google Maps link, tự động trích xuất URL ảnh
        if 'google.com/maps' in image_url:
            print("  Phát hiện Google Maps link, đang trích xuất URL ảnh...")
            extracted_url = extract_image_url_from_google_maps(image_url)
            if extracted_url:
                print(f"  Đã trích xuất URL ảnh: {extracted_url[:80]}...")
                image_url = extracted_url
            else:
                print("  Không thể trích xuất URL ảnh từ Google Maps link. Bỏ qua.")
                fail_count += 1
                continue
        
        # Tải ảnh
        img_description = description or f"Ảnh {idx} của {ten_dia_diem}"
        success, message = download_image(image_url, ma_dia_diem, img_description)
        
        if success:
            print(f"  ✓ {message}")
            success_count += 1
        else:
            print(f"  ✗ {message}")
            fail_count += 1
        
        print()
    
    # Tổng kết
    print("="*80)
    print("TỔNG KẾT")
    print("="*80)
    print(f"Thành công: {success_count}/{len(image_urls)}")
    print(f"Thất bại: {fail_count}/{len(image_urls)}")
    print("="*80)
    
    if fail_count > 0:
        sys.exit(1)


if __name__ == '__main__':
    main()

