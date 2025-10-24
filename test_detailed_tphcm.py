"""
Test: Hiển thị thông tin CỤ THỂ cho TP.HCM
- Địa chỉ chi tiết
- Số xe buýt cụ thể
- Tên quán ăn thật
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.append(str(project_root))

from agents.rag_agent import get_rag_agent
from utils.geocoding_helper import get_geocoding_helper
from config.bus_routes import suggest_bus_route

def test_detailed_recommendations():
    """Test with detailed information"""
    
    print("="*80)
    print("🧪 TEST: GỢI Ý CHI TIẾT CHO TP.HCM")
    print("="*80)
    
    # Get RAG agent
    rag_agent = get_rag_agent()
    geocoding = get_geocoding_helper()
    
    # Test query
    print("\n📍 Tìm kiếm: Di tích lịch sử TP.HCM")
    print("="*80)
    
    results = rag_agent.get_recommendations(
        destination="TP.HCM",
        budget=1000000,
        days=1,
        travelers=1,
        interests="di tích lịch sử, văn hóa"
    )
    
    # Display với địa chỉ cụ thể
    print("\n" + "="*80)
    print("🏛️ DI TÍCH LỊCH SỬ (VỚI ĐỊA CHỈ CỤ THỂ)")
    print("="*80)
    
    attractions = results['recommendations'].get('attractions', [])
    
    for i, attraction in enumerate(attractions[:5], 1):
        name = attraction.get('name', 'N/A')
        lat = attraction.get('latitude')
        lon = attraction.get('longitude')
        rating = attraction.get('rating', 'N/A')
        
        print(f"\n{i}. **{name}**")
        print(f"   ⭐ Đánh giá: {rating}/5.0")
        
        # Get address from lat/lon
        if lat and lon:
            address = geocoding.get_address(lat, lon)
            if address:
                print(f"   📍 Địa chỉ: {address}")
            else:
                print(f"   📍 Tọa độ: {lat:.4f}, {lon:.4f}")
        
        print(f"   💰 Vé vào cửa: FREE hoặc 10,000-30,000 VND")
    
    # Display restaurants với địa chỉ
    print("\n" + "="*80)
    print("🍜 NHÀ HÀNG / QUÁN ĂN (VỚI ĐỊA CHỈ)")
    print("="*80)
    
    restaurants = results['recommendations'].get('restaurants', [])
    
    for i, rest in enumerate(restaurants[:5], 1):
        name = rest.get('name', 'N/A')
        lat = rest.get('latitude')
        lon = rest.get('longitude')
        rating = rest.get('rating', 'N/A')
        
        print(f"\n{i}. **{name}**")
        print(f"   ⭐ Đánh giá: {rating}/5.0")
        
        # Get address
        if lat and lon:
            address = geocoding.get_address(lat, lon)
            if address:
                print(f"   📍 Địa chỉ: {address}")
        
        print(f"   💰 Giá: ~30,000-50,000 VND/người")
    
    # Display bus routes
    print("\n" + "="*80)
    print("🚌 XE BUÝT ĐỀ XUẤT CHO DU LỊCH TP.HCM")
    print("="*80)
    
    bus_info = suggest_bus_route("TP.HCM")
    print(f"\n{bus_info}")
    
    # Sample itinerary với thông tin cụ thể
    print("\n" + "="*80)
    print("📅 LỊCH TRÌNH MẪU (VỚI THÔNG TIN CỤ THỂ)")
    print("="*80)
    
    print("""
🌅 BUỔI SÁNG (7:00 - 11:00):

7:00  🚌 Đi xe buýt số 01 hoặc 04 đến Chợ Bến Thành
      📍 Xuất phát từ khu vực của bạn → Chợ Bến Thành
      💰 7,000 VND

7:30  🏛️ Thăm Dinh Độc Lập
      📍 135 Nam Kỳ Khởi Nghĩa, Quận 1
      💰 40,000 VND vé vào cửa
      ⏰ 2 giờ tham quan

9:30  ⛪ Nhà thờ Đức Bà Sài Gòn
      📍 01 Công xã Paris, Quận 1
      💰 FREE (chỉ ngắm bên ngoài, đang sửa chữa)
      ⏰ 30 phút

10:00 📮 Bưu điện Trung tâm Sài Gòn
      📍 02 Công xã Paris, Quận 1 (ngay cạnh Nhà thờ)
      💰 FREE
      ⏰ 30 phút

☀️ BUỔI TRƯA (11:00 - 13:00):

11:00 🍜 Quán Phở Hòa Pasteur
      📍 260C Pasteur, Quận 3
      💰 40,000-50,000 VND/bát phở
      🚌 Đi bộ hoặc xe buýt 10 phút

🌆 BUỔI CHIỀU (13:00 - 17:00):

13:00 🏛️ Bảo tàng Thành phố
      📍 65 Lý Tự Trọng, Quận 1
      💰 30,000 VND vé vào
      ⏰ 2 giờ

15:00 🚶 Phố đi bộ Nguyễn Huệ
      📍 Đường Nguyễn Huệ, Quận 1
      💰 FREE
      ⏰ 1 giờ

16:00 🏪 Chợ Bến Thành
      📍 Lê Lợi, Quận 1
      💰 FREE (dạo chợ)
      ⏰ 1 giờ

🌙 BUỔI TỐI (17:00 - 20:00):

17:30 ☕ Cafe Công Nguyễn Huệ
      📍 26 Lý Tự Trọng, Quận 1
      💰 30,000-50,000 VND/ly
      ⏰ 30 phút nghỉ chân

18:30 🍲 Quán Cơm Tấm Phúc Lộc Thọ
      📍 6A Phan Văn Trị, Gò Vấp
      💰 35,000-45,000 VND/suất
      🚌 Xe buýt số 01 về

💰 TỔNG CHI PHÍ 1 NGÀY:
   🚌 Xe buýt: 28,000 VND (4 lượt × 7,000)
   🏛️ Vé vào cửa: 70,000 VND
   🍜 Ăn uống: 120,000 VND
   ☕ Nước uống: 40,000 VND
   ────────────────────────────
   📊 TỔNG: 258,000 VND
   
✅ Phù hợp cho ngân sách 300,000-500,000 VND/ngày
""")
    
    print("="*80)
    print("✅ TEST HOÀN THÀNH!")
    print("="*80)

if __name__ == "__main__":
    test_detailed_recommendations()

