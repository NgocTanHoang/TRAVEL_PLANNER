"""
Kiểm tra lat/lon của các địa điểm từ RAG
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.append(str(project_root))

from agents.rag_agent import get_rag_agent
from utils.geocoding_helper import get_geocoding_helper

def check_latlon():
    """Check lat/lon của các gợi ý"""
    
    print("="*80)
    print("🔍 CHECKING LAT/LON FROM RAG")
    print("="*80)
    
    rag_agent = get_rag_agent()
    geocoding = get_geocoding_helper()
    
    # Get recommendations
    rag_results = rag_agent.get_recommendations(
        destination="TP.HCM",
        budget=2000000,
        days=2,
        travelers=2,
        interests="biển, hải sản"
    )
    
    # Check hotels
    print(f"\n🏨 HOTELS:")
    print(f"{'='*80}")
    hotels = rag_results['recommendations']['hotels']
    for i, hotel in enumerate(hotels[:3], 1):
        lat = hotel.get('latitude')
        lon = hotel.get('longitude')
        print(f"\n{i}. {hotel.get('name', 'N/A')}")
        print(f"   Lat/Lon: {lat}, {lon}")
        print(f"   Type: lat={type(lat)}, lon={type(lon)}")
        
        if lat and lon:
            try:
                # Try to geocode
                info = geocoding.get_detailed_info(lat, lon)
                if info:
                    print(f"   ✅ Address: {info.get('formatted', 'N/A')[:80]}")
                else:
                    print(f"   ❌ No address returned")
            except Exception as e:
                print(f"   ❌ Error: {e}")
        else:
            print(f"   ⚠️  No lat/lon available")
    
    # Check restaurants
    print(f"\n🍜 RESTAURANTS:")
    print(f"{'='*80}")
    restaurants = rag_results['recommendations']['restaurants']
    for i, rest in enumerate(restaurants[:3], 1):
        lat = rest.get('latitude')
        lon = rest.get('longitude')
        print(f"\n{i}. {rest.get('name', 'N/A')}")
        print(f"   Lat/Lon: {lat}, {lon}")
        print(f"   Type: lat={type(lat)}, lon={type(lon)}")
        
        if lat and lon:
            try:
                # Try to geocode
                info = geocoding.get_detailed_info(lat, lon)
                if info:
                    print(f"   ✅ Address: {info.get('formatted', 'N/A')[:80]}")
                else:
                    print(f"   ❌ No address returned")
            except Exception as e:
                print(f"   ❌ Error: {e}")
        else:
            print(f"   ⚠️  No lat/lon available")
    
    print(f"\n{'='*80}")
    print(f"✅ DONE!")
    print(f"{'='*80}")

if __name__ == "__main__":
    check_latlon()

