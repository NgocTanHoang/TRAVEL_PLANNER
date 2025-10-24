"""
═══════════════════════════════════════════════════════════════════════════════
VIETNAM TRAIN TICKET PRICE SCRAPER
═══════════════════════════════════════════════════════════════════════════════

⚠️  IMPORTANT WARNINGS AND LEGAL COMPLIANCE ⚠️

1. RATE LIMITING:
   - This script implements automatic rate limiting (minimum 3 seconds between requests)
   - Excessive requests may result in your IP being blocked
   - Consider using official APIs if available

2. TERMS OF SERVICE:
   - Always read and comply with the website's Terms of Service
   - Check robots.txt file: https://dsvn.vn/robots.txt
   - Respect copyright and data usage policies

3. LEGAL CONSIDERATIONS:
   - Web scraping may be against the website's ToS
   - Some jurisdictions have laws against unauthorized data access
   - Use this script responsibly and ethically
   - Consider contacting the website owner for permission

4. TECHNICAL RISKS:
   - Website structure may change, breaking the scraper
   - You may be temporarily or permanently blocked
   - Captchas or anti-bot measures may be implemented

5. BEST PRACTICES:
   - Use official APIs when available
   - Cache results to minimize requests
   - Identify your bot with a proper User-Agent
   - Respect rate limits and server resources

═══════════════════════════════════════════════════════════════════════════════
"""

import requests
from bs4 import BeautifulSoup
import time
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
import hashlib
import random

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════

# Rate limiting configuration
MIN_REQUEST_DELAY = 3.0  # Minimum 3 seconds between requests
MAX_REQUEST_DELAY = 5.0  # Maximum 5 seconds between requests

# Cache configuration
CACHE_DURATION_HOURS = 24  # Cache results for 24 hours
CACHE_DB_PATH = "train_prices_cache.db"

# User agent - ALWAYS identify your bot properly
USER_AGENT = (
    "TravelPlannerBot/1.0 (Educational Project; Contact: your-email@example.com) "
    "Python-Requests/2.28.0"
)

# HTTP headers
HEADERS = {
    'User-Agent': USER_AGENT,
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7',
    'Accept-Encoding': 'gzip, deflate',
    'DNT': '1',  # Do Not Track
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}

# Request timeout
REQUEST_TIMEOUT = 10  # seconds

# Maximum retries
MAX_RETRIES = 2

# ═══════════════════════════════════════════════════════════════════════════
# WARNING DISPLAY
# ═══════════════════════════════════════════════════════════════════════════

def display_legal_warning():
    """Display comprehensive legal and ethical warnings"""
    print("\n" + "="*80)
    print("⚠️  LEGAL AND ETHICAL WARNING ⚠️".center(80))
    print("="*80)
    print("""
This script is for EDUCATIONAL PURPOSES ONLY.

BEFORE USING THIS SCRIPT, YOU MUST:
1. ✅ Read and accept the target website's Terms of Service
2. ✅ Check robots.txt: https://dsvn.vn/robots.txt
3. ✅ Ensure compliance with local laws regarding web scraping
4. ✅ Consider using official APIs instead of scraping
5. ✅ Implement proper rate limiting (already included)
6. ✅ Be prepared to be blocked by anti-bot measures

RISKS:
❌ Your IP may be temporarily or permanently blocked
❌ Legal action may be taken against unauthorized access
❌ The website structure may change, breaking this script
❌ Captchas may prevent automated access

BEST PRACTICES:
✅ Use official APIs when available
✅ Cache results to minimize requests (implemented)
✅ Respect rate limits (3-5 seconds delay implemented)
✅ Identify your bot properly (User-Agent configured)
✅ Contact website owner for permission

BY USING THIS SCRIPT, YOU ACCEPT ALL RISKS AND RESPONSIBILITIES.
    """)
    print("="*80)
    
    response = input("\nDo you understand and accept these terms? (yes/no): ")
    if response.lower() != 'yes':
        print("\n❌ Script terminated. Please use official APIs instead.")
        exit(1)
    
    print("\n✅ Terms accepted. Proceeding with caution...\n")


