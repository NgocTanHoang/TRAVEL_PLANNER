import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import json
import pickle
import os
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, mean_squared_error, r2_score
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.linear_model import LogisticRegression, LinearRegression
from sklearn.svm import SVC, SVR
from sklearn.preprocessing import StandardScaler, LabelEncoder
import warnings
warnings.filterwarnings('ignore')

class ModelTrainer:
    def __init__(self, model_dir: str = 'ml_models/saved_models'):
        """Initialize Model Trainer"""
        self.model_dir = model_dir
        self.ensure_model_dir()
        
        # Initialize models
        self.models = {}
        self.scalers = {}
        self.encoders = {}
        self.model_metrics = {}
        
        # Model configurations
        self.model_configs = {
            'recommendation': {
                'type': 'classification',
                'models': {
                    'random_forest': RandomForestClassifier(n_estimators=100, random_state=42),
                    'logistic_regression': LogisticRegression(random_state=42, max_iter=1000),
                    'svm': SVC(random_state=42, probability=True)
                }
            },
            'price_prediction': {
                'type': 'regression',
                'models': {
                    'random_forest': RandomForestRegressor(n_estimators=100, random_state=42),
                    'linear_regression': LinearRegression(),
                    'svr': SVR()
                }
            },
            'sentiment_analysis': {
                'type': 'classification',
                'models': {
                    'random_forest': RandomForestClassifier(n_estimators=100, random_state=42),
                    'logistic_regression': LogisticRegression(random_state=42, max_iter=1000),
                    'svm': SVC(random_state=42, probability=True)
                }
            }
        }
        
        # Load existing models
        self.load_models()
    
    def ensure_model_dir(self):
        """Create directory model nếu chưa tồn tại"""
        if not os.path.exists(self.model_dir):
            os.makedirs(self.model_dir)
    
    def load_models(self):
        """Load models đã train"""
        try:
            # Load models
            for model_type in self.model_configs.keys():
                model_path = os.path.join(self.model_dir, f'{model_type}_model.pkl')
                if os.path.exists(model_path):
                    with open(model_path, 'rb') as f:
                        self.models[model_type] = pickle.load(f)
                
                # Load scaler
                scaler_path = os.path.join(self.model_dir, f'{model_type}_scaler.pkl')
                if os.path.exists(scaler_path):
                    with open(scaler_path, 'rb') as f:
                        self.scalers[model_type] = pickle.load(f)
                
                # Load encoder
                encoder_path = os.path.join(self.model_dir, f'{model_type}_encoder.pkl')
                if os.path.exists(encoder_path):
                    with open(encoder_path, 'rb') as f:
                        self.encoders[model_type] = pickle.load(f)
            
            print("[SUCCESS] Models loaded successfully")
        except Exception as e:
            print(f"[WARNING] Could not load models: {e}")
    
    def save_models(self):
        """Save models đã train"""
        try:
            for model_type, model in self.models.items():
                # Save model
                model_path = os.path.join(self.model_dir, f'{model_type}_model.pkl')
                with open(model_path, 'wb') as f:
                    pickle.dump(model, f)
                
                # Save scaler
                if model_type in self.scalers:
                    scaler_path = os.path.join(self.model_dir, f'{model_type}_scaler.pkl')
                    with open(scaler_path, 'wb') as f:
                        pickle.dump(self.scalers[model_type], f)
                
                # Save encoder
                if model_type in self.encoders:
                    encoder_path = os.path.join(self.model_dir, f'{model_type}_encoder.pkl')
                    with open(encoder_path, 'wb') as f:
                        pickle.dump(self.encoders[model_type], f)
            
            print("[SUCCESS] Models saved successfully")
        except Exception as e:
            print(f"[ERROR] Could not save models: {e}")
    
    def prepare_recommendation_data(self, places_data: List[Dict[str, Any]], 
                                  user_interactions: List[Dict[str, Any]]) -> Tuple[np.ndarray, np.ndarray]:
        """Chuẩn bị data cho recommendation model"""
        features = []
        labels = []
        
        # Create user-item interaction matrix
        user_item_matrix = {}
        for interaction in user_interactions:
            user_id = interaction.get('user_id', '')
            place_id = interaction.get('place_id', '')
            rating = interaction.get('rating', 0)
            
            if user_id not in user_item_matrix:
                user_item_matrix[user_id] = {}
            user_item_matrix[user_id][place_id] = rating
        
        # Prepare features and labels
        for place in places_data:
            place_id = place.get('place_id', '')
            
            # Place features
            place_features = [
                place.get('rating', 0),
                place.get('price_level', 0),
                place.get('popularity_score', 0),
                1 if 'historical' in str(place.get('category', '')).lower() else 0,
                1 if 'museum' in str(place.get('category', '')).lower() else 0,
                1 if 'park' in str(place.get('category', '')).lower() else 0,
                1 if 'temple' in str(place.get('category', '')).lower() else 0,
                1 if 'market' in str(place.get('category', '')).lower() else 0
            ]
            
            # User interaction features (simplified)
            user_ratings = [rating for ratings in user_item_matrix.values() for place_id_key, rating in ratings.items() if place_id_key == place_id]
            avg_user_rating = np.mean(user_ratings) if user_ratings else 0
            user_count = len(user_ratings)
            
            # Combine features
            combined_features = place_features + [avg_user_rating, user_count]
            features.append(combined_features)
            
            # Label: 1 if recommended (rating > 3), 0 otherwise
            label = 1 if place.get('rating', 0) > 3.0 else 0
            labels.append(label)
        
        return np.array(features), np.array(labels)
    
    def prepare_price_data(self, places_data: List[Dict[str, Any]], 
                          price_type: str = 'hotel') -> Tuple[np.ndarray, np.ndarray]:
        """Chuẩn bị data cho price prediction model"""
        features = []
        prices = []
        
        for place in places_data:
            if price_type == 'hotel':
                price = place.get('price_per_night', 0)
                if price > 0:
                    # Hotel features
                    place_features = [
                        place.get('rating', 0),
                        place.get('star_rating', 0),
                        len(place.get('amenities', [])),
                        1 if 'pool' in str(place.get('amenities', [])).lower() else 0,
                        1 if 'spa' in str(place.get('amenities', [])).lower() else 0,
                        1 if 'gym' in str(place.get('amenities', [])).lower() else 0,
                        1 if 'restaurant' in str(place.get('amenities', [])).lower() else 0,
                        1 if 'center' in str(place.get('address', '')).lower() else 0
                    ]
                    features.append(place_features)
                    prices.append(price)
            
            elif price_type == 'restaurant':
                price_range = place.get('price_range', '$')
                price_level = len(price_range)
                if price_level > 0:
                    # Restaurant features
                    place_features = [
                        place.get('rating', 0),
                        len(place.get('menu', [])),
                        1 if place.get('menu') else 0,
                        1 if 'vietnamese' in str(place.get('cuisine', '')).lower() else 0,
                        1 if any(cuisine in str(place.get('cuisine', '')).lower() 
                               for cuisine in ['japanese', 'korean', 'chinese', 'italian']) else 0,
                        place.get('popularity_score', 0)
                    ]
                    features.append(place_features)
                    prices.append(price_level)
        
        return np.array(features), np.array(prices)
    
    def prepare_sentiment_data(self, reviews_data: List[Dict[str, Any]]) -> Tuple[np.ndarray, np.ndarray]:
        """Chuẩn bị data cho sentiment analysis model"""
        features = []
        labels = []
        
        for review in reviews_data:
            text = review.get('comment', '') or review.get('review_text', '') or review.get('content', '')
            rating = review.get('rating', 0)
            
            if text and rating > 0:
                # Text features (simplified)
                text_features = [
                    len(text),  # Text length
                    text.count('!'),  # Exclamation marks
                    text.count('?'),  # Question marks
                    text.count(' '),  # Word count (approximate)
                    rating  # Rating as feature
                ]
                
                features.append(text_features)
                
                # Label: 1 if positive (rating > 3), 0 otherwise
                label = 1 if rating > 3 else 0
                labels.append(label)
        
        return np.array(features), np.array(labels)
    
    def train_recommendation_model(self, places_data: List[Dict[str, Any]], 
                                 user_interactions: List[Dict[str, Any]]):
        """Train recommendation model"""
        print("[MATCH] Training recommendation model...")
        
        # Prepare data
        X, y = self.prepare_recommendation_data(places_data, user_interactions)
        
        if len(X) < 20:
            print("[WARNING] Not enough data to train recommendation model")
            return
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Train models
        best_model = None
        best_score = 0
        best_model_name = ""
        
        for model_name, model in self.model_configs['recommendation']['models'].items():
            print(f"   Training {model_name}...")
            
            # Train model
            model.fit(X_train_scaled, y_train)
            
            # Evaluate model
            y_pred = model.predict(X_test_scaled)
            accuracy = accuracy_score(y_test, y_pred)
            
            print(f"   {model_name} accuracy: {accuracy:.3f}")
            
            if accuracy > best_score:
                best_score = accuracy
                best_model = model
                best_model_name = model_name
        
        # Save best model
        self.models['recommendation'] = best_model
        self.scalers['recommendation'] = scaler
        self.model_metrics['recommendation'] = {
            'best_model': best_model_name,
            'accuracy': best_score,
            'trained_at': datetime.now().isoformat()
        }
        
        print(f"[SUCCESS] Recommendation model trained - Best: {best_model_name} (accuracy: {best_score:.3f})")
        
        # Save models
        self.save_models()
    
    def train_price_model(self, places_data: List[Dict[str, Any]], price_type: str = 'hotel'):
        """Train price prediction model"""
        print(f"[BUDGET] Training {price_type} price prediction model...")
        
        # Prepare data
        X, y = self.prepare_price_data(places_data, price_type)
        
        if len(X) < 20:
            print(f"[WARNING] Not enough data to train {price_type} price model")
            return
        
        # Remove outliers
        Q1 = np.percentile(y, 25)
        Q3 = np.percentile(y, 75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        mask = (y >= lower_bound) & (y <= upper_bound)
        X = X[mask]
        y = y[mask]
        
        if len(X) < 10:
            print(f"[WARNING] Not enough data after outlier removal for {price_type} price model")
            return
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Train models
        best_model = None
        best_score = float('inf')
        best_model_name = ""
        
        for model_name, model in self.model_configs['price_prediction']['models'].items():
            print(f"   Training {model_name}...")
            
            # Train model
            model.fit(X_train_scaled, y_train)
            
            # Evaluate model
            y_pred = model.predict(X_test_scaled)
            mse = mean_squared_error(y_test, y_pred)
            r2 = r2_score(y_test, y_pred)
            
            print(f"   {model_name} MSE: {mse:.3f}, R²: {r2:.3f}")
            
            if mse < best_score:
                best_score = mse
                best_model = model
                best_model_name = model_name
        
        # Save best model
        model_key = f'price_{price_type}'
        self.models[model_key] = best_model
        self.scalers[model_key] = scaler
        self.model_metrics[model_key] = {
            'best_model': best_model_name,
            'mse': best_score,
            'trained_at': datetime.now().isoformat()
        }
        
        print(f"[SUCCESS] {price_type} price model trained - Best: {best_model_name} (MSE: {best_score:.3f})")
        
        # Save models
        self.save_models()
    
    def train_sentiment_model(self, reviews_data: List[Dict[str, Any]]):
        """Train sentiment analysis model"""
        print("😊 Training sentiment analysis model...")
        
        # Prepare data
        X, y = self.prepare_sentiment_data(reviews_data)
        
        if len(X) < 20:
            print("[WARNING] Not enough data to train sentiment model")
            return
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        # Scale features
        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        
        # Train models
        best_model = None
        best_score = 0
        best_model_name = ""
        
        for model_name, model in self.model_configs['sentiment_analysis']['models'].items():
            print(f"   Training {model_name}...")
            
            # Train model
            model.fit(X_train_scaled, y_train)
            
            # Evaluate model
            y_pred = model.predict(X_test_scaled)
            accuracy = accuracy_score(y_test, y_pred)
            f1 = f1_score(y_test, y_pred)
            
            print(f"   {model_name} accuracy: {accuracy:.3f}, F1: {f1:.3f}")
            
            if accuracy > best_score:
                best_score = accuracy
                best_model = model
                best_model_name = model_name
        
        # Save best model
        self.models['sentiment'] = best_model
        self.scalers['sentiment'] = scaler
        self.model_metrics['sentiment'] = {
            'best_model': best_model_name,
            'accuracy': best_score,
            'trained_at': datetime.now().isoformat()
        }
        
        print(f"[SUCCESS] Sentiment model trained - Best: {best_model_name} (accuracy: {best_score:.3f})")
        
        # Save models
        self.save_models()
    
    def train_all_models(self, places_data: List[Dict[str, Any]], 
                        user_interactions: List[Dict[str, Any]], 
                        reviews_data: List[Dict[str, Any]]):
        """Train tất cả models"""
        print("[TRAINING] Training all ML models...")
        
        # Train recommendation model
        self.train_recommendation_model(places_data, user_interactions)
        
        # Train price models
        self.train_price_model(places_data, 'hotel')
        self.train_price_model(places_data, 'restaurant')
        
        # Train sentiment model
        self.train_sentiment_model(reviews_data)
        
        print("[SUCCESS] All models training completed!")
    
    def evaluate_model(self, model_type: str, X_test: np.ndarray, y_test: np.ndarray) -> Dict[str, Any]:
        """Đánh giá model performance"""
        if model_type not in self.models:
            return {'error': f'Model {model_type} not found'}
        
        model = self.models[model_type]
        scaler = self.scalers.get(model_type)
        
        if scaler:
            X_test_scaled = scaler.transform(X_test)
        else:
            X_test_scaled = X_test
        
        # Make predictions
        y_pred = model.predict(X_test_scaled)
        
        # Calculate metrics
        if self.model_configs.get(model_type, {}).get('type') == 'classification':
            metrics = {
                'accuracy': accuracy_score(y_test, y_pred),
                'precision': precision_score(y_test, y_pred, average='weighted'),
                'recall': recall_score(y_test, y_pred, average='weighted'),
                'f1_score': f1_score(y_test, y_pred, average='weighted')
            }
        else:  # regression
            metrics = {
                'mse': mean_squared_error(y_test, y_pred),
                'rmse': np.sqrt(mean_squared_error(y_test, y_pred)),
                'r2_score': r2_score(y_test, y_pred)
            }
        
        return metrics
    
    def get_model_performance(self) -> Dict[str, Any]:
        """Lấy performance của tất cả models"""
        return self.model_metrics
    
    def get_model_info(self) -> Dict[str, Any]:
        """Lấy thông tin về tất cả models"""
        info = {
            'total_models': len(self.models),
            'model_types': list(self.models.keys()),
            'model_configs': self.model_configs,
            'models_loaded': {model_type: model is not None for model_type, model in self.models.items()},
            'scalers_loaded': {model_type: scaler is not None for model_type, scaler in self.scalers.items()},
            'encoders_loaded': {model_type: encoder is not None for model_type, encoder in self.encoders.items()}
        }
        
        return info
    
    def predict_recommendation(self, place_features: List[float]) -> Dict[str, Any]:
        """Dự đoán recommendation"""
        if 'recommendation' not in self.models:
            return {'error': 'Recommendation model not trained'}
        
        try:
            model = self.models['recommendation']
            scaler = self.scalers['recommendation']
            
            # Scale features
            X = np.array(place_features).reshape(1, -1)
            X_scaled = scaler.transform(X)
            
            # Make prediction
            prediction = model.predict(X_scaled)[0]
            probability = model.predict_proba(X_scaled)[0] if hasattr(model, 'predict_proba') else [0.5, 0.5]
            
            return {
                'recommendation': int(prediction),
                'confidence': float(max(probability)),
                'probability_positive': float(probability[1]),
                'probability_negative': float(probability[0])
            }
        except Exception as e:
            return {'error': str(e)}
    
    def predict_price(self, place_features: List[float], price_type: str = 'hotel') -> Dict[str, Any]:
        """Dự đoán giá"""
        model_key = f'price_{price_type}'
        if model_key not in self.models:
            return {'error': f'{price_type} price model not trained'}
        
        try:
            model = self.models[model_key]
            scaler = self.scalers[model_key]
            
            # Scale features
            X = np.array(place_features).reshape(1, -1)
            X_scaled = scaler.transform(X)
            
            # Make prediction
            prediction = model.predict(X_scaled)[0]
            
            return {
                'predicted_price': float(prediction),
                'price_type': price_type,
                'currency': 'USD'
            }
        except Exception as e:
            return {'error': str(e)}
    
    def predict_sentiment(self, text_features: List[float]) -> Dict[str, Any]:
        """Dự đoán sentiment"""
        if 'sentiment' not in self.models:
            return {'error': 'Sentiment model not trained'}
        
        try:
            model = self.models['sentiment']
            scaler = self.scalers['sentiment']
            
            # Scale features
            X = np.array(text_features).reshape(1, -1)
            X_scaled = scaler.transform(X)
            
            # Make prediction
            prediction = model.predict(X_scaled)[0]
            probability = model.predict_proba(X_scaled)[0] if hasattr(model, 'predict_proba') else [0.5, 0.5]
            
            return {
                'sentiment': int(prediction),
                'confidence': float(max(probability)),
                'probability_positive': float(probability[1]),
                'probability_negative': float(probability[0])
            }
        except Exception as e:
            return {'error': str(e)}
