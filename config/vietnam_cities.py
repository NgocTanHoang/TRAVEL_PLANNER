"""
Danh sách 56 tỉnh thành Việt Nam với tọa độ trung tâm
Dùng cho thu thập dữ liệu từ APIs
"""

VIETNAM_CITIES = {
    # Thành phố lớn (đã có dữ liệu chi tiết)
    "Hanoi": {"lat": 21.0285, "lon": 105.8542, "name_vi": "Hà Nội", "priority": 1},
    "Ho Chi Minh City": {"lat": 10.8231, "lon": 106.6297, "name_vi": "TP.HCM", "priority": 1},
    "Da Nang": {"lat": 16.0544, "lon": 108.2022, "name_vi": "Đà Nẵng", "priority": 1},
    "Hoi An": {"lat": 15.8786, "lon": 108.3348, "name_vi": "Hội An", "priority": 1},
    "Hue": {"lat": 16.4637, "lon": 107.5909, "name_vi": "Huế", "priority": 1},
    "Nha Trang": {"lat": 12.2388, "lon": 109.1967, "name_vi": "Nha Trang", "priority": 1},
    "Da Lat": {"lat": 11.9404, "lon": 108.4583, "name_vi": "Đà Lạt", "priority": 1},
    "Phu Quoc": {"lat": 10.2899, "lon": 103.9840, "name_vi": "Phú Quốc", "priority": 1},
    
    # Miền Bắc (cần bổ sung dữ liệu)
    "Hai Phong": {"lat": 20.8449, "lon": 106.6881, "name_vi": "Hải Phòng", "priority": 2},
    "Ha Long": {"lat": 20.9519, "lon": 107.0758, "name_vi": "Hạ Long", "priority": 2},
    "Quang Ninh": {"lat": 21.0064, "lon": 107.2925, "name_vi": "Quảng Ninh", "priority": 2},
    "Cat Ba": {"lat": 20.7267, "lon": 107.0456, "name_vi": "Cát Bà", "priority": 2},
    "Sapa": {"lat": 22.3364, "lon": 103.8438, "name_vi": "Sapa", "priority": 2},
    "Lao Cai": {"lat": 22.4856, "lon": 103.9750, "name_vi": "Lào Cai", "priority": 3},
    "Ha Giang": {"lat": 22.8025, "lon": 104.9784, "name_vi": "Hà Giang", "priority": 3},
    "Cao Bang": {"lat": 22.6663, "lon": 106.2525, "name_vi": "Cao Bằng", "priority": 3},
    "Lang Son": {"lat": 21.8537, "lon": 106.7617, "name_vi": "Lạng Sơn", "priority": 3},
    "Bac Kan": {"lat": 22.1474, "lon": 105.8348, "name_vi": "Bắc Kạn", "priority": 3},
    "Thai Nguyen": {"lat": 21.5671, "lon": 105.8252, "name_vi": "Thái Nguyên", "priority": 3},
    "Tuyen Quang": {"lat": 21.8237, "lon": 105.2189, "name_vi": "Tuyên Quang", "priority": 3},
    "Yen Bai": {"lat": 21.7168, "lon": 104.8986, "name_vi": "Yên Bái", "priority": 3},
    "Dien Bien": {"lat": 21.3833, "lon": 103.0167, "name_vi": "Điện Biên", "priority": 3},
    "Lai Chau": {"lat": 22.3864, "lon": 103.4702, "name_vi": "Lai Châu", "priority": 3},
    "Son La": {"lat": 21.3256, "lon": 103.9019, "name_vi": "Sơn La", "priority": 3},
    "Hoa Binh": {"lat": 20.6861, "lon": 105.3131, "name_vi": "Hòa Bình", "priority": 3},
    "Phu Tho": {"lat": 21.2686, "lon": 105.2045, "name_vi": "Phú Thọ", "priority": 3},
    "Vinh Phuc": {"lat": 21.3609, "lon": 105.5474, "name_vi": "Vĩnh Phúc", "priority": 3},
    "Bac Ninh": {"lat": 21.1214, "lon": 106.1110, "name_vi": "Bắc Ninh", "priority": 3},
    "Bac Giang": {"lat": 21.2731, "lon": 106.1946, "name_vi": "Bắc Giang", "priority": 3},
    "Hai Duong": {"lat": 20.9373, "lon": 106.3148, "name_vi": "Hải Dương", "priority": 3},
    "Hung Yen": {"lat": 20.6464, "lon": 106.0511, "name_vi": "Hưng Yên", "priority": 3},
    "Thai Binh": {"lat": 20.4464, "lon": 106.3365, "name_vi": "Thái Bình", "priority": 3},
    "Nam Dinh": {"lat": 20.4388, "lon": 106.1621, "name_vi": "Nam Định", "priority": 3},
    "Ha Nam": {"lat": 20.5835, "lon": 105.9230, "name_vi": "Hà Nam", "priority": 3},
    "Ninh Binh": {"lat": 20.2506, "lon": 105.9745, "name_vi": "Ninh Bình", "priority": 2},
    "Tam Dao": {"lat": 21.4572, "lon": 105.6389, "name_vi": "Tam Đảo", "priority": 2},
    "Ba Vi": {"lat": 21.0856, "lon": 105.3728, "name_vi": "Ba Vì", "priority": 3},
    
    # Miền Trung (cần bổ sung dữ liệu)
    "Thanh Hoa": {"lat": 19.8067, "lon": 105.7852, "name_vi": "Thanh Hóa", "priority": 3},
    "Nghe An": {"lat": 18.6792, "lon": 105.6819, "name_vi": "Nghệ An", "priority": 2},
    "Ha Tinh": {"lat": 18.3559, "lon": 105.9058, "name_vi": "Hà Tĩnh", "priority": 3},
    "Quang Binh": {"lat": 17.4676, "lon": 106.6229, "name_vi": "Quảng Bình", "priority": 2},
    "Quang Tri": {"lat": 16.7943, "lon": 107.1856, "name_vi": "Quảng Trị", "priority": 3},
    "Thua Thien Hue": {"lat": 16.4637, "lon": 107.5909, "name_vi": "Thừa Thiên Huế", "priority": 2},
    "Quang Nam": {"lat": 15.5394, "lon": 108.0191, "name_vi": "Quảng Nam", "priority": 2},
    "Quang Ngai": {"lat": 15.1214, "lon": 108.8044, "name_vi": "Quảng Ngãi", "priority": 3},
    "Binh Dinh": {"lat": 13.7829, "lon": 109.2196, "name_vi": "Bình Định", "priority": 3},
    "Quy Nhon": {"lat": 13.7829, "lon": 109.2196, "name_vi": "Quy Nhơn", "priority": 2},
    "Phu Yen": {"lat": 13.0955, "lon": 109.0929, "name_vi": "Phú Yên", "priority": 3},
    "Khanh Hoa": {"lat": 12.2388, "lon": 109.1967, "name_vi": "Khánh Hòa", "priority": 2},
    "Ninh Thuan": {"lat": 11.6739, "lon": 108.8629, "name_vi": "Ninh Thuận", "priority": 3},
    "Binh Thuan": {"lat": 10.9297, "lon": 108.0717, "name_vi": "Bình Thuận", "priority": 2},
    "Phan Thiet": {"lat": 10.9297, "lon": 108.1022, "name_vi": "Phan Thiết", "priority": 2},
    "Mui Ne": {"lat": 10.9333, "lon": 108.2833, "name_vi": "Mũi Né", "priority": 2},
    
    # Tây Nguyên (cần bổ sung dữ liệu)
    "Kon Tum": {"lat": 14.3545, "lon": 108.0004, "name_vi": "Kon Tum", "priority": 3},
    "Gia Lai": {"lat": 13.9833, "lon": 108.0000, "name_vi": "Gia Lai", "priority": 3},
    "Dak Lak": {"lat": 12.6667, "lon": 108.0500, "name_vi": "Đắk Lắk", "priority": 2},
    "Dak Nong": {"lat": 12.2646, "lon": 107.6098, "name_vi": "Đắk Nông", "priority": 3},
    "Lam Dong": {"lat": 11.5753, "lon": 108.1429, "name_vi": "Lâm Đồng", "priority": 2},
    
    # Miền Nam (cần bổ sung dữ liệu)
    "Binh Phuoc": {"lat": 11.7511, "lon": 106.7234, "name_vi": "Bình Phước", "priority": 3},
    "Tay Ninh": {"lat": 11.3351, "lon": 106.0988, "name_vi": "Tây Ninh", "priority": 3},
    "Binh Duong": {"lat": 11.3254, "lon": 106.4770, "name_vi": "Bình Dương", "priority": 2},
    "Dong Nai": {"lat": 10.9467, "lon": 107.1676, "name_vi": "Đồng Nai", "priority": 2},
    "Ba Ria - Vung Tau": {"lat": 10.5417, "lon": 107.2429, "name_vi": "Bà Rịa - Vũng Tàu", "priority": 2},
    "Vung Tau": {"lat": 10.3460, "lon": 107.0843, "name_vi": "Vũng Tàu", "priority": 2},
    "Con Dao": {"lat": 8.6833, "lon": 106.6000, "name_vi": "Côn Đảo", "priority": 2},
    "Long An": {"lat": 10.6956, "lon": 106.2431, "name_vi": "Long An", "priority": 3},
    "Tien Giang": {"lat": 10.3596, "lon": 106.3622, "name_vi": "Tiền Giang", "priority": 3},
    "Ben Tre": {"lat": 10.2433, "lon": 106.3759, "name_vi": "Bến Tre", "priority": 3},
    "Tra Vinh": {"lat": 9.8124, "lon": 106.2992, "name_vi": "Trà Vinh", "priority": 3},
    "Vinh Long": {"lat": 10.2397, "lon": 105.9571, "name_vi": "Vĩnh Long", "priority": 3},
    "Dong Thap": {"lat": 10.4938, "lon": 105.6881, "name_vi": "Đồng Tháp", "priority": 3},
    "An Giang": {"lat": 10.5216, "lon": 105.1259, "name_vi": "An Giang", "priority": 2},
    "Kien Giang": {"lat": 10.0125, "lon": 105.0809, "name_vi": "Kiên Giang", "priority": 2},
    "Can Tho": {"lat": 10.0452, "lon": 105.7469, "name_vi": "Cần Thơ", "priority": 2},
    "Hau Giang": {"lat": 9.7577, "lon": 105.6412, "name_vi": "Hậu Giang", "priority": 3},
    "Soc Trang": {"lat": 9.6025, "lon": 105.9738, "name_vi": "Sóc Trăng", "priority": 3},
    "Bac Lieu": {"lat": 9.2515, "lon": 105.7244, "name_vi": "Bạc Liêu", "priority": 3},
    "Ca Mau": {"lat": 9.1769, "lon": 105.1524, "name_vi": "Cà Mau", "priority": 3},
}

