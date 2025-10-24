"""
Script để populate geocode cache từ vector database
Lấy tất cả địa điểm có lat/lon và cache địa chỉ
"""

import sys
from pathlib import Path
import time

project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from agents.vector_db_agent import get_vector_db_agent
from utils.geocoding_helper import get_geocoding_helper

def populate_geocode_cache():
    """Populate geocode cache từ vector DB"""
    
    print("="*80)
    print("🗺️ POPULATING GEOCODE CACHE")
    print("="*80)
    
    # Get instances
    vector_db = get_vector_db_agent()
    geocoding = get_geocoding_helper()
    
    # Check current cache stats
    stats = geocoding.get_cache_stats()
    print(f"\n📊 Current cache:")
    print(f"   Cached addresses: {stats['total_cached']}")
    print(f"   Cities: {stats['cities']}")
    
    # Get all documents from vector DB
    print(f"\n📍 Fetching locations from Vector DB...")
    
    try:
        # Query all documents (no filter)
        results = vector_db.collection.get(
            include=['metadatas']
        )
        
        total_docs = len(results['ids'])
        print(f"   ✅ Found {total_docs:,} documents")
        
        # Extract unique lat/lon pairs
        locations = set()
        for metadata in results['metadatas']:
            lat = metadata.get('latitude')
            lon = metadata.get('longitude')
            if lat and lon:
                # Round to 4 decimals
                locations.add((round(float(lat), 4), round(float(lon), 4)))
        
        print(f"   ✅ Found {len(locations):,} unique locations")
        
        # Geocode each location
        print(f"\n🔄 Geocoding locations...")
        print(f"   (This will take a while, ~1 sec per location)")
        
        cached_count = 0
        api_calls = 0
        errors = 0
        
        for i, (lat, lon) in enumerate(locations, 1):
            try:
                # This will auto-cache if not already cached
                info = geocoding.get_detailed_info(lat, lon)
                
                if info:
                    if info.get('formatted'):
                        cached_count += 1
                        # Check if it was from cache or API
                        # (if from cache, it returns instantly)
                        api_calls += 1
                    
                    if i % 10 == 0:
                        print(f"   Progress: {i}/{len(locations)} ({i/len(locations)*100:.1f}%)")
                    
                    # Rate limit: 1 request per second for free tier
                    if i % 10 == 0:  # Sleep every 10 requests
                        time.sleep(1)
                
            except Exception as e:
                errors += 1
                if errors < 5:  # Only print first 5 errors
                    print(f"   ⚠️ Error at {lat}, {lon}: {e}")
        
        print(f"\n✅ Geocoding completed!")
        print(f"   Total processed: {len(locations):,}")
        print(f"   Successfully cached: {cached_count:,}")
        print(f"   Errors: {errors}")
        
        # Final stats
        stats_after = geocoding.get_cache_stats()
        print(f"\n📊 Final cache stats:")
        print(f"   Cached addresses: {stats_after['total_cached']:,}")
        print(f"   Cities: {stats_after['cities']}")
        print(f"   New entries: {stats_after['total_cached'] - stats['total_cached']:,}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n{'='*80}")
    print(f"✅ DONE!")
    print(f"{'='*80}")


if __name__ == "__main__":
    print("\n⚠️  WARNING: This will make many API calls to Geoapify")
    print("   Free tier limit: 3000 requests/day")
    print("   Estimated locations to cache: ~1000-2000")
    print("   Time: ~20-30 minutes")
    
    response = input("\n▶️  Continue? (y/n): ")
    if response.lower() == 'y':
        populate_geocode_cache()
    else:
        print("❌ Cancelled.")

