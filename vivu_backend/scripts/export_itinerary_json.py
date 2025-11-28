"""
Script để export lịch trình thành file JSON với format LICHTRINH, DIADIEM, LICHTRINH_DIADIEM
"""
import os
import sys
import django
import json
from pathlib import Path

# Setup Django
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vivu_core.settings')
django.setup()

from apps.itineraries.models import LichTrinh
from utils.itinerary_formatter import format_itinerary_to_json


def export_itinerary_json(ma_lich_trinh: int, output_file: str = None):
    """
    Export lịch trình thành file JSON
    
    Args:
        ma_lich_trinh: Mã lịch trình cần export
        output_file: Đường dẫn file output (nếu None, sẽ tự động tạo tên)
    """
    try:
        # Lấy lịch trình từ database
        lich_trinh = LichTrinh.objects.get(maLichTrinh=ma_lich_trinh)
        
        # Format thành JSON
        json_data = format_itinerary_to_json(lich_trinh, include_places=True)
        
        # Tạo tên file nếu chưa có
        if output_file is None:
            output_dir = BASE_DIR / 'exports'
            output_dir.mkdir(exist_ok=True)
            safe_title = "".join(c for c in lich_trinh.tieuDe if c.isalnum() or c in (' ', '-', '_')).strip()
            safe_title = safe_title.replace(' ', '_')[:50]
            output_file = output_dir / f"itinerary_{ma_lich_trinh}_{safe_title}.json"
        
        # Lưu vào file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ Đã export lịch trình {ma_lich_trinh} thành công!")
        print(f"📁 File: {output_file}")
        print(f"📊 Thống kê:")
        print(f"   - LICHTRINH: {len(json_data.get('LICHTRINH', []))} bản ghi")
        print(f"   - DIADIEM: {len(json_data.get('DIADIEM', []))} địa điểm")
        print(f"   - LICHTRINH_DIADIEM: {len(json_data.get('LICHTRINH_DIADIEM', []))} liên kết")
        
        return output_file
        
    except LichTrinh.DoesNotExist:
        print(f"❌ Không tìm thấy lịch trình với mã {ma_lich_trinh}")
        return None
    except Exception as e:
        print(f"❌ Lỗi khi export: {e}")
        import traceback
        traceback.print_exc()
        return None


def export_all_recent_itineraries(limit: int = 10, output_dir: str = None):
    """
    Export tất cả lịch trình gần đây
    
    Args:
        limit: Số lượng lịch trình cần export
        output_dir: Thư mục output (nếu None, dùng exports/)
    """
    if output_dir is None:
        output_dir = BASE_DIR / 'exports'
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(exist_ok=True)
    
    # Lấy các lịch trình gần đây
    lich_trinhs = LichTrinh.objects.all().order_by('-ngayTao')[:limit]
    
    print(f"📦 Đang export {len(lich_trinhs)} lịch trình gần đây...")
    
    exported = []
    for lich_trinh in lich_trinhs:
        output_file = export_itinerary_json(lich_trinh.maLichTrinh, None)
        if output_file:
            exported.append(output_file)
    
    print(f"\n✅ Đã export {len(exported)}/{len(lich_trinhs)} lịch trình thành công!")
    return exported


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Export lịch trình thành file JSON')
    parser.add_argument('--id', type=int, help='Mã lịch trình cần export')
    parser.add_argument('--all', action='store_true', help='Export tất cả lịch trình gần đây')
    parser.add_argument('--limit', type=int, default=10, help='Số lượng lịch trình khi dùng --all')
    parser.add_argument('--output', type=str, help='Đường dẫn file output')
    
    args = parser.parse_args()
    
    if args.all:
        export_all_recent_itineraries(limit=args.limit)
    elif args.id:
        export_itinerary_json(args.id, args.output)
    else:
        print("❌ Vui lòng chỉ định --id <ma_lich_trinh> hoặc --all")
        print("\nVí dụ:")
        print("  python export_itinerary_json.py --id 1")
        print("  python export_itinerary_json.py --all --limit 5")

