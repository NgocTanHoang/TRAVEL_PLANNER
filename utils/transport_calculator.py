"""
Transport Cost Calculator
=========================
Tính chi phí di chuyển giữa các thành phố Việt Nam
"""

from typing import Dict, Tuple, Optional


# Distance matrix (km) - Khoảng cách đường bộ
DISTANCES = {
    ('Hà Nội', 'Hồ Chí Minh'): 1700,
    ('Hà Nội', 'Đà Nẵng'): 770,
    ('Hà Nội', 'Huế'): 660,
    ('Hà Nội', 'Nha Trang'): 1280,
    ('Hà Nội', 'Đà Lạt'): 1500,
    ('Hà Nội', 'Hội An'): 790,
    ('Hà Nội', 'Phú Quốc'): 1900,
    ('Hà Nội', 'Cần Thơ'): 1780,
    ('Hà Nội', 'Vũng Tàu'): 1670,
    ('Hà Nội', 'Đồng Nai'): 1680,
    ('Hà Nội', 'Binh Duong'): 1690,
    
    ('Hồ Chí Minh', 'Đà Nẵng'): 970,
    ('Hồ Chí Minh', 'Huế'): 1090,
    ('Hồ Chí Minh', 'Nha Trang'): 450,
    ('Hồ Chí Minh', 'Đà Lạt'): 310,
    ('Hồ Chí Minh', 'Hội An'): 920,
    ('Hồ Chí Minh', 'Phú Quốc'): 340,
    ('Hồ Chí Minh', 'Cần Thơ'): 170,
    ('Hồ Chí Minh', 'Vũng Tàu'): 125,
    ('Hồ Chí Minh', 'Đồng Nai'): 50,
    ('Hồ Chí Minh', 'Binh Duong'): 30,
    
    ('Đà Nẵng', 'Huế'): 100,
    ('Đà Nẵng', 'Hội An'): 30,
    ('Đà Nẵng', 'Nha Trang'): 540,
}

# Normalize city names
CITY_ALIASES = {
    'hanoi': 'Hà Nội',
    'hà nội': 'Hà Nội',
    'ha noi': 'Hà Nội',
    'hn': 'Hà Nội',
    
    'ho chi minh': 'Hồ Chí Minh',
    'hồ chí minh': 'Hồ Chí Minh',
    'tp hcm': 'Hồ Chí Minh',
    'tp.hcm': 'Hồ Chí Minh',
    'tphcm': 'Hồ Chí Minh',
    'hcm': 'Hồ Chí Minh',
    'sài gòn': 'Hồ Chí Minh',
    'saigon': 'Hồ Chí Minh',
    'sg': 'Hồ Chí Minh',
    
    'da nang': 'Đà Nẵng',
    'đà nẵng': 'Đà Nẵng',
    'đn': 'Đà Nẵng',
    
    'hue': 'Huế',
    'huế': 'Huế',
    
    'nha trang': 'Nha Trang',
    
    'da lat': 'Đà Lạt',
    'đà lạt': 'Đà Lạt',
    'dalat': 'Đà Lạt',
    
    'hoi an': 'Hội An',
    'hội an': 'Hội An',
    
    'phu quoc': 'Phú Quốc',
    'phú quốc': 'Phú Quốc',
    
    'can tho': 'Cần Thơ',
    'cần thơ': 'Cần Thơ',
    
    'vung tau': 'Vũng Tàu',
    'vũng tàu': 'Vũng Tàu',
    
    'dong nai': 'Đồng Nai',
    'đồng nai': 'Đồng Nai',
    
    'binh duong': 'Binh Duong',
    'bình dương': 'Binh Duong',
}


def normalize_city_name(city: str) -> str:
    """Normalize city name"""
    if not city:
        return city
    
    city_lower = city.lower().strip()
    return CITY_ALIASES.get(city_lower, city.strip())


def get_distance(city1: str, city2: str) -> Optional[int]:
    """Get distance between two cities in km"""
    c1 = normalize_city_name(city1)
    c2 = normalize_city_name(city2)
    
    # Same city
    if c1 == c2:
        return 0
    
    # Try both directions
    key1 = (c1, c2)
    key2 = (c2, c1)
    
    return DISTANCES.get(key1) or DISTANCES.get(key2)


