"""API Views for Vi Vu."""
from rest_framework import status, generics, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.views import TokenObtainPairView
from django.db.models import Count, Avg, Q
from django.core.cache import cache
import logging

from apps.users.models import NguoiDung, LichSuTimKiem
from apps.places.models import TinhThanh, DiaDiem, DanhGia
from apps.itineraries.models import LichTrinh
from .serializers import (
    RegisterSerializer, NguoiDungSerializer,
    DiaDiemListSerializer, DiaDiemDetailSerializer,
    LichTrinhSerializer, TinhThanhSerializer
)

# Import travel plan views
from .travel_plan_views import (
    TravelPlanPreviewView,
    TravelPlanCreateView,
    SaveTravelPlanView,
)
# Import 4-step workflow views
from .travel_plan_step_views import (
    Step1LocationSelectionView,
    Step2TravelInfoView,
    Step3BudgetSuggestionView,
    Step4ConfirmAndPlanView,
    Step4SaveItineraryView
)

logger = logging.getLogger(__name__)


class RegisterView(APIView):
    """User registration."""
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response({
                'message': 'Đăng ký thành công',
                'maNguoiDung': user.id,
                'tenDangNhap': user.username
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PlaceListView(generics.ListAPIView):
    """List places with search, ordering, and limit."""
    serializer_class = DiaDiemListSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['tenDiaDiem', 'moTa', 'diaChi']
    ordering_fields = ['danhGiaTrungBinh', 'soLuotDanhGia', 'soLuotXem', 'tenDiaDiem', 'ngayTao']
    ordering = ['-danhGiaTrungBinh', '-soLuotDanhGia']  # Default ordering
    pagination_class = None  # Disable pagination by default, handle in list() method
    
    def get_queryset(self):
        queryset = DiaDiem.objects.filter(trangThai='active').select_related('maTinhThanh').prefetch_related('hinh_anhs')
        
        # Filter by city
        city = self.request.query_params.get('city')
        if city:
            queryset = queryset.filter(maTinhThanh__tenTinhThanh__icontains=city)
        
        # Filter by category
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(loaiDiaDiem=category)
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        """Override to support limit parameter and save search history."""
        try:
            queryset = self.filter_queryset(self.get_queryset())
            
            # Get limit from query params
            limit = request.query_params.get('limit')
            if limit:
                try:
                    limit = int(limit)
                    queryset = queryset[:limit]
                except ValueError:
                    limit = None
            
            # Serialize data
            serializer = self.get_serializer(queryset, many=True)
            results = serializer.data
            
            # Build response
            response_data = {
                'count': len(results),
                'next': None,
                'previous': None,
                'results': results
            }
            
            # Save search history if user is authenticated and has search query
            if request.user.is_authenticated and 'search' in request.query_params:
                query = request.query_params.get('search', '')
                if query and len(results) > 0:
                    try:
                        LichSuTimKiem.objects.create(
                            maNguoiDung=request.user,
                            tuKhoa=query,
                            soKetQua=len(results),
                            maDiaDiem=results[0].get('maDiaDiem')
                        )
                    except Exception:
                        pass  # Ignore search history errors
            
            return Response(response_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error in PlaceListView.list: {e}", exc_info=True)
            # Return empty response instead of crashing
            return Response({
                'count': 0,
                'next': None,
                'previous': None,
                'results': []
            }, status=status.HTTP_200_OK)


class PlaceSearchView(APIView):
    """Search places and save history."""
    permission_classes = [AllowAny]
    
    def get(self, request):
        query = request.query_params.get('q', '').strip()
        
        if not query:
            return Response({
                'results': [],
                'count': 0,
                'query': ''
            })
        
        # Search places
        places = DiaDiem.objects.filter(
            trangThai='active'
        ).filter(
            Q(tenDiaDiem__icontains=query) |
            Q(moTa__icontains=query) |
            Q(diaChi__icontains=query) |
            Q(maTinhThanh__tenTinhThanh__icontains=query)
        ).select_related('maTinhThanh')[:50]
        
        serializer = DiaDiemListSerializer(places, many=True)
        results_data = serializer.data
        
        # Save search history if user is authenticated
        if request.user.is_authenticated:
            first_place = places.first()
            LichSuTimKiem.objects.create(
                maNguoiDung=request.user,
                tuKhoa=query,
                soKetQua=places.count(),
                maDiaDiem=first_place
            )
        
        return Response({
            'results': results_data,
            'count': places.count(),
            'query': query
        })


class PlaceDetailView(generics.RetrieveAPIView):
    """Place detail with images and reviews."""
    serializer_class = DiaDiemDetailSerializer
    permission_classes = [AllowAny]
    queryset = DiaDiem.objects.all()
    lookup_field = 'maDiaDiem'
    lookup_url_kwarg = 'id'


class PlaceEnrichedDetailView(APIView):
    """Place detail with web search enrichment."""
    permission_classes = [AllowAny]
    
    def get(self, request, id):
        """Get place detail with enriched information from web."""
        try:
            place = DiaDiem.objects.select_related('maTinhThanh').get(maDiaDiem=id)
        except DiaDiem.DoesNotExist:
            return Response({
                'error': 'Địa điểm không tồn tại'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Serialize place data
        serializer = DiaDiemDetailSerializer(place)
        place_data = serializer.data
        
        # Enrich with web search if requested
        search_web = request.query_params.get('search_web', 'false').lower() == 'true'
        if search_web:
            try:
                from .place_info_searcher import get_place_searcher
                searcher = get_place_searcher()
                place_data = searcher.enrich_place_data(place_data)
            except Exception as e:
                logger.warning(f"Failed to enrich place data: {e}")
                # Continue with original data
        
        return Response(place_data, status=status.HTTP_200_OK)


class PlaceCreateView(generics.CreateAPIView):
    """Create new place (auth required)."""
    serializer_class = DiaDiemDetailSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(maNguoiTao=self.request.user)


class ItineraryListView(generics.ListCreateAPIView):
    """List and create itineraries."""
    serializer_class = LichTrinhSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return LichTrinh.objects.filter(maNguoiDung=self.request.user).order_by('-ngayTao')
    
    def perform_create(self, serializer):
        serializer.save(maNguoiDung=self.request.user)


class RecentItinerariesView(APIView):
    """Get recent itineraries for dropdown (limit 5)"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        limit = int(request.query_params.get('limit', 5))
        itineraries = LichTrinh.objects.filter(
            maNguoiDung=request.user
        ).order_by('-ngayTao')[:limit]
        
        serializer = LichTrinhSerializer(itineraries, many=True)
        return Response({
            'status': 'success',
            'itineraries': serializer.data
        }, status=status.HTTP_200_OK)


class ItineraryDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Itinerary detail."""
    serializer_class = LichTrinhSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'maLichTrinh'
    lookup_url_kwarg = 'id'
    
    def get_queryset(self):
        return LichTrinh.objects.filter(maNguoiDung=self.request.user)


class AnalyticsView(APIView):
    """Basic analytics."""
    permission_classes = [AllowAny]
    
    def get(self, request):
        # Get statistics
        total_places = DiaDiem.objects.filter(trangThai='active').count()
        total_cities = TinhThanh.objects.count()
        total_reviews = DanhGia.objects.count()
        
        # Top rated places
        top_places = DiaDiem.objects.filter(
            trangThai='active'
        ).order_by('-danhGiaTrungBinh', '-soLuotDanhGia')[:10]
        
        # Places by category
        by_category = DiaDiem.objects.filter(
            trangThai='active'
        ).values('loaiDiaDiem').annotate(count=Count('maDiaDiem'))
        
        # Top cities
        top_cities = TinhThanh.objects.annotate(
            place_count=Count('dia_diems')
        ).order_by('-place_count')[:10]
        
        return Response({
            'statistics': {
                'total_places': total_places,
                'total_cities': total_cities,
                'total_reviews': total_reviews,
            },
            'top_places': DiaDiemListSerializer(top_places, many=True).data,
            'by_category': list(by_category),
            'top_cities': TinhThanhSerializer(top_cities, many=True).data,
        })


# ChatView được import từ chat_views.py để sử dụng RAG với Vector Database
from .chat_views import ChatView, ItineraryChatView
from .ml_recommendation_views import (
    ContentBasedRecommendationView,
    ClusterRecommendationView,
    CostPredictionView,
    HybridRecommendationView
)


def rate_limit_check(user_id: int, limit: int = 10, window: int = 60) -> bool:
    """Check if user has exceeded rate limit."""
    try:
        cache_key = f"rate_limit:user_{user_id}"
        count = cache.get(cache_key, 0)
        
        if count >= limit:
            return False
        
        cache.set(cache_key, count + 1, window)
        return True
    except Exception:
        # If cache fails, allow the request (fail open)
        logger.warning(f"Cache error in rate_limit_check for user {user_id}, allowing request")
        return True


class QueryView(APIView):
    """Interactive query endpoint with rate limiting."""
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        POST /api/v1/query/
        
        Payload:
        {
            "type": "query",
            "user_id": 1,
            "query_type": "chat" | "search",
            "query": "Câu hỏi của người dùng",
            "top_k": 6 (optional)
        }
        """
        try:
            # Rate limiting: 10 requests per minute per user
            user_id = request.user.id if request.user.is_authenticated else request.data.get('user_id', 0)
            if not rate_limit_check(user_id, limit=10, window=60):
                return Response({
                    'status': 'error',
                    'error': 'Rate limit exceeded. Maximum 10 requests per minute.',
                    'result': {},
                    'sources': []
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)
            
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))
            
            from agents.orchestrator import get_orchestrator
            
            # Prepare payload
            payload = {
                'type': request.data.get('type', 'query'),
                'user_id': user_id,
                'query_type': request.data.get('query_type', 'search'),
                'query': request.data.get('query', ''),
                'top_k': request.data.get('top_k', 6)
            }
            
            # Execute interactive workflow
            orchestrator = get_orchestrator()
            result = orchestrator.execute_interactive(payload)
            
            return Response(result, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Error in QueryView: {e}", exc_info=True)
            return Response({
                'status': 'error',
                'error': str(e),
                'result': {},
                'sources': []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GeneratePlanView(APIView):
    """
    Generate trip plan với 7 Agents (Legacy endpoint - backward compatibility)
    
    Sử dụng 7 agents mới:
    - Transport Agent
    - Flight Agent
    - Accommodation Agent
    - Activities Agent
    - Budget Agent
    - Planning Agent
    - Orchestrator Agent
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """
        POST /api/v1/plan/ (Legacy - sử dụng 7 agents mới)
        
        Payload:
        {
            "type": "plan",
            "query_type": "plan",
            "departure_location": "Hà Nội",
            "destinationLocations": ["Đà Nẵng"],
            "start_date": "2025-02-01",
            "end_date": "2025-02-05",
            "budget": 5000000,
            "interests": ["văn hóa", "ẩm thực"],
            "adults": 2,
            "duration": 5,
            "travel_style": "standard"
        }
        """
        try:
            # Rate limiting
            user_id = request.user.id if request.user.is_authenticated else request.data.get('user_id', 0)
            if not rate_limit_check(user_id, limit=10, window=60):
                return Response({
                    'status': 'error',
                    'error': 'Rate limit exceeded. Maximum 10 requests per minute.',
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)
            
            # Add backend directory to path for agents, etc.
            import sys
            from pathlib import Path
            BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
            if str(BACKEND_DIR) not in sys.path:
                sys.path.insert(0, str(BACKEND_DIR))
            
            # Import 7 agents orchestrator
            from agents.travel_agents.orchestrator_agent import OrchestratorAgent
            import asyncio
            
            # Extract data (support both old and new format)
            departure = request.data.get('departure_location') or request.data.get('origin')
            destinations = request.data.get('destinationLocations') or request.data.get('cities', [])
            destination = destinations[0] if destinations else request.data.get('destination')
            start_date = request.data.get('start_date')
            end_date = request.data.get('end_date')
            duration = request.data.get('duration') or request.data.get('days')
            adults = request.data.get('adults') or request.data.get('group_size', 2)
            travel_style = request.data.get('travel_style', 'standard')
            
            # Calculate days if not provided
            if not duration and start_date and end_date:
                from datetime import datetime
                start = datetime.strptime(start_date, '%Y-%m-%d')
                end = datetime.strptime(end_date, '%Y-%m-%d')
                duration = (end - start).days
            
            if not all([departure, destination, start_date, duration]):
                return Response({
                    'status': 'error',
                    'error': 'Missing required fields: departure_location, destination, start_date, duration'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Prepare state for 7 agents
            state = {
                'origin': departure,
                'destination': destination,
                'start_date': start_date,
                'days': duration,
                'travelers': adults,
                'travel_style': travel_style,
                'interests': request.data.get('interests', []),
                'rooms': request.data.get('rooms', 1),
            }
            
            if request.data.get('budget'):
                state['max_budget'] = request.data['budget']
            
            if request.data.get('selected_hotel'):
                state['selected_hotel'] = request.data['selected_hotel']
            
            # Execute orchestrator agent
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
                        result_state = future.result(timeout=120)
                else:
                    result_state = loop.run_until_complete(run_plan())
            except RuntimeError:
                result_state = asyncio.run(run_plan())
            
            # Format response (backward compatible)
            if result_state.get('status') == 'error':
                return Response({
                    'status': 'error',
                    'error': result_state.get('error', 'Unknown error'),
                    'result': {},
                    'sources': []
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            return Response({
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
            }, status=status.HTTP_200_OK)
        
        except Exception as e:
            logger.error(f"Error in GeneratePlanView: {e}", exc_info=True)
            return Response({
                'status': 'error',
                'error': str(e),
                'result': {},
                'sources': []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LocationSuggestionsView(APIView):
    """Get location suggestions for autocomplete."""
    permission_classes = [AllowAny]
    
    # 34 tỉnh/thành phố Việt Nam sau sáp nhập 2025 (theo Nghị quyết Quốc hội)
    # Bao gồm: 11 tỉnh/thành không sắp xếp + 23 đơn vị mới sau sáp nhập
    
    # 11 tỉnh/thành phố không thực hiện sắp xếp
    NO_REORGANIZATION = [
        'Tỉnh Cao Bằng',
        'Tỉnh Điện Biên',
        'Tỉnh Hà Tĩnh',
        'Tỉnh Lai Châu',
        'Tỉnh Lạng Sơn',
        'Tỉnh Nghệ An',
        'Tỉnh Quảng Ninh',
        'Tỉnh Thanh Hoá',
        'Tỉnh Sơn La',
        'Thành phố Hà Nội',
        'Thành phố Huế'
    ]
    
    # 23 đơn vị hành chính cấp tỉnh mới sau sáp nhập
    REORGANIZED_PROVINCES = [
        'Tỉnh Tuyên Quang',
        'Tỉnh Lào Cai',
        'Tỉnh Thái Nguyên',
        'Tỉnh Phú Thọ',
        'Tỉnh Bắc Ninh',
        'Tỉnh Hưng Yên',
        'Thành phố Hải Phòng',
        'Tỉnh Ninh Bình',
        'Tỉnh Quảng Trị',
        'Thành phố Đà Nẵng',
        'Tỉnh Quảng Ngãi',
        'Tỉnh Gia Lai',
        'Tỉnh Khánh Hòa',
        'Tỉnh Lâm Đồng',
        'Tỉnh Đắk Lắk',
        'Thành phố Hồ Chí Minh',
        'Tỉnh Đồng Nai',
        'Tỉnh Tây Ninh',
        'Thành phố Cần Thơ',
        'Tỉnh Vĩnh Long',
        'Tỉnh Đồng Tháp',
        'Tỉnh Cà Mau',
        'Tỉnh An Giang'
    ]
    
    # Tổng hợp 34 tỉnh/thành phố
    ALL_PROVINCES = NO_REORGANIZATION + REORGANIZED_PROVINCES
    
    # Mapping các tỉnh cũ đã sáp nhập -> hiển thị "Tỉnh cũ (thuộc Tỉnh mới)"
    # Format: 'Tên tỉnh cũ': 'Tên tỉnh cũ (thuộc Tỉnh mới)'
    MERGED_PROVINCES_MAPPING = {
        # Sáp nhập vào Tuyên Quang
        'Tỉnh Hà Giang': 'Hà Giang (thuộc Tỉnh Tuyên Quang)',
        'Hà Giang': 'Hà Giang (thuộc Tỉnh Tuyên Quang)',
        
        # Sáp nhập vào Lào Cai
        'Tỉnh Yên Bái': 'Yên Bái (thuộc Tỉnh Lào Cai)',
        'Yên Bái': 'Yên Bái (thuộc Tỉnh Lào Cai)',
        
        # Sáp nhập vào Thái Nguyên
        'Tỉnh Bắc Kạn': 'Bắc Kạn (thuộc Tỉnh Thái Nguyên)',
        'Bắc Kạn': 'Bắc Kạn (thuộc Tỉnh Thái Nguyên)',
        
        # Sáp nhập vào Phú Thọ
        'Tỉnh Vĩnh Phúc': 'Vĩnh Phúc (thuộc Tỉnh Phú Thọ)',
        'Vĩnh Phúc': 'Vĩnh Phúc (thuộc Tỉnh Phú Thọ)',
        'Tỉnh Hòa Bình': 'Hòa Bình (thuộc Tỉnh Phú Thọ)',
        'Hòa Bình': 'Hòa Bình (thuộc Tỉnh Phú Thọ)',
        
        # Sáp nhập vào Bắc Ninh
        'Tỉnh Bắc Giang': 'Bắc Giang (thuộc Tỉnh Bắc Ninh)',
        'Bắc Giang': 'Bắc Giang (thuộc Tỉnh Bắc Ninh)',
        
        # Sáp nhập vào Hưng Yên
        'Tỉnh Thái Bình': 'Thái Bình (thuộc Tỉnh Hưng Yên)',
        'Thái Bình': 'Thái Bình (thuộc Tỉnh Hưng Yên)',
        
        # Sáp nhập vào Hải Phòng
        'Tỉnh Hải Dương': 'Hải Dương (thuộc Thành phố Hải Phòng)',
        'Hải Dương': 'Hải Dương (thuộc Thành phố Hải Phòng)',
        
        # Sáp nhập vào Ninh Bình
        'Tỉnh Nam Định': 'Nam Định (thuộc Tỉnh Ninh Bình)',
        'Nam Định': 'Nam Định (thuộc Tỉnh Ninh Bình)',
        'Tỉnh Hà Nam': 'Hà Nam (thuộc Tỉnh Ninh Bình)',
        'Hà Nam': 'Hà Nam (thuộc Tỉnh Ninh Bình)',
        
        # Sáp nhập vào Quảng Trị
        'Tỉnh Quảng Bình': 'Quảng Bình (thuộc Tỉnh Quảng Trị)',
        'Quảng Bình': 'Quảng Bình (thuộc Tỉnh Quảng Trị)',
        
        # Sáp nhập vào Đà Nẵng
        'Tỉnh Quảng Nam': 'Quảng Nam (thuộc Thành phố Đà Nẵng)',
        'Quảng Nam': 'Quảng Nam (thuộc Thành phố Đà Nẵng)',
        
        # Sáp nhập vào Quảng Ngãi
        'Tỉnh Kon Tum': 'Kon Tum (thuộc Tỉnh Quảng Ngãi)',
        'Kon Tum': 'Kon Tum (thuộc Tỉnh Quảng Ngãi)',
        
        # Sáp nhập vào Gia Lai
        'Tỉnh Bình Định': 'Bình Định (thuộc Tỉnh Gia Lai)',
        'Bình Định': 'Bình Định (thuộc Tỉnh Gia Lai)',
        
        # Sáp nhập vào Khánh Hòa
        'Tỉnh Ninh Thuận': 'Ninh Thuận (thuộc Tỉnh Khánh Hòa)',
        'Ninh Thuận': 'Ninh Thuận (thuộc Tỉnh Khánh Hòa)',
        
        # Sáp nhập vào Lâm Đồng
        'Tỉnh Bình Thuận': 'Bình Thuận (thuộc Tỉnh Lâm Đồng)',
        'Bình Thuận': 'Bình Thuận (thuộc Tỉnh Lâm Đồng)',
        'Tỉnh Đắk Nông': 'Đắk Nông (thuộc Tỉnh Lâm Đồng)',
        'Đắk Nông': 'Đắk Nông (thuộc Tỉnh Lâm Đồng)',
        
        # Sáp nhập vào Đắk Lắk
        'Tỉnh Phú Yên': 'Phú Yên (thuộc Tỉnh Đắk Lắk)',
        'Phú Yên': 'Phú Yên (thuộc Tỉnh Đắk Lắk)',
        
        # Sáp nhập vào Thành phố Hồ Chí Minh
        'Tỉnh Bà Rịa - Vũng Tàu': 'Bà Rịa - Vũng Tàu (thuộc Thành phố Hồ Chí Minh)',
        'Bà Rịa Vũng Tàu': 'Bà Rịa - Vũng Tàu (thuộc Thành phố Hồ Chí Minh)',
        'Bà Rịa - Vũng Tàu': 'Bà Rịa - Vũng Tàu (thuộc Thành phố Hồ Chí Minh)',
        'Tỉnh Bình Dương': 'Bình Dương (thuộc Thành phố Hồ Chí Minh)',
        'Bình Dương': 'Bình Dương (thuộc Thành phố Hồ Chí Minh)',
        
        # Sáp nhập vào Đồng Nai
        'Tỉnh Bình Phước': 'Bình Phước (thuộc Tỉnh Đồng Nai)',
        'Bình Phước': 'Bình Phước (thuộc Tỉnh Đồng Nai)',
        
        # Sáp nhập vào Tây Ninh
        'Tỉnh Long An': 'Long An (thuộc Tỉnh Tây Ninh)',
        'Long An': 'Long An (thuộc Tỉnh Tây Ninh)',
        
        # Sáp nhập vào Cần Thơ
        'Tỉnh Sóc Trăng': 'Sóc Trăng (thuộc Thành phố Cần Thơ)',
        'Sóc Trăng': 'Sóc Trăng (thuộc Thành phố Cần Thơ)',
        'Tỉnh Hậu Giang': 'Hậu Giang (thuộc Thành phố Cần Thơ)',
        'Hậu Giang': 'Hậu Giang (thuộc Thành phố Cần Thơ)',
        
        # Sáp nhập vào Vĩnh Long
        'Tỉnh Bến Tre': 'Bến Tre (thuộc Tỉnh Vĩnh Long)',
        'Bến Tre': 'Bến Tre (thuộc Tỉnh Vĩnh Long)',
        'Tỉnh Trà Vinh': 'Trà Vinh (thuộc Tỉnh Vĩnh Long)',
        'Trà Vinh': 'Trà Vinh (thuộc Tỉnh Vĩnh Long)',
        
        # Sáp nhập vào Đồng Tháp
        'Tỉnh Tiền Giang': 'Tiền Giang (thuộc Tỉnh Đồng Tháp)',
        'Tiền Giang': 'Tiền Giang (thuộc Tỉnh Đồng Tháp)',
        
        # Sáp nhập vào Cà Mau
        'Tỉnh Bạc Liêu': 'Bạc Liêu (thuộc Tỉnh Cà Mau)',
        'Bạc Liêu': 'Bạc Liêu (thuộc Tỉnh Cà Mau)',
        
        # Sáp nhập vào An Giang
        'Tỉnh Kiên Giang': 'Kiên Giang (thuộc Tỉnh An Giang)',
        'Kiên Giang': 'Kiên Giang (thuộc Tỉnh An Giang)',
    }
    
    def get(self, request):
        query = request.query_params.get('q', '').strip()
        location_type = request.query_params.get('type', 'both')
        limit = int(request.query_params.get('limit', 10))
        
        suggestions = []
        query_lower = query.lower() if query else ''
        
        # For departure: return all 34 cities/provinces or filtered by query
        if location_type in ['departure', 'both']:
            if query:
                # Filter from full list (use original query for filtering, not lowercased)
                filtered_provinces = [
                    p for p in self.ALL_PROVINCES 
                    if query_lower in p.lower() or self._remove_tones(query_lower) in self._remove_tones(p.lower())
                ]
                
                # Check merged provinces mapping (tỉnh cũ đã sáp nhập)
                for old_name, new_name in self.MERGED_PROVINCES_MAPPING.items():
                    if query_lower in old_name.lower() or self._remove_tones(query_lower) in self._remove_tones(old_name.lower()):
                        if new_name not in filtered_provinces:
                            filtered_provinces.append(new_name)
                
                # Also try to match from database
                db_cities = TinhThanh.objects.filter(
                    Q(tenTinhThanh__icontains=query)
                ).values_list('tenTinhThanh', flat=True)
                
                # Normalize all database names
                db_cities_normalized = [self._normalize_province_name(city) for city in db_cities]
                
                # Normalize filtered provinces too
                filtered_provinces_normalized = [self._normalize_province_name(p) for p in filtered_provinces]
                
                # Combine and deduplicate intelligently
                all_matches = filtered_provinces_normalized + db_cities_normalized
                cities_list = self._deduplicate_suggestions(all_matches)
                cities_list = sorted(cities_list)[:limit]
            else:
                # If no query, return all 34 provinces
                cities_list = sorted(self.ALL_PROVINCES)
            
            # Add cities as simple strings (for autocomplete)
            suggestions.extend(cities_list[:limit])
        
        # For destination: return both cities and popular places
        if location_type in ['destination', 'both']:
            if query:
                # Add popular places
                places = DiaDiem.objects.filter(
                    trangThai='active'
                ).filter(
                    Q(tenDiaDiem__icontains=query) |
                    Q(maTinhThanh__tenTinhThanh__icontains=query)
                ).select_related('maTinhThanh').order_by(
                    '-danhGiaTrungBinh', '-soLuotDanhGia'
                )[:limit]
                
                for place in places:
                    city_name = place.maTinhThanh.tenTinhThanh if place.maTinhThanh else ''
                    suggestions.append(f'{place.tenDiaDiem} ({city_name})')
                
                # Also check merged provinces for destination search
                for old_name, new_name in self.MERGED_PROVINCES_MAPPING.items():
                    if query_lower in old_name.lower() or self._remove_tones(query_lower) in self._remove_tones(old_name.lower()):
                        if new_name not in suggestions:
                            suggestions.append(new_name)
        
        # Normalize all suggestions first
        normalized_suggestions = []
        for suggestion in suggestions:
            # If it's a place with city name format "Place (City)", normalize city part
            if ' (' in suggestion and suggestion.endswith(')'):
                # Keep place format, but could normalize city name if needed
                normalized_suggestions.append(suggestion)
            else:
                # It's a province/city name, normalize it
                normalized_suggestions.append(self._normalize_province_name(suggestion))
        
        # Remove duplicates intelligently - return simple array of strings
        unique_suggestions = self._deduplicate_suggestions(normalized_suggestions)[:limit]
        
        return Response({
            'suggestions': unique_suggestions
        })
    
    def _normalize_province_name(self, name: str) -> str:
        """
        Normalize province name to have full Vietnamese diacritics and consistent format.
        Maps common misspellings/no-diacritics to correct format.
        """
        # Mapping các tên không dấu hoặc sai -> tên có dấu đầy đủ
        NORMALIZATION_MAP = {
            # Common misspellings
            'Ninh Thuan': 'Ninh Thuận',
            'Quang Ninh': 'Quảng Ninh',
            'Tay Ninh': 'Tây Ninh',
            'Binh Duong': 'Bình Dương',
            'Dong Nai': 'Đồng Nai',
            'Thanh Hoa': 'Thanh Hóa',
            'Nghe An': 'Nghệ An',
            'Ha Noi': 'Hà Nội',
            'Hai Phong': 'Hải Phòng',
            'Ho Chi Minh': 'Hồ Chí Minh',
            'Da Nang': 'Đà Nẵng',
            'Khanh Hoa': 'Khánh Hòa',
            'Lam Dong': 'Lâm Đồng',
            'Dak Lak': 'Đắk Lắk',
            'Dak Nong': 'Đắk Nông',
            'Bac Ninh': 'Bắc Ninh',
            'Hung Yen': 'Hưng Yên',
            'Hai Duong': 'Hải Dương',
            'Nam Dinh': 'Nam Định',
            'Ha Nam': 'Hà Nam',
            'Quang Binh': 'Quảng Bình',
            'Quang Nam': 'Quảng Nam',
            'Quang Ngai': 'Quảng Ngãi',
            'Binh Dinh': 'Bình Định',
            'Binh Thuan': 'Bình Thuận',
            'Phu Yen': 'Phú Yên',
            'Ba Ria - Vung Tau': 'Bà Rịa - Vũng Tàu',
            'Ba Ria Vung Tau': 'Bà Rịa - Vũng Tàu',
            'Binh Phuoc': 'Bình Phước',
            'Long An': 'Long An',
            'Soc Trang': 'Sóc Trăng',
            'Hau Giang': 'Hậu Giang',
            'Ben Tre': 'Bến Tre',
            'Tra Vinh': 'Trà Vinh',
            'Tien Giang': 'Tiền Giang',
            'Bac Lieu': 'Bạc Liêu',
            'Kien Giang': 'Kiên Giang',
            'Ha Giang': 'Hà Giang',
            'Yen Bai': 'Yên Bái',
            'Bac Kan': 'Bắc Kạn',
            'Vinh Phuc': 'Vĩnh Phúc',
            'Hoa Binh': 'Hòa Bình',
            'Bac Giang': 'Bắc Giang',
            'Thai Binh': 'Thái Bình',
            'Thai Nguyen': 'Thái Nguyên',
            'Tuyen Quang': 'Tuyên Quang',
            'Lao Cai': 'Lào Cai',
            'Phu Tho': 'Phú Thọ',
            'Quang Tri': 'Quảng Trị',
            'Kon Tum': 'Kon Tum',
            'Gia Lai': 'Gia Lai',
            'Vinh Long': 'Vĩnh Long',
            'Dong Thap': 'Đồng Tháp',
            'Ca Mau': 'Cà Mau',
            'An Giang': 'An Giang',
            'Cao Bang': 'Cao Bằng',
            'Dien Bien': 'Điện Biên',
            'Ha Tinh': 'Hà Tĩnh',
            'Lai Chau': 'Lai Châu',
            'Lang Son': 'Lạng Sơn',
            'Son La': 'Sơn La',
        }
        
        # Remove prefix để so sánh
        name_clean = name.replace('Tỉnh ', '').replace('Thành phố ', '').strip()
        
        # Check normalization map
        if name_clean in NORMALIZATION_MAP:
            normalized = NORMALIZATION_MAP[name_clean]
            # Restore prefix if original had it
            if name.startswith('Tỉnh '):
                return f'Tỉnh {normalized}'
            elif name.startswith('Thành phố '):
                return f'Thành phố {normalized}'
            return normalized
        
        return name
    
    def _deduplicate_suggestions(self, suggestions: list) -> list:
        """
        Remove duplicates intelligently:
        - If both "Quang Ninh" and "Tỉnh Quảng Ninh" exist, keep only "Tỉnh Quảng Ninh"
        - If both "Ninh Thuan" and "Tỉnh Ninh Thuận" exist, keep only "Tỉnh Ninh Thuận"
        - Prefer format with "Tỉnh"/"Thành phố" prefix
        """
        seen_names = {}
        result = []
        
        for suggestion in suggestions:
            # Normalize first
            normalized = self._normalize_province_name(suggestion)
            
            # Extract base name (without prefix)
            base_name = normalized.replace('Tỉnh ', '').replace('Thành phố ', '').strip()
            
            # Remove any "(thuộc...)" for deduplication check
            base_name_clean = base_name.split(' (thuộc')[0].strip()
            
            # Check if we already have this province
            if base_name_clean in seen_names:
                # Prefer format with prefix "Tỉnh"/"Thành phố"
                existing = seen_names[base_name_clean]
                existing_has_prefix = existing.startswith('Tỉnh ') or existing.startswith('Thành phố ')
                current_has_prefix = normalized.startswith('Tỉnh ') or normalized.startswith('Thành phố ')
                
                # If current has prefix and existing doesn't, replace
                if current_has_prefix and not existing_has_prefix:
                    # Find and replace existing
                    idx = result.index(existing)
                    result[idx] = normalized
                    seen_names[base_name_clean] = normalized
                # If both have prefix or both don't, prefer the one with "(thuộc...)" if exists
                elif normalized != existing:
                    # Keep both if formats are different (one might have "thuộc")
                    if '(thuộc' in normalized and '(thuộc' not in existing:
                        idx = result.index(existing)
                        result[idx] = normalized
                        seen_names[base_name_clean] = normalized
                    elif '(thuộc' not in normalized and '(thuộc' in existing:
                        # Keep existing one with "thuộc"
                        pass
                    else:
                        # Same format, skip duplicate
                        continue
                else:
                    # Exact duplicate, skip
                    continue
            else:
                # New province, add it
                result.append(normalized)
                seen_names[base_name_clean] = normalized
        
        return result
    
    def _get_type_label(self, loai_dia_diem):
        """Convert loaiDiaDiem to readable label."""
        labels = {
            'dia_danh': 'Địa danh',
            'nha_hang': 'Nhà hàng',
            'khach_san': 'Khách sạn',
            'giai_tri': 'Giải trí',
            'mua_sam': 'Mua sắm',
            'khac': 'Khác'
        }
        return labels.get(loai_dia_diem, 'Địa điểm')
    
    def _remove_tones(self, text):
        """Remove Vietnamese tones for better matching."""
        import unicodedata
        return ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn').lower().replace('đ', 'd').replace('Đ', 'D')


class ReverseGeocodeView(APIView):
    """
    Reverse geocode coordinates to location name.
    Uses OpenStreetMap Nominatim API (free, no API key required).
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        lat = request.query_params.get('lat')
        lon = request.query_params.get('lon')
        
        if not lat or not lon:
            return Response({
                'error': 'Missing lat or lon parameters'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            lat = float(lat)
            lon = float(lon)
        except ValueError:
            return Response({
                'error': 'Invalid lat or lon format'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Try to reverse geocode
        try:
            import requests
            from django.conf import settings
            
            location = None
            
            # Try OpenRouteService
            if hasattr(settings, 'OPENROUTE_API_KEY') and settings.OPENROUTE_API_KEY:
                try:
                    url = "https://api.openrouteservice.org/geocode/reverse"
                    params = {
                        'api_key': settings.OPENROUTE_API_KEY,
                        'point.lon': lon,
                        'point.lat': lat,
                        'size': 1
                    }
                    response = requests.get(url, params=params, timeout=5)
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('features') and len(data['features']) > 0:
                            location = data['features'][0].get('properties', {}).get('label', '')
                except Exception as e:
                    logger.debug(f"OpenRouteService reverse geocode failed: {e}")
            
            if location:
                # Try to match with our database
                for province in TinhThanh.objects.all():
                    if province.tenTinhThanh in location:
                        location = province.tenTinhThanh
                        break
                
                return Response({
                    'location': location,
                    'lat': lat,
                    'lon': lon
                })
            else:
                return Response({
                    'location': 'Vị trí không xác định',
                    'lat': lat,
                    'lon': lon
                })
                
        except Exception as e:
            logger.error(f"Reverse geocode error: {e}")
            return Response({
                'error': str(e),
                'location': 'Vị trí không xác định'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


