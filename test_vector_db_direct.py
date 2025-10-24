"""
Test trực tiếp vector DB xem có lat/lon không
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.append(str(project_root))

from agents.vector_db_agent import get_vector_db_agent

def test_vector_db_direct():
    """Test vector DB trực tiếp"""
    
    print("="*80)
    print("🔍 TESTING VECTOR DB DIRECTLY")
    print("="*80)
    
    vector_db = get_vector_db_agent()
    
    # Search for hotels in TPHCM
    print(f"\n🏨 Searching hotels in TP.HCM...")
    hotels = vector_db.semantic_search(
        query="khách sạn hotel accommodation",
        n_results=5,
        city_filter="TP.HCM"
    )
    
    print(f"   Found: {len(hotels)} hotels\n")
    
    for i, hotel in enumerate(hotels, 1):
        print(f"{i}. {hotel.get('name', 'N/A')}")
        print(f"   City: {hotel.get('city', 'N/A')}")
        print(f"   Category: {hotel.get('category', 'N/A')}")
        print(f"   Rating: {hotel.get('rating', 0)}")
        print(f"   Lat: {hotel.get('latitude')}")
        print(f"   Lon: {hotel.get('longitude')}")
        print(f"   Type: lat={type(hotel.get('latitude'))}, lon={type(hotel.get('longitude'))}")
        print()
    
    print(f"{'='*80}")

if __name__ == "__main__":
    test_vector_db_direct()

