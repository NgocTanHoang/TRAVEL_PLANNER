"""
Travel Styles - Phong cách du lịch mở rộng
==========================================
Định nghĩa các phong cách du lịch với scoring profiles và constraints
"""
from enum import Enum
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass


class TravelStyle(str, Enum):
    """Enum cho các phong cách du lịch"""
    # Core styles
    BUDGET = 'budget'
    STANDARD = 'standard'
    LUXURY = 'luxury'
    
    # Extended styles
    ADVENTURE = 'adventure'
    CULTURAL = 'cultural'
    GASTRONOMY = 'gastronomy'
    ECO = 'eco'
    WELLNESS = 'wellness'
    FAMILY = 'family'
    ROMANTIC = 'romantic'
    SLOW = 'slow'
    DIGITAL_NOMAD = 'digital_nomad'
    SHOP_LEISURE = 'shop_leisure'
    PHOTOGRAPHY = 'photography'
    RELIGIOUS = 'religious'
    FESTIVAL = 'festival'
    EXTREME = 'extreme'


@dataclass
class StyleProfile:
    """Profile cho một phong cách du lịch"""
    name: str
    description: str
    target_audience: str
    examples: List[str]
    
    # Scoring weights (tổng = 1.0)
    weights: Dict[str, float]  # rating, distance, price, cuisine, difficulty, etc.
    
    # Constraints
    preferred_radius_km: float
    preferred_price_range: Tuple[int, int]  # (min, max) price_level
    max_daily_travel_time_min: int
    preferred_activity_types: List[str]
    
    # Requirements
    requires_internet: bool = False
    requires_guide: bool = False
    requires_reservation: bool = False
    requires_accessibility: bool = False
    sustainability_preference: float = 0.0  # 0.0-1.0
    
    # Meal preferences
    meal_importance: float = 0.5  # 0.0-1.0, importance of meals
    preferred_meal_types: List[str] = None
    
    # Special considerations
    special_notes: str = ""


