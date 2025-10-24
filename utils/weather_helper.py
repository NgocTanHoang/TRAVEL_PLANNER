"""
Weather Helper - Simple weather recommendations
================================================
Cung cấp gợi ý thời tiết và chuẩn bị cho các thành phố Việt Nam
"""

from typing import Dict, Any
from datetime import datetime


# Weather data cho các thành phố chính
CITY_WEATHER = {
    'Hanoi': {
        'rainy_season': (5, 10),  # May - October
        'dry_season': (11, 4),
        'hot_months': (5, 8),
        'cool_months': (11, 2),
        'avg_temp': {'summer': 32, 'winter': 20},
        'avg_rain_days': {'rainy': 15, 'dry': 3},
        'uv_index': {'summer': 'Very High (9-11)', 'winter': 'Moderate (5-7)'}
    },
    'Ho Chi Minh City': {
        'rainy_season': (5, 11),
        'dry_season': (12, 4),
        'hot_months': (3, 5),
        'cool_months': None,  # Always warm
        'avg_temp': {'year_round': 28},
        'avg_rain_days': {'rainy': 20, 'dry': 2},
        'uv_index': {'year_round': 'Very High (10-11)'}
    },
    'Da Nang': {
        'rainy_season': (9, 12),
        'dry_season': (1, 8),
        'hot_months': (5, 8),
        'cool_months': (12, 2),
        'avg_temp': {'summer': 30, 'winter': 22},
        'avg_rain_days': {'rainy': 18, 'dry': 4},
        'uv_index': {'summer': 'Very High (10-11)', 'winter': 'High (7-9)'}
    },
    'Nha Trang': {
        'rainy_season': (9, 12),
        'dry_season': (1, 8),
        'hot_months': (4, 8),
        'cool_months': (12, 2),
        'avg_temp': {'summer': 30, 'winter': 24},
        'avg_rain_days': {'rainy': 15, 'dry': 2},
        'uv_index': {'year_round': 'Very High (9-11)'}
    },
    'Hue': {
        'rainy_season': (9, 1),
        'dry_season': (2, 8),
        'hot_months': (5, 8),
        'cool_months': (12, 2),
        'avg_temp': {'summer': 32, 'winter': 21},
        'avg_rain_days': {'rainy': 20, 'dry': 5},
        'uv_index': {'summer': 'Very High (10-11)', 'winter': 'High (7-8)'}
    },
    'Phu Quoc': {
        'rainy_season': (6, 10),
        'dry_season': (11, 5),
        'hot_months': (3, 5),
        'cool_months': None,
        'avg_temp': {'year_round': 28},
        'avg_rain_days': {'rainy': 18, 'dry': 2},
        'uv_index': {'year_round': 'Extreme (11+)'}
    },
    'Sapa': {
        'rainy_season': (5, 9),
        'dry_season': (10, 4),
        'hot_months': (6, 8),
        'cool_months': (12, 2),
        'avg_temp': {'summer': 22, 'winter': 10},
        'avg_rain_days': {'rainy': 20, 'dry': 5},
        'uv_index': {'year_round': 'High (7-9)'}
    },
    'Da Lat': {
        'rainy_season': (5, 10),
        'dry_season': (11, 4),
        'hot_months': None,  # Cool year-round
        'cool_months': (11, 2),
        'avg_temp': {'year_round': 18},
        'avg_rain_days': {'rainy': 18, 'dry': 4},
        'uv_index': {'year_round': 'High (7-9)'}
    }
}

# Normalize city names
CITY_ALIASES = {
    'hà nội': 'Hanoi',
    'hanoi': 'Hanoi',
    'hồ chí minh': 'Ho Chi Minh City',
    'tp.hcm': 'Ho Chi Minh City',
    'sài gòn': 'Ho Chi Minh City',
    'đà nẵng': 'Da Nang',
    'da nang': 'Da Nang',
    'nha trang': 'Nha Trang',
    'huế': 'Hue',
    'hue': 'Hue',
    'phú quốc': 'Phu Quoc',
    'phu quoc': 'Phu Quoc',
    'sapa': 'Sapa',
    'sa pa': 'Sapa',
    'đà lạt': 'Da Lat',
    'da lat': 'Da Lat',
    'dalat': 'Da Lat'
}


def normalize_city(city: str) -> str:
    """Normalize city name"""
    return CITY_ALIASES.get(city.lower().strip(), city)


