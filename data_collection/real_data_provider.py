import pandas as pd
import json
import random
from typing import Dict, List, Any, Optional
from pathlib import Path
import os

class RealDataProvider:
    """Provider for real data from CSV files instead of mock data"""
    
    def __init__(self, data_dir: str = "TRAVEL_PLANNER/data"):
        """Initialize with real data from CSV files"""
        self.data_dir = Path(data_dir)
        self.data_cache = {}
        self._load_all_data()
    
    def _load_all_data(self):
        """Load all CSV data into memory"""
        print("Loading real data from CSV files...")
        
        # Load main datasets
        datasets = {
            'hotels': 'hotels.csv',
            'restaurants': 'restaurants.csv', 
            'attractions': 'attractions.csv',
            'vietnam_all': 'vietnam_all_places.csv',
            'entertainment': 'entertainment.csv',
            'family': 'family.csv',
            'foodandbeverage': 'foodandbeverage.csv',
            'wellness': 'wellness.csv'
        }
        
        for key, filename in datasets.items():
            file_path = self.data_dir / filename
            if file_path.exists():
                try:
                    df = pd.read_csv(file_path)
                    self.data_cache[key] = df
                    print(f"Loaded {len(df)} records from {filename}")
                except Exception as e:
                    print(f"Error loading {filename}: {e}")
                    self.data_cache[key] = pd.DataFrame()
            else:
                print(f"File not found: {filename}")
                self.data_cache[key] = pd.DataFrame()
        
        # Load statistics
        stats_file = self.data_dir / 'data_statistics.json'
        if stats_file.exists():
            with open(stats_file, 'r', encoding='utf-8') as f:
                self.stats = json.load(f)
        else:
            self.stats = {}
        
        print(f"Data loading complete. Total datasets: {len(self.data_cache)}")
    
    def get_places_data(self, city: str, limit: int = 10) -> Dict[str, Any]:
        """Get real places data for a city"""
        print(f"Getting real places data for {city}")
        
        places_data = {
            'hotels': [],
            'restaurants': [],
            'attractions': [],
            'city': city,
            'collected_at': self._get_current_time(),
            'source': 'real_csv_data'
        }
        
        # Get hotels
        if 'hotels' in self.data_cache and not self.data_cache['hotels'].empty:
            hotels_df = self.data_cache['hotels']
            city_hotels = hotels_df[hotels_df['city'].str.contains(city, case=False, na=False)]
            if not city_hotels.empty:
                places_data['hotels'] = city_hotels.head(limit).to_dict('records')
        
        # Get restaurants
        if 'restaurants' in self.data_cache and not self.data_cache['restaurants'].empty:
            restaurants_df = self.data_cache['restaurants']
            city_restaurants = restaurants_df[restaurants_df['city'].str.contains(city, case=False, na=False)]
            if not city_restaurants.empty:
                places_data['restaurants'] = city_restaurants.head(limit).to_dict('records')
        
        # Get attractions
        if 'attractions' in self.data_cache and not self.data_cache['attractions'].empty:
            attractions_df = self.data_cache['attractions']
            city_attractions = attractions_df[attractions_df['city'].str.contains(city, case=False, na=False)]
            if not city_attractions.empty:
                places_data['attractions'] = city_attractions.head(limit).to_dict('records')
        
        # If no specific data found, try vietnam_all_places
        if not places_data['hotels'] and not places_data['restaurants'] and not places_data['attractions']:
            if 'vietnam_all' in self.data_cache and not self.data_cache['vietnam_all'].empty:
                all_df = self.data_cache['vietnam_all']
                city_data = all_df[all_df['city'].str.contains(city, case=False, na=False)]
                if not city_data.empty:
                    places_data['attractions'] = city_data.head(limit).to_dict('records')
        
        print(f"Found {len(places_data['hotels'])} hotels, {len(places_data['restaurants'])} restaurants, {len(places_data['attractions'])} attractions")
        return places_data
    
    def get_weather_data(self, city: str) -> Dict[str, Any]:
        """Get mock weather data (since we don't have real weather CSV)"""
        # This would typically come from OpenWeather API
        # For now, return realistic mock data based on Vietnamese climate
        weather_conditions = [
            "sunny", "partly cloudy", "overcast", "light rain", "heavy rain"
        ]
        
        temperatures = {
            "Hanoi": (15, 35),
            "Ho Chi Minh City": (22, 38),
            "Da Nang": (18, 36),
            "Hue": (16, 37),
            "Nha Trang": (20, 35)
        }
        
        city_key = city if city in temperatures else "Hanoi"
        temp_range = temperatures[city_key]
        
        return {
            'city': city,
            'temperature': round(random.uniform(temp_range[0], temp_range[1]), 1),
            'description': random.choice(weather_conditions),
            'humidity': random.randint(60, 90),
            'wind_speed': round(random.uniform(1.0, 5.0), 1),
            'collected_at': self._get_current_time(),
            'source': 'realistic_mock_data'
        }
    
    def get_travel_info(self, query: str) -> Dict[str, Any]:
        """Get travel information from real data"""
        print(f"Searching travel info: {query}")
        
        # Search in vietnam_all_places for relevant information
        results = []
        if 'vietnam_all' in self.data_cache and not self.data_cache['vietnam_all'].empty:
            df = self.data_cache['vietnam_all']
            
            # Search by name, description, or category
            search_terms = query.lower().split()
            for term in search_terms:
                mask = (
                    df['name'].str.contains(term, case=False, na=False) |
                    df['description'].str.contains(term, case=False, na=False) |
                    df['category'].str.contains(term, case=False, na=False)
                )
                matching = df[mask]
                if not matching.empty:
                    results.extend(matching.head(3).to_dict('records'))
        
        # Remove duplicates
        seen = set()
        unique_results = []
        for result in results:
            key = result.get('name', '')
            if key not in seen:
                seen.add(key)
                unique_results.append(result)
        
        return {
            'query': query,
            'results': unique_results[:5],  # Limit to 5 results
            'answer': f"Found {len(unique_results)} places related to '{query}' in Vietnam",
            'collected_at': self._get_current_time(),
            'source': 'real_csv_data'
        }
    
    def get_cities_list(self) -> List[str]:
        """Get list of all cities in the dataset"""
        cities = set()
        
        for dataset_name, df in self.data_cache.items():
            if not df.empty and 'city' in df.columns:
                cities.update(df['city'].dropna().unique())
        
        return sorted(list(cities))
    
    def get_data_statistics(self) -> Dict[str, Any]:
        """Get statistics about the real data"""
        stats = {
            'total_datasets': len(self.data_cache),
            'datasets_info': {},
            'total_cities': 0,
            'total_places': 0
        }
        
        all_cities = set()
        
        for dataset_name, df in self.data_cache.items():
            if not df.empty:
                stats['datasets_info'][dataset_name] = {
                    'records': len(df),
                    'columns': list(df.columns)
                }
                
                if 'city' in df.columns:
                    all_cities.update(df['city'].dropna().unique())
                
                stats['total_places'] += len(df)
        
        stats['total_cities'] = len(all_cities)
        stats['cities_list'] = sorted(list(all_cities))
        
        # Add original statistics if available
        if hasattr(self, 'stats'):
            stats.update(self.stats)
        
        return stats
    
    def search_places(self, search_term: str, city: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Search for places by term and optionally by city"""
        results = []
        
        for dataset_name, df in self.data_cache.items():
            if df.empty:
                continue
            
            # Search in name, description, category
            mask = (
                df['name'].str.contains(search_term, case=False, na=False) |
                df['description'].str.contains(search_term, case=False, na=False)
            )
            
            if 'category' in df.columns:
                mask |= df['category'].str.contains(search_term, case=False, na=False)
            
            if city:
                if 'city' in df.columns:
                    mask &= df['city'].str.contains(city, case=False, na=False)
            
            matching = df[mask]
            if not matching.empty:
                results.extend(matching.head(limit).to_dict('records'))
        
        return results[:limit]
    
    def _get_current_time(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_dataset_info(self) -> Dict[str, Any]:
        """Get information about available datasets"""
        info = {}
        for dataset_name, df in self.data_cache.items():
            if not df.empty:
                info[dataset_name] = {
                    'records': len(df),
                    'columns': list(df.columns),
                    'sample_record': df.iloc[0].to_dict() if len(df) > 0 else {}
                }
        return info
