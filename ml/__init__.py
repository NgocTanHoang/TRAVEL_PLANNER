"""
ML Recommendation System Package
=================================
Các mô hình ML cho hệ thống recommendation du lịch
"""

from .recommendation_system import (
    ContentBasedRecommender,
    CollaborativeFilteringRecommender,
    CostPredictionModel,
    DestinationClustering,
    MLRecommendationSystem,
    get_ml_recommender
)

from .neural_recommendation import (
    NeuralCollaborativeFiltering,
    DeepFM,
    HybridNeuralRecommender
)

from .travel_chatbot import (
    TravelChatbot,
    get_travel_chatbot
)

from .api_integration import (
    get_content_based_recommendations,
    get_cluster_recommendations,
    predict_trip_cost,
    get_hybrid_recommendations
)

__all__ = [
    # Basic recommendation
    'ContentBasedRecommender',
    'CollaborativeFilteringRecommender',
    'CostPredictionModel',
    'DestinationClustering',
    'MLRecommendationSystem',
    'get_ml_recommender',
    # Neural recommendation
    'NeuralCollaborativeFiltering',
    'DeepFM',
    'HybridNeuralRecommender',
    # Chatbot
    'TravelChatbot',
    'get_travel_chatbot',
    # API integration
    'get_content_based_recommendations',
    'get_cluster_recommendations',
    'predict_trip_cost',
    'get_hybrid_recommendations',
]

