"""
Budget Tools - Công cụ quản lý ngân sách
=========================================
- Phân tích ngân sách
- Tính tổng chi phí
- Đề xuất ngân sách phù hợp
- Phân bổ ngân sách theo hạng mục
"""
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


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
    
    # Travel style multipliers
    TRAVEL_STYLE_MULTIPLIERS = {
        'budget': 0.7,      # Tiết kiệm: giảm 30%
        'standard': 1.0,   # Trung bình: giữ nguyên
        'luxury': 1.8      # Cao cấp: tăng 80%
    }
    
    # Chi phí ăn uống ước tính (VNĐ/người/ngày)
    DINING_COST_PER_DAY = {
        'budget': 200000,      # 200k/người/ngày
        'standard': 400000,    # 400k/người/ngày
        'luxury': 800000       # 800k/người/ngày
    }
    
    def calculate_total_budget(
        self,
        transport_cost: float,
        accommodation_cost: float,
        dining_cost: Optional[float] = None,
        activities_cost: Optional[float] = None,
        days: int = 1,
        travelers: int = 1,
        travel_style: str = 'standard'
    ) -> Dict[str, Any]:
        """
        Tính tổng ngân sách
        
        Args:
            transport_cost: Chi phí vận chuyển (VNĐ)
            accommodation_cost: Chi phí lưu trú (VNĐ)
            dining_cost: Chi phí ăn uống (VNĐ, None để tự tính)
            activities_cost: Chi phí hoạt động (VNĐ, None để tự tính)
            days: Số ngày
            travelers: Số người
            travel_style: 'budget', 'standard', 'luxury'
            
        Returns:
            Dict với breakdown chi tiết
        """
        multiplier = self.TRAVEL_STYLE_MULTIPLIERS.get(travel_style, 1.0)
        
        # Đảm bảo tất cả chi phí không phải None
        transport_cost = transport_cost or 0
        accommodation_cost = accommodation_cost or 0
        
        # Tính chi phí ăn uống nếu chưa có
        if dining_cost is None:
            base_dining = self.DINING_COST_PER_DAY.get(travel_style, 400000)
            dining_cost = base_dining * days * travelers
        
        # Tính chi phí hoạt động nếu chưa có (ước tính 10% tổng)
        if activities_cost is None:
            activities_cost = (transport_cost + accommodation_cost) * 0.1
        
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
        travel_style: str = 'standard'
    ) -> Dict[str, Any]:
        """
        Đề xuất ngân sách dựa trên điểm đến và số ngày
        
        Args:
            destination: Điểm đến
            days: Số ngày
            travelers: Số người
            travel_style: 'budget', 'standard', 'luxury'
            
        Returns:
            Dict với ngân sách đề xuất
        """
        # Ước tính chi phí cơ bản (VNĐ/người/ngày) theo destination
        base_costs = {
            'Hà Nội': {'transport': 500000, 'accommodation': 500000, 'activities': 200000},
            'TP. Hồ Chí Minh': {'transport': 500000, 'accommodation': 500000, 'activities': 200000},
            'Đà Nẵng': {'transport': 300000, 'accommodation': 400000, 'activities': 150000},
            'Nha Trang': {'transport': 400000, 'accommodation': 450000, 'activities': 180000},
            'Phú Quốc': {'transport': 1500000, 'accommodation': 600000, 'activities': 250000},
        }
        
        # Tìm cost cho destination
        dest_key = destination
        costs = base_costs.get(dest_key, {'transport': 500000, 'accommodation': 500000, 'activities': 200000})
        
        # Tính tổng
        multiplier = self.TRAVEL_STYLE_MULTIPLIERS.get(travel_style, 1.0)
        
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

