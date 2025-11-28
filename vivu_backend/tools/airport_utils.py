"""
Airport mapping utilities - Xác định sân bay gần nhất
"""
from typing import Dict, Optional, Tuple, Any

# Mapping tỉnh/thành phố → sân bay gần nhất
CITY_AIRPORT_MAP = {
        # Miền Bắc
        'Hà Nội': ('HAN', 'Nội Bài', 'Hà Nội'),
        'Ha Noi': ('HAN', 'Nội Bài', 'Hà Nội'),
        'Hanoi': ('HAN', 'Nội Bài', 'Hà Nội'),
        'Hải Phòng': ('HPH', 'Cát Bi', 'Hải Phòng'),
        'Hai Phong': ('HPH', 'Cát Bi', 'Hải Phòng'),
        'Hải Dương': ('HPH', 'Cát Bi', 'Hải Phòng'),  # Thuộc Hải Phòng
        'Hai Duong': ('HPH', 'Cát Bi', 'Hải Phòng'),
        'Hưng Yên': ('HAN', 'Nội Bài', 'Hà Nội'),
        'Hung Yen': ('HAN', 'Nội Bài', 'Hà Nội'),
        'Thái Bình': ('HPH', 'Cát Bi', 'Hải Phòng'),  # Thuộc Hưng Yên, nhưng gần Hải Phòng hơn
        'Thai Binh': ('HPH', 'Cát Bi', 'Hải Phòng'),
        'Hà Nam': ('HAN', 'Nội Bài', 'Hà Nội'),  # Thuộc Ninh Bình
        'Ha Nam': ('HAN', 'Nội Bài', 'Hà Nội'),
        'Nam Định': ('HAN', 'Nội Bài', 'Hà Nội'),  # Thuộc Ninh Bình
        'Nam Dinh': ('HAN', 'Nội Bài', 'Hà Nội'),
        'Ninh Bình': ('HAN', 'Nội Bài', 'Hà Nội'),
        'Ninh Binh': ('HAN', 'Nội Bài', 'Hà Nội'),
        'Bắc Ninh': ('HAN', 'Nội Bài', 'Hà Nội'),
        'Bac Ninh': ('HAN', 'Nội Bài', 'Hà Nội'),
        'Bắc Giang': ('HAN', 'Nội Bài', 'Hà Nội'),  # Thuộc Bắc Ninh
        'Bac Giang': ('HAN', 'Nội Bài', 'Hà Nội'),
        'Thái Nguyên': ('HAN', 'Nội Bài', 'Hà Nội'),
        'Thai Nguyen': ('HAN', 'Nội Bài', 'Hà Nội'),
        'Bắc Kạn': ('HAN', 'Nội Bài', 'Hà Nội'),  # Thuộc Thái Nguyên
        'Bac Kan': ('HAN', 'Nội Bài', 'Hà Nội'),
        'Phú Thọ': ('HAN', 'Nội Bài', 'Hà Nội'),
        'Phu Tho': ('HAN', 'Nội Bài', 'Hà Nội'),
        'Hòa Bình': ('HAN', 'Nội Bài', 'Hà Nội'),  # Thuộc Phú Thọ
        'Hoa Binh': ('HAN', 'Nội Bài', 'Hà Nội'),
        'Vĩnh Phúc': ('HAN', 'Nội Bài', 'Hà Nội'),  # Thuộc Phú Thọ
        'Vinh Phuc': ('HAN', 'Nội Bài', 'Hà Nội'),
        'Tuyên Quang': ('HAN', 'Nội Bài', 'Hà Nội'),
        'Tuyen Quang': ('HAN', 'Nội Bài', 'Hà Nội'),
        'Hà Giang': ('HAN', 'Nội Bài', 'Hà Nội'),  # Thuộc Tuyên Quang
        'Ha Giang': ('HAN', 'Nội Bài', 'Hà Nội'),
        'Lào Cai': ('HAN', 'Nội Bài', 'Hà Nội'),
        'Lao Cai': ('HAN', 'Nội Bài', 'Hà Nội'),
        'Yên Bái': ('HAN', 'Nội Bài', 'Hà Nội'),  # Thuộc Lào Cai
        'Yen Bai': ('HAN', 'Nội Bài', 'Hà Nội'),
        'Lai Châu': ('HAN', 'Nội Bài', 'Hà Nội'),
        'Lai Chau': ('HAN', 'Nội Bài', 'Hà Nội'),
        'Điện Biên': ('HAN', 'Nội Bài', 'Hà Nội'),
        'Dien Bien': ('HAN', 'Nội Bài', 'Hà Nội'),
        'Sơn La': ('HAN', 'Nội Bài', 'Hà Nội'),
        'Son La': ('HAN', 'Nội Bài', 'Hà Nội'),
        'Lạng Sơn': ('HAN', 'Nội Bài', 'Hà Nội'),
        'Lang Son': ('HAN', 'Nội Bài', 'Hà Nội'),
        'Cao Bằng': ('HAN', 'Nội Bài', 'Hà Nội'),
        'Cao Bang': ('HAN', 'Nội Bài', 'Hà Nội'),
        'Thanh Hóa': ('HAN', 'Nội Bài', 'Hà Nội'),
        'Thanh Hoa': ('HAN', 'Nội Bài', 'Hà Nội'),
        'Nghệ An': ('HAN', 'Nội Bài', 'Hà Nội'),
        'Nghe An': ('HAN', 'Nội Bài', 'Hà Nội'),
        'Hà Tĩnh': ('HAN', 'Nội Bài', 'Hà Nội'),
        'Ha Tinh': ('HAN', 'Nội Bài', 'Hà Nội'),
        'Quảng Bình': ('HUI', 'Phú Bài', 'Huế'),  # Thuộc Quảng Trị, nhưng gần Huế hơn
        'Quang Binh': ('HUI', 'Phú Bài', 'Huế'),
        'Quảng Trị': ('HUI', 'Phú Bài', 'Huế'),
        'Quang Tri': ('HUI', 'Phú Bài', 'Huế'),
        'Thừa Thiên Huế': ('HUI', 'Phú Bài', 'Huế'),
        'Thua Thien Hue': ('HUI', 'Phú Bài', 'Huế'),
        'Thừa Thiên – Huế': ('HUI', 'Phú Bài', 'Huế'),
        'Huế': ('HUI', 'Phú Bài', 'Huế'),
        'Hue': ('HUI', 'Phú Bài', 'Huế'),
        
        # Miền Trung
        'Đà Nẵng': ('DAD', 'Đà Nẵng', 'Đà Nẵng'),
        'Da Nang': ('DAD', 'Đà Nẵng', 'Đà Nẵng'),
        'Quảng Nam': ('DAD', 'Đà Nẵng', 'Đà Nẵng'),  # Thuộc Đà Nẵng
        'Quang Nam': ('DAD', 'Đà Nẵng', 'Đà Nẵng'),
        'Quảng Ngãi': ('DAD', 'Đà Nẵng', 'Đà Nẵng'),
        'Quang Ngai': ('DAD', 'Đà Nẵng', 'Đà Nẵng'),
        'Kon Tum': ('DAD', 'Đà Nẵng', 'Đà Nẵng'),  # Thuộc Quảng Ngãi
        'Bình Định': ('UIH', 'Phù Cát', 'Quy Nhơn'),  # Thuộc Gia Lai
        'Binh Dinh': ('UIH', 'Phù Cát', 'Quy Nhơn'),
        'Phú Yên': ('UIH', 'Phù Cát', 'Quy Nhơn'),  # Thuộc Đắk Lắk, nhưng gần Quy Nhơn
        'Phu Yen': ('UIH', 'Phù Cát', 'Quy Nhơn'),
        'Gia Lai': ('UIH', 'Phù Cát', 'Quy Nhơn'),
        'Khánh Hòa': ('CXR', 'Cam Ranh', 'Nha Trang'),
        'Khanh Hoa': ('CXR', 'Cam Ranh', 'Nha Trang'),
        'Nha Trang': ('CXR', 'Cam Ranh', 'Nha Trang'),
        'Ninh Thuận': ('CXR', 'Cam Ranh', 'Nha Trang'),  # Thuộc Khánh Hòa
        'Ninh Thuan': ('CXR', 'Cam Ranh', 'Nha Trang'),
        'Bình Thuận': ('CXR', 'Cam Ranh', 'Nha Trang'),  # Thuộc Lâm Đồng
        'Binh Thuan': ('CXR', 'Cam Ranh', 'Nha Trang'),
        'Đà Lạt': ('DLI', 'Liên Khương', 'Đà Lạt'),
        'Da Lat': ('DLI', 'Liên Khương', 'Đà Lạt'),
        'Lâm Đồng': ('DLI', 'Liên Khương', 'Đà Lạt'),
        'Lam Dong': ('DLI', 'Liên Khương', 'Đà Lạt'),
        'Đắk Lắk': ('DLI', 'Liên Khương', 'Đà Lạt'),
        'Dak Lak': ('DLI', 'Liên Khương', 'Đà Lạt'),
        'Đắk Nông': ('DLI', 'Liên Khương', 'Đà Lạt'),  # Thuộc Lâm Đồng
        'Dak Nong': ('DLI', 'Liên Khương', 'Đà Lạt'),
        
        # Miền Nam
        'TP. Hồ Chí Minh': ('SGN', 'Tân Sơn Nhất', 'TP.HCM'),
        'Thành phố Hồ Chí Minh': ('SGN', 'Tân Sơn Nhất', 'TP.HCM'),
        'Ho Chi Minh': ('SGN', 'Tân Sơn Nhất', 'TP.HCM'),
        'Ho Chi Minh City': ('SGN', 'Tân Sơn Nhất', 'TP.HCM'),
        'TP.HCM': ('SGN', 'Tân Sơn Nhất', 'TP.HCM'),
        'Sài Gòn': ('SGN', 'Tân Sơn Nhất', 'TP.HCM'),
        'Sai Gon': ('SGN', 'Tân Sơn Nhất', 'TP.HCM'),
        'Đồng Nai': ('SGN', 'Tân Sơn Nhất', 'TP.HCM'),
        'Dong Nai': ('SGN', 'Tân Sơn Nhất', 'TP.HCM'),
        'Biên Hòa': ('SGN', 'Tân Sơn Nhất', 'TP.HCM'),
        'Bien Hoa': ('SGN', 'Tân Sơn Nhất', 'TP.HCM'),
        'Bình Dương': ('SGN', 'Tân Sơn Nhất', 'TP.HCM'),  # Thuộc TP.HCM
        'Binh Duong': ('SGN', 'Tân Sơn Nhất', 'TP.HCM'),
        'Bà Rịa - Vũng Tàu': ('SGN', 'Tân Sơn Nhất', 'TP.HCM'),  # Thuộc TP.HCM
        'Ba Ria - Vung Tau': ('SGN', 'Tân Sơn Nhất', 'TP.HCM'),
        'Bình Phước': ('SGN', 'Tân Sơn Nhất', 'TP.HCM'),  # Thuộc Đồng Nai
        'Binh Phuoc': ('SGN', 'Tân Sơn Nhất', 'TP.HCM'),
        'Tây Ninh': ('SGN', 'Tân Sơn Nhất', 'TP.HCM'),
        'Tay Ninh': ('SGN', 'Tân Sơn Nhất', 'TP.HCM'),
        'Long An': ('SGN', 'Tân Sơn Nhất', 'TP.HCM'),  # Thuộc Tây Ninh
        'Tiền Giang': ('SGN', 'Tân Sơn Nhất', 'TP.HCM'),  # Thuộc Đồng Tháp
        'Tien Giang': ('SGN', 'Tân Sơn Nhất', 'TP.HCM'),
        'Bến Tre': ('SGN', 'Tân Sơn Nhất', 'TP.HCM'),  # Thuộc Vĩnh Long
        'Ben Tre': ('SGN', 'Tân Sơn Nhất', 'TP.HCM'),
        'Vĩnh Long': ('SGN', 'Tân Sơn Nhất', 'TP.HCM'),
        'Vinh Long': ('SGN', 'Tân Sơn Nhất', 'TP.HCM'),
        'Trà Vinh': ('SGN', 'Tân Sơn Nhất', 'TP.HCM'),  # Thuộc Vĩnh Long
        'Tra Vinh': ('SGN', 'Tân Sơn Nhất', 'TP.HCM'),
        'Đồng Tháp': ('SGN', 'Tân Sơn Nhất', 'TP.HCM'),
        'Dong Thap': ('SGN', 'Tân Sơn Nhất', 'TP.HCM'),
        'Cần Thơ': ('VCA', 'Cần Thơ', 'Cần Thơ'),
        'Can Tho': ('VCA', 'Cần Thơ', 'Cần Thơ'),
        'Hậu Giang': ('VCA', 'Cần Thơ', 'Cần Thơ'),  # Thuộc Cần Thơ
        'Hau Giang': ('VCA', 'Cần Thơ', 'Cần Thơ'),
        'Sóc Trăng': ('VCA', 'Cần Thơ', 'Cần Thơ'),  # Thuộc Cần Thơ
        'Soc Trang': ('VCA', 'Cần Thơ', 'Cần Thơ'),
        'An Giang': ('VCA', 'Cần Thơ', 'Cần Thơ'),
        'An Giang': ('VCA', 'Cần Thơ', 'Cần Thơ'),
        'Kiên Giang': ('PQC', 'Phú Quốc', 'Phú Quốc'),  # Thuộc An Giang
        'Kien Giang': ('PQC', 'Phú Quốc', 'Phú Quốc'),
        'Phú Quốc': ('PQC', 'Phú Quốc', 'Phú Quốc'),
        'Phu Quoc': ('PQC', 'Phú Quốc', 'Phú Quốc'),
        'Bạc Liêu': ('VCA', 'Cần Thơ', 'Cần Thơ'),  # Thuộc Cà Mau
        'Bac Lieu': ('VCA', 'Cần Thơ', 'Cần Thơ'),
        'Cà Mau': ('VCA', 'Cần Thơ', 'Cần Thơ'),
        'Ca Mau': ('VCA', 'Cần Thơ', 'Cần Thơ'),
        'Quảng Ninh': ('HAN', 'Nội Bài', 'Hà Nội'),
        'Quang Ninh': ('HAN', 'Nội Bài', 'Hà Nội'),
    }