# Style Profiles với scoring weights và constraints
STYLE_PROFILES: Dict[str, StyleProfile] = {
    TravelStyle.BUDGET: StyleProfile(
        name="Tiết kiệm",
        description="Du lịch với ngân sách hạn chế, ưu tiên giá cả phải chăng",
        target_audience="Người có ngân sách hạn chế, sinh viên, backpackers",
        examples=["Homestay, xe buýt công cộng, quán ăn địa phương"],
        weights={
            'rating': 0.25,
            'distance': 0.20,
            'price': 0.40,  # Ưu tiên giá thấp
            'cuisine': 0.10,
            'difficulty': 0.05
        },
        preferred_radius_km=10.0,
        preferred_price_range=(1, 2),
        max_daily_travel_time_min=120,
        preferred_activity_types=['free', 'low_cost', 'local'],
        meal_importance=0.6,
        preferred_meal_types=['local', 'street_food']
    ),
    
    TravelStyle.STANDARD: StyleProfile(
        name="Tiêu chuẩn",
        description="Du lịch cân bằng giữa chất lượng và giá cả",
        target_audience="Du khách phổ thông",
        examples=["Khách sạn 3-4 sao, nhà hàng trung bình"],
        weights={
            'rating': 0.30,
            'distance': 0.25,
            'price': 0.25,
            'cuisine': 0.15,
            'difficulty': 0.05
        },
        preferred_radius_km=15.0,
        preferred_price_range=(2, 3),
        max_daily_travel_time_min=180,
        preferred_activity_types=['standard', 'popular'],
        meal_importance=0.7
    ),
    
    TravelStyle.LUXURY: StyleProfile(
        name="Sang trọng",
        description="Du lịch cao cấp với dịch vụ và tiện nghi tốt nhất",
        target_audience="Người có ngân sách cao, muốn trải nghiệm đặc biệt",
        examples=["Resort 5 sao, nhà hàng Michelin, dịch vụ VIP"],
        weights={
            'rating': 0.40,
            'distance': 0.15,
            'price': 0.10,  # Không quan trọng giá
            'cuisine': 0.25,
            'difficulty': 0.10
        },
        preferred_radius_km=20.0,
        preferred_price_range=(3, 4),
        max_daily_travel_time_min=240,
        preferred_activity_types=['premium', 'exclusive', 'private'],
        requires_reservation=True,
        meal_importance=0.9,
        preferred_meal_types=['fine_dining', 'gourmet']
    ),
    
    TravelStyle.ADVENTURE: StyleProfile(
        name="Phiêu lưu",
        description="Chuyến đi có yếu tố mạo hiểm, hoạt động ngoài trời",
        target_audience="Người trẻ, ưa vận động, thích trải nghiệm cảm giác mạnh",
        examples=["Trek Fansipan, kayaking Hạ Long, đạp xe xuyên ĐBSCL"],
        weights={
            'rating': 0.20,
            'distance': 0.20,
            'price': 0.15,
            'cuisine': 0.10,
            'difficulty': 0.35  # Ưu tiên độ khó
        },
        preferred_radius_km=30.0,
        preferred_price_range=(1, 3),
        max_daily_travel_time_min=300,
        preferred_activity_types=['outdoor', 'extreme', 'sports', 'trekking'],
        requires_guide=True,
        meal_importance=0.5,
        preferred_meal_types=['local', 'camping']
    ),
    
    TravelStyle.CULTURAL: StyleProfile(
        name="Văn hóa & Lịch sử",
        description="Trọng tâm là di tích, bảo tàng, trải nghiệm văn hoá bản địa",
        target_audience="Người có thiên hướng học thuật, gia đình trung niên",
        examples=["Hội An, Huế, Thăng Long, tham gia lễ truyền thống"],
        weights={
            'rating': 0.30,
            'distance': 0.20,
            'price': 0.20,
            'cuisine': 0.15,
            'difficulty': 0.15  # Ưu tiên nội dung văn hóa
        },
        preferred_radius_km=20.0,
        preferred_price_range=(1, 3),
        max_daily_travel_time_min=150,  # Tempo chậm
        preferred_activity_types=['museum', 'temple', 'heritage', 'cultural'],
        requires_guide=True,
        meal_importance=0.6,
        preferred_meal_types=['traditional', 'local']
    ),
    
    TravelStyle.GASTRONOMY: StyleProfile(
        name="Ẩm thực",
        description="Lấy ẩm thực làm trung tâm - food tour, cooking class, chợ địa phương",
        target_audience="Người yêu ẩm thực, bloggers, food influencer",
        examples=["Food tour Hà Nội, chợ đêm Đà Nẵng, lớp làm phở"],
        weights={
            'rating': 0.40,
            'distance': 0.20,
            'price': 0.15,
            'cuisine': 0.35,  # Ưu tiên cao cho ẩm thực
            'difficulty': 0.05
        },
        preferred_radius_km=10.0,
        preferred_price_range=(2, 4),
        max_daily_travel_time_min=180,
        preferred_activity_types=['food_tour', 'cooking_class', 'market', 'restaurant'],
        requires_reservation=True,
        meal_importance=1.0,  # Rất quan trọng
        preferred_meal_types=['local', 'street_food', 'fine_dining', 'gourmet']
    ),
    
    TravelStyle.ECO: StyleProfile(
        name="Sinh thái & Bền vững",
        description="Ưu tiên thiên nhiên, bảo tồn, homestay thân thiện môi trường",
        target_audience="Người quan tâm môi trường, du lịch cộng đồng",
        examples=["Cồn Phụng homestay bền vững, rừng tràm Trà Sư"],
        weights={
            'rating': 0.25,
            'distance': 0.25,
            'price': 0.20,
            'cuisine': 0.10,
            'difficulty': 0.20,
            'sustainability': 0.30  # Ưu tiên bền vững
        },
        preferred_radius_km=25.0,
        preferred_price_range=(1, 3),
        max_daily_travel_time_min=180,
        preferred_activity_types=['nature', 'eco', 'sustainable', 'community'],
        sustainability_preference=0.9,
        meal_importance=0.6,
        preferred_meal_types=['local', 'organic', 'vegetarian']
    ),
    
    TravelStyle.WELLNESS: StyleProfile(
        name="Chăm sóc sức khỏe & Wellness",
        description="Spa, thiền, retreat, khoá detox, yoga",
        target_audience="Người cần thư giãn, hồi phục, trung niên, giới bận rộn",
        examples=["Retreat ở Đà Lạt, spa biển Nha Trang"],
        weights={
            'rating': 0.35,
            'distance': 0.15,
            'price': 0.20,
            'cuisine': 0.20,
            'difficulty': 0.10
        },
        preferred_radius_km=15.0,
        preferred_price_range=(2, 4),
        max_daily_travel_time_min=120,  # Lịch nhẹ nhàng
        preferred_activity_types=['spa', 'yoga', 'meditation', 'retreat', 'wellness'],
        meal_importance=0.7,
        preferred_meal_types=['healthy', 'vegetarian', 'organic']
    ),
    
    TravelStyle.FAMILY: StyleProfile(
        name="Gia đình",
        description="Lịch thân thiện trẻ em; hoạt động an toàn, thời gian nghỉ xen kẽ",
        target_audience="Gia đình có con nhỏ",
        examples=["VinWonders, Safari, bãi biển có bờ cát nông"],
        weights={
            'rating': 0.30,
            'distance': 0.30,  # Ưu tiên gần
            'price': 0.25,
            'cuisine': 0.10,
            'difficulty': 0.05,
            'accessibility': 0.20  # Ưu tiên an toàn, dễ tiếp cận
        },
        preferred_radius_km=10.0,
        preferred_price_range=(1, 3),
        max_daily_travel_time_min=120,  # Di chuyển ngắn
        preferred_activity_types=['family', 'kid_friendly', 'safe', 'educational'],
        requires_accessibility=True,
        meal_importance=0.7,
        preferred_meal_types=['family_friendly', 'kid_menu']
    ),
    
    TravelStyle.ROMANTIC: StyleProfile(
        name="Lãng mạn",
        description="Trải nghiệm riêng tư, không gian lãng mạn, dinner under stars",
        target_audience="Cặp đôi, vợ chồng mới cưới",
        examples=["Resort Hội An, bungalow Phú Quốc"],
        weights={
            'rating': 0.35,
            'distance': 0.20,
            'price': 0.15,
            'cuisine': 0.30,  # Ưu tiên nhà hàng lãng mạn
            'difficulty': 0.10
        },
        preferred_radius_km=15.0,
        preferred_price_range=(3, 4),
        max_daily_travel_time_min=180,
        preferred_activity_types=['romantic', 'private', 'scenic', 'sunset'],
        requires_reservation=True,
        meal_importance=0.9,
        preferred_meal_types=['fine_dining', 'romantic', 'sunset_dinner']
    ),
    
    TravelStyle.SLOW: StyleProfile(
        name="Slow Travel",
        description="Ở lâu một nơi, cảm nhận chậm rãi, ít di chuyển",
        target_audience="Muốn thư giãn sâu, học tiếng, làm việc từ xa",
        examples=["1 tuần ở Huế, sống như người bản địa"],
        weights={
            'rating': 0.30,
            'distance': 0.15,  # Ít di chuyển
            'price': 0.25,
            'cuisine': 0.20,
            'difficulty': 0.10
        },
        preferred_radius_km=5.0,  # Rất gần
        preferred_price_range=(1, 3),
        max_daily_travel_time_min=60,  # Rất ít di chuyển
        preferred_activity_types=['local', 'cultural', 'relaxing'],
        meal_importance=0.7,
        preferred_meal_types=['local', 'traditional']
    ),
    
    TravelStyle.DIGITAL_NOMAD: StyleProfile(
        name="Digital Nomad / Workation",
        description="Kết hợp làm việc và du lịch; ưu tiên coworking, Internet ổn định",
        target_audience="Freelancer, remote worker",
        examples=["Chỗ ở có workspace ở Đà Nẵng, HCM"],
        weights={
            'rating': 0.25,
            'distance': 0.20,
            'price': 0.25,
            'cuisine': 0.15,
            'difficulty': 0.15
        },
        preferred_radius_km=10.0,
        preferred_price_range=(1, 3),
        max_daily_travel_time_min=90,  # Ít di chuyển để làm việc
        preferred_activity_types=['coworking', 'cafe', 'quiet'],
        requires_internet=True,
        meal_importance=0.6,
        preferred_meal_types=['cafe', 'quick', 'healthy']
    ),
    
    TravelStyle.SHOP_LEISURE: StyleProfile(
        name="Shopping & Giải trí",
        description="Ưu tiên mua sắm, outlet, nightlife, show",
        target_audience="Người thích mua sắm, nightlife",
        examples=["Phố đi bộ Nguyễn Huệ, chợ Bến Thành, trung tâm thương mại"],
        weights={
            'rating': 0.30,
            'distance': 0.25,
            'price': 0.25,
            'cuisine': 0.15,
            'difficulty': 0.05
        },
        preferred_radius_km=10.0,
        preferred_price_range=(1, 4),
        max_daily_travel_time_min=240,
        preferred_activity_types=['shopping', 'nightlife', 'entertainment', 'show'],
        meal_importance=0.7,
        preferred_meal_types=['casual', 'nightlife', 'quick']
    ),
    
    TravelStyle.PHOTOGRAPHY: StyleProfile(
        name="Photography & Cảnh quan",
        description="Lộ trình tối ưu ánh sáng, viewpoint, golden hour",
        target_audience="Photographer, content creator",
        examples=["Bãi Đá Ông Địa lúc bình minh, đồi chè Mộc Châu"],
        weights={
            'rating': 0.25,
            'distance': 0.30,  # Ưu tiên viewpoint
            'price': 0.15,
            'cuisine': 0.10,
            'difficulty': 0.20
        },
        preferred_radius_km=30.0,
        preferred_price_range=(1, 3),
        max_daily_travel_time_min=300,
        preferred_activity_types=['scenic', 'viewpoint', 'sunrise', 'sunset', 'landscape'],
        meal_importance=0.4,
        preferred_meal_types=['quick', 'local']
    ),
    
    TravelStyle.RELIGIOUS: StyleProfile(
        name="Tâm linh",
        description="Tham quan đền chùa, hành hương, lễ nghi",
        target_audience="Người theo tôn giáo, tín ngưỡng",
        examples=["Chùa, đền, lễ hội tôn giáo"],
        weights={
            'rating': 0.30,
            'distance': 0.20,
            'price': 0.20,
            'cuisine': 0.10,
            'difficulty': 0.20
        },
        preferred_radius_km=25.0,
        preferred_price_range=(1, 2),
        max_daily_travel_time_min=180,
        preferred_activity_types=['temple', 'pagoda', 'religious', 'pilgrimage'],
        requires_guide=True,
        meal_importance=0.5,
        preferred_meal_types=['vegetarian', 'traditional']
    ),
    
    TravelStyle.FESTIVAL: StyleProfile(
        name="Festival & Sự kiện",
        description="Đi vì sự kiện (lễ hội, hội nghị, concert)",
        target_audience="Người tham gia sự kiện, khách du lịch theo mùa",
        examples=["Lễ hội, concert, hội nghị"],
        weights={
            'rating': 0.30,
            'distance': 0.25,
            'price': 0.25,
            'cuisine': 0.15,
            'difficulty': 0.05
        },
        preferred_radius_km=15.0,
        preferred_price_range=(1, 4),
        max_daily_travel_time_min=180,
        preferred_activity_types=['festival', 'event', 'concert', 'conference'],
        meal_importance=0.6,
        preferred_meal_types=['quick', 'local', 'festival_food']
    ),
    
    TravelStyle.EXTREME: StyleProfile(
        name="Extreme / Expedition",
        description="Đi vào vùng hẻo lánh, nhiều chuẩn bị, guide chuyên nghiệp",
        target_audience="Expedition teams, hardcore adventurers",
        examples=["Thám hiểm vùng sâu, leo núi khó, cắm trại hoang dã"],
        weights={
            'rating': 0.20,
            'distance': 0.15,
            'price': 0.15,
            'cuisine': 0.10,
            'difficulty': 0.40  # Rất quan trọng
        },
        preferred_radius_km=50.0,
        preferred_price_range=(2, 4),
        max_daily_travel_time_min=480,
        preferred_activity_types=['extreme', 'expedition', 'wilderness', 'challenging'],
        requires_guide=True,
        meal_importance=0.4,
        preferred_meal_types=['camping', 'survival', 'high_energy']
    )
}


