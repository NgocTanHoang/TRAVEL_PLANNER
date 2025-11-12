"""
Budget Agent - Agent quản lý ngân sách
=======================================
Chịu trách nhiệm:
- Tổng hợp chi phí từ tất cả agents
- Phân tích và đề xuất ngân sách
- Tính toán chi phí theo người và theo ngày
"""
import logging
from typing import Dict, Any, Optional
from decimal import Decimal
from ..base_agent import BaseAgent
from tools.budget_tools import get_budget_tools

logger = logging.getLogger(__name__)


def _to_float(value: Any, default: float = 0.0) -> float:
    """
    Chuyển đổi giá trị sang float an toàn.
    
    Args:
        value: Giá trị cần chuyển đổi (có thể là None, str, int, float, Decimal)
        default: Giá trị mặc định nếu không thể chuyển đổi
        
    Returns:
        float value
    """
    if value is None:
        return default
    
    if isinstance(value, (int, float)):
        return float(value)
    
    if isinstance(value, Decimal):
        return float(value)
    
    if isinstance(value, str):
        try:
            # Loại bỏ khoảng trắng và ký tự đặc biệt
            cleaned = value.strip().replace(',', '').replace(' ', '')
            return float(cleaned)
        except (ValueError, AttributeError):
            return default
    
    try:
        return float(value)
    except (ValueError, TypeError):
        logger.warning(f"Cannot convert {type(value)} to float: {value}, using default {default}")
        return default


def _to_int(value: Any, default: int = 1, min_value: int = 1) -> int:
    """
    Chuyển đổi giá trị sang int an toàn với validation.
    
    Args:
        value: Giá trị cần chuyển đổi
        default: Giá trị mặc định
        min_value: Giá trị tối thiểu
        
    Returns:
        int value >= min_value
    """
    if value is None:
        return max(default, min_value)
    
    if isinstance(value, int):
        return max(value, min_value)
    
    if isinstance(value, (float, Decimal)):
        return max(int(value), min_value)
    
    if isinstance(value, str):
        try:
            cleaned = value.strip()
            result = int(float(cleaned))  # Cho phép "1.0" -> 1
            return max(result, min_value)
        except (ValueError, TypeError):
            return max(default, min_value)
    
    try:
        result = int(value)
        return max(result, min_value)
    except (ValueError, TypeError):
        logger.warning(f"Cannot convert {type(value)} to int: {value}, using default {max(default, min_value)}")
        return max(default, min_value)


def _normalize_travel_style(value: Any) -> Any:
    """
    Chuẩn hóa travel_style - support cả string và list, extended styles
    
    Args:
        value: Giá trị travel_style (có thể là string, list, hoặc JSON string)
        
    Returns:
        str hoặc list: Normalized travel style(s)
    """
    if value is None:
        return 'standard'
    
    # Nếu là list, giữ nguyên (có thể đã được parse)
    if isinstance(value, list):
        return value
    
    # Nếu là string, thử parse JSON
    if isinstance(value, str):
        try:
            import json
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return parsed
            elif isinstance(parsed, str):
                value = parsed
        except (json.JSONDecodeError, ValueError):
            pass  # Keep as string
    
    # Normalize string style
    style = str(value).lower().strip()
    
    # Extended styles mapping (keep original if valid)
    extended_styles = [
        'budget', 'standard', 'luxury',
        'adventure', 'cultural', 'gastronomy', 'eco', 'wellness',
        'family', 'romantic', 'slow', 'digital_nomad',
        'shop_leisure', 'photography', 'religious', 'festival', 'extreme'
    ]
    
    if style in extended_styles:
        return style
    
    # Fallback mapping cho backward compatibility
    style_mapping = {
        'tiết kiệm': 'budget',
        'tiet kiem': 'budget',
        'cheap': 'budget',
        'cao cấp': 'luxury',
        'cao cap': 'luxury',
        'premium': 'luxury',
        'deluxe': 'luxury',
        'phiêu lưu': 'adventure',
        'phieu luu': 'adventure',
        'văn hóa': 'cultural',
        'van hoa': 'cultural',
        'ẩm thực': 'gastronomy',
        'am thuc': 'gastronomy',
        'foodie': 'gastronomy',
        'sinh thái': 'eco',
        'sinh thai': 'eco',
        'wellness': 'wellness',
        'gia đình': 'family',
        'gia dinh': 'family',
        'lãng mạn': 'romantic',
        'lang man': 'romantic',
        'honeymoon': 'romantic'
    }
    
    return style_mapping.get(style, 'standard')


