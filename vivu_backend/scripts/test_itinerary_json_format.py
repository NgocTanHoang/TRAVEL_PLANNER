"""
Test script đơn giản để tạo JSON và description từ dữ liệu mẫu
"""
import os
import sys
import django
import json
from pathlib import Path
from datetime import datetime, timedelta

# Fix encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Setup Django
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load .env file before Django setup
from dotenv import load_dotenv
env_path = PROJECT_ROOT.parent / '.env'
if env_path.exists():
    try:
        load_dotenv(env_path, override=True)
        print(f"✅ Loaded .env from: {env_path}")
    except Exception as e:
        print(f"⚠️ Error loading .env: {e}")
        # Try to load from parent directory
        try:
            load_dotenv(override=True)
            print("✅ Loaded .env from default location")
        except:
            print("⚠️ Could not load .env file")
else:
    print(f"⚠️ .env file not found at: {env_path}")
    # Try to load from default location
    try:
        load_dotenv(override=True)
        print("✅ Loaded .env from default location")
    except:
        pass

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vivu_core.settings')
django.setup()

# Set Groq API key and model
import os
groq_key = os.getenv('GROQ_API_KEY')
if not groq_key:
    print("❌ GROQ_API_KEY not found in environment variables")
    print("Please set GROQ_API_KEY in your .env file or environment")
    sys.exit(1)
else:
    os.environ['GROQ_MODEL'] = 'openai/gpt-oss-120b'  # Use with prefix
    print(f"✅ GROQ_API_KEY is set, using GROQ_MODEL: openai/gpt-oss-120b")

from utils.itinerary_formatter import format_state_to_json, generate_itinerary_description

# Tạo state mẫu với dữ liệu giả lập
start_date = '2025-12-15'
end_date = (datetime.strptime(start_date, '%Y-%m-%d') + timedelta(days=2)).strftime('%Y-%m-%d')

