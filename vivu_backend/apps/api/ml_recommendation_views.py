"""
ML Recommendation API Views
===========================
API endpoints cho ML recommendation system
"""

import sys
from pathlib import Path
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
import logging

# Add backend directory to path for ml, etc.
# BASE_DIR (vivu_backend) is already added in settings.py, but adding here for safety
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

logger = logging.getLogger(__name__)


class ContentBasedRecommendationView(APIView):
    """
    Content-based Recommendation API
    
    POST /api/v1/recommendations/content-based/
    {
        "query": "bảo tàng văn hóa",
        "destination": "Hà Nội",  # Optional
        "n_results": 10,
        "filters": {
            "max_price": 1000000,
            "category": "attraction"
        }
    }
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        try:
            from ml.api_integration import get_content_based_recommendations
            
            query = request.data.get('query', '')
            destination = request.data.get('destination')
            n_results = int(request.data.get('n_results', 10))
            filters = request.data.get('filters', {})
            
            if not query:
                return Response({
                    'error': 'Query không được để trống'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            recommendations = get_content_based_recommendations(
                query_text=query,
                destination=destination,
                n_results=n_results,
                filters=filters
            )
            
            return Response({
                'status': 'success',
                'recommendations': recommendations,
                'count': len(recommendations)
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error in content-based recommendation: {e}", exc_info=True)
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ClusterRecommendationView(APIView):
    """
    Cluster-based Recommendation API
    
    POST /api/v1/recommendations/cluster/
    {
        "destination": "Hà Nội",
        "place_name": "Lăng Bác",  # Optional
        "n_results": 10
    }
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        try:
            from ml.api_integration import get_cluster_recommendations
            
            destination = request.data.get('destination')
            place_name = request.data.get('place_name')
            n_results = int(request.data.get('n_results', 10))
            
            if not destination:
                return Response({
                    'error': 'Destination không được để trống'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            recommendations = get_cluster_recommendations(
                destination=destination,
                place_name=place_name,
                n_results=n_results
            )
            
            return Response({
                'status': 'success',
                'recommendations': recommendations,
                'count': len(recommendations)
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error in cluster recommendation: {e}", exc_info=True)
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CostPredictionView(APIView):
    """
    Cost Prediction API
    
    POST /api/v1/recommendations/predict-cost/
    {
        "destination": "Hà Nội",
        "days": 3,
        "travelers": 2,
        "travel_style": "standard",
        "season": "normal"  # Optional
    }
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        try:
            from ml.api_integration import predict_trip_cost
            
            destination = request.data.get('destination')
            days = int(request.data.get('days', 3))
            travelers = int(request.data.get('travelers', 2))
            travel_style = request.data.get('travel_style', 'standard')
            season = request.data.get('season', 'normal')
            
            if not destination:
                return Response({
                    'error': 'Destination không được để trống'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            prediction = predict_trip_cost(
                destination=destination,
                days=days,
                travelers=travelers,
                travel_style=travel_style,
                season=season
            )
            
            return Response({
                'status': 'success',
                'prediction': prediction
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error in cost prediction: {e}", exc_info=True)
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class HybridRecommendationView(APIView):
    """
    Hybrid Recommendation API (combining multiple methods)
    
    POST /api/v1/recommendations/hybrid/
    {
        "query": "điểm tham quan văn hóa",
        "user_id": 1,  # Optional, for collaborative filtering
        "destination": "Hà Nội",  # Optional
        "n_results": 10,
        "use_content": true,
        "use_collaborative": false,
        "use_clustering": true
    }
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        try:
            from ml.api_integration import get_hybrid_recommendations
            
            query = request.data.get('query', '')
            user_id = request.data.get('user_id')
            destination = request.data.get('destination')
            n_results = int(request.data.get('n_results', 10))
            use_content = request.data.get('use_content', True)
            use_collaborative = request.data.get('use_collaborative', False)
            use_clustering = request.data.get('use_clustering', True)
            
            if not query:
                return Response({
                    'error': 'Query không được để trống'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            recommendations = get_hybrid_recommendations(
                query_text=query,
                user_id=user_id,
                destination=destination,
                n_results=n_results,
                use_content=use_content,
                use_collaborative=use_collaborative,
                use_clustering=use_clustering
            )
            
            return Response({
                'status': 'success',
                'recommendations': recommendations,
                'count': len(recommendations),
                'methods_used': {
                    'content_based': use_content,
                    'collaborative': use_collaborative,
                    'clustering': use_clustering
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error in hybrid recommendation: {e}", exc_info=True)
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