def get_nearest_airport(city_name: str) -> Optional[Tuple[str, str, str]]:
    """
    Lấy sân bay gần nhất cho một thành phố/tỉnh
    
    Args:
        city_name: Tên thành phố/tỉnh
        
    Returns:
        Tuple (IATA_code, airport_name, city_name) hoặc None
    """
    # Tìm exact match
    if city_name in CITY_AIRPORT_MAP:
        return CITY_AIRPORT_MAP[city_name]
    
    # Tìm case-insensitive
    city_lower = city_name.strip().lower()
    for city, airport_info in CITY_AIRPORT_MAP.items():
        if city.lower() == city_lower:
            return airport_info
    
    # Fallback: Nếu không tìm thấy, thử các pattern
    if 'hà nội' in city_lower or 'hanoi' in city_lower:
        return ('HAN', 'Nội Bài', 'Hà Nội')
    if 'hồ chí minh' in city_lower or 'ho chi minh' in city_lower or 'sài gòn' in city_lower or 'sai gon' in city_lower:
        return ('SGN', 'Tân Sơn Nhất', 'TP.HCM')
    if 'đà nẵng' in city_lower or 'da nang' in city_lower:
        return ('DAD', 'Đà Nẵng', 'Đà Nẵng')
    if 'đồng nai' in city_lower or 'dong nai' in city_lower or 'biên hòa' in city_lower:
        return ('SGN', 'Tân Sơn Nhất', 'TP.HCM')
    
    return None