def get_style_profile(style: str) -> Optional[StyleProfile]:
    """
    Lấy profile cho một phong cách du lịch
    
    Args:
        style: Tên phong cách (string)
        
    Returns:
        StyleProfile hoặc None
    """
    # Normalize style name
    style_lower = style.lower().strip()
    
    # Try direct match
    if style_lower in STYLE_PROFILES:
        return STYLE_PROFILES[style_lower]
    
    # Try enum match
    try:
        style_enum = TravelStyle(style_lower)
        return STYLE_PROFILES.get(style_enum.value)
    except ValueError:
        pass
    
    # Try partial match
    for key, profile in STYLE_PROFILES.items():
        if style_lower in key.lower() or key.lower() in style_lower:
            return profile
    
    # Default to standard
    return STYLE_PROFILES.get(TravelStyle.STANDARD)


def get_combined_profile(styles: List[str]) -> StyleProfile:
    """
    Kết hợp nhiều phong cách thành một profile
    
    Args:
        styles: List các phong cách
        
    Returns:
        Combined StyleProfile
    """
    if not styles:
        return STYLE_PROFILES[TravelStyle.STANDARD]
    
    if len(styles) == 1:
        return get_style_profile(styles[0]) or STYLE_PROFILES[TravelStyle.STANDARD]
    
    # Combine multiple styles
    profiles = [get_style_profile(s) for s in styles if get_style_profile(s)]
    if not profiles:
        return STYLE_PROFILES[TravelStyle.STANDARD]
    
    # Average weights
    combined_weights = {}
    for key in profiles[0].weights.keys():
        combined_weights[key] = sum(p.weights.get(key, 0) for p in profiles) / len(profiles)
    
    # Use max for constraints (most restrictive)
    max_radius = max(p.preferred_radius_km for p in profiles)
    max_travel_time = max(p.max_daily_travel_time_min for p in profiles)
    min_price = min(p.preferred_price_range[0] for p in profiles)
    max_price = max(p.preferred_price_range[1] for p in profiles)
    
    # Combine requirements (OR logic)
    requires_internet = any(p.requires_internet for p in profiles)
    requires_guide = any(p.requires_guide for p in profiles)
    requires_reservation = any(p.requires_reservation for p in profiles)
    requires_accessibility = any(p.requires_accessibility for p in profiles)
    
    # Average sustainability
    sustainability = sum(p.sustainability_preference for p in profiles) / len(profiles)
    meal_importance = sum(p.meal_importance for p in profiles) / len(profiles)
    
    # Combine activity types
    all_activity_types = []
    for p in profiles:
        all_activity_types.extend(p.preferred_activity_types)
    preferred_activity_types = list(set(all_activity_types))
    
    # Combine meal types
    all_meal_types = []
    for p in profiles:
        if p.preferred_meal_types:
            all_meal_types.extend(p.preferred_meal_types)
    preferred_meal_types = list(set(all_meal_types)) if all_meal_types else None
    
    return StyleProfile(
        name=f"Combined: {', '.join([p.name for p in profiles])}",
        description=f"Kết hợp {len(profiles)} phong cách",
        target_audience="Multi-style travelers",
        examples=[],
        weights=combined_weights,
        preferred_radius_km=max_radius,
        preferred_price_range=(min_price, max_price),
        max_daily_travel_time_min=max_travel_time,
        preferred_activity_types=preferred_activity_types,
        requires_internet=requires_internet,
        requires_guide=requires_guide,
        requires_reservation=requires_reservation,
        requires_accessibility=requires_accessibility,
        sustainability_preference=sustainability,
        meal_importance=meal_importance,
        preferred_meal_types=preferred_meal_types
    )


