"""
Script để kiểm tra tính khoảng cách giữa 20 cặp địa điểm ngẫu nhiên
"""
import os
import sys
import django
import random
from pathlib import Path

# Fix encoding for Windows console
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

# Setup Django
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vivu_core.settings')
django.setup()

from apps.places.models import DiaDiem
from tools.geo_tools import get_geo_tools

print("=" * 100)
print("KIỂM TRA TÍNH KHOẢNG CÁCH GIỮA 20 CẶP ĐỊA ĐIỂM NGẪU NHIÊN")
print("=" * 100)

# Lấy tất cả địa điểm có tọa độ
places = DiaDiem.objects.filter(
    viDo__isnull=False,
    kinhDo__isnull=False,
    trangThai='active'
).exclude(viDo=0).exclude(kinhDo=0)

print(f"\n📊 Tổng số địa điểm có tọa độ: {places.count()}")

if places.count() < 2:
    print("❌ Không đủ địa điểm để test!")
    sys.exit(1)

# Chọn 20 cặp ngẫu nhiên
selected_pairs = []
place_list = list(places)
max_pairs = min(20, len(place_list) * (len(place_list) - 1) // 2)

for _ in range(max_pairs):
    pair = random.sample(place_list, 2)
    # Tránh trùng lặp
    pair_tuple = tuple(sorted([p.maDiaDiem for p in pair]))
    if pair_tuple not in selected_pairs:
        selected_pairs.append((pair[0], pair[1]))

print(f"✅ Đã chọn {len(selected_pairs)} cặp địa điểm ngẫu nhiên\n")

# Khởi tạo geo_tools
geo_tools = get_geo_tools()

results = []

for idx, (place1, place2) in enumerate(selected_pairs, 1):
    origin = f"{place1.tenDiaDiem}, {place1.maTinhThanh.tenTinhThanh if place1.maTinhThanh else 'N/A'}"
    destination = f"{place2.tenDiaDiem}, {place2.maTinhThanh.tenTinhThanh if place2.maTinhThanh else 'N/A'}"
    
    print(f"[{idx}/{len(selected_pairs)}] Đang tính: {origin} → {destination}")
    
    try:
        route_info = geo_tools.calculate_distance_time(
            origin=origin,
            destination=destination
        )
        
        if route_info:
            distance_km = route_info.get('distance_km', 0)
            duration_hours = route_info.get('duration_hours', 0)
            duration_minutes = route_info.get('duration_minutes', 0)
            method = route_info.get('method', 'unknown')
            
            # Tính khoảng cách đường thẳng (Haversine) để so sánh
            from tools.geo_tools import haversine_distance
            straight_distance = haversine_distance(
                place1.viDo, place1.kinhDo,
                place2.viDo, place2.kinhDo
            )
            
            # Tính tỷ lệ (road distance / straight distance)
            ratio = distance_km / straight_distance if straight_distance > 0 else 0
            
            results.append({
                'origin': origin,
                'destination': destination,
                'distance_km': distance_km,
                'straight_distance_km': straight_distance,
                'ratio': ratio,
                'duration_hours': duration_hours,
                'duration_minutes': duration_minutes,
                'method': method,
                'status': 'success'
            })
            
            print(f"  ✅ Khoảng cách: {distance_km:.1f} km | Thời gian: {int(duration_hours)}h {int(duration_minutes)}m | Method: {method}")
            print(f"     (Đường thẳng: {straight_distance:.1f} km, Tỷ lệ: {ratio:.2f}x)")
        else:
            results.append({
                'origin': origin,
                'destination': destination,
                'status': 'failed',
                'error': 'No route info returned'
            })
            print(f"  ❌ Không tính được khoảng cách")
    except Exception as e:
        results.append({
            'origin': origin,
            'destination': destination,
            'status': 'error',
            'error': str(e)
        })
        print(f"  ❌ Lỗi: {e}")
    
    print()

# Tổng hợp kết quả
print("=" * 100)
print("TỔNG HỢP KẾT QUẢ")
print("=" * 100)

successful = [r for r in results if r.get('status') == 'success']
failed = [r for r in results if r.get('status') != 'success']

print(f"\n✅ Thành công: {len(successful)}/{len(results)}")
print(f"❌ Thất bại: {len(failed)}/{len(results)}")

if successful:
    distances = [r['distance_km'] for r in successful]
    ratios = [r['ratio'] for r in successful]
    
    print(f"\n📊 Thống kê khoảng cách:")
    print(f"  - Nhỏ nhất: {min(distances):.1f} km")
    print(f"  - Lớn nhất: {max(distances):.1f} km")
    print(f"  - Trung bình: {sum(distances)/len(distances):.1f} km")
    
    print(f"\n📊 Thống kê tỷ lệ (đường bộ / đường thẳng):")
    print(f"  - Nhỏ nhất: {min(ratios):.2f}x")
    print(f"  - Lớn nhất: {max(ratios):.2f}x")
    print(f"  - Trung bình: {sum(ratios)/len(ratios):.2f}x")
    
    # Phân tích các trường hợp bất thường
    print(f"\n⚠️ Các trường hợp cần chú ý:")
    unusual = [r for r in successful if r['ratio'] > 2.5 or r['ratio'] < 1.0]
    if unusual:
        for r in unusual[:5]:  # Hiển thị tối đa 5 trường hợp
            print(f"  - {r['origin']} → {r['destination']}")
            print(f"    Khoảng cách: {r['distance_km']:.1f} km, Tỷ lệ: {r['ratio']:.2f}x, Method: {r['method']}")
    else:
        print("  ✅ Không có trường hợp bất thường")

# Hiển thị chi tiết từng cặp
print("\n" + "=" * 100)
print("CHI TIẾT TỪNG CẶP")
print("=" * 100)
print(f"\n{'STT':<5} {'Điểm đi':<40} {'Điểm đến':<40} {'Khoảng cách':<15} {'Thời gian':<15} {'Method':<15}")
print("-" * 100)

for idx, r in enumerate(results, 1):
    if r.get('status') == 'success':
        origin_short = r['origin'][:38] + '..' if len(r['origin']) > 40 else r['origin']
        dest_short = r['destination'][:38] + '..' if len(r['destination']) > 40 else r['destination']
        distance_str = f"{r['distance_km']:.1f} km"
        time_str = f"{int(r['duration_hours'])}h {int(r['duration_minutes'])}m"
        print(f"{idx:<5} {origin_short:<40} {dest_short:<40} {distance_str:<15} {time_str:<15} {r['method']:<15}")
    else:
        origin_short = r['origin'][:38] + '..' if len(r['origin']) > 40 else r['origin']
        dest_short = r['destination'][:38] + '..' if len(r['destination']) > 40 else r['destination']
        print(f"{idx:<5} {origin_short:<40} {dest_short:<40} {'FAILED':<15} {'-':<15} {'-':<15}")

print("\n" + "=" * 100)
print("✅ Hoàn thành!")
print("=" * 100)
