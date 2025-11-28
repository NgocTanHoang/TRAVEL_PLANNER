"""
Script để tìm các tỉnh không có dữ liệu địa điểm trong database
"""
import os
import sys
import django
from collections import defaultdict

# Setup Django
script_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.dirname(script_dir)
sys.path.insert(0, backend_dir)
os.chdir(backend_dir)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vivu_core.settings')
django.setup()

from apps.places.models import TinhThanh, DiaDiem


def find_provinces_without_places():
    """Tìm các tỉnh không có hoặc có ít địa điểm"""
    
    print("=" * 80)
    print("KIỂM TRA DỮ LIỆU ĐỊA ĐIỂM THEO TỈNH THÀNH")
    print("=" * 80)
    
    # Lấy tất cả tỉnh thành
    all_provinces = TinhThanh.objects.all().order_by('tenTinhThanh')
    
    # Thống kê số lượng địa điểm theo tỉnh
    province_stats = []
    
    for province in all_provinces:
        # Đếm tổng số địa điểm
        total_places = DiaDiem.objects.filter(maTinhThanh=province).count()
        
        # Đếm địa điểm active
        active_places = DiaDiem.objects.filter(
            maTinhThanh=province,
            trangThai='active'
        ).count()
        
        # Đếm theo loại địa điểm
        dia_danh = DiaDiem.objects.filter(
            maTinhThanh=province,
            trangThai='active',
            loaiDiaDiem='dia_danh'
        ).count()
        
        giai_tri = DiaDiem.objects.filter(
            maTinhThanh=province,
            trangThai='active',
            loaiDiaDiem='giai_tri'
        ).count()
        
        nha_hang = DiaDiem.objects.filter(
            maTinhThanh=province,
            trangThai='active',
            loaiDiaDiem='nha_hang'
        ).count()
        
        khach_san = DiaDiem.objects.filter(
            maTinhThanh=province,
            trangThai='active',
            loaiDiaDiem__in=['khach_san', 'co_so_luu_tru']
        ).count()
        
        # Địa điểm tham quan (quan trọng cho travel planning)
        tourist_places = dia_danh + giai_tri
        
        province_stats.append({
            'province': province,
            'total': total_places,
            'active': active_places,
            'dia_danh': dia_danh,
            'giai_tri': giai_tri,
            'tourist_places': tourist_places,  # Địa điểm tham quan
            'nha_hang': nha_hang,
            'khach_san': khach_san
        })
    
    # Sắp xếp theo số lượng active places
    province_stats.sort(key=lambda x: x['active'])
    
    # Phân loại theo tổng số địa điểm
    no_places = [p for p in province_stats if p['active'] == 0]
    few_places = [p for p in province_stats if 1 <= p['active'] < 5]
    some_places = [p for p in province_stats if 5 <= p['active'] < 20]
    many_places = [p for p in province_stats if p['active'] >= 20]
    
    # Phân loại theo địa điểm tham quan (quan trọng hơn)
    no_tourist_places = [p for p in province_stats if p['tourist_places'] == 0]
    few_tourist_places = [p for p in province_stats if 1 <= p['tourist_places'] < 5]
    some_tourist_places = [p for p in province_stats if 5 <= p['tourist_places'] < 20]
    many_tourist_places = [p for p in province_stats if p['tourist_places'] >= 20]
    
    print(f"\n📊 TỔNG QUAN:")
    print(f"  Tổng số tỉnh thành: {len(province_stats)}")
    print(f"  Tỉnh không có địa điểm: {len(no_places)}")
    print(f"  Tỉnh có ít địa điểm (1-4): {len(few_places)}")
    print(f"  Tỉnh có một số địa điểm (5-19): {len(some_places)}")
    print(f"  Tỉnh có nhiều địa điểm (≥20): {len(many_places)}")
    
    print(f"\n🎯 TỔNG QUAN ĐỊA ĐIỂM THAM QUAN (Địa danh + Giải trí):")
    print(f"  Tỉnh không có địa điểm tham quan: {len(no_tourist_places)}")
    print(f"  Tỉnh có ít địa điểm tham quan (1-4): {len(few_tourist_places)}")
    print(f"  Tỉnh có một số địa điểm tham quan (5-19): {len(some_tourist_places)}")
    print(f"  Tỉnh có nhiều địa điểm tham quan (≥20): {len(many_tourist_places)}")
    
    # Chi tiết các tỉnh không có địa điểm
    if no_places:
        print(f"\n❌ CÁC TỈNH KHÔNG CÓ ĐỊA ĐIỂM ({len(no_places)} tỉnh):")
        print("-" * 80)
        for stat in no_places:
            print(f"  • {stat['province'].tenTinhThanh} (ID: {stat['province'].maTinhThanh})")
            print(f"    - Tổng: {stat['total']}, Active: {stat['active']}")
    
    # Chi tiết các tỉnh có ít địa điểm
    if few_places:
        print(f"\n⚠️  CÁC TỈNH CÓ ÍT ĐỊA ĐIỂM (1-4 địa điểm) ({len(few_places)} tỉnh):")
        print("-" * 80)
        for stat in few_places:
            print(f"  • {stat['province'].tenTinhThanh} (ID: {stat['province'].maTinhThanh})")
            print(f"    - Active: {stat['active']} (Địa danh: {stat['dia_danh']}, Giải trí: {stat['giai_tri']}, "
                  f"Nhà hàng: {stat['nha_hang']}, Khách sạn: {stat['khach_san']})")
    
    # Chi tiết các tỉnh không có địa điểm tham quan
    if no_tourist_places:
        print(f"\n❌ CÁC TỈNH KHÔNG CÓ ĐỊA ĐIỂM THAM QUAN ({len(no_tourist_places)} tỉnh):")
        print("-" * 80)
        for stat in no_tourist_places:
            print(f"  • {stat['province'].tenTinhThanh} (ID: {stat['province'].maTinhThanh})")
            print(f"    - Địa điểm tham quan: 0 (Địa danh: {stat['dia_danh']}, Giải trí: {stat['giai_tri']})")
            print(f"    - Tổng địa điểm: {stat['active']} (Nhà hàng: {stat['nha_hang']}, Khách sạn: {stat['khach_san']})")
    
    # Chi tiết các tỉnh có ít địa điểm tham quan
    if few_tourist_places:
        print(f"\n⚠️  CÁC TỈNH CÓ ÍT ĐỊA ĐIỂM THAM QUAN (1-4 địa điểm) ({len(few_tourist_places)} tỉnh):")
        print("-" * 80)
        for stat in few_tourist_places:
            print(f"  • {stat['province'].tenTinhThanh} (ID: {stat['province'].maTinhThanh})")
            print(f"    - Địa điểm tham quan: {stat['tourist_places']} (Địa danh: {stat['dia_danh']}, Giải trí: {stat['giai_tri']})")
            print(f"    - Tổng địa điểm: {stat['active']} (Nhà hàng: {stat['nha_hang']}, Khách sạn: {stat['khach_san']})")
    
    # Chi tiết các tỉnh có một số địa điểm
    if some_places:
        print(f"\n📌 CÁC TỈNH CÓ MỘT SỐ ĐỊA ĐIỂM (5-19 địa điểm) ({len(some_places)} tỉnh):")
        print("-" * 80)
        for stat in some_places:
            print(f"  • {stat['province'].tenTinhThanh} (ID: {stat['province'].maTinhThanh})")
            print(f"    - Active: {stat['active']} (Địa danh: {stat['dia_danh']}, Giải trí: {stat['giai_tri']}, "
                  f"Nhà hàng: {stat['nha_hang']}, Khách sạn: {stat['khach_san']})")
    
    # Top 10 tỉnh có nhiều địa điểm nhất
    if many_places:
        print(f"\n✅ TOP 10 TỈNH CÓ NHIỀU ĐỊA ĐIỂM NHẤT:")
        print("-" * 80)
        top_10 = sorted(many_places, key=lambda x: x['active'], reverse=True)[:10]
        for i, stat in enumerate(top_10, 1):
            print(f"  {i:2d}. {stat['province'].tenTinhThanh}: {stat['active']} địa điểm "
                  f"(Địa danh: {stat['dia_danh']}, Giải trí: {stat['giai_tri']}, "
                  f"Nhà hàng: {stat['nha_hang']}, Khách sạn: {stat['khach_san']})")
    
    # Export danh sách tỉnh không có địa điểm tham quan
    if no_tourist_places:
        output_file = 'provinces_without_tourist_places.txt'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("DANH SÁCH CÁC TỈNH KHÔNG CÓ ĐỊA ĐIỂM THAM QUAN\n")
            f.write("=" * 80 + "\n\n")
            for stat in no_tourist_places:
                f.write(f"{stat['province'].tenTinhThanh} (ID: {stat['province'].maTinhThanh})\n")
                f.write(f"  - Địa điểm tham quan: 0 (Địa danh: {stat['dia_danh']}, Giải trí: {stat['giai_tri']})\n")
                f.write(f"  - Tổng địa điểm: {stat['active']} (Nhà hàng: {stat['nha_hang']}, Khách sạn: {stat['khach_san']})\n\n")
        print(f"\n💾 Đã lưu danh sách vào file: {output_file}")
    
    # Export danh sách tỉnh có ít địa điểm tham quan
    if few_tourist_places:
        output_file = 'provinces_with_few_tourist_places.txt'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("DANH SÁCH CÁC TỈNH CÓ ÍT ĐỊA ĐIỂM THAM QUAN (1-4 địa điểm)\n")
            f.write("=" * 80 + "\n\n")
            for stat in few_tourist_places:
                f.write(f"{stat['province'].tenTinhThanh} (ID: {stat['province'].maTinhThanh})\n")
                f.write(f"  - Địa điểm tham quan: {stat['tourist_places']} (Địa danh: {stat['dia_danh']}, Giải trí: {stat['giai_tri']})\n")
                f.write(f"  - Tổng địa điểm: {stat['active']} (Nhà hàng: {stat['nha_hang']}, Khách sạn: {stat['khach_san']})\n\n")
        print(f"💾 Đã lưu danh sách vào file: {output_file}")
    
    # Export danh sách tỉnh không có địa điểm ra file
    if no_places:
        output_file = 'provinces_without_places.txt'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("DANH SÁCH CÁC TỈNH KHÔNG CÓ ĐỊA ĐIỂM\n")
            f.write("=" * 80 + "\n\n")
            for stat in no_places:
                f.write(f"{stat['province'].tenTinhThanh} (ID: {stat['province'].maTinhThanh})\n")
        print(f"💾 Đã lưu danh sách vào file: {output_file}")
    
    # Export danh sách tỉnh có ít địa điểm
    if few_places:
        output_file = 'provinces_with_few_places.txt'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("DANH SÁCH CÁC TỈNH CÓ ÍT ĐỊA ĐIỂM (1-4 địa điểm)\n")
            f.write("=" * 80 + "\n\n")
            for stat in few_places:
                f.write(f"{stat['province'].tenTinhThanh} (ID: {stat['province'].maTinhThanh}) - "
                       f"{stat['active']} địa điểm\n")
        print(f"💾 Đã lưu danh sách vào file: {output_file}")
    
    return {
        'no_places': no_places,
        'few_places': few_places,
        'some_places': some_places,
        'many_places': many_places
    }


if __name__ == '__main__':
    find_provinces_without_places()