def get_all_styles() -> List[Dict[str, Any]]:
    """
    Lấy danh sách tất cả phong cách với metadata
    
    Returns:
        List các dict với thông tin phong cách
    """
    return [
        {
            'value': key,
            'name': profile.name,
            'description': profile.description,
            'target_audience': profile.target_audience,
            'examples': profile.examples
        }
        for key, profile in STYLE_PROFILES.items()
    ]


# Preset combinations (common style combinations)
STYLE_PRESETS = {
    'romantic_luxury': [TravelStyle.ROMANTIC, TravelStyle.LUXURY],
    'family_budget': [TravelStyle.FAMILY, TravelStyle.BUDGET],
    'adventure_eco': [TravelStyle.ADVENTURE, TravelStyle.ECO],
    'cultural_slow': [TravelStyle.CULTURAL, TravelStyle.SLOW],
    'gastronomy_cultural': [TravelStyle.GASTRONOMY, TravelStyle.CULTURAL],
    'wellness_romantic': [TravelStyle.WELLNESS, TravelStyle.ROMANTIC],
    'photography_adventure': [TravelStyle.PHOTOGRAPHY, TravelStyle.ADVENTURE]
}


def get_preset_profile(preset_name: str) -> Optional[StyleProfile]:
    """
    Lấy profile cho một preset
    
    Args:
        preset_name: Tên preset
        
    Returns:
        StyleProfile hoặc None
    """
    if preset_name in STYLE_PRESETS:
        styles = [s.value for s in STYLE_PRESETS[preset_name]]
        return get_combined_profile(styles)
    return None

