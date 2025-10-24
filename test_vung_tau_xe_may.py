"""
Test: Du lịch Vũng Tàu từ TP.HCM (Gò Vấp) bằng xe máy
- 2 người, 2 ngày 1 đêm
- Bãi Sau + Tháp Tam Thắng
- Chi phí tối thiểu cho chuyến đi trung bình
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.append(str(project_root))

from agents.rag_agent import get_rag_agent
from utils.transport_calculator import calculate_transport_cost, validate_budget

def calculate_vung_tau_trip():
    """Tính chi phí chi tiết cho chuyến Vũng Tàu"""
    
    print("="*80)
    print("🏖️ TÍNH CHI PHÍ DU LỊCH VŨNG TÀU")
    print("="*80)
    
    # Trip details
    from_location = "TP.HCM Quận Gò Vấp"
    to_location = "Vũng Tàu"
    travelers = 2
    days = 2
    nights = 1
    
    print(f"\n📍 Điểm đi: {from_location}")
    print(f"🎯 Điểm đến: {to_location}")
    print(f"👥 Số người: {travelers}")
    print(f"📅 Thời gian: {days} ngày {nights} đêm")
    print(f"🏍️ Phương tiện: Xe máy tự túc")
    print(f"🏖️ Hoạt động: Bãi Sau + Tháp Tam Thắng")
    
    # Calculate detailed costs
    print("\n" + "="*80)
    print("💰 TÍNH CHI PHÍ CHI TIẾT")
    print("="*80)
    
    # 1. Transportation (Motorcycle)
    print("\n1️⃣ CHI PHÍ DI CHUYỂN (XE MÁY)")
    print("-" * 80)
    
    distance_one_way = 125  # km từ TP.HCM đến Vũng Tàu
    distance_total = distance_one_way * 2  # Khứ hồi
    
    # Xe máy tiêu thụ khoảng 2L/100km
    fuel_consumption = 2.0  # lít/100km
    fuel_price = 25000  # VND/lít (giá xăng hiện tại)
    fuel_needed = (distance_total / 100) * fuel_consumption
    fuel_cost = fuel_needed * fuel_price
    
    # Phí đường bộ (nếu có)
    toll_fee = 20000 * 2  # ~20k/lượt khứ hồi
    
    # Gửi xe (nếu ở khách sạn không free)
    parking_fee = 20000 * nights  # ~20k/đêm
    
    transport_cost = fuel_cost + toll_fee + parking_fee
    
    print(f"   Khoảng cách: {distance_one_way}km × 2 (khứ hồi) = {distance_total}km")
    print(f"   Xăng cần: {fuel_needed:.1f} lít × {fuel_price:,} VND/lít = {fuel_cost:,.0f} VND")
    print(f"   Phí cầu đường: {toll_fee:,} VND (khứ hồi)")
    print(f"   Gửi xe: {parking_fee:,} VND ({nights} đêm)")
    print(f"   ───────────────────────────────")
    print(f"   📊 Tổng di chuyển: {transport_cost:,.0f} VND")
    
    # 2. Accommodation
    print("\n2️⃣ CHI PHÍ LƯU TRÚ")
    print("-" * 80)
    
    # Khách sạn 2-3 sao gần Bãi Sau
    hotel_options = [
        {"name": "Khách sạn 2 sao (bình dân)", "price": 250000},
        {"name": "Khách sạn 3 sao (trung bình)", "price": 400000},
        {"name": "Khách sạn 3-4 sao (khá)", "price": 600000},
    ]
    
    print(f"   Lựa chọn khách sạn gần Bãi Sau ({nights} đêm):")
    for i, option in enumerate(hotel_options, 1):
        print(f"   {i}. {option['name']:40s} {option['price']:>10,} VND/đêm")
    
    # Chọn option trung bình
    selected_hotel = hotel_options[1]  # 3 sao
    hotel_cost = selected_hotel['price'] * nights
    
    print(f"\n   ✅ Gợi ý: {selected_hotel['name']}")
    print(f"   📊 Chi phí: {hotel_cost:,} VND")
    
    # 3. Food
    print("\n3️⃣ CHI PHÍ ĂN UỐNG")
    print("-" * 80)
    
    # Ăn uống trung bình tại Vũng Tàu
    meals = {
        "Sáng (bánh mì, phở)": 30000,
        "Trưa (cơm, hải sản bình dân)": 80000,
        "Tối (hải sản, nướng)": 150000,
        "Nước uống, cafe": 40000,
    }
    
    daily_food_per_person = sum(meals.values())
    total_food = daily_food_per_person * travelers * days
    
    print(f"   Chi phí ăn uống/người/ngày:")
    for meal, price in meals.items():
        print(f"   • {meal:35s} {price:>10,} VND")
    print(f"   ───────────────────────────────")
    print(f"   Tổng/người/ngày: {daily_food_per_person:,} VND")
    print(f"   📊 Tổng {travelers} người × {days} ngày: {total_food:,} VND")
    
    # 4. Activities
    print("\n4️⃣ CHI PHÍ HOẠT ĐỘNG & THAM QUAN")
    print("-" * 80)
    
    activities = {
        "Bãi Sau - Tắm biển": 0,  # FREE
        "Thuê ghế nằm + dù": 50000,  # Optional
        "Tháp Tam Thắng (Lighthouse) - Vé vào": 10000 * travelers,
        "Chụp ảnh check-in": 0,  # FREE
        "Tham quan Bãi Trước": 0,  # FREE
        "Ghé Chợ Vũng Tàu": 0,  # FREE
    }
    
    total_activities = sum(activities.values())
    
    print(f"   Hoạt động:")
    for activity, price in activities.items():
        price_text = "FREE" if price == 0 else f"{price:,} VND"
        print(f"   • {activity:50s} {price_text:>15s}")
    print(f"   ───────────────────────────────")
    print(f"   📊 Tổng: {total_activities:,} VND")
    
    # 5. Miscellaneous
    print("\n5️⃣ CHI PHÍ PHỤ")
    print("-" * 80)
    
    misc = {
        "Mua quà lưu niệm": 100000,
        "Thuê áo phao (nếu cần)": 20000,
        "Dự phòng": 50000,
    }
    
    total_misc = sum(misc.values())
    
    for item, price in misc.items():
        print(f"   • {item:40s} {price:>10,} VND")
    print(f"   ───────────────────────────────")
    print(f"   📊 Tổng: {total_misc:,} VND")
    
    # TOTAL COST
    print("\n" + "="*80)
    print("📊 TỔNG KẾT CHI PHÍ")
    print("="*80)
    
    total_cost = transport_cost + hotel_cost + total_food + total_activities + total_misc
    cost_per_person = total_cost / travelers
    
    print(f"\n   1. Di chuyển (xe máy):        {transport_cost:>15,} VND")
    print(f"   2. Khách sạn ({nights} đêm):          {hotel_cost:>15,} VND")
    print(f"   3. Ăn uống ({days} ngày):            {total_food:>15,} VND")
    print(f"   4. Hoạt động & tham quan:     {total_activities:>15,} VND")
    print(f"   5. Chi phí phụ:               {total_misc:>15,} VND")
    print(f"   {'─'*60}")
    print(f"   💰 TỔNG CHI PHÍ:              {total_cost:>15,} VND")
    print(f"   👤 Chi phí/người:             {cost_per_person:>15,} VND")
    
    # Budget recommendations
    print("\n" + "="*80)
    print("💡 GỢI Ý NGÂN SÁCH")
    print("="*80)
    
    budgets = {
        "Tối thiểu (bình dân)": total_cost,
        "Trung bình (thoải mái)": total_cost * 1.3,
        "Khá giả (sang trọng)": total_cost * 1.8,
    }
    
    for level, amount in budgets.items():
        per_person = amount / travelers
        print(f"   • {level:30s} {amount:>12,} VND ({per_person:>10,} VND/người)")
    
    # Detailed itinerary
    print("\n" + "="*80)
    print("📅 LỊCH TRÌNH CHI TIẾT 2 NGÀY 1 ĐÊM")
    print("="*80)
    
    print("""
