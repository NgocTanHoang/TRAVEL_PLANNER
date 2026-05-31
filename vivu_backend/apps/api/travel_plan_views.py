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
import json
import threading
import time
from pathlib import Path
from datetime import datetime, timedelta
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import ValidationError
from django.utils import timezone
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from django.db import IntegrityError, transaction
from django.http import StreamingHttpResponse
import logging
import asyncio
import traceback
from typing import Dict, Any, List, Optional
from pydantic import ValidationError as PydanticValidationError
import requests

from apps.analytics.models import YeuCauLoTrinh
from apps.analytics.services import (
    cap_nhat_yeu_cau_lo_trinh,
    ghi_nhan_yeu_cau_lo_trinh_async,
    tao_ban_ghi_yeu_cau_lo_trinh,
)
from apps.itineraries.models import (
    LichTrinh,
    LichTrinhDiaDiem,
)
from apps.places.models import TinhThanh, DiaDiem
from agents.state import FullTravelPlanOutput
from utils.travel_plan_streaming import (
    append_event,
    check_generation_rate_limit,
    complete_run,
    create_thread_id,
    fail_run,
    get_client_ip,
    get_events_since,
    get_run,
    initialize_run,
    record_day_updates,
    record_progress,
    release_streaming_connections,
    set_running,
)
from utils.security import ensure_sensitive_log_filter, sanitize_sensitive_data, sanitize_sensitive_string

# Add backend directory to path for agents, tools, etc.
# BASE_DIR (vivu_backend) is already added in settings.py, but adding here for safety
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from .travel_plan_serializers import (
    TravelPlanRequestSerializer,
    TravelPlanResponseSerializer,
    TravelPlanPreviewSerializer,
    TravelPlanPreviewQuerySerializer,
)

logger = logging.getLogger(__name__)
ensure_sensitive_log_filter(logger)


def rate_limit_check(user_id: int, limit: int = 10, window: int = 60) -> bool:
    """Check if user has exceeded rate limit"""
    cache_key = f"rate_limit:travel_plan:user_{user_id}"
    count = cache.get(cache_key, 0)
    
    if count >= limit:
        return False
    
    cache.set(cache_key, count + 1, window)
    return True


def _build_auth_required_response() -> Response:
    return Response(
        {
            "error": "Bạn cần đăng nhập để sử dụng tính năng này."
        },
        status=status.HTTP_401_UNAUTHORIZED,
    )


def _require_authenticated_request(request) -> Optional[Response]:
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return _build_auth_required_response()
    return None


def _iso_timestamp() -> str:
    return timezone.now().isoformat()


