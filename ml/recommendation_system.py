"""
ML Recommendation System
=========================
Triển khai các mô hình ML cho hệ thống recommendation du lịch:
1. Content-based Recommendation (TF-IDF + Embeddings)
2. Collaborative Filtering đơn giản
3. Regression dự đoán chi phí
4. Clustering phân nhóm điểm đến
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
import logging
from pathlib import Path
import pickle
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import TruncatedSVD
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans, DBSCAN
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
import joblib

logger = logging.getLogger(__name__)

# Optional imports
try:
    from surprise import Dataset, Reader, SVD as SurpriseSVD
    SURPRISE_AVAILABLE = True
except ImportError:
    SURPRISE_AVAILABLE = False
    logger.warning("Surprise library not available, collaborative filtering will use simple SVD")

try:
    import xgboost as xgb
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    logger.warning("XGBoost not available, will use RandomForest for regression")


class ContentBasedRecommender:
    """
    Content-based Recommendation System
    Sử dụng TF-IDF hoặc embeddings để tính similarity
    """
    
    def __init__(self, use_tfidf: bool = True, use_embeddings: bool = True):
        """
        Args:
            use_tfidf: Sử dụng TF-IDF vectorization
            use_embeddings: Sử dụng embeddings từ Vector DB
        """
        self.use_tfidf = use_tfidf
        self.use_embeddings = use_embeddings
        
        if use_tfidf:
            self.tfidf_vectorizer = TfidfVectorizer(
                max_features=500,
                stop_words=None,  # Vietnamese stop words có thể thêm sau
                ngram_range=(1, 2),
                min_df=2,
                max_df=0.95
            )
            self.tfidf_matrix = None
        
        self.places_df = None
        self.similarity_matrix = None
        
    def fit(self, places: List[Dict[str, Any]]):
        """
        Fit model với danh sách điểm đến
        
        Args:
            places: List of place dictionaries với keys: name, description, city, category, etc.
        """
        if not places:
            logger.warning("No places provided for fitting")
            return
        
        # Convert to DataFrame
        self.places_df = pd.DataFrame(places)
        
        if self.use_tfidf:
            # Tạo text features từ các trường
            text_features = []
            for _, row in self.places_df.iterrows():
                features = []
                if pd.notna(row.get('name')):
                    features.append(str(row['name']))
                if pd.notna(row.get('description')):
                    features.append(str(row['description']))
                if pd.notna(row.get('category')):
                    features.append(str(row['category']))
                if pd.notna(row.get('city')):
                    features.append(str(row['city']))
                if pd.notna(row.get('province')):
                    features.append(str(row['province']))
                
                text_features.append(' '.join(features))
            
            # Fit TF-IDF
            self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(text_features)
            logger.info(f"TF-IDF matrix shape: {self.tfidf_matrix.shape}")
            
            # Tính similarity matrix
            self.similarity_matrix = cosine_similarity(self.tfidf_matrix)
            logger.info("TF-IDF similarity matrix computed")
    
    def recommend(
        self,
        query_place: Dict[str, Any] = None,
        query_text: str = None,
        n_results: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Gợi ý điểm đến dựa trên content similarity
        
        Args:
            query_place: Place dictionary để tìm similar
            query_text: Text query để tìm similar
            n_results: Số kết quả
            filters: Dict với filters như {'city': 'Hà Nội', 'category': 'attraction', 'max_price': 1000000}
        
        Returns:
            List of recommended places với similarity scores
        """
        if self.similarity_matrix is None or self.places_df is None:
            logger.warning("Model not fitted yet")
            return []
        
        # Tìm index của query place
        if query_place:
            # Tìm place trong DataFrame
            matches = self.places_df[
                (self.places_df['name'] == query_place.get('name', ''))
            ]
            if matches.empty:
                logger.warning(f"Query place not found: {query_place.get('name')}")
                return []
            query_idx = matches.index[0]
        elif query_text:
            # Tạo TF-IDF vector cho query text
            query_vector = self.tfidf_vectorizer.transform([query_text])
            # Tính similarity với tất cả places
            similarities = cosine_similarity(query_vector, self.tfidf_matrix)[0]
            # Lấy top-k
            top_indices = np.argsort(similarities)[::-1][:n_results]
            results = []
            for idx in top_indices:
                place = self.places_df.iloc[idx].to_dict()
                place['similarity_score'] = float(similarities[idx])
                results.append(place)
            return self._apply_filters(results, filters)[:n_results]
        else:
            logger.warning("Either query_place or query_text must be provided")
            return []
        
        # Lấy similarity scores
        similarities = self.similarity_matrix[query_idx]
        
        # Lấy top-k (trừ chính nó)
        top_indices = np.argsort(similarities)[::-1][1:n_results+1]
        
        # Format results
        results = []
        for idx in top_indices:
            place = self.places_df.iloc[idx].to_dict()
            place['similarity_score'] = float(similarities[idx])
            results.append(place)
        
        return self._apply_filters(results, filters)
    
    def _apply_filters(self, results: List[Dict], filters: Optional[Dict]) -> List[Dict]:
        """Apply filters to results"""
        if not filters:
            return results
        
        filtered = []
        for place in results:
            # Filter by city
            if 'city' in filters and place.get('city', '').lower() != filters['city'].lower():
                continue
            
            # Filter by category
            if 'category' in filters and place.get('category', '').lower() != filters['category'].lower():
                continue
            
            # Filter by price
            if 'max_price' in filters:
                price = place.get('price', 0) or 0
                if price > filters['max_price']:
                    continue
            
            if 'min_price' in filters:
                price = place.get('price', 0) or 0
                if price < filters['min_price']:
                    continue
            
            filtered.append(place)
        
        return filtered


