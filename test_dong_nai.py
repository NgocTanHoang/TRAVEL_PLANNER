"""
Test RAG system với Đồng Nai - tỉnh không có dữ liệu hotel/restaurant chi tiết
"""

import sys
from pathlib import Path

# Add project to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from agents.rag_agent import get_rag_agent
from agents.vector_db_agent import get_vector_db_agent

def test_dong_nai():
    """Test recommendations for Đồng Nai"""
    print("="*80)
    print("🧪 TEST: Đồng Nai - Tỉnh KHÔNG có dữ liệu hotels/restaurants chi tiết")
    print("="*80)
    print()
    
    # Test parameters
    destination = "Đồng Nai"
    budget = 5000000  # 5 triệu VND
    days = 2
    travelers = 2
    interests = "thiên nhiên, văn hóa"
    
    print(f"📍 Điểm đến: {destination}")
    print(f"💰 Ngân sách: {budget:,} VND")
    print(f"📅 Số ngày: {days}")
    print(f"👥 Số người: {travelers}")
    print(f"🎯 Sở thích: {interests}")
    print()
    print("="*80)
    print("BƯỚC 1: Kiểm tra Vector DB")
    print("="*80)
    
    # Test Vector DB
    vdb = get_vector_db_agent()
    
    # Check general places
    print("\n🔍 Tìm kiếm địa điểm tổng quát...")
    places = vdb.semantic_search(
        query=f"Địa điểm du lịch ở {destination}",
        n_results=5,
        city_filter=destination
    )
    print(f"✅ Tìm thấy {len(places)} địa điểm từ Vector DB:")
    for i, place in enumerate(places[:5], 1):
        print(f"   {i}. {place.get('name', 'N/A')} - {place.get('category', 'N/A')}")
    
    # Check hotels
    print("\n🏨 Tìm kiếm khách sạn...")
    hotels = vdb.semantic_search(
        query=f"Khách sạn hotel ở {destination}",
        n_results=5,
        city_filter=destination
    )
    print(f"{'✅' if hotels else '❌'} Tìm thấy {len(hotels)} khách sạn từ Vector DB")
    for i, hotel in enumerate(hotels[:3], 1):
        print(f"   {i}. {hotel.get('name', 'N/A')} - {hotel.get('price', 0):,} VND")
    
    # Check restaurants
    print("\n🍜 Tìm kiếm nhà hàng...")
    restaurants = vdb.semantic_search(
        query=f"Nhà hàng restaurant ở {destination}",
        n_results=5,
        city_filter=destination
    )
    print(f"{'✅' if restaurants else '❌'} Tìm thấy {len(restaurants)} nhà hàng từ Vector DB")
    for i, rest in enumerate(restaurants[:3], 1):
        print(f"   {i}. {rest.get('name', 'N/A')} - {rest.get('price', 0):,} VND")
    
    print()
    print("="*80)
    print("BƯỚC 2: Test RAG Agent (Vector DB + Tavily + OpenAI)")
    print("="*80)
    print()
    print("⏳ Đang xử lý... (khoảng 10-20 giây)")
    print()
    
    try:
        rag_agent = get_rag_agent()
        results = rag_agent.get_recommendations(
            destination=destination,
            budget=budget,
            days=days,
            travelers=travelers,
            interests=interests
        )
        
        print("✅ RAG Agent đã hoàn thành!")
        print()
        print("="*80)
        print("KẾT QUẢ")
        print("="*80)
        
        # Hotels
        hotels = results['recommendations'].get('hotels', [])
        print(f"\n🏨 KHÁCH SẠN ({len(hotels)} gợi ý):")
        if hotels:
            for i, hotel in enumerate(hotels[:5], 1):
                print(f"   {i}. {hotel.get('name', 'N/A')}")
                print(f"      📍 {hotel.get('address', hotel.get('city', 'N/A'))}")
                print(f"      ⭐ {hotel.get('rating', 'N/A')}/5.0")
                print(f"      💰 {hotel.get('price', 0):,} VND/đêm")
                print()
        else:
            print("   ❌ Không có gợi ý khách sạn")
        
        # Restaurants
        restaurants = results['recommendations'].get('restaurants', [])
        print(f"🍜 NHÀ HÀNG ({len(restaurants)} gợi ý):")
        if restaurants:
            for i, rest in enumerate(restaurants[:5], 1):
                print(f"   {i}. {rest.get('name', 'N/A')}")
                print(f"      📍 {rest.get('address', rest.get('city', 'N/A'))}")
                print(f"      ⭐ {rest.get('rating', 'N/A')}/5.0")
                print(f"      💰 {rest.get('price', 0):,} VND/người")
                print()
        else:
            print("   ❌ Không có gợi ý nhà hàng")
        
        # Attractions
        attractions = results['recommendations'].get('attractions', [])
        print(f"🏛️ ĐIỂM THAM QUAN ({len(attractions)} gợi ý):")
        if attractions:
            for i, attr in enumerate(attractions[:5], 1):
                print(f"   {i}. {attr.get('name', 'N/A')}")
                print(f"      📍 {attr.get('address', attr.get('city', 'N/A'))}")
                print(f"      ⭐ {attr.get('rating', 'N/A')}/5.0")
                print()
        else:
            print("   ❌ Không có gợi ý điểm tham quan")
        
        # AI Insights
        if results.get('ai_insights'):
            print("\n💡 AI INSIGHTS:")
            print(results['ai_insights'][:500] + "..." if len(results['ai_insights']) > 500 else results['ai_insights'])
        
        # Web Insights
        web_insights = results.get('web_insights', [])
        if web_insights:
            print(f"\n🌐 WEB SEARCH INSIGHTS ({len(web_insights)} kết quả từ Tavily):")
            for i, insight in enumerate(web_insights[:3], 1):
                print(f"   {i}. {insight.get('title', 'N/A')}")
                print(f"      🔗 {insight.get('url', 'N/A')}")
                print(f"      📝 {insight.get('content', 'N/A')[:150]}...")
                print()
        
        print("="*80)
        print("📊 ĐÁNH GIÁ KẾT QUẢ")
        print("="*80)
        
        total_recommendations = len(hotels) + len(restaurants) + len(attractions)
        
        if total_recommendations >= 10:
            print("✅ XUẤT SẮC: Đủ dữ liệu để tạo kế hoạch chi tiết")
            print(f"   📍 {len(hotels)} khách sạn, {len(restaurants)} nhà hàng, {len(attractions)} điểm tham quan")
        elif total_recommendations >= 5:
            print("⚠️ TẠM ỔN: Có một số gợi ý, nhưng hạn chế")
            print(f"   📍 {len(hotels)} khách sạn, {len(restaurants)} nhà hàng, {len(attractions)} điểm tham quan")
            print("   💡 NÊN bổ sung dữ liệu cho tỉnh này")
        else:
            print("❌ THIẾU: Không đủ dữ liệu để tạo kế hoạch tốt")
            print(f"   📍 {len(hotels)} khách sạn, {len(restaurants)} nhà hàng, {len(attractions)} điểm tham quan")
            print("   💡 CẦN bổ sung dữ liệu cho tỉnh này")
        
        print()
        print("="*80)
        
    except Exception as e:
        print(f"❌ LỖI: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_dong_nai()

