import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity, euclidean_distances
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import pickle
import os

class SimilarityEngine:
    def __init__(self, model_dir: str = 'ml_models/saved_models'):
        """Initialize Similarity Engine"""
        self.model_dir = model_dir
        self.ensure_model_dir()
        
        # Initialize models
        self.tfidf_vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        self.scaler = StandardScaler()
        self.pca = PCA(n_components=50)
        
        # Similarity weights
        self.similarity_weights = {
            'content': 0.4,
            'location': 0.3,
            'category': 0.2,
            'rating': 0.1
        }
        
        # Load models
        self.load_models()
    
    def ensure_model_dir(self):
        """Create directory model nếu chưa tồn tại"""
        if not os.path.exists(self.model_dir):
            os.makedirs(self.model_dir)
    
    def load_models(self):
        """Load models đã train"""
        try:
            # Load TF-IDF vectorizer
            tfidf_path = os.path.join(self.model_dir, 'similarity_tfidf.pkl')
            if os.path.exists(tfidf_path):
                with open(tfidf_path, 'rb') as f:
                    self.tfidf_vectorizer = pickle.load(f)
            
            # Load scaler
            scaler_path = os.path.join(self.model_dir, 'similarity_scaler.pkl')
            if os.path.exists(scaler_path):
                with open(scaler_path, 'rb') as f:
                    self.scaler = pickle.load(f)
            
            # Load PCA
            pca_path = os.path.join(self.model_dir, 'similarity_pca.pkl')
            if os.path.exists(pca_path):
                with open(pca_path, 'rb') as f:
                    self.pca = pickle.load(f)
            
            print("[SUCCESS] Similarity models loaded successfully")
        except Exception as e:
            print(f"[WARNING] Could not load similarity models: {e}")
    
    def save_models(self):
        """Save models đã train"""
        try:
            # Save TF-IDF vectorizer
            tfidf_path = os.path.join(self.model_dir, 'similarity_tfidf.pkl')
            with open(tfidf_path, 'wb') as f:
                pickle.dump(self.tfidf_vectorizer, f)
            
            # Save scaler
            scaler_path = os.path.join(self.model_dir, 'similarity_scaler.pkl')
            with open(scaler_path, 'wb') as f:
                pickle.dump(self.scaler, f)
            
            # Save PCA
            pca_path = os.path.join(self.model_dir, 'similarity_pca.pkl')
            with open(pca_path, 'wb') as f:
                pickle.dump(self.pca, f)
            
            print("[SUCCESS] Similarity models saved successfully")
        except Exception as e:
            print(f"[ERROR] Could not save similarity models: {e}")
    
    def prepare_features(self, places_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """Prepare features cho similarity calculation"""
        features = []
        
        for place in places_data:
            feature = {
                'place_id': place.get('place_id', ''),
                'name': place.get('name', ''),
                'city': place.get('city', ''),
                'category': place.get('category', ''),
                'rating': place.get('rating', 0),
                'price_level': place.get('price_level', 0),
                'latitude': place.get('latitude', 0),
                'longitude': place.get('longitude', 0),
                'types': ', '.join(place.get('types', [])),
                'description': f"{place.get('name', '')} {place.get('category', '')} {', '.join(place.get('types', []))}",
                'popularity_score': place.get('popularity_score', 0)
            }
            features.append(feature)
        
        return pd.DataFrame(features)
    
    def train_models(self, places_data: List[Dict[str, Any]]):
        """Train similarity models"""
        print("[TRAINING] Training similarity models...")
        
        # Prepare features
        df = self.prepare_features(places_data)
        
        if len(df) < 10:
            print("[WARNING] Not enough data to train similarity models")
            return
        
        # Train TF-IDF vectorizer
        print("[TFIDF] Training TF-IDF vectorizer...")
        descriptions = df['description'].fillna('')
        self.tfidf_vectorizer.fit(descriptions)
        
        # Prepare numerical features
        numerical_features = ['rating', 'price_level', 'latitude', 'longitude', 'popularity_score']
        X_numerical = df[numerical_features].fillna(0)
        
        # Train scaler
        print("[SCALER] Training scaler...")
        self.scaler.fit(X_numerical)
        
        # Train PCA
        print("[MATCH] Training PCA...")
        X_scaled = self.scaler.transform(X_numerical)
        self.pca.fit(X_scaled)
        
        # Save models
        self.save_models()
        
        print("[SUCCESS] Similarity models training completed!")
    
    def calculate_content_similarity(self, place1: Dict[str, Any], place2: Dict[str, Any]) -> float:
        """Tính content similarity giữa 2 places"""
        try:
            # Create descriptions
            desc1 = f"{place1.get('name', '')} {place1.get('category', '')} {', '.join(place1.get('types', []))}"
            desc2 = f"{place2.get('name', '')} {place2.get('category', '')} {', '.join(place2.get('types', []))}"
            
            # Vectorize descriptions
            descriptions = [desc1, desc2]
            tfidf_matrix = self.tfidf_vectorizer.transform(descriptions)
            
            # Calculate cosine similarity
            similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
            
            return similarity
        except Exception as e:
            print(f"[ERROR] Error calculating content similarity: {e}")
            return 0.0
    
    def calculate_location_similarity(self, place1: Dict[str, Any], place2: Dict[str, Any]) -> float:
        """Tính location similarity giữa 2 places"""
        try:
            lat1, lon1 = place1.get('latitude', 0), place1.get('longitude', 0)
            lat2, lon2 = place2.get('latitude', 0), place2.get('longitude', 0)
            
            if lat1 == 0 or lon1 == 0 or lat2 == 0 or lon2 == 0:
                return 0.0
            
            # Calculate distance using Haversine formula
            distance = self._calculate_distance(lat1, lon1, lat2, lon2)
            
            # Convert distance to similarity (closer = more similar)
            # Max distance for similarity calculation: 50km
            max_distance = 50
            similarity = max(0, 1 - (distance / max_distance))
            
            return similarity
        except Exception as e:
            print(f"[ERROR] Error calculating location similarity: {e}")
            return 0.0
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Tính khoảng cách giữa 2 điểm (Haversine formula)"""
        from math import radians, cos, sin, asin, sqrt
        
        # Convert to radians
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        
        # Radius of earth in kilometers
        r = 6371
        
        return c * r
    
    def calculate_category_similarity(self, place1: Dict[str, Any], place2: Dict[str, Any]) -> float:
        """Tính category similarity giữa 2 places"""
        try:
            category1 = place1.get('category', '')
            category2 = place2.get('category', '')
            
            if not category1 or not category2:
                return 0.0
            
            # Exact match
            if category1 == category2:
                return 1.0
            
            # Similar categories
            similar_categories = {
                'Địa điểm du lịch': ['Bảo tàng', 'Công viên', 'Di tích lịch sử'],
                'Bảo tàng': ['Di tích lịch sử', 'Địa điểm du lịch'],
                'Công viên': ['Cảnh quan thiên nhiên', 'Địa điểm du lịch'],
                'Chùa/Đền': ['Di tích lịch sử', 'Địa điểm du lịch'],
                'Chợ': ['Trung tâm thương mại', 'Địa điểm du lịch']
            }
            
            for main_cat, sub_cats in similar_categories.items():
                if (category1 == main_cat and category2 in sub_cats) or \
                   (category2 == main_cat and category1 in sub_cats):
                    return 0.7
            
            return 0.0
        except Exception as e:
            print(f"[ERROR] Error calculating category similarity: {e}")
            return 0.0
    
    def calculate_rating_similarity(self, place1: Dict[str, Any], place2: Dict[str, Any]) -> float:
        """Tính rating similarity giữa 2 places"""
        try:
            rating1 = place1.get('rating', 0)
            rating2 = place2.get('rating', 0)
            
            if rating1 == 0 or rating2 == 0:
                return 0.0
            
            # Calculate similarity based on rating difference
            rating_diff = abs(rating1 - rating2)
            similarity = max(0, 1 - (rating_diff / 5.0))  # Max difference is 5.0
            
            return similarity
        except Exception as e:
            print(f"[ERROR] Error calculating rating similarity: {e}")
            return 0.0
    
    def calculate_overall_similarity(self, place1: Dict[str, Any], place2: Dict[str, Any]) -> float:
        """Tính overall similarity giữa 2 places"""
        try:
            # Calculate individual similarities
            content_sim = self.calculate_content_similarity(place1, place2)
            location_sim = self.calculate_location_similarity(place1, place2)
            category_sim = self.calculate_category_similarity(place1, place2)
            rating_sim = self.calculate_rating_similarity(place1, place2)
            
            # Weighted combination
            overall_similarity = (
                content_sim * self.similarity_weights['content'] +
                location_sim * self.similarity_weights['location'] +
                category_sim * self.similarity_weights['category'] +
                rating_sim * self.similarity_weights['rating']
            )
            
            return overall_similarity
        except Exception as e:
            print(f"[ERROR] Error calculating overall similarity: {e}")
            return 0.0
    
    def find_similar_places(self, target_place: Dict[str, Any], 
                          places_data: List[Dict[str, Any]], 
                          top_k: int = 10) -> List[Dict[str, Any]]:
        """Find similar places với target place"""
        if not places_data:
            return []
        
        similarities = []
        
        for place in places_data:
            if place.get('place_id') != target_place.get('place_id'):
                similarity = self.calculate_overall_similarity(target_place, place)
                place['similarity_score'] = similarity
                similarities.append(place)
        
        # Sort by similarity score
        similarities.sort(key=lambda x: x.get('similarity_score', 0), reverse=True)
        
        return similarities[:top_k]
    
    def get_place_clusters(self, places_data: List[Dict[str, Any]], 
                          n_clusters: int = 5) -> Dict[str, List[Dict[str, Any]]]:
        """Phân nhóm places thành clusters"""
        if not places_data or len(places_data) < n_clusters:
            return {}
        
        try:
            from sklearn.cluster import KMeans
            
            # Prepare features
            df = self.prepare_features(places_data)
            
            # Create feature matrix
            descriptions = df['description'].fillna('')
            tfidf_matrix = self.tfidf_vectorizer.transform(descriptions)
            
            # Add numerical features
            numerical_features = ['rating', 'price_level', 'latitude', 'longitude', 'popularity_score']
            X_numerical = df[numerical_features].fillna(0)
            X_scaled = self.scaler.transform(X_numerical)
            
            # Combine features
            X_combined = np.hstack([tfidf_matrix.toarray(), X_scaled])
            
            # Apply PCA
            X_pca = self.pca.transform(X_combined)
            
            # KMeans clustering
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            cluster_labels = kmeans.fit_predict(X_pca)
            
            # Group places by cluster
            clusters = {}
            for i, place in enumerate(places_data):
                cluster_id = f"cluster_{cluster_labels[i]}"
                if cluster_id not in clusters:
                    clusters[cluster_id] = []
                place['cluster_id'] = cluster_id
                clusters[cluster_id].append(place)
            
            return clusters
        except Exception as e:
            print(f"[ERROR] Error creating place clusters: {e}")
            return {}
    
    def get_similarity_matrix(self, places_data: List[Dict[str, Any]]) -> np.ndarray:
        """Tạo similarity matrix cho tất cả places"""
        if not places_data:
            return np.array([])
        
        n = len(places_data)
        similarity_matrix = np.zeros((n, n))
        
        for i in range(n):
            for j in range(n):
                if i != j:
                    similarity = self.calculate_overall_similarity(places_data[i], places_data[j])
                    similarity_matrix[i][j] = similarity
                else:
                    similarity_matrix[i][j] = 1.0  # Self-similarity
        
        return similarity_matrix
    
    def get_similarity_insights(self, places_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Tạo insights từ similarity analysis"""
        if not places_data:
            return {'insights': [], 'summary': 'No places available for analysis'}
        
        insights = []
        
        # Calculate similarity matrix
        similarity_matrix = self.get_similarity_matrix(places_data)
        
        if similarity_matrix.size > 0:
            # Insight 1: Average similarity
            avg_similarity = np.mean(similarity_matrix[np.triu_indices_from(similarity_matrix, k=1)])
            if avg_similarity > 0.7:
                insights.append("🔗 High similarity among places - many similar attractions")
            elif avg_similarity < 0.3:
                insights.append("[MATCH] Low similarity among places - diverse attractions")
            else:
                insights.append("[SCALER] Moderate similarity among places - balanced variety")
            
            # Insight 2: Most similar pair
            max_similarity = np.max(similarity_matrix[np.triu_indices_from(similarity_matrix, k=1)])
            if max_similarity > 0.8:
                insights.append("👥 Very similar places found - potential duplicates")
            
            # Insight 3: Similarity distribution
            similarities = similarity_matrix[np.triu_indices_from(similarity_matrix, k=1)]
            high_sim_count = np.sum(similarities > 0.7)
            if high_sim_count > len(places_data) * 0.3:
                insights.append("🔄 Many highly similar places - consider grouping")
        
        # Insight 4: Category diversity
        categories = [place.get('category', '') for place in places_data]
        unique_categories = len(set(categories))
        if unique_categories < len(places_data) * 0.5:
            insights.append("🏷️ Limited category diversity - consider adding more variety")
        
        return {
            'insights': insights,
            'summary': f"Analyzed {len(places_data)} places with {unique_categories} unique categories",
            'average_similarity': float(avg_similarity) if similarity_matrix.size > 0 else 0,
            'max_similarity': float(max_similarity) if similarity_matrix.size > 0 else 0
        }
    
    def get_model_info(self) -> Dict[str, Any]:
        """Lấy thông tin về similarity models"""
        return {
            'model_type': 'similarity_engine',
            'components': ['tfidf_vectorizer', 'scaler', 'pca'],
            'similarity_weights': self.similarity_weights,
            'max_features': self.tfidf_vectorizer.max_features,
            'pca_components': self.pca.n_components if hasattr(self.pca, 'n_components') else 50,
            'models_loaded': all([
                hasattr(self.tfidf_vectorizer, 'vocabulary_'),
                hasattr(self.scaler, 'scale_'),
                hasattr(self.pca, 'components_')
            ])
        }

