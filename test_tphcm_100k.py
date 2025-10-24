"""
Test case: Du lịch TP.HCM với 100,000 VND, 1 người, 1 ngày
Ưu tiên: Di tích lịch sử, du lịch bình dân
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.append(str(project_root))

from multi_agent_system.langgraph_workflow import run_travel_workflow
from agents.rag_agent import get_rag_agent
from utils.transport_calculator import calculate_transport_cost, validate_budget
from utils.html_formatter import format_travel_plan_html

def test_tphcm_100k():
    """Test với budget 100,000 VND"""
    
    print("="*80)
    print("🧪 TEST: Du lịch TP.HCM với 100,000 VND")
    print("="*80)
    
    # Parameters
    diem_di = "TP.HCM"
    diem_den = "TP.HCM"  # Du lịch tại chỗ
    budget = 100000
    days = 1
    travelers = 1
    interests = "di tích lịch sử, văn hóa, bình dân"
    
    print(f"\n📍 Điểm xuất phát: {diem_di}")
    print(f"🎯 Điểm đến: {diem_den}")
    print(f"💰 Ngân sách: {budget:,} VND")
    print(f"📅 Số ngày: {days}")
    print(f"👥 Số người: {travelers}")
    print(f"🏛️ Sở thích: {interests}")
    
    # Calculate transport (trong thành phố)
    print("\n" + "="*80)
    print("🚗 TÍNH CHI PHÍ DI CHUYỂN")
    print("="*80)
    
    transport_info = calculate_transport_cost(diem_di, diem_den, travelers)
    transport_cost = transport_info['min_cost']
    
    print(f"Khoảng cách: {transport_info['distance']}km")
    print(f"Chi phí di chuyển: {transport_cost:,} VND (du lịch tại chỗ)")
    
    # Validate budget
    is_valid, validation_msg, budget_breakdown = validate_budget(
        budget, transport_cost, days, travelers
    )
    
    print("\n" + "="*80)
    print("💰 PHÂN BỔ NGÂN SÁCH")
    print("="*80)
    print(f"Tổng ngân sách: {budget:,} VND")
    print(f"Di chuyển (xe bus/grab): ~{budget_breakdown['transport']:,} VND")
    print(f"Còn lại cho hoạt động: {budget_breakdown['remaining']:,} VND")
    print(f"Budget/ngày: {budget_breakdown['per_day']:,} VND")
    
    if not is_valid:
        print("\n⚠️ CẢNH BÁO:")
        print(validation_msg)
    
    # Use RAG to get recommendations
    print("\n" + "="*80)
    print("🤖 GỢI Ý TỪ RAG SYSTEM")
    print("="*80)
    
    rag_agent = get_rag_agent()
    
    # Tìm di tích lịch sử FREE hoặc rẻ ở TP.HCM
    print("\n🏛️ Tìm kiếm di tích lịch sử, văn hóa ở TP.HCM...")
    
    rag_results = rag_agent.get_recommendations(
        destination=diem_den,
        budget=budget_breakdown['remaining'],
        days=days,
        travelers=travelers,
        interests=interests
    )
    
    # Display recommendations
    print("\n" + "="*80)
    print("📋 GỢI Ý LỊCH TRÌNH 100,000 VND")
    print("="*80)
    
    attractions = rag_results['recommendations'].get('attractions', [])
    restaurants = rag_results['recommendations'].get('restaurants', [])
    
    print("\n🏛️ DI TÍCH LỊCH SỬ & VĂN HÓA (MIỄN PHÍ/GIÁ RẺ):")
    if attractions:
        for i, attr in enumerate(attractions[:5], 1):
            print(f"\n{i}. {attr.get('name', 'N/A')}")
            print(f"   📍 {attr.get('address', attr.get('city', 'N/A'))}")
            print(f"   ⭐ {attr.get('rating', 'N/A')}/5.0")
            print(f"   💰 FREE hoặc vé rẻ")
    else:
        print("   ❌ Không tìm thấy")
    
    print("\n🍜 ĂN UỐNG BÌNH DÂN:")
    if restaurants:
        for i, rest in enumerate(restaurants[:3], 1):
            print(f"\n{i}. {rest.get('name', 'N/A')}")
            print(f"   📍 {rest.get('address', rest.get('city', 'N/A'))}")
            print(f"   ⭐ {rest.get('rating', 'N/A')}/5.0")
            print(f"   💰 ~20,000-30,000 VND/bữa")
    else:
        print("   ❌ Không tìm thấy")
    
    # Gợi ý lịch trình cụ thể
    print("\n" + "="*80)
    print("📅 LỊCH TRÌNH ĐỀ XUẤT 1 NGÀY (100,000 VND)")
    print("="*80)
    
    print("""
🌅 BUỔI SÁNG (7:00 - 11:00):
   - Di chuyển bằng xe bus: 7,000 VND
   - Thăm Dinh Độc Lập: FREE
   - Thăm Nhà thờ Đức Bà: FREE
   - Bưu điện Trung tâm: FREE
   
☀️ BUỔI TRƯA (11:00 - 13:00):
   - Ăn trưa tại quán cơm bình dân: 30,000 VND
   
🌆 BUỔI CHIỀU (13:00 - 17:00):
   - Thăm Bảo tàng Thành phố: 15,000 VND vé vào
   - Dạo phố đi bộ Nguyễn Huệ: FREE
   - Chợ Bến Thành: FREE (chỉ dạo, không mua)
   - Di chuyển xe bus: 7,000 VND
   
🌙 BUỔI TỐI (17:00 - 20:00):
   - Ăn tối tại quán phở: 35,000 VND
   - Về nhà bằng xe bus: 7,000 VND
   
💰 TỔNG CHI PHÍ:
   - Di chuyển (xe bus): 21,000 VND
   - Ăn uống: 65,000 VND
   - Vé vào cửa: 15,000 VND
   - Tổng: 101,000 VND ≈ 100,000 VND ✅
    """)
    
    # Web insights
    web_insights = rag_results.get('web_insights', [])
    if web_insights:
        print("\n" + "="*80)
        print("🌐 THÔNG TIN BỔ SUNG TỪ WEB")
        print("="*80)
        for i, insight in enumerate(web_insights[:3], 1):
            print(f"\n{i}. {insight.get('title', 'N/A')}")
            print(f"   🔗 {insight.get('url', 'N/A')}")
    
    print("\n" + "="*80)
    print("✅ KẾT LUẬN")
    print("="*80)
    print("""
Với 100,000 VND, bạn CÓ THỂ du lịch TP.HCM 1 ngày nếu:

✅ Ưu tiên các địa điểm MIỄN PHÍ:
   - Dinh Độc Lập, Nhà thờ Đức Bà, Bưu điện
   - Phố đi bộ Nguyễn Huệ
   - Công viên Tao Đàn, Công viên 30/4

✅ Di chuyển bằng xe bus (7,000 VND/lượt)

✅ Ăn uống tại quán bình dân (20,000-35,000 VND/bữa)

✅ Tham quan 1-2 bảo tàng (10,000-15,000 VND vé)

⚠️ KHÔNG ĐỦ cho:
   - Khách sạn/nhà nghỉ
   - Nhà hàng cao cấp
   - Di chuyển taxi/grab
   - Mua sắm
    """)
    
    print("\n" + "="*80)

if __name__ == "__main__":
    test_tphcm_100k()

