import sys
import os
from pathlib import Path

# Setup paths
BACKEND_DIR = Path(__file__).parent / "vivu_backend"
sys.path.append(str(BACKEND_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vivu_core.settings')
import django
django.setup()

from vivu_backend.tools.geo_tools import get_geo_tools

def test_geo():
    geo = get_geo_tools()
    
    print("Testing HCM -> Vung Tau")
    r1 = geo.calculate_distance_time("Ho Chi Minh City", "Vung Tau")
    print(f"Result: {r1}")
    
    print("Testing Hanoi -> Haiphong")
    r2 = geo.calculate_distance_time("Hanoi", "Haiphong")
    print(f"Result: {r2}")
    
    print("Testing HCM -> Da Nang")
    r3 = geo.calculate_distance_time("Ho Chi Minh City", "Da Nang")
    print(f"Result: {r3}")

if __name__ == "__main__":
    test_geo()