test_state = {
    'origin': 'Vũng Tàu',
    'destination': 'Đà Nẵng',
    'start_date': start_date,
    'days': 3,
    'travelers': 2,
    'travel_style': 'danh_lam_thang_canh',
    'total_cost': 12000000,
    'itinerary': {
        'itinerary': [
            {
                'day': 1,
                'date': start_date,
                'activities': [
                    {
                        'activity': {
                            'name': 'Bãi biển Mỹ Khê',
                            'description': 'Bãi biển đẹp nhất Đà Nẵng với cát trắng mịn, nước trong xanh, lý tưởng cho các hoạt động tắm biển và thư giãn.',
                            'address': 'Phạm Văn Đồng, Sơn Trà, Đà Nẵng',
                            'type': 'dia_danh',
                            'latitude': 16.0583,
                            'longitude': 108.2417,
                            'price': 0,
                            'rating': 4.6,
                            'reviews': 15000,
                            'opening_hours': {'open': '06:00', 'close': '18:00'}
                        },
                        'time_slot': '08:00-11:00'
                    },
                    {
                        'activity': {
                            'name': 'Ngũ Hành Sơn',
                            'description': 'Quần thể 5 ngọn núi đá vôi với nhiều hang động, chùa chiền cổ kính, là điểm đến tâm linh và danh lam thắng cảnh nổi tiếng.',
                            'address': 'Ngũ Hành Sơn, Đà Nẵng',
                            'type': 'dia_danh',
                            'latitude': 16.0000,
                            'longitude': 108.2667,
                            'price': 40000,
                            'rating': 4.5,
                            'reviews': 12000,
                            'opening_hours': {'open': '07:00', 'close': '17:30'}
                        },
                        'time_slot': '14:00-17:00'
                    }
                ]
            },
            {
                'day': 2,
                'date': (datetime.strptime(start_date, '%Y-%m-%d') + timedelta(days=1)).strftime('%Y-%m-%d'),
                'activities': [
                    {
                        'activity': {
                            'name': 'Bà Nà Hills',
                            'description': 'Khu du lịch trên núi với cáp treo dài nhất thế giới, vườn hoa, làng Pháp cổ, và nhiều trò chơi giải trí.',
                            'address': 'Hòa Vang, Đà Nẵng',
                            'type': 'giai_tri',
                            'latitude': 15.9983,
                            'longitude': 107.9992,
                            'price': 900000,
                            'rating': 4.7,
                            'reviews': 25000,
                            'opening_hours': {'open': '07:00', 'close': '22:00'}
                        },
                        'time_slot': '08:00-17:00'
                    },
                    {
                        'activity': {
                            'name': 'Cầu Rồng Đà Nẵng',
                            'description': 'Biểu tượng của Đà Nẵng, cầu Rồng phun lửa và nước vào cuối tuần, là điểm check-in nổi tiếng.',
                            'address': 'Cầu Rồng, Sơn Trà, Đà Nẵng',
                            'type': 'dia_danh',
                            'latitude': 16.0617,
                            'longitude': 108.2272,
                            'price': 0,
                            'rating': 4.4,
                            'reviews': 18000,
                            'opening_hours': {'open': '00:00', 'close': '23:59'}
                        },
                        'time_slot': '19:00-20:00'
                    }
                ]
            },
            {
                'day': 3,
                'date': end_date,
                'activities': [
                    {
                        'activity': {
                            'name': 'Bán đảo Sơn Trà',
                            'description': 'Khu bảo tồn thiên nhiên với rừng nguyên sinh, bãi biển hoang sơ, và điểm ngắm cảnh tuyệt đẹp.',
                            'address': 'Sơn Trà, Đà Nẵng',
                            'type': 'dia_danh',
                            'latitude': 16.1000,
                            'longitude': 108.2500,
                            'price': 0,
                            'rating': 4.6,
                            'reviews': 10000,
                            'opening_hours': {'open': '06:00', 'close': '18:00'}
                        },
                        'time_slot': '08:00-12:00'
                    },
                    {
                        'activity': {
                            'name': 'Làng Cổ Hội An',
                            'description': 'Phố cổ Hội An với kiến trúc cổ kính, đèn lồng rực rỡ, và văn hóa truyền thống độc đáo (cách Đà Nẵng 30km).',
                            'address': 'Hội An, Quảng Nam',
                            'type': 'dia_danh',
                            'latitude': 15.8801,
                            'longitude': 108.3380,
                            'price': 120000,
                            'rating': 4.8,
                            'reviews': 35000,
                            'opening_hours': {'open': '08:00', 'close': '21:00'}
                        },
                        'time_slot': '14:00-18:00'
                    }
                ]
            }
        ]
    }
}

print("=" * 80)
print("TẠO JSON VÀ MÔ TẢ LỊCH TRÌNH")
print("=" * 80)
print(f"\n📋 Lịch trình: {test_state['origin']} → {test_state['destination']}")
print(f"   Số ngày: {test_state['days']} ngày")
print(f"   Số người: {test_state['travelers']} người")
print(f"   Phong cách: {test_state['travel_style']}")

# Format to JSON
print("\n📦 Đang format thành JSON structure...")
print("-" * 80)
json_data = format_state_to_json(test_state)

# Save JSON to file
json_file = PROJECT_ROOT / 'scripts' / 'itinerary_output.json'
with open(json_file, 'w', encoding='utf-8') as f:
    json.dump(json_data, f, ensure_ascii=False, indent=2)
print(f"✅ Đã lưu JSON vào: {json_file}")

# Display JSON
print("\n" + "=" * 80)
print("📄 JSON DATA:")
print("=" * 80)
print(json.dumps(json_data, ensure_ascii=False, indent=2))

# Generate description using LLM
print("\n" + "=" * 80)
print("🤖 Đang generate mô tả bằng LLM...")
print("-" * 80)

try:
    description = generate_itinerary_description(json_data, force_llm=True)
    
    # Save description to file
    desc_file = PROJECT_ROOT / 'scripts' / 'itinerary_description.txt'
    with open(desc_file, 'w', encoding='utf-8') as f:
        f.write(description)
    print(f"✅ Đã lưu mô tả vào: {desc_file}")
    
    # Display description
    print("\n" + "=" * 80)
    print("📝 MÔ TẢ LỊCH TRÌNH (Generated by LLM):")
    print("=" * 80)
    print(description)
    
except Exception as e:
    print(f"❌ Lỗi khi generate description: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("✅ Hoàn thành!")
print("=" * 80)

