import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import re
import json
from dataclasses import asdict

class DataProcessor:
    def __init__(self):
        """Khởi tạo Data Processor"""
        self.vietnamese_cities = [
            'Hồ Chí Minh', 'Hà Nội', 'Đà Nẵng', 'Hải Phòng', 'Cần Thơ',
            'Huế', 'Nha Trang', 'Vũng Tàu', 'Quy Nhon', 'Hội An',
            'Phan Thiết', 'Đà Lạt', 'Sapa', 'Hạ Long', 'Ninh Bình'
        ]
        
        self.place_categories = {
            'tourist_attraction': 'Địa điểm du lịch',
            'museum': 'Bảo tàng',
            'park': 'Công viên',
            'temple': 'Chùa/Đền',
            'market': 'Chợ',
            'restaurant': 'Nhà hàng',
            'hotel': 'Khách sạn',
            'shopping_mall': 'Trung tâm thương mại',
            'historical_site': 'Di tích lịch sử',
            'natural_feature': 'Cảnh quan thiên nhiên'
        }
        
        self.cuisine_types = {
            'vietnamese': 'Ẩm thực Việt Nam',
            'chinese': 'Ẩm thực Trung Hoa',
            'japanese': 'Ẩm thực Nhật Bản',
            'korean': 'Ẩm thực Hàn Quốc',
            'thai': 'Ẩm thực Thái Lan',
            'french': 'Ẩm thực Pháp',
            'italian': 'Ẩm thực Ý',
            'american': 'Ẩm thực Mỹ',
            'seafood': 'Hải sản',
            'street_food': 'Đồ ăn đường phố'
        }
    
    def clean_text(self, text: str) -> str:
        """Làm sạch text data"""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove special characters but keep Vietnamese characters
        text = re.sub(r'[^\w\sàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđĐ]', '', text)
        
        return text
    
    def normalize_rating(self, rating: Any) -> float:
        """Chuẩn hóa rating về thang điểm 5"""
        if not rating:
            return 0.0
        
        try:
            rating = float(rating)
            # Nếu rating > 5, chia cho 2 (từ thang 10 về 5)
            if rating > 5:
                rating = rating / 2
            return min(max(rating, 0.0), 5.0)
        except (ValueError, TypeError):
            return 0.0
    
    def normalize_price(self, price: Any, currency: str = 'USD') -> float:
        """Chuẩn hóa giá về USD"""
        if not price:
            return 0.0
        
        try:
            price = float(price)
            
            # Convert VND to USD (approximate rate: 1 USD = 24,000 VND)
            if currency.upper() == 'VND':
                price = price / 24000
            elif currency.upper() == 'EUR':
                price = price * 1.1  # Approximate EUR to USD
            
            return round(price, 2)
        except (ValueError, TypeError):
            return 0.0
    
    def extract_coordinates(self, location_data: Dict[str, Any]) -> Tuple[float, float]:
        """Trích xuất tọa độ từ location data"""
        lat = location_data.get('latitude', location_data.get('lat', 0))
        lng = location_data.get('longitude', location_data.get('lng', location_data.get('lon', 0)))
        
        try:
            return float(lat), float(lng)
        except (ValueError, TypeError):
            return 0.0, 0.0
    
    def categorize_place(self, place_data: Dict[str, Any]) -> str:
        """Phân loại địa điểm"""
        name = place_data.get('name', '').lower()
        types = place_data.get('types', [])
        
        # Check by types first
        for place_type, category in self.place_categories.items():
            if place_type in types:
                return category
        
        # Check by name keywords
        if any(keyword in name for keyword in ['chợ', 'market']):
            return 'Chợ'
        elif any(keyword in name for keyword in ['chùa', 'temple', 'pagoda']):
            return 'Chùa/Đền'
        elif any(keyword in name for keyword in ['bảo tàng', 'museum']):
            return 'Bảo tàng'
        elif any(keyword in name for keyword in ['công viên', 'park']):
            return 'Công viên'
        elif any(keyword in name for keyword in ['hồ', 'lake']):
            return 'Cảnh quan thiên nhiên'
        
        return 'Địa điểm du lịch'
    
    def categorize_cuisine(self, restaurant_data: Dict[str, Any]) -> str:
        """Phân loại ẩm thực"""
        cuisine = restaurant_data.get('cuisine', '').lower()
        name = restaurant_data.get('name', '').lower()
        
        # Check cuisine field
        for cuisine_type, category in self.cuisine_types.items():
            if cuisine_type in cuisine:
                return category
        
        # Check by name keywords
        if any(keyword in name for keyword in ['phở', 'bún', 'bánh']):
            return 'Ẩm thực Việt Nam'
        elif any(keyword in name for keyword in ['sushi', 'ramen']):
            return 'Ẩm thực Nhật Bản'
        elif any(keyword in name for keyword in ['kimchi', 'korean']):
            return 'Ẩm thực Hàn Quốc'
        elif any(keyword in name for keyword in ['pizza', 'pasta']):
            return 'Ẩm thực Ý'
        
        return 'Ẩm thực Việt Nam'
    
    def process_places_data(self, places_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Xử lý dữ liệu địa điểm"""
        processed_places = []
        
        for place in places_data:
            processed_place = {
                'place_id': place.get('place_id', ''),
                'name': self.clean_text(place.get('name', '')),
                'city': place.get('city', ''),
                'address': self.clean_text(place.get('address', '')),
                'latitude': self.extract_coordinates(place)[0],
                'longitude': self.extract_coordinates(place)[1],
                'rating': self.normalize_rating(place.get('rating', 0)),
                'price_level': place.get('price_level', 0),
                'types': place.get('types', []),
                'photos': place.get('photos', []),
                'category': self.categorize_place(place),
                'processed_at': datetime.now().isoformat()
            }
            processed_places.append(processed_place)
        
        return processed_places
    
    def process_hotels_data(self, hotels_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Xử lý dữ liệu khách sạn"""
        processed_hotels = []
        
        for hotel in hotels_data:
            processed_hotel = {
                'hotel_id': hotel.get('hotel_id', ''),
                'name': self.clean_text(hotel.get('name', '')),
                'city': hotel.get('city', ''),
                'address': self.clean_text(hotel.get('address', '')),
                'rating': self.normalize_rating(hotel.get('rating', 0)),
                'price_per_night': self.normalize_price(
                    hotel.get('price_per_night', 0),
                    hotel.get('currency', 'USD')
                ),
                'currency': 'USD',
                'amenities': hotel.get('amenities', []),
                'availability': hotel.get('availability', {}),
                'star_rating': self._estimate_star_rating(hotel),
                'processed_at': datetime.now().isoformat()
            }
            processed_hotels.append(processed_hotel)
        
        return processed_hotels
    
    def process_restaurants_data(self, restaurants_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Xử lý dữ liệu nhà hàng"""
        processed_restaurants = []
        
        for restaurant in restaurants_data:
            processed_restaurant = {
                'restaurant_id': restaurant.get('restaurant_id', ''),
                'name': self.clean_text(restaurant.get('name', '')),
                'city': restaurant.get('city', ''),
                'address': self.clean_text(restaurant.get('address', '')),
                'cuisine': self.categorize_cuisine(restaurant),
                'rating': self.normalize_rating(restaurant.get('rating', 0)),
                'price_range': restaurant.get('price_range', '$'),
                'hours': restaurant.get('hours', {}),
                'menu': restaurant.get('menu', []),
                'popularity_score': self._calculate_popularity_score(restaurant),
                'processed_at': datetime.now().isoformat()
            }
            processed_restaurants.append(processed_restaurant)
        
        return processed_restaurants
    
    def process_weather_data(self, weather_data: Dict[str, Any]) -> Dict[str, Any]:
        """Xử lý dữ liệu thời tiết"""
        if not weather_data:
            return {}
        
        processed_weather = {
            'city': weather_data.get('city', ''),
            'temperature': float(weather_data.get('temperature', 0)),
            'feels_like': float(weather_data.get('feels_like', 0)),
            'humidity': int(weather_data.get('humidity', 0)),
            'pressure': int(weather_data.get('pressure', 0)),
            'description': self.clean_text(weather_data.get('description', '')),
            'wind_speed': float(weather_data.get('wind_speed', 0)),
            'visibility': int(weather_data.get('visibility', 0)),
            'comfort_index': self._calculate_comfort_index(weather_data),
            'processed_at': datetime.now().isoformat()
        }
        
        return processed_weather
    
    def _estimate_star_rating(self, hotel_data: Dict[str, Any]) -> int:
        """Ước tính sao khách sạn dựa trên rating và amenities"""
        rating = hotel_data.get('rating', 0)
        amenities = hotel_data.get('amenities', [])
        
        # Base star rating from rating
        if rating >= 4.5:
            base_stars = 5
        elif rating >= 4.0:
            base_stars = 4
        elif rating >= 3.5:
            base_stars = 3
        elif rating >= 3.0:
            base_stars = 2
        else:
            base_stars = 1
        
        # Adjust based on amenities
        luxury_amenities = ['spa', 'pool', 'gym', 'restaurant', 'bar']
        luxury_count = sum(1 for amenity in amenities if any(lux in amenity.lower() for lux in luxury_amenities))
        
        if luxury_count >= 4:
            base_stars = min(base_stars + 1, 5)
        
        return base_stars
    
    def _calculate_popularity_score(self, restaurant_data: Dict[str, Any]) -> float:
        """Tính điểm độ phổ biến của nhà hàng"""
        rating = restaurant_data.get('rating', 0)
        price_range = restaurant_data.get('price_range', '$')
        
        # Base score from rating
        popularity_score = rating * 20  # Convert to 0-100 scale
        
        # Adjust based on price range (more expensive = more popular)
        price_multiplier = len(price_range) * 0.1
        popularity_score *= (1 + price_multiplier)
        
        return min(popularity_score, 100.0)
    
    def _calculate_comfort_index(self, weather_data: Dict[str, Any]) -> float:
        """Tính chỉ số thoải mái thời tiết"""
        temp = weather_data.get('temperature', 25)
        humidity = weather_data.get('humidity', 50)
        wind_speed = weather_data.get('wind_speed', 0)
        
        # Optimal temperature range: 20-28°C
        temp_score = 100 - abs(temp - 24) * 5
        temp_score = max(0, min(100, temp_score))
        
        # Optimal humidity: 40-70%
        humidity_score = 100 - abs(humidity - 55) * 2
        humidity_score = max(0, min(100, humidity_score))
        
        # Wind speed bonus (light breeze is good)
        wind_score = min(100, wind_speed * 10)
        
        # Weighted average
        comfort_index = (temp_score * 0.5 + humidity_score * 0.3 + wind_score * 0.2)
        
        return round(comfort_index, 1)
    
    def merge_data_sources(self, api_data: Dict[str, Any], scraped_data: Dict[str, Any]) -> Dict[str, Any]:
        """Kết hợp dữ liệu từ API và web scraping"""
        merged_data = {
            'city': api_data.get('city', scraped_data.get('city', '')),
            'timestamp': datetime.now().isoformat(),
            'places': [],
            'hotels': [],
            'restaurants': [],
            'weather': {},
            'reviews': [],
            'travel_guides': []
        }
        
        # Merge places (prioritize API data)
        api_places = api_data.get('places', [])
        scraped_attractions = scraped_data.get('attractions', [])
        
        # Add API places
        merged_data['places'].extend(api_places)
        
        # Add scraped attractions (avoid duplicates)
        existing_names = {place['name'] for place in api_places}
        for attraction in scraped_attractions:
            if attraction['name'] not in existing_names:
                # Convert scraped attraction to place format
                place = {
                    'place_id': f"scraped_{attraction['name'].replace(' ', '_').lower()}",
                    'name': attraction['name'],
                    'city': merged_data['city'],
                    'address': attraction.get('address', ''),
                    'latitude': 0,  # Will be geocoded later
                    'longitude': 0,
                    'rating': attraction.get('rating', 0),
                    'price_level': 0,
                    'types': [attraction.get('category', 'tourist_attraction')],
                    'photos': [],
                    'source': 'scraped'
                }
                merged_data['places'].append(place)
        
        # Merge hotels
        api_hotels = api_data.get('hotels', [])
        scraped_hotels = scraped_data.get('hotels', [])
        
        merged_data['hotels'].extend(api_hotels)
        merged_data['hotels'].extend(scraped_hotels)
        
        # Merge restaurants
        api_restaurants = api_data.get('restaurants', [])
        merged_data['restaurants'].extend(api_restaurants)
        
        # Merge weather (prioritize API data)
        merged_data['weather'] = api_data.get('weather', scraped_data.get('weather', {}))
        
        # Add scraped data
        merged_data['reviews'] = scraped_data.get('restaurant_reviews', [])
        merged_data['travel_guides'] = scraped_data.get('travel_guides', [])
        
        return merged_data
    
    def generate_data_summary(self, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Tạo tóm tắt dữ liệu đã xử lý"""
        summary = {
            'city': processed_data.get('city', ''),
            'total_places': len(processed_data.get('places', [])),
            'total_hotels': len(processed_data.get('hotels', [])),
            'total_restaurants': len(processed_data.get('restaurants', [])),
            'has_weather': bool(processed_data.get('weather')),
            'total_reviews': len(processed_data.get('reviews', [])),
            'total_guides': len(processed_data.get('travel_guides', [])),
            'data_quality_score': self._calculate_data_quality_score(processed_data),
            'processed_at': datetime.now().isoformat()
        }
        
        return summary
    
    def _calculate_data_quality_score(self, data: Dict[str, Any]) -> float:
        """Tính điểm chất lượng dữ liệu"""
        score = 0
        max_score = 100
        
        # Places quality (30 points)
        places = data.get('places', [])
        if places:
            places_with_coords = sum(1 for p in places if p.get('latitude') and p.get('longitude'))
            places_with_rating = sum(1 for p in places if p.get('rating', 0) > 0)
            score += (places_with_coords / len(places)) * 15
            score += (places_with_rating / len(places)) * 15
        
        # Hotels quality (25 points)
        hotels = data.get('hotels', [])
        if hotels:
            hotels_with_price = sum(1 for h in hotels if h.get('price_per_night', 0) > 0)
            hotels_with_rating = sum(1 for h in hotels if h.get('rating', 0) > 0)
            score += (hotels_with_price / len(hotels)) * 12.5
            score += (hotels_with_rating / len(hotels)) * 12.5
        
        # Restaurants quality (25 points)
        restaurants = data.get('restaurants', [])
        if restaurants:
            restaurants_with_rating = sum(1 for r in restaurants if r.get('rating', 0) > 0)
            restaurants_with_cuisine = sum(1 for r in restaurants if r.get('cuisine'))
            score += (restaurants_with_rating / len(restaurants)) * 12.5
            score += (restaurants_with_cuisine / len(restaurants)) * 12.5
        
        # Weather quality (10 points)
        if data.get('weather'):
            weather = data['weather']
            if weather.get('temperature') and weather.get('humidity'):
                score += 10
        
        # Reviews quality (10 points)
        reviews = data.get('reviews', [])
        if reviews:
            reviews_with_text = sum(1 for r in reviews if r.get('review_text'))
            score += (reviews_with_text / len(reviews)) * 10
        
        return round(score, 1)

