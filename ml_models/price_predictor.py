import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import LinearRegression, Ridge
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import pickle
import os

class PricePredictor:
    def __init__(self, model_dir: str = 'ml_models/saved_models'):
        """Initialize Price Predictor"""
        self.model_dir = model_dir
        self.ensure_model_dir()
        
        # Initialize models
        self.hotel_model = RandomForestRegressor(n_estimators=100, random_state=42)
        self.restaurant_model = GradientBoostingRegressor(n_estimators=100, random_state=42)
        self.activity_model = LinearRegression()
        
        # Preprocessing
        self.scaler = StandardScaler()
        self.city_encoder = LabelEncoder()
        self.category_encoder = LabelEncoder()
        
        # Feature importance
        self.feature_importance = {}
        
        # Load models
        self.load_models()
    
    def ensure_model_dir(self):
        """Create directory model nếu chưa tồn tại"""
        if not os.path.exists(self.model_dir):
            os.makedirs(self.model_dir)
    
    def load_models(self):
        """Load models đã train"""
        try:
            # Load hotel model
            hotel_path = os.path.join(self.model_dir, 'hotel_price_model.pkl')
            if os.path.exists(hotel_path):
                with open(hotel_path, 'rb') as f:
                    self.hotel_model = pickle.load(f)
            
            # Load restaurant model
            restaurant_path = os.path.join(self.model_dir, 'restaurant_price_model.pkl')
            if os.path.exists(restaurant_path):
                with open(restaurant_path, 'rb') as f:
                    self.restaurant_model = pickle.load(f)
            
            # Load activity model
            activity_path = os.path.join(self.model_dir, 'activity_price_model.pkl')
            if os.path.exists(activity_path):
                with open(activity_path, 'rb') as f:
                    self.activity_model = pickle.load(f)
            
            # Load scaler
            scaler_path = os.path.join(self.model_dir, 'price_scaler.pkl')
            if os.path.exists(scaler_path):
                with open(scaler_path, 'rb') as f:
                    self.scaler = pickle.load(f)
            
            # Load encoders
            city_encoder_path = os.path.join(self.model_dir, 'city_encoder.pkl')
            if os.path.exists(city_encoder_path):
                with open(city_encoder_path, 'rb') as f:
                    self.city_encoder = pickle.load(f)
            
            category_encoder_path = os.path.join(self.model_dir, 'category_encoder.pkl')
            if os.path.exists(category_encoder_path):
                with open(category_encoder_path, 'rb') as f:
                    self.category_encoder = pickle.load(f)
            
            print("[SUCCESS] Price prediction models loaded successfully")
        except Exception as e:
            print(f"[WARNING] Could not load price models: {e}")
    
    def save_models(self):
        """Save models đã train"""
        try:
            # Save models
            with open(os.path.join(self.model_dir, 'hotel_price_model.pkl'), 'wb') as f:
                pickle.dump(self.hotel_model, f)
            
            with open(os.path.join(self.model_dir, 'restaurant_price_model.pkl'), 'wb') as f:
                pickle.dump(self.restaurant_model, f)
            
            with open(os.path.join(self.model_dir, 'activity_price_model.pkl'), 'wb') as f:
                pickle.dump(self.activity_model, f)
            
            # Save scaler
            with open(os.path.join(self.model_dir, 'price_scaler.pkl'), 'wb') as f:
                pickle.dump(self.scaler, f)
            
            # Save encoders
            with open(os.path.join(self.model_dir, 'city_encoder.pkl'), 'wb') as f:
                pickle.dump(self.city_encoder, f)
            
            with open(os.path.join(self.model_dir, 'category_encoder.pkl'), 'wb') as f:
                pickle.dump(self.category_encoder, f)
            
            print("[SUCCESS] Price prediction models saved successfully")
        except Exception as e:
            print(f"[ERROR] Could not save price models: {e}")
    
    def prepare_hotel_features(self, hotels_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """Prepare features cho hotel price prediction"""
        features = []
        
        for hotel in hotels_data:
            feature = {
                'hotel_id': hotel.get('hotel_id', ''),
                'name': hotel.get('name', ''),
                'city': hotel.get('city', ''),
                'rating': hotel.get('rating', 0),
                'star_rating': hotel.get('star_rating', 0),
                'amenities_count': len(hotel.get('amenities', [])),
                'has_pool': 1 if 'pool' in str(hotel.get('amenities', [])).lower() else 0,
                'has_spa': 1 if 'spa' in str(hotel.get('amenities', [])).lower() else 0,
                'has_gym': 1 if 'gym' in str(hotel.get('amenities', [])).lower() else 0,
                'has_restaurant': 1 if 'restaurant' in str(hotel.get('amenities', [])).lower() else 0,
                'has_wifi': 1 if 'wifi' in str(hotel.get('amenities', [])).lower() else 0,
                'is_center': 1 if 'center' in str(hotel.get('address', '')).lower() else 0,
                'is_airport': 1 if 'airport' in str(hotel.get('address', '')).lower() else 0,
                'price_per_night': hotel.get('price_per_night', 0)
            }
            features.append(feature)
        
        return pd.DataFrame(features)
    
    def prepare_restaurant_features(self, restaurants_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """Prepare features cho restaurant price prediction"""
        features = []
        
        for restaurant in restaurants_data:
            feature = {
                'restaurant_id': restaurant.get('restaurant_id', ''),
                'name': restaurant.get('name', ''),
                'city': restaurant.get('city', ''),
                'rating': restaurant.get('rating', 0),
                'cuisine': restaurant.get('cuisine', ''),
                'menu_items_count': len(restaurant.get('menu', [])),
                'has_menu': 1 if restaurant.get('menu') else 0,
                'is_vietnamese': 1 if 'vietnamese' in str(restaurant.get('cuisine', '')).lower() else 0,
                'is_international': 1 if any(cuisine in str(restaurant.get('cuisine', '')).lower() 
                                           for cuisine in ['japanese', 'korean', 'chinese', 'italian']) else 0,
                'price_range': len(restaurant.get('price_range', '$')),
                'popularity_score': restaurant.get('popularity_score', 0)
            }
            features.append(feature)
        
        return pd.DataFrame(features)
    
    def prepare_activity_features(self, activities_data: List[Dict[str, Any]]) -> pd.DataFrame:
        """Prepare features cho activity price prediction"""
        features = []
        
        for activity in activities_data:
            feature = {
                'activity_id': activity.get('place_id', ''),
                'name': activity.get('name', ''),
                'city': activity.get('city', ''),
                'rating': activity.get('rating', 0),
                'category': activity.get('category', ''),
                'price_level': activity.get('price_level', 0),
                'is_historical': 1 if 'historical' in str(activity.get('category', '')).lower() else 0,
                'is_museum': 1 if 'museum' in str(activity.get('category', '')).lower() else 0,
                'is_park': 1 if 'park' in str(activity.get('category', '')).lower() else 0,
                'is_temple': 1 if 'temple' in str(activity.get('category', '')).lower() else 0,
                'is_market': 1 if 'market' in str(activity.get('category', '')).lower() else 0,
                'popularity_score': activity.get('popularity_score', 0)
            }
            features.append(feature)
        
        return pd.DataFrame(features)
    
    def train_hotel_model(self, hotels_data: List[Dict[str, Any]]):
        """Train hotel price prediction model"""
        print("🏨 Training hotel price prediction model...")
        
        # Prepare features
        df = self.prepare_hotel_features(hotels_data)
        
        if len(df) < 20:
            print("[WARNING] Not enough hotel data to train model")
            return
        
        # Prepare features and target
        feature_columns = ['rating', 'star_rating', 'amenities_count', 'has_pool', 
                          'has_spa', 'has_gym', 'has_restaurant', 'has_wifi', 
                          'is_center', 'is_airport']
        
        X = df[feature_columns].fillna(0)
        y = df['price_per_night'].fillna(0)
        
        # Remove outliers
        Q1 = y.quantile(0.25)
        Q3 = y.quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        mask = (y >= lower_bound) & (y <= upper_bound)
        X = X[mask]
        y = y[mask]
        
        if len(X) < 10:
            print("[WARNING] Not enough data after outlier removal")
            return
        
        # Train model
        self.hotel_model.fit(X, y)
        
        # Calculate feature importance
        if hasattr(self.hotel_model, 'feature_importances_'):
            self.feature_importance['hotel'] = dict(zip(feature_columns, self.hotel_model.feature_importances_))
        
        # Evaluate model
        y_pred = self.hotel_model.predict(X)
        mse = mean_squared_error(y, y_pred)
        mae = mean_absolute_error(y, y_pred)
        r2 = r2_score(y, y_pred)
        
        print(f"[SUCCESS] Hotel model trained - MSE: {mse:.2f}, MAE: {mae:.2f}, R²: {r2:.3f}")
        
        # Save model
        self.save_models()
    
    def train_restaurant_model(self, restaurants_data: List[Dict[str, Any]]):
        """Train restaurant price prediction model"""
        print("🍜 Training restaurant price prediction model...")
        
        # Prepare features
        df = self.prepare_restaurant_features(restaurants_data)
        
        if len(df) < 20:
            print("[WARNING] Not enough restaurant data to train model")
            return
        
        # Prepare features and target
        feature_columns = ['rating', 'menu_items_count', 'has_menu', 'is_vietnamese', 
                          'is_international', 'price_range', 'popularity_score']
        
        X = df[feature_columns].fillna(0)
        y = df['price_range'].fillna(1)  # Use price_range as target
        
        # Train model
        self.restaurant_model.fit(X, y)
        
        # Calculate feature importance
        if hasattr(self.restaurant_model, 'feature_importances_'):
            self.feature_importance['restaurant'] = dict(zip(feature_columns, self.restaurant_model.feature_importances_))
        
        # Evaluate model
        y_pred = self.restaurant_model.predict(X)
        mse = mean_squared_error(y, y_pred)
        mae = mean_absolute_error(y, y_pred)
        r2 = r2_score(y, y_pred)
        
        print(f"[SUCCESS] Restaurant model trained - MSE: {mse:.2f}, MAE: {mae:.2f}, R²: {r2:.3f}")
        
        # Save model
        self.save_models()
    
    def train_activity_model(self, activities_data: List[Dict[str, Any]]):
        """Train activity price prediction model"""
        print("[MATCH] Training activity price prediction model...")
        
        # Prepare features
        df = self.prepare_activity_features(activities_data)
        
        if len(df) < 20:
            print("[WARNING] Not enough activity data to train model")
            return
        
        # Prepare features and target
        feature_columns = ['rating', 'is_historical', 'is_museum', 'is_park', 
                          'is_temple', 'is_market', 'popularity_score']
        
        X = df[feature_columns].fillna(0)
        y = df['price_level'].fillna(0)
        
        # Train model
        self.activity_model.fit(X, y)
        
        # Evaluate model
        y_pred = self.activity_model.predict(X)
        mse = mean_squared_error(y, y_pred)
        mae = mean_absolute_error(y, y_pred)
        r2 = r2_score(y, y_pred)
        
        print(f"[SUCCESS] Activity model trained - MSE: {mse:.2f}, MAE: {mae:.2f}, R²: {r2:.3f}")
        
        # Save model
        self.save_models()
    
    def predict_hotel_price(self, hotel_data: Dict[str, Any]) -> Dict[str, Any]:
        """Dự đoán giá khách sạn"""
        try:
            # Prepare features
            feature_columns = ['rating', 'star_rating', 'amenities_count', 'has_pool', 
                              'has_spa', 'has_gym', 'has_restaurant', 'has_wifi', 
                              'is_center', 'is_airport']
            
            features = []
            for col in feature_columns:
                if col == 'amenities_count':
                    features.append(len(hotel_data.get('amenities', [])))
                elif col == 'has_pool':
                    features.append(1 if 'pool' in str(hotel_data.get('amenities', [])).lower() else 0)
                elif col == 'has_spa':
                    features.append(1 if 'spa' in str(hotel_data.get('amenities', [])).lower() else 0)
                elif col == 'has_gym':
                    features.append(1 if 'gym' in str(hotel_data.get('amenities', [])).lower() else 0)
                elif col == 'has_restaurant':
                    features.append(1 if 'restaurant' in str(hotel_data.get('amenities', [])).lower() else 0)
                elif col == 'has_wifi':
                    features.append(1 if 'wifi' in str(hotel_data.get('amenities', [])).lower() else 0)
                elif col == 'is_center':
                    features.append(1 if 'center' in str(hotel_data.get('address', '')).lower() else 0)
                elif col == 'is_airport':
                    features.append(1 if 'airport' in str(hotel_data.get('address', '')).lower() else 0)
                else:
                    features.append(hotel_data.get(col, 0))
            
            # Make prediction
            X = np.array(features).reshape(1, -1)
            predicted_price = self.hotel_model.predict(X)[0]
            
            # Add confidence interval (simplified)
            confidence = 0.8  # Placeholder
            
            return {
                'predicted_price': round(predicted_price, 2),
                'confidence': confidence,
                'currency': 'USD',
                'model_type': 'hotel_price_prediction'
            }
        except Exception as e:
            print(f"[ERROR] Error predicting hotel price: {e}")
            return {
                'predicted_price': 0,
                'confidence': 0,
                'currency': 'USD',
                'error': str(e)
            }
    
    def predict_restaurant_price(self, restaurant_data: Dict[str, Any]) -> Dict[str, Any]:
        """Dự đoán giá nhà hàng"""
        try:
            # Prepare features
            feature_columns = ['rating', 'menu_items_count', 'has_menu', 'is_vietnamese', 
                              'is_international', 'price_range', 'popularity_score']
            
            features = []
            for col in feature_columns:
                if col == 'menu_items_count':
                    features.append(len(restaurant_data.get('menu', [])))
                elif col == 'has_menu':
                    features.append(1 if restaurant_data.get('menu') else 0)
                elif col == 'is_vietnamese':
                    features.append(1 if 'vietnamese' in str(restaurant_data.get('cuisine', '')).lower() else 0)
                elif col == 'is_international':
                    features.append(1 if any(cuisine in str(restaurant_data.get('cuisine', '')).lower() 
                                           for cuisine in ['japanese', 'korean', 'chinese', 'italian']) else 0)
                elif col == 'price_range':
                    features.append(len(restaurant_data.get('price_range', '$')))
                else:
                    features.append(restaurant_data.get(col, 0))
            
            # Make prediction
            X = np.array(features).reshape(1, -1)
            predicted_price_range = self.restaurant_model.predict(X)[0]
            
            # Convert to price range string
            price_range = '$' * max(1, min(4, int(predicted_price_range)))
            
            return {
                'predicted_price_range': price_range,
                'confidence': 0.75,
                'model_type': 'restaurant_price_prediction'
            }
        except Exception as e:
            print(f"[ERROR] Error predicting restaurant price: {e}")
            return {
                'predicted_price_range': '$',
                'confidence': 0,
                'error': str(e)
            }
    
    def predict_activity_price(self, activity_data: Dict[str, Any]) -> Dict[str, Any]:
        """Dự đoán giá hoạt động"""
        try:
            # Prepare features
            feature_columns = ['rating', 'is_historical', 'is_museum', 'is_park', 
                              'is_temple', 'is_market', 'popularity_score']
            
            features = []
            for col in feature_columns:
                if col == 'is_historical':
                    features.append(1 if 'historical' in str(activity_data.get('category', '')).lower() else 0)
                elif col == 'is_museum':
                    features.append(1 if 'museum' in str(activity_data.get('category', '')).lower() else 0)
                elif col == 'is_park':
                    features.append(1 if 'park' in str(activity_data.get('category', '')).lower() else 0)
                elif col == 'is_temple':
                    features.append(1 if 'temple' in str(activity_data.get('category', '')).lower() else 0)
                elif col == 'is_market':
                    features.append(1 if 'market' in str(activity_data.get('category', '')).lower() else 0)
                else:
                    features.append(activity_data.get(col, 0))
            
            # Make prediction
            X = np.array(features).reshape(1, -1)
            predicted_price_level = self.activity_model.predict(X)[0]
            
            return {
                'predicted_price_level': max(0, min(4, int(predicted_price_level))),
                'confidence': 0.7,
                'model_type': 'activity_price_prediction'
            }
        except Exception as e:
            print(f"[ERROR] Error predicting activity price: {e}")
            return {
                'predicted_price_level': 0,
                'confidence': 0,
                'error': str(e)
            }
    
    def get_price_forecast(self, city: str, date_range: Tuple[datetime, datetime]) -> Dict[str, Any]:
        """Dự đoán giá theo thời gian"""
        try:
            start_date, end_date = date_range
            days = (end_date - start_date).days
            
            # Simple seasonal pricing model
            base_price = 100  # Base price in USD
            
            # Seasonal adjustments
            month = start_date.month
            if month in [12, 1, 2]:  # Winter (high season)
                seasonal_multiplier = 1.3
            elif month in [6, 7, 8]:  # Summer (high season)
                seasonal_multiplier = 1.2
            else:  # Low season
                seasonal_multiplier = 0.9
            
            # Weekend premium
            weekend_days = 0
            current_date = start_date
            while current_date <= end_date:
                if current_date.weekday() >= 5:  # Saturday or Sunday
                    weekend_days += 1
                current_date += timedelta(days=1)
            
            weekend_premium = weekend_days * 0.1
            
            # Calculate total price
            total_price = base_price * days * seasonal_multiplier * (1 + weekend_premium)
            
            return {
                'total_price': round(total_price, 2),
                'daily_average': round(total_price / days, 2),
                'seasonal_multiplier': seasonal_multiplier,
                'weekend_premium': weekend_premium,
                'currency': 'USD',
                'forecast_period': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
            }
        except Exception as e:
            print(f"[ERROR] Error generating price forecast: {e}")
            return {
                'total_price': 0,
                'daily_average': 0,
                'error': str(e)
            }
    
    def get_feature_importance(self) -> Dict[str, Any]:
        """Lấy feature importance của các models"""
        return self.feature_importance
    
    def get_model_performance(self) -> Dict[str, Any]:
        """Lấy performance metrics của các models"""
        # This would typically be calculated during training
        return {
            'hotel_model': {
                'model_type': 'RandomForestRegressor',
                'status': 'trained' if hasattr(self.hotel_model, 'feature_importances_') else 'not_trained'
            },
            'restaurant_model': {
                'model_type': 'GradientBoostingRegressor',
                'status': 'trained' if hasattr(self.restaurant_model, 'feature_importances_') else 'not_trained'
            },
            'activity_model': {
                'model_type': 'LinearRegression',
                'status': 'trained' if hasattr(self.activity_model, 'coef_') else 'not_trained'
            }
        }