def calculate_airport_transport_cost(
    origin: str,
    destination: str,
    distance_km: float,
    method: str = 'taxi'
) -> Dict[str, Any]:
    """
    Tính chi phí di chuyển từ điểm xuất phát/đến đến sân bay
    
    Args:
        origin: Điểm xuất phát/đến (có thể là thành phố hoặc đã là sân bay)
        destination: Điểm đến/đi (sân bay)
        distance_km: Khoảng cách (km)
        method: Phương tiện ('taxi', 'bus', 'grab')
        
    Returns:
        Dict với cost, method, duration
    """
    from tools.transport_tools import get_transport_tools
    transport_tools = get_transport_tools()
    
    # Tính chi phí
    if method == 'bus':
        cost_per_km = 2000  # Xe buýt: 2k/km
    elif method == 'taxi' or method == 'grab':
        cost_per_km = 12000  # Taxi/Grab: 12k/km
    elif method == 'greencar':
        # VinFast GreenCar: tính theo cấu trúc giá đặc biệt
        opening_fee = 20000
        if distance_km <= 0:
            cost = opening_fee
        elif distance_km <= 25:
            cost = opening_fee + (distance_km * 14000)
        else:
            cost = opening_fee + (25 * 14000) + ((distance_km - 25) * 12000)
        return {
            'cost_vnd': round(cost),
            'method': method,
            'distance_km': round(distance_km, 2),
            'duration_minutes': round((distance_km / 50) * 60, 1)
        }
    elif method == 'luxurycar':
        # VinFast LuxuryCar: 21k/km cố định
        opening_fee = 21000
        cost = opening_fee + (distance_km * 21000) if distance_km > 0 else opening_fee
        return {
            'cost_vnd': round(cost),
            'method': method,
            'distance_km': round(distance_km, 2),
            'duration_minutes': round((distance_km / 50) * 60, 1)
        }
    else:
        cost_per_km = 12000
    
    cost = distance_km * cost_per_km
    
    # Ước tính thời gian (tốc độ trung bình)
    if method == 'bus':
        avg_speed = 40  # km/h
    else:
        avg_speed = 50  # km/h
    
    duration_minutes = (distance_km / avg_speed) * 60
    
    return {
        'cost_vnd': round(cost),
        'method': method,
        'distance_km': round(distance_km, 2),
        'duration_minutes': round(duration_minutes, 1)
    }

