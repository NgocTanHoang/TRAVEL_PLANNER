"""
HTML Formatter for Travel Plan Output
======================================
Format kết quả du lịch thành HTML đẹp
"""

from typing import Dict, Any, List
from utils.geocoding_helper import get_geocoding_helper
from config.bus_routes import get_bus_info

# Initialize geocoding helper
geocoding = get_geocoding_helper()


def format_travel_plan_html(
    diem_den: str,
    budget: int,
    days: int,
    travelers: int,
    so_thich: str,
    result: Dict[str, Any]
) -> str:
    """
    Format travel plan thành HTML đẹp
    
    Args:
        diem_den: Điểm đến
        budget: Ngân sách
        days: Số ngày
        travelers: Số người
        so_thich: Sở thích
        result: Kết quả từ workflow
    
    Returns:
        HTML string
    """
    
    # Get recommendations
    recommendations = result.get('recommendations', {})
    hotels = recommendations.get('hotels', [])
    restaurants = recommendations.get('restaurants', [])
    attractions = recommendations.get('attractions', [])
    
    # Get AI insights
    ai_insights = result.get('ai_insights', '')
    
    # Get web insights
    web_insights = result.get('web_insights', [])
    
    # Get transport info
    transport_info = result.get('transport_info', {})
    budget_breakdown = result.get('budget_breakdown', {})
    departure_city = result.get('departure_city', '')
    
    # Get weather info
    try:
        from utils.weather_helper import get_weather_recommendations
        weather_info = get_weather_recommendations(diem_den)
    except:
        weather_info = None
    
    # Build HTML
    html = f"""
    <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 1200px; margin: 0 auto;">
        
        <!-- Header -->
        <div style="text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; border-radius: 15px; color: white; margin-bottom: 30px; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
            <h1 style="margin: 0; font-size: 2.5em; text-shadow: 2px 2px 4px rgba(0,0,0,0.3);">🌍 KẾ HOẠCH DU LỊCH {diem_den.upper()}</h1>
            <p style="margin: 10px 0 0 0; font-size: 1.2em; opacity: 0.95;">Được tạo bởi RAG AI System</p>
        </div>
        
        <!-- Transport Section -->
        {f'''
        <div style="background: linear-gradient(135deg, #4299e115, #3b82f615); padding: 25px; border-radius: 15px; margin-bottom: 25px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); border-left: 5px solid #3b82f6;">
            <h2 style="color: #1e40af; margin-top: 0; display: flex; align-items: center;">
                🚗 PHƯƠNG TIỆN DI CHUYỂN
            </h2>
            <div style="background: white; padding: 15px; border-radius: 10px; margin-bottom: 15px;">
                <div style="font-size: 1.1em; color: #2d3748; margin-bottom: 10px;">
                    <strong>{departure_city}</strong> → <strong>{diem_den}</strong>: {transport_info.get('distance', 0)}km
                </div>
                <div style="color: #48bb78; font-size: 1.2em; font-weight: bold;">
                    ✅ Gợi ý: {transport_info.get('recommended', 'N/A')}
                </div>
            </div>
            <div style="display: grid; gap: 10px;">
                {''.join([f"""
                <div style="background: white; padding: 15px; border-radius: 10px; display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="font-weight: bold; color: #2d3748; margin-bottom: 5px;">{opt['type']}</div>
                        <div style="color: #718096; font-size: 0.9em;">{opt['duration']} • {opt['note']}</div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 1.3em; font-weight: bold; color: #3b82f6;">{opt['total_cost']:,} VND</div>
                        <div style="color: #718096; font-size: 0.85em;">{opt['cost_per_person']:,} VND/người</div>
                    </div>
                </div>
                """ for opt in transport_info.get('options', [])[:4]])}
            </div>
        </div>
        ''' if transport_info.get('options') else ''}
        
        <!-- Weather Section -->
        {f'''
        <div style="background: linear-gradient(135deg, #fef3c7, #fde68a); padding: 25px; border-radius: 15px; margin-bottom: 25px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); border-left: 5px solid #f59e0b;">
            <h2 style="color: #92400e; margin-top: 0; display: flex; align-items: center;">
                🌤️ THÔNG TIN THỜI TIẾT
            </h2>
            <div style="background: white; padding: 20px; border-radius: 10px; line-height: 1.8; white-space: pre-line;">
                {weather_info.replace('**', '<strong>').replace('**', '</strong>')}
            </div>
        </div>
        ''' if weather_info else ''}
        
        <!-- Thông tin chuyến đi -->
        <div style="background: white; padding: 25px; border-radius: 15px; margin-bottom: 25px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <h2 style="color: #667eea; margin-top: 0; border-bottom: 3px solid #667eea; padding-bottom: 10px;">
                📋 THÔNG TIN CHUYẾN ĐI
            </h2>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin-top: 20px;">
                <div style="padding: 15px; background: linear-gradient(135deg, #667eea15, #667eea05); border-radius: 10px; border-left: 4px solid #667eea;">
                    <div style="color: #718096; font-size: 0.9em; margin-bottom: 5px;">📍 Điểm đến</div>
                    <div style="font-weight: bold; font-size: 1.3em; color: #2d3748;">{diem_den}</div>
                </div>
                <div style="padding: 15px; background: linear-gradient(135deg, #48bb7815, #48bb7805); border-radius: 10px; border-left: 4px solid #48bb78;">
                    <div style="color: #718096; font-size: 0.9em; margin-bottom: 5px;">💰 Ngân sách</div>
                    <div style="font-weight: bold; font-size: 1.3em; color: #2d3748;">{budget:,} VND</div>
                </div>
                <div style="padding: 15px; background: linear-gradient(135deg, #ed893615, #ed893605); border-radius: 10px; border-left: 4px solid #ed8936;">
                    <div style="color: #718096; font-size: 0.9em; margin-bottom: 5px;">📅 Số ngày</div>
                    <div style="font-weight: bold; font-size: 1.3em; color: #2d3748;">{days} ngày</div>
                </div>
                <div style="padding: 15px; background: linear-gradient(135deg, #f5656515, #f5656505); border-radius: 10px; border-left: 4px solid #f56565;">
                    <div style="color: #718096; font-size: 0.9em; margin-bottom: 5px;">👥 Số người</div>
                    <div style="font-weight: bold; font-size: 1.3em; color: #2d3748;">{travelers} người</div>
                </div>
            </div>
            {f'''
            <div style="margin-top: 20px; padding: 15px; background: linear-gradient(135deg, #9f7aea15, #9f7aea05); border-radius: 10px; border-left: 4px solid #9f7aea;">
                <div style="color: #718096; font-size: 0.9em; margin-bottom: 5px;">🎯 Sở thích</div>
                <div style="font-weight: bold; font-size: 1.2em; color: #2d3748;">{so_thich}</div>
            </div>
            ''' if so_thich else ''}
        </div>
    """
    
    # AI Insights (nếu có)
    if ai_insights:
        html += f"""
        <div style="background: linear-gradient(135deg, #faf089 0%, #f6e05e 100%); padding: 25px; border-radius: 15px; margin-bottom: 25px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <h2 style="color: #744210; margin-top: 0; display: flex; align-items: center;">
                💡 AI INSIGHTS
            </h2>
            <div style="color: #2d3748; line-height: 1.8; white-space: pre-line;">
{ai_insights}
            </div>
        </div>
        """
    
    # Hotels
    if hotels:
        html += """
        <div style="background: white; padding: 25px; border-radius: 15px; margin-bottom: 25px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <h2 style="color: #667eea; margin-top: 0; border-bottom: 3px solid #667eea; padding-bottom: 10px;">
                🏨 KHÁCH SẠN ĐỀ XUẤT
            </h2>
            <div style="display: grid; gap: 15px; margin-top: 20px;">
        """
        
        for i, hotel in enumerate(hotels[:5], 1):
            rating_stars = "⭐" * int(hotel.get('rating', 0))
            price_text = f"{hotel.get('price', 0):,.0f} VND/đêm" if hotel.get('price', 0) > 0 else "200,000-400,000 VND/đêm"
            
            # Get address
            lat = hotel.get('latitude')
            lon = hotel.get('longitude')
            address = "Đang cập nhật địa chỉ..."
            if lat and lon:
                try:
                    addr_info = geocoding.get_detailed_info(lat, lon)
                    if addr_info:
                        street = addr_info.get('street', '')
                        suburb = addr_info.get('suburb', '')
                        city = addr_info.get('city', '')
                        address = f"{street}, {suburb}, {city}".strip(', ')
                        if not address or address == ', , ':
                            address = addr_info.get('formatted', 'Địa chỉ không rõ')[:80]
                except:
                    address = hotel.get('description', '')[:80] if hotel.get('description') else 'Trung tâm ' + diem_den
            
            html += f"""
            <div style="padding: 20px; background: linear-gradient(135deg, #f7fafc, #edf2f7); border-radius: 12px; border-left: 5px solid #667eea; transition: transform 0.2s;">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div style="flex: 1;">
                        <div style="font-size: 1.3em; font-weight: bold; color: #2d3748; margin-bottom: 8px;">
                            {i}. {hotel.get('name', 'N/A')}
                        </div>
                        <div style="color: #718096; margin-bottom: 5px;">
                            {rating_stars} <span style="font-weight: bold; color: #2d3748;">{hotel.get('rating', 0)}/5.0</span>
                        </div>
                        <div style="color: #3b82f6; margin-bottom: 5px; font-size: 0.95em;">
                            📍 {address}
                        </div>
                        <div style="color: #48bb78; font-weight: bold; font-size: 1.1em;">
                            💰 {price_text}
                        </div>
                    </div>
                </div>
            </div>
            """
        
        html += """
            </div>
        </div>
        """
    
    # Restaurants
    if restaurants:
        html += """
        <div style="background: white; padding: 25px; border-radius: 15px; margin-bottom: 25px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <h2 style="color: #48bb78; margin-top: 0; border-bottom: 3px solid #48bb78; padding-bottom: 10px;">
                🍜 NHÀ HÀNG ĐỀ XUẤT
            </h2>
            <div style="display: grid; gap: 15px; margin-top: 20px;">
        """
        
        for i, rest in enumerate(restaurants[:5], 1):
            rating_stars = "⭐" * int(rest.get('rating', 0))
            price_text = f"{rest.get('price', 0):,.0f} VND/người" if rest.get('price', 0) > 0 else "30,000-80,000 VND/người"
            
            # Get address
            lat = rest.get('latitude')
            lon = rest.get('longitude')
            address = "Đang cập nhật địa chỉ..."
            if lat and lon:
                try:
                    addr_info = geocoding.get_detailed_info(lat, lon)
                    if addr_info:
                        street = addr_info.get('street', '')
                        suburb = addr_info.get('suburb', '')
                        city = addr_info.get('city', '')
                        address = f"{street}, {suburb}, {city}".strip(', ')
                        if not address or address == ', , ':
                            address = addr_info.get('formatted', 'Địa chỉ không rõ')[:80]
                except:
                    address = rest.get('description', '')[:80] if rest.get('description') else 'Trung tâm ' + diem_den
            
            html += f"""
            <div style="padding: 20px; background: linear-gradient(135deg, #f0fff4, #c6f6d5); border-radius: 12px; border-left: 5px solid #48bb78;">
                <div style="font-size: 1.3em; font-weight: bold; color: #2d3748; margin-bottom: 8px;">
                    {i}. {rest.get('name', 'N/A')}
                </div>
                <div style="color: #718096; margin-bottom: 5px;">
                    {rating_stars} <span style="font-weight: bold; color: #2d3748;">{rest.get('rating', 0)}/5.0</span>
                </div>
                <div style="color: #3b82f6; margin-bottom: 5px; font-size: 0.95em;">
                    📍 {address}
                </div>
                <div style="color: #48bb78; font-weight: bold;">
                    💰 {price_text}
                </div>
            </div>
            """
        
        html += """
            </div>
        </div>
        """
    
    # Attractions
    if attractions:
        html += """
        <div style="background: white; padding: 25px; border-radius: 15px; margin-bottom: 25px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <h2 style="color: #ed8936; margin-top: 0; border-bottom: 3px solid #ed8936; padding-bottom: 10px;">
                🏛️ ĐIỂM THAM QUAN ĐỀ XUẤT
            </h2>
            <div style="display: grid; gap: 15px; margin-top: 20px;">
        """
        
        for i, attr in enumerate(attractions[:5], 1):
            rating_stars = "⭐" * int(attr.get('rating', 0))
            price_text = f"{attr.get('price', 0):,.0f} VND" if attr.get('price', 0) > 0 else "Miễn phí"
            
            # Get address
            lat = attr.get('latitude')
            lon = attr.get('longitude')
            address = "Đang cập nhật địa chỉ..."
            if lat and lon:
                try:
                    addr_info = geocoding.get_detailed_info(lat, lon)
                    if addr_info:
                        street = addr_info.get('street', '')
                        suburb = addr_info.get('suburb', '')
                        city = attr.get('city', '')
                        address = f"{street}, {suburb}, {city}".strip(', ')
                        if not address or address == ', , ':
                            address = addr_info.get('formatted', 'Địa chỉ không rõ')[:80]
                except:
                    address = attr.get('description', '')[:80] if attr.get('description') else 'Trung tâm ' + diem_den
            
            html += f"""
            <div style="padding: 20px; background: linear-gradient(135deg, #fffaf0, #feebc8); border-radius: 12px; border-left: 5px solid #ed8936;">
                <div style="font-size: 1.3em; font-weight: bold; color: #2d3748; margin-bottom: 8px;">
                    {i}. {attr.get('name', 'N/A')}
                </div>
                <div style="color: #718096; margin-bottom: 5px;">
                    {rating_stars} <span style="font-weight: bold; color: #2d3748;">{attr.get('rating', 0)}/5.0</span>
                </div>
                <div style="color: #3b82f6; margin-bottom: 5px; font-size: 0.95em;">
                    📍 {address}
                </div>
                <div style="color: #ed8936; font-weight: bold;">
                    🎫 {price_text}
                </div>
            </div>
            """
        
        html += """
            </div>
        </div>
        """
    
    # Bus Info
    bus_info = get_bus_info(diem_den)
    if bus_info:
        html += f"""
        <div style="background: white; padding: 25px; border-radius: 15px; margin-bottom: 25px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <h2 style="color: #3b82f6; margin-top: 0; border-bottom: 3px solid #3b82f6; padding-bottom: 10px;">
                🚌 THÔNG TIN XE BUÝT TẠI {diem_den.upper()}
            </h2>
            <div style="background: linear-gradient(135deg, #eff6ff, #dbeafe); padding: 20px; border-radius: 12px; margin-top: 15px; border-left: 5px solid #3b82f6;">
                <div style="color: #1e40af; line-height: 2; white-space: pre-line; font-size: 1.05em;">
{bus_info}
                </div>
            </div>
        </div>
        """
    
    # Web Resources (nếu có)
    if web_insights and len(web_insights) > 0:
        html += """
        <div style="background: white; padding: 25px; border-radius: 15px; margin-bottom: 25px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <h2 style="color: #9f7aea; margin-top: 0; border-bottom: 3px solid #9f7aea; padding-bottom: 10px;">
                🌐 TÀI NGUYÊN WEB
            </h2>
            <div style="display: grid; gap: 12px; margin-top: 20px;">
        """
        
        for i, web in enumerate(web_insights[:3], 1):
            html += f"""
            <div style="padding: 15px; background: #faf5ff; border-radius: 10px; border-left: 4px solid #9f7aea;">
                <a href="{web.get('url', '#')}" target="_blank" style="color: #667eea; text-decoration: none; font-weight: bold; font-size: 1.1em;">
                    {i}. {web.get('title', 'Link')}
                </a>
                <div style="color: #718096; font-size: 0.9em; margin-top: 5px;">
                    {web.get('url', '')}
                </div>
            </div>
            """
        
        html += """
            </div>
        </div>
        """
    
    # Summary & Stats
    workflow_result = result.get('workflow_result', {})
    
    html += f"""
        <div style="background: linear-gradient(135deg, #e0e7ff, #c7d2fe); padding: 25px; border-radius: 15px; margin-bottom: 25px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
            <h2 style="color: #4c51bf; margin-top: 0;">
                📊 TỔNG KẾT
            </h2>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-top: 15px;">
                <div style="text-align: center; padding: 15px; background: white; border-radius: 10px;">
                    <div style="font-size: 2em; color: #667eea;">🏨</div>
                    <div style="font-size: 1.5em; font-weight: bold; color: #2d3748;">{len(hotels)}</div>
                    <div style="color: #718096;">Khách sạn</div>
                </div>
                <div style="text-align: center; padding: 15px; background: white; border-radius: 10px;">
                    <div style="font-size: 2em; color: #48bb78;">🍜</div>
                    <div style="font-size: 1.5em; font-weight: bold; color: #2d3748;">{len(restaurants)}</div>
                    <div style="color: #718096;">Nhà hàng</div>
                </div>
                <div style="text-align: center; padding: 15px; background: white; border-radius: 10px;">
                    <div style="font-size: 2em; color: #ed8936;">🏛️</div>
                    <div style="font-size: 1.5em; font-weight: bold; color: #2d3748;">{len(attractions)}</div>
                    <div style="color: #718096;">Điểm tham quan</div>
                </div>
                <div style="text-align: center; padding: 15px; background: white; border-radius: 10px;">
                    <div style="font-size: 2em; color: #9f7aea;">🤖</div>
                    <div style="font-size: 1.5em; font-weight: bold; color: #2d3748;">10</div>
                    <div style="color: #718096;">AI Agents</div>
                </div>
            </div>
        </div>
        
        <!-- Footer -->
        <div style="text-align: center; padding: 25px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 15px; color: white; box-shadow: 0 4px 15px rgba(0,0,0,0.2);">
            <h3 style="margin: 0 0 10px 0;">🎉 Chúc bạn có chuyến đi vui vẻ!</h3>
            <p style="margin: 5px 0; opacity: 0.9;">Kế hoạch được tạo bởi RAG AI System với Vector Database (50K+ places)</p>
            <p style="margin: 5px 0; opacity: 0.9;">💾 Dữ liệu đã được cache - lần tìm kiếm sau sẽ nhanh hơn!</p>
            <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid rgba(255,255,255,0.3);">
                <small>Powered by: OpenAI GPT-4 • ChromaDB • Tavily • LangGraph</small>
            </div>
        </div>
    </div>
    """
    
    return html
