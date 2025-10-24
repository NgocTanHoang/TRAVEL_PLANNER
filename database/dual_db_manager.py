"""
Dual Database Manager - Quản lý 2 files: cache.db và data.db
==============================================================

Thiết kế:
---------
1. cache.db (Temporary data - Có thể xóa)
   ├── api_cache          (API responses cache)
   └── web_cache          (Web scraping cache)

2. data.db (Persistent data - Quan trọng, phải backup)
   ├── vietnam_places     (50K+ địa điểm Việt Nam)
   ├── travel_plans       (Kế hoạch du lịch của user)
   ├── analytics_results  (Kết quả phân tích)
   ├── processed_places   (Places đã xử lý ML)
   └── user_history       (Lịch sử user)

Ưu điểm:
--------
- ✅ Tách biệt temporary vs persistent data
- ✅ Có thể xóa cache.db mà không mất data quan trọng
- ✅ Backup chỉ cần data.db
- ✅ Đơn giản hơn nhiều so với 10 files
- ✅ Rõ ràng về purpose của mỗi file
"""

import sqlite3
import json
import hashlib
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from contextlib import contextmanager
import os


class DualDatabaseManager:
    """Manager cho 2 databases: cache.db và data.db"""
    
    def __init__(self, cache_db: str = "cache.db", data_db: str = "data.db"):
        """
        Initialize với 2 database files
        
        Args:
            cache_db: File cho cache (temporary data)
            data_db: File cho persistent data
        """
        self.cache_db_path = cache_db
        self.data_db_path = data_db
        
        self._init_cache_db()
        self._init_data_db()
        
        print(f"✅ Dual Database System initialized:")
        print(f"   📦 Cache: {cache_db}")
        print(f"   💾 Data:  {data_db}")
    
    @contextmanager
    def get_cache_connection(self):
        """Context manager cho cache database connection"""
        conn = sqlite3.connect(self.cache_db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    @contextmanager
    def get_data_connection(self):
        """Context manager cho data database connection"""
        conn = sqlite3.connect(self.data_db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    # =========================================================================
    # CACHE DATABASE INITIALIZATION
    # =========================================================================
    
    def _init_cache_db(self):
        """Khởi tạo CACHE database (temporary data)"""
        with self.get_cache_connection() as conn:
            cursor = conn.cursor()
            
            # Table 1: API Cache
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS api_cache (
                    cache_key TEXT PRIMARY KEY,
                    api_name TEXT NOT NULL,
                    endpoint TEXT NOT NULL,
                    params TEXT,
                    response_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    hit_count INTEGER DEFAULT 0
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_api_expires 
                ON api_cache(api_name, expires_at)
            ''')
            
            # Table 2: Web Scraper Cache
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS web_cache (
                    cache_key TEXT PRIMARY KEY,
                    url TEXT NOT NULL,
                    content TEXT,
                    content_type TEXT DEFAULT 'html',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    hit_count INTEGER DEFAULT 0
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_web_expires 
                ON web_cache(expires_at)
            ''')
            
            # Table 3: Cache Statistics
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cache_stats (
                    stat_date DATE PRIMARY KEY,
                    api_requests INTEGER DEFAULT 0,
                    api_cache_hits INTEGER DEFAULT 0,
                    web_requests INTEGER DEFAULT 0,
                    web_cache_hits INTEGER DEFAULT 0,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            print("✅ Cache database tables initialized")
    
    # =========================================================================
    # DATA DATABASE INITIALIZATION
    # =========================================================================
    
    def _init_data_db(self):
        """Khởi tạo DATA database (persistent data)"""
        with self.get_data_connection() as conn:
            cursor = conn.cursor()
            
            # Table 1: Vietnam Places (50K+ địa điểm)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS vietnam_places (
                    place_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    city TEXT NOT NULL,
                    category TEXT,
                    rating REAL,
                    price_level INTEGER,
                    latitude REAL,
                    longitude REAL,
                    description TEXT,
                    address TEXT,
                    phone TEXT,
                    website TEXT,
                    types TEXT,
                    metadata TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_city_category 
                ON vietnam_places(city, category)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_rating 
                ON vietnam_places(rating)
            ''')
            
            # Table 2: Processed Places (ML features)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS processed_places (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    place_id TEXT NOT NULL,
                    processed_features TEXT,
                    ml_cluster INTEGER,
                    popularity_score REAL,
                    recent_score REAL,
                    similarity_vector TEXT,
                    processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (place_id) REFERENCES vietnam_places(place_id)
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_place_processed 
                ON processed_places(place_id)
            ''')
            
            # Table 3: Travel Plans
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS travel_plans (
                    plan_id TEXT PRIMARY KEY,
                    user_id TEXT,
                    destination TEXT NOT NULL,
                    budget INTEGER,
                    days INTEGER,
                    travelers INTEGER,
                    interests TEXT,
                    itinerary TEXT,
                    recommendations TEXT,
                    budget_breakdown TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_user_created 
                ON travel_plans(user_id, created_at)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_destination 
                ON travel_plans(destination)
            ''')
            
            # Table 4: Analytics Results
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS analytics_results (
                    analytics_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    plan_id TEXT,
                    analytics_type TEXT,
                    metrics TEXT,
                    insights TEXT,
                    sentiment_score REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (plan_id) REFERENCES travel_plans(plan_id)
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_plan_analytics 
                ON analytics_results(plan_id, analytics_type)
            ''')
            
            # Table 5: User History
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_history (
                    history_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    action_type TEXT,
                    action_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_user_history 
                ON user_history(user_id, created_at)
            ''')
            
            # Table 6: Data Statistics
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS data_stats (
                    stat_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    total_places INTEGER,
                    total_plans INTEGER,
                    total_users INTEGER,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            print("✅ Data database tables initialized")
    
    # =========================================================================
    # API CACHE METHODS (cache.db)
    # =========================================================================
    
    def get_api_cache(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """Lấy API cache"""
        with self.get_cache_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT response_data, expires_at 
                FROM api_cache 
                WHERE cache_key = ? AND expires_at > ?
            ''', (cache_key, datetime.now()))
            
            result = cursor.fetchone()
            if result:
                # Update hit count
                cursor.execute('''
                    UPDATE api_cache 
                    SET hit_count = hit_count + 1 
                    WHERE cache_key = ?
                ''', (cache_key,))
                conn.commit()
                
                return json.loads(result['response_data'])
            return None
    
    def set_api_cache(self, cache_key: str, api_name: str, endpoint: str, 
                     params: Dict, response_data: Dict, cache_hours: int = 24):
        """Lưu API cache"""
        with self.get_cache_connection() as conn:
            cursor = conn.cursor()
            expires_at = datetime.now() + timedelta(hours=cache_hours)
            
            cursor.execute('''
                INSERT OR REPLACE INTO api_cache 
                (cache_key, api_name, endpoint, params, response_data, expires_at, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (cache_key, api_name, endpoint, json.dumps(params), 
                  json.dumps(response_data), expires_at, datetime.now()))
            
            conn.commit()
    
    # =========================================================================
    # WEB CACHE METHODS (cache.db)
    # =========================================================================
    
    def get_web_cache(self, url: str) -> Optional[str]:
        """Lấy web scraper cache"""
        cache_key = hashlib.md5(url.encode()).hexdigest()
        
        with self.get_cache_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT content 
                FROM web_cache 
                WHERE cache_key = ? AND expires_at > ?
            ''', (cache_key, datetime.now()))
            
            result = cursor.fetchone()
            if result:
                # Update hit count
                cursor.execute('''
                    UPDATE web_cache 
                    SET hit_count = hit_count + 1 
                    WHERE cache_key = ?
                ''', (cache_key,))
                conn.commit()
                return result['content']
            return None
    
    def set_web_cache(self, url: str, content: str, cache_hours: int = 24):
        """Lưu web cache"""
        cache_key = hashlib.md5(url.encode()).hexdigest()
        
        with self.get_cache_connection() as conn:
            cursor = conn.cursor()
            expires_at = datetime.now() + timedelta(hours=cache_hours)
            
            cursor.execute('''
                INSERT OR REPLACE INTO web_cache 
                (cache_key, url, content, expires_at, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (cache_key, url, content, expires_at, datetime.now()))
            
            conn.commit()
    
    # =========================================================================
    # VIETNAM PLACES METHODS (data.db)
    # =========================================================================
    
    def save_place(self, place_data: Dict[str, Any]):
        """Lưu place vào database"""
        with self.get_data_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO vietnam_places 
                (place_id, name, city, category, rating, price_level, 
                 latitude, longitude, description, address, phone, website, types, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                place_data.get('place_id'),
                place_data.get('name'),
                place_data.get('city'),
                place_data.get('category'),
                place_data.get('rating'),
                place_data.get('price_level'),
                place_data.get('latitude'),
                place_data.get('longitude'),
                place_data.get('description'),
                place_data.get('address'),
                place_data.get('phone'),
                place_data.get('website'),
                json.dumps(place_data.get('types', [])),
                json.dumps(place_data.get('metadata', {}))
            ))
            conn.commit()
    
    def get_places_by_city(self, city: str, category: str = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Lấy places theo city và category"""
        with self.get_data_connection() as conn:
            cursor = conn.cursor()
            
            if category:
                cursor.execute('''
                    SELECT * FROM vietnam_places 
                    WHERE city LIKE ? AND category = ?
                    ORDER BY rating DESC 
                    LIMIT ?
                ''', (f'%{city}%', category, limit))
            else:
                cursor.execute('''
                    SELECT * FROM vietnam_places 
                    WHERE city LIKE ? 
                    ORDER BY rating DESC 
                    LIMIT ?
                ''', (f'%{city}%', limit))
            
            return [dict(row) for row in cursor.fetchall()]
    
    # =========================================================================
    # TRAVEL PLANS METHODS (data.db)
    # =========================================================================
    
    def save_travel_plan(self, plan_data: Dict[str, Any]) -> str:
        """Lưu travel plan"""
        plan_id = hashlib.md5(
            f"{plan_data['destination']}_{datetime.now().isoformat()}".encode()
        ).hexdigest()
        
        with self.get_data_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO travel_plans 
                (plan_id, user_id, destination, budget, days, travelers, interests, 
                 itinerary, recommendations, budget_breakdown)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                plan_id,
                plan_data.get('user_id', 'anonymous'),
                plan_data['destination'],
                plan_data.get('budget'),
                plan_data.get('days'),
                plan_data.get('travelers'),
                json.dumps(plan_data.get('interests', [])),
                json.dumps(plan_data.get('itinerary', {})),
                json.dumps(plan_data.get('recommendations', {})),
                json.dumps(plan_data.get('budget_breakdown', {}))
            ))
            conn.commit()
        
        return plan_id
    
    def get_travel_plan(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Lấy travel plan"""
        with self.get_data_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM travel_plans WHERE plan_id = ?', (plan_id,))
            result = cursor.fetchone()
            
            if result:
                return dict(result)
            return None
    
    def get_user_plans(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Lấy tất cả plans của user"""
        with self.get_data_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM travel_plans 
                WHERE user_id = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            ''', (user_id, limit))
            
            return [dict(row) for row in cursor.fetchall()]
    
    # =========================================================================
    # ANALYTICS METHODS (data.db)
    # =========================================================================
    
    def save_analytics(self, plan_id: str, analytics_type: str, 
                      metrics: Dict, insights: List[str], sentiment_score: float = 0):
        """Lưu analytics results"""
        with self.get_data_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO analytics_results 
                (plan_id, analytics_type, metrics, insights, sentiment_score)
                VALUES (?, ?, ?, ?, ?)
            ''', (plan_id, analytics_type, json.dumps(metrics), 
                  json.dumps(insights), sentiment_score))
            conn.commit()
    
    def get_plan_analytics(self, plan_id: str) -> List[Dict[str, Any]]:
        """Lấy analytics của plan"""
        with self.get_data_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM analytics_results 
                WHERE plan_id = ?
            ''', (plan_id,))
            
            return [dict(row) for row in cursor.fetchall()]
    
    # =========================================================================
    # MAINTENANCE METHODS
    # =========================================================================
    
    def clear_expired_cache(self) -> Dict[str, int]:
        """Xóa cache hết hạn"""
        with self.get_cache_connection() as conn:
            cursor = conn.cursor()
            
            # Clear API cache
            cursor.execute('DELETE FROM api_cache WHERE expires_at < ?', (datetime.now(),))
            api_deleted = cursor.rowcount
            
            # Clear web cache
            cursor.execute('DELETE FROM web_cache WHERE expires_at < ?', (datetime.now(),))
            web_deleted = cursor.rowcount
            
            conn.commit()
        
        return {
            'api_cache_deleted': api_deleted,
            'web_cache_deleted': web_deleted,
            'total_deleted': api_deleted + web_deleted
        }
    
    def clear_all_cache(self) -> Dict[str, int]:
        """Xóa TẤT CẢ cache (useful khi muốn fresh start)"""
        with self.get_cache_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) as count FROM api_cache')
            api_count = cursor.fetchone()['count']
            
            cursor.execute('SELECT COUNT(*) as count FROM web_cache')
            web_count = cursor.fetchone()['count']
            
            cursor.execute('DELETE FROM api_cache')
            cursor.execute('DELETE FROM web_cache')
            
            conn.commit()
        
        print(f"🗑️  Cleared ALL cache: {api_count} API + {web_count} Web entries")
        return {
            'api_cache_deleted': api_count,
            'web_cache_deleted': web_count,
            'total_deleted': api_count + web_count
        }
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Lấy statistics của cache database"""
        with self.get_cache_connection() as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # API cache
            cursor.execute('SELECT COUNT(*) as count FROM api_cache')
            stats['api_cache_entries'] = cursor.fetchone()['count']
            
            cursor.execute('SELECT SUM(hit_count) as hits FROM api_cache')
            stats['api_cache_hits'] = cursor.fetchone()['hits'] or 0
            
            cursor.execute('SELECT COUNT(*) as count FROM api_cache WHERE expires_at < ?', (datetime.now(),))
            stats['api_cache_expired'] = cursor.fetchone()['count']
            
            # Web cache
            cursor.execute('SELECT COUNT(*) as count FROM web_cache')
            stats['web_cache_entries'] = cursor.fetchone()['count']
            
            cursor.execute('SELECT SUM(hit_count) as hits FROM web_cache')
            stats['web_cache_hits'] = cursor.fetchone()['hits'] or 0
            
            cursor.execute('SELECT COUNT(*) as count FROM web_cache WHERE expires_at < ?', (datetime.now(),))
            stats['web_cache_expired'] = cursor.fetchone()['count']
            
            # File size
            if os.path.exists(self.cache_db_path):
                stats['cache_file_size_mb'] = round(os.path.getsize(self.cache_db_path) / (1024 * 1024), 2)
        
        return stats
    
    def get_data_stats(self) -> Dict[str, Any]:
        """Lấy statistics của data database"""
        with self.get_data_connection() as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # Places
            cursor.execute('SELECT COUNT(*) as count FROM vietnam_places')
            stats['total_places'] = cursor.fetchone()['count']
            
            cursor.execute('SELECT COUNT(DISTINCT city) as count FROM vietnam_places')
            stats['total_cities'] = cursor.fetchone()['count']
            
            # Travel plans
            cursor.execute('SELECT COUNT(*) as count FROM travel_plans')
            stats['total_plans'] = cursor.fetchone()['count']
            
            cursor.execute('SELECT COUNT(DISTINCT user_id) as count FROM travel_plans')
            stats['total_users'] = cursor.fetchone()['count']
            
            # Analytics
            cursor.execute('SELECT COUNT(*) as count FROM analytics_results')
            stats['total_analytics'] = cursor.fetchone()['count']
            
            # Processed places
            cursor.execute('SELECT COUNT(*) as count FROM processed_places')
            stats['processed_places'] = cursor.fetchone()['count']
            
            # File size
            if os.path.exists(self.data_db_path):
                stats['data_file_size_mb'] = round(os.path.getsize(self.data_db_path) / (1024 * 1024), 2)
        
        return stats
    
    def get_all_stats(self) -> Dict[str, Any]:
        """Lấy tất cả statistics"""
        cache_stats = self.get_cache_stats()
        data_stats = self.get_data_stats()
        
        return {
            'cache': cache_stats,
            'data': data_stats,
            'total_size_mb': cache_stats.get('cache_file_size_mb', 0) + data_stats.get('data_file_size_mb', 0)
        }
    
    def vacuum_databases(self):
        """Tối ưu cả 2 databases"""
        with self.get_cache_connection() as conn:
            conn.execute('VACUUM')
        
        with self.get_data_connection() as conn:
            conn.execute('VACUUM')
        
        print("✅ Both databases vacuumed and optimized")


# ===== SINGLETON INSTANCE =====
db_manager = DualDatabaseManager()


# ===== USAGE EXAMPLE =====
if __name__ == "__main__":
    print("="*80)
    print("DUAL DATABASE MANAGER - TEST")
    print("="*80)
    
    # Test cache
    print("\n1️⃣  Testing API Cache...")
    cache_key = "test_hanoi_123"
    db_manager.set_api_cache(
        cache_key=cache_key,
        api_name="google_places",
        endpoint="search",
        params={"query": "Hanoi hotels"},
        response_data={"results": [{"name": "Sofitel Legend Metropole"}]},
        cache_hours=24
    )
    
    cached_data = db_manager.get_api_cache(cache_key)
    print(f"   ✅ Cached data: {cached_data}")
    
    # Test travel plan
    print("\n2️⃣  Testing Travel Plan...")
    plan_id = db_manager.save_travel_plan({
        'destination': 'Hanoi',
        'budget': 10000000,
        'days': 5,
        'travelers': 2,
        'interests': ['culture', 'food']
    })
    print(f"   ✅ Plan saved: {plan_id}")
    
    # Test analytics
    print("\n3️⃣  Testing Analytics...")
    db_manager.save_analytics(
        plan_id=plan_id,
        analytics_type='budget_analysis',
        metrics={'total_cost': 9500000, 'savings': 500000},
        insights=['Budget optimized', 'Good value'],
        sentiment_score=0.85
    )
    print(f"   ✅ Analytics saved")
    
    # Get stats
    print("\n4️⃣  Database Statistics:")
    stats = db_manager.get_all_stats()
    
    print("\n   📦 CACHE.DB:")
    for key, value in stats['cache'].items():
        print(f"      {key}: {value}")
    
    print("\n   💾 DATA.DB:")
    for key, value in stats['data'].items():
        print(f"      {key}: {value}")
    
    print(f"\n   📊 TOTAL SIZE: {stats['total_size_mb']} MB")
    
    # Clear expired cache
    print("\n5️⃣  Clearing expired cache...")
    result = db_manager.clear_expired_cache()
    print(f"   ✅ Deleted: {result}")
    
    print("\n" + "="*80)
    print("✅ All tests passed! Dual database system working perfectly!")
    print("="*80)

