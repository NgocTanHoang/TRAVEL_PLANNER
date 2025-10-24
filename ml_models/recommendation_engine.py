import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import pickle
import os

class RecommendationEngine:
    def __init__(self, model_dir: str = 'ml_models/saved_models'):
        """Initialize Recommendation Engine"""
        self.model_dir = model_dir
        self.ensure_model_dir()
        
        # Initialize models
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        self.scaler = StandardScaler()
        self.kmeans = KMeans(n_clusters=5, random_state=42)
        
        # User preferences weights
        self.preference_weights = {
            'rating': 0.3,
            'price': 0.2,
            'distance': 0.15,
            'category': 0.15,
            'popularity': 0.1,
            'recent': 0.1
        }
        
        # Load or initialize models
        self.load_models()
    
    def ensure_model_dir(self):
        """Create model directory if not exists"""
        if not os.path.exists(self.model_dir):
            os.makedirs(self.model_dir)
    
    def load_models(self):
        """Load models đã train"""
        try:
            # Load TF-IDF vectorizer
            tfidf_path = os.path.join(self.model_dir, 'tfidf_vectorizer.pkl')
            if os.path.exists(tfidf_path):
                with open(tfidf_path, 'rb') as f:
                    self.tfidf_vectorizer = pickle.load(f)
            
            # Load scaler
            scaler_path = os.path.join(self.model_dir, 'scaler.pkl')
            if os.path.exists(scaler_path):
                with open(scaler_path, 'rb') as f:
                    self.scaler = pickle.load(f)
            
            # Load KMeans
            kmeans_path = os.path.join(self.model_dir, 'kmeans.pkl')
            if os.path.exists(kmeans_path):
                with open(kmeans_path, 'rb') as f:
                    self.kmeans = pickle.load(f)
            
            print("[SUCCESS] Models loaded successfully")
        except Exception as e:
            print(f"[WARNING] Could not load models: {e}")
    
    def save_models(self):
        """Save models đã train"""
        try:
            # Save TF-IDF vectorizer
            tfidf_path = os.path.join(self.model_dir, 'tfidf_vectorizer.pkl')
            with open(tfidf_path, 'wb') as f:
                pickle.dump(self.tfidf_vectorizer, f)
            
            # Save scaler
            scaler_path = os.path.join(self.model_dir, 'scaler.pkl')
            with open(scaler_path, 'wb') as f:
                pickle.dump(self.scaler, f)
            
            # Save KMeans
            kmeans_path = os.path.join(self.model_dir, 'kmeans.pkl')
            with open(kmeans_path, 'wb') as f:
                pickle.dump(self.kmeans, f)
            
            print("[SUCCESS] Models saved successfully")
        except Exception as e:
            print(f"[ERROR] Could not save models: {e}")
    
    def prepare_features(self, places_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """Prepare features cho ML models"""
        features = []
        
        for place in places_data:
            feature = {
                'place_id': place.get('place_id', ''),
                'name': place.get('name', ''),
                'city': place.get('city', ''),
                'rating': place.get('rating', 0),
                'price_level': place.get('price_level', 0),
                'latitude': place.get('latitude', 0),
                'longitude': place.get('longitude', 0),
                'category': place.get('category', ''),
                'types': ', '.join(place.get('types', [])),
                'description': f"{place.get('name', '')} {place.get('category', '')} {', '.join(place.get('types', []))}",
                'popularity_score': self._calculate_popularity_score(place),
                'recent_score': self._calculate_recent_score(place)
            }
            features.append(feature)
        
        return pd.DataFrame(features)
    
    def _calculate_popularity_score(self, place: Dict[str, Any]) -> float:
        """Calculate popularity score"""
        rating = place.get('rating', 0)
        price_level = place.get('price_level', 0)
        
        # Higher rating = more popular
        popularity = rating * 20  # Convert to 0-100 scale
        
        # Adjust for price level (moderate price = more popular)
        if price_level == 2:  # Moderate price
            popularity *= 1.1
        elif price_level > 3:  # Expensive
            popularity *= 0.9
        
        return min(popularity, 100.0)
    
    def _calculate_recent_score(self, place: Dict[str, Any]) -> float:
        """Calculate recent score gần đây"""
        created_at = place.get('created_at', '')
        if not created_at:
            return 50.0  # Default score
        
        try:
            created_date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
            days_ago = (datetime.now() - created_date).days
            
            # Recent places get higher scores
            if days_ago <= 7:
                return 100.0
            elif days_ago <= 30:
                return 80.0
            elif days_ago <= 90:
                return 60.0
            else:
                return 40.0
        except:
            return 50.0
    
    def train_models(self, places_data: List[Dict[str, Any]]):
        """Train ML models"""
        print("[TRAINING] Training recommendation models...")
        
        # Prepare features
        df = self.prepare_features(places_data)
        
        if len(df) < 10:
            print("[WARNING] Not enough data to train models")
            return
        
        # Train TF-IDF vectorizer
        print("[TFIDF] Training TF-IDF vectorizer...")
        descriptions = df['description'].fillna('')
        self.tfidf_vectorizer.fit(descriptions)
        
        # Prepare numerical features
        numerical_features = ['rating', 'price_level', 'popularity_score', 'recent_score']
        X_numerical = df[numerical_features].fillna(0)
        
        # Train scaler
        print("[SCALER] Training scaler...")
        self.scaler.fit(X_numerical)
        
        # Train KMeans clustering
        print("[MATCH] Training KMeans clustering...")
        X_scaled = self.scaler.transform(X_numerical)
        self.kmeans.fit(X_scaled)
        
        # Save models
        self.save_models()
        
        print("[SUCCESS] Models training completed!")
    
    def get_content_based_recommendations(self, user_preferences: Dict[str, Any], 
                                        places_data: List[Dict[str, Any]], 
                                        top_k: int = 10) -> List[Dict[str, Any]]:
        """Content-based recommendations"""
        if not places_data:
            return []
        
        # Prepare features
        df = self.prepare_features(places_data)
        
        # Create user profile
        user_profile = self._create_user_profile(user_preferences, df)
        
        # Calculate similarities
        similarities = self._calculate_content_similarity(user_profile, df)
        
        # Get top recommendations
        recommendations = self._get_top_recommendations(df, similarities, top_k)
        
        return recommendations.to_dict('records')
    
    def _create_user_profile(self, preferences: Dict[str, Any], df: pd.DataFrame) -> np.ndarray:
        """Create user profile từ preferences"""
        # Check if vectorizer is fitted
        if not hasattr(self.tfidf_vectorizer, 'vocabulary_'):
            # Return zero vector if not fitted
            return np.zeros(1000)  # Default size
        
        # Default profile
        profile = np.zeros(len(self.tfidf_vectorizer.get_feature_names_out()))
        
        # Extract preferences
        preferred_categories = preferences.get('categories', [])
        preferred_cities = preferences.get('cities', [])
        preferred_price_range = preferences.get('price_range', [1, 2, 3])
        min_rating = preferences.get('min_rating', 3.0)
        
        # Filter places based on preferences
        filtered_df = df[
            (df['category'].isin(preferred_categories) if preferred_categories else True) &
            (df['city'].isin(preferred_cities) if preferred_cities else True) &
            (df['price_level'].isin(preferred_price_range)) &
            (df['rating'] >= min_rating)
        ]
        
        if len(filtered_df) > 0:
            # Create TF-IDF matrix for preferred places
            descriptions = filtered_df['description'].fillna('')
            tfidf_matrix = self.tfidf_vectorizer.transform(descriptions)
            
            # Average the TF-IDF vectors
            profile = np.mean(tfidf_matrix.toarray(), axis=0)
        
        return profile
    
    def _calculate_content_similarity(self, user_profile: np.ndarray, df: pd.DataFrame) -> np.ndarray:
        """Calculate similarity giữa user profile và places"""
        # Check if vectorizer is fitted
        if not hasattr(self.tfidf_vectorizer, 'vocabulary_'):
            # Return random similarities if not fitted
            return np.random.random(len(df))
        
        descriptions = df['description'].fillna('')
        tfidf_matrix = self.tfidf_vectorizer.transform(descriptions)
        
        # Calculate cosine similarity
        similarities = cosine_similarity([user_profile], tfidf_matrix)[0]
        
        return similarities
    
    def _get_top_recommendations(self, df: pd.DataFrame, similarities: np.ndarray, top_k: int) -> pd.DataFrame:
        """Get top recommendations dựa trên similarities"""
        # Add similarity scores to dataframe
        df = df.copy()
        df['similarity_score'] = similarities
        
        # Sort by similarity score
        df_sorted = df.sort_values('similarity_score', ascending=False)
        
        # Return top k recommendations
        return df_sorted.head(top_k)
    
    def get_collaborative_recommendations(self, user_id: str, 
                                        user_history: List[Dict[str, Any]], 
                                        places_data: List[Dict[str, Any]], 
                                        top_k: int = 10) -> List[Dict[str, Any]]:
        """Collaborative filtering recommendations"""
        if not user_history or not places_data:
            return []
        
        # Create user-item matrix (simplified)
        user_ratings = {}
        for item in user_history:
            place_id = item.get('place_id', '')
            rating = item.get('rating', 0)
            if place_id and rating > 0:
                user_ratings[place_id] = rating
        
        # Find similar users (simplified approach)
        similar_places = self._find_similar_places(user_ratings, places_data)
        
        # Get recommendations
        recommendations = []
        for place in places_data:
            place_id = place.get('place_id', '')
            if place_id not in user_ratings and place_id in similar_places:
                place['predicted_rating'] = similar_places[place_id]
                recommendations.append(place)
        
        # Sort by predicted rating
        recommendations.sort(key=lambda x: x.get('predicted_rating', 0), reverse=True)
        
        return recommendations[:top_k]
    
    def _find_similar_places(self, user_ratings: Dict[str, float], 
                           places_data: List[Dict[str, Any]]) -> Dict[str, float]:
        """Find similar places dựa trên user ratings"""
        similar_places = {}
        
        # Simple collaborative filtering
        for place in places_data:
            place_id = place.get('place_id', '')
            if place_id not in user_ratings:
                # Calculate predicted rating based on similar places
                predicted_rating = self._predict_rating(place, user_ratings, places_data)
                if predicted_rating > 0:
                    similar_places[place_id] = predicted_rating
        
        return similar_places
    
    def _predict_rating(self, target_place: Dict[str, Any], 
                       user_ratings: Dict[str, float], 
                       places_data: List[Dict[str, Any]]) -> float:
        """Predict rating cho một place"""
        target_category = target_place.get('category', '')
        target_city = target_place.get('city', '')
        
        # Find similar places that user has rated
        similar_ratings = []
        for place in places_data:
            place_id = place.get('place_id', '')
            if place_id in user_ratings:
                place_category = place.get('category', '')
                place_city = place.get('city', '')
                
                # Calculate similarity
                similarity = 0
                if place_category == target_category:
                    similarity += 0.5
                if place_city == target_city:
                    similarity += 0.3
                if abs(place.get('price_level', 0) - target_place.get('price_level', 0)) <= 1:
                    similarity += 0.2
                
                if similarity > 0:
                    similar_ratings.append((user_ratings[place_id], similarity))
        
        # Calculate weighted average
        if similar_ratings:
            total_weight = sum(weight for _, weight in similar_ratings)
            weighted_sum = sum(rating * weight for rating, weight in similar_ratings)
            return weighted_sum / total_weight if total_weight > 0 else 0
        
        return 0
    
    def get_hybrid_recommendations(self, user_id: str, 
                                 user_preferences: Dict[str, Any], 
                                 user_history: List[Dict[str, Any]], 
                                 places_data: List[Dict[str, Any]], 
                                 top_k: int = 10) -> List[Dict[str, Any]]:
        """Hybrid recommendations combining content-based và collaborative filtering"""
        # Get content-based recommendations
        content_recs = self.get_content_based_recommendations(
            user_preferences, places_data, top_k * 2
        )
        
        # Get collaborative recommendations
        collab_recs = self.get_collaborative_recommendations(
            user_id, user_history, places_data, top_k * 2
        )
        
        # Combine recommendations
        combined_recs = self._combine_recommendations(content_recs, collab_recs, top_k)
        
        return combined_recs
    
    def _combine_recommendations(self, content_recs: List[Dict[str, Any]], 
                               collab_recs: List[Dict[str, Any]], 
                               top_k: int) -> List[Dict[str, Any]]:
        """Combine content-based và collaborative recommendations"""
        # Create place_id to recommendation mapping
        content_dict = {rec['place_id']: rec for rec in content_recs}
        collab_dict = {rec['place_id']: rec for rec in collab_recs}
        
        # Combine scores
        combined_recs = []
        all_place_ids = set(content_dict.keys()) | set(collab_dict.keys())
        
        for place_id in all_place_ids:
            content_score = 0
            collab_score = 0
            
            if place_id in content_dict:
                content_score = 1.0  # Normalized score
            if place_id in collab_dict:
                collab_score = collab_dict[place_id].get('predicted_rating', 0) / 5.0
            
            # Weighted combination
            combined_score = 0.6 * content_score + 0.4 * collab_score
            
            # Get place data
            place_data = content_dict.get(place_id, collab_dict.get(place_id, {}))
            place_data['combined_score'] = combined_score
            
            combined_recs.append(place_data)
        
        # Sort by combined score
        combined_recs.sort(key=lambda x: x.get('combined_score', 0), reverse=True)
        
        return combined_recs[:top_k]
    
    def get_cluster_recommendations(self, places_data: List[Dict[str, Any]], 
                                  target_place: Dict[str, Any], 
                                  top_k: int = 10) -> List[Dict[str, Any]]:
        """Clustering-based recommendations"""
        if not places_data:
            return []
        
        # Prepare features
        df = self.prepare_features(places_data)
        
        # Get numerical features
        numerical_features = ['rating', 'price_level', 'popularity_score', 'recent_score']
        X_numerical = df[numerical_features].fillna(0)
        X_scaled = self.scaler.transform(X_numerical)
        
        # Get cluster for target place
        target_features = self.prepare_features([target_place])
        target_numerical = target_features[numerical_features].fillna(0)
        target_scaled = self.scaler.transform(target_numerical)
        target_cluster = self.kmeans.predict(target_scaled)[0]
        
        # Find places in same cluster
        cluster_labels = self.kmeans.predict(X_scaled)
        same_cluster_indices = np.where(cluster_labels == target_cluster)[0]
        
        # Get recommendations from same cluster
        recommendations = []
        for idx in same_cluster_indices:
            place_data = df.iloc[idx].to_dict()
            recommendations.append(place_data)
        
        # Sort by rating
        recommendations.sort(key=lambda x: x.get('rating', 0), reverse=True)
        
        return recommendations[:top_k]
    
    def get_personalized_recommendations(self, user_profile: Dict[str, Any], 
                                       places_data: List[Dict[str, Any]], 
                                       top_k: int = 10) -> List[Dict[str, Any]]:
        """Personalized recommendations dựa trên user profile"""
        if not places_data:
            return []
        
        # Prepare features
        df = self.prepare_features(places_data)
        
        # Calculate personalized scores
        personalized_scores = []
        for _, place in df.iterrows():
            score = self._calculate_personalized_score(place, user_profile)
            personalized_scores.append(score)
        
        # Add scores to dataframe
        df['personalized_score'] = personalized_scores
        
        # Sort by personalized score
        df_sorted = df.sort_values('personalized_score', ascending=False)
        
        return df_sorted.head(top_k).to_dict('records')
    
    def _calculate_personalized_score(self, place: pd.Series, user_profile: Dict[str, Any]) -> float:
        """Calculate personalized score cho một place"""
        score = 0
        
        # Rating component
        rating = place.get('rating', 0)
        score += rating * self.preference_weights['rating'] * 20  # Convert to 0-100 scale
        
        # Price component
        price_level = place.get('price_level', 0)
        preferred_price = user_profile.get('preferred_price_level', 2)
        price_diff = abs(price_level - preferred_price)
        price_score = max(0, 100 - price_diff * 25)
        score += price_score * self.preference_weights['price']
        
        # Category component
        category = place.get('category', '')
        preferred_categories = user_profile.get('preferred_categories', [])
        if category in preferred_categories:
            score += 100 * self.preference_weights['category']
        
        # Popularity component
        popularity = place.get('popularity_score', 0)
        score += popularity * self.preference_weights['popularity']
        
        # Recent component
        recent = place.get('recent_score', 0)
        score += recent * self.preference_weights['recent']
        
        return score
    
    def get_recommendation_explanation(self, place: Dict[str, Any], 
                                     user_profile: Dict[str, Any]) -> str:
        """Generate explanation cho recommendation"""
        explanations = []
        
        rating = place.get('rating', 0)
        if rating >= 4.0:
            explanations.append(f"[RATING] Highly rated ({rating}/5.0)")
        
        category = place.get('category', '')
        preferred_categories = user_profile.get('preferred_categories', [])
        if category in preferred_categories:
            explanations.append(f"[MATCH] Matches your interest in {category}")
        
        price_level = place.get('price_level', 0)
        preferred_price = user_profile.get('preferred_price_level', 2)
        if abs(price_level - preferred_price) <= 1:
            explanations.append("[BUDGET] Fits your budget preference")
        
        popularity = place.get('popularity_score', 0)
        if popularity >= 80:
            explanations.append("[POPULAR] Very popular among travelers")
        
        if not explanations:
            explanations.append("[RECOMMEND] Recommended based on your preferences")
        
        return " | ".join(explanations)