def get_weather_recommendations(city: str, month: int = None) -> str:
    """
    Get weather recommendations for a city
    
    Args:
        city: City name
        month: Month (1-12), if None use current month
    
    Returns:
        Weather recommendation string
    """
    city_normalized = normalize_city(city)
    
    if city_normalized not in CITY_WEATHER:
        return f"📍 {city}: Thời tiết thông thường Việt Nam - Nên mang kem chống nắng và dù."
    
    if month is None:
        month = datetime.now().month
    
    weather = CITY_WEATHER[city_normalized]
    
    # Check season
    rainy = weather['rainy_season']
    is_rainy = _is_in_season(month, rainy[0], rainy[1])
    
    hot = weather.get('hot_months')
    is_hot = _is_in_season(month, hot[0], hot[1]) if hot else False
    
    cool = weather.get('cool_months')
    is_cool = _is_in_season(month, cool[0], cool[1]) if cool else False
    
    # Build recommendation
    parts = [f"🌤️ **THỜI TIẾT {city_normalized.upper()}** (Tháng {month}):"]
    
    # Season
    if is_rainy:
        rain_days = weather['avg_rain_days'].get('rainy', 15)
        parts.append(f"  • 🌧️ **Mùa mưa** - Khoảng {rain_days} ngày mưa/tháng")
        parts.append(f"  • ☔ **Khuyến cáo**: Mang dù, áo mưa")
    else:
        rain_days = weather['avg_rain_days'].get('dry', 3)
        parts.append(f"  • ☀️ **Mùa khô** - Ít mưa (~{rain_days} ngày/tháng)")
    
    # Temperature
    if is_hot:
        temp = weather['avg_temp'].get('summer', 30)
        parts.append(f"  • 🌡️ **Nhiệt độ**: ~{temp}°C (Nóng)")
    elif is_cool:
        temp = weather['avg_temp'].get('winter', 20)
        parts.append(f"  • 🌡️ **Nhiệt độ**: ~{temp}°C (Mát mẻ)")
    elif 'year_round' in weather['avg_temp']:
        temp = weather['avg_temp']['year_round']
        parts.append(f"  • 🌡️ **Nhiệt độ**: ~{temp}°C quanh năm")
    
    # Sunshine hours (estimate)
    if is_rainy:
        parts.append(f"  • ☀️ **Nắng**: 4-6 giờ/ngày")
    else:
        parts.append(f"  • ☀️ **Nắng**: 7-10 giờ/ngày")
    
    # UV Index
    if 'year_round' in weather['uv_index']:
        uv = weather['uv_index']['year_round']
    elif is_hot or (month >= 5 and month <= 8):
        uv = weather['uv_index'].get('summer', 'High')
    else:
        uv = weather['uv_index'].get('winter', 'Moderate')
    
    parts.append(f"  • ☢️ **Chỉ số UV**: {uv}")
    
    # Recommendations
    parts.append(f"\n  📦 **NÊN MANG:**")
    
    # Always
    if 'Extreme' in uv or 'Very High' in uv:
        parts.append(f"    ✓ Kem chống nắng SPF 50+++ (QUAN TRỌNG!)")
    elif 'High' in uv:
        parts.append(f"    ✓ Kem chống nắng SPF 30+")
    else:
        parts.append(f"    ✓ Kem chống nắng SPF 15+")
    
    # Conditional
    if is_rainy:
        parts.append(f"    ✓ Dù, áo mưa")
    
    if is_hot or 'Very High' in uv or 'Extreme' in uv:
        parts.append(f"    ✓ Mũ/nón rộng vành")
        parts.append(f"    ✓ Kính râm chống UV")
        parts.append(f"    ✓ Quần áo che kín, thoáng mát")
    
    if is_cool:
        parts.append(f"    ✓ Áo khoác nhẹ")
    
    return "\n".join(parts)


def _is_in_season(month: int, start: int, end: int) -> bool:
    """Check if month is in season"""
    if start <= end:
        return start <= month <= end
    else:  # Season crosses year boundary
        return month >= start or month <= end


# Test
if __name__ == "__main__":
    print("="*60)
    print("WEATHER HELPER - TEST")
    print("="*60)
    
    cities = ['Hà Nội', 'TP.HCM', 'Đà Nẵng', 'Sapa']
    months = [7, 12]
    
    for city in cities:
        for month in months:
            print(f"\n{get_weather_recommendations(city, month)}")
            print("-"*60)