def get_cities_by_priority(priority: int = None):
    """Lấy danh sách tỉnh thành theo độ ưu tiên
    
    Args:
        priority: 1 = đã có data, 2 = ưu tiên cao, 3 = ưu tiên thấp
    """
    if priority is None:
        return VIETNAM_CITIES
    
    return {
        city: data for city, data in VIETNAM_CITIES.items()
        if data['priority'] == priority
    }

def get_cities_needing_data():
    """Lấy danh sách các tỉnh cần thu thập dữ liệu (priority 2, 3)"""
    return {
        city: data for city, data in VIETNAM_CITIES.items()
        if data['priority'] in [2, 3]
    }

# 8 tỉnh đã có dữ liệu chi tiết
CITIES_WITH_DATA = [city for city, data in VIETNAM_CITIES.items() if data['priority'] == 1]

# 48 tỉnh cần thu thập dữ liệu
CITIES_NEED_DATA = [city for city, data in VIETNAM_CITIES.items() if data['priority'] in [2, 3]]

print(f"✅ Tỉnh có dữ liệu: {len(CITIES_WITH_DATA)}")
print(f"⚠️  Tỉnh cần thu thập: {len(CITIES_NEED_DATA)}")
print(f"📊 Tổng: {len(VIETNAM_CITIES)}")

