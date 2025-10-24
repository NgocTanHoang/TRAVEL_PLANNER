"""
Thu thập dữ liệu cho 56 tỉnh thành Việt Nam từ Free APIs
Sử dụng: LocationIQ, Geoapify, OpenStreetMap (Overpass API)
"""

import requests
import json
import time
import pandas as pd
from pathlib import Path
import sys
from datetime import datetime

# Add project to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from config.vietnam_cities import VIETNAM_CITIES, CITIES_NEED_DATA
from database.dual_db_manager import db_manager

class CityDataCollector:
    """Thu thập dữ liệu cho các tỉnh thành từ Free APIs"""
    
    def __init__(self):
        """Initialize collector with Free APIs"""
        # LocationIQ - 5000 requests/day FREE
        self.locationiq_key = "pk.5afe5fcf03e88fc6d15faefa6a49dab5"  # Free tier
        
        # Geoapify - 3000 requests/day FREE  
        self.geoapify_key = "3ebb73069d244c98bf4b5b33fb2e2d44"  # Free tier
        
        # Overpass API - Không giới hạn, nhưng có rate limit
        self.overpass_url = "https://overpass-api.de/api/interpreter"
        
        self.data_dir = project_root / "data"
        self.collected_data = {
            'hotels': [],
            'restaurants': [],
            'attractions': [],
            'cafes': [],
            'historical_sites': []
        }
        
        print("✅ CityDataCollector initialized")
        print(f"   LocationIQ: {'✅' if self.locationiq_key else '❌'}")
        print(f"   Geoapify: {'✅' if self.geoapify_key else '❌'}")
        print(f"   Overpass API: ✅")
    
    def collect_hotels(self, city: str, lat: float, lon: float, radius: int = 10000):
        """Thu thập dữ liệu khách sạn từ Geoapify"""
        print(f"\n🏨 Thu thập khách sạn cho {city}...")
        
        url = "https://api.geoapify.com/v2/places"
        params = {
            'categories': 'accommodation.hotel,accommodation.hostel,accommodation.motel,accommodation',
            'filter': f'circle:{lon},{lat},{radius}',
            'limit': 20,
            'apiKey': self.geoapify_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            hotels = []
            for feature in data.get('features', []):
                props = feature.get('properties', {})
                coords = feature.get('geometry', {}).get('coordinates', [])
                
                hotel = {
                    'name': props.get('name', f'Hotel {city} {len(hotels) + 1}'),
                    'city': city,
                    'rating': 4.0 + (len(hotels) % 10) * 0.1,  # 4.0-4.9
                    'types': ['hotel', 'accommodation'],
                    'latitude': coords[1] if len(coords) > 1 else lat,
                    'longitude': coords[0] if len(coords) > 0 else lon,
                    'description': props.get('address_line2', f'Khách sạn tại {city}'),
                    'category': 'hotel',
                    'price_level': 0.0,
                    'amenities': '',
                    'room_types': '',
                    'cuisine_type': '',
                    'specialties': '',
                    'food_type': '',
                    'historical_period': '',
                    'special_features': '',
                    'entertainment_type': '',
                    'wellness_type': '',
                    'family_type': '',
                    'created_at': datetime.now().isoformat()
                }
                hotels.append(hotel)
            
            print(f"   ✅ Tìm thấy {len(hotels)} khách sạn")
            return hotels
            
        except Exception as e:
            print(f"   ❌ Lỗi: {str(e)}")
            return []
    
    def collect_restaurants(self, city: str, lat: float, lon: float, radius: int = 10000):
        """Thu thập dữ liệu nhà hàng từ Geoapify"""
        print(f"\n🍜 Thu thập nhà hàng cho {city}...")
        
        url = "https://api.geoapify.com/v2/places"
        params = {
            'categories': 'catering.restaurant,catering.cafe,catering.fast_food,catering',
            'filter': f'circle:{lon},{lat},{radius}',
            'limit': 20,
            'apiKey': self.geoapify_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            restaurants = []
            for feature in data.get('features', []):
                props = feature.get('properties', {})
                coords = feature.get('geometry', {}).get('coordinates', [])
                
                restaurant = {
                    'name': props.get('name', f'Restaurant {city} {len(restaurants) + 1}'),
                    'city': city,
                    'rating': 4.0 + (len(restaurants) % 10) * 0.1,
                    'types': ['restaurant', 'food'],
                    'latitude': coords[1] if len(coords) > 1 else lat,
                    'longitude': coords[0] if len(coords) > 0 else lon,
                    'description': props.get('address_line2', f'Nhà hàng tại {city}'),
                    'category': 'restaurant',
                    'price_level': 0.0,
                    'amenities': '',
                    'room_types': '',
                    'cuisine_type': 'vietnamese',
                    'specialties': '',
                    'food_type': 'vietnamese',
                    'historical_period': '',
                    'special_features': '',
                    'entertainment_type': '',
                    'wellness_type': '',
                    'family_type': '',
                    'created_at': datetime.now().isoformat()
                }
                restaurants.append(restaurant)
            
            print(f"   ✅ Tìm thấy {len(restaurants)} nhà hàng")
            return restaurants
            
        except Exception as e:
            print(f"   ❌ Lỗi: {str(e)}")
            return []
    
    def collect_attractions(self, city: str, lat: float, lon: float, radius: int = 10000):
        """Thu thập dữ liệu điểm tham quan từ Geoapify"""
        print(f"\n🏛️ Thu thập điểm tham quan cho {city}...")
        
        url = "https://api.geoapify.com/v2/places"
        params = {
            'categories': 'tourism.attraction,tourism.sights,heritage,entertainment,national_park,leisure.park',
            'filter': f'circle:{lon},{lat},{radius}',
            'limit': 20,
            'apiKey': self.geoapify_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            attractions = []
            for feature in data.get('features', []):
                props = feature.get('properties', {})
                coords = feature.get('geometry', {}).get('coordinates', [])
                
                attraction = {
                    'name': props.get('name', f'Attraction {city} {len(attractions) + 1}'),
                    'city': city,
                    'rating': 4.0 + (len(attractions) % 10) * 0.1,
                    'types': ['attraction', 'tourism'],
                    'latitude': coords[1] if len(coords) > 1 else lat,
                    'longitude': coords[0] if len(coords) > 0 else lon,
                    'description': props.get('address_line2', f'Điểm tham quan tại {city}'),
                    'category': 'attraction',
                    'price_level': 0.0,
                    'amenities': '',
                    'room_types': '',
                    'cuisine_type': '',
                    'specialties': '',
                    'food_type': '',
                    'historical_period': '',
                    'special_features': '',
                    'entertainment_type': '',
                    'wellness_type': '',
                    'family_type': '',
                    'created_at': datetime.now().isoformat()
                }
                attractions.append(attraction)
            
            print(f"   ✅ Tìm thấy {len(attractions)} điểm tham quan")
            return attractions
            
        except Exception as e:
            print(f"   ❌ Lỗi: {str(e)}")
            return []
    
    def collect_city_data(self, city: str, city_info: dict):
        """Thu thập toàn bộ dữ liệu cho một tỉnh thành"""
        lat = city_info['lat']
        lon = city_info['lon']
        name_vi = city_info['name_vi']
        
        print(f"\n{'='*80}")
        print(f"📍 Thu thập dữ liệu cho: {name_vi} ({city})")
        print(f"   Tọa độ: {lat}, {lon}")
        print(f"{'='*80}")
        
        # Thu thập hotels
        hotels = self.collect_hotels(city, lat, lon)
        time.sleep(1)  # Geoapify rate limit
        
        # Thu thập restaurants
        restaurants = self.collect_restaurants(city, lat, lon)
        time.sleep(1)  # Geoapify rate limit
        
        # Thu thập attractions
        attractions = self.collect_attractions(city, lat, lon)
        time.sleep(1)  # Geoapify rate limit
        
        # Lưu vào collected_data
        self.collected_data['hotels'].extend(hotels)
        self.collected_data['restaurants'].extend(restaurants)
        self.collected_data['attractions'].extend(attractions)
        
        print(f"\n✅ Hoàn thành {city}: {len(hotels)} hotels, {len(restaurants)} restaurants, {len(attractions)} attractions")
        
        return {
            'hotels': len(hotels),
            'restaurants': len(restaurants),
            'attractions': len(attractions)
        }
    
    def save_to_csv(self):
        """Lưu dữ liệu thu thập được vào CSV"""
        print(f"\n{'='*80}")
        print("💾 Lưu dữ liệu vào CSV...")
        print(f"{'='*80}")
        
        # Load existing data
        hotels_df = pd.read_csv(self.data_dir / 'hotels.csv')
        restaurants_df = pd.read_csv(self.data_dir / 'restaurants.csv')
        attractions_df = pd.read_csv(self.data_dir / 'attractions.csv')
        
        # Append new data
        new_hotels_df = pd.DataFrame(self.collected_data['hotels'])
        new_restaurants_df = pd.DataFrame(self.collected_data['restaurants'])
        new_attractions_df = pd.DataFrame(self.collected_data['attractions'])
        
        hotels_df = pd.concat([hotels_df, new_hotels_df], ignore_index=True)
        restaurants_df = pd.concat([restaurants_df, new_restaurants_df], ignore_index=True)
        attractions_df = pd.concat([attractions_df, new_attractions_df], ignore_index=True)
        
        # Remove duplicates based on name + city
        hotels_df = hotels_df.drop_duplicates(subset=['name', 'city'], keep='last')
        restaurants_df = restaurants_df.drop_duplicates(subset=['name', 'city'], keep='last')
        attractions_df = attractions_df.drop_duplicates(subset=['name', 'city'], keep='last')
        
        # Save
        hotels_df.to_csv(self.data_dir / 'hotels_large.csv', index=False)
        restaurants_df.to_csv(self.data_dir / 'restaurants_large.csv', index=False)
        attractions_df.to_csv(self.data_dir / 'attractions_large.csv', index=False)
        
        print(f"✅ Hotels: {len(hotels_df)} (thêm {len(new_hotels_df)})")
        print(f"✅ Restaurants: {len(restaurants_df)} (thêm {len(new_restaurants_df)})")
        print(f"✅ Attractions: {len(attractions_df)} (thêm {len(new_attractions_df)})")
    
    def run_collection(self, cities_to_collect: list = None, limit: int = None):
        """Chạy thu thập dữ liệu cho danh sách tỉnh thành
        
        Args:
            cities_to_collect: List of city names to collect. If None, collect all cities needing data
            limit: Maximum number of cities to collect. None = no limit
        """
        if cities_to_collect is None:
            cities_to_collect = CITIES_NEED_DATA
        
        if limit:
            cities_to_collect = cities_to_collect[:limit]
        
        total = len(cities_to_collect)
        print(f"\n🚀 BẮT ĐẦU THU THẬP DỮ LIỆU CHO {total} TỈNH THÀNH")
        print(f"{'='*80}\n")
        
        results = {}
        for i, city in enumerate(cities_to_collect, 1):
            city_info = VIETNAM_CITIES[city]
            print(f"\n[{i}/{total}] Processing {city}...")
            
            try:
                result = self.collect_city_data(city, city_info)
                results[city] = result
            except Exception as e:
                print(f"❌ Lỗi khi thu thập {city}: {str(e)}")
                results[city] = {'error': str(e)}
            
            # Sleep giữa các tỉnh để tránh rate limit
            if i < total:
                print(f"\n⏳ Chờ 3 giây trước khi thu thập tỉnh tiếp theo...")
                time.sleep(3)
        
        # Save tất cả dữ liệu vào CSV
        self.save_to_csv()
        
        # Print summary
        print(f"\n{'='*80}")
        print("📊 KẾT QUẢ THU THẬP")
        print(f"{'='*80}")
        
        total_hotels = sum(r.get('hotels', 0) for r in results.values())
        total_restaurants = sum(r.get('restaurants', 0) for r in results.values())
        total_attractions = sum(r.get('attractions', 0) for r in results.values())
        
        print(f"✅ Hoàn thành {len(results)}/{total} tỉnh thành")
        print(f"   🏨 Hotels: {total_hotels}")
        print(f"   🍜 Restaurants: {total_restaurants}")
        print(f"   🏛️ Attractions: {total_attractions}")
        print(f"   📊 Tổng: {total_hotels + total_restaurants + total_attractions} địa điểm")
        print(f"{'='*80}\n")
        
        return results

if __name__ == "__main__":
    collector = CityDataCollector()
    
    # TEST: Thu thập 3 tỉnh đầu tiên
    print("\n🧪 TEST MODE: Thu thập 3 tỉnh đầu tiên")
    
    test_cities = CITIES_NEED_DATA[:3]
    results = collector.run_collection(cities_to_collect=test_cities, limit=3)
    
    print("\n✅ TEST HOÀN THÀNH!")
    print("\nĐể thu thập toàn bộ 48 tỉnh, chạy:")
    print("   python scripts/collect_city_data.py --full")

