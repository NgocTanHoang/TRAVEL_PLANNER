"""
═══════════════════════════════════════════════════════════════════════════════
    HỆ THỐNG LẬP KẾ HOẠCH DU LỊCH THÔNG MINH
    Multi-Agent System for Travel Planning in Vietnam
═══════════════════════════════════════════════════════════════════════════════

Tác giả: Travel Planner MAS Team
Ngày: 2025
Phiên bản: 2.0

Hệ thống sử dụng:
- 10 AI Agents làm việc đồng bộ
- LangGraph + AutoGen + LangChain
- 50,000+ địa điểm thực tế tại Việt Nam
- ML-based recommendations
- Free APIs (540,000+ requests/month)

═══════════════════════════════════════════════════════════════════════════════
"""

import gradio as gr
import sys
from pathlib import Path

# Thêm project vào path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from multi_agent_system.langgraph_workflow import run_travel_workflow
from agents.chat_assistant_agent import TravelChatAssistant
from utils.html_formatter import format_travel_plan_html
from utils.transport_calculator import calculate_transport_cost, validate_budget

# Khởi tạo chat assistant
chat_assistant = TravelChatAssistant()


def tao_ke_hoach_du_lich(diem_di: str, diem_den: str, ngan_sach: str, so_ngay: str, so_nguoi: str, so_thich: str):
    """
    Tạo kế hoạch du lịch sử dụng hệ thống Multi-Agent
    
    Args:
        diem_di: Điểm xuất phát (VD: Hà Nội, TP.HCM)
        diem_den: Địa điểm du lịch (VD: Hà Nội, Đà Nẵng)
        ngan_sach: Ngân sách (VND)
        so_ngay: Số ngày du lịch
        so_nguoi: Số người đi
        so_thich: Sở thích (VD: văn hóa, ẩm thực, thiên nhiên)
    
    Returns:
        Kết quả phân tích và kế hoạch du lịch
    """
    try:
        # Validate input
        if not diem_den or not diem_den.strip():
            return "❌ **Lỗi**: Vui lòng nhập điểm đến!"
        
        if not diem_di or not diem_di.strip():
            diem_di = diem_den  # Nếu không nhập điểm đi, coi như du lịch tại chỗ
        
        # Chuyển đổi dữ liệu
        try:
            budget = int(ngan_sach.replace(",", "").replace(".", "").strip()) if ngan_sach else 10000000
        except:
            budget = 10000000
            
        try:
            days = int(so_ngay.strip()) if so_ngay else 3
        except:
            days = 3
            
        try:
            travelers = int(so_nguoi.strip()) if so_nguoi else 2
        except:
            travelers = 2
        
        # Tính chi phí di chuyển
        transport_info = calculate_transport_cost(diem_di, diem_den, travelers)
        transport_cost = transport_info['min_cost']  # Use cheapest option
        
        # Validate budget
        is_valid, validation_msg, budget_breakdown = validate_budget(
            budget, transport_cost, days, travelers
        )
        
        if not is_valid:
            # Budget không đủ
            return f"""
<div style="padding: 30px; background: linear-gradient(135deg, #fc8181, #f56565); border-radius: 15px; color: white; max-width: 800px; margin: 20px auto; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
    <h2 style="margin: 0 0 20px 0; font-size: 2em;">❌ NGÂN SÁCH KHÔNG ĐỦ</h2>
    
    <div style="background: rgba(255,255,255,0.2); padding: 20px; border-radius: 10px; margin-bottom: 20px;">
        <h3 style="margin: 0 0 15px 0;">📍 Thông tin chuyến đi:</h3>
        <div style="line-height: 1.8;">
            <p style="margin: 5px 0;">🚀 <strong>Từ:</strong> {diem_di}</p>
            <p style="margin: 5px 0;">🎯 <strong>Đến:</strong> {diem_den}</p>
            <p style="margin: 5px 0;">📅 <strong>Số ngày:</strong> {days} ngày</p>
            <p style="margin: 5px 0;">👥 <strong>Số người:</strong> {travelers} người</p>
            <p style="margin: 5px 0;">💰 <strong>Ngân sách hiện tại:</strong> {budget:,} VND</p>
        </div>
    </div>
    
    <div style="background: rgba(255,255,255,0.2); padding: 20px; border-radius: 10px; margin-bottom: 20px;">
        <h3 style="margin: 0 0 15px 0;">🚗 Chi phí di chuyển:</h3>
        <p style="margin: 5px 0; font-size: 1.2em;"><strong>{transport_info['distance']}km</strong> - Chi phí tối thiểu: <strong>{transport_cost:,} VND</strong></p>
        <p style="margin: 10px 0 5px 0;">Các phương tiện:</p>
        <ul style="margin: 5px 0; padding-left: 20px;">
            {''.join([f"<li>{opt['type']}: {opt['total_cost']:,} VND ({opt['duration']})</li>" for opt in transport_info['options'][:3]])}
        </ul>
    </div>
    
    <div style="background: rgba(255,255,255,0.3); padding: 20px; border-radius: 10px; border: 2px solid white;">
        <h3 style="margin: 0 0 10px 0; font-size: 1.3em;">💡 ĐỀ XUẤT:</h3>
        <div style="white-space: pre-line; line-height: 1.8;">
{validation_msg}
        </div>
    </div>
    
    <div style="margin-top: 20px; padding: 15px; background: rgba(0,0,0,0.2); border-radius: 10px; text-align: center;">
        <p style="margin: 0; font-size: 0.95em;">💡 <strong>Mẹo:</strong> Bạn có thể:</p>
        <p style="margin: 5px 0;">• Tăng ngân sách</p>
        <p style="margin: 5px 0;">• Chọn điểm xuất phát gần hơn</p>
        <p style="margin: 5px 0;">• Giảm số ngày hoặc số người</p>
    </div>
</div>
"""
        
        # Hiển thị thông tin processing
        output = f"""
{'='*80}
KẾ HOẠCH DU LỊCH {diem_den.upper()}
{'='*80}

📋 THÔNG TIN CHUYẾN ĐI
{'-'*80}
🚀 Điểm đi:     {diem_di}
📍 Điểm đến:    {diem_den}
💰 Ngân sách:   {budget:,} VND
📅 Số ngày:     {days} ngày
👥 Số người:    {travelers} người
🎯 Sở thích:    {so_thich if so_thich else 'Tất cả'}

{'='*80}
🚗 CHI PHÍ DI CHUYỂN
{'='*80}
Khoảng cách:    {transport_info['distance']}km
Phương tiện:    {transport_info['recommended']}
Chi phí:        {transport_cost:,} VND

{'='*80}
💰 PHÂN BỔ NGÂN SÁCH
{'='*80}
Di chuyển:      {budget_breakdown['transport']:,} VND
Còn lại:        {budget_breakdown['remaining']:,} VND ({budget_breakdown['per_day']:,} VND/ngày)

{'='*80}
🤖 HỆ THỐNG 10 AI AGENTS ĐANG XỬ LÝ
{'='*80}

Layer 1 - Data Collection:
  ✅ API Collector       - Thu thập dữ liệu từ APIs
  ✅ Web Scraper         - Tìm kiếm thông tin bổ sung

Layer 2 - Data Processing:
  ✅ Data Processor      - Xử lý và chuẩn hóa dữ liệu

Layer 3 - ML Analysis (Parallel):
  ✅ Recommendation      - Tạo gợi ý ML-based
  ✅ Sentiment Analyzer  - Phân tích đánh giá
  ✅ Similarity Engine   - Tìm địa điểm tương tự
  ✅ Price Predictor     - Dự đoán và tối ưu giá

Layer 4 - Planning:
  ✅ Planner            - Lập lịch trình chi tiết

Layer 5 - Research:
  ✅ Researcher         - Nghiên cứu thông tin địa phương

Layer 6 - Analytics:
  ✅ Analytics Engine   - Phân tích tổng hợp

{'='*80}
⏳ Đang xử lý... Vui lòng đợi 10-30 giây
{'='*80}
"""
        
        yield output
        
        # Sử dụng RAG Agent để lấy recommendations
        # Dùng REMAINING BUDGET sau khi trừ transport
        from agents.rag_agent import get_rag_agent
        
        rag_agent = get_rag_agent()
        rag_results = rag_agent.get_recommendations(
            destination=diem_den,
            budget=budget_breakdown['remaining'],  # Use remaining budget after transport
            days=days,
            travelers=travelers,
            interests=so_thich if so_thich else ""
        )
        
        # Chạy workflow
        result = run_travel_workflow(
            destination=diem_den,
            budget=budget,
            days=days,
            travelers=travelers,
            interests=so_thich if so_thich else ""
        )
        
        # Merge RAG results vào workflow result
        result['recommendations'] = rag_results['recommendations']
        result['all_options'] = rag_results.get('all_options', {})
        result['ai_insights'] = rag_results.get('ai_insights', '')
        result['web_insights'] = rag_results.get('web_insights', [])
        result['transport_info'] = transport_info
        result['budget_breakdown'] = budget_breakdown
        result['departure_city'] = diem_di
        
        if "error" in result:
            yield f"""
{'='*80}
❌ LỖI
{'='*80}

Đã xảy ra lỗi khi xử lý:

{result['error']}

Vui lòng thử lại hoặc kiểm tra thông tin đầu vào.
{'='*80}
"""
            return
        
        # Format kết quả bằng HTML đẹp
        html_output = format_travel_plan_html(
            diem_den=diem_den,
            budget=budget,
            days=days,
            travelers=travelers,
            so_thich=so_thich,
            result=result
        )
        
        yield html_output
        return
        
        # Cache statistics
        if "collected_data" in result and "cache_stats" in result["collected_data"]:
            cache_stats = result["collected_data"]["cache_stats"]
            output += f"""
{'='*80}
💾 THỐNG KÊ CACHE
{'='*80}
Tổng dữ liệu đã lưu:  {cache_stats.get('total_entries', 0)} mục
API đã dùng:          {', '.join(cache_stats.get('api_stats', {}).keys())}
Dữ liệu hết hạn:      {cache_stats.get('expired_entries', 0)} mục

"""
        
        # Workflow summary
        if "workflow_summary" in result:
            summary = result["workflow_summary"]
            output += f"""
{'='*80}
🔄 TÓM TẮT XỬ LÝ
{'='*80}
Bước hoàn thành:      {len(summary.get('steps_completed', []))} bước
Địa điểm phân tích:   {summary.get('total_places_analyzed', 0)} địa điểm
Gợi ý tạo ra:         {summary.get('recommendations_generated', 0)} gợi ý
Lỗi gặp phải:         {summary.get('errors_encountered', 0)} lỗi

"""
        
        # Analytics results
        if "analytics_results" in result:
            analytics = result["analytics_results"]
            output += f"""
{'='*80}
📊 PHÂN TÍCH CHI TIẾT
{'='*80}
Tổng chi phí ước tính: {analytics.get('total_cost_estimate', 0):,} VND
Điểm trung bình:       {analytics.get('average_rating', 0)}/5.0
Tỷ lệ thành công:      {analytics.get('success_rate', 0)}%
Địa điểm đề xuất:      {analytics.get('recommended_places', 0)} địa điểm

"""
            
            # Budget breakdown
            if "budget_breakdown" in analytics:
                breakdown = analytics["budget_breakdown"]
                output += f"""
💰 PHÂN BỔ NGÂN SÁCH
{'-'*80}
🏨 Khách sạn:    {breakdown.get('accommodation', 0):,} VND ({breakdown.get('accommodation', 0)/budget*100:.1f}%)
🍜 Ăn uống:      {breakdown.get('food', 0):,} VND ({breakdown.get('food', 0)/budget*100:.1f}%)
🚗 Di chuyển:    {breakdown.get('transportation', 0):,} VND ({breakdown.get('transportation', 0)/budget*100:.1f}%)
🎭 Hoạt động:    {breakdown.get('activities', 0):,} VND ({breakdown.get('activities', 0)/budget*100:.1f}%)
{'-'*80}
TỔNG:            {sum(breakdown.values()):,} VND

"""
        
        # Travel plan
        if "travel_plan" in result:
            plan = result["travel_plan"]
            output += f"""
{'='*80}
📅 LỊCH TRÌNH CHI TIẾT
{'='*80}
"""
            itinerary = plan.get("itinerary", {})
            for day, activities in itinerary.items():
                output += f"\n{day.upper()}\n{'-'*80}\n"
                for time, activity in activities.items():
                    emoji = "🌅" if "sáng" in time.lower() or "morning" in time.lower() else \
                            "☀️" if "trưa" in time.lower() or "noon" in time.lower() else \
                            "🌆" if "chiều" in time.lower() or "afternoon" in time.lower() else "🌙"
                    output += f"{emoji} {time.capitalize():15s} {activity}\n"
        
        # Recommendations
        if "recommendations" in result:
            recs = result["recommendations"]
            output += f"""
{'='*80}
🎯 ĐỊA ĐIỂM ĐỀ XUẤT
{'='*80}
"""
            
            category_names = {
                "hotels": "🏨 KHÁCH SẠN",
                "restaurants": "🍜 NHÀ HÀNG",
                "attractions": "🏛️ ĐIỂM THAM QUAN",
                "activities": "🎭 HOẠT ĐỘNG"
            }
            
            for category, items in recs.items():
                if items:
                    cat_name = category_names.get(category, category.upper())
                    output += f"\n{cat_name}\n{'-'*80}\n"
                    for i, item in enumerate(items[:5], 1):
                        name = item.get('name', 'Chưa rõ tên')
                        rating = item.get('rating', 'N/A')
                        price = item.get('price_level', 'N/A')
                        output += f"{i}. {name:40s} ⭐ {rating}/5.0  💵 {price}\n"
        
        output += f"""
{'='*80}
✅ HOÀN THÀNH
{'='*80}

🎉 Kế hoạch du lịch đã được tạo thành công!
💾 Dữ liệu đã được cache - lần chạy sau sẽ nhanh hơn!
🤖 10 AI agents đã làm việc để tạo kế hoạch tốt nhất cho bạn!

Chúc bạn có chuyến đi vui vẻ! 🌍✨

{'='*80}
"""
        
        yield output
        
    except Exception as e:
        yield f"""
{'='*80}
❌ LỖI
{'='*80}

Đã xảy ra lỗi:

{str(e)}

Vui lòng kiểm tra lại thông tin và thử lại.
{'='*80}
"""


