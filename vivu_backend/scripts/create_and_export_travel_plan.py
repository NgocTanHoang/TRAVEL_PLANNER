"""
Script để tạo travel plan và export thành file JSON
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
from utils.itinerary_formatter import format_state_to_json


async def create_travel_plan(
    origin: str,
    destination: str,
    start_date: str,
    days: int,
    travelers: int,
    travel_style: str,
    rooms: int = 1
):
    """
    Tạo travel plan đầy đủ
    
    Args:
        origin: Điểm xuất phát
        destination: Điểm đến
        start_date: Ngày bắt đầu (YYYY-MM-DD)
        days: Số ngày
        travelers: Số người
        travel_style: Phong cách du lịch
        rooms: Số phòng
    """
    print(f"🚀 Đang tạo travel plan...")
    print(f"   Điểm đi: {origin}")
    print(f"   Điểm đến: {destination}")
    print(f"   Ngày xuất phát: {start_date}")
    print(f"   Số ngày: {days}")
    print(f"   Số người: {travelers}")
    print(f"   Phong cách: {travel_style}")
    print(f"   Số phòng: {rooms}")
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
    
    return result_state


def export_to_json_files(state: dict, output_dir: str = None):
    """
    Export state thành các file JSON
    
    Args:
        state: State dictionary từ orchestrator
        output_dir: Thư mục output (nếu None, dùng exports/)
    """
    if output_dir is None:
        output_dir = BASE_DIR / 'exports'
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(exist_ok=True)
    
    # Tạo tên file dựa trên thông tin chuyến đi
    origin = state.get('origin', 'origin').replace(' ', '_').replace('/', '_')
    destination = state.get('destination', 'destination').replace(' ', '_').replace('/', '_')
    start_date = state.get('start_date', '').replace('-', '')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    base_filename = f"{origin}_to_{destination}_{start_date}_{timestamp}"
    
    # 1. Export itinerary JSON (LICHTRINH, DIADIEM, LICHTRINH_DIADIEM, PHUONGTIEN_GIAOTHONG, HOATDONG)
    itinerary_json = format_state_to_json(state)
    itinerary_file = output_dir / f"{base_filename}_itinerary.json"
    with open(itinerary_file, 'w', encoding='utf-8') as f:
        json.dump(itinerary_json, f, ensure_ascii=False, indent=2)
    print(f"✅ Đã export itinerary JSON: {itinerary_file}")
    
    # 2. Export full state (tất cả thông tin)
    state_file = output_dir / f"{base_filename}_full_state.json"
    # Convert state to JSON-serializable format
    state_serializable = {}
    for key, value in state.items():
        try:
            json.dumps(value)  # Test if serializable
            state_serializable[key] = value
        except (TypeError, ValueError):
            # Skip non-serializable values
            state_serializable[key] = str(value)
    
    with open(state_file, 'w', encoding='utf-8') as f:
        json.dump(state_serializable, f, ensure_ascii=False, indent=2)
    print(f"✅ Đã export full state JSON: {state_file}")
    
    # 3. Export summary (tóm tắt thông tin chính)
    summary = {
        'origin': state.get('origin'),
        'destination': state.get('destination'),
        'start_date': state.get('start_date'),
        'days': state.get('days'),
        'travelers': state.get('travelers'),
        'travel_style': state.get('travel_style'),
        'rooms': state.get('rooms'),
        'costs': {
            'transport': state.get('transport_cost', 0),
            'accommodation': state.get('accommodation_cost', 0),
            'activities': state.get('activities_cost', 0),
            'dining': state.get('dining_cost', 0),
            'total': state.get('budget', {}).get('total_vnd', 0)
        },
        'transport': state.get('transport', {}),
        'flight': state.get('flight'),
        'hotels_count': len(state.get('hotels', [])),
        'activities_count': len(state.get('activities', [])),
        'restaurants_count': len(state.get('restaurants', []))
    }
    
    summary_file = output_dir / f"{base_filename}_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"✅ Đã export summary JSON: {summary_file}")
    
    # 4. Export itinerary description (nếu có)
    if state.get('itinerary_description'):
        description_file = output_dir / f"{base_filename}_description.txt"
        with open(description_file, 'w', encoding='utf-8') as f:
            f.write(state.get('itinerary_description', ''))
        print(f"✅ Đã export description: {description_file}")
    
    # In thống kê
    print()
    print("📊 Thống kê:")
    print(f"   - LICHTRINH: {len(itinerary_json.get('LICHTRINH', []))} bản ghi")
    print(f"   - DIADIEM: {len(itinerary_json.get('DIADIEM', []))} địa điểm")
    print(f"   - LICHTRINH_DIADIEM: {len(itinerary_json.get('LICHTRINH_DIADIEM', []))} liên kết")
    print(f"   - PHUONGTIEN_GIAOTHONG: {len(itinerary_json.get('PHUONGTIEN_GIAOTHONG', []))} phương tiện")
    print(f"   - HOATDONG: {len(itinerary_json.get('HOATDONG', []))} hoạt động")
    print(f"   - Khách sạn: {len(state.get('hotels', []))}")
    print(f"   - Nhà hàng: {len(state.get('restaurants', []))}")
    print(f"   - Tổng chi phí: {state.get('budget', {}).get('total_vnd', 0):,} VNĐ")
    
    return {
        'itinerary_file': itinerary_file,
        'state_file': state_file,
        'summary_file': summary_file,
        'description_file': output_dir / f"{base_filename}_description.txt" if state.get('itinerary_description') else None
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
        # Tạo travel plan
        state = await create_travel_plan(
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
        
        # Export thành các file JSON
        print()
        print("📁 Đang export thành các file JSON...")
        files = export_to_json_files(state)
        
        print()
        print("=" * 60)
        print("✅ HOÀN TẤT!")
        print("=" * 60)
        print(f"📂 Thư mục: {files['itinerary_file'].parent}")
        print(f"📄 Files đã tạo:")
        for key, file_path in files.items():
            if file_path:
                print(f"   - {key}: {file_path.name}")
        
    except Exception as e:
        print(f"❌ Lỗi: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(main())

