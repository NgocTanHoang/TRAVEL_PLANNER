"""
Geocoding Helper - Lấy địa chỉ cụ thể từ lat/lon
Sử dụng Geoapify Reverse Geocoding (FREE)
Với Database Cache để tránh gọi API nhiều lần
"""

import requests
import sqlite3
from typing import Optional, Dict
from pathlib import Path
import json

class GeocodingHelper:
    """Helper để lấy địa chỉ từ tọa độ với database cache"""
    
    def __init__(self):
        self.geoapify_key = "3ebb73069d244c98bf4b5b33fb2e2d44"
        
        # Setup database cache
        project_root = Path(__file__).parent.parent
        self.db_path = project_root / "cache.db"
        self._init_cache_table()
        
        print(f"✅ Geocoding cache initialized at {self.db_path}")
    
    def _init_cache_table(self):
        """Tạo bảng cache nếu chưa có"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS geocode_cache (
                    lat REAL,
                    lon REAL,
                    address TEXT,
                    street TEXT,
                    housenumber TEXT,
                    suburb TEXT,
                    district TEXT,
                    city TEXT,
                    state TEXT,
                    postcode TEXT,
                    formatted TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (lat, lon)
                )
            """)
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"⚠️ Error creating geocode cache table: {e}")
    
    def _get_from_cache(self, lat: float, lon: float) -> Optional[Dict]:
        """Lấy địa chỉ từ database cache"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Round lat/lon to 4 decimal places for cache key (~11m precision)
            lat_rounded = round(lat, 4)
            lon_rounded = round(lon, 4)
            
            cursor.execute("""
                SELECT street, housenumber, suburb, district, city, state, postcode, formatted
                FROM geocode_cache
                WHERE lat = ? AND lon = ?
            """, (lat_rounded, lon_rounded))
            
            row = cursor.fetchone()
            conn.close()
            
            if row:
                return {
                    'street': row[0] or '',
                    'housenumber': row[1] or '',
                    'suburb': row[2] or '',
                    'district': row[3] or '',
                    'city': row[4] or '',
                    'state': row[5] or '',
                    'postcode': row[6] or '',
                    'formatted': row[7] or '',
                }
            
            return None
            
        except Exception as e:
            print(f"⚠️ Error reading geocode cache: {e}")
            return None
    
    def _save_to_cache(self, lat: float, lon: float, info: Dict):
        """Lưu địa chỉ vào database cache"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Round lat/lon to 4 decimal places
            lat_rounded = round(lat, 4)
            lon_rounded = round(lon, 4)
            
            # Build simple address string
            address_parts = []
            if info.get('housenumber'):
                address_parts.append(info['housenumber'])
            if info.get('street'):
                address_parts.append(info['street'])
            if info.get('suburb'):
                address_parts.append(info['suburb'])
            if info.get('city'):
                address_parts.append(info['city'])
            
            address = ', '.join(address_parts) if address_parts else info.get('formatted', '')
            
            cursor.execute("""
                INSERT OR REPLACE INTO geocode_cache 
                (lat, lon, address, street, housenumber, suburb, district, city, state, postcode, formatted)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                lat_rounded,
                lon_rounded,
                address,
                info.get('street', ''),
                info.get('housenumber', ''),
                info.get('suburb', ''),
                info.get('district', ''),
                info.get('city', ''),
                info.get('state', ''),
                info.get('postcode', ''),
                info.get('formatted', '')
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"⚠️ Error saving to geocode cache: {e}")
    
    def get_address(self, lat: float, lon: float) -> Optional[str]:
        """
        Lấy địa chỉ từ latitude/longitude
        Sử dụng database cache để tránh gọi API nhiều lần
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Địa chỉ đầy đủ hoặc None
        """
        # Try cache first
        cached = self._get_from_cache(lat, lon)
        if cached:
            # Build address from cached data
            address_parts = []
            if cached.get('housenumber'):
                address_parts.append(cached['housenumber'])
            if cached.get('street'):
                address_parts.append(cached['street'])
            if cached.get('suburb'):
                address_parts.append(cached['suburb'])
            if cached.get('city'):
                address_parts.append(cached['city'])
            
            if address_parts:
                return ', '.join(address_parts)
            elif cached.get('formatted'):
                return cached['formatted']
        
        # Not in cache, call API
        try:
            url = "https://api.geoapify.com/v1/geocode/reverse"
            params = {
                'lat': lat,
                'lon': lon,
                'apiKey': self.geoapify_key,
                'format': 'json'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('results'):
                result = data['results'][0]
                
                # Extract info
                info = {
                    'street': result.get('street', ''),
                    'housenumber': result.get('housenumber', ''),
                    'suburb': result.get('suburb', ''),
                    'district': result.get('district', ''),
                    'city': result.get('city', ''),
                    'state': result.get('state', ''),
                    'postcode': result.get('postcode', ''),
                    'formatted': result.get('formatted', ''),
                }
                
                # Save to cache
                self._save_to_cache(lat, lon, info)
                
                # Build address string
                address_parts = []
                if info.get('housenumber'):
                    address_parts.append(info['housenumber'])
                if info.get('street'):
                    address_parts.append(info['street'])
                if info.get('suburb'):
                    address_parts.append(info['suburb'])
                elif info.get('district'):
                    address_parts.append(info['district'])
                if info.get('city'):
                    address_parts.append(info['city'])
                elif info.get('state'):
                    address_parts.append(info['state'])
                
                address = ', '.join(address_parts) if address_parts else info.get('formatted', 'N/A')
                
                return address
            
            return None
            
        except Exception as e:
            print(f"⚠️ Geocoding error: {e}")
            return None
    
    def get_detailed_info(self, lat: float, lon: float) -> Optional[Dict]:
        """
        Lấy thông tin chi tiết từ lat/lon
        Sử dụng database cache để tránh gọi API nhiều lần
        
        Returns:
            Dict với address, street, district, city, etc.
        """
        # Try cache first
        cached = self._get_from_cache(lat, lon)
        if cached:
            return cached
        
        # Not in cache, call API
        try:
            url = "https://api.geoapify.com/v1/geocode/reverse"
            params = {
                'lat': lat,
                'lon': lon,
                'apiKey': self.geoapify_key,
                'format': 'json'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if data.get('results'):
                result = data['results'][0]
                info = {
                    'street': result.get('street', ''),
                    'housenumber': result.get('housenumber', ''),
                    'suburb': result.get('suburb', ''),
                    'district': result.get('district', ''),
                    'city': result.get('city', ''),
                    'state': result.get('state', ''),
                    'postcode': result.get('postcode', ''),
                    'formatted': result.get('formatted', ''),
                }
                
                # Save to cache
                self._save_to_cache(lat, lon, info)
                
                return info
            
            return None
            
        except Exception as e:
            print(f"⚠️ Geocoding error: {e}")
            return None


    def get_cache_stats(self) -> Dict:
        """Lấy thống kê về cache"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM geocode_cache")
            total = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(DISTINCT city) FROM geocode_cache WHERE city != ''")
            cities = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'total_cached': total,
                'cities': cities
            }
        except Exception as e:
            print(f"⚠️ Error getting cache stats: {e}")
            return {'total_cached': 0, 'cities': 0}


# Singleton instance
_geocoding_helper = None

def get_geocoding_helper() -> GeocodingHelper:
    """Get singleton instance"""
    global _geocoding_helper
    if _geocoding_helper is None:
        _geocoding_helper = GeocodingHelper()
    return _geocoding_helper


# Test
if __name__ == "__main__":
    helper = get_geocoding_helper()
    
    # Test với Dinh Độc Lập
    print("Test: Dinh Độc Lập")
    lat, lon = 10.7770, 106.6953
    address = helper.get_address(lat, lon)
    print(f"Address: {address}")
    
    detailed = helper.get_detailed_info(lat, lon)
    if detailed:
        print(f"Street: {detailed['street']}")
        print(f"District: {detailed['district']}")
        print(f"City: {detailed['city']}")

