import requests
from bs4 import BeautifulSoup
import time
import random
import sqlite3
import hashlib
import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import re
from urllib.parse import urljoin, urlparse

class WebScraper:
    def __init__(self):
        """Khởi tạo Web Scraper với caching"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        self.delay_range = (1, 3)  # Random delay between requests
        self.max_retries = 3
        
        # Vietnamese travel websites
        self.travel_sites = {
            'vietnam_tourism': 'https://vietnam.travel/',
            'tripadvisor_vn': 'https://www.tripadvisor.com.vn/',
            'booking_vn': 'https://www.booking.com/',
            'agoda_vn': 'https://www.agoda.com/',
            'lonely_planet': 'https://www.lonelyplanet.com/vietnam'
        }
        
        # Initialize cache database
        self.cache_db = "web_scraper_cache.db"
        self._init_cache_db()
    
    def _init_cache_db(self):
        """Initialize cache database"""
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS web_cache (
                cache_key TEXT PRIMARY KEY,
                url TEXT,
                content TEXT,
                created_at TIMESTAMP,
                expires_at TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()
    
    def _generate_cache_key(self, url: str) -> str:
        """Generate cache key for URL"""
        return hashlib.md5(url.encode()).hexdigest()
    
    def _get_cached_content(self, cache_key: str) -> Optional[str]:
        """Get cached web content"""
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT content FROM web_cache 
            WHERE cache_key = ? AND expires_at > ?
        ''', (cache_key, datetime.now()))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return result[0]
        return None
    
    def _cache_content(self, cache_key: str, url: str, content: str, cache_duration_hours: int = 24):
        """Cache web content"""
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        
        expires_at = datetime.now() + timedelta(hours=cache_duration_hours)
        
        cursor.execute('''
            INSERT OR REPLACE INTO web_cache 
            (cache_key, url, content, created_at, expires_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (cache_key, url, content, datetime.now(), expires_at))
        
        conn.commit()
        conn.close()
    
    def _random_delay(self):
        """Random delay để tránh bị block"""
        delay = random.uniform(*self.delay_range)
        time.sleep(delay)
    
    def _make_request(self, url: str, retries: int = 0, cache_duration_hours: int = 24) -> Optional[str]:
        """Thực hiện HTTP request với caching"""
        cache_key = self._generate_cache_key(url)
        
        # Check cache first
        cached_content = self._get_cached_content(cache_key)
        if cached_content:
            print(f"Cache hit for {url}")
            return cached_content
        
        try:
            self._random_delay()
            print(f"Fetching {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Cache the content
            self._cache_content(cache_key, url, response.text, cache_duration_hours)
            print(f"Content cached for {cache_duration_hours}h")
            
            return response.text
            
        except requests.exceptions.RequestException as e:
            if retries < self.max_retries:
                print(f"Request failed, retrying... ({retries + 1}/{self.max_retries})")
                time.sleep(2 ** retries)  # Exponential backoff
                return self._make_request(url, retries + 1, cache_duration_hours)
            else:
                print(f"Request failed after {self.max_retries} retries: {e}")
                return None
    
    def scrape_places(self, city: str) -> Dict[str, Any]:
        """Scrape places information for a city"""
        print(f"Scraping places data for {city}")
        
        scraped_data = {
            'city': city,
            'reviews': [],
            'events': [],
            'tips': [],
                'scraped_at': datetime.now().isoformat()
            }
        
        # Scrape Vietnam Tourism website
        vietnam_tourism_url = f"https://vietnam.travel/destinations/{city.lower().replace(' ', '-')}"
        content = self._make_request(vietnam_tourism_url, cache_duration_hours=12)
        
        if content:
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract attractions
            attractions = soup.find_all(['h2', 'h3'], string=re.compile(r'attraction|place|site', re.I))
            for attraction in attractions[:5]:  # Limit to 5
                scraped_data['tips'].append({
                    'type': 'attraction',
                    'name': attraction.get_text().strip(),
                    'source': 'vietnam.travel'
                })
        
        # Scrape TripAdvisor for reviews
        tripadvisor_url = f"https://www.tripadvisor.com.vn/Tourism-g293921-{city}-Vietnam.html"
        content = self._make_request(tripadvisor_url, cache_duration_hours=6)
        
        if content:
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract review snippets
            reviews = soup.find_all('div', class_=re.compile(r'review', re.I))
            for review in reviews[:3]:  # Limit to 3
                review_text = review.get_text().strip()
                if len(review_text) > 50:  # Only meaningful reviews
                    scraped_data['reviews'].append({
                        'text': review_text[:200] + '...' if len(review_text) > 200 else review_text,
                        'source': 'tripadvisor',
                        'rating': 4.0  # Default rating
                    })
        
        print(f"Scraped {len(scraped_data['tips'])} tips, {len(scraped_data['reviews'])} reviews")
        return scraped_data
    
    def scrape_hotels(self, city: str) -> List[Dict[str, Any]]:
        """Scrape hotel information"""
        print(f"Scraping hotels for {city}")
        
        hotels = []
        
        # Scrape Booking.com
        booking_url = f"https://www.booking.com/searchresults.html?ss={city}&checkin=&checkout="
        content = self._make_request(booking_url, cache_duration_hours=6)
        
        if content:
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract hotel information
            hotel_elements = soup.find_all('div', class_=re.compile(r'hotel', re.I))
            for hotel in hotel_elements[:5]:  # Limit to 5
                name_elem = hotel.find(['h3', 'h4'], class_=re.compile(r'name|title', re.I))
                if name_elem:
                    hotels.append({
                        'name': name_elem.get_text().strip(),
                        'source': 'booking.com',
                        'city': city,
                        'rating': 4.0  # Default rating
                    })
        
        print(f"Scraped {len(hotels)} hotels")
        return hotels
    
    def scrape_restaurants(self, city: str) -> List[Dict[str, Any]]:
        """Scrape restaurant information"""
        print(f"Scraping restaurants for {city}")
        
        restaurants = []
        
        # Scrape TripAdvisor restaurants
        tripadvisor_url = f"https://www.tripadvisor.com.vn/Restaurants-g293921-{city}-Vietnam.html"
        content = self._make_request(tripadvisor_url, cache_duration_hours=6)
        
        if content:
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract restaurant information
            restaurant_elements = soup.find_all('div', class_=re.compile(r'restaurant', re.I))
            for restaurant in restaurant_elements[:5]:  # Limit to 5
                name_elem = restaurant.find(['h3', 'h4'], class_=re.compile(r'name|title', re.I))
                if name_elem:
                    restaurants.append({
                        'name': name_elem.get_text().strip(),
                        'source': 'tripadvisor',
                        'city': city,
                        'rating': 4.0  # Default rating
                    })
        
        print(f"Scraped {len(restaurants)} restaurants")
        return restaurants
    
    def scrape_events(self, city: str) -> List[Dict[str, Any]]:
        """Scrape events and festivals"""
        print(f"Scraping events for {city}")
        
        events = []
        
        # Scrape Vietnam Tourism events
        events_url = f"https://vietnam.travel/events"
        content = self._make_request(events_url, cache_duration_hours=12)
        
        if content:
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract event information
            event_elements = soup.find_all(['div', 'article'], class_=re.compile(r'event', re.I))
            for event in event_elements[:3]:  # Limit to 3
                title_elem = event.find(['h2', 'h3'], class_=re.compile(r'title|name', re.I))
                if title_elem:
                    events.append({
                        'name': title_elem.get_text().strip(),
                        'city': city,
                        'source': 'vietnam.travel',
                        'date': 'TBD'  # Default date
                    })
        
        print(f"Scraped {len(events)} events")
        return events
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        
        # Get total cached entries
        cursor.execute('SELECT COUNT(*) FROM web_cache')
        total_entries = cursor.fetchone()[0]
        
        # Get expired entries
        cursor.execute('SELECT COUNT(*) FROM web_cache WHERE expires_at < ?', (datetime.now(),))
        expired_entries = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_entries': total_entries,
            'expired_entries': expired_entries,
            'cache_db': self.cache_db
        }
    
    def clear_expired_cache(self):
        """Clear expired cache entries"""
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM web_cache WHERE expires_at < ?', (datetime.now(),))
        deleted_count = cursor.rowcount
        
        conn.commit()
        conn.close()
        
        print(f"Cleared {deleted_count} expired cache entries")
        return deleted_count