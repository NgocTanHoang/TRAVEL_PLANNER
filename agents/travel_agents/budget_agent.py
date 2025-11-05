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
from ..base_agent import BaseAgent
from tools.budget_tools import get_budget_tools

logger = logging.getLogger(__name__)


class BudgetAgent(BaseAgent):
    """Agent xử lý ngân sách"""
    
    def __init__(self):
        super().__init__(
            agent_name="budget_agent",
            description="Handles budget calculation and analysis"
        )
        self.budget_tools = get_budget_tools()
    
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Xử lý tính toán ngân sách
        
        Args:
            state: State dictionary với các chi phí:
                - transport_cost: Chi phí vận chuyển
                - accommodation_cost: Chi phí lưu trú
                - dining_cost: Chi phí ăn uống (optional)
                - activities_cost: Chi phí hoạt động (optional)
                - days: Số ngày
                - travelers: Số người
                - travel_style: 'budget', 'standard', 'luxury'
                
        Returns:
            Updated state với phân tích ngân sách
        """
        self.log_input(state)
        
        try:
            transport_cost = state.get('transport_cost', 0)
            accommodation_cost = state.get('accommodation_cost', 0)
            dining_cost = state.get('dining_cost')
            activities_cost = state.get('activities_cost')
            days = state.get('days', 1)
            travelers = state.get('travelers', 1)
            travel_style = state.get('travel_style', 'standard')
            
            # Tính tổng ngân sách
            budget_result = self.budget_tools.calculate_total_budget(
                transport_cost=transport_cost,
                accommodation_cost=accommodation_cost,
                dining_cost=dining_cost,
                activities_cost=activities_cost,
                days=days,
                travelers=travelers,
                travel_style=travel_style
            )
            
            # Phân tích phân bổ ngân sách
            allocation = self.budget_tools.analyze_budget_allocation(
                total_budget=budget_result['total_vnd'],
                breakdown=budget_result['breakdown']
            )
            
            state['budget'] = budget_result
            state['budget_allocation'] = allocation
            
            self.log_output(state)
            return state
            
        except Exception as e:
            self.log_error(e, context={'state': state})
            state['budget_error'] = str(e)
            return state
    
    async def suggest_budget(
        self,
        destination: str,
        days: int,
        travelers: int,
        travel_style: str = 'standard'
    ) -> Dict[str, Any]:
        """
        Đề xuất ngân sách ban đầu
        
        Args:
            destination: Điểm đến
            days: Số ngày
            travelers: Số người
            travel_style: 'budget', 'standard', 'luxury'
            
        Returns:
            Dict với ngân sách đề xuất
        """
        return self.budget_tools.suggest_budget(destination, days, travelers, travel_style)

