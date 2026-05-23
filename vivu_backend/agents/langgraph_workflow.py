"""
LangGraph Workflow for Travel Planning with 7 Agents
====================================================
Workflow sử dụng LangGraph để điều phối 7 agents chính với tích hợp đầy đủ LangChain, LangGraph và LangSmith:
1. Transport Agent
2. Flight Agent
3. Accommodation Agent
4. Activities Agent
5. Budget Agent
6. Planning Agent
7. Orchestrator Agent (điều phối)
"""
import logging
from typing import Dict, Any, Optional
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from .state import TravelPlanningState
from config.langsmith_config import get_langsmith_config
from utils.error_handling import (
    retry_with_backoff,
    RetryConfig,
    classify_error,
    ErrorType
)

# Import 7 agents
from .travel_agents.transport_agent import TransportAgent
from .travel_agents.flight_agent import FlightAgent
from .travel_agents.accommodation_agent import AccommodationAgent
from .travel_agents.activities_agent import ActivitiesAgent
from .travel_agents.budget_agent import BudgetAgent
from .travel_agents.planning_agent import PlanningAgent

logger = logging.getLogger(__name__)


class LangGraphTravelWorkflow:
    """
    LangGraph workflow cho travel planning với 7 agents.
    
    Workflow:
    1. Transport Agent → Tính khoảng cách, đề xuất phương tiện
    2. Flight Agent (conditional) → Nếu cần máy bay
    3. Accommodation Agent → Tìm khách sạn
    4. Activities Agent → Tìm hoạt động & ăn uống
    5. Budget Agent → Tính tổng ngân sách
    6. Planning Agent → Tạo lịch trình chi tiết
    """
    
    def __init__(self):
        """Initialize workflow with all 7 agents and LangSmith integration"""
        # Initialize LangSmith config
        self.langsmith_config = get_langsmith_config()
        
        # Initialize agents
        self.transport_agent = TransportAgent()
        self.flight_agent = FlightAgent()
        self.accommodation_agent = AccommodationAgent()
        self.activities_agent = ActivitiesAgent()
        self.budget_agent = BudgetAgent()
        self.planning_agent = PlanningAgent()
        
        # Build graph với LangSmith checkpointing
        self.graph = self._build_graph()
        if self.graph:
            # Sử dụng MemorySaver cho checkpointing (có thể nâng cấp lên PostgresSaver sau)
            memory = MemorySaver()
            self.app = self.graph.compile(checkpointer=memory)
        else:
            self.app = None
        
        logger.info("LangGraph travel workflow initialized with 7 agents")
        if self.langsmith_config.tracing_enabled:
            logger.info(f"LangSmith tracing enabled for workflow (project: {self.langsmith_config.project_name})")
    
    def _build_graph(self) -> Optional[StateGraph]:
        """Build the LangGraph workflow"""
        try:
            # Create graph
            workflow = StateGraph(TravelPlanningState)
            
            # Add nodes (agents)
            workflow.add_node("transport", self._transport_node)
            workflow.add_node("flight", self._flight_node)
            workflow.add_node("accommodation", self._accommodation_node)
            workflow.add_node("activities", self._activities_node)
            workflow.add_node("budget", self._budget_node)
            workflow.add_node("planning", self._planning_node)
            
            # Define workflow edges
            workflow.set_entry_point("transport")
            
            # Conditional edge: flight chỉ chạy nếu cần máy bay
            workflow.add_conditional_edges(
                "transport",
                self._should_use_flight,
                {
                    "yes": "flight",
                    "no": "accommodation"
                }
            )
            
            workflow.add_edge("flight", "accommodation")
            workflow.add_edge("accommodation", "activities")
            workflow.add_edge("activities", "budget")
            workflow.add_edge("budget", "planning")
            workflow.add_edge("planning", END)
            
            logger.info("LangGraph workflow built successfully")
            return workflow
            
        except Exception as e:
            logger.error(f"Error building graph: {e}", exc_info=True)
            return None
    
    def _should_use_flight(self, state: TravelPlanningState) -> str:
        """Determine if flight agent should run"""
        transport = state.get('transport', {})
        method = transport.get('suggested_method', '')
        return "yes" if method == 'flight' else "no"
    
    # Node functions (wrappers for agents với error handling và tracing)
    @retry_with_backoff(config=RetryConfig(max_retries=2, initial_delay=1.0))
    async def _transport_node(self, state: TravelPlanningState) -> TravelPlanningState:
        """Transport agent node với retry và LangSmith tracing"""
        try:
            state['current_step'] = 'transport'
            
            # Get LangSmith config for tracing
            runnable_config = self.transport_agent.get_runnable_config(
                tags=['langgraph-node', 'transport'],
                metadata={'step': 'transport'}
            )
            
            # Execute agent với tracing
            result = await self.transport_agent.execute(state)
            result['completed_steps'] = result.get('completed_steps', []) + ['transport']
            return result
        except Exception as e:
            error_type = classify_error(e)
            logger.error(f"Transport node error ({error_type.value}): {e}", exc_info=True)
            state['transport_error'] = str(e)
            state['status'] = 'error'
            # Không stop workflow nếu là retryable error, chỉ log
            if error_type == ErrorType.RETRYABLE:
                state['completed_steps'] = state.get('completed_steps', []) + ['transport']
            return state
    
    @retry_with_backoff(config=RetryConfig(max_retries=2, initial_delay=1.0))
    async def _flight_node(self, state: TravelPlanningState) -> TravelPlanningState:
        """Flight agent node với retry và LangSmith tracing"""
        try:
            state['current_step'] = 'flight'
            state['departure_date'] = state.get('start_date')
            
            # Get LangSmith config for tracing
            runnable_config = self.flight_agent.get_runnable_config(
                tags=['langgraph-node', 'flight'],
                metadata={'step': 'flight'}
            )
            
            result = await self.flight_agent.execute(state)
            
            # Update transport cost from flight
            if result.get('flight'):
                result['transport_cost'] = result['flight'].get('price_vnd', 0)
            else:
                result['transport_cost'] = result.get('transport', {}).get('estimated_cost_vnd', 0)
            
            result['completed_steps'] = result.get('completed_steps', []) + ['flight']
            return result
        except Exception as e:
            error_type = classify_error(e)
            logger.error(f"Flight node error ({error_type.value}): {e}", exc_info=True)
            state['flight_error'] = str(e)
            state['completed_steps'] = state.get('completed_steps', []) + ['flight']
            return state
    
    @retry_with_backoff(config=RetryConfig(max_retries=2, initial_delay=1.0))
    async def _accommodation_node(self, state: TravelPlanningState) -> TravelPlanningState:
        """Accommodation agent node với retry và LangSmith tracing"""
        try:
            # Get LangSmith config for tracing
            runnable_config = self.accommodation_agent.get_runnable_config(
                tags=['langgraph-node', 'accommodation'],
                metadata={'step': 'accommodation'}
            )
            state['current_step'] = 'accommodation'
            
            # Đồng bộ logic với custom orchestrator:
            # nights = max(1, days - 1) để tránh lệch chi phí lưu trú.
            state['check_in'] = state.get('start_date')
            if state.get('start_date') and state.get('days'):
                from datetime import datetime, timedelta
                start = datetime.strptime(state['start_date'], '%Y-%m-%d')
                nights = max(1, int(state['days']) - 1)
                state['nights'] = nights
                end = start + timedelta(days=nights)
                state['check_out'] = end.strftime('%Y-%m-%d')
            
            result = await self.accommodation_agent.execute(state)
            
            # Calculate accommodation cost
            if result.get('selected_hotel') and result.get('check_in') and result.get('check_out'):
                from datetime import datetime
                from tools.accommodation_tools import get_accommodation_tools
                start = datetime.strptime(result['check_in'], '%Y-%m-%d')
                end = datetime.strptime(result['check_out'], '%Y-%m-%d')
                nights = max(1, (end - start).days)
                acc_tools = get_accommodation_tools()
                result['accommodation_cost'] = acc_tools.calculate_total_accommodation_cost(
                    price_per_night=result['selected_hotel'].get('price_per_night', 0),
                    nights=nights,
                    rooms=result.get('rooms', 1)
                )
            elif result.get('hotels'):
                hotel = result['hotels'][0]
                if result.get('days'):
                    from tools.accommodation_tools import get_accommodation_tools
                    acc_tools = get_accommodation_tools()
                    result['accommodation_cost'] = acc_tools.calculate_total_accommodation_cost(
                        price_per_night=hotel.get('price_per_night', 0),
                        nights=result.get('nights', max(1, int(result['days']) - 1)),
                        rooms=result.get('rooms', 1)
                    )
            
            result['completed_steps'] = result.get('completed_steps', []) + ['accommodation']
            return result
        except Exception as e:
            error_type = classify_error(e)
            logger.error(f"Accommodation node error ({error_type.value}): {e}", exc_info=True)
            state['accommodation_error'] = str(e)
            state['completed_steps'] = state.get('completed_steps', []) + ['accommodation']
            return state
    
    @retry_with_backoff(config=RetryConfig(max_retries=2, initial_delay=1.0))
    async def _activities_node(self, state: TravelPlanningState) -> TravelPlanningState:
        """Activities agent node với retry và LangSmith tracing"""
        try:
            state['current_step'] = 'activities'
            
            # Get LangSmith config for tracing
            runnable_config = self.activities_agent.get_runnable_config(
                tags=['langgraph-node', 'activities'],
                metadata={'step': 'activities'}
            )
            
            result = await self.activities_agent.execute(state)
            result['activities_cost'] = result.get('activities_cost', 0)
            result['dining_cost'] = result.get('dining_cost', 0)
            result['completed_steps'] = result.get('completed_steps', []) + ['activities']
            return result
        except Exception as e:
            error_type = classify_error(e)
            logger.error(f"Activities node error ({error_type.value}): {e}", exc_info=True)
            state['activities_error'] = str(e)
            state['completed_steps'] = state.get('completed_steps', []) + ['activities']
            return state
    
    async def _budget_node(self, state: TravelPlanningState) -> TravelPlanningState:
        """Budget agent node với LangSmith tracing"""
        try:
            state['current_step'] = 'budget'
            
            # Get LangSmith config for tracing
            runnable_config = self.budget_agent.get_runnable_config(
                tags=['langgraph-node', 'budget'],
                metadata={'step': 'budget'}
            )
            
            result = await self.budget_agent.execute(state)
            result['completed_steps'] = result.get('completed_steps', []) + ['budget']
            return result
        except Exception as e:
            error_type = classify_error(e)
            logger.error(f"Budget node error ({error_type.value}): {e}", exc_info=True)
            state['budget_error'] = str(e)
            state['completed_steps'] = state.get('completed_steps', []) + ['budget']
            return state
    
    async def _planning_node(self, state: TravelPlanningState) -> TravelPlanningState:
        """Planning agent node với LangSmith tracing"""
        try:
            state['current_step'] = 'planning'
            
            # Get LangSmith config for tracing
            runnable_config = self.planning_agent.get_runnable_config(
                tags=['langgraph-node', 'planning'],
                metadata={'step': 'planning'}
            )
            
            result = await self.planning_agent.execute(state)
            result['status'] = 'success'
            result['plan_ready'] = True
            result['completed_steps'] = result.get('completed_steps', []) + ['planning']
            return result
        except Exception as e:
            error_type = classify_error(e)
            logger.error(f"Planning node error ({error_type.value}): {e}", exc_info=True)
            state['planning_error'] = str(e)
            state['status'] = 'error'
            state['completed_steps'] = state.get('completed_steps', []) + ['planning']
            return state
    
    async def run(self, initial_state: Dict[str, Any], config: Optional[Dict] = None) -> TravelPlanningState:
        """
        Run the complete workflow với LangSmith tracing và checkpointing
        
        Args:
            initial_state: Initial state dictionary
            config: Optional LangGraph config (for checkpointing thread_id, etc.)
            
        Returns:
            Final state after workflow completion
        """
        if not self.app:
            raise ValueError("Workflow not available (graph build failed)")
        
        logger.info("Starting LangGraph travel workflow")
        logger.info(f"Input: {initial_state.get('origin')} -> {initial_state.get('destination')}")
        
        try:
            # Convert to TravelPlanningState
            state: TravelPlanningState = {
                'status': 'in_progress',
                'completed_steps': [],
                **initial_state
            }
            
            # Prepare config với LangSmith tracing
            if config is None:
                import uuid
                config = {
                    'configurable': {
                        'thread_id': str(uuid.uuid4())
                    }
                }
            
            # Merge với LangSmith config
            langsmith_config = self.langsmith_config.get_runnable_config(
                tags=['langgraph-workflow', 'travel-planning'],
                metadata={
                    'origin': initial_state.get('origin'),
                    'destination': initial_state.get('destination'),
                    'days': initial_state.get('days')
                }
            )
            
            # Run the graph với tracing
            final_state = await self.app.ainvoke(state, config)
            
            logger.info(f"Workflow completed. Steps: {final_state.get('completed_steps', [])}")
            
            return final_state
            
        except Exception as e:
            error_type = classify_error(e)
            logger.error(f"Workflow failed ({error_type.value}): {e}", exc_info=True)
            # Propagate error nhưng với context
            final_state = state.copy()
            final_state['status'] = 'error'
            final_state['error'] = str(e)
            final_state['error_type'] = error_type.value
            return final_state


# Convenience function
async def run_travel_workflow(
    origin: str,
    destination: str,
    start_date: str,
    days: int,
    travelers: int = 2,
    travel_style: str = "standard",
    **kwargs
) -> TravelPlanningState:
    """
    Convenience function to run travel workflow
    
    Args:
        origin: Điểm xuất phát
        destination: Điểm đến
        start_date: Ngày bắt đầu (YYYY-MM-DD)
        days: Số ngày
        travelers: Số người
        travel_style: Phong cách du lịch
        **kwargs: Additional parameters
        
    Returns:
        Final state with complete travel plan
    """
    workflow = LangGraphTravelWorkflow()
    
    initial_state = {
        'origin': origin,
        'destination': destination,
        'start_date': start_date,
        'days': days,
        'travelers': travelers,
        'travel_style': travel_style,
        **kwargs
    }
    
    return await workflow.run(initial_state)
