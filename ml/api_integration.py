"""
ML Recommendation System - API Integration
===========================================
Tích hợp ML recommendation vào API endpoints
"""

import logging
from typing import Dict, Any, Optional, List
from ml.recommendation_system import get_ml_recommender, MLRecommendationSystem

logger = logging.getLogger(__name__)


def get_content_based_recommendations(
    query_text: str,
    destination: Optional[str] = None,
    n_results: int = 10,
    filters: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
    """
    Get content-based recommendations
    
    Args:
        query_text: Text query (e.g., "bảo tàng văn hóa")
        destination: Destination city (optional)
        n_results: Number of results
        filters: Additional filters
    
    Returns:
        List of recommended places
    """
    try:
        recommender = get_ml_recommender()
        
        # Load places nếu chưa có
        if recommender.places_df is None:
            recommender.load_places_from_vector_db()
        
        # Fit model nếu chưa fit
        if recommender.content_based.similarity_matrix is None:
            places = recommender.load_places_from_vector_db()
            if places:
                recommender.content_based.fit(places)
        
        # Get recommendations
        recommendations = recommender.content_based.recommend(
            query_text=query_text,
            n_results=n_results,
            filters=filters
        )
        
        return recommendations
        
    except Exception as e:
        logger.error(f"Error getting content-based recommendations: {e}")
        return []


def get_cluster_recommendations(
    destination: str,
    place_name: Optional[str] = None,
    n_results: int = 10
) -> List[Dict[str, Any]]:
    """
    Get recommendations from same cluster
    
    Args:
        destination: Destination city
        place_name: Specific place name (optional)
        n_results: Number of results
    
    Returns:
        List of recommended places from same cluster
    """
    try:
        recommender = get_ml_recommender()
        
        # Load places nếu chưa có
        if recommender.places_df is None:
            recommender.load_places_from_vector_db()
        
        # Fit clustering nếu chưa fit
        if recommender.clustering.model is None:
            places = recommender.load_places_from_vector_db()
            if places:
                recommender.clustering.fit(places)
        
        # Find place
        if place_name:
            matches = recommender.places_df[
                recommender.places_df['name'].str.contains(place_name, case=False, na=False)
            ]
        else:
            matches = recommender.places_df[
                recommender.places_df['city'].str.contains(destination, case=False, na=False)
            ]
        
        if matches.empty:
            return []
        
        place = matches.iloc[0].to_dict()
        
        # Get cluster recommendations
        recommendations = recommender.clustering.get_cluster_recommendations(
            place,
            n_results=n_results
        )
        
        return recommendations
        
    except Exception as e:
        logger.error(f"Error getting cluster recommendations: {e}")
        return []


def predict_trip_cost(
    destination: str,
    days: int,
    travelers: int,
    travel_style: str = 'standard',
    season: str = 'normal'
) -> Dict[str, Any]:
    """
    Predict trip cost
    
    Args:
        destination: Destination city
        days: Number of days
        travelers: Number of travelers
        travel_style: 'budget', 'standard', 'luxury'
        season: Season (optional)
    
    Returns:
        Dict with predicted cost and breakdown
    """
    try:
        recommender = get_ml_recommender()
        
        # Predict cost
        predicted_cost = recommender.cost_predictor.predict(
            destination=destination,
            days=days,
            travelers=travelers,
            travel_style=travel_style,
            season=season
        )
        
        # Calculate per-person and per-day
        per_person = predicted_cost / travelers if travelers > 0 else 0
        per_day = predicted_cost / days if days > 0 else 0
        
        return {
            'total_cost': predicted_cost,
            'per_person': round(per_person),
            'per_day': round(per_day),
            'days': days,
            'travelers': travelers,
            'travel_style': travel_style
        }
        
    except Exception as e:
        logger.error(f"Error predicting trip cost: {e}")
        # Fallback to simple estimation
        base_cost_per_day = {
            'budget': 500000,
            'standard': 1500000,
            'luxury': 3000000
        }
        base = base_cost_per_day.get(travel_style, 1500000)
        total = base * days * travelers
        return {
            'total_cost': total,
            'per_person': round(total / travelers),
            'per_day': round(total / days),
            'days': days,
            'travelers': travelers,
            'travel_style': travel_style,
            'note': 'Fallback estimation'
        }


def get_hybrid_recommendations(
    query_text: str,
    user_id: Optional[int] = None,
    destination: Optional[str] = None,
    n_results: int = 10,
    use_content: bool = True,
    use_collaborative: bool = False,
    use_clustering: bool = True
) -> List[Dict[str, Any]]:
    """
    Get hybrid recommendations combining multiple methods
    
    Args:
        query_text: Text query
        user_id: User ID (optional, for collaborative filtering)
        destination: Destination city (optional)
        n_results: Number of results
        use_content: Use content-based filtering
        use_collaborative: Use collaborative filtering
        use_clustering: Use clustering
    
    Returns:
        List of recommended places
    """
    try:
        recommender = get_ml_recommender()
        
        # Ensure models are fitted
        if recommender.places_df is None:
            recommender.load_places_from_vector_db()
        
        places = recommender.places_df.to_dict('records') if recommender.places_df is not None else []
        
        if use_content and recommender.content_based.similarity_matrix is None:
            if places:
                recommender.content_based.fit(places)
        
        if use_clustering and recommender.clustering.model is None:
            if places:
                recommender.clustering.fit(places)
        
        # Get hybrid recommendations
        recommendations = recommender.hybrid_recommend(
            user_id=user_id,
            query_text=query_text,
            destination=destination,
            n_results=n_results,
            use_content=use_content,
            use_collaborative=use_collaborative,
            use_clustering=use_clustering
        )
        
        return recommendations
        
    except Exception as e:
        logger.error(f"Error getting hybrid recommendations: {e}")
        return []