🌅 NGÀY 1: TPHCM → VŨNG TÀU

06:00  🏍️ Xuất phát từ Gò Vấp
       📍 Quận Gò Vấp → Quốc lộ 51 → Vũng Tàu
       ⏰ Khoảng 2.5 giờ (125km)
       💰 Xăng: ~{:.0f} VND (1 chiều)

08:30  🍜 Ăn sáng tại Vũng Tàu
       📍 Bánh mì Huyền hoặc Phở Hùng
       💰 30,000 VND/người

09:30  🏨 Check-in khách sạn gần Bãi Sau
       📍 Đường Thùy Vân, Vũng Tàu
       💰 Đặt phòng trước để có giá tốt
       ⏰ Gửi đồ, nghỉ ngơi

10:30  🏖️ Tắm biển Bãi Sau
       📍 Bãi Sau, đường Thùy Vân
       💰 FREE (thuê ghế nằm 50k optional)
       ⏰ 2-3 giờ

13:00  🍲 Ăn trưa hải sản
       📍 Quán Ngọc Sương hoặc các quán ven biển
       💰 80,000-100,000 VND/người
       🦐 Gợi ý: Ghẹ hấp, nghêu hấp, cá nướng

15:00  💒 Tháp Tam Thắng (Check-in)
       📍 Núi Nhỏ, Vũng Tàu
       💰 10,000 VND/người vé vào
       ⏰ 1.5 giờ tham quan + chụp hình
       📸 View đẹp nhìn toàn cảnh thành phố

