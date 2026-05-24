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
from pathlib import Path
from datetime import datetime, timedelta
from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.exceptions import ValidationError
from django.utils import timezone
from django.core.cache import cache
from django.db import transaction
import logging
import asyncio
import traceback
from typing import Dict, Any, List, Optional
from pydantic import ValidationError as PydanticValidationError
import requests

from apps.analytics.models import YeuCauLoTrinh
from apps.analytics.services import ghi_nhan_yeu_cau_lo_trinh_async
from apps.itineraries.models import LichTrinh, LichTrinhDiaDiem
from apps.places.models import TinhThanh, DiaDiem
from agents.state import FullTravelPlanOutput

# Add backend directory to path for agents, tools, etc.
# BASE_DIR (vivu_backend) is already added in settings.py, but adding here for safety
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

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
            days_str = request.query_params.get('days')
            days = int(days_str) if days_str else None
            travelers_str = request.query_params.get('travelers', '2')
            travelers = int(travelers_str) if travelers_str else 2
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
                    'error': 'Vui lòng nhập số người dưới 20 để đảm bảo chất lượng chuyến đi',
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
                    so_ngay_di=locals().get('days') or int(request.query_params.get('days', '1') or 1),
                    so_nguoi=locals().get('travelers') or int(request.query_params.get('travelers', '2') or 2),
                    ngan_sach_du_kien=None,
                    du_lieu_phan_hoi={
                        'error_message': str(e),
                        'traceback': traceback.format_exc(),
                        'travel_style': locals().get('travel_style') or request.query_params.get('travel_style', 'standard'),
                        'preview_mode': True,
                    },
                )
            except Exception:
                logger.exception("Không thể ghi analytics lỗi cho preview request")
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
                    so_ngay_di=validated_data_local.get('days') or int(request_data.get('days', 1) or 1),
                    so_nguoi=validated_data_local.get('travelers') or int(request_data.get('travelers', 1) or 1),
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


class SaveTravelPlanView(APIView):
    """
    POST /api/v1/travel-plans/save/

    Luu ban ke hoach du lich da duoc generate vao bang LichTrinh cua nguoi dung.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Validate payload structured output va luu vao DB."""
        try:
            request_data = request.data if isinstance(request.data, dict) else {}
            plan_payload = _extract_plan_payload(request_data)
            validated_plan = _validate_full_travel_plan_output(plan_payload)
            normalized_payload = _dump_full_travel_plan_output(validated_plan)

            start_date, end_date = _extract_trip_dates(normalized_payload)
            daily_itinerary = normalized_payload.get("daily_itinerary", [])
            budget_analytics = normalized_payload.get("budget_analytics", {})
            trip_overview = normalized_payload.get("trip_overview", {})

            destination = request_data.get("destination") or request_data.get("city") or ""
            mo_ta = request_data.get("description") or request_data.get("moTa") or ""
            travelers = int(request_data.get("travelers", request_data.get("soNguoi", 1)) or 1)
            so_ngay = len(daily_itinerary)
            ngan_sach = int(
                trip_overview.get("total_estimated_cost")
                or request_data.get("budget")
                or request_data.get("nganSach")
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
                    maNguoiDung=request.user,
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
                    chiTiet=json.dumps(normalized_payload, ensure_ascii=False),
                )

                place_by_id, place_by_name = _build_place_lookup_maps(daily_itinerary)
                lich_trinh_dia_diem_rows: List[LichTrinhDiaDiem] = []
                seen_place_per_day = set()

                for day in daily_itinerary:
                    if not isinstance(day, dict):
                        continue

                    ngay_tham_quan_str = day.get("date")
                    if not ngay_tham_quan_str:
                        logger.warning(
                            "Bo qua daily_itinerary item vi thieu date khi luu LichTrinhDiaDiem cho lich_trinh=%s",
                            lich_trinh.maLichTrinh,
                        )
                        continue

                    ngay_tham_quan = datetime.strptime(ngay_tham_quan_str, "%Y-%m-%d").date()

                    for index, timeline_item in enumerate(day.get("timeline", []), start=1):
                        if not isinstance(timeline_item, dict):
                            continue

                        resolved_place: Optional[DiaDiem] = None
                        numeric_place_id = _safe_int(timeline_item.get("place_id"))
                        if numeric_place_id is not None:
                            resolved_place = place_by_id.get(numeric_place_id)

                        if resolved_place is None:
                            activity_name = str(timeline_item.get("activity_name", "")).strip().lower()
                            if activity_name:
                                resolved_place = place_by_name.get(activity_name)

                        if resolved_place is None:
                            logger.warning(
                                "Khong resolve duoc DiaDiem cho place_id=%s, activity_name=%s, bo qua khi luu LichTrinhDiaDiem",
                                timeline_item.get("place_id"),
                                timeline_item.get("activity_name"),
                            )
                            continue

                        dedupe_key = (ngay_tham_quan, resolved_place.pk)
                        if dedupe_key in seen_place_per_day:
                            logger.info(
                                "Bo qua ban ghi trung DiaDiem=%s trong ngay=%s cho lich_trinh=%s",
                                resolved_place.pk,
                                ngay_tham_quan,
                                lich_trinh.maLichTrinh,
                            )
                            continue
                        seen_place_per_day.add(dedupe_key)

                        time_start = str(timeline_item.get("time_start", "")).strip()
                        time_end = str(timeline_item.get("time_end", "")).strip()
                        if time_start and time_end:
                            thoi_gian_tham_quan = f"{time_start} - {time_end}"
                        else:
                            thoi_gian_tham_quan = time_start or time_end or ""

                        lich_trinh_dia_diem_rows.append(
                            LichTrinhDiaDiem(
                                maLichTrinh=lich_trinh,
                                maDiaDiem=resolved_place,
                                ngayThamQuan=ngay_tham_quan,
                                thoiGianThamQuan=thoi_gian_tham_quan,
                                thuTu=index,
                                chiPhiUocTinh=float(timeline_item.get("cost", 0) or 0),
                                ghiChu=str(timeline_item.get("local_hint", "") or ""),
                            )
                        )

                if lich_trinh_dia_diem_rows:
                    LichTrinhDiaDiem.objects.bulk_create(lich_trinh_dia_diem_rows)

            return Response(
                {
                    "status": "success",
                    "message": "Da luu lich trinh thanh cong",
                    "maLichTrinh": lich_trinh.maLichTrinh,
                    "soDiaDiemDaLuu": len(lich_trinh_dia_diem_rows),
                },
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
        except Exception as exc:
            logger.error("Error saving structured travel plan: %s", exc, exc_info=True)
            return Response(
                {
                    "error": str(exc),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