def _is_authorized_for_run(request, run_state: Optional[Dict[str, Any]]) -> bool:
    if not run_state:
        return False
    user = getattr(request, "user", None)
    if user is None or not user.is_authenticated:
        return False
    owner_key = str(run_state.get("owner_key") or "")
    return owner_key == f"user:{user.pk}"


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
            serializer = TravelPlanPreviewQuerySerializer(data=request.query_params)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            validated_data = serializer.validated_data
            origin = validated_data['origin']
            destination = validated_data['destination']
            days = validated_data['days']
            travelers = validated_data['travelers']
            travel_style = validated_data['travel_style']
            
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

            # Ghi nhận analytics ở background để không chặn phản hồi preview.
            ghi_nhan_yeu_cau_lo_trinh_async(
                user_id=request.user.pk if request.user.is_authenticated else None,
                loai_yeu_cau=YeuCauLoTrinh.LoaiYeuCau.PREVIEW,
                trang_thai=YeuCauLoTrinh.TrangThaiXuLy.THANH_CONG,
                diem_di=origin,
                diem_den=destination,
                so_ngay_di=days,
                so_nguoi=travelers,
                ngan_sach_du_kien=result_state.get('budget', {}).get('total_vnd'),
                du_lieu_phan_hoi={
                    'transport': result_state.get('transport', {}),
                    'budget_estimate': result_state.get('budget', {}),
                    'travel_style': travel_style,
                    'preview_mode': True,
                },
            )
            
            return Response(serializer.data, status=status.HTTP_200_OK)
            
        except ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            try:
                ghi_nhan_yeu_cau_lo_trinh_async(
                    user_id=request.user.pk if request.user.is_authenticated else None,
                    loai_yeu_cau=YeuCauLoTrinh.LoaiYeuCau.PREVIEW,
                    trang_thai=YeuCauLoTrinh.TrangThaiXuLy.THAT_BAI,
                    diem_di=locals().get('origin') or request.query_params.get('origin', ''),
                    diem_den=locals().get('destination') or request.query_params.get('destination', ''),
                    so_ngay_di=locals().get('days') or request.query_params.get('days'),
                    so_nguoi=locals().get('travelers') or request.query_params.get('travelers'),
                    ngan_sach_du_kien=None,
                    du_lieu_phan_hoi={
                        'error_message': sanitize_sensitive_string(str(e)),
                        'error_type': e.__class__.__name__,
                        'travel_style': locals().get('travel_style') or request.query_params.get('travel_style', 'standard'),
                        'preview_mode': True,
                    },
                )
            except Exception:
                logger.exception("Không thể ghi analytics lỗi cho preview request")
            logger.error(f"Error in travel plan preview: {e}", exc_info=True)
            return Response({
                'error': sanitize_sensitive_string(str(e))
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _build_travel_plan_state(validated_data: Dict[str, Any]) -> Dict[str, Any]:
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

    return state


def _build_streaming_response_data(
    request,
    validated_data: Dict[str, Any],
    result_state: Dict[str, Any],
    workflow_engine: str,
    analytics_request_id: Optional[int] = None,
) -> Dict[str, Any]:
    structured_output = result_state.get('itinerary_json')
    weather_snapshot = _fetch_destination_weather(validated_data.get('destination'))

    saved_itinerary = None
    if request.user.is_authenticated:
        try:
            from utils.itinerary_saver import save_itinerary_to_database
            saved_itinerary = save_itinerary_to_database(
                itinerary_data=result_state.get('itinerary', {}),
                user=request.user,
                destination=validated_data.get('destination'),
                origin=validated_data.get('origin'),
                start_date=validated_data['start_date'].strftime('%Y-%m-%d'),
                days=validated_data['days'],
                travelers=validated_data['travelers'],
                travel_style=validated_data.get('travel_style', 'standard'),
                total_cost=result_state.get('budget', {}).get('total_vnd', 0)
            )
        except Exception as e:
            logger.error(f"Error saving itinerary to database: {e}", exc_info=True)

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
            'structured_output': structured_output,
            'weather': weather_snapshot,
        },
        'costs': {
            'transport': result_state.get('transport_cost', 0),
            'accommodation': result_state.get('accommodation_cost', 0),
            'activities': result_state.get('activities_cost', 0),
            'dining': result_state.get('dining_cost', 0),
            'total': result_state.get('budget', {}).get('total_vnd', 0),
        },
        'saved_itinerary_id': saved_itinerary.maLichTrinh if saved_itinerary else None,
        'thread_id': result_state.get('thread_id'),
        'workflow_engine': workflow_engine,
        'telemetry': {
            'analytics_request_id': analytics_request_id,
            'duration_ms': result_state.get('workflow_duration_ms', 0),
            'llm_token_usage': result_state.get('llm_token_usage', {'total': 0}),
            'server_flags': result_state.get('server_flags', {}),
            'map_completion_status': result_state.get('map_completion_status', {}),
        },
        'timestamp': timezone.now(),
    }

    cap_nhat_yeu_cau_lo_trinh(
        analytics_request_id,
        trang_thai=YeuCauLoTrinh.TrangThaiXuLy.THANH_CONG,
        merge_du_lieu_phan_hoi={
            'transport': result_state.get('transport', {}),
            'flight': result_state.get('flight'),
            'budget': result_state.get('budget', {}),
            'costs': response_data['costs'],
            'selected_hotel': result_state.get('selected_hotel'),
            'activities_count': len(result_state.get('activities', [])),
            'restaurants_count': len(result_state.get('restaurants', [])),
            'saved_itinerary_id': saved_itinerary.maLichTrinh if saved_itinerary else None,
            'travel_style': validated_data.get('travel_style', 'standard'),
            'workflow_engine': workflow_engine,
            'thread_id': result_state.get('thread_id'),
            'duration_ms': result_state.get('workflow_duration_ms', 0),
            'llm_token_usage': result_state.get('llm_token_usage', {'total': 0}),
            'server_flags': result_state.get('server_flags', {}),
            'map_completion_status': result_state.get('map_completion_status', {}),
            'completed_steps': result_state.get('completed_steps', []),
            'completed_at': _iso_timestamp(),
        },
    )

    return response_data


def _sse_message(event_name: str, payload: Dict[str, Any]) -> str:
    return f"event: {event_name}\ndata: {json.dumps(sanitize_sensitive_data(payload), ensure_ascii=False, default=str)}\n\n"


def _stream_travel_plan_events(thread_id: str):
    last_event_id = 0
    idle_cycles = 0

    yield _sse_message('connected', {
        'thread_id': thread_id,
        'message': 'Đã kết nối luồng cập nhật lịch trình.',
    })

    while True:
        run_state = get_run(thread_id)
        if not run_state:
            yield _sse_message('error', {
                'thread_id': thread_id,
                'message': 'Không tìm thấy tiến trình lập kế hoạch cần khôi phục.',
            })
            break

        events = get_events_since(thread_id, last_event_id)
        if events:
            idle_cycles = 0
            for event in events:
                last_event_id = int(event.get('id', last_event_id))
                yield _sse_message(event.get('event', 'message'), event.get('data', {}))
        else:
            idle_cycles += 1
            yield ': keep-alive\n\n'

        if run_state.get('status') in {'completed', 'failed'}:
            break

        if idle_cycles > 300:
            yield _sse_message('error', {
                'thread_id': thread_id,
                'message': 'Phiên phát trực tiếp đã hết thời gian chờ. Hãy kết nối lại để tiếp tục nhận tiến độ.',
            })
            break

        time.sleep(1)


def _safe_stream_travel_plan_events(thread_id: str):
    try:
        for chunk in _stream_travel_plan_events(thread_id):
            yield chunk
    except Exception as exc:
        safe_message = sanitize_sensitive_string(str(exc)) or 'Hệ thống AI gặp sự cố. Vui lòng thử lại.'
        logger.error("SSE streaming error for thread_id=%s: %s", thread_id, safe_message, exc_info=True)
        fail_run(thread_id, 'Hệ thống AI gặp sự cố. Vui lòng thử lại.')
        yield _sse_message('error', {
            'thread_id': thread_id,
            'message': 'Hệ thống AI gặp sự cố. Vui lòng thử lại.',
        })
    finally:
        release_streaming_connections()


