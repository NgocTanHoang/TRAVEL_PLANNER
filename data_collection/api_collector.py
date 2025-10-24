import requests
import json
import time
import sqlite3
import hashlib
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
try:
    load_dotenv()
except:
    pass

class APICollector:
    def __init__(self):
        """Khởi tạo API Collector với caching"""
        self.api_keys = {
            'google_places': os.getenv('GOOGLE_PLACES_API_KEY'),
            'openweather': os.getenv('OPENWEATHER_API_KEY'),
            'foursquare': os.getenv('FOURSQUARE_API_KEY'),
            'tavily': os.getenv('TAVILY_API_KEY')
        }
        
        self.base_urls = {
            'google_places': 'https://maps.googleapis.com/maps/api/place',
            'openweather': 'https://api.openweathermap.org/data/2.5',
            'foursquare': 'https://api.foursquare.com/v3/places',
            'tavily': 'https://api.tavily.com'
        }
        
        self.rate_limits = {
            'google_places': {'requests_per_second': 10, 'requests_per_day': 100000},
            'openweather': {'requests_per_second': 60, 'requests_per_day': 1000000},
            'foursquare': {'requests_per_second': 500, 'requests_per_day': 100000},
            'tavily': {'requests_per_second': 10, 'requests_per_day': 1000}
        }
        
        self.request_counts = {api: 0 for api in self.rate_limits.keys()}
        self.last_request_time = {api: datetime.now() for api in self.rate_limits.keys()}
        
        # Initialize cache database
        self.cache_db = "api_cache.db"
        self._init_cache_db()
    
    def _init_cache_db(self):
        """Initialize cache database"""
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_cache (
                cache_key TEXT PRIMARY KEY,
                api_name TEXT,
                endpoint TEXT,
                response_data TEXT,
                created_at TIMESTAMP,
                expires_at TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
    
    def _generate_cache_key(self, api_name: str, endpoint: str, params: Dict[str, Any]) -> str:
        """Generate cache key for API request"""
        key_string = f"{api_name}:{endpoint}:{json.dumps(params, sort_keys=True)}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _get_cached_response(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Get cached API response"""
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT response_data, expires_at FROM api_cache 
            WHERE cache_key = ? AND expires_at > ?
        ''', (cache_key, datetime.now()))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return json.loads(result[0])
        return None
    
    def _cache_response(self, cache_key: str, api_name: str, endpoint: str, 
                       response_data: Dict[str, Any], cache_duration_hours: int = 24):
        """Cache API response"""
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        
        expires_at = datetime.now() + timedelta(hours=cache_duration_hours)
        
        cursor.execute('''
            INSERT OR REPLACE INTO api_cache 
            (cache_key, api_name, endpoint, response_data, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (cache_key, api_name, endpoint, json.dumps(response_data), 
              datetime.now(), expires_at))
        
        conn.commit()
        conn.close()
    
    def _rate_limit_check(self, api_name: str) -> bool:
        """Kiểm tra rate limit cho API"""
        now = datetime.now()
        time_diff = (now - self.last_request_time[api_name]).total_seconds()
        
        # Reset counter nếu đã qua 1 giây
        if time_diff >= 1:
            self.request_counts[api_name] = 0
        
        # Kiểm tra rate limit
        if self.request_counts[api_name] >= self.rate_limits[api_name]['requests_per_second']:
            sleep_time = 1 - time_diff
            if sleep_time > 0:
                time.sleep(sleep_time)
                self.request_counts[api_name] = 0
        
        self.request_counts[api_name] += 1
        self.last_request_time[api_name] = now
        return True
    
    def _make_api_request(self, api_name: str, endpoint: str, params: Dict[str, Any], 
                         cache_duration_hours: int = 24) -> Optional[Dict[str, Any]]:
        """Thực hiện API request với caching"""
        # Generate cache key
        cache_key = self._generate_cache_key(api_name, endpoint, params)
        
        # Check cache first
        cached_response = self._get_cached_response(cache_key)
        if cached_response:
            print(f"Cache hit for {api_name}:{endpoint}")
            return cached_response
        
        # Check rate limit
        if not self._rate_limit_check(api_name):
            print(f"Rate limit exceeded for {api_name}")
            return None
        
        # Make API request
        api_key = self.api_keys.get(api_name)
        if not api_key:
            print(f"API key not found for {api_name}")
            return None
        
        params['key'] = api_key
        url = f"{self.base_urls[api_name]}/{endpoint}"
        
        try:
            print(f"Making API request to {api_name}:{endpoint}")
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            response_data = response.json()
            
            # Cache the response
            self._cache_response(cache_key, api_name, endpoint, response_data, cache_duration_hours)
            print(f"API request successful, cached for {cache_duration_hours}h")
            
            return response_data
            
        except requests.exceptions.RequestException as e:
            print(f"API request failed for {api_name}: {e}")
            return None
    
    def collect_places_data(self, city: str, radius: int = 5000) -> Dict[str, Any]:
        """Collect places data from Google Places API or real CSV data"""
        print(f"Collecting places data for {city}")
        
        # Check if API key is available
        if not self.api_keys.get('google_places'):
            print("Google Places API key not found, using real CSV data")
            return self._get_real_csv_data(city)
        
        # Search for places in the city
        places_data = {
            'hotels': [],
            'restaurants': [],
            'attractions': [],
            'city': city,
            'collected_at': datetime.now().isoformat()
        }
        
        # Search for hotels
        hotel_params = {
            'query': f'hotels in {city}',
            'type': 'lodging',
            'radius': radius
        }
        
        hotel_response = self._make_api_request('google_places', 'textsearch/json', hotel_params)
        if hotel_response and 'results' in hotel_response:
            places_data['hotels'] = hotel_response['results'][:10]  # Limit to 10
        
        # Search for restaurants
        restaurant_params = {
            'query': f'restaurants in {city}',
            'type': 'restaurant',
            'radius': radius
        }
        
        restaurant_response = self._make_api_request('google_places', 'textsearch/json', restaurant_params)
        if restaurant_response and 'results' in restaurant_response:
            places_data['restaurants'] = restaurant_response['results'][:10]
        
        # Search for attractions
        attraction_params = {
            'query': f'tourist attractions in {city}',
            'type': 'tourist_attraction',
            'radius': radius
        }
        
        attraction_response = self._make_api_request('google_places', 'textsearch/json', attraction_params)
        if attraction_response and 'results' in attraction_response:
            places_data['attractions'] = attraction_response['results'][:10]
        
        print(f"Collected {len(places_data['hotels'])} hotels, {len(places_data['restaurants'])} restaurants, {len(places_data['attractions'])} attractions")
        return places_data
    
    def _get_real_csv_data(self, city: str) -> Dict[str, Any]:
        """Get real data from CSV files instead of mock data"""
        try:
            # Import real data provider
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            
            from real_data_provider import RealDataProvider
            
            # Initialize data provider
            data_provider = RealDataProvider()
            
            # Get real places data
            places_data = data_provider.get_places_data(city)
            
            print(f"Using real CSV data: {len(places_data['hotels'])} hotels, {len(places_data['restaurants'])} restaurants, {len(places_data['attractions'])} attractions")
            return places_data
            
        except Exception as e:
            print(f"Error loading real CSV data: {e}, falling back to mock data")
            return self._get_mock_places_data(city)
    
    def _get_mock_places_data(self, city: str) -> Dict[str, Any]:
        """Get mock places data when API key is not available"""
        return {
            'hotels': [
                {
                    'name': f'Hotel Central {city}',
                    'rating': 4.5,
                    'price_level': 3,
                    'vicinity': f'Downtown {city}',
                    'place_id': 'mock_hotel_1'
                },
                {
                    'name': f'Grand Plaza {city}',
                    'rating': 4.2,
                    'price_level': 4,
                    'vicinity': f'City Center {city}',
                    'place_id': 'mock_hotel_2'
                }
            ],
            'restaurants': [
                {
                    'name': f'Local Cuisine {city}',
                    'rating': 4.3,
                    'price_level': 2,
                    'vicinity': f'Old Quarter {city}',
                    'place_id': 'mock_restaurant_1'
                },
                {
                    'name': f'Street Food {city}',
                    'rating': 4.6,
                    'price_level': 1,
                    'vicinity': f'Market Area {city}',
                    'place_id': 'mock_restaurant_2'
                }
            ],
            'attractions': [
                {
                    'name': f'{city} Museum',
                    'rating': 4.4,
                    'vicinity': f'Cultural District {city}',
                    'place_id': 'mock_attraction_1'
                },
                {
                    'name': f'{city} Temple',
                    'rating': 4.7,
                    'vicinity': f'Historic Area {city}',
                    'place_id': 'mock_attraction_2'
                }
            ],
            'city': city,
            'collected_at': datetime.now().isoformat(),
            'source': 'mock_data'
        }
    
    def get_weather_data(self, city: str) -> Dict[str, Any]:
        """Get weather data from OpenWeather API"""
        print(f"Getting weather data for {city}")
        
        # Check if API key is available
        if not self.api_keys.get('openweather'):
            print("OpenWeather API key not found, using mock data")
            return self._get_mock_weather_data(city)
        
        weather_params = {
            'q': city,
            'units': 'metric',
            'appid': self.api_keys.get('openweather')
        }
        
        weather_response = self._make_api_request('openweather', 'weather', weather_params, cache_duration_hours=6)
        
        if weather_response:
            return {
                'city': city,
                'temperature': weather_response.get('main', {}).get('temp'),
                'description': weather_response.get('weather', [{}])[0].get('description'),
                'humidity': weather_response.get('main', {}).get('humidity'),
                'wind_speed': weather_response.get('wind', {}).get('speed'),
                'collected_at': datetime.now().isoformat()
            }
        
        return {'error': 'Weather data not available'}
    
    def _get_mock_weather_data(self, city: str) -> Dict[str, Any]:
        """Get mock weather data when API key is not available"""
        return {
            'city': city,
            'temperature': 25.0,
            'description': 'Partly cloudy',
            'humidity': 65,
            'wind_speed': 3.2,
            'collected_at': datetime.now().isoformat(),
            'source': 'mock_data'
        }
    
    def search_travel_info(self, query: str) -> Dict[str, Any]:
        """Search travel information using Tavily API or real CSV data"""
        print(f"Searching travel info: {query}")
        
        # Check if API key is available
        if not self.api_keys.get('tavily'):
            print("Tavily API key not found, using real CSV data")
            return self._get_real_travel_info(query)
        
        search_params = {
            'query': query,
            'search_depth': 'basic',
            'include_answer': True,
            'include_raw_content': False,
            'max_results': 5
        }
        
        search_response = self._make_api_request('tavily', 'search', search_params)
        
        if search_response and 'results' in search_response:
            return {
                'query': query,
                'results': search_response['results'],
                'answer': search_response.get('answer', ''),
                'collected_at': datetime.now().isoformat()
            }
        
        return {'error': 'Search results not available'}
    
    def _get_real_travel_info(self, query: str) -> Dict[str, Any]:
        """Get real travel info from CSV data"""
        try:
            # Import real data provider
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.abspath(__file__)))
            
            from real_data_provider import RealDataProvider
            
            # Initialize data provider
            data_provider = RealDataProvider()
            
            # Get real travel info
            travel_info = data_provider.get_travel_info(query)
            
            print(f"Using real CSV data for travel info: {len(travel_info['results'])} results")
            return travel_info
            
        except Exception as e:
            print(f"Error loading real CSV data: {e}, falling back to mock data")
            return self._get_mock_travel_info(query)
    
    def _get_mock_travel_info(self, query: str) -> Dict[str, Any]:
        """Get mock travel info when API key is not available"""
        return {
            'query': query,
            'results': [
                {
                    'title': f'Travel Guide for {query}',
                    'url': 'https://example.com/travel-guide',
                    'content': f'Comprehensive travel information about {query} including attractions, restaurants, and activities.',
                    'score': 0.95
                },
                {
                    'title': f'Best Places to Visit in {query}',
                    'url': 'https://example.com/best-places',
                    'content': f'Top attractions and must-see locations in {query} for tourists.',
                    'score': 0.87
                }
            ],
            'answer': f'{query} is a wonderful destination with rich culture, delicious food, and beautiful attractions.',
            'collected_at': datetime.now().isoformat(),
            'source': 'mock_data'
        }
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        
        # Get total cached entries
        cursor.execute('SELECT COUNT(*) FROM api_cache')
        total_entries = cursor.fetchone()[0]
        
        # Get entries by API
        cursor.execute('SELECT api_name, COUNT(*) FROM api_cache GROUP BY api_name')
        api_stats = dict(cursor.fetchall())
        
        # Get expired entries
        cursor.execute('SELECT COUNT(*) FROM api_cache WHERE expires_at < ?', (datetime.now(),))
        expired_entries = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_entries': total_entries,
            'api_stats': api_stats,
            'expired_entries': expired_entries,
            'cache_db': self.cache_db
        }
    
    def clear_expired_cache(self):
        """Clear expired cache entries"""
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM api_cache WHERE expires_at < ?', (datetime.now(),))
        deleted_count = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        print(f"🗑️ Cleared {deleted_count} expired cache entries")
        return deleted_count