class CollaborativeFilteringRecommender:
    """
    Collaborative Filtering đơn giản
    Sử dụng Matrix Factorization (SVD) hoặc Surprise library
    """
    
    def __init__(self, use_surprise: bool = True):
        """
        Args:
            use_surprise: Sử dụng Surprise library nếu available
        """
        self.use_surprise = use_surprise and SURPRISE_AVAILABLE
        self.model = None
        self.ratings_df = None
        self.user_item_matrix = None
        self.svd_model = None
        
    def fit(self, ratings: List[Dict[str, Any]]):
        """
        Fit model với user ratings
        
        Args:
            ratings: List of dicts với keys: user_id, place_id, rating (1-5)
        """
        if not ratings:
            logger.warning("No ratings provided")
            return
        
        self.ratings_df = pd.DataFrame(ratings)
        
        if self.use_surprise:
            # Sử dụng Surprise library
            reader = Reader(rating_scale=(1, 5))
            data = Dataset.load_from_df(
                self.ratings_df[['user_id', 'place_id', 'rating']],
                reader
            )
            self.model = SurpriseSVD()
            trainset = data.build_full_trainset()
            self.model.fit(trainset)
            logger.info("Collaborative filtering model fitted with Surprise")
        else:
            # Sử dụng sklearn SVD
            # Tạo user-item matrix
            self.user_item_matrix = self.ratings_df.pivot_table(
                index='user_id',
                columns='place_id',
                values='rating',
                fill_value=0
            )
            
            # SVD decomposition
            self.svd_model = TruncatedSVD(n_components=50, random_state=42)
            self.user_item_matrix_reduced = self.svd_model.fit_transform(self.user_item_matrix)
            logger.info("Collaborative filtering model fitted with sklearn SVD")
    
    def recommend(
        self,
        user_id: int,
        n_results: int = 10,
        places_df: Optional[pd.DataFrame] = None
    ) -> List[Dict[str, Any]]:
        """
        Gợi ý cho user
        
        Args:
            user_id: ID của user
            n_results: Số kết quả
            places_df: DataFrame với thông tin places (optional)
        
        Returns:
            List of recommended places
        """
        if self.model is None and self.svd_model is None:
            logger.warning("Model not fitted yet")
            return []
        
        if self.use_surprise:
            # Dự đoán ratings cho tất cả items user chưa rate
            user_rated = set(
                self.ratings_df[self.ratings_df['user_id'] == user_id]['place_id']
            )
            all_items = set(self.ratings_df['place_id'].unique())
            unrated_items = all_items - user_rated
            
            predictions = []
            for item_id in unrated_items:
                pred = self.model.predict(user_id, item_id)
                predictions.append({
                    'place_id': item_id,
                    'predicted_rating': pred.est
                })
            
            # Sort và lấy top-k
            predictions.sort(key=lambda x: x['predicted_rating'], reverse=True)
            top_predictions = predictions[:n_results]
            
            # Merge với places_df nếu có
            if places_df is not None:
                results = []
                for pred in top_predictions:
                    place_info = places_df[places_df['place_id'] == pred['place_id']]
                    if not place_info.empty:
                        place = place_info.iloc[0].to_dict()
                        place['predicted_rating'] = pred['predicted_rating']
                        results.append(place)
                return results
            
            return top_predictions
        else:
            # Sử dụng SVD
            if user_id not in self.user_item_matrix.index:
                logger.warning(f"User {user_id} not found")
                return []
            
            user_idx = self.user_item_matrix.index.get_loc(user_id)
            user_vector = self.user_item_matrix_reduced[user_idx]
            
            # Tính similarity với tất cả users
            similarities = cosine_similarity([user_vector], self.user_item_matrix_reduced)[0]
            
            # Lấy top similar users
            top_users = np.argsort(similarities)[::-1][1:11]  # Top 10 similar users
            
            # Lấy items từ similar users
            recommendations = {}
            for user_idx in top_users:
                user_id_similar = self.user_item_matrix.index[user_idx]
                user_ratings = self.ratings_df[self.ratings_df['user_id'] == user_id_similar]
                
                for _, row in user_ratings.iterrows():
                    place_id = row['place_id']
                    rating = row['rating']
                    similarity = similarities[user_idx]
                    
                    if place_id not in recommendations:
                        recommendations[place_id] = {
                            'place_id': place_id,
                            'weighted_rating': 0,
                            'total_weight': 0
                        }
                    
                    recommendations[place_id]['weighted_rating'] += rating * similarity
                    recommendations[place_id]['total_weight'] += similarity
            
            # Tính predicted rating
            for place_id in recommendations:
                if recommendations[place_id]['total_weight'] > 0:
                    recommendations[place_id]['predicted_rating'] = (
                        recommendations[place_id]['weighted_rating'] / 
                        recommendations[place_id]['total_weight']
                    )
            
            # Sort và lấy top-k
            sorted_recs = sorted(
                recommendations.values(),
                key=lambda x: x.get('predicted_rating', 0),
                reverse=True
            )[:n_results]
            
            # Merge với places_df nếu có
            if places_df is not None:
                results = []
                for rec in sorted_recs:
                    place_info = places_df[places_df['place_id'] == rec['place_id']]
                    if not place_info.empty:
                        place = place_info.iloc[0].to_dict()
                        place['predicted_rating'] = rec.get('predicted_rating', 0)
                        results.append(place)
                return results
            
            return sorted_recs


