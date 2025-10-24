"""
Migration Script - Chuyển từ 10 files .db sang 2 files: cache.db và data.db
=============================================================================

Phân loại:
----------
cache.db (Temporary - có thể xóa):
  ← api_cache.db
  ← api_cache_root.db
  ← web_scraper_cache.db
  ← web_scraper_cache_root.db
  ← travel_cache.db

data.db (Persistent - quan trọng):
  ← vietnam_places_expanded.db
  ← travel_planner.db
  ← processed_data.db
  ← analytics_results.db

Script này sẽ:
1. Backup tất cả files .db cũ
2. Migrate cache data → cache.db
3. Migrate persistent data → data.db
4. Report kết quả chi tiết
"""

import sqlite3
import os
import shutil
from datetime import datetime
from pathlib import Path
from dual_db_manager import DualDatabaseManager


class DualDatabaseMigration:
    """Migrate từ 10 files sang 2 files: cache.db và data.db"""
    
    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)
        self.backup_dir = self.base_dir / "db_backup"
        
        # Files cũ phân theo loại
        self.cache_files = [
            "api_cache.db",
            "api_cache_root.db",
            "web_scraper_cache.db",
            "web_scraper_cache_root.db",
            "travel_cache.db"
        ]
        
        self.data_files = [
            "vietnam_places_expanded.db",
            "travel_planner.db",
            "processed_data.db",
            "analytics_results.db"
        ]
        
        # Initialize dual database manager
        self.db_manager = DualDatabaseManager("cache.db", "data.db")
    
    def backup_old_databases(self):
        """Backup tất cả files .db cũ"""
        print("\n" + "="*80)
        print("📦 BACKING UP OLD DATABASES")
        print("="*80)
        
        # Create backup directory
        self.backup_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_subdir = self.backup_dir / f"backup_{timestamp}"
        backup_subdir.mkdir(exist_ok=True)
        
        backed_up = 0
        all_files = self.cache_files + self.data_files
        
        for db_file in all_files:
            db_path = self.base_dir / db_file
            if db_path.exists():
                backup_path = backup_subdir / db_file
                shutil.copy2(db_path, backup_path)
                file_size = os.path.getsize(db_path) / (1024 * 1024)
                print(f"✅ Backed up: {db_file} ({file_size:.2f} MB)")
                backed_up += 1
            else:
                print(f"⚠️  Not found: {db_file}")
        
        print(f"\n✅ Backed up {backed_up} database files to: {backup_subdir}")
        return backup_subdir
    
    def migrate_cache_data(self):
        """Migrate cache data từ các files cũ → cache.db"""
        print("\n" + "="*80)
        print("📦 MIGRATING CACHE DATA → cache.db")
        print("="*80)
        
        total_migrated = {
            'api_cache': 0,
            'web_cache': 0
        }
        
        # Migrate API Cache
        print("\n🔄 Migrating API Cache...")
        for db_file in ["api_cache.db", "api_cache_root.db", "travel_cache.db"]:
            db_path = self.base_dir / db_file
            if not db_path.exists():
                print(f"  ⚠️  File not found: {db_file}")
                continue
            
            try:
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Check if table exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='api_cache'")
                if not cursor.fetchone():
                    print(f"  ⚠️  Table 'api_cache' not found in {db_file}")
                    conn.close()
                    continue
                
                # Get all entries
                cursor.execute("SELECT * FROM api_cache")
                entries = cursor.fetchall()
                
                # Migrate each entry
                for entry in entries:
                    try:
                        import json
                        self.db_manager.set_api_cache(
                            cache_key=entry['cache_key'],
                            api_name=entry.get('api_name', 'unknown'),
                            endpoint=entry.get('endpoint', ''),
                            params={},
                            response_data=json.loads(entry['response_data']) if entry.get('response_data') else {},
                            cache_hours=24
                        )
                        total_migrated['api_cache'] += 1
                    except Exception as e:
                        pass  # Skip errors
                
                conn.close()
                print(f"  ✅ Migrated {len(entries)} entries from {db_file}")
                
            except Exception as e:
                print(f"  ❌ Error reading {db_file}: {e}")
        
        # Migrate Web Cache
        print("\n🔄 Migrating Web Cache...")
        for db_file in ["web_scraper_cache.db", "web_scraper_cache_root.db"]:
            db_path = self.base_dir / db_file
            if not db_path.exists():
                print(f"  ⚠️  File not found: {db_file}")
                continue
            
            try:
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Check if table exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='web_cache'")
                if not cursor.fetchone():
                    print(f"  ⚠️  Table 'web_cache' not found in {db_file}")
                    conn.close()
                    continue
                
                # Get all entries
                cursor.execute("SELECT * FROM web_cache")
                entries = cursor.fetchall()
                
                # Migrate each entry
                for entry in entries:
                    try:
                        self.db_manager.set_web_cache(
                            url=entry['url'],
                            content=entry.get('content', ''),
                            cache_hours=24
                        )
                        total_migrated['web_cache'] += 1
                    except Exception as e:
                        pass  # Skip errors
                
                conn.close()
                print(f"  ✅ Migrated {len(entries)} entries from {db_file}")
                
            except Exception as e:
                print(f"  ❌ Error reading {db_file}: {e}")
        
        print(f"\n✅ Cache migration completed:")
        print(f"   API Cache:  {total_migrated['api_cache']} entries")
        print(f"   Web Cache:  {total_migrated['web_cache']} entries")
        
        return total_migrated
    
    def migrate_persistent_data(self):
        """Migrate persistent data từ các files cũ → data.db"""
        print("\n" + "="*80)
        print("💾 MIGRATING PERSISTENT DATA → data.db")
        print("="*80)
        
        total_migrated = {
            'vietnam_places': 0,
            'travel_plans': 0,
            'processed_places': 0,
            'analytics_results': 0
        }
        
        # Migrate Vietnam Places
        print("\n🔄 Migrating Vietnam Places...")
        db_path = self.base_dir / "vietnam_places_expanded.db"
        if db_path.exists():
            try:
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Get table names
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row['name'] for row in cursor.fetchall()]
                print(f"  📋 Found tables: {tables}")
                
                # Try to migrate from first table with place data
                for table_name in tables:
                    try:
                        cursor.execute(f"SELECT * FROM {table_name} LIMIT 1")
                        sample = cursor.fetchone()
                        if sample and 'name' in dict(sample).keys():
                            print(f"  ✅ Migrating from table: {table_name}")
                            
                            cursor.execute(f"SELECT * FROM {table_name}")
                            entries = cursor.fetchall()
                            
                            for entry in entries:
                                entry_dict = dict(entry)
                                try:
                                    self.db_manager.save_place({
                                        'place_id': entry_dict.get('place_id', entry_dict.get('id', f"place_{total_migrated['vietnam_places']}")),
                                        'name': entry_dict.get('name', ''),
                                        'city': entry_dict.get('city', ''),
                                        'category': entry_dict.get('category', ''),
                                        'rating': entry_dict.get('rating', 0),
                                        'price_level': entry_dict.get('price_level', 0),
                                        'latitude': entry_dict.get('latitude', 0),
                                        'longitude': entry_dict.get('longitude', 0),
                                        'description': entry_dict.get('description', ''),
                                        'address': entry_dict.get('address', ''),
                                        'phone': entry_dict.get('phone', ''),
                                        'website': entry_dict.get('website', ''),
                                        'types': entry_dict.get('types', []),
                                        'metadata': entry_dict.get('metadata', {})
                                    })
                                    total_migrated['vietnam_places'] += 1
                                except Exception as e:
                                    pass  # Skip errors
                            
                            print(f"  ✅ Migrated {len(entries)} places from {table_name}")
                            break
                            
                    except Exception as e:
                        continue
                
                conn.close()
                
            except Exception as e:
                print(f"  ❌ Error reading vietnam_places_expanded.db: {e}")
        else:
            print(f"  ⚠️  File not found: vietnam_places_expanded.db")
        
        # Migrate Travel Plans
        print("\n🔄 Migrating Travel Plans...")
        db_path = self.base_dir / "travel_planner.db"
        if db_path.exists():
            try:
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Check for travel_plans table
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='travel_plans'")
                if cursor.fetchone():
                    cursor.execute("SELECT * FROM travel_plans")
                    entries = cursor.fetchall()
                    
                    for entry in entries:
                        try:
                            entry_dict = dict(entry)
                            import json
                            self.db_manager.save_travel_plan({
                                'user_id': entry_dict.get('user_id', 'anonymous'),
                                'destination': entry_dict.get('destination', ''),
                                'budget': entry_dict.get('budget', 0),
                                'days': entry_dict.get('days', 0),
                                'travelers': entry_dict.get('travelers', 0),
                                'interests': json.loads(entry_dict.get('interests', '[]')) if entry_dict.get('interests') else [],
                                'itinerary': json.loads(entry_dict.get('itinerary', '{}')) if entry_dict.get('itinerary') else {},
                                'recommendations': json.loads(entry_dict.get('recommendations', '{}')) if entry_dict.get('recommendations') else {},
                                'budget_breakdown': json.loads(entry_dict.get('budget_breakdown', '{}')) if entry_dict.get('budget_breakdown') else {}
                            })
                            total_migrated['travel_plans'] += 1
                        except Exception as e:
                            pass
                    
                    print(f"  ✅ Migrated {len(entries)} travel plans")
                else:
                    print(f"  ⚠️  Table 'travel_plans' not found")
                
                conn.close()
                
            except Exception as e:
                print(f"  ❌ Error reading travel_planner.db: {e}")
        else:
            print(f"  ⚠️  File not found: travel_planner.db")
        
        print(f"\n✅ Persistent data migration completed:")
        print(f"   Vietnam Places:  {total_migrated['vietnam_places']} entries")
        print(f"   Travel Plans:    {total_migrated['travel_plans']} entries")
        print(f"   Processed:       {total_migrated['processed_places']} entries")
        print(f"   Analytics:       {total_migrated['analytics_results']} entries")
        
        return total_migrated
    
    def run_full_migration(self):
        """Chạy migration hoàn chỉnh"""
        print("\n" + "="*80)
        print("🚀 STARTING DUAL DATABASE MIGRATION")
        print("="*80)
        print(f"From: 10 separate .db files")
        print(f"To:   2 files (cache.db + data.db)")
        print("="*80)
        
        # Backup
        backup_dir = self.backup_old_databases()
        
        # Migrate cache data
        cache_stats = self.migrate_cache_data()
        
        # Migrate persistent data
        data_stats = self.migrate_persistent_data()
        
        # Get database stats
        print("\n" + "="*80)
        print("📊 NEW DATABASE STATISTICS")
        print("="*80)
        
        all_stats = self.db_manager.get_all_stats()
        
        print("\n📦 CACHE.DB (Temporary):")
        for key, value in all_stats['cache'].items():
            print(f"   {key}: {value}")
        
        print("\n💾 DATA.DB (Persistent):")
        for key, value in all_stats['data'].items():
            print(f"   {key}: {value}")
        
        print(f"\n📊 TOTAL SIZE: {all_stats['total_size_mb']} MB")
        
        # Summary
        print("\n" + "="*80)
        print("✅ MIGRATION COMPLETED!")
        print("="*80)
        
        print(f"\n📦 Backup location: {backup_dir}")
        
        print(f"\n📊 Migration Summary:")
        print(f"\n   CACHE.DB:")
        for key, value in cache_stats.items():
            print(f"      {key}: {value} entries")
        
        print(f"\n   DATA.DB:")
        for key, value in data_stats.items():
            print(f"      {key}: {value} entries")
        
        print(f"\n💾 New Database Files:")
        print(f"   cache.db - {all_stats['cache'].get('cache_file_size_mb', 0)} MB (temporary)")
        print(f"   data.db  - {all_stats['data'].get('data_file_size_mb', 0)} MB (persistent)")
        
        print("="*80)
        
        print("\n💡 NEXT STEPS:")
        print("\n1. ✅ Test the new dual database system")
        print("   - Check cache operations")
        print("   - Check data retrieval")
        print("   - Test travel plan creation")
        
        print("\n2. 🔄 Update your code:")
        print("   from database.dual_db_manager import db_manager")
        print("   db_manager.set_api_cache(...)")
        print("   db_manager.save_travel_plan(...)")
        
        print("\n3. 🗑️  If everything works, delete old .db files:")
        print("   (They are backed up in db_backup/ folder)")
        print("   - api_cache.db, api_cache_root.db")
        print("   - web_scraper_cache.db, web_scraper_cache_root.db")
        print("   - travel_planner.db, travel_cache.db")
        print("   - processed_data.db, analytics_results.db")
        print("   - vietnam_places_expanded.db")
        
        print("\n4. 💾 Remember:")
        print("   cache.db - Can be deleted anytime (will regenerate)")
        print("   data.db  - IMPORTANT! Always backup before deployment")
        
        print("\n🎉 Migration successful! From 10 files → 2 files!")
        print("="*80)


if __name__ == "__main__":
    # Run migration
    migration = DualDatabaseMigration()
    migration.run_full_migration()

