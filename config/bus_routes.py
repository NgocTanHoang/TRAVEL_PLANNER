"""
Database tuyến xe buýt cho các tỉnh thành Việt Nam
"""

# Tuyến xe buýt phổ biến cho du lịch
BUS_ROUTES = {
    "Hồ Chí Minh": {
        "routes": {
            "01": {
                "name": "Bến Thành - Chợ Lớn",
                "points": ["Chợ Bến Thành", "Bưu điện", "Nhà thờ Đức Bà", "Dinh Độc Lập", "Chợ Lớn"],
                "price": 7000
            },
            "04": {
                "name": "Bến Thành - Bình Tây",
                "points": ["Chợ Bến Thành", "Trần Hưng Đạo", "An Đông", "Chợ Bình Tây"],
                "price": 7000
            },
            "36": {
                "name": "Bến Xe Miền Đông - Bến Thành",
                "points": ["Bến Xe Miền Đông", "Trần Hưng Đạo", "Chợ Bến Thành"],
                "price": 7000
            },
            "93": {
                "name": "Sân bay Tân Sơn Nhất - Bến Thành",
                "points": ["Sân bay", "Công viên Hoàng Văn Thụ", "Bảo tàng", "Chợ Bến Thành"],
                "price": 20000
            }
        },
        "note": "Vé 7,000 VND/lượt, xe buýt 93 sân bay 20,000 VND"
    },
    
    "Hà Nội": {
        "routes": {
            "09": {
                "name": "Kim Mã - Bến xe Giáp Bát",
                "points": ["Kim Mã", "Văn Miếu", "Hoàng Cầu", "Bến xe Giáp Bát"],
                "price": 7000
            },
            "14": {
                "name": "Long Biên - Bến xe Mỹ Đình",
                "points": ["Long Biên", "Hồ Gươm", "Nhà Hát Lớn", "Mỹ Đình"],
                "price": 7000
            },
            "86": {
                "name": "Sân bay Nội Bài - Bến xe Nước Ngầm",
                "points": ["Sân bay Nội Bài", "Mỹ Đình", "Kim Mã", "Nước Ngầm"],
                "price": 45000
            }
        },
        "note": "Vé 7,000 VND/lượt, xe buýt 86 sân bay 45,000 VND"
    },
    
    "Đà Nẵng": {
        "routes": {
            "01": {
                "name": "Bệnh viện C - Bãi biển Mỹ Khê",
                "points": ["Bệnh viện C", "Chợ Hàn", "Cầu Rồng", "Bãi biển Mỹ Khê"],
                "price": 6000
            },
            "03": {
                "name": "Bến xe trung tâm - Hội An",
                "points": ["Bến xe", "Ngã tư 2/9", "Hội An"],
                "price": 25000
            }
        },
        "note": "Vé 6,000-7,000 VND/lượt"
    },
    
    "Nha Trang": {
        "routes": {
            "04": {
                "name": "Bến xe phía Nam - Tháp Bà",
                "points": ["Bến xe phía Nam", "Chợ Đầm", "Bãi biển", "Tháp Bà"],
                "price": 7000
            }
        },
        "note": "Vé 7,000 VND/lượt"
    },
    
    "Cần Thơ": {
        "routes": {
            "01": {
                "name": "Bến Ninh Kiều - Cần Thơ",
                "points": ["Bến Ninh Kiều", "Chợ Cần Thơ", "ĐH Cần Thơ"],
                "price": 6000
            }
        },
        "note": "Vé 6,000 VND/lượt"
    },
    
    # Default for other cities
    "_default": {
        "routes": {},
        "note": "Di chuyển bằng xe ôm, taxi, hoặc xe bus địa phương (~7,000-10,000 VND/lượt)"
    }
}

def get_bus_info(city: str) -> dict:
    """
    Lấy thông tin xe buýt cho thành phố
    
    Args:
        city: Tên thành phố
        
    Returns:
        Dict with routes and pricing info
    """
    # Normalize city name
    city_map = {
        'ho chi minh city': 'Hồ Chí Minh',
        'tp.hcm': 'Hồ Chí Minh',
        'tphcm': 'Hồ Chí Minh',
        'saigon': 'Hồ Chí Minh',
        'hanoi': 'Hà Nội',
        'da nang': 'Đà Nẵng',
        'nha trang': 'Nha Trang',
        'can tho': 'Cần Thơ'
    }
    
    normalized = city_map.get(city.lower(), city)
    return BUS_ROUTES.get(normalized, BUS_ROUTES['_default'])


def suggest_bus_route(city: str, from_point: str = None, to_point: str = None) -> str:
    """
    Gợi ý tuyến xe buýt phù hợp
    
    Returns:
        String with bus route suggestions
    """
    bus_info = get_bus_info(city)
    
    if not bus_info['routes']:
        return bus_info['note']
    
    suggestions = []
    for route_num, route_data in bus_info['routes'].items():
        suggestions.append(
            f"Xe buýt số {route_num}: {route_data['name']} ({route_data['price']:,} VND)"
        )
    
    result = "\n".join(suggestions)
    result += f"\n\n💡 {bus_info['note']}"
    
    return result


# Test
if __name__ == "__main__":
    print("="*60)
    print("TEST: Bus Routes Database")
    print("="*60)
    
    cities = ["Hồ Chí Minh", "Hà Nội", "Đà Nẵng", "Đồng Nai"]
    
    for city in cities:
        print(f"\n🚌 {city}:")
        print(suggest_bus_route(city))