class CostPredictionModel:
    """
    Regression model để dự đoán chi phí chuyến đi
    """
    
    def __init__(self, use_xgboost: bool = True):
        """
        Args:
            use_xgboost: Sử dụng XGBoost nếu available, else RandomForest
        """
        self.use_xgboost = use_xgboost and XGBOOST_AVAILABLE
        self.model = None
        self.scaler = StandardScaler()
        self.feature_names = None
        
    def fit(self, trips: List[Dict[str, Any]]):
        """
        Fit model với dữ liệu trips
        
        Args:
            trips: List of dicts với keys:
                - destination: str
                - days: int
                - travelers: int
                - travel_style: str ('budget', 'standard', 'luxury')
                - season: str (optional)
                - total_cost: float (target variable)
        """
        if not trips:
            logger.warning("No trips provided for fitting")
            return
        
        df = pd.DataFrame(trips)
        
        # Feature engineering
        features = []
        for _, row in df.iterrows():
            feature_vector = []
            
            # Days
            feature_vector.append(row.get('days', 1))
            
            # Travelers
            feature_vector.append(row.get('travelers', 1))
            
            # Travel style (one-hot encoding)
            travel_style = row.get('travel_style', 'standard')
            feature_vector.extend([
                1 if travel_style == 'budget' else 0,
                1 if travel_style == 'standard' else 0,
                1 if travel_style == 'luxury' else 0
            ])
            
            # Destination encoding (simple - city name hash)
            destination = str(row.get('destination', ''))
            feature_vector.append(hash(destination) % 1000)  # Simple hash
            
            # Season (if available)
            season = row.get('season', 'normal')
            seasons = ['spring', 'summer', 'autumn', 'winter', 'peak', 'low', 'normal']
            feature_vector.extend([1 if s == season else 0 for s in seasons])
            
            features.append(feature_vector)
        
        X = np.array(features)
        y = df['total_cost'].values
        
        # Normalize features
        X_scaled = self.scaler.fit_transform(X)
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X_scaled, y, test_size=0.2, random_state=42
        )
        
        # Train model
        if self.use_xgboost:
            self.model = xgb.XGBRegressor(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42
            )
        else:
            from sklearn.ensemble import RandomForestRegressor
            self.model = RandomForestRegressor(
                n_estimators=100,
                max_depth=10,
                random_state=42
            )
        
        self.model.fit(X_train, y_train)
        
        # Evaluate
        train_score = self.model.score(X_train, y_train)
        test_score = self.model.score(X_test, y_test)
        logger.info(f"Cost prediction model fitted. Train R²: {train_score:.3f}, Test R²: {test_score:.3f}")
    
    def predict(
        self,
        destination: str,
        days: int,
        travelers: int,
        travel_style: str = 'standard',
        season: str = 'normal'
    ) -> float:
        """
        Dự đoán chi phí chuyến đi
        
        Returns:
            Predicted total cost (VNĐ)
        """
        if self.model is None:
            logger.warning("Model not fitted yet")
            return 0.0
        
        # Create feature vector
        feature_vector = []
        feature_vector.append(days)
        feature_vector.append(travelers)
        feature_vector.extend([
            1 if travel_style == 'budget' else 0,
            1 if travel_style == 'standard' else 0,
            1 if travel_style == 'luxury' else 0
        ])
        feature_vector.append(hash(destination) % 1000)
        
        seasons = ['spring', 'summer', 'autumn', 'winter', 'peak', 'low', 'normal']
        feature_vector.extend([1 if s == season else 0 for s in seasons])
        
        X = np.array([feature_vector])
        X_scaled = self.scaler.transform(X)
        
        prediction = self.model.predict(X_scaled)[0]
        return max(0, round(prediction))  # Ensure non-negative


