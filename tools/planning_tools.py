"""
Planning Tools - Công cụ lập kế hoạch
======================================
- Tạo lịch trình hàng ngày
- Phân bổ thời gian
- Đề xuất hoạt động theo thời gian
- Sử dụng OpenAI GPT-4o-mini để tạo lịch trình tự nhiên và thú vị
"""
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import os

logger = logging.getLogger(__name__)

# Initialize OpenAI LLM for natural language generation
_llm = None
def get_llm():
    """Get OpenAI LLM instance"""
    global _llm
    if _llm is None:
        try:
            OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
            if OPENAI_API_KEY:
                from langchain_openai import ChatOpenAI
                _llm = ChatOpenAI(
                    model=os.getenv('MODEL', 'gpt-4o-mini'),
                    temperature=0.7,
                    api_key=OPENAI_API_KEY
                )
                logger.info("OpenAI LLM initialized for planning tools")
            else:
                logger.warning("OPENAI_API_KEY not found, LLM disabled")
        except Exception as e:
            logger.warning(f"Failed to initialize OpenAI LLM: {e}")
    return _llm


class PlanningTools:
    """Công cụ lập kế hoạch cho Planning Agent"""
    
    # Khung giờ hoạt động trong ngày
    TIME_SLOTS = {
        'morning': {'start': 8, 'end': 12, 'label': 'Sáng (8h-12h)'},
        'afternoon': {'start': 12, 'end': 17, 'label': 'Chiều (12h-17h)'},
        'evening': {'start': 17, 'end': 21, 'label': 'Tối (17h-21h)'},
        'night': {'start': 21, 'end': 23, 'label': 'Đêm (21h-23h)'}
    }
    
    def create_daily_schedule(
        self,
        day: int,
        date: str,
        destination: str,
        hotels: List[Dict] = None,
        restaurants: List[Dict] = None,
        activities: List[Dict] = None,
        travel_style: str = 'standard'
    ) -> Dict[str, Any]:
        """
        Tạo lịch trình cho một ngày
        
        Args:
            day: Số thứ tự ngày (1, 2, 3...)
            date: Ngày (YYYY-MM-DD)
            destination: Điểm đến
            hotels: Danh sách khách sạn
            restaurants: Danh sách nhà hàng
            activities: Danh sách hoạt động
            travel_style: 'budget', 'standard', 'luxury'
            
        Returns:
            Dict với lịch trình chi tiết
        """
        hotel = hotels[0] if hotels else None
        schedule = {
            'day': day,
            'date': date,
            'theme': self._suggest_theme(day, destination, travel_style),
            'accommodation': hotel,
            'meals': {
                'breakfast': self._suggest_restaurant(restaurants, 'breakfast', travel_style, day),
                'lunch': self._suggest_restaurant(restaurants, 'lunch', travel_style, day),
                'dinner': self._suggest_restaurant(restaurants, 'dinner', travel_style, day),
                'snacks': self._suggest_restaurant(restaurants, 'snack', travel_style, day),
                'drinks': self._suggest_restaurant(restaurants, 'drink', travel_style, day),
                'afternoon_tea': self._suggest_restaurant(restaurants, 'afternoon_tea', travel_style, day) if travel_style in ['standard', 'luxury'] else None
            },
            'activities': self._distribute_activities(activities, day, travel_style),
            'tips': self._generate_tips(destination, day, travel_style)
        }
        
        return schedule
    
    def _suggest_theme(self, day: int, destination: str, travel_style: str = 'standard') -> str:
        """Đề xuất chủ đề cho ngày - có thể dùng AI để tạo tự nhiên hơn"""
        llm = get_llm()
        
        if llm:
            try:
                prompt = f"""Bạn là chuyên gia du lịch Việt Nam. Hãy đề xuất một chủ đề thú vị cho ngày {day} trong chuyến du lịch đến {destination}.
Phong cách du lịch: {travel_style} (budget/standard/luxury)
Chỉ trả về chủ đề ngắn gọn, không giải thích thêm. Ví dụ: "Khám phá ẩm thực địa phương" hoặc "Tham quan di tích lịch sử"."""
                
                response = llm.invoke(prompt)
                theme = response.content if hasattr(response, 'content') else str(response)
                return theme.strip()
            except Exception as e:
                logger.warning(f"LLM theme generation failed: {e}, using fallback")
        
        # Fallback themes
        themes = {
            1: 'Khám phá & Tham quan',
            2: 'Văn hóa & Lịch sử',
            3: 'Thiên nhiên & Giải trí',
            4: 'Thư giãn & Mua sắm',
            5: 'Ẩm thực & Trải nghiệm'
        }
        return themes.get(day, f'Du lịch {destination}')
    
    def _suggest_restaurant(
        self,
        restaurants: Optional[List[Dict]],
        meal_type: str,
        travel_style: str = 'standard',
        day: int = 1
    ) -> Optional[Dict]:
        """
        Đề xuất nhà hàng cho bữa ăn
        
        Args:
            restaurants: Danh sách nhà hàng
            meal_type: Loại bữa ăn (breakfast, lunch, dinner, snack, drink, afternoon_tea)
            travel_style: 'budget', 'standard', 'luxury'
        """
        if not restaurants:
            return None
        
        # Map meal_type với query keywords
        meal_keywords = {
            'breakfast': ['bữa sáng', 'breakfast', 'café', 'quán ăn sáng', 'phở', 'bún'],
            'lunch': ['bữa trưa', 'lunch', 'nhà hàng', 'quán ăn', 'cơm', 'phở'],
            'dinner': ['bữa tối', 'dinner', 'nhà hàng', 'fine dining', 'restaurant'],
            'snack': ['ăn vặt', 'snack', 'street food', 'quán vỉa hè', 'chè', 'bánh'],
            'drink': ['cà phê', 'coffee', 'trà', 'drink', 'nước giải khát', 'café'],
            'afternoon_tea': ['trà chiều', 'afternoon tea', 'high tea', 'tea house', 'trà']
        }
        
        keywords = meal_keywords.get(meal_type, ['nhà hàng'])
        
        # Filter restaurants theo meal_type và travel_style
        filtered = []
        for rest in restaurants:
            rest_name = rest.get('name', '').lower()
            rest_desc = rest.get('description', '').lower()
            rest_cuisine = rest.get('cuisine', '').lower()
            
            # Check nếu restaurant phù hợp với meal_type
            matches_meal = any(kw in rest_name or kw in rest_desc or kw in rest_cuisine for kw in keywords)
            
            # Check travel_style qua price_range hoặc rating
            price_range = rest.get('price_range', '').lower()
            rating = rest.get('rating', 0)
            
            matches_style = False
            if travel_style == 'budget':
                matches_style = price_range in ['low', 'budget', 'cheap', ''] or rating < 4.0
            elif travel_style == 'standard':
                matches_style = price_range in ['medium', 'moderate', ''] or 3.5 <= rating <= 4.5
            elif travel_style == 'luxury':
                matches_style = price_range in ['high', 'luxury', 'fine'] or rating >= 4.5
            
            if matches_meal and matches_style:
                filtered.append(rest)
        
        # Nếu không tìm thấy phù hợp, chọn theo travel_style
        if not filtered:
            for rest in restaurants:
                price_range = rest.get('price_range', '').lower()
                rating = rest.get('rating', 0)
                
                if travel_style == 'budget' and (price_range in ['low', 'budget', ''] or rating < 4.0):
                    filtered.append(rest)
                elif travel_style == 'standard' and (price_range in ['medium', ''] or 3.5 <= rating <= 4.5):
                    filtered.append(rest)
                elif travel_style == 'luxury' and (price_range in ['high', 'luxury'] or rating >= 4.5):
                    filtered.append(rest)
        
        # Return restaurant đầu tiên phù hợp, hoặc random để đa dạng
        if filtered:
            # Để đa dạng, chọn theo index (day * meal_type_offset) để mỗi ngày và mỗi bữa khác nhau
            meal_offsets = {'breakfast': 0, 'lunch': 1, 'dinner': 2, 'snack': 3, 'drink': 4, 'afternoon_tea': 5}
            offset = meal_offsets.get(meal_type, 0)
            index = ((day - 1) * 6 + offset) % len(filtered)
            return filtered[index]
        
        # Fallback: chọn theo rotation để đa dạng
        if restaurants:
            meal_offsets = {'breakfast': 0, 'lunch': 1, 'dinner': 2, 'snack': 3, 'drink': 4, 'afternoon_tea': 5}
            offset = meal_offsets.get(meal_type, 0)
            index = ((day - 1) * 6 + offset) % len(restaurants)
            return restaurants[index]
        
        return None
    
    def _distribute_activities(
        self,
        activities: Optional[List[Dict]],
        day: int,
        travel_style: str = 'standard'
    ) -> List[Dict[str, Any]]:
        """
        Phân bổ hoạt động trong ngày
        
        Đảm bảo mỗi ngày có hoạt động khác nhau và thú vị nhất
        """
        if not activities:
            return []
        
        # Đảm bảo mỗi ngày có hoạt động khác nhau bằng cách rotate
        # Sử dụng day để tính offset và chọn activities khác nhau
        num_activities = min(len(activities), 3)  # Tối đa 3 hoạt động/ngày
        start_idx = ((day - 1) * 2) % len(activities)  # Offset để mỗi ngày khác nhau
        
        selected_activities = []
        for i in range(num_activities):
            idx = (start_idx + i) % len(activities)
            selected_activities.append(activities[idx])
        
        # Phân bổ theo khung giờ
        distributed = []
        slots = ['morning', 'afternoon', 'evening']
        
        for i, slot in enumerate(slots):
            if i < len(selected_activities):
                activity = selected_activities[i]
                # Thêm thông tin travel_style vào activity
                activity_with_style = activity.copy()
                activity_with_style['recommended_for'] = travel_style
                
                distributed.append({
                    'time_slot': slot,
                    'time': self.TIME_SLOTS[slot]['label'],
                    'activity': activity_with_style,
                    'description': self._get_activity_description(activity, slot, travel_style)
                })
        
        return distributed
    
    def _get_activity_description(self, activity: Dict, time_slot: str, travel_style: str) -> str:
        """Tạo mô tả hoạt động phù hợp với time slot và travel style - sử dụng AI"""
        llm = get_llm()
        activity_name = activity.get('name', 'Hoạt động')
        activity_desc = activity.get('description', '')
        
        if llm:
            try:
                time_labels = {
                    'morning': 'buổi sáng (8h-12h)',
                    'afternoon': 'buổi chiều (12h-17h)',
                    'evening': 'buổi tối (17h-21h)'
                }
                
                prompt = f"""Bạn là hướng dẫn viên du lịch chuyên nghiệp. Hãy viết một câu mô tả ngắn gọn, thú vị và hấp dẫn về hoạt động "{activity_name}" vào {time_labels.get(time_slot, 'thời gian này')}.
Phong cách du lịch: {travel_style}
Mô tả hiện tại: {activity_desc[:200] if activity_desc else 'Địa điểm tham quan'}

Chỉ trả về 1 câu mô tả ngắn gọn bằng tiếng Việt, không giải thích thêm."""
                
                response = llm.invoke(prompt)
                desc = response.content if hasattr(response, 'content') else str(response)
                return desc.strip()
            except Exception as e:
                logger.warning(f"LLM activity description failed: {e}, using fallback")
        
        # Fallback descriptions
        descriptions = {
            'morning': f"Bắt đầu ngày mới với {activity_name.lower()}",
            'afternoon': f"Tiếp tục khám phá với {activity_name.lower()}",
            'evening': f"Kết thúc ngày với {activity_name.lower()}"
        }
        
        base_desc = descriptions.get(time_slot, f"Tham quan {activity_name.lower()}")
        
        style_prefix = {
            'budget': 'Tiết kiệm',
            'standard': 'Thú vị',
            'luxury': 'Đặc biệt'
        }
        
        return f"{style_prefix.get(travel_style, '')} - {base_desc}"
    
    def _generate_tips(self, destination: str, day: int, travel_style: str = 'standard') -> List[str]:
        """Tạo mẹo du lịch phù hợp với travel style - sử dụng AI"""
        llm = get_llm()
        
        if llm:
            try:
                prompt = f"""Bạn là chuyên gia du lịch Việt Nam. Hãy đưa ra 5 mẹo du lịch hữu ích và thực tế cho ngày {day} tại {destination}.
Phong cách du lịch: {travel_style} (budget/standard/luxury)
Mỗi mẹo là một câu ngắn gọn, thực tế, dễ thực hiện.
Trả về dạng list, mỗi dòng một mẹo, không đánh số."""
                
                response = llm.invoke(prompt)
                tips_text = response.content if hasattr(response, 'content') else str(response)
                tips = [tip.strip() for tip in tips_text.split('\n') if tip.strip() and not tip.strip().startswith('#')]
                if tips:
                    return tips[:5]
            except Exception as e:
                logger.warning(f"LLM tips generation failed: {e}, using fallback")
        
        # Fallback tips
        tips = [
            f'Mang theo nước uống và kem chống nắng khi tham quan {destination}',
            'Kiểm tra thời tiết trước khi ra ngoài',
            'Giữ giấy tờ tùy thân và tiền mặt an toàn'
        ]
        
        if day == 1:
            tips.append('Ngày đầu nên tham quan nhẹ nhàng để làm quen với địa điểm')
        
        # Thêm tips theo travel style
        style_tips = {
            'budget': [
                'Tìm các quán ăn địa phương để tiết kiệm chi phí',
                'Sử dụng phương tiện công cộng để di chuyển',
                'Mua vé combo để được giảm giá'
            ],
            'standard': [
                'Đặt bàn trước tại nhà hàng nổi tiếng',
                'Tham gia tour để tìm hiểu văn hóa địa phương',
                'Thử các món ăn đặc sản địa phương'
            ],
            'luxury': [
                'Đặt dịch vụ VIP để có trải nghiệm tốt nhất',
                'Thưởng thức ẩm thực cao cấp tại nhà hàng Michelin',
                'Sử dụng dịch vụ concierge của khách sạn'
            ]
        }
        
        tips.extend(style_tips.get(travel_style, []))
        return tips[:5]  # Giới hạn 5 tips
    
    def create_full_itinerary(
        self,
        start_date: str,
        days: int,
        destination: str,
        hotels: List[Dict] = None,
        restaurants: List[Dict] = None,
        activities: List[Dict] = None,
        travel_style: str = 'standard'
    ) -> Dict[str, Any]:
        """
        Tạo lịch trình đầy đủ cho toàn bộ chuyến đi
        
        Args:
            start_date: Ngày bắt đầu (YYYY-MM-DD)
            days: Số ngày
            destination: Điểm đến
            hotels: Danh sách khách sạn
            restaurants: Danh sách nhà hàng
            activities: Danh sách hoạt động
            
        Returns:
            Dict với lịch trình đầy đủ
        """
        start = datetime.strptime(start_date, '%Y-%m-%d')
        itinerary = []
        
        for day in range(1, days + 1):
            date = (start + timedelta(days=day - 1)).strftime('%Y-%m-%d')
            daily_schedule = self.create_daily_schedule(
                day, date, destination, hotels, restaurants, activities, travel_style
            )
            itinerary.append(daily_schedule)
        
        return {
            'destination': destination,
            'start_date': start_date,
            'end_date': (start + timedelta(days=days - 1)).strftime('%Y-%m-%d'),
            'total_days': days,
            'itinerary': itinerary
        }


# Singleton instance
_planning_tools = None

def get_planning_tools() -> PlanningTools:
    """Get singleton PlanningTools instance"""
    global _planning_tools
    if _planning_tools is None:
        _planning_tools = PlanningTools()
    return _planning_tools

