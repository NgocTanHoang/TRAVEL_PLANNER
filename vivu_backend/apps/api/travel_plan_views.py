"""
RESTful API Views cho Travel Planning với 7 Agents
===================================================
Tuân thủ RESTful principles:
- GET /api/v1/travel-plans/ - List plans (if saved)
- POST /api/v1/travel-plans/ - Create new plan
- GET /api/v1/travel-plans/{id}/ - Get plan detail
- PUT /api/v1/travel-plans/{id}/ - Update plan
- DELETE /api/v1/travel-plans/{id}/ - Delete plan
- GET /api/v1/travel-plans/preview/ - Preview plan (no save)
"""
import sys
import os
from pathlib import Path
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import ValidationError
from django.utils import timezone
from django.core.cache import cache
import logging
import asyncio

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from .travel_plan_serializers import (
    TravelPlanRequestSerializer,
    TravelPlanResponseSerializer,
    TravelPlanPreviewSerializer
)

logger = logging.getLogger(__name__)


def rate_limit_check(user_id: int, limit: int = 10, window: int = 60) -> bool:
    """Check if user has exceeded rate limit"""
    cache_key = f"rate_limit:travel_plan:user_{user_id}"
    count = cache.get(cache_key, 0)
    
    if count >= limit:
        return False
    
    cache.set(cache_key, count + 1, window)
    return True


class TravelPlanPreviewView(APIView):
    """
    GET /api/v1/travel-plans/preview/
    
    Preview travel plan không lưu vào database
    Sử dụng 7 agents để tính toán nhanh
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """
        Preview travel plan
        
        Query params:
        - origin: Điểm xuất phát
        - destination: Điểm đến
        - days: Số ngày
        - travelers: Số người
        - travel_style: budget/standard/luxury
        """
        try:
            # Validate params
            origin = request.query_params.get('origin')
            destination = request.query_params.get('destination')
            days = request.query_params.get('days', type=int)
            travelers = request.query_params.get('travelers', type=int, default=2)
            travel_style = request.query_params.get('travel_style', 'standard')
            
            if not all([origin, destination, days]):
                raise ValidationError({
                    'error': 'Missing required parameters: origin, destination, days'
                })
            
            # Validate days (1-14)
            if days < 1:
                raise ValidationError({
                    'error': 'Số ngày phải lớn hơn 0',
                    'days': days
                })
            
            if days > 14:
                raise ValidationError({
                    'error': 'Số ngày không được vượt quá 14 ngày',
                    'days': days,
                    'max_days': 14
                })
            
            # Validate travelers (1-20)
            if travelers < 1:
                raise ValidationError({
                    'error': 'Số người phải lớn hơn 0',
                    'travelers': travelers
                })
            
            if travelers > 20:
                raise ValidationError({
                    'error': 'Số người không được vượt quá 20 người (tương ứng với 1 gia đình)',
                    'travelers': travelers,
                    'max_travelers': 20
                })
            
            # Rate limiting
            user_id = request.user.id if request.user.is_authenticated else 0
            if not rate_limit_check(user_id, limit=20, window=60):
                return Response({
                    'error': 'Rate limit exceeded. Maximum 20 requests per minute.'
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)
            
            # Import orchestrator agent
            from agents.travel_agents.orchestrator_agent import OrchestratorAgent
            
            # Create state
            state = {
                'origin': origin,
                'destination': destination,
                'days': days,
                'travelers': travelers,
                'travel_style': travel_style,
                'preview_mode': True
            }
            
            # Only run Transport and Budget agents for preview
            from agents.travel_agents.transport_agent import TransportAgent
            from agents.travel_agents.budget_agent import BudgetAgent
            
            transport_agent = TransportAgent()
            budget_agent = BudgetAgent()
            
            # Execute agents (sync wrapper for async)
            async def run_preview():
                state_result = await transport_agent.execute(state)
                
                # Suggest budget
                if state_result.get('transport'):
                    suggested_budget = await budget_agent.suggest_budget(
                        destination, days, travelers, travel_style
                    )
                    state_result['budget'] = suggested_budget
                
                return state_result
            
            # Run async
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, run_preview())
                        result_state = future.result(timeout=30)
                else:
                    result_state = loop.run_until_complete(run_preview())
            except RuntimeError:
                result_state = asyncio.run(run_preview())
            
            # Format response
            serializer = TravelPlanPreviewSerializer({
                'status': 'success',
                'preview': {
                    'transport': result_state.get('transport', {}),
                    'budget_estimate': result_state.get('budget', {}),
                },
                'timestamp': timezone.now()
            })
            
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error in travel plan preview: {e}", exc_info=True)
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TravelPlanCreateView(APIView):
    """
    POST /api/v1/travel-plans/
    
    Tạo kế hoạch du lịch hoàn chỉnh với 7 agents
    """
    permission_classes = [AllowAny]  # Có thể đổi thành IsAuthenticated
    
    def post(self, request):
        """
        Tạo travel plan
        
        Request body:
        {
            "origin": "Hà Nội",
            "destination": "Đà Nẵng",
            "start_date": "2025-02-01",
            "days": 5,
            "travelers": 2,
            "travel_style": "standard",
            "budget": 10000000,
            "rooms": 1,
            "interests": ["văn hóa", "ẩm thực"],
            "selected_hotel": {...} (optional)
        }
        """
        try:
            # Validate request
            serializer = TravelPlanRequestSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            validated_data = serializer.validated_data
            
            # Rate limiting
            user_id = request.user.id if request.user.is_authenticated else 0
            if not rate_limit_check(user_id, limit=10, window=60):
                return Response({
                    'error': 'Rate limit exceeded. Maximum 10 requests per minute.'
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)
            
            # Import orchestrator agent
            from agents.travel_agents.orchestrator_agent import OrchestratorAgent
            
            # Prepare state
            state = {
                'origin': validated_data['origin'],
                'destination': validated_data['destination'],
                'start_date': validated_data['start_date'].strftime('%Y-%m-%d'),
                'days': validated_data['days'],
                'travelers': validated_data['travelers'],
                'travel_style': validated_data.get('travel_style', 'standard'),
                'rooms': validated_data.get('rooms', 1),
                'interests': validated_data.get('interests', []),
            }
            
            if validated_data.get('budget'):
                state['max_budget'] = validated_data['budget']
            
            if validated_data.get('selected_hotel'):
                state['selected_hotel'] = validated_data['selected_hotel']
            
            # Execute orchestrator
            orchestrator = OrchestratorAgent()
            
            # Run async
            async def run_plan():
                return await orchestrator.execute(state)
            
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, run_plan())
                        result_state = future.result(timeout=120)  # 2 minutes timeout
                else:
                    result_state = loop.run_until_complete(run_plan())
            except RuntimeError:
                result_state = asyncio.run(run_plan())
            
            # Check for errors
            if result_state.get('status') == 'error':
                return Response({
                    'error': result_state.get('error', 'Unknown error occurred')
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Format response
            response_data = {
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
                'timestamp': timezone.now()
            }
            
            response_serializer = TravelPlanResponseSerializer(response_data)
            
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            
        except ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error creating travel plan: {e}", exc_info=True)
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