def _execute_travel_plan_run(request, validated_data: Dict[str, Any], thread_id: str) -> None:
    state = _build_travel_plan_state(validated_data)
    state['thread_id'] = thread_id
    state['workflow_started_at'] = _iso_timestamp()
    state['llm_token_usage'] = {'total': 0}
    state['server_flags'] = {
        'use_langgraph_workflow': os.environ.get("USE_LANGGRAPH_WORKFLOW", "False").lower() == "true",
        'sse_enabled': True,
    }
    state['map_completion_status'] = {
        'activities_ready': False,
        'restaurants_ready': False,
        'itinerary_ready': False,
    }
    use_langgraph_workflow = os.environ.get("USE_LANGGRAPH_WORKFLOW", "False").lower() == "true"
    started_at = time.perf_counter()
    analytics_record = tao_ban_ghi_yeu_cau_lo_trinh(
        user_id=request.user.pk if request.user.is_authenticated else None,
        loai_yeu_cau=YeuCauLoTrinh.LoaiYeuCau.TAO_KE_HOACH,
        trang_thai=YeuCauLoTrinh.TrangThaiXuLy.TU_CACHE if get_run(thread_id) and get_run(thread_id).get("status") == "completed" else YeuCauLoTrinh.TrangThaiXuLy.THANH_CONG,
        diem_di=validated_data.get('origin', ''),
        diem_den=validated_data.get('destination', ''),
        so_ngay_di=validated_data.get('days'),
        so_nguoi=validated_data.get('travelers'),
        ngan_sach_du_kien=validated_data.get('budget'),
        ngay_khoi_hanh_du_kien=validated_data.get('start_date'),
        du_lieu_phan_hoi={
            'thread_id': thread_id,
            'workflow_started_at': state['workflow_started_at'],
            'travel_style': validated_data.get('travel_style', 'standard'),
            'server_flags': state['server_flags'],
            'completed_steps': [],
            'current_step': 'transport',
            'map_completion_status': state['map_completion_status'],
        },
    )
    state['analytics_request_id'] = analytics_record.maYeuCau if analytics_record else None

    async def progress_callback(event_type: str, payload: Dict[str, Any]):
        completed_steps = payload.get('completed_steps')
        step = payload.get('step', 'planning')
        message = payload.get('message', 'Đang xử lý yêu cầu lập kế hoạch.')
        progress_extra = {
            key: value
            for key, value in payload.items()
            if key not in {'step', 'message', 'completed_steps'}
        }
        if step == 'activities':
            state['map_completion_status'] = {
                'activities_ready': bool(progress_extra.get('activities_ready') or state.get('activities')),
                'restaurants_ready': bool(progress_extra.get('restaurants_ready') or state.get('restaurants')),
                'itinerary_ready': bool(state.get('plan_ready')),
            }
        elif event_type == 'day_ready':
            state['map_completion_status'] = {
                **(state.get('map_completion_status') or {}),
                'itinerary_ready': True,
            }
        record_progress(
            thread_id,
            step=step,
            message=message,
            completed_steps=completed_steps if isinstance(completed_steps, list) else None,
            extra=progress_extra,
        )
        cap_nhat_yeu_cau_lo_trinh(
            state.get('analytics_request_id'),
            merge_du_lieu_phan_hoi={
                'thread_id': thread_id,
                'current_step': step,
                'last_message': message,
                'completed_steps': completed_steps if isinstance(completed_steps, list) else state.get('completed_steps', []),
                'last_event_type': event_type,
                'map_completion_status': state.get('map_completion_status', {}),
                'last_progress_at': _iso_timestamp(),
                'active_server_flags': state.get('server_flags', {}),
            },
        )
        if event_type == 'day_ready':
            append_event(thread_id, 'day_ready', {
                'thread_id': thread_id,
                **payload,
            })

    async def run_orchestrator_plan():
        from agents.travel_agents.orchestrator_agent import OrchestratorAgent

        orchestrator = OrchestratorAgent()
        return await orchestrator.execute(state, progress_callback=progress_callback)

    async def run_langgraph_plan():
        from agents.langgraph_workflow import LangGraphTravelWorkflow

        workflow = LangGraphTravelWorkflow()
        return await workflow.run(
            state,
            config={
                'configurable': {
                    'thread_id': thread_id
                }
            },
            progress_callback=progress_callback,
        )

    try:
        set_running(thread_id, current_step='transport')
        workflow_engine = "orchestrator"

        if use_langgraph_workflow:
            try:
                result_state = asyncio.run(run_langgraph_plan())
                if result_state.get('status') == 'error':
                    raise RuntimeError(result_state.get('error', 'LangGraph workflow returned error state'))
                workflow_engine = "langgraph"
            except Exception as langgraph_err:
                logger.warning(
                    "LangGraph workflow failed, falling back to orchestrator: %s",
                    langgraph_err,
                    exc_info=True
                )
                append_event(thread_id, 'progress', {
                    'thread_id': thread_id,
                    'step': 'fallback',
                    'message': 'Luồng LangGraph gặp sự cố, hệ thống đang chuyển sang lớp điều phối dự phòng.',
                    'completed_steps': [],
                })
                result_state = asyncio.run(run_orchestrator_plan())
                workflow_engine = "orchestrator_fallback"
        else:
            result_state = asyncio.run(run_orchestrator_plan())

        if result_state.get('status') == 'error':
            raise RuntimeError(result_state.get('error', 'Đã xảy ra lỗi không xác định trong quá trình lập kế hoạch.'))

        result_state['thread_id'] = thread_id
        result_state['workflow_duration_ms'] = int((time.perf_counter() - started_at) * 1000)
        result_state['map_completion_status'] = {
            **(result_state.get('map_completion_status') or {}),
            'itinerary_ready': bool(result_state.get('plan_ready') or result_state.get('itinerary_json')),
        }
        response_data = _build_streaming_response_data(
            request,
            validated_data,
            result_state,
            workflow_engine,
            analytics_request_id=state.get('analytics_request_id'),
        )
        complete_run(thread_id, response_data=response_data, workflow_engine=workflow_engine)
    except Exception as e:
        duration_ms = int((time.perf_counter() - started_at) * 1000)
        cap_nhat_yeu_cau_lo_trinh(
            state.get('analytics_request_id'),
            trang_thai=YeuCauLoTrinh.TrangThaiXuLy.THAT_BAI,
            merge_du_lieu_phan_hoi={
                'thread_id': thread_id,
                'duration_ms': duration_ms,
                'error_message': sanitize_sensitive_string(str(e)),
                'error_type': e.__class__.__name__,
                'completed_steps': state.get('completed_steps', []),
                'current_step': state.get('current_step'),
                'active_server_flags': state.get('server_flags', {}),
                'map_completion_status': state.get('map_completion_status', {}),
                'failed_at': _iso_timestamp(),
            },
        )
        try:
            ghi_nhan_yeu_cau_lo_trinh_async(
                user_id=request.user.pk if request.user.is_authenticated else None,
                loai_yeu_cau=YeuCauLoTrinh.LoaiYeuCau.TAO_KE_HOACH,
                trang_thai=YeuCauLoTrinh.TrangThaiXuLy.THAT_BAI,
                diem_di=validated_data.get('origin', ''),
                diem_den=validated_data.get('destination', ''),
                so_ngay_di=validated_data.get('days'),
                so_nguoi=validated_data.get('travelers'),
                ngan_sach_du_kien=validated_data.get('budget'),
                ngay_khoi_hanh_du_kien=validated_data.get('start_date'),
                du_lieu_phan_hoi={
                    'error_message': sanitize_sensitive_string(str(e)),
                    'error_type': e.__class__.__name__,
                    'travel_style': validated_data.get('travel_style', 'standard'),
                    'use_langgraph_workflow': os.environ.get("USE_LANGGRAPH_WORKFLOW", "False"),
                    'thread_id': thread_id,
                },
            )
        except Exception:
            logger.exception("KhÃ´ng thá»ƒ ghi analytics lá»—i cho travel-plans request")
        logger.error(f"Error creating travel plan: {e}", exc_info=True)
        fail_run(thread_id, sanitize_sensitive_string(str(e)) or 'Hệ thống AI gặp sự cố. Vui lòng thử lại.')


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
            use_langgraph_workflow = os.environ.get("USE_LANGGRAPH_WORKFLOW", "False").lower() == "true"

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
            
            orchestrator = OrchestratorAgent()
            workflow_engine = "orchestrator"

            async def run_orchestrator_plan():
                return await orchestrator.execute(state)

            async def run_langgraph_plan():
                from agents.langgraph_workflow import LangGraphTravelWorkflow

                workflow = LangGraphTravelWorkflow()
                thread_id = (
                    f"travel-plan-{request.user.pk}-{validated_data['start_date'].strftime('%Y%m%d')}"
                    if request.user.is_authenticated
                    else f"travel-plan-guest-{validated_data['start_date'].strftime('%Y%m%d')}"
                )
                return await workflow.run(
                    state,
                    config={
                        'configurable': {
                            'thread_id': thread_id
                        }
                    }
                )
            
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        if use_langgraph_workflow:
                            try:
                                future = executor.submit(asyncio.run, run_langgraph_plan())
                                result_state = future.result(timeout=120)
                                if result_state.get('status') == 'error':
                                    raise RuntimeError(result_state.get('error', 'LangGraph workflow returned error state'))
                                workflow_engine = "langgraph"
                            except Exception as langgraph_err:
                                logger.warning(
                                    "LangGraph workflow failed, falling back to orchestrator: %s",
                                    langgraph_err,
                                    exc_info=True
                                )
                                future = executor.submit(asyncio.run, run_orchestrator_plan())
                                result_state = future.result(timeout=120)
                                workflow_engine = "orchestrator_fallback"
                        else:
                            future = executor.submit(asyncio.run, run_orchestrator_plan())
                            result_state = future.result(timeout=120)  # 2 minutes timeout
                else:
                    if use_langgraph_workflow:
                        try:
                            result_state = loop.run_until_complete(run_langgraph_plan())
                            if result_state.get('status') == 'error':
                                raise RuntimeError(result_state.get('error', 'LangGraph workflow returned error state'))
                            workflow_engine = "langgraph"
                        except Exception as langgraph_err:
                            logger.warning(
                                "LangGraph workflow failed, falling back to orchestrator: %s",
                                langgraph_err,
                                exc_info=True
                            )
                            result_state = loop.run_until_complete(run_orchestrator_plan())
                            workflow_engine = "orchestrator_fallback"
                    else:
                        result_state = loop.run_until_complete(run_orchestrator_plan())
            except RuntimeError:
                if use_langgraph_workflow:
                    try:
                        result_state = asyncio.run(run_langgraph_plan())
                        if result_state.get('status') == 'error':
                            raise RuntimeError(result_state.get('error', 'LangGraph workflow returned error state'))
                        workflow_engine = "langgraph"
                    except Exception as langgraph_err:
                        logger.warning(
                            "LangGraph workflow failed, falling back to orchestrator: %s",
                            langgraph_err,
                            exc_info=True
                        )
                        result_state = asyncio.run(run_orchestrator_plan())
                        workflow_engine = "orchestrator_fallback"
                else:
                    result_state = asyncio.run(run_orchestrator_plan())
            
            # Check for errors
            if result_state.get('status') == 'error':
                return Response({
                    'error': result_state.get('error', 'Unknown error occurred')
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            structured_output = result_state.get('itinerary_json')
            weather_snapshot = _fetch_destination_weather(validated_data.get('destination'))
            
            # Save itinerary to database if user is authenticated
            saved_itinerary = None
            if request.user.is_authenticated:
                try:
                    from utils.itinerary_saver import save_itinerary_to_database
                    saved_itinerary = save_itinerary_to_database(
                        itinerary_data=result_state.get('itinerary', {}),
                        user=request.user,
                        destination=validated_data.get('destination'),
                        origin=validated_data.get('origin'),
                        start_date=validated_data['start_date'].strftime('%Y-%m-%d'),
                        days=validated_data['days'],
                        travelers=validated_data['travelers'],
                        travel_style=validated_data.get('travel_style', 'standard'),
                        total_cost=result_state.get('budget', {}).get('total_vnd', 0)
                    )
                    if saved_itinerary:
                        logger.info(f"Saved itinerary {saved_itinerary.maLichTrinh} to database")
                except Exception as e:
                    logger.error(f"Error saving itinerary to database: {e}", exc_info=True)
                    # Don't fail the request if saving fails
            
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
                    'structured_output': structured_output,
                    'weather': weather_snapshot,
                },
                'costs': {
                    'transport': result_state.get('transport_cost', 0),
                    'accommodation': result_state.get('accommodation_cost', 0),
                    'activities': result_state.get('activities_cost', 0),
                    'dining': result_state.get('dining_cost', 0),
                    'total': result_state.get('budget', {}).get('total_vnd', 0),
                },
                'saved_itinerary_id': saved_itinerary.maLichTrinh if saved_itinerary else None,
                'timestamp': timezone.now()
            }

            # Ghi nhận yêu cầu hoàn chỉnh để phục vụ tracking hành vi.
            ghi_nhan_yeu_cau_lo_trinh_async(
                user_id=request.user.pk if request.user.is_authenticated else None,
                loai_yeu_cau=YeuCauLoTrinh.LoaiYeuCau.TAO_KE_HOACH,
                trang_thai=YeuCauLoTrinh.TrangThaiXuLy.THANH_CONG,
                diem_di=validated_data['origin'],
                diem_den=validated_data['destination'],
                so_ngay_di=validated_data['days'],
                so_nguoi=validated_data['travelers'],
                ngan_sach_du_kien=validated_data.get('budget') or result_state.get('budget', {}).get('total_vnd'),
                ngay_khoi_hanh_du_kien=validated_data['start_date'],
                du_lieu_phan_hoi={
                    'transport': result_state.get('transport', {}),
                    'flight': result_state.get('flight'),
                    'budget': result_state.get('budget', {}),
                    'costs': response_data['costs'],
                    'selected_hotel': result_state.get('selected_hotel'),
                    'activities_count': len(result_state.get('activities', [])),
                    'restaurants_count': len(result_state.get('restaurants', [])),
                    'saved_itinerary_id': saved_itinerary.maLichTrinh if saved_itinerary else None,
                    'travel_style': validated_data.get('travel_style', 'standard'),
                    'workflow_engine': workflow_engine,
                },
            )
            
            response_serializer = TravelPlanResponseSerializer(response_data)
            
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
            
        except ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            try:
                request_data = request.data if hasattr(request, 'data') else {}
                validated_data_local = locals().get('validated_data', {})
                ghi_nhan_yeu_cau_lo_trinh_async(
                    user_id=request.user.pk if request.user.is_authenticated else None,
                    loai_yeu_cau=YeuCauLoTrinh.LoaiYeuCau.TAO_KE_HOACH,
                    trang_thai=YeuCauLoTrinh.TrangThaiXuLy.THAT_BAI,
                    diem_di=validated_data_local.get('origin') or request_data.get('origin', ''),
                    diem_den=validated_data_local.get('destination') or request_data.get('destination', ''),
                    so_ngay_di=validated_data_local.get('days') or request_data.get('days'),
                    so_nguoi=validated_data_local.get('travelers') or request_data.get('travelers'),
                    ngan_sach_du_kien=validated_data_local.get('budget') or request_data.get('budget'),
                    ngay_khoi_hanh_du_kien=validated_data_local.get('start_date') or request_data.get('start_date'),
                    du_lieu_phan_hoi={
                        'error_message': str(e),
                        'traceback': traceback.format_exc(),
                        'travel_style': validated_data_local.get('travel_style') or request_data.get('travel_style', 'standard'),
                        'use_langgraph_workflow': os.environ.get("USE_LANGGRAPH_WORKFLOW", "False"),
                    },
                )
            except Exception:
                logger.exception("Không thể ghi analytics lỗi cho travel-plans request")
            logger.error(f"Error creating travel plan: {e}", exc_info=True)
            return Response({
                'error': str(e)
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


class TravelPlanCreateView(APIView):
    """POST /api/v1/travel-plans/ voi SSE streaming."""

    permission_classes = [AllowAny]

    def post(self, request):
        try:
            auth_response = _require_authenticated_request(request)
            if auth_response is not None:
                return auth_response

            serializer = TravelPlanRequestSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            validated_data = serializer.validated_data
            thread_id = create_thread_id(request.data.get('thread_id'))
            client_ip = get_client_ip(request)
            user_id = request.user.id if request.user.is_authenticated else None
            existing_run = get_run(thread_id)

            if existing_run and not _is_authorized_for_run(request, existing_run):
                return Response(
                    {
                        'error': 'Bạn không có quyền truy cập tiến trình lập kế hoạch này.'
                    },
                    status=status.HTTP_403_FORBIDDEN,
                )

            if not existing_run:
                allowed, _rate_info = check_generation_rate_limit(
                    user_id=user_id,
                    client_ip=client_ip,
                )
                if not allowed:
                    return Response(
                        {
                            'error': 'Bạn đã vượt quá hạn mức thử nghiệm AI. Vui lòng quay lại sau.'
                        },
                        status=status.HTTP_429_TOO_MANY_REQUESTS,
                    )

                initialize_run(
                    thread_id=thread_id,
                    owner_key=f"user:{user_id}" if user_id else f"ip:{client_ip}",
                    request_payload=_build_travel_plan_state(validated_data),
                    workflow_engine='langgraph' if os.environ.get("USE_LANGGRAPH_WORKFLOW", "False").lower() == "true" else 'orchestrator',
                )
                worker = threading.Thread(
                    target=_execute_travel_plan_run,
                    args=(request, validated_data, thread_id),
                    daemon=True,
                )
                worker.start()

            response = StreamingHttpResponse(
                _safe_stream_travel_plan_events(thread_id),
                content_type='text/event-stream; charset=utf-8',
                status=status.HTTP_200_OK,
            )
            response['Cache-Control'] = 'no-cache'
            response['X-Accel-Buffering'] = 'no'
            return response
        except ValidationError as e:
            return Response(e.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Error creating travel plan stream: {e}", exc_info=True)
            return Response(
                {
                    'error': sanitize_sensitive_string(str(e))
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class TravelPlanStreamView(APIView):
    """GET /api/v1/travel-plans/stream/<thread_id>/ de reconnect."""

    permission_classes = [AllowAny]

    def get(self, request, thread_id: str):
        auth_response = _require_authenticated_request(request)
        if auth_response is not None:
            return auth_response

        run_state = get_run(thread_id)
        if not run_state:
            return Response(
                {
                    'error': 'Không tìm thấy tiến trình lập kế hoạch cần khôi phục.'
                },
                status=status.HTTP_404_NOT_FOUND,
            )
        if not _is_authorized_for_run(request, run_state):
            return Response(
                {
                    'error': 'Bạn không có quyền truy cập tiến trình lập kế hoạch này.'
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        response = StreamingHttpResponse(
            _safe_stream_travel_plan_events(thread_id),
            content_type='text/event-stream; charset=utf-8',
            status=status.HTTP_200_OK,
        )
        response['Cache-Control'] = 'no-cache'
        response['X-Accel-Buffering'] = 'no'
        return response


def _validate_full_travel_plan_output(payload: Dict[str, Any]) -> FullTravelPlanOutput:
    """Validate payload tu frontend theo Pydantic schema cua planning output."""
    if hasattr(FullTravelPlanOutput, "model_validate"):
        return FullTravelPlanOutput.model_validate(payload)
    return FullTravelPlanOutput.parse_obj(payload)


def _dump_full_travel_plan_output(plan: FullTravelPlanOutput) -> Dict[str, Any]:
    """Tuong thich Pydantic v1/v2 khi can dump ve dict."""
    if hasattr(plan, "model_dump"):
        return plan.model_dump()
    return plan.dict()


def _extract_plan_payload(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Chap nhan ca payload raw FullTravelPlanOutput va dang wrapper {plan: ...}."""
    plan_payload = request_data.get("plan")
    if isinstance(plan_payload, dict) and "trip_overview" in plan_payload:
        return plan_payload
    return request_data


def _find_tinh_thanh_by_name(destination: Optional[str]) -> Optional[TinhThanh]:
    """Co gang tim TinhThanh theo ten diem den, fail-safe neu khong match duoc."""
    if not destination:
        return None

    destination_clean = destination.strip()
    if not destination_clean:
        return None

    exact_match = TinhThanh.objects.filter(tenTinhThanh__iexact=destination_clean).first()
    if exact_match:
        return exact_match

    return TinhThanh.objects.filter(tenTinhThanh__icontains=destination_clean).first()


def _resolve_destination_coordinates(destination: Optional[str]) -> Optional[Dict[str, float]]:
    """Lay toa do diem den uu tien tu TinhThanh, fallback qua geocoding."""
    tinh_thanh = _find_tinh_thanh_by_name(destination)
    if tinh_thanh and tinh_thanh.viDo is not None and tinh_thanh.kinhDo is not None:
        return {
            "lat": float(tinh_thanh.viDo),
            "lon": float(tinh_thanh.kinhDo),
        }

    if not destination:
        return None

    try:
        from tools.geo_tools import get_geo_tools

        geo_tools = get_geo_tools()
        geocoded = geo_tools.geocode(destination, country="VN")
        if geocoded and geocoded.get("lat") is not None and geocoded.get("lon") is not None:
            return {
                "lat": float(geocoded["lat"]),
                "lon": float(geocoded["lon"]),
            }
    except Exception:
        logger.warning("Khong resolve duoc toa do destination=%s de lay weather", destination, exc_info=True)

    return None


def _fetch_destination_weather(destination: Optional[str]) -> Optional[Dict[str, Any]]:
    """Lay snapshot weather backend-side de phuc vu integration flow."""
    coords = _resolve_destination_coordinates(destination)
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not coords or not api_key:
        return None

    try:
        response = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={
                "lat": coords["lat"],
                "lon": coords["lon"],
                "appid": api_key,
                "units": "metric",
                "lang": "vi",
            },
            timeout=8,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            return None
        payload["requested_destination"] = destination
        return payload
    except Exception:
        logger.warning("Khong the lay weather snapshot cho destination=%s", destination, exc_info=True)
        return None


def _extract_trip_dates(plan_payload: Dict[str, Any]) -> tuple[datetime.date, datetime.date]:
    """Lay ngay bat dau va ket thuc tu daily_itinerary."""
    daily_itinerary = plan_payload.get("daily_itinerary", [])
    if not daily_itinerary:
        raise ValueError("Payload khong co daily_itinerary de suy ra ngay di.")

    start_date = daily_itinerary[0].get("date")
    end_date = daily_itinerary[-1].get("date")

    if not start_date or not end_date:
        raise ValueError("Payload thieu date trong daily_itinerary.")

    start = datetime.strptime(start_date, "%Y-%m-%d").date()
    end = datetime.strptime(end_date, "%Y-%m-%d").date()
    return start, end


def _build_itinerary_title(destination: Optional[str], so_ngay: int) -> str:
    """Tao tieu de ngan gon cho LichTrinh moi."""
    if destination:
        return f"Lich trinh {so_ngay} ngay den {destination}"
    return f"Lich trinh {so_ngay} ngay"


def _safe_int(value: Any) -> Optional[int]:
    """Co gang ep kieu sang int, tra ve None neu that bai."""
    try:
        if value is None:
            return None
        if isinstance(value, str):
            cleaned = value.strip().replace(",", "")
            if not cleaned:
                return None
            return int(float(cleaned))
        return int(value)
    except (TypeError, ValueError):
        return None


def _build_place_lookup_maps(daily_itinerary: List[Dict[str, Any]]) -> tuple[Dict[int, DiaDiem], Dict[str, DiaDiem]]:
    """
    Tao 2 map de resolve place_id:
    - Theo PK so hoc neu AI tra ve ma DB that.
    - Theo ten activity_name de fallback neu AI tra ve ma ao nhu DD001.
    """
    numeric_place_ids = set()
    activity_names: List[str] = []

    for day in daily_itinerary:
        if not isinstance(day, dict):
            continue
        for timeline_item in day.get("timeline", []):
            if not isinstance(timeline_item, dict):
                continue
            place_id = _safe_int(timeline_item.get("place_id"))
            if place_id is not None:
                numeric_place_ids.add(place_id)

            activity_name = str(timeline_item.get("activity_name", "")).strip()
            if activity_name:
                activity_names.append(activity_name)

    place_by_id = DiaDiem.objects.in_bulk(numeric_place_ids) if numeric_place_ids else {}

    place_by_name: Dict[str, DiaDiem] = {}
    for activity_name in activity_names:
        normalized_name = activity_name.lower()
        if normalized_name in place_by_name:
            continue
        matched_place = DiaDiem.objects.filter(
            tenDiaDiem__icontains=activity_name,
            trangThai="active",
        ).first()
        if matched_place:
            place_by_name[normalized_name] = matched_place

    return place_by_id, place_by_name


def _resolve_timeline_place(
    timeline_item: Dict[str, Any],
    *,
    place_by_id: Dict[int, DiaDiem],
    place_by_name: Dict[str, DiaDiem],
) -> Optional[DiaDiem]:
    resolved_place: Optional[DiaDiem] = None
    numeric_place_id = _safe_int(timeline_item.get("place_id"))
    if numeric_place_id is not None:
        resolved_place = place_by_id.get(numeric_place_id)

    if resolved_place is None:
        activity_name = str(timeline_item.get("activity_name", "")).strip().lower()
        if activity_name:
            resolved_place = place_by_name.get(activity_name)

    return resolved_place


def _build_thoi_gian_tham_quan(timeline_item: Dict[str, Any]) -> str:
    time_start = str(timeline_item.get("time_start", "")).strip()
    time_end = str(timeline_item.get("time_end", "")).strip()
    if time_start and time_end:
        return f"{time_start} - {time_end}"
    return time_start or time_end or ""


def _build_timeline_ghi_chu(
    timeline_item: Dict[str, Any],
    *,
    day_theme: str,
) -> str:
    local_hint = str(timeline_item.get("local_hint", "") or "").strip()
    fallback = timeline_item.get("plan_b_fallback") or {}
    fallback_reason = ""
    if isinstance(fallback, dict):
        fallback_reason = str(fallback.get("reason", "") or "").strip()

    note_parts = [part for part in [day_theme.strip(), local_hint, fallback_reason] if part]
    return " | ".join(note_parts)[:1000]


def _upsert_junction_row(
    *,
    junction_model,
    parent_field_name: str,
    parent_instance,
    place: DiaDiem,
    ngay_tham_quan,
    thu_tu: int,
    timeline_item: Dict[str, Any],
    day_theme: str,
):
    lookup = {
        parent_field_name: parent_instance,
        "maDiaDiem": place,
        "ngayThamQuan": ngay_tham_quan,
    }
    defaults = {
        "thoiGianThamQuan": _build_thoi_gian_tham_quan(timeline_item),
        "thuTu": thu_tu,
        "chiPhiUocTinh": float(timeline_item.get("cost", 0) or 0),
        "ghiChu": _build_timeline_ghi_chu(timeline_item, day_theme=day_theme),
    }

    try:
        row, _created = junction_model.objects.update_or_create(
            **lookup,
            defaults=defaults,
        )
        return row
    except IntegrityError:
        existing_row = junction_model.objects.select_for_update().filter(**lookup).first()
        if not existing_row:
            raise
        for field_name, field_value in defaults.items():
            setattr(existing_row, field_name, field_value)
        existing_row.save(update_fields=list(defaults.keys()))
        return existing_row


def _persist_timeline_rows(
    *,
    junction_model,
    parent_field_name: str,
    parent_instance,
    daily_itinerary: List[Dict[str, Any]],
    place_by_id: Dict[int, DiaDiem],
    place_by_name: Dict[str, DiaDiem],
) -> int:
    persisted_keys = set()

    for day in daily_itinerary:
        if not isinstance(day, dict):
            continue

        ngay_tham_quan_str = day.get("date")
        if not ngay_tham_quan_str:
            logger.warning(
                "Bo qua daily_itinerary item vi thieu date khi luu %s cho parent=%s",
                junction_model.__name__,
                getattr(parent_instance, "pk", None),
            )
            continue

        ngay_tham_quan = datetime.strptime(ngay_tham_quan_str, "%Y-%m-%d").date()
        day_theme = str(day.get("theme", "") or "").strip()

        for index, timeline_item in enumerate(day.get("timeline", []), start=1):
            if not isinstance(timeline_item, dict):
                continue

            resolved_place = _resolve_timeline_place(
                timeline_item,
                place_by_id=place_by_id,
                place_by_name=place_by_name,
            )
            if resolved_place is None:
                logger.warning(
                    "Khong resolve duoc DiaDiem cho place_id=%s, activity_name=%s, bo qua khi luu %s",
                    timeline_item.get("place_id"),
                    timeline_item.get("activity_name"),
                    junction_model.__name__,
                )
                continue

            dedupe_key = (ngay_tham_quan, resolved_place.pk)
            _upsert_junction_row(
                junction_model=junction_model,
                parent_field_name=parent_field_name,
                parent_instance=parent_instance,
                place=resolved_place,
                ngay_tham_quan=ngay_tham_quan,
                thu_tu=index,
                timeline_item=timeline_item,
                day_theme=day_theme,
            )
            persisted_keys.add(dedupe_key)

    return len(persisted_keys)


def _save_structured_travel_plan_for_user(
    *,
    user,
    request_data: Dict[str, Any],
) -> Dict[str, Any]:
    """Validate structured travel plan payload and persist it atomically."""
    plan_payload = _extract_plan_payload(request_data)
    validated_plan = _validate_full_travel_plan_output(plan_payload)
    normalized_payload = _dump_full_travel_plan_output(validated_plan)

    start_date, end_date = _extract_trip_dates(normalized_payload)
    daily_itinerary = normalized_payload.get("daily_itinerary", [])
    budget_analytics = normalized_payload.get("budget_analytics", {})
    trip_overview = normalized_payload.get("trip_overview", {})

    destination = request_data.get("destination") or request_data.get("city") or ""
    mo_ta = request_data.get("description") or request_data.get("moTa") or ""
    travelers = _safe_int(request_data.get("travelers", request_data.get("soNguoi", 1))) or 1
    so_ngay = len(daily_itinerary)
    ngan_sach = (
        _safe_int(trip_overview.get("total_estimated_cost"))
        or _safe_int(request_data.get("budget"))
        or _safe_int(request_data.get("nganSach"))
        or 0
    )
    chi_phi_uoc_tinh = int(
        budget_analytics.get("accommodation_total", 0)
        + budget_analytics.get("transportation_total", 0)
        + budget_analytics.get("food_total", 0)
        + budget_analytics.get("activities_total", 0)
        + budget_analytics.get("emergency_buffer", 0)
    )

    tinh_thanh = _find_tinh_thanh_by_name(destination)
    tieu_de = request_data.get("title") or request_data.get("tieuDe") or _build_itinerary_title(
        destination=destination,
        so_ngay=so_ngay,
    )

    with transaction.atomic():
        lich_trinh = LichTrinh.objects.create(
            maNguoiDung=user,
            maTinhThanh=tinh_thanh,
            tieuDe=tieu_de,
            moTa=mo_ta[:1000],
            ngayBatDau=start_date,
            ngayKetThuc=end_date,
            soNgay=so_ngay,
            soNguoi=max(1, travelers),
            nganSach=ngan_sach,
            chiPhiUocTinh=chi_phi_uoc_tinh,
            trangThai="draft",
            laCongKhai=False,
            is_ai_generated=True,
            chiTiet=json.dumps(normalized_payload, ensure_ascii=False),
        )

        place_by_id, place_by_name = _build_place_lookup_maps(daily_itinerary)
        saved_user_rows = _persist_timeline_rows(
            junction_model=LichTrinhDiaDiem,
            parent_field_name="maLichTrinh",
            parent_instance=lich_trinh,
            daily_itinerary=daily_itinerary,
            place_by_id=place_by_id,
            place_by_name=place_by_name,
        )

    return {
        "status": "success",
        "message": "Da luu lich trinh thanh cong",
        "maLichTrinh": lich_trinh.maLichTrinh,
        "soDiaDiemDaLuu": saved_user_rows,
    }


class SaveTravelPlanView(APIView):
    """
    POST /api/v1/travel-plans/save/

    Luu ban ke hoach du lich da duoc generate vao bang LichTrinh cua nguoi dung.
    """

    permission_classes = [AllowAny]

    def post(self, request):
        """Validate payload structured output va luu vao DB."""
        try:
            auth_response = _require_authenticated_request(request)
            if auth_response is not None:
                return auth_response

            request_data = request.data if isinstance(request.data, dict) else {}
            payload = _save_structured_travel_plan_for_user(
                user=request.user,
                request_data=request_data,
            )

            return Response(
                payload,
                status=status.HTTP_201_CREATED,
            )

        except PydanticValidationError as exc:
            return Response(
                {
                    "error": "Payload khong dung schema FullTravelPlanOutput",
                    "details": exc.errors(),
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except IntegrityError as exc:
            logger.warning("Integrity guard triggered while saving travel plan: %s", sanitize_sensitive_string(str(exc)))
            return Response(
                {
                    "error": "Dữ liệu lịch trình đang được cập nhật đồng thời. Vui lòng thử lại.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as exc:
            logger.error("Error saving structured travel plan: %s", exc, exc_info=True)
            return Response(
                {
                    "error": sanitize_sensitive_string(str(exc)),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

