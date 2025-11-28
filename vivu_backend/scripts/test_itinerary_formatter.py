"""
Test script để kiểm tra itinerary formatter và LLM description generation
"""
import os
import sys
import django
from pathlib import Path

# Setup Django
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vivu_core.settings')
django.setup()

from utils.itinerary_formatter import format_state_to_json, generate_itinerary_description
import json

# Test data
test_state = {
    'origin': 'Đà Nẵng',
    'destination': 'Cần Thơ',
    'days': 5,
    'travelers': 2,
    'travel_style': 'shopping_giai_tri',
    'start_date': '2025-12-01',
    'total_cost': 16000000,
    'itinerary': {
        'itinerary': [
            {
                'day': 1,
                'activities': [
                    {
                        'activity': {
                            'name': 'Bến Ninh Kiều',
                            'description': 'Biểu tượng nổi tiếng của Cần Thơ, nơi giao hòa giữa sông nước và nhịp sống miền Tây.',
                            'address': 'Đường Hai Bà Trưng, Ninh Kiều, Cần Thơ',
                            'type': 'dia_danh',
                            'latitude': 10.034135,
                            'longitude': 105.786423,
                            'price': 0,
                            'rating': 4.5,
                            'reviews': 20000
                        }
                    },
                    {
                        'activity': {
                            'name': 'Cầu đi bộ Ninh Kiều',
                            'description': 'Cầu đi bộ bắc qua rạch Khai Luông, nổi bật với ánh sáng lung linh ban đêm.',
                            'address': 'Bến Ninh Kiều, Ninh Kiều, Cần Thơ',
                            'type': 'giai_tri',
                            'latitude': 10.033821,
                            'longitude': 105.786995,
                            'price': 0,
                            'rating': 4.4,
                            'reviews': 12000
                        }
                    }
                ]
            }
        ]
    }
}

print("=" * 80)
print("TEST ITINERARY FORMATTER")
print("=" * 80)

# Test format_state_to_json
print("\n1. Format state to JSON:")
print("-" * 80)
json_data = format_state_to_json(test_state)
print(json.dumps(json_data, ensure_ascii=False, indent=2))

# Test generate description
print("\n2. Generate description using LLM:")
print("-" * 80)
description = generate_itinerary_description(json_data)
print(description)

print("\n" + "=" * 80)