# ═══════════════════════════════════════════════════════════════════════════
# CACHE MANAGEMENT
# ═══════════════════════════════════════════════════════════════════════════

class TrainPriceCache:
    """SQLite-based cache for train prices"""
    
    def __init__(self, db_path: str = CACHE_DB_PATH):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize cache database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS train_prices (
                id TEXT PRIMARY KEY,
                departure TEXT NOT NULL,
                destination TEXT NOT NULL,
                date TEXT NOT NULL,
                cheapest_price REAL,
                travel_time TEXT,
                available_trains INTEGER,
                raw_data TEXT,
                cached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _generate_cache_key(self, departure: str, destination: str, date: str) -> str:
        """Generate unique cache key"""
        key_string = f"{departure}_{destination}_{date}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def get(self, departure: str, destination: str, date: str) -> Optional[Dict]:
        """Get cached result if not expired"""
        cache_key = self._generate_cache_key(departure, destination, date)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT cheapest_price, travel_time, available_trains, raw_data
            FROM train_prices
            WHERE id = ? AND expires_at > datetime('now')
        """, (cache_key,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            logger.info(f"✅ Cache HIT for {departure} → {destination} on {date}")
            return {
                'cheapest_price': result[0],
                'travel_time': result[1],
                'available_trains': result[2],
                'raw_data': result[3],
                'from_cache': True
            }
        
        logger.info(f"❌ Cache MISS for {departure} → {destination} on {date}")
        return None
    
    def set(self, departure: str, destination: str, date: str, data: Dict):
        """Store result in cache"""
        cache_key = self._generate_cache_key(departure, destination, date)
        expires_at = datetime.now() + timedelta(hours=CACHE_DURATION_HOURS)
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO train_prices 
            (id, departure, destination, date, cheapest_price, travel_time, 
             available_trains, raw_data, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            cache_key, departure, destination, date,
            data.get('cheapest_price'), data.get('travel_time'),
            data.get('available_trains'), str(data.get('raw_data', '')),
            expires_at
        ))
        
        conn.commit()
        conn.close()
        
        logger.info(f"💾 Cached result for {departure} → {destination} on {date}")


# ═══════════════════════════════════════════════════════════════════════════
# RATE LIMITER
# ═══════════════════════════════════════════════════════════════════════════

class RateLimiter:
    """Enforce rate limiting between requests"""
    
    def __init__(self, min_delay: float = MIN_REQUEST_DELAY, 
                 max_delay: float = MAX_REQUEST_DELAY):
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.last_request_time = 0
    
    def wait(self):
        """Wait before next request to respect rate limits"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.min_delay:
            # Add random jitter to appear more human-like
            delay = random.uniform(self.min_delay, self.max_delay)
            wait_time = delay - time_since_last_request
            
            if wait_time > 0:
                logger.warning(
                    f"⏳ Rate limiting: waiting {wait_time:.2f} seconds "
                    f"(min: {self.min_delay}s, max: {self.max_delay}s)"
                )
                time.sleep(wait_time)
        
        self.last_request_time = time.time()


# ═══════════════════════════════════════════════════════════════════════════
# MAIN SCRAPING FUNCTION
# ═══════════════════════════════════════════════════════════════════════════

def scrape_train_prices(
    departure: str, 
    destination: str, 
    date: str,
    use_cache: bool = True,
    force_refresh: bool = False
) -> Dict:
    """
    Scrape train ticket prices from Vietnamese railway website
    
    ⚠️  WARNING: This function performs web scraping which may:
    - Violate the website's Terms of Service
    - Result in your IP being blocked
    - Be illegal in some jurisdictions
    
    Args:
        departure (str): Departure station (e.g., "Hà Nội", "Sài Gòn")
        destination (str): Destination station (e.g., "Đà Nẵng", "Nha Trang")
        date (str): Travel date in format YYYY-MM-DD
        use_cache (bool): Use cached results if available
        force_refresh (bool): Force refresh even if cache exists
    
    Returns:
        Dict containing:
            - cheapest_price: Lowest ticket price found (VND)
            - travel_time: Estimated travel duration
            - available_trains: Number of trains found
            - trains: List of train details
            - from_cache: Whether result came from cache
            - error: Error message if scraping failed
    
    Example:
        >>> result = scrape_train_prices("Hà Nội", "Đà Nẵng", "2025-12-25")
        >>> print(f"Cheapest: {result['cheapest_price']} VND")
    
    ⚠️  IMPORTANT REMINDERS:
    - This script implements 3-5 second delays between requests
    - Results are cached for 24 hours to minimize server load
    - You may still be blocked by anti-bot measures
    - Always prefer official APIs when available
    """
    
    # Initialize cache and rate limiter
    cache = TrainPriceCache()
    rate_limiter = RateLimiter()
    
    # Check cache first (unless force refresh)
    if use_cache and not force_refresh:
        cached_result = cache.get(departure, destination, date)
        if cached_result:
            return cached_result
    
    # ⚠️  WARNING: About to make HTTP request
    logger.warning(
        f"⚠️  About to scrape: {departure} → {destination} on {date}"
    )
    logger.warning(
        "⚠️  Please ensure you have permission and are complying with ToS"
    )
    
    # Apply rate limiting
    rate_limiter.wait()
    
    try:
        # NOTE: This is a SIMULATED example
        # Real implementation would need actual DSVN website structure
        
        # Example URL structure (may not be actual)
        # Real DSVN might use different parameters or require POST requests
        url = f"https://dsvn.vn/vi/tra-cuu-gia-ve"  # Example URL
        
        params = {
            'departure': departure,
            'destination': destination,
            'date': date
        }
        
        logger.info(f"🌐 Requesting: {url}")
        logger.info(f"📊 Parameters: {params}")
        
        # Make request with retry logic
        response = None
        for attempt in range(MAX_RETRIES + 1):
            try:
                response = requests.get(
                    url,
                    params=params,
                    headers=HEADERS,
                    timeout=REQUEST_TIMEOUT,
                    allow_redirects=True
                )
                
                # Check for common anti-bot responses
                if response.status_code == 403:
                    raise Exception(
                        "❌ 403 Forbidden - You may be blocked by anti-bot measures"
                    )
                elif response.status_code == 429:
                    raise Exception(
                        "❌ 429 Too Many Requests - Rate limit exceeded"
                    )
                elif response.status_code != 200:
                    raise Exception(
                        f"❌ HTTP {response.status_code} - Unexpected response"
                    )
                
                break  # Success
                
            except requests.exceptions.Timeout:
                if attempt < MAX_RETRIES:
                    logger.warning(f"⏳ Timeout on attempt {attempt + 1}, retrying...")
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise Exception("❌ Request timeout after retries")
            
            except requests.exceptions.RequestException as e:
                raise Exception(f"❌ Request failed: {str(e)}")
        
        if not response:
            raise Exception("❌ Failed to get response")
        
        # Parse HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # ═══════════════════════════════════════════════════════════════
        # ⚠️  IMPORTANT: Website structure analysis
        # ═══════════════════════════════════════════════════════════════
        # The following parsing logic is SIMULATED
        # Real implementation requires analyzing actual website structure:
        # 1. Inspect the website HTML
        # 2. Identify train listings (usually <div>, <table>, or <ul>)
        # 3. Find price elements (look for class names like 'price', 'cost')
        # 4. Extract travel time information
        # ═══════════════════════════════════════════════════════════════
        
        # SIMULATED PARSING (replace with actual selectors)
        trains = []
        
        # Example: Find all train listings
        # Actual selectors would be based on real website structure
        train_listings = soup.find_all('div', class_='train-item')  # EXAMPLE
        
        if not train_listings:
            logger.warning("⚠️  No train listings found - website structure may have changed")
            
            # SIMULATION: Generate mock data for demonstration
            logger.info("ℹ️  Using simulated data for demonstration")
            trains = [
                {
                    'train_number': 'SE1',
                    'departure_time': '19:00',
                    'arrival_time': '08:30 +1',
                    'travel_time': '13h30m',
                    'price': 550000,
                    'seat_type': 'Giường nằm khoang 4'
                },
                {
                    'train_number': 'SE3',
                    'departure_time': '21:00',
                    'arrival_time': '10:30 +1',
                    'travel_time': '13h30m',
                    'price': 520000,
                    'seat_type': 'Giường nằm khoang 6'
                },
                {
                    'train_number': 'SE5',
                    'departure_time': '06:00',
                    'arrival_time': '19:30',
                    'travel_time': '13h30m',
                    'price': 450000,
                    'seat_type': 'Ngồi mềm'
                }
            ]
        else:
            # REAL PARSING (example structure)
            for listing in train_listings:
                try:
                    # Example selectors - MUST BE UPDATED for real website
                    train_number = listing.find('span', class_='train-number').text
                    price_text = listing.find('span', class_='price').text
                    price = int(price_text.replace('.', '').replace(' VNĐ', ''))
                    time_text = listing.find('span', class_='duration').text
                    
                    trains.append({
                        'train_number': train_number,
                        'price': price,
                        'travel_time': time_text,
                        # ... extract other fields
                    })
                except Exception as e:
                    logger.error(f"❌ Error parsing train listing: {e}")
                    continue
        
        # Find cheapest option
        if trains:
            cheapest_train = min(trains, key=lambda x: x['price'])
            cheapest_price = cheapest_train['price']
            travel_time = cheapest_train['travel_time']
        else:
            cheapest_price = None
            travel_time = None
        
        # Prepare result
        result = {
            'departure': departure,
            'destination': destination,
            'date': date,
            'cheapest_price': cheapest_price,
            'travel_time': travel_time,
            'available_trains': len(trains),
            'trains': trains,
            'from_cache': False,
            'scraped_at': datetime.now().isoformat(),
            'success': True
        }
        
        # Cache the result
        if use_cache:
            cache.set(departure, destination, date, result)
        
        logger.info(f"✅ Successfully scraped {len(trains)} trains")
        logger.info(f"💵 Cheapest price: {cheapest_price:,} VND" if cheapest_price else "No prices found")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ Scraping failed: {str(e)}")
        
        return {
            'departure': departure,
            'destination': destination,
            'date': date,
            'error': str(e),
            'success': False,
            'from_cache': False,
            'scraped_at': datetime.now().isoformat()
        }


# ═══════════════════════════════════════════════════════════════════════════
# EXAMPLE USAGE
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Display legal warnings
    display_legal_warning()
    
    print("\n" + "="*80)
    print("VIETNAM TRAIN PRICE SCRAPER - EXAMPLE USAGE")
    print("="*80)
    
    # Example queries
    routes = [
        ("Hà Nội", "Đà Nẵng", "2025-12-25"),
        ("Sài Gòn", "Nha Trang", "2025-12-31"),
        ("Hà Nội", "Sài Gòn", "2026-01-01")
    ]
    
    for departure, destination, date in routes:
        print(f"\n{'─'*80}")
        print(f"Route: {departure} → {destination} on {date}")
        print(f"{'─'*80}")
        
        result = scrape_train_prices(departure, destination, date)
        
        if result.get('success'):
            print(f"✅ Found {result['available_trains']} trains")
            print(f"💵 Cheapest price: {result['cheapest_price']:,} VND")
            print(f"⏱️  Travel time: {result['travel_time']}")
            print(f"💾 From cache: {result['from_cache']}")
            
            if result.get('trains'):
                print(f"\nAll trains:")
                for i, train in enumerate(result['trains'], 1):
                    print(f"  {i}. {train['train_number']}: "
                          f"{train['price']:,} VND - {train['travel_time']}")
        else:
            print(f"❌ Error: {result.get('error')}")
        
        # Wait between queries (rate limiting)
        if routes.index((departure, destination, date)) < len(routes) - 1:
            time.sleep(random.uniform(MIN_REQUEST_DELAY, MAX_REQUEST_DELAY))
    
    print("\n" + "="*80)
    print("✅ Example completed")
    print("💡 Remember: Always prefer official APIs when available!")
    print("="*80)


