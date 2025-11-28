"""
Script test tạo file JSON và sử dụng LLM để in ra lịch trình chi tiết
"""
import os
import sys
import django
import json
import asyncio
from pathlib import Path
from datetime import datetime

# Setup Django
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vivu_core.settings')
django.setup()

from agents.travel_agents.orchestrator_agent import OrchestratorAgent
from utils.itinerary_formatter import format_state_to_json, generate_itinerary_description


async def create_travel_plan_and_generate_description(
    origin: str,
    destination: str,
    start_date: str,
    days: int,
    travelers: int,
    travel_style: str,
    rooms: int = 1
):
    """
    Tạo travel plan và generate description bằng LLM
    """
    print(f"🚀 Đang tạo travel plan...")
    print(f"   Điểm đi: {origin}")
    print(f"   Điểm đến: {destination}")
    print(f"   Ngày xuất phát: {start_date}")
    print(f"   Số ngày: {days}")
    print(f"   Số người: {travelers}")
    print(f"   Phong cách: {travel_style}")
    print()
    
    # Tạo state ban đầu
    state = {
        'origin': origin,
        'destination': destination,
        'start_date': start_date,
        'days': days,
        'travelers': travelers,
        'travel_style': travel_style,
        'rooms': rooms
    }
    
    # Chạy orchestrator agent
    orchestrator = OrchestratorAgent()
    result_state = await orchestrator.execute(state)
    
    # Format thành JSON
    json_data = format_state_to_json(result_state)
    
    # Generate description bằng LLM
    print("🤖 Đang sử dụng LLM để tạo mô tả lịch trình...")
    description = generate_itinerary_description(json_data, llm=None, force_llm=True)
    
    return result_state, json_data, description


def save_results(state: dict, json_data: dict, description: str, output_dir: str = None):
    """
    Lưu kết quả vào các file
    """
    if output_dir is None:
        output_dir = BASE_DIR / 'exports'
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(exist_ok=True)
    
    # Tạo tên file
    origin = state.get('origin', 'origin').replace(' ', '_').replace('/', '_')
    destination = state.get('destination', 'destination').replace(' ', '_').replace('/', '_')
    start_date = state.get('start_date', '').replace('-', '')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    base_filename = f"{origin}_to_{destination}_{start_date}_{timestamp}"
    
    # 1. Lưu JSON
    json_file = output_dir / f"{base_filename}_itinerary.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    print(f"✅ Đã lưu JSON: {json_file}")
    
    # 2. Lưu description từ LLM
    description_file = output_dir / f"{base_filename}_description.txt"
    with open(description_file, 'w', encoding='utf-8') as f:
        f.write(description)
    print(f"✅ Đã lưu description: {description_file}")
    
    # 3. In ra console để xem
    print("\n" + "="*80)
    print("📋 LỊCH TRÌNH ĐƯỢC TẠO BỞI LLM:")
    print("="*80)
    print(description)
    print("="*80)
    
    # 4. In thống kê JSON
    print("\n📊 Thống kê JSON:")
    print(f"   - LICHTRINH: {len(json_data.get('LICHTRINH', []))} bản ghi")
    print(f"   - DIADIEM: {len(json_data.get('DIADIEM', []))} địa điểm")
    print(f"   - LICHTRINH_DIADIEM: {len(json_data.get('LICHTRINH_DIADIEM', []))} liên kết")
    print(f"   - PHUONGTIEN_GIAOTHONG: {len(json_data.get('PHUONGTIEN_GIAOTHONG', []))} phương tiện")
    print(f"   - HOATDONG: {len(json_data.get('HOATDONG', []))} hoạt động")
    
    return {
        'json_file': json_file,
        'description_file': description_file
    }


async def main():
    """Main function"""
    # Thông tin chuyến đi
    origin = "Cần Thơ"
    destination = "Bắc Ninh"
    start_date = "2025-11-30"
    days = 5
    travelers = 2
    travel_style = "eco"  # Sinh thái bền vững
    rooms = 1
    
    try:
        # Tạo travel plan và generate description
        state, json_data, description = await create_travel_plan_and_generate_description(
            origin=origin,
            destination=destination,
            start_date=start_date,
            days=days,
            travelers=travelers,
            travel_style=travel_style,
            rooms=rooms
        )
        
        # Kiểm tra lỗi
        if state.get('error'):
            print(f"❌ Lỗi: {state.get('error')}")
            return
        
        # Lưu kết quả
        print()
        files = save_results(state, json_data, description)
        
        print()
        print("=" * 80)
        print("✅ HOÀN TẤT!")
        print("=" * 80)
        print(f"📂 Thư mục: {files['json_file'].parent}")
        print(f"📄 Files đã tạo:")
        print(f"   - JSON: {files['json_file'].name}")
        print(f"   - Description: {files['description_file'].name}")
        
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(main())

