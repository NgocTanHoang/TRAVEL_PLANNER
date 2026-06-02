"""
Orchestrator for Vi Vu multi-agent system
===================================================
Điều phối cả interactive workflow và LangGraph workflow với 7 agents.

NOTE: Đây là high-level orchestrator. 
Chi tiết điều phối 7 agents được thực hiện bởi OrchestratorAgent trong travel_agents/orchestrator_agent.py
"""
import logging
from typing import Dict, Any, Optional

# Import workflows
from .interactive_workflow import run_interactive_workflow
from .langgraph_workflow import LangGraphTravelWorkflow

logger = logging.getLogger(__name__)


class TravelPlannerOrchestrator:
    """
    Orchestrates both interactive and LangGraph workflows với 7 agents.
    
    - Interactive workflow: Synchronous, lightweight, for user queries
    - LangGraph workflow: Async workflow cho complex planning với 7 agents
    """
    
    def __init__(self):
        """Initialize the orchestrator."""
        logger.info("Vi Vu orchestrator initialized (7 agents)")
        logger.info("  - Interactive workflow: Available (synchronous)")
        logger.info("  - LangGraph workflow: Available (async)")
        self._langgraph_workflow = None
    
    def execute_interactive(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute interactive workflow (synchronous).
        
        Args:
            payload: Input payload với:
                - type: 'query' hoặc 'plan'
                - user_id: User ID
                - query_type: 'chat', 'search', hoặc 'plan'
                - ... (các tham số khác)
        
        Returns:
            JSON response dictionary
        """
        logger.info(f"Executing interactive workflow: {payload.get('query_type', 'unknown')}")
        
        try:
            # Use interactive workflow (synchronous, lightweight)
            result = run_interactive_workflow(payload, timeout=20)
            
            logger.info(f"Interactive workflow completed: {result.get('status', 'unknown')}")
            return result
        
        except Exception as e:
            logger.error(f"Error in execute_interactive: {e}", exc_info=True)
            return {
                'status': 'error',
                'error': str(e),
                'result': {},
                'sources': []
            }
    
    async def run_langgraph_workflow(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run LangGraph workflow với 7 agents cho travel planning.
        
        Args:
            payload: Input data với:
                - origin: Điểm xuất phát
                - destination: Điểm đến
                - start_date: Ngày bắt đầu
                - days: Số ngày
                - travelers: Số người
                - travel_style: Phong cách
                - ... (các tham số khác)
            
        Returns:
            Final state sau khi workflow hoàn thành
        """
        try:
            # Lazy initialization của LangGraph workflow
            if self._langgraph_workflow is None:
                self._langgraph_workflow = LangGraphTravelWorkflow()
            
            result = await self._langgraph_workflow.run(payload)
            
            logger.info(f"LangGraph workflow completed")
            return result
            
        except Exception as e:
            logger.error(f"Error in LangGraph workflow: {e}", exc_info=True)
            raise


# Singleton instance
_orchestrator_instance = None


def get_orchestrator() -> TravelPlannerOrchestrator:
    """
    Get or create the orchestrator singleton.
    
    Returns:
        TravelPlannerOrchestrator instance
    """
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = TravelPlannerOrchestrator()
    return _orchestrator_instance

