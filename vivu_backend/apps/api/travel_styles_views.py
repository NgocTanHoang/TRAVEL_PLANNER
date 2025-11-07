"""
Travel Styles API Views
=======================
API endpoints để quản lý và lấy thông tin về các phong cách du lịch
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
import logging

logger = logging.getLogger(__name__)

try:
    from tools.travel_styles import (
        get_all_styles, get_style_profile, get_combined_profile,
        get_preset_profile, STYLE_PRESETS, TravelStyle
    )
    TRAVEL_STYLES_AVAILABLE = True
except ImportError:
    TRAVEL_STYLES_AVAILABLE = False
    logger.warning("Travel styles module not available")


class TravelStylesListView(APIView):
    """
    GET /api/v1/travel-styles/
    
    Lấy danh sách tất cả phong cách du lịch
    """
    permission_classes = [AllowAny]
    
    def get(self, request):
        """List all travel styles"""
        if not TRAVEL_STYLES_AVAILABLE:
            # Fallback to basic styles
            return Response({
                'styles': [
                    {'value': 'budget', 'name': 'Tiết kiệm', 'description': 'Du lịch với ngân sách hạn chế'},
                    {'value': 'standard', 'name': 'Tiêu chuẩn', 'description': 'Du lịch cân bằng giữa chất lượng và giá cả'},
                    {'value': 'luxury', 'name': 'Sang trọng', 'description': 'Du lịch cao cấp với dịch vụ tốt nhất'}
                ],
                'presets': []
            }, status=status.HTTP_200_OK)
        
        try:
            styles = get_all_styles()
            presets = [
                {
                    'name': preset_name,
                    'styles': [s.value for s in STYLE_PRESETS[preset_name]],
                    'description': f"Kết hợp {len(STYLE_PRESETS[preset_name])} phong cách"
                }
                for preset_name in STYLE_PRESETS.keys()
            ]
            
            return Response({
                'styles': styles,
                'presets': presets,
                'count': len(styles)
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error listing travel styles: {e}", exc_info=True)
            return Response({
                'error': 'Không thể lấy danh sách phong cách du lịch',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TravelStyleDetailView(APIView):
    """
    GET /api/v1/travel-styles/{style}/
    
    Lấy chi tiết một phong cách du lịch
    """
    permission_classes = [AllowAny]
    
    def get(self, request, style):
        """Get travel style details"""
        if not TRAVEL_STYLES_AVAILABLE:
            return Response({
                'error': 'Travel styles module not available'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        try:
            profile = get_style_profile(style)
            if not profile:
                return Response({
                    'error': f'Không tìm thấy phong cách: {style}'
                }, status=status.HTTP_404_NOT_FOUND)
            
            return Response({
                'value': style,
                'name': profile.name,
                'description': profile.description,
                'target_audience': profile.target_audience,
                'examples': profile.examples,
                'weights': profile.weights,
                'preferred_radius_km': profile.preferred_radius_km,
                'preferred_price_range': profile.preferred_price_range,
                'max_daily_travel_time_min': profile.max_daily_travel_time_min,
                'preferred_activity_types': profile.preferred_activity_types,
                'requires_internet': profile.requires_internet,
                'requires_guide': profile.requires_guide,
                'requires_reservation': profile.requires_reservation,
                'requires_accessibility': profile.requires_accessibility,
                'sustainability_preference': profile.sustainability_preference,
                'meal_importance': profile.meal_importance,
                'preferred_meal_types': profile.preferred_meal_types,
                'special_notes': profile.special_notes
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error getting travel style detail: {e}", exc_info=True)
            return Response({
                'error': 'Không thể lấy thông tin phong cách',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class TravelStyleCombineView(APIView):
    """
    POST /api/v1/travel-styles/combine/
    
    Kết hợp nhiều phong cách thành một profile
    
    Body: {
        "styles": ["romantic", "luxury"]
    }
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Combine multiple travel styles"""
        if not TRAVEL_STYLES_AVAILABLE:
            return Response({
                'error': 'Travel styles module not available'
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        try:
            styles = request.data.get('styles', [])
            if not styles:
                return Response({
                    'error': 'Danh sách phong cách không được để trống'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not isinstance(styles, list):
                return Response({
                    'error': 'styles phải là một mảng'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            profile = get_combined_profile(styles)
            
            return Response({
                'styles': styles,
                'combined_profile': {
                    'name': profile.name,
                    'description': profile.description,
                    'weights': profile.weights,
                    'preferred_radius_km': profile.preferred_radius_km,
                    'preferred_price_range': profile.preferred_price_range,
                    'max_daily_travel_time_min': profile.max_daily_travel_time_min,
                    'preferred_activity_types': profile.preferred_activity_types,
                    'requires_internet': profile.requires_internet,
                    'requires_guide': profile.requires_guide,
                    'requires_reservation': profile.requires_reservation,
                    'requires_accessibility': profile.requires_accessibility,
                    'sustainability_preference': profile.sustainability_preference,
                    'meal_importance': profile.meal_importance,
                    'preferred_meal_types': profile.preferred_meal_types
                }
            }, status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error combining travel styles: {e}", exc_info=True)
            return Response({
                'error': 'Không thể kết hợp phong cách',
                'detail': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