def calculate_transport_cost(from_city: str, to_city: str, travelers: int = 1) -> Dict:
    """
    Tính chi phí di chuyển giữa 2 thành phố
    
    Args:
        from_city: Thành phố xuất phát
        to_city: Thành phố đến
        travelers: Số người
    
    Returns:
        Dict với transport options và costs
    """
    distance = get_distance(from_city, to_city)
    
    # Same city or unknown
    if distance is None:
        return {
            'distance': 0,
            'options': [],
            'min_cost': 0,
            'max_cost': 0,
            'recommended': 'local_transport',
            'note': f'Khoảng cách giữa {from_city} và {to_city} chưa có dữ liệu. Giả định du lịch tại chỗ.'
        }
    
    if distance == 0:
        # Du lịch tại chỗ - nhiều lựa chọn
        options = [
            {
                'type': 'Xe bus',
                'cost_per_person': 7000,  # ~7k VND/lượt
                'total_cost': 7000 * travelers * 4,  # 4 lượt/ngày
                'duration': 'Cả ngày',
                'note': 'Rẻ nhất - 4 lượt/ngày (~28k VND/người)'
            },
            {
                'type': 'Xe ôm công nghệ',
                'cost_per_person': 30000,
                'total_cost': 30000 * travelers * 3,  # 3 chuyến
                'duration': 'Cả ngày',
                'note': 'Tiện lợi - 3 chuyến/ngày (~90k VND/người)'
            },
            {
                'type': 'Taxi/Grab',
                'cost_per_person': 50000,
                'total_cost': 50000 * travelers * 3,  # 3 chuyến
                'duration': 'Cả ngày',
                'note': 'Thoải mái - 3 chuyến/ngày (~150k VND/người)'
            }
        ]
        
        return {
            'distance': 0,
            'options': options,
            'min_cost': 7000 * travelers * 4,  # Bus rẻ nhất
            'max_cost': 50000 * travelers * 3,  # Taxi đắt nhất
            'recommended': 'Xe bus',
            'note': 'Du lịch tại chỗ - xe bus rẻ nhất'
        }
    
    options = []
    
    # Flight (for distance > 300km)
    if distance > 300:
        flight_cost = max(1000000, distance * 0.8 * 1000)  # ~0.8k VND/km
        options.append({
            'type': 'Máy bay',
            'cost_per_person': int(flight_cost),
            'total_cost': int(flight_cost * travelers),
            'duration': f'{int(distance / 700) + 1} giờ',
            'note': 'Nhanh nhất'
        })
    
    # Train (for distance > 200km)
    if distance > 200:
        train_cost = distance * 0.3 * 1000  # ~0.3k VND/km
        options.append({
            'type': 'Tàu hỏa',
            'cost_per_person': int(train_cost),
            'total_cost': int(train_cost * travelers),
            'duration': f'{int(distance / 60) + 1} giờ',
            'note': 'Tiết kiệm, thoải mái'
        })
    
    # Bus (for distance > 50km)
    if distance > 50:
        bus_cost = distance * 0.15 * 1000  # ~0.15k VND/km
        options.append({
            'type': 'Xe khách',
            'cost_per_person': int(bus_cost),
            'total_cost': int(bus_cost * travelers),
            'duration': f'{int(distance / 50) + 1} giờ',
            'note': 'Rẻ nhất'
        })
    
    # Motorbike/Car (for short distance < 500km)
    if distance < 500:
        car_cost = distance * 0.2 * 1000 * travelers  # ~0.2k VND/km per person
        options.append({
            'type': 'Ô tô/Xe máy',
            'cost_per_person': int(car_cost / travelers),
            'total_cost': int(car_cost),
            'duration': f'{int(distance / 60) + 1} giờ',
            'note': 'Tự do, linh hoạt'
        })
    
    # Calculate min/max
    min_cost = min(opt['total_cost'] for opt in options) if options else 0
    max_cost = max(opt['total_cost'] for opt in options) if options else 0
    
    # Recommended option (cheapest for short, flight for long)
    if distance > 500:
        recommended = 'Máy bay'
    elif distance > 200:
        recommended = 'Tàu hỏa'
    else:
        recommended = 'Xe khách'
    
    return {
        'distance': distance,
        'options': sorted(options, key=lambda x: x['total_cost']),
        'min_cost': min_cost,
        'max_cost': max_cost,
        'recommended': recommended,
        'note': f'Khoảng cách: {distance}km'
    }


