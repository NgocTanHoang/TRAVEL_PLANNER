"""
Test xem UI có hiển thị đầy đủ thông tin chi tiết không
- Địa chỉ
- Xe buýt
- Giá cụ thể
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.append(str(project_root))

from agents.rag_agent import get_rag_agent
from utils.html_formatter import format_travel_plan_html
from utils.transport_calculator import calculate_transport_cost, validate_budget

def test_ui_output():
    """Test HTML output với đầy đủ thông tin"""
    
    print("="*80)
    print("🧪 TEST UI OUTPUT - THÔNG TIN CHI TIẾT")
    print("="*80)
    
    # Test case
    diem_den = "TP.HCM"
    diem_di = "TP.HCM"
    budget = 2000000
    days = 2
    travelers = 2
    so_thich = "biển, tháp Tam Thắng, hải sản"
    
    print(f"\n📋 Input:")
    print(f"   From: {diem_di}")
    print(f"   To: {diem_den}")
    print(f"   Budget: {budget:,} VND")
    print(f"   Days: {days}")
    print(f"   Travelers: {travelers}")
    print(f"   Interests: {so_thich}")
    
    # Get RAG recommendations
    rag_agent = get_rag_agent()
    
    # Calculate transport
    transport_info = calculate_transport_cost(diem_di, diem_den, travelers)
    
    # Validate budget
    is_valid, message, budget_breakdown = validate_budget(
        budget,
        transport_info['min_cost'],
        days,
        travelers
    )
    
    print(f"\n✅ Transport: {transport_info['recommended']}")
    print(f"✅ Budget Valid: {is_valid}")
    
    # Get RAG recommendations
    rag_results = rag_agent.get_recommendations(
        destination=diem_den,
        budget=budget_breakdown.get('remaining', budget),
        days=days,
        travelers=travelers,
        interests=so_thich
    )
    
    print(f"✅ Hotels: {len(rag_results['recommendations']['hotels'])}")
    print(f"✅ Restaurants: {len(rag_results['recommendations']['restaurants'])}")
    print(f"✅ Attractions: {len(rag_results['recommendations']['attractions'])}")
    
    # Build result dict
    result = {
        'recommendations': rag_results['recommendations'],
        'ai_insights': rag_results.get('ai_insights', ''),
        'web_insights': [],
        'transport_info': transport_info,
        'budget_breakdown': budget_breakdown,
        'departure_city': diem_di,
        'workflow_result': {}
    }
    
    # Format HTML
    print(f"\n🎨 Formatting HTML...")
    html_output = format_travel_plan_html(
        diem_den=diem_den,
        budget=budget,
        days=days,
        travelers=travelers,
        so_thich=so_thich,
        result=result
    )
    
    # Save to file
    output_file = project_root / "test_ui_output.html"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_output)
    
    print(f"✅ HTML saved to: {output_file}")
    print(f"\n📊 HTML Length: {len(html_output):,} characters")
    
    # Check if address is included
    has_address = "📍" in html_output
    has_bus = "🚌 THÔNG TIN XE BUÝT" in html_output
    has_price = "VND" in html_output
    
    print(f"\n✅ Kiểm tra nội dung:")
    print(f"   Địa chỉ (📍): {'✅' if has_address else '❌'}")
    print(f"   Xe buýt (🚌): {'✅' if has_bus else '❌'}")
    print(f"   Giá (VND): {'✅' if has_price else '❌'}")
    
    print(f"\n{'='*80}")
    print(f"✅ TEST HOÀN TẤT!")
    print(f"📂 Mở file HTML để xem kết quả: {output_file}")
    print(f"{'='*80}")

if __name__ == "__main__":
    test_ui_output()

