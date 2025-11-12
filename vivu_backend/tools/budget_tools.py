"""
Budget Tools - Công cụ quản lý ngân sách
=========================================
- Phân tích ngân sách
- Tính tổng chi phí
- Đề xuất ngân sách phù hợp
- Phân bổ ngân sách theo hạng mục
- Hỗ trợ 14+ phong cách du lịch với cost mapping riêng
"""
import logging
from typing import Dict, Any, Optional, List, Union

logger = logging.getLogger(__name__)

# Import travel styles
try:
    from tools.travel_styles import get_style_profile, get_combined_profile, TravelStyle
    TRAVEL_STYLES_AVAILABLE = True
except ImportError:
    TRAVEL_STYLES_AVAILABLE = False
    logger.warning("Travel styles module not available")


class BudgetTools:
    """Công cụ ngân sách cho Budget Agent"""
    
    # Tỷ lệ phân bổ ngân sách mặc định (%)
    DEFAULT_BUDGET_ALLOCATION = {
        'transport': 30,       # Vận chuyển (bao gồm vé máy bay)
        'accommodation': 35,   # Lưu trú
        'dining': 20,          # Ăn uống
        'activities': 10,      # Hoạt động/giải trí
        'shopping': 3,         # Mua sắm
        'misc': 2              # Chi phí khác
    }
    
    # Travel style multipliers (accommodation & dining)
    TRAVEL_STYLE_MULTIPLIERS = {
        # Core styles
        'budget': 0.7,      # Tiết kiệm: giảm 30%
        'standard': 1.0,   # Trung bình: giữ nguyên
        'luxury': 1.8,     # Cao cấp: tăng 80%
        
        # Extended styles
        'adventure': 0.9,      # Gần standard, nhưng ưu tiên equipment
        'cultural': 0.85,      # Gần standard, ưu tiên guide
        'gastronomy': 1.3,     # Tăng dining cost
        'eco': 0.8,            # Homestay, sustainable
        'wellness': 1.5,       # Spa, retreat cao cấp
        'family': 1.1,         # Family rooms, activities
        'romantic': 1.6,       # Resort, fine dining
        'slow': 0.75,          # Long stay discount
        'digital_nomad': 0.9,  # Workspace, cafe
        'shop_leisure': 1.2,   # Shopping, nightlife
        'photography': 1.0,    # Standard
        'religious': 0.7,      # Budget-friendly
        'festival': 1.1,       # Event pricing
        'extreme': 1.2         # Equipment, guide
    }
    
    # Chi phí ăn uống ước tính (VNĐ/người/ngày)
    DINING_COST_PER_DAY = {
        # Core styles
        'budget': 200000,      # 200k/người/ngày
        'standard': 400000,    # 400k/người/ngày
        'luxury': 800000,      # 800k/người/ngày
        
        # Extended styles
        'adventure': 300000,   # Camping, local food
        'cultural': 350000,    # Traditional, local
        'gastronomy': 600000, # Food tours, fine dining
        'eco': 250000,        # Organic, local
        'wellness': 500000,   # Healthy, organic
        'family': 350000,     # Family-friendly
        'romantic': 700000,    # Fine dining, romantic
        'slow': 300000,       # Local, affordable
        'digital_nomad': 300000, # Cafe, quick meals
        'shop_leisure': 450000, # Casual, nightlife
        'photography': 350000,  # Quick meals
        'religious': 200000,    # Vegetarian, simple
        'festival': 400000,      # Festival food
        'extreme': 300000        # High energy, camping
    }
    
    # Budget allocation per style (%)
    STYLE_BUDGET_ALLOCATION = {
        'budget': {
            'transport': 35, 'accommodation': 30, 'dining': 20,
            'activities': 10, 'shopping': 3, 'misc': 2
        },
        'standard': {
            'transport': 30, 'accommodation': 35, 'dining': 20,
            'activities': 10, 'shopping': 3, 'misc': 2
        },
        'luxury': {
            'transport': 25, 'accommodation': 40, 'dining': 25,
            'activities': 7, 'shopping': 2, 'misc': 1
        },
        'gastronomy': {
            'transport': 25, 'accommodation': 30, 'dining': 35,  # Higher dining
            'activities': 7, 'shopping': 2, 'misc': 1
        },
        'wellness': {
            'transport': 20, 'accommodation': 45, 'dining': 25,  # Higher accommodation
            'activities': 7, 'shopping': 2, 'misc': 1
        },
        'romantic': {
            'transport': 25, 'accommodation': 40, 'dining': 28,
            'activities': 5, 'shopping': 1, 'misc': 1
        },
        'adventure': {
            'transport': 30, 'accommodation': 25, 'dining': 20,
            'activities': 20, 'shopping': 3, 'misc': 2  # Higher activities
        },
        'family': {
            'transport': 30, 'accommodation': 35, 'dining': 22,
            'activities': 10, 'shopping': 2, 'misc': 1
        },
        'shop_leisure': {
            'transport': 25, 'accommodation': 30, 'dining': 20,
            'activities': 5, 'shopping': 18, 'misc': 2  # Higher shopping
        }
    }
    
    def _get_style_multiplier(self, travel_style: Union[str, List[str]]) -> float:
        """
        Lấy multiplier cho travel style (có thể là string hoặc list)
        
        Args:
            travel_style: String hoặc list các phong cách
            
        Returns:
            Multiplier (float)
        """
        # Handle string that might be comma-separated
        if isinstance(travel_style, str) and ',' in travel_style:
            travel_style = [s.strip() for s in travel_style.split(',')]
        
        if isinstance(travel_style, list):
            if len(travel_style) == 1:
                return self.TRAVEL_STYLE_MULTIPLIERS.get(travel_style[0], 1.0)
            else:
                # For combined styles, use weighted average or specific combination rules
                # Special combinations
                style_set = set(s.lower() for s in travel_style)
                if 'romantic' in style_set and 'wellness' in style_set:
                    # Romantic + Wellness: premium combination (1.6 * 1.15 = 1.84)
                    return 1.84
                elif 'romantic' in style_set and 'luxury' in style_set:
                    # Romantic + Luxury: very premium (1.6 * 1.2 = 1.92)
                    return 1.92
                elif 'wellness' in style_set and 'luxury' in style_set:
                    # Wellness + Luxury: premium (1.5 * 1.2 = 1.8)
                    return 1.8
                else:
                    # Average multipliers for other combinations
                    multipliers = [self.TRAVEL_STYLE_MULTIPLIERS.get(s, 1.0) for s in travel_style]
                    return sum(multipliers) / len(multipliers)
        else:
            return self.TRAVEL_STYLE_MULTIPLIERS.get(travel_style, 1.0)
    
    def _get_dining_cost(self, travel_style: Union[str, List[str]]) -> float:
        """
        Lấy chi phí ăn uống cho travel style
        
        Args:
            travel_style: String hoặc list các phong cách
            
        Returns:
            Chi phí ăn uống (VNĐ/người/ngày)
        """
        # Handle string that might be comma-separated
        if isinstance(travel_style, str) and ',' in travel_style:
            travel_style = [s.strip() for s in travel_style.split(',')]
        
        if isinstance(travel_style, list):
            if len(travel_style) == 1:
                return self.DINING_COST_PER_DAY.get(travel_style[0], 400000)
            else:
                # For combined styles, use weighted average or specific combination rules
                style_set = set(s.lower() for s in travel_style)
                if 'romantic' in style_set and 'wellness' in style_set:
                    # Romantic + Wellness: premium dining (average of 700k + 500k = 600k, but premium = 650k)
                    return 650000
                elif 'romantic' in style_set and 'gastronomy' in style_set:
                    # Romantic + Gastronomy: very premium (700k + 600k = 650k, but very premium = 750k)
                    return 750000
                elif 'wellness' in style_set and 'gastronomy' in style_set:
                    # Wellness + Gastronomy: premium healthy dining (500k + 600k = 550k)
                    return 550000
                else:
                    # Average dining cost for other combinations
                    costs = [self.DINING_COST_PER_DAY.get(s, 400000) for s in travel_style]
                    return sum(costs) / len(costs)
        else:
            return self.DINING_COST_PER_DAY.get(travel_style, 400000)
    
    def calculate_total_budget(
        self,
        transport_cost: float,
        accommodation_cost: float,
        dining_cost: Optional[float] = None,
        activities_cost: Optional[float] = None,
        days: int = 1,
        travelers: int = 1,
        travel_style: Union[str, List[str]] = 'standard'
    ) -> Dict[str, Any]:
        """
        Tính tổng ngân sách với style-aware cost calculation
        
        Args:
            transport_cost: Chi phí vận chuyển (VNĐ)
            accommodation_cost: Chi phí lưu trú (VNĐ)
            dining_cost: Chi phí ăn uống (VNĐ, None để tự tính)
            activities_cost: Chi phí hoạt động (VNĐ, None để tự tính)
            days: Số ngày
            travelers: Số người
            travel_style: String hoặc list các phong cách ('budget', 'gastronomy', ['romantic', 'luxury'], ...)
            
        Returns:
            Dict với breakdown chi tiết
        """
        multiplier = self._get_style_multiplier(travel_style)
        
        # Đảm bảo tất cả chi phí không phải None
        transport_cost = transport_cost or 0
        accommodation_cost = accommodation_cost or 0
        
        # Tính chi phí ăn uống nếu chưa có
        if dining_cost is None:
            base_dining = self._get_dining_cost(travel_style)
            dining_cost = base_dining * days * travelers
        
        # Tính chi phí hoạt động nếu chưa có
        # Style-specific activity cost estimation
        if activities_cost is None:
            # Get style profile for activity cost estimation
            if TRAVEL_STYLES_AVAILABLE:
                if isinstance(travel_style, list):
                    if len(travel_style) == 1:
                        style_profile = get_style_profile(travel_style[0])
                    else:
                        style_profile = get_combined_profile(travel_style)
                else:
                    style_profile = get_style_profile(travel_style)
                
                if style_profile:
                    # Estimate based on preferred activity types
                    activity_types = [t.lower() for t in style_profile.preferred_activity_types]
                    if any('extreme' in t or 'expedition' in t for t in activity_types):
                        activities_cost = (transport_cost + accommodation_cost) * 0.25  # Higher for extreme
                    elif any('adventure' in t for t in activity_types):
                        activities_cost = (transport_cost + accommodation_cost) * 0.20  # Higher for adventure
                    elif any('wellness' in t or 'spa' in t for t in activity_types):
                        activities_cost = (transport_cost + accommodation_cost) * 0.15  # Higher for wellness
                    else:
                        activities_cost = (transport_cost + accommodation_cost) * 0.10  # Standard
                else:
                    activities_cost = (transport_cost + accommodation_cost) * 0.10
            else:
                activities_cost = (transport_cost + accommodation_cost) * 0.10
        
        # Áp dụng multiplier cho accommodation và dining
        accommodation_cost *= multiplier
        dining_cost *= multiplier
        
        # Chi phí khác (5% tổng)
        misc_cost = (transport_cost + accommodation_cost + dining_cost + activities_cost) * 0.05
        
        total_cost = transport_cost + accommodation_cost + dining_cost + activities_cost + misc_cost
        
        return {
            'total_vnd': round(total_cost),
            'breakdown': {
                'transport': round(transport_cost),
                'accommodation': round(accommodation_cost),
                'dining': round(dining_cost),
                'activities': round(activities_cost),
                'misc': round(misc_cost)
            },
            'per_person': round(total_cost / travelers),
            'per_day': round(total_cost / days),
            'travel_style': travel_style,
            'days': days,
            'travelers': travelers
        }
    
    def suggest_budget(
        self,
        destination: str,
        days: int,
        travelers: int,
        travel_style: Union[str, List[str]] = 'standard'
    ) -> Dict[str, Any]:
        """
        Đề xuất ngân sách dựa trên điểm đến và số ngày với style-aware calculation
        
        Args:
            destination: Điểm đến
            days: Số ngày
            travelers: Số người
            travel_style: String hoặc list các phong cách
            
        Returns:
            Dict với ngân sách đề xuất
        """
        # Ước tính chi phí cơ bản (VNĐ/người/ngày) - không hardcode theo thành phố
        # Tính toán động dựa trên loại địa điểm (thành phố lớn, biển, núi, v.v.)
        # Mặc định cho mọi địa điểm
        base_transport = 500000  # Chi phí di chuyển trong thành phố/địa phương
        base_accommodation = 500000  # Chi phí lưu trú trung bình
        base_activities = 200000  # Chi phí hoạt động trung bình
        
        # Điều chỉnh dựa trên loại địa điểm (nếu có thông tin)
        # Có thể mở rộng sau bằng cách query từ database để xác định loại địa điểm
        costs = {
            'transport': base_transport,
            'accommodation': base_accommodation,
            'activities': base_activities
        }
        
        # Tính tổng với style-aware multiplier
        multiplier = self._get_style_multiplier(travel_style)
        
        transport_cost = costs['transport'] * travelers
        accommodation_cost = costs['accommodation'] * days * travelers * multiplier
        activities_cost = costs['activities'] * days * travelers * multiplier
        
        return self.calculate_total_budget(
            transport_cost=transport_cost,
            accommodation_cost=accommodation_cost,
            activities_cost=activities_cost,
            days=days,
            travelers=travelers,
            travel_style=travel_style
        )
    
    def analyze_budget_allocation(
        self,
        total_budget: float,
        breakdown: Dict[str, float]
    ) -> Dict[str, Any]:
        """
        Phân tích phân bổ ngân sách
        
        Args:
            total_budget: Tổng ngân sách (VNĐ)
            breakdown: Breakdown chi phí
            
        Returns:
            Dict với phân tích và đề xuất
        """
        allocation = {}
        for key, value in breakdown.items():
            allocation[key] = round((value / total_budget * 100), 1)
        
        # Đánh giá
        issues = []
        if allocation.get('accommodation', 0) > 50:
            issues.append('Chi phí lưu trú quá cao (>50%)')
        if allocation.get('transport', 0) > 40:
            issues.append('Chi phí vận chuyển quá cao (>40%)')
        if allocation.get('dining', 0) < 10:
            issues.append('Chi phí ăn uống có thể quá thấp (<10%)')
        
        return {
            'allocation_percent': allocation,
            'recommendations': issues,
            'is_balanced': len(issues) == 0
        }


# Singleton instance
_budget_tools = None

def get_budget_tools() -> BudgetTools:
    """Get singleton BudgetTools instance"""
    global _budget_tools
    if _budget_tools is None:
        _budget_tools = BudgetTools()
    return _budget_tools

