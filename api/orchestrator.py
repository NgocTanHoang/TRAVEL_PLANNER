"""
FastAPI Orchestrator for Travel Planner Multi-Agent System
==========================================================
Điều phối 7 agents chính:
1. Transport Agent
2. Flight Agent
3. Accommodation Agent
4. Activities Agent
5. Budget Agent
6. Planning Agent
7. Orchestrator Agent (coordinate all)
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime
import logging
import asyncio

# Import 7 agents
from agents.travel_agents.orchestrator_agent import OrchestratorAgent

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Travel Planner API",
    description="Multi-Agent System for Travel Planning",
    version="2.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Orchestrator Agent
orchestrator_agent = OrchestratorAgent()


# Request Models
class TravelPlanRequest(BaseModel):
    """Request model for travel planning"""
    origin: str = Field(..., description="Điểm xuất phát")
    destination: str = Field(..., description="Điểm đến")
    start_date: str = Field(..., description="Ngày bắt đầu (YYYY-MM-DD)")
    days: int = Field(..., description="Số ngày", ge=1, le=30)
    travelers: int = Field(..., description="Số người", ge=1, le=20)
    travel_style: str = Field(default="standard", description="Phong cách: budget, standard, luxury")
    budget: Optional[float] = Field(None, description="Ngân sách tối đa (VNĐ)")
    selected_hotel: Optional[Dict[str, Any]] = Field(None, description="Khách sạn đã chọn")
    rooms: int = Field(default=1, description="Số phòng")
    interests: Optional[List[str]] = Field(None, description="Sở thích du lịch")


class HealthCheck(BaseModel):
    """Health check response"""
    status: str
    timestamp: str
    agents_available: List[str]


# API Endpoints
@app.get("/", response_model=HealthCheck)
async def root():
    """Root endpoint - health check"""
    return HealthCheck(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        agents_available=[
            "transport_agent",
            "flight_agent",
            "accommodation_agent",
            "activities_agent",
            "budget_agent",
            "planning_agent",
            "orchestrator_agent"
        ]
    )


@app.post("/api/v1/plan")
async def create_travel_plan(request: TravelPlanRequest) -> Dict[str, Any]:
    """
    Tạo kế hoạch du lịch hoàn chỉnh
    
    Args:
        request: TravelPlanRequest với thông tin chuyến đi
        
    Returns:
        Dict với kế hoạch du lịch hoàn chỉnh
    """
    logger.info(f"Received travel plan request: {request.origin} -> {request.destination}")
    
    try:
        # Convert request to state dict
        state = {
            'origin': request.origin,
            'destination': request.destination,
            'start_date': request.start_date,
            'days': request.days,
            'travelers': request.travelers,
            'travel_style': request.travel_style,
            'rooms': request.rooms,
            'interests': request.interests or [],
        }
        
        if request.budget:
            state['max_budget'] = request.budget
        
        if request.selected_hotel:
            state['selected_hotel'] = request.selected_hotel
        
        # Execute orchestrator agent
        result_state = await orchestrator_agent.execute(state)
        
        # Check for errors
        if result_state.get('status') == 'error':
            raise HTTPException(
                status_code=500,
                detail=result_state.get('error', 'Unknown error occurred')
            )
        
        # Format response
        return {
            'status': 'success',
            'plan': {
                'transport': result_state.get('transport', {}),
                'flight': result_state.get('flight'),
                'hotels': result_state.get('hotels', []),
                'selected_hotel': result_state.get('selected_hotel'),
                'activities': result_state.get('activities', []),
                'restaurants': result_state.get('restaurants', []),
                'budget': result_state.get('budget', {}),
                'itinerary': result_state.get('itinerary', {}),
            },
            'costs': {
                'transport': result_state.get('transport_cost', 0),
                'accommodation': result_state.get('accommodation_cost', 0),
                'activities': result_state.get('activities_cost', 0),
                'dining': result_state.get('dining_cost', 0),
                'total': result_state.get('budget', {}).get('total_vnd', 0),
            },
            'timestamp': datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating travel plan: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


@app.get("/api/v1/plan/preview")
async def preview_travel_plan(
    origin: str,
    destination: str,
    days: int,
    travelers: int,
    travel_style: str = "standard"
) -> Dict[str, Any]:
    """
    Preview kế hoạch du lịch (không tạo lịch trình chi tiết)
    
    Args:
        origin: Điểm xuất phát
        destination: Điểm đến
        days: Số ngày
        travelers: Số người
        travel_style: Phong cách du lịch
        
    Returns:
        Dict với preview (transport, budget estimate)
    """
    try:
        state = {
            'origin': origin,
            'destination': destination,
            'days': days,
            'travelers': travelers,
            'travel_style': travel_style,
            'preview_mode': True
        }
        
        # Chỉ chạy Transport và Budget Agent
        from agents.travel_agents.transport_agent import TransportAgent
        from agents.travel_agents.budget_agent import BudgetAgent
        
        transport_agent = TransportAgent()
        budget_agent = BudgetAgent()
        
        state = await transport_agent.execute(state)
        
        # Suggest budget
        if state.get('transport'):
            suggested_budget = await budget_agent.suggest_budget(
                destination, days, travelers, travel_style
            )
            state['budget'] = suggested_budget
        
        return {
            'status': 'success',
            'preview': {
                'transport': state.get('transport', {}),
                'budget_estimate': state.get('budget', {}),
            },
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error previewing travel plan: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)