def xu_ly_chat(tin_nhan, lich_su):
    """Xử lý chat với trợ lý AI"""
    try:
        if not tin_nhan.strip():
            return lich_su
        
        phan_hoi = chat_assistant.chat(tin_nhan)
        lich_su.append((tin_nhan, phan_hoi))
        return lich_su
    except Exception as e:
        lich_su.append((tin_nhan, f"Xin lỗi, đã có lỗi: {str(e)}"))
        return lich_su


def lay_thong_tin_hieu_biet():
    """Lấy thông tin mà assistant đã hiểu"""
    context = chat_assistant.user_context
    if not context:
        return """
💬 **Hãy chat với trợ lý để nhận tư vấn!**

Trợ lý sẽ nhớ các thông tin bạn chia sẻ và giúp điền form tự động.
"""
    
    info = f"""
{'='*60}
💭 TRỢ LÝ ĐÃ HIỂU
{'='*60}
"""
    if 'destination' in context:
        info += f"📍 Điểm đến:   {context['destination']}\n"
    if 'budget' in context:
        info += f"💰 Ngân sách:  {context['budget']:,} VND\n"
    if 'days' in context:
        info += f"📅 Số ngày:    {context['days']} ngày\n"
    if 'interests' in context:
        info += f"🎯 Sở thích:   {', '.join(context['interests'])}\n"
    
    info += f"{'='*60}\n"
    return info