class DestinationClustering:
    """
    Clustering để phân nhóm điểm đến theo đặc trưng
    """
    
    def __init__(self, n_clusters: int = 8, method: str = 'kmeans'):
        """
        Args:
            n_clusters: Số clusters
            method: 'kmeans' hoặc 'dbscan'
        """
        self.n_clusters = n_clusters
        self.method = method
        self.model = None
        self.scaler = StandardScaler()
        self.places_df = None
        self.cluster_labels = None
        
    def fit(self, places: List[Dict[str, Any]]):
        """
        Fit clustering model
        
        Args:
            places: List of place dictionaries
        """
        if not places:
            logger.warning("No places provided for clustering")
            return
        
        self.places_df = pd.DataFrame(places)
        
        # Feature engineering
        features = []
        for _, row in self.places_df.iterrows():
            feature_vector = []
            
            # Price (normalized)
            price = row.get('price', 0) or 0
            feature_vector.append(price / 1000000)  # Scale to millions
            
            # Rating
            rating = row.get('rating', 0) or 0
            feature_vector.append(rating)
            
            # Category encoding
            category = str(row.get('category', '')).lower()
            categories = ['attraction', 'restaurant', 'hotel']
            feature_vector.extend([1 if cat in category else 0 for cat in categories])
            
            # Location encoding (simple hash)
            city = str(row.get('city', ''))
            feature_vector.append(hash(city) % 100)
            
            features.append(feature_vector)
        
        X = np.array(features)
        X_scaled = self.scaler.fit_transform(X)
        
        # Fit clustering
        if self.method == 'kmeans':
            self.model = KMeans(n_clusters=self.n_clusters, random_state=42)
            self.cluster_labels = self.model.fit_predict(X_scaled)
        else:  # DBSCAN
            self.model = DBSCAN(eps=0.5, min_samples=3)
            self.cluster_labels = self.model.fit_predict(X_scaled)
            # Count unique clusters
            n_clusters_found = len(set(self.cluster_labels)) - (1 if -1 in self.cluster_labels else 0)
            logger.info(f"DBSCAN found {n_clusters_found} clusters")
        
        self.places_df['cluster'] = self.cluster_labels
        
        logger.info(f"Clustering completed. {len(set(self.cluster_labels))} clusters found")
    
    def get_cluster_recommendations(
        self,
        place: Dict[str, Any],
        n_results: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Lấy recommendations từ cùng cluster
        
        Args:
            place: Place dictionary
            n_results: Số kết quả
        
        Returns:
            List of places trong cùng cluster
        """
        if self.places_df is None or 'cluster' not in self.places_df.columns:
            logger.warning("Model not fitted yet")
            return []
        
        # Tìm cluster của place
        matches = self.places_df[
            (self.places_df['name'] == place.get('name', ''))
        ]
        
        if matches.empty:
            logger.warning(f"Place not found: {place.get('name')}")
            return []
        
        cluster_id = matches.iloc[0]['cluster']
        
        # Lấy places trong cùng cluster
        cluster_places = self.places_df[self.places_df['cluster'] == cluster_id]
        
        # Exclude chính place đó
        cluster_places = cluster_places[
            cluster_places['name'] != place.get('name', '')
        ]
        
        # Sort by rating hoặc similarity
        cluster_places = cluster_places.sort_values(
            by='rating', ascending=False
        )[:n_results]
        
        return cluster_places.to_dict('records')


class MLRecommendationSystem:
    """
    Tổng hợp tất cả ML models
    """
    
    def __init__(self, model_dir: str = "ml_models"):
        """
        Args:
            model_dir: Thư mục lưu models
        """
        self.model_dir = Path(model_dir)
        self.model_dir.mkdir(exist_ok=True)
        
        self.content_based = ContentBasedRecommender()
        self.collaborative = CollaborativeFilteringRecommender()
        self.cost_predictor = CostPredictionModel()
        self.clustering = DestinationClustering()
        
        self.places_df = None
        self.ratings_df = None
        
    def load_places_from_vector_db(self):
        """Load places từ Vector DB"""
        try:
            from agents.travel_agents.vector_db import get_vector_db_agent
            vector_db = get_vector_db_agent()
            
            if not vector_db or not vector_db.collection:
                logger.warning("Vector DB not available")
                return []
            
            # Get all places từ Vector DB
            all_places = vector_db.collection.get()
            
            places = []
            if all_places and all_places.get('metadatas'):
                for i, metadata in enumerate(all_places['metadatas']):
                    place = {
                        'place_id': all_places['ids'][i] if all_places.get('ids') else f"place_{i}",
                        'name': metadata.get('name', ''),
                        'city': metadata.get('city', ''),
                        'category': metadata.get('category', ''),
                        'rating': metadata.get('rating', 0),
                        'price': metadata.get('price', 0),
                        'description': metadata.get('description', ''),
                        'province': metadata.get('province', ''),
                        'image_url': metadata.get('image_url')
                    }
                    places.append(place)
            
            self.places_df = pd.DataFrame(places)
            logger.info(f"Loaded {len(places)} places from Vector DB")
            
            return places
            
        except Exception as e:
            logger.error(f"Error loading places from Vector DB: {e}")
            return []
    
    def fit_all_models(self, places: List[Dict] = None, ratings: List[Dict] = None, trips: List[Dict] = None):
        """Fit tất cả models"""
        # Load places nếu chưa có
        if places is None:
            places = self.load_places_from_vector_db()
        
        if places:
            # Fit content-based
            logger.info("Fitting content-based recommender...")
            self.content_based.fit(places)
            
            # Fit clustering
            logger.info("Fitting destination clustering...")
            self.clustering.fit(places)
        
        # Fit collaborative filtering nếu có ratings
        if ratings:
            logger.info("Fitting collaborative filtering...")
            self.collaborative.fit(ratings)
            self.ratings_df = pd.DataFrame(ratings)
        
        # Fit cost prediction nếu có trips
        if trips:
            logger.info("Fitting cost prediction model...")
            self.cost_predictor.fit(trips)
    
    def hybrid_recommend(
        self,
        user_id: Optional[int] = None,
        query_text: Optional[str] = None,
        destination: Optional[str] = None,
        n_results: int = 10,
        use_content: bool = True,
        use_collaborative: bool = False,
        use_clustering: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Hybrid recommendation combining multiple methods
        
        Returns:
            List of recommended places
        """
        results = []
        
        # Content-based
        if use_content and query_text:
            content_results = self.content_based.recommend(
                query_text=query_text,
                n_results=n_results * 2
            )
            results.extend(content_results)
        
        # Collaborative filtering
        if use_collaborative and user_id and self.ratings_df is not None:
            collab_results = self.collaborative.recommend(
                user_id=user_id,
                n_results=n_results,
                places_df=self.places_df
            )
            results.extend(collab_results)
        
        # Clustering
        if use_clustering and destination:
            # Tìm place trong cluster
            if self.places_df is not None:
                dest_places = self.places_df[
                    self.places_df['city'].str.contains(destination, case=False, na=False)
                ]
                if not dest_places.empty:
                    place = dest_places.iloc[0].to_dict()
                    cluster_results = self.clustering.get_cluster_recommendations(
                        place,
                        n_results=n_results
                    )
                    results.extend(cluster_results)
        
        # Deduplicate và rank
        seen = set()
        unique_results = []
        for result in results:
            place_id = result.get('place_id') or result.get('name', '')
            if place_id not in seen:
                seen.add(place_id)
                unique_results.append(result)
        
        # Sort by score/rating
        unique_results.sort(
            key=lambda x: x.get('similarity_score', 0) or x.get('predicted_rating', 0) or x.get('rating', 0),
            reverse=True
        )
        
        return unique_results[:n_results]
    
    def save_models(self):
        """Save models to disk"""
        model_path = self.model_dir
        
        if self.content_based.tfidf_matrix is not None:
            joblib.dump(self.content_based, model_path / 'content_based.pkl')
        
        if self.collaborative.model is not None or self.collaborative.svd_model is not None:
            joblib.dump(self.collaborative, model_path / 'collaborative.pkl')
        
        if self.cost_predictor.model is not None:
            joblib.dump(self.cost_predictor, model_path / 'cost_predictor.pkl')
        
        if self.clustering.model is not None:
            joblib.dump(self.clustering, model_path / 'clustering.pkl')
        
        logger.info("Models saved to disk")
    
    def load_models(self):
        """Load models from disk"""
        model_path = self.model_dir
        
        if (model_path / 'content_based.pkl').exists():
            self.content_based = joblib.load(model_path / 'content_based.pkl')
        
        if (model_path / 'collaborative.pkl').exists():
            self.collaborative = joblib.load(model_path / 'collaborative.pkl')
        
        if (model_path / 'cost_predictor.pkl').exists():
            self.cost_predictor = joblib.load(model_path / 'cost_predictor.pkl')
        
        if (model_path / 'clustering.pkl').exists():
            self.clustering = joblib.load(model_path / 'clustering.pkl')
        
        logger.info("Models loaded from disk")


# Singleton instance
_ml_recommender = None

def get_ml_recommender() -> MLRecommendationSystem:
    """Get singleton ML Recommendation System instance"""
    global _ml_recommender
    if _ml_recommender is None:
        _ml_recommender = MLRecommendationSystem()
    return _ml_recommender