16:30  🚶 Dạo Bãi Trước
       📍 Dọc bờ biển Bãi Trước
       💰 FREE
       ⏰ 1 giờ

18:00  🍜 Ăn tối hải sản nướng
       📍 Khu ẩm thực Thùy Vân
       💰 150,000-200,000 VND/người
       🦑 Gợi ý: Mực nướng, tôm nướng, sò điệp

20:00  ☕ Cafe ngắm biển ban đêm
       📍 Cafe ven biển Bãi Sau
       💰 40,000 VND/người

21:30  🏨 Về khách sạn nghỉ ngơi

🌅 NGÀY 2: KHÁM PHÁ & TRỞ VỀ

06:30  🌅 Dậy sớm ngắm bình minh
       📍 Bãi Trước hoặc Bãi Sau
       💰 FREE

07:30  🍜 Ăn sáng Bánh khọt Vũng Tàu
       📍 Bánh khọt Gốc Vú Sữa
       💰 30,000-40,000 VND/người

09:00  🏪 Ghé chợ Vũng Tàu mua đặc sản
       📍 Chợ Vũng Tàu
       💰 100,000 VND (mua quà: bánh bông lan, khô cá...)
       ⏰ 1 giờ

10:00  🏖️ Tắm biển lần cuối
       📍 Bãi Sau
       ⏰ 1 giờ

11:00  🏨 Check-out khách sạn

11:30  🍲 Ăn trưa nhẹ
       📍 Lẩu mắm/Bánh canh gần đường về
       💰 70,000 VND/người

13:00  🏍️ Khởi hành về TP.HCM
       📍 Vũng Tàu → Quốc lộ 51 → Gò Vấp
       ⏰ Khoảng 2.5 giờ

15:30  🏠 Về đến Gò Vấp

""".format(fuel_cost / 2))
    
    # Cost saving tips
    print("\n" + "="*80)
    print("💡 MẸO TIẾT KIỆM CHI PHÍ")
    print("="*80)
    
    print("""
✅ Để giảm chi phí:
   • Đặt khách sạn online trước (Booking, Traveloka) giảm 10-20%
   • Ăn tại quán địa phương thay vì resort
   • Tránh cuối tuần (giá khách sạn cao gấp đôi)
   • Mang theo nước uống từ nhà
   • Đi nhóm 3-4 người để chia phòng rẻ hơn

⚠️ Lưu ý quan trọng:
   • Kiểm tra xe máy kỹ trước khi đi
   • Mang theo áo mưa (thời tiết biển thất thường)
   • Đặt phòng trước, đặc biệt cuối tuần
   • Mang kem chống nắng, mũ
   • Đổ đầy bình xăng ở TP.HCM (rẻ hơn Vũng Tàu)

🏖️ Thời điểm tốt nhất:
   • Thứ 2-5: Ít người, giá rẻ hơn
   • Tháng 3-8: Thời tiết đẹp, nắng nhiều
   • Tránh mùa mưa (9-11): Sóng to, gió lớn
""")
    
    print("\n" + "="*80)
    print(f"✅ ĐÁP ÁN: Tối thiểu cần {total_cost:,} VND cho 2 người")
    print(f"   ({cost_per_person:,} VND/người)")
    print("="*80)
    
    return {
        'total_cost': total_cost,
        'cost_per_person': cost_per_person,
        'transport': transport_cost,
        'hotel': hotel_cost,
        'food': total_food,
        'activities': total_activities,
        'misc': total_misc
    }

if __name__ == "__main__":
    result = calculate_vung_tau_trip()