def ap_dung_vao_form():
    """Áp dụng thông tin từ chat vào form"""
    context = chat_assistant.user_context
    
    diem_den = context.get('destination', '')
    ngan_sach = str(context.get('budget', ''))
    so_ngay = str(context.get('days', ''))
    so_thich = ', '.join(context.get('interests', []))
    
    return diem_den, ngan_sach, so_ngay, so_thich


def tao_giao_dien():
    """Tạo giao diện Gradio với layout mới"""
    
    # CSS tùy chỉnh
    custom_css = """
    .gradio-container {
        font-family: 'Segoe UI', 'Arial', sans-serif;
        max-width: 1600px !important;
        margin: auto !important;
    }
    .main-header {
        text-align: center;
        padding: 30px 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 15px;
        margin-bottom: 30px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .main-header h1 {
        font-size: 2.8em !important;
        font-weight: bold;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }
    .main-header p {
        font-size: 1.2em;
        margin: 10px 0 0 0;
        opacity: 0.95;
    }
    .section-header {
        background: linear-gradient(90deg, #f093fb 0%, #f5576c 100%);
        color: white;
        padding: 15px 25px;
        border-radius: 10px;
        margin: 20px 0 10px 0;
        text-align: center;
        font-size: 1.3em;
        font-weight: bold;
        box-shadow: 0 3px 5px rgba(0,0,0,0.1);
    }
    .output-markdown {
        font-family: 'Courier New', monospace;
        font-size: 14px;
        line-height: 1.8;
        background: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        white-space: pre-wrap;
    }
    .chat-section {
        background: linear-gradient(135deg, #667eea22 0%, #764ba222 100%);
        border-radius: 15px;
        padding: 25px;
        margin-top: 30px;
        border: 2px solid #667eea;
    }
    .footer {
        text-align: center;
        padding: 20px;
        color: #666;
        font-size: 0.95em;
        margin-top: 30px;
        border-top: 2px solid #e0e0e0;
    }
    """
    
    with gr.Blocks(
        theme=gr.themes.Soft(primary_hue="purple", secondary_hue="pink"),
        css=custom_css,
        title="Lập Kế Hoạch Du Lịch AI"
    ) as demo:
        
        # Header
        gr.HTML("""
            <div class="main-header">
                <h1>🌍 HỆ THỐNG LẬP KẾ HOẠCH DU LỊCH THÔNG MINH</h1>
                <p>Multi-Agent System for Travel Planning in Vietnam</p>
                <p style="font-size: 0.9em; margin-top: 5px;">
                    🤖 10 AI Agents • 📍 50,000+ Địa điểm • 💰 540,000+ Free API Requests/month
                </p>
            </div>
        """)
        
        # Main Planning Section - 2 Columns
        with gr.Row():
            # Left Column: Input Form
            with gr.Column(scale=1):
                gr.HTML('<div class="section-header">📝 THÔNG TIN CHUYẾN ĐI</div>')
                
                diem_di = gr.Textbox(
                    label="🚀 Điểm Đi (Xuất phát)",
                    placeholder="VD: Hà Nội, TP.HCM, Đà Nẵng...",
                    value="",
                    info="Để trống nếu du lịch tại chỗ"
                )
                
                diem_den = gr.Textbox(
                    label="🎯 Điểm Đến",
                    placeholder="VD: Hà Nội, Đà Nẵng, TP.HCM, Sapa...",
                    value="Đồng Nai",
                    info="Nhập tên thành phố hoặc địa điểm muốn đến"
                )
                
                ngan_sach = gr.Textbox(
                    label="💰 Ngân Sách (VND)",
                    placeholder="VD: 10000000",
                    value="10000000",
                    info="Tổng ngân sách cho chuyến đi"
                )
                
                so_ngay = gr.Textbox(
                    label="📅 Số Ngày",
                    placeholder="VD: 3",
                    value="3",
                    info="Số ngày dự định đi du lịch"
                )
                
                so_nguoi = gr.Textbox(
                    label="👥 Số Người",
                    placeholder="VD: 2",
                    value="2",
                    info="Số người tham gia chuyến đi"
                )
                
                so_thich = gr.Textbox(
                    label="🎯 Sở Thích / Mối Quan Tâm",
                    placeholder="VD: văn hóa, ẩm thực, thiên nhiên, lịch sử...",
                    value="văn hóa, ẩm thực",
                    info="Nhập các hoạt động hoặc chủ đề bạn quan tâm",
                    lines=2
                )
                
                with gr.Row():
                    nut_tao_plan = gr.Button(
                        "🚀 Tạo Kế Hoạch Du Lịch",
                        variant="primary",
                        size="lg",
                        scale=2
                    )
                    nut_xoa_form = gr.Button(
                        "🔄 Xóa",
                        variant="secondary",
                        size="lg",
                        scale=1
                    )
                
                gr.Markdown("""
                    ---
                    ### ⚡ Hướng Dẫn:
                    
                    **Cách 1:** Điền form và nhấn "🚀 Tạo Kế Hoạch"
                    
                    **Cách 2:** Chat với AI ở dưới → Nhấn "✨ Áp Dụng" → Tạo plan
                    
                    **Thời gian:** 10-30 giây (lần đầu), 2-5 giây (có cache)
                """)
            
            # Right Column: Output/Results
            with gr.Column(scale=2):
                gr.HTML('<div class="section-header">📊 KẾ HOẠCH DU LỊCH CỦA BẠN</div>')
                
                ket_qua = gr.HTML(
                    value="""
                    <div style="padding: 30px; background: linear-gradient(135deg, #667eea15 0%, #764ba215 100%); border-radius: 15px; border: 2px solid #667eea30;">
                        <!-- Welcome Header -->
                        <div style="text-align: center; margin-bottom: 30px;">
                            <h2 style="color: #667eea; font-size: 2em; margin: 0;">👋 CHÀO MỪNG ĐẾN VỚI TRAVEL PLANNER MAS</h2>
                            <p style="color: #666; font-size: 1.1em; margin-top: 10px;">Hệ thống sẵn sàng tạo kế hoạch du lịch hoàn hảo cho bạn!</p>
                        </div>
                        
                        <!-- Agents System -->
                        <div style="background: white; padding: 25px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                            <h3 style="color: #667eea; margin-top: 0; font-size: 1.3em;">🤖 HỆ THỐNG 10 AI AGENTS</h3>
                            
                            <!-- Layer 1 -->
                            <div style="background: #f0f7ff; padding: 15px; border-radius: 8px; margin-bottom: 12px; border-left: 4px solid #4299e1;">
                                <div style="font-weight: bold; color: #2c5282; margin-bottom: 8px;">📥 Data Collection Layer</div>
                                <div style="margin-left: 20px; color: #4a5568;">
                                    <div>1️⃣ <strong>API Collector</strong> - Thu thập từ 5 APIs (540K+ requests FREE)</div>
                                    <div>2️⃣ <strong>Web Scraper</strong> - Tìm kiếm web với Tavily</div>
                                </div>
                            </div>
                            
                            <!-- Layer 2 -->
                            <div style="background: #fff5f5; padding: 15px; border-radius: 8px; margin-bottom: 12px; border-left: 4px solid #f56565;">
                                <div style="font-weight: bold; color: #742a2a; margin-bottom: 8px;">⚙️ Data Processing Layer</div>
                                <div style="margin-left: 20px; color: #4a5568;">
                                    <div>3️⃣ <strong>Data Processor</strong> - Xử lý 50,000+ địa điểm</div>
                                </div>
                            </div>
                            
                            <!-- Layer 3 -->
                            <div style="background: #f0fff4; padding: 15px; border-radius: 8px; margin-bottom: 12px; border-left: 4px solid #48bb78;">
                                <div style="font-weight: bold; color: #22543d; margin-bottom: 8px;">🧠 ML Analysis Layer (Parallel)</div>
                                <div style="margin-left: 20px; color: #4a5568;">
                                    <div>4️⃣ <strong>Recommendation</strong> - ML-based gợi ý</div>
                                    <div>5️⃣ <strong>Sentiment Analyzer</strong> - Phân tích reviews</div>
                                    <div>6️⃣ <strong>Similarity Engine</strong> - Tìm địa điểm tương tự</div>
                                    <div>7️⃣ <strong>Price Predictor</strong> - Dự đoán và tối ưu giá</div>
                                </div>
                            </div>
                            
                            <!-- Layer 4 -->
                            <div style="background: #fffaf0; padding: 15px; border-radius: 8px; margin-bottom: 12px; border-left: 4px solid #ed8936;">
                                <div style="font-weight: bold; color: #7c2d12; margin-bottom: 8px;">📝 Planning Layer</div>
                                <div style="margin-left: 20px; color: #4a5568;">
                                    <div>8️⃣ <strong>Planner</strong> - Lập lịch trình chi tiết</div>
                                    <div>9️⃣ <strong>Researcher</strong> - Nghiên cứu địa phương</div>
                                </div>
                            </div>
                            
                            <!-- Layer 5 -->
                            <div style="background: #faf5ff; padding: 15px; border-radius: 8px; border-left: 4px solid #9f7aea;">
                                <div style="font-weight: bold; color: #44337a; margin-bottom: 8px;">📊 Analytics Layer</div>
                                <div style="margin-left: 20px; color: #4a5568;">
                                    <div>🔟 <strong>Analytics Engine</strong> - Phân tích tổng hợp</div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Getting Started -->
                        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 25px; border-radius: 12px; color: white; box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);">
                            <h3 style="margin-top: 0; font-size: 1.4em;">🚀 BẮT ĐẦU NGAY</h3>
                            
                            <div style="background: rgba(255,255,255,0.15); padding: 20px; border-radius: 8px; margin-bottom: 15px;">
                                <div style="font-weight: bold; margin-bottom: 10px; font-size: 1.1em;">Bạn có thể:</div>
                                <div style="margin-left: 10px;">
                                    <div style="margin-bottom: 8px;">📝 Điền form bên trái và nhấn <strong>"🚀 Tạo Kế Hoạch"</strong></div>
                                    <div style="margin-bottom: 8px;">💬 Chat với AI ở dưới để được tư vấn</div>
                                    <div>✨ Hoặc kết hợp cả hai!</div>
                                </div>
                            </div>
                            
                            <div style="background: rgba(255,255,255,0.15); padding: 20px; border-radius: 8px;">
                                <div style="font-weight: bold; margin-bottom: 10px; font-size: 1.1em;">Kết quả bạn nhận được:</div>
                                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-left: 10px;">
                                    <div>✅ Lịch trình chi tiết từng ngày</div>
                                    <div>✅ Khách sạn đề xuất</div>
                                    <div>✅ Nhà hàng gợi ý</div>
                                    <div>✅ Điểm tham quan</div>
                                    <div>✅ Phân bổ ngân sách chi tiết</div>
                                    <div>✅ Phân tích và insights</div>
                                </div>
                            </div>
                            
                            <div style="text-align: center; margin-top: 20px; font-size: 1.3em; font-weight: bold;">
                                Hãy bắt đầu ngay! 🌟
                            </div>
                        </div>
                    </div>
                    """
                )
        
        # Chat Assistant Section - Separate Area Below
        gr.HTML('<div class="chat-section">')
        gr.HTML('<div class="section-header">💬 TRỢ LÝ DU LỊCH AI - CHAT & TƯ VẤN</div>')
        
        with gr.Row():
            with gr.Column(scale=2):
                chatbot = gr.Chatbot(
                    label="Chat với AI Assistant",
                    height=400,
                    show_copy_button=True,
                    avatar_images=(None, "🤖"),
                    bubble_full_width=False
                )
                
                with gr.Row():
                    tin_nhan = gr.Textbox(
                        placeholder="💬 Hỏi bất cứ điều gì... VD: 'Địa điểm nào đẹp ở Đà Nẵng?'",
                        scale=5,
                        show_label=False,
                        container=False
                    )
                    nut_gui = gr.Button("📤 Gửi", scale=1, variant="primary", size="sm")
            
            with gr.Column(scale=1):
                thong_tin_hieu_biet = gr.Markdown(
                    value="💬 Bắt đầu chat để nhận tư vấn!",
                    label="Thông tin AI đã hiểu"
                )
                
                with gr.Row():
                    nut_ap_dung = gr.Button(
                        "✨ Áp Dụng Vào Form",
                        variant="secondary",
                        size="sm"
                    )
                    nut_xoa_chat = gr.Button(
                        "🔄 Xóa Chat",
                        variant="secondary",
                        size="sm"
                    )
                
                gr.Markdown("""
                    **💡 Gợi Ý Sử Dụng:**
                    
                    • "Nên đi đâu ở Hà Nội?"
                    • "10 triệu đi được không?"
                    • "Tôi thích thiên nhiên"
                    • "Gợi ý khách sạn"
                    
                    Chat tự nhiên, AI sẽ hiểu!
                """)
        
        gr.HTML('</div>')
        
        # Footer
        gr.HTML("""
            <div class="footer">
                <strong>Được xây dựng với ❤️ bởi Travel Planner MAS Team</strong><br>
                🤖 Powered by: OpenAI GPT-4 • LangGraph • AutoGen • LangChain<br>
                📊 Data: 50,000+ địa điểm Việt Nam • LocationIQ • Geoapify • OpenWeather<br>
                💰 100% Miễn phí với Free APIs • Tiết kiệm 99.97% so với Google Places
            </div>
        """)
        
        # Event handlers
        
        # Main planning
        nut_tao_plan.click(
            fn=tao_ke_hoach_du_lich,
            inputs=[diem_di, diem_den, ngan_sach, so_ngay, so_nguoi, so_thich],
            outputs=ket_qua
        )
        
        nut_xoa_form.click(
            fn=lambda: ("", "Đồng Nai", "1000000", "1", "1", "", ""),
            inputs=[],
            outputs=[diem_di, diem_den, ngan_sach, so_ngay, so_nguoi, so_thich, ket_qua]
        )
        
        # Chat
        def gui_chat(tin_nhan, lich_su):
            return xu_ly_chat(tin_nhan, lich_su), "", lay_thong_tin_hieu_biet()
        
        tin_nhan.submit(
            fn=gui_chat,
            inputs=[tin_nhan, chatbot],
            outputs=[chatbot, tin_nhan, thong_tin_hieu_biet]
        )
        
        nut_gui.click(
            fn=gui_chat,
            inputs=[tin_nhan, chatbot],
            outputs=[chatbot, tin_nhan, thong_tin_hieu_biet]
        )
        
        # Apply context
        nut_ap_dung.click(
            fn=ap_dung_vao_form,
            outputs=[diem_den, ngan_sach, so_ngay, so_thich]
        )
        
        # Clear chat
        def xoa_chat():
            chat_assistant.reset_conversation()
            return None, "💬 Chat đã được xóa! Bắt đầu lại từ đầu."
        
        nut_xoa_chat.click(
            fn=xoa_chat,
            outputs=[chatbot, thong_tin_hieu_biet]
        )
    return demo


if __name__ == "__main__":
    print("="*80)
    print("🚀 KHỞI ĐỘNG HỆ THỐNG LẬP KẾ HOẠCH DU LỊCH THÔNG MINH")
    print("="*80)
    print()
    print("🤖 10 AI Agents sẵn sàng")
    print("📍 50,000+ địa điểm Việt Nam")
    print("💰 540,000+ Free API requests/month")
    print()
    print("🌐 Giao diện sẽ mở tại: http://localhost:7860")
    print("💡 Nhấn CTRL+C để dừng server")
    print("="*80)
    print()
    
    demo = tao_giao_dien()
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False,
        show_error=True,
        inbrowser=True
    )

