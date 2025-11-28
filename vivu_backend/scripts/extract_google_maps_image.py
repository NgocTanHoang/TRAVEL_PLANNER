"""
Trích xuất URL ảnh từ Google Maps link
"""
import re
from urllib.parse import unquote

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

if __name__ == '__main__':
    test_url = "https://www.google.com/maps/place/Karaoke+Th%C3%A0nh+%C4%90%E1%BA%A1t/@10.0950703,105.7217531,3a,75y,90t/data=!3m8!1e2!3m6!1sCIHM0ogKEICAgIDV1aqWdg!2e10!3e12!6shttps:%2F%2Flh3.googleusercontent.com%2Fgps-cs-s%2FAG0ilSxrQUkpqQd3HZuQqGpKIlgxeIzEM9EyZq-_WLj6I9_3Jc0NKDjoby4111GaLbueIeANvbzBLh4rNyXApBB2dP858-EN0znuMkJvhLNth0CXM5e4_U4OPs155Ak8eg2aPIxz5bk%3Dw203-h270-k-no!7i3024!8i4032!4m9!3m8!1s0x31a0865a203ef6d5:0x4327e380ea869b5c!8m2!3d10.0949435!4d105.7216468!10e5!14m1!1BCgIgAQ!16s%2Fg%2F11h0r3g18?entry=ttu&g_ep=EgoyMDI1MTExNy4wIKXMDSoASAFQAw%3D%3D#"
    
    image_url = extract_image_url_from_google_maps(test_url)
    if image_url:
        print(f"Extracted image URL: {image_url}")
    else:
        print("Could not extract image URL")