class BudgetAgent(BaseAgent):
    """Agent xử lý ngân sách với validation và error handling chặt chẽ"""
    
    def __init__(self):
        super().__init__(
            agent_name="budget_agent",
            description="Handles budget calculation and analysis with robust validation"
        )
        self.budget_tools = get_budget_tools()
    
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Xử lý tính toán ngân sách với validation đầy đủ.
        
        Args:
            state: State dictionary với các chi phí:
                - transport_cost: Chi phí vận chuyển (VNĐ)
                - accommodation_cost: Chi phí lưu trú (VNĐ)
                - dining_cost: Chi phí ăn uống (VNĐ, optional)
                - activities_cost: Chi phí hoạt động (VNĐ, optional)
                - days: Số ngày (>= 1)
                - travelers: Số người (>= 1)
                - travel_style: 'budget', 'standard', 'luxury'
                
        Returns:
            Updated state với phân tích ngân sách đầy đủ:
                - budget: Dict với total_vnd, breakdown, currency, etc.
                - budget_allocation: Phân tích phân bổ
                - budget_summary: Các chỉ số tiện dụng (per_person_total, per_person_per_day)
        """
        self.log_input(state)
        
        try:
            # Chuẩn hóa và validate input
            transport_cost = _to_float(state.get('transport_cost'), 0.0)
            accommodation_cost = _to_float(state.get('accommodation_cost'), 0.0)
            dining_cost = state.get('dining_cost')  # None được xử lý bởi budget_tools
            activities_cost = state.get('activities_cost')  # None được xử lý bởi budget_tools
            
            # Convert None thành None (để budget_tools tự tính), otherwise convert to float
            if dining_cost is not None:
                dining_cost = _to_float(dining_cost, 0.0)
            if activities_cost is not None:
                activities_cost = _to_float(activities_cost, 0.0)
            
            # Validate days và travelers
            days = _to_int(state.get('days'), default=1, min_value=1)
            travelers = _to_int(state.get('travelers'), default=1, min_value=1)
            # Support extended styles - không normalize về 3 styles cơ bản nữa
            travel_style = _normalize_travel_style(state.get('travel_style', 'standard'))
            
            # Log validated inputs
            logger.debug(
                f"Budget calculation inputs - "
                f"transport: {transport_cost}, accommodation: {accommodation_cost}, "
                f"dining: {dining_cost}, activities: {activities_cost}, "
                f"days: {days}, travelers: {travelers}, style: {travel_style}"
            )
            
            # Tính tổng ngân sách (synchronous call)
            budget_result = self.budget_tools.calculate_total_budget(
                transport_cost=transport_cost,
                accommodation_cost=accommodation_cost,
                dining_cost=dining_cost,
                activities_cost=activities_cost,
                days=days,
                travelers=travelers,
                travel_style=travel_style
            )
            
            # Validate response từ budget_tools
            if not isinstance(budget_result, dict):
                raise ValueError(f"budget_tools.calculate_total_budget returned non-dict: {type(budget_result)}")
            
            total_vnd = budget_result.get('total_vnd') or budget_result.get('total') or 0
            total_vnd = _to_float(total_vnd, 0.0)
            
            breakdown = budget_result.get('breakdown', {})
            if not isinstance(breakdown, dict):
                logger.warning(f"Invalid breakdown format: {type(breakdown)}, using empty dict")
                breakdown = {}
            
            # Phân tích phân bổ ngân sách
            try:
                allocation = self.budget_tools.analyze_budget_allocation(
                    total_budget=total_vnd,
                    breakdown=breakdown
                )
            except Exception as e:
                logger.error(f"Error in analyze_budget_allocation: {e}", exc_info=True)
                # Fallback allocation
                allocation = {
                    'allocation_percent': {},
                    'recommendations': [f'Lỗi phân tích: {str(e)}'],
                    'is_balanced': False
                }
            
            # Tính các chỉ số tiện dụng
            per_person_total = total_vnd / travelers if travelers > 0 else total_vnd
            per_person_per_day = per_person_total / days if days > 0 else per_person_total
            
            # Chuẩn hóa breakdown values (đảm bảo tất cả là float)
            normalized_breakdown = {}
            for key, value in breakdown.items():
                normalized_breakdown[key] = _to_float(value, 0.0)
            
            # Cập nhật state với kết quả đầy đủ
            state['budget'] = {
                'total_vnd': round(total_vnd),
                'total': round(total_vnd),  # Alias for backward compatibility
                'currency': 'VND',  # Budget tools sử dụng VND
                'breakdown': normalized_breakdown,
                'per_person': round(per_person_total),
                'per_day': round(total_vnd / days) if days > 0 else round(total_vnd),
                'travel_style': travel_style,
                'days': days,
                'travelers': travelers
            }
            
            state['budget_allocation'] = allocation
            
            # Thêm summary với các chỉ số tiện dụng
            state['budget_summary'] = {
                'per_person_total': round(per_person_total),
                'per_person_per_day': round(per_person_per_day),
                'total_vnd': round(total_vnd),
                'days': days,
                'travelers': travelers,
                'travel_style': travel_style,
                'currency': 'VND'
            }
            
            self.log_output(state)
            return state
            
        except KeyError as e:
            error_msg = f"Missing required field in budget_result: {e}"
            logger.error(error_msg, exc_info=True)
            self.log_error(e, context={'state': state, 'error_type': 'KeyError'})
            state['budget_error'] = error_msg
            state['budget'] = {}
            state['budget_allocation'] = {}
            return state
            
        except Exception as e:
            error_msg = f"Budget calculation failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.log_error(e, context={'state': state})
            state['budget_error'] = error_msg
            # Đảm bảo state luôn có các keys cần thiết
            state.setdefault('budget', {})
            state.setdefault('budget_allocation', {})
            state.setdefault('budget_summary', {})
            return state
    
    async def suggest_budget(
        self,
        destination: str,
        days: int,
        travelers: int,
        travel_style: Any = 'standard'
    ) -> Dict[str, Any]:
        """
        Đề xuất ngân sách ban đầu với validation - support extended styles.
        
        Args:
            destination: Điểm đến
            days: Số ngày (>= 1)
            travelers: Số người (>= 1)
            travel_style: String hoặc list các phong cách (extended styles supported)
            
        Returns:
            Dict với ngân sách đề xuất hoặc error dict nếu thất bại
        """
        try:
            # Validate và normalize inputs
            if not destination or not isinstance(destination, str):
                return {
                    'error': 'Invalid destination: must be a non-empty string',
                    'destination': destination
                }
            
            days = _to_int(days, default=1, min_value=1)
            travelers = _to_int(travelers, default=1, min_value=1)
            # Support extended styles
            travel_style = _normalize_travel_style(travel_style)
            
            # Gọi budget_tools (synchronous)
            result = self.budget_tools.suggest_budget(
                destination=destination,
                days=days,
                travelers=travelers,
                travel_style=travel_style
            )
            
            # Validate response
            if not isinstance(result, dict):
                return {
                    'error': f'Invalid response from suggest_budget: {type(result)}',
                    'result': result
                }
            
            # Thêm currency nếu chưa có
            if 'currency' not in result:
                result['currency'] = 'VND'
            
            return result
            
        except Exception as e:
            error_msg = f"suggest_budget failed: {str(e)}"
            logger.exception(error_msg)
            return {
                'error': error_msg,
                'destination': destination,
                'days': days,
                'travelers': travelers,
                'travel_style': travel_style
            }

