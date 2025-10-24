import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import re
import json
from collections import Counter
import pickle
import os

class SentimentAnalyzer:
    def __init__(self, model_dir: str = 'ml_models/saved_models'):
        """Initialize Sentiment Analyzer"""
        self.model_dir = model_dir
        self.ensure_model_dir()
        
        # Vietnamese sentiment dictionaries
        self.positive_words = {
            'tuyệt vời', 'xuất sắc', 'tốt', 'hay', 'đẹp', 'ngon', 'thích', 'hài lòng',
            'ấn tượng', 'thú vị', 'thoải mái', 'sạch sẽ', 'thân thiện', 'chuyên nghiệp',
            'nhanh chóng', 'tiện lợi', 'giá trị', 'đáng giá', 'khuyến khích', 'giới thiệu',
            'hoàn hảo', 'tuyệt hảo', 'tuyệt đối', 'tuyệt vời', 'xuất sắc', 'tốt nhất',
            'hài lòng', 'thích thú', 'thú vị', 'ấn tượng', 'tuyệt vời', 'tốt đẹp'
        }
        
        self.negative_words = {
            'tệ', 'xấu', 'không tốt', 'thất vọng', 'không hài lòng', 'chán', 'nhàm chán',
            'đắt', 'mắc', 'không đáng', 'không xứng', 'tồi tệ', 'kinh khủng', 'khủng khiếp',
            'bẩn', 'bẩn thỉu', 'không sạch', 'không an toàn', 'nguy hiểm', 'khó chịu',
            'không thân thiện', 'thô lỗ', 'không chuyên nghiệp', 'chậm', 'không tiện',
            'không đáng giá', 'lãng phí', 'không khuyến khích', 'không nên', 'tránh'
        }
        
        # English sentiment dictionaries
        self.positive_words_en = {
            'excellent', 'amazing', 'wonderful', 'fantastic', 'great', 'good', 'awesome',
            'beautiful', 'delicious', 'perfect', 'outstanding', 'brilliant', 'superb',
            'magnificent', 'stunning', 'breathtaking', 'incredible', 'fabulous', 'marvelous',
            'satisfied', 'happy', 'pleased', 'impressed', 'recommend', 'love', 'enjoy'
        }
        
        self.negative_words_en = {
            'terrible', 'awful', 'horrible', 'bad', 'disappointed', 'disgusting', 'nasty',
            'dirty', 'unclean', 'unsafe', 'dangerous', 'rude', 'unfriendly', 'slow',
            'expensive', 'overpriced', 'waste', 'avoid', 'hate', 'dislike', 'boring',
            'dull', 'uncomfortable', 'unprofessional', 'inconvenient', 'poor', 'worst'
        }
        
        # Sentiment weights
        self.sentiment_weights = {
            'very_positive': 1.0,
            'positive': 0.7,
            'neutral': 0.0,
            'negative': -0.7,
            'very_negative': -1.0
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
            # Load sentiment model if exists
            sentiment_path = os.path.join(self.model_dir, 'sentiment_model.pkl')
            if os.path.exists(sentiment_path):
                with open(sentiment_path, 'rb') as f:
                    self.sentiment_model = pickle.load(f)
            else:
                self.sentiment_model = None
            
            print("[SUCCESS] Sentiment analyzer loaded successfully")
        except Exception as e:
            print(f"[WARNING] Could not load sentiment model: {e}")
            self.sentiment_model = None
    
    def save_models(self):
        """Save models đã train"""
        try:
            if self.sentiment_model:
                with open(os.path.join(self.model_dir, 'sentiment_model.pkl'), 'wb') as f:
                    pickle.dump(self.sentiment_model, f)
            
            print("[SUCCESS] Sentiment model saved successfully")
        except Exception as e:
            print(f"[ERROR] Could not save sentiment model: {e}")
    
    def clean_text(self, text: str) -> str:
        """Làm sạch text"""
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove special characters but keep Vietnamese characters
        text = re.sub(r'[^\w\sàáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđĐ]', ' ', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        return text
    
    def analyze_sentiment(self, text: str) -> Dict[str, Any]:
        """Phân tích sentiment của text"""
        if not text:
            return {
                'sentiment': 'neutral',
                'score': 0.0,
                'confidence': 0.0,
                'positive_words': [],
                'negative_words': []
            }
        
        # Clean text
        cleaned_text = self.clean_text(text)
        words = cleaned_text.split()
        
        # Count positive and negative words
        positive_count = 0
        negative_count = 0
        positive_words_found = []
        negative_words_found = []
        
        for word in words:
            if word in self.positive_words or word in self.positive_words_en:
                positive_count += 1
                positive_words_found.append(word)
            elif word in self.negative_words or word in self.negative_words_en:
                negative_count += 1
                negative_words_found.append(word)
        
        # Calculate sentiment score
        total_words = len(words)
        if total_words == 0:
            sentiment_score = 0.0
        else:
            sentiment_score = (positive_count - negative_count) / total_words
        
        # Determine sentiment category
        if sentiment_score >= 0.1:
            sentiment = 'positive'
        elif sentiment_score <= -0.1:
            sentiment = 'negative'
        else:
            sentiment = 'neutral'
        
        # Calculate confidence
        confidence = min(abs(sentiment_score) * 2, 1.0)
        
        return {
            'sentiment': sentiment,
            'score': round(sentiment_score, 3),
            'confidence': round(confidence, 3),
            'positive_words': positive_words_found,
            'negative_words': negative_words_found,
            'total_words': total_words,
            'positive_count': positive_count,
            'negative_count': negative_count
        }
    
    def analyze_reviews(self, reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Phân tích sentiment của nhiều reviews"""
        if not reviews:
            return {
                'overall_sentiment': 'neutral',
                'overall_score': 0.0,
                'confidence': 0.0,
                'sentiment_distribution': {},
                'total_reviews': 0,
                'detailed_analysis': []
            }
        
        sentiment_scores = []
        sentiment_counts = Counter()
        detailed_analysis = []
        
        for review in reviews:
            text = review.get('comment', '') or review.get('review_text', '') or review.get('content', '')
            if text:
                analysis = self.analyze_sentiment(text)
                sentiment_scores.append(analysis['score'])
                sentiment_counts[analysis['sentiment']] += 1
                
                detailed_analysis.append({
                    'review_id': review.get('id', ''),
                    'author': review.get('author', ''),
                    'rating': review.get('rating', 0),
                    'sentiment': analysis['sentiment'],
                    'score': analysis['score'],
                    'confidence': analysis['confidence'],
                    'text_preview': text[:100] + '...' if len(text) > 100 else text
                })
        
        # Calculate overall sentiment
        if sentiment_scores:
            overall_score = np.mean(sentiment_scores)
            if overall_score >= 0.1:
                overall_sentiment = 'positive'
            elif overall_score <= -0.1:
                overall_sentiment = 'negative'
            else:
                overall_sentiment = 'neutral'
            
            overall_confidence = min(abs(overall_score) * 2, 1.0)
        else:
            overall_score = 0.0
            overall_sentiment = 'neutral'
            overall_confidence = 0.0
        
        # Calculate sentiment distribution
        total_reviews = len(reviews)
        sentiment_distribution = {
            'positive': sentiment_counts['positive'] / total_reviews if total_reviews > 0 else 0,
            'neutral': sentiment_counts['neutral'] / total_reviews if total_reviews > 0 else 0,
            'negative': sentiment_counts['negative'] / total_reviews if total_reviews > 0 else 0
        }
        
        return {
            'overall_sentiment': overall_sentiment,
            'overall_score': round(overall_score, 3),
            'confidence': round(overall_confidence, 3),
            'sentiment_distribution': sentiment_distribution,
            'total_reviews': total_reviews,
            'detailed_analysis': detailed_analysis
        }
    
    def analyze_place_sentiment(self, place_data: Dict[str, Any], reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Phân tích sentiment cho một địa điểm"""
        # Analyze reviews
        review_analysis = self.analyze_reviews(reviews)
        
        # Get place information
        place_name = place_data.get('name', '')
        place_rating = place_data.get('rating', 0)
        place_category = place_data.get('category', '')
        
        # Calculate sentiment score based on rating and reviews
        rating_sentiment_score = (place_rating - 2.5) / 2.5  # Normalize to -1 to 1
        review_sentiment_score = review_analysis['overall_score']
        
        # Combine scores
        combined_score = (rating_sentiment_score * 0.4 + review_sentiment_score * 0.6)
        
        # Determine final sentiment
        if combined_score >= 0.1:
            final_sentiment = 'positive'
        elif combined_score <= -0.1:
            final_sentiment = 'negative'
        else:
            final_sentiment = 'neutral'
        
        return {
            'place_name': place_name,
            'place_category': place_category,
            'final_sentiment': final_sentiment,
            'combined_score': round(combined_score, 3),
            'rating_sentiment_score': round(rating_sentiment_score, 3),
            'review_sentiment_score': round(review_sentiment_score, 3),
            'review_analysis': review_analysis,
            'recommendation': self._generate_recommendation(final_sentiment, combined_score)
        }
    
    def _generate_recommendation(self, sentiment: str, score: float) -> str:
        """Tạo recommendation dựa trên sentiment"""
        if sentiment == 'positive' and score >= 0.5:
            return "Highly recommended - Excellent reviews and ratings"
        elif sentiment == 'positive':
            return "Recommended - Good reviews and ratings"
        elif sentiment == 'neutral':
            return "Consider visiting - Mixed reviews"
        elif sentiment == 'negative' and score <= -0.5:
            return "Not recommended - Poor reviews and ratings"
        else:
            return "Proceed with caution - Some negative feedback"
    
    def get_sentiment_trends(self, reviews: List[Dict[str, Any]], time_period: str = 'month') -> Dict[str, Any]:
        """Phân tích xu hướng sentiment theo thời gian"""
        if not reviews:
            return {'trends': [], 'overall_trend': 'stable'}
        
        # Group reviews by time period
        time_groups = {}
        for review in reviews:
            created_at = review.get('created_at', '')
            if created_at:
                try:
                    if time_period == 'month':
                        time_key = created_at[:7]  # YYYY-MM
                    elif time_period == 'week':
                        # Simplified week grouping
                        date = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        week_key = f"{date.year}-W{date.isocalendar()[1]}"
                    else:  # day
                        time_key = created_at[:10]  # YYYY-MM-DD
                    
                    if time_key not in time_groups:
                        time_groups[time_key] = []
                    time_groups[time_key].append(review)
                except:
                    continue
        
        # Analyze sentiment for each time period
        trends = []
        for time_key, period_reviews in sorted(time_groups.items()):
            analysis = self.analyze_reviews(period_reviews)
            trends.append({
                'time_period': time_key,
                'sentiment': analysis['overall_sentiment'],
                'score': analysis['overall_score'],
                'review_count': len(period_reviews)
            })
        
        # Calculate overall trend
        if len(trends) >= 2:
            first_score = trends[0]['score']
            last_score = trends[-1]['score']
            score_diff = last_score - first_score
            
            if score_diff > 0.1:
                overall_trend = 'improving'
            elif score_diff < -0.1:
                overall_trend = 'declining'
            else:
                overall_trend = 'stable'
        else:
            overall_trend = 'stable'
        
        return {
            'trends': trends,
            'overall_trend': overall_trend,
            'time_period': time_period
        }
    
    def get_sentiment_insights(self, reviews: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Tạo insights từ sentiment analysis"""
        if not reviews:
            return {'insights': [], 'summary': 'No reviews available'}
        
        # Analyze all reviews
        analysis = self.analyze_reviews(reviews)
        
        insights = []
        
        # Insight 1: Overall sentiment
        if analysis['overall_sentiment'] == 'positive':
            insights.append("[RECOMMEND] Overall sentiment is positive - customers are generally satisfied")
        elif analysis['overall_sentiment'] == 'negative':
            insights.append("[WARNING] Overall sentiment is negative - there are areas for improvement")
        else:
            insights.append("[SCALER] Overall sentiment is neutral - mixed customer feedback")
        
        # Insight 2: Sentiment distribution
        dist = analysis['sentiment_distribution']
        if dist['positive'] > 0.7:
            insights.append("👍 High positive sentiment ratio - excellent customer satisfaction")
        elif dist['negative'] > 0.3:
            insights.append("👎 High negative sentiment ratio - needs attention")
        
        # Insight 3: Review volume
        total_reviews = analysis['total_reviews']
        if total_reviews > 100:
            insights.append("📈 High review volume - strong customer engagement")
        elif total_reviews < 10:
            insights.append("📉 Low review volume - limited feedback available")
        
        # Insight 4: Confidence level
        confidence = analysis['confidence']
        if confidence > 0.8:
            insights.append("[MATCH] High confidence in sentiment analysis - clear customer opinions")
        elif confidence < 0.3:
            insights.append("❓ Low confidence in sentiment analysis - mixed signals")
        
        return {
            'insights': insights,
            'summary': f"Analyzed {total_reviews} reviews with {analysis['overall_sentiment']} sentiment",
            'analysis': analysis
        }
    
    def train_sentiment_model(self, training_data: List[Dict[str, Any]]):
        """Train sentiment model từ training data"""
        print("🧠 Training sentiment model...")
        
        if not training_data:
            print("[WARNING] No training data provided")
            return
        
        # Prepare training data
        texts = []
        labels = []
        
        for item in training_data:
            text = item.get('text', '')
            label = item.get('sentiment', '')
            
            if text and label:
                texts.append(self.clean_text(text))
                labels.append(label)
        
        if len(texts) < 10:
            print("[WARNING] Not enough training data")
            return
        
        # Simple model training (could be enhanced with more sophisticated models)
        self.sentiment_model = {
            'positive_words': self.positive_words,
            'negative_words': self.negative_words,
            'positive_words_en': self.positive_words_en,
            'negative_words_en': self.negative_words_en,
            'trained_at': datetime.now().isoformat(),
            'training_samples': len(texts)
        }
        
        # Save model
        self.save_models()
        
        print(f"[SUCCESS] Sentiment model trained with {len(texts)} samples")
    
    def get_model_info(self) -> Dict[str, Any]:
        """Lấy thông tin về model"""
        return {
            'model_type': 'rule_based_sentiment_analyzer',
            'languages_supported': ['vietnamese', 'english'],
            'positive_words_count': len(self.positive_words) + len(self.positive_words_en),
            'negative_words_count': len(self.negative_words) + len(self.negative_words_en),
            'model_loaded': self.sentiment_model is not None,
            'trained_at': self.sentiment_model.get('trained_at') if self.sentiment_model else None
        }