def validate_budget(
    total_budget: int,
    transport_cost: int,
    days: int,
    travelers: int
) -> Tuple[bool, str, Dict]:
    """
    Validate xem ngân sách có đủ không
    
    Returns:
        (is_valid, message, breakdown)
    """
    remaining = total_budget - transport_cost
    
    # Estimate minimum costs per day per person
    min_hotel_per_day = 200000  # 200k/night
    min_food_per_day = 150000   # 150k/day for 3 meals
    min_activities = 100000      # 100k/day for activities
    
    min_cost_per_day = min_hotel_per_day + min_food_per_day + min_activities
    min_total_needed = transport_cost + (min_cost_per_day * days * travelers)
    
    if total_budget < min_total_needed:
        shortage = min_total_needed - total_budget
        # Vẫn return breakdown để hiển thị
        budget_per_day = remaining / days if remaining > 0 else 0
        
        return (
            False,
            f"⚠️ Ngân sách không đủ! Cần thêm tối thiểu {shortage:,} VND.\n"
            f"Chi phí di chuyển: {transport_cost:,} VND\n"
            f"Chi phí tối thiểu tại điểm đến: {(min_cost_per_day * days * travelers):,} VND\n"
            f"Tổng cần: {min_total_needed:,} VND",
            {
                'transport': transport_cost,
                'remaining': remaining,
                'per_day': int(budget_per_day) if budget_per_day > 0 else 0,
                'hotel': 0,
                'food': 0,
                'activities': 0,
                'misc': 0,
                'shortage': shortage
            }
        )
    
    # Calculate budget breakdown
    budget_per_day = remaining / days
    
    breakdown = {
        'transport': transport_cost,
        'remaining': remaining,
        'per_day': int(budget_per_day),
        'hotel': int(budget_per_day * 0.4),
        'food': int(budget_per_day * 0.3),
        'activities': int(budget_per_day * 0.2),
        'misc': int(budget_per_day * 0.1)
    }
    
    return (True, "✅ Ngân sách phù hợp!", breakdown)


# Test
if __name__ == "__main__":
    print("="*60)
    print("TRANSPORT COST CALCULATOR - TEST")
    print("="*60)
    
    # Test 1: Hà Nội → Đồng Nai
    print("\n1️⃣ Hà Nội → Đồng Nai (1 người):")
    result = calculate_transport_cost("Hà Nội", "Đồng Nai", 1)
    print(f"   Khoảng cách: {result['distance']}km")
    print(f"   Chi phí: {result['min_cost']:,} - {result['max_cost']:,} VND")
    print(f"   Gợi ý: {result['recommended']}")
    
    valid, msg, breakdown = validate_budget(1000000, result['min_cost'], 1, 1)
    print(f"\n   Budget 1M VND: {msg}")
    
    # Test 2: TP.HCM → Đồng Nai
    print("\n2️⃣ TP.HCM → Đồng Nai (1 người):")
    result = calculate_transport_cost("TP.HCM", "Đồng Nai", 1)
    print(f"   Khoảng cách: {result['distance']}km")
    print(f"   Chi phí: {result['min_cost']:,} - {result['max_cost']:,} VND")
    print(f"   Gợi ý: {result['recommended']}")
    
    valid, msg, breakdown = validate_budget(1000000, result['min_cost'], 1, 1)
    print(f"\n   Budget 1M VND: {msg}")
    if valid:
        print(f"   Còn lại: {breakdown['remaining']:,} VND")
        print(f"   Hotel: {breakdown['hotel']:,} VND")
        print(f"   Food: {breakdown['food']:,} VND")
    
    print("\n" + "="*60)

