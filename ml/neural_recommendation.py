"""
Neural Collaborative Filtering (NCF) và DeepFM
==============================================
Hybrid Recommender System với deep learning models
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
import logging
from pathlib import Path
import pickle

logger = logging.getLogger(__name__)

# Optional imports
try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch not available, Neural CF will use TensorFlow")

try:
    import tensorflow as tf
    from tensorflow import keras
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    logger.warning("TensorFlow not available, Neural CF will be disabled")


class NeuralCollaborativeFiltering:
    """
    Neural Collaborative Filtering (NCF)
    Sử dụng deep learning để học user-item interactions
    """
    
    def __init__(self, n_factors: int = 50, n_layers: int = 3, use_pytorch: bool = True):
        """
        Args:
            n_factors: Số embedding dimensions
            n_layers: Số layers trong MLP
            use_pytorch: Sử dụng PyTorch nếu available
        """
        self.n_factors = n_factors
        self.n_layers = n_layers
        self.use_pytorch = use_pytorch and TORCH_AVAILABLE
        
        self.model = None
        self.user_encoder = None
        self.item_encoder = None
        self.n_users = 0
        self.n_items = 0
        
    def _build_pytorch_model(self):
        """Build PyTorch NCF model"""
        class NCF(nn.Module):
            def __init__(self, n_users, n_items, n_factors, n_layers):
                super(NCF, self).__init__()
                
                # Embedding layers
                self.user_embedding = nn.Embedding(n_users, n_factors)
                self.item_embedding = nn.Embedding(n_items, n_factors)
                
                # MLP layers
                layers = []
                input_dim = n_factors * 2
                for i in range(n_layers):
                    output_dim = n_factors * (2 ** (n_layers - i - 1))
                    layers.append(nn.Linear(input_dim, output_dim))
                    layers.append(nn.ReLU())
                    layers.append(nn.Dropout(0.2))
                    input_dim = output_dim
                
                layers.append(nn.Linear(input_dim, 1))
                layers.append(nn.Sigmoid())
                
                self.mlp = nn.Sequential(*layers)
            
            def forward(self, user_ids, item_ids):
                user_embed = self.user_embedding(user_ids)
                item_embed = self.item_embedding(item_ids)
                
                # Concatenate embeddings
                concat = torch.cat([user_embed, item_embed], dim=1)
                
                # MLP
                output = self.mlp(concat)
                return output.squeeze()
        
        return NCF(self.n_users, self.n_items, self.n_factors, self.n_layers)
    
    def _build_tensorflow_model(self):
        """Build TensorFlow/Keras NCF model"""
        if not TENSORFLOW_AVAILABLE:
            raise ImportError("TensorFlow not available")
        
        # Input layers
        user_input = keras.layers.Input(shape=(1,), name='user_input')
        item_input = keras.layers.Input(shape=(1,), name='item_input')
        
        # Embedding layers
        user_embedding = keras.layers.Embedding(
            self.n_users, self.n_factors, name='user_embedding'
        )(user_input)
        item_embedding = keras.layers.Embedding(
            self.n_items, self.n_factors, name='item_embedding'
        )(item_input)
        
        # Flatten
        user_vec = keras.layers.Flatten()(user_embedding)
        item_vec = keras.layers.Flatten()(item_embedding)
        
        # Concatenate
        concat = keras.layers.Concatenate()([user_vec, item_vec])
        
        # MLP
        x = concat
        for i in range(self.n_layers):
            dim = self.n_factors * (2 ** (self.n_layers - i - 1))
            x = keras.layers.Dense(dim, activation='relu')(x)
            x = keras.layers.Dropout(0.2)(x)
        
        # Output
        output = keras.layers.Dense(1, activation='sigmoid')(x)
        
        model = keras.Model(inputs=[user_input, item_input], outputs=output)
        model.compile(
            optimizer='adam',
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    def fit(self, ratings: List[Dict[str, Any]], epochs: int = 10, batch_size: int = 256):
        """
        Fit NCF model
        
        Args:
            ratings: List of dicts với keys: user_id, item_id, rating
            epochs: Số epochs
            batch_size: Batch size
        """
        if not ratings:
            logger.warning("No ratings provided")
            return
        
        df = pd.DataFrame(ratings)
        
        # Encode user và item IDs
        unique_users = df['user_id'].unique()
        unique_items = df['item_id'].unique()
        
        self.user_encoder = {uid: idx for idx, uid in enumerate(unique_users)}
        self.item_encoder = {iid: idx for idx, iid in enumerate(unique_items)}
        
        self.n_users = len(unique_users)
        self.n_items = len(unique_items)
        
        # Convert ratings
        df['user_idx'] = df['user_id'].map(self.user_encoder)
        df['item_idx'] = df['item_id'].map(self.item_encoder)
        
        # Normalize ratings to [0, 1]
        df['rating_norm'] = (df['rating'] - df['rating'].min()) / (df['rating'].max() - df['rating'].min())
        
        # Build model
        if self.use_pytorch:
            self.model = self._build_pytorch_model()
            optimizer = optim.Adam(self.model.parameters(), lr=0.001)
            criterion = nn.BCELoss()
            
            # Train
            for epoch in range(epochs):
                self.model.train()
                total_loss = 0
                
                # Mini-batch training
                for i in range(0, len(df), batch_size):
                    batch = df.iloc[i:i+batch_size]
                    
                    user_ids = torch.LongTensor(batch['user_idx'].values)
                    item_ids = torch.LongTensor(batch['item_idx'].values)
                    ratings_tensor = torch.FloatTensor(batch['rating_norm'].values)
                    
                    optimizer.zero_grad()
                    predictions = self.model(user_ids, item_ids)
                    loss = criterion(predictions, ratings_tensor)
                    loss.backward()
                    optimizer.step()
                    
                    total_loss += loss.item()
                
                if (epoch + 1) % 2 == 0:
                    logger.info(f"Epoch {epoch+1}/{epochs}, Loss: {total_loss/len(df)*batch_size:.4f}")
        else:
            if TENSORFLOW_AVAILABLE:
                self.model = self._build_tensorflow_model()
                
                # Prepare data
                X_user = df['user_idx'].values
                X_item = df['item_idx'].values
                y = df['rating_norm'].values
                
                # Train
                self.model.fit(
                    [X_user, X_item],
                    y,
                    epochs=epochs,
                    batch_size=batch_size,
                    verbose=1 if epochs <= 10 else 0
                )
            else:
                logger.error("Neither PyTorch nor TensorFlow available")
                return
        
        logger.info("NCF model fitted successfully")
    
    def predict(self, user_id: int, item_id: int) -> float:
        """Predict rating for user-item pair"""
        if self.model is None:
            logger.warning("Model not fitted yet")
            return 0.0
        
        user_idx = self.user_encoder.get(user_id)
        item_idx = self.item_encoder.get(item_id)
        
        if user_idx is None or item_idx is None:
            return 0.0
        
        if self.use_pytorch:
            self.model.eval()
            with torch.no_grad():
                user_tensor = torch.LongTensor([user_idx])
                item_tensor = torch.LongTensor([item_idx])
                prediction = self.model(user_tensor, item_tensor)
                return float(prediction.item())
        else:
            if TENSORFLOW_AVAILABLE:
                prediction = self.model.predict([[user_idx], [item_idx]], verbose=0)
                return float(prediction[0][0])
        
        return 0.0
    
    def recommend(self, user_id: int, n_results: int = 10, exclude_items: List[int] = None) -> List[Dict[str, Any]]:
        """Recommend items for user"""
        if self.model is None:
            return []
        
        user_idx = self.user_encoder.get(user_id)
        if user_idx is None:
            return []
        
        exclude_items = exclude_items or []
        
        # Predict for all items
        predictions = []
        for item_id, item_idx in self.item_encoder.items():
            if item_id in exclude_items:
                continue
            
            score = self.predict(user_id, item_id)
            predictions.append({
                'item_id': item_id,
                'predicted_rating': score
            })
        
        # Sort và lấy top-k
        predictions.sort(key=lambda x: x['predicted_rating'], reverse=True)
        return predictions[:n_results]


class DeepFM:
    """
    DeepFM: Factorization Machine + Deep Neural Network
    Kết hợp wide (FM) và deep components
    """
    
    def __init__(self, n_factors: int = 10, deep_layers: List[int] = [128, 64, 32]):
        """
        Args:
            n_factors: Số factors cho FM
            deep_layers: Số units trong mỗi deep layer
        """
        self.n_factors = n_factors
        self.deep_layers = deep_layers
        self.model = None
        self.n_fields = 0
        
    def _build_model(self, n_fields: int):
        """Build DeepFM model"""
        if not TENSORFLOW_AVAILABLE:
            raise ImportError("TensorFlow required for DeepFM")
        
        self.n_fields = n_fields
        
        # Input layer
        inputs = keras.layers.Input(shape=(n_fields,), name='input')
        
        # FM Component
        # Linear part
        linear_output = keras.layers.Dense(1, use_bias=True)(inputs)
        
        # Factorization Machine part
        embedding_layers = []
        for i in range(n_fields):
            embedding = keras.layers.Embedding(
                input_dim=1000,  # Assume max feature value
                output_dim=self.n_factors
            )(keras.layers.Lambda(lambda x: x[:, i:i+1])(inputs))
            embedding_layers.append(embedding)
        
        # Sum of embeddings
        fm_sum = keras.layers.Add()(embedding_layers)
        fm_sum_square = keras.layers.Lambda(lambda x: x ** 2)(fm_sum)
        
        # Sum of squares
        embedding_squares = [keras.layers.Lambda(lambda x: x ** 2)(emb) for emb in embedding_layers]
        fm_square_sum = keras.layers.Add()(embedding_squares)
        
        # FM output: (sum^2 - sum_square) / 2
        fm_output = keras.layers.Lambda(
            lambda x: (x[0] - x[1]) * 0.5
        )([fm_sum_square, fm_square_sum])
        fm_output = keras.layers.Flatten()(fm_output)
        fm_output = keras.layers.Dense(1)(fm_output)
        
        # Deep Component
        deep_input = keras.layers.Concatenate()(embedding_layers)
        deep_input = keras.layers.Flatten()(deep_input)
        
        x = deep_input
        for units in self.deep_layers:
            x = keras.layers.Dense(units, activation='relu')(x)
            x = keras.layers.Dropout(0.2)(x)
        
        deep_output = keras.layers.Dense(1)(x)
        
        # Combine FM and Deep
        combined = keras.layers.Add()([linear_output, fm_output, deep_output])
        output = keras.layers.Activation('sigmoid')(combined)
        
        model = keras.Model(inputs=inputs, outputs=output)
        model.compile(
            optimizer='adam',
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
        
        return model
    
    def fit(self, features: np.ndarray, ratings: np.ndarray, epochs: int = 10, batch_size: int = 256):
        """
        Fit DeepFM model
        
        Args:
            features: Feature matrix (n_samples, n_features)
            ratings: Target ratings (n_samples,)
            epochs: Số epochs
            batch_size: Batch size
        """
        if not TENSORFLOW_AVAILABLE:
            logger.error("TensorFlow required for DeepFM")
            return
        
        n_fields = features.shape[1]
        
        # Normalize ratings
        ratings_norm = (ratings - ratings.min()) / (ratings.max() - ratings.min())
        
        # Build và train model
        self.model = self._build_model(n_fields)
        
        self.model.fit(
            features,
            ratings_norm,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=0.2,
            verbose=1
        )
        
        logger.info("DeepFM model fitted successfully")
    
    def predict(self, features: np.ndarray) -> np.ndarray:
        """Predict ratings"""
        if self.model is None:
            return np.zeros(len(features))
        
        predictions = self.model.predict(features, verbose=0)
        return predictions.flatten()


class HybridNeuralRecommender:
    """
    Hybrid Recommender kết hợp NCF + Content-based + DeepFM
    """
    
    def __init__(self):
        self.ncf = NeuralCollaborativeFiltering()
        self.deepfm = DeepFM()
        self.content_based = None  # Will be set from external
        self.weights = {
            'ncf': 0.4,
            'deepfm': 0.3,
            'content': 0.3
        }
    
    def fit(
        self,
        ratings: List[Dict[str, Any]],
        content_features: Optional[np.ndarray] = None,
        epochs: int = 10
    ):
        """Fit all models"""
        # Fit NCF
        logger.info("Fitting NCF...")
        self.ncf.fit(ratings, epochs=epochs)
        
        # Fit DeepFM nếu có features
        if content_features is not None and len(content_features) > 0:
            logger.info("Fitting DeepFM...")
            ratings_array = np.array([r['rating'] for r in ratings])
            self.deepfm.fit(content_features, ratings_array, epochs=epochs)
    
    def hybrid_predict(
        self,
        user_id: int,
        item_id: int,
        content_features: Optional[np.ndarray] = None
    ) -> float:
        """Hybrid prediction combining all models"""
        predictions = []
        weights = []
        
        # NCF prediction
        if self.ncf.model is not None:
            ncf_pred = self.ncf.predict(user_id, item_id)
            predictions.append(ncf_pred)
            weights.append(self.weights['ncf'])
        
        # DeepFM prediction
        if self.deepfm.model is not None and content_features is not None:
            deepfm_pred = self.deepfm.predict(content_features.reshape(1, -1))[0]
            predictions.append(deepfm_pred)
            weights.append(self.weights['deepfm'])
        
        # Content-based (nếu có)
        if self.content_based is not None:
            # Content-based score sẽ được tính riêng
            content_score = 0.5  # Placeholder
            predictions.append(content_score)
            weights.append(self.weights['content'])
        
        # Weighted average
        if predictions:
            weights = np.array(weights)
            weights = weights / weights.sum()  # Normalize
            final_pred = np.dot(predictions, weights)
            return float(final_pred)
        
        return 0.0
    
    def hybrid_recommend(
        self,
        user_id: int,
        n_results: int = 10,
        content_features_dict: Optional[Dict[int, np.ndarray]] = None
    ) -> List[Dict[str, Any]]:
        """Hybrid recommendations"""
        # Get recommendations from each model
        all_recommendations = {}
        
        # NCF recommendations
        if self.ncf.model is not None:
            ncf_recs = self.ncf.recommend(user_id, n_results * 2)
            for rec in ncf_recs:
                item_id = rec['item_id']
                if item_id not in all_recommendations:
                    all_recommendations[item_id] = {
                        'item_id': item_id,
                        'scores': {}
                    }
                all_recommendations[item_id]['scores']['ncf'] = rec['predicted_rating']
        
        # DeepFM recommendations (nếu có features)
        if self.deepfm.model is not None and content_features_dict:
            for item_id, features in content_features_dict.items():
                deepfm_pred = self.deepfm.predict(features.reshape(1, -1))[0]
                if item_id not in all_recommendations:
                    all_recommendations[item_id] = {
                        'item_id': item_id,
                        'scores': {}
                    }
                all_recommendations[item_id]['scores']['deepfm'] = deepfm_pred
        
        # Combine scores
        final_recommendations = []
        for item_id, rec in all_recommendations.items():
            scores = rec['scores']
            weighted_score = 0.0
            total_weight = 0.0
            
            for model_name, score in scores.items():
                weight = self.weights.get(model_name, 0.0)
                weighted_score += score * weight
                total_weight += weight
            
            if total_weight > 0:
                final_score = weighted_score / total_weight
                final_recommendations.append({
                    'item_id': item_id,
                    'hybrid_score': final_score,
                    'scores': scores
                })
        
        # Sort và lấy top-k
        final_recommendations.sort(key=lambda x: x['hybrid_score'], reverse=True)
        return final_recommendations[:n_results]

