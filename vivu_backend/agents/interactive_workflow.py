"""
Interactive Workflow for Vi Vu - Simplified for 7 Agents
=================================================================
Workflow tương tác với người dùng, sử dụng 7 agents chính
Tích hợp đầy đủ với LangChain, LangGraph và LangSmith
"""
import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from agents.travel_agents.orchestrator_agent import OrchestratorAgent
from config.langsmith_config import get_langsmith_config

logger = logging.getLogger(__name__)


def run_interactive_workflow(payload: dict, timeout: int = 30) -> dict:
    """
    Hàm chính xử lý interactive workflow với 7 agents
    
    Args:
        payload: Dictionary chứa:
            - type: Loại request ('query' hoặc 'plan')
            - query_type: 'chat', 'search', hoặc 'plan'
            - ... (các tham số khác tùy query_type)
        timeout: Timeout tổng (giây)
    
    Returns:
        Dictionary với cấu trúc:
        {
            "status": "ok" | "error",
            "result": {...},
            "sources": [...],
            "error": "..." (nếu có lỗi)
        }
    """
    logger.info(f"Starting interactive workflow: {payload.get('query_type', 'unknown')}")
    
    try:
        # Validate input
        validation_result = _validate_payload(payload)
        if not validation_result['valid']:
            return {
                'status': 'error',
                'error': validation_result['error'],
                'result': {},
                'sources': []
            }
        
        query_type = payload.get('query_type')
        
        # Route to appropriate handler
        if query_type == 'plan':
            return _handle_plan_query(payload, timeout)
        elif query_type == 'chat':
            # Simple chat - có thể tích hợp RAG sau
            return {
                'status': 'ok',
                'result': {
                    'response': 'Xin chào! Tôi có thể giúp bạn lập kế hoạch du lịch. Hãy sử dụng query_type="plan" để tạo kế hoạch.',
                    'timestamp': datetime.now().isoformat()
                },
                'sources': []
            }
        elif query_type == 'search':
            # Search - có thể tích hợp RAG sau
            return {
                'status': 'ok',
                'result': {
                    'response': 'Tính năng tìm kiếm đang được phát triển.',
                    'timestamp': datetime.now().isoformat()
                },
                'sources': []
            }
        else:
            return {
                'status': 'error',
                'error': f'Unknown query_type: {query_type}',
                'result': {},
                'sources': []
            }
    
    except Exception as e:
        logger.error(f"Error in interactive workflow: {e}", exc_info=True)
        return {
            'status': 'error',
            'error': str(e),
            'result': {},
            'sources': []
        }


def _validate_payload(payload: dict) -> dict:
    """Validate payload structure"""
    if not isinstance(payload, dict):
        return {'valid': False, 'error': 'Payload must be a dictionary'}
    
    query_type = payload.get('query_type')
    
    if query_type == 'plan':
        # Required fields for plan
        required_fields = ['origin', 'destination', 'start_date', 'days', 'travelers']
        for field in required_fields:
            if field not in payload:
                return {'valid': False, 'error': f'Missing required field for plan: {field}'}
    
    return {'valid': True}


async def _handle_plan_query_async(payload: dict) -> dict:
    """Handle plan query asynchronously"""
    try:
        # Initialize Orchestrator Agent
        orchestrator = OrchestratorAgent()
        
        # Convert payload to state
        state = {
            'origin': payload.get('origin'),
            'destination': payload.get('destination'),
            'start_date': payload.get('start_date'),
            'days': payload.get('days'),
            'travelers': payload.get('travelers'),
            'travel_style': payload.get('travel_style', 'standard'),
            'rooms': payload.get('rooms', 1),
            'interests': payload.get('interests', []),
        }
        
        if payload.get('budget'):
            state['max_budget'] = payload['budget']
        
        if payload.get('selected_hotel'):
            state['selected_hotel'] = payload['selected_hotel']
        
        # Execute orchestrator
        result_state = await orchestrator.execute(state)
        
        # Check for errors
        if result_state.get('status') == 'error':
            return {
                'status': 'error',
                'error': result_state.get('error', 'Unknown error'),
                'result': {},
                'sources': []
            }
        
        # Format response
        return {
            'status': 'ok',
            'result': {
                'transport': result_state.get('transport', {}),
                'flight': result_state.get('flight'),
                'hotels': result_state.get('hotels', []),
                'selected_hotel': result_state.get('selected_hotel'),
                'activities': result_state.get('activities', []),
                'restaurants': result_state.get('restaurants', []),
                'budget': result_state.get('budget', {}),
                'itinerary': result_state.get('itinerary', {}),
                'costs': {
                    'transport': result_state.get('transport_cost', 0),
                    'accommodation': result_state.get('accommodation_cost', 0),
                    'activities': result_state.get('activities_cost', 0),
                    'dining': result_state.get('dining_cost', 0),
                    'total': result_state.get('budget', {}).get('total_vnd', 0),
                }
            },
            'sources': []
        }
        
    except Exception as e:
        logger.error(f"Error in plan query handler: {e}", exc_info=True)
        return {
            'status': 'error',
            'error': str(e),
            'result': {},
            'sources': []
        }


def _handle_plan_query(payload: dict, timeout: int) -> dict:
    """
    Handle trip planning query (synchronous wrapper with proper async handling).
    
    Sử dụng asyncio.run() đơn giản và xử lý timeout đúng cách.
    """
    try:
        # Sử dụng asyncio.run() - cách đơn giản và đúng đắn nhất
        # Nếu đã có event loop đang chạy, sẽ raise RuntimeError
        try:
            return asyncio.run(
                asyncio.wait_for(_handle_plan_query_async(payload), timeout=timeout)
            )
        except RuntimeError:
            # Nếu đã có event loop đang chạy (như trong Django/async context)
            # Tạo event loop mới trong thread riêng
            import concurrent.futures
            import threading
            
            def run_in_thread():
                # Tạo event loop mới trong thread này
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(
                        asyncio.wait_for(_handle_plan_query_async(payload), timeout=timeout)
                    )
                finally:
                    loop.close()
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_in_thread)
                return future.result(timeout=timeout + 5)  # Extra time for thread overhead
                
    except asyncio.TimeoutError:
        logger.error(f"Plan query timeout after {timeout}s")
        return {
            'status': 'error',
            'error': f'Request timeout after {timeout} seconds',
            'result': {},
            'sources': []
        }
    except Exception as e:
        logger.error(f"Error in sync plan handler: {e}", exc_info=True)
        return {
            'status': 'error',
            'error': str(e),
            'result': {},
            'sources': []
        }
