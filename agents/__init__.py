"""
Travel Planner Agents Package
==============================
7 Agents chính:
1. Orchestrator Agent - Điều phối
2. Transport Agent - Vận chuyển
3. Flight Agent - Vé máy bay
4. Accommodation Agent - Lưu trú
5. Budget Agent - Ngân sách
6. Planning Agent - Lập kế hoạch
7. Activities Agent - Hoạt động & ăn uống
"""

# Import 7 main agents
from .travel_agents import (
    OrchestratorAgent,
    TransportAgent,
    FlightAgent,
    AccommodationAgent,
    BudgetAgent,
    PlanningAgent,
    ActivitiesAgent
)

# Import Vector DB & RAG
from .travel_agents.vector_db import VectorDatabaseAgent, get_vector_db_agent
from .travel_agents.rag import RAGAgent

# Import orchestrator and workflows
from .orchestrator import TravelPlannerOrchestrator, get_orchestrator
from .interactive_workflow import run_interactive_workflow
from .langgraph_workflow import LangGraphTravelWorkflow, run_travel_workflow

# Base agent (required for all agents)
from .base_agent import BaseAgent

# State definition
from .state import TravelPlanningState

__all__ = [
    # 7 Main Agents
    'OrchestratorAgent',
    'TransportAgent',
    'FlightAgent',
    'AccommodationAgent',
    'BudgetAgent',
    'PlanningAgent',
    'ActivitiesAgent',
    # Vector DB & RAG
    'VectorDatabaseAgent',
    'get_vector_db_agent',
    'RAGAgent',
    # Orchestrator
    'TravelPlannerOrchestrator',
    'get_orchestrator',
    # Workflows
    'run_interactive_workflow',
    'LangGraphTravelWorkflow',
    'run_travel_workflow',
    # Base
    'BaseAgent',
    'TravelPlanningState',
]
