import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
import logging
from datetime import datetime

class AnalyticsEngine:
    """Analytics Engine for comprehensive data analysis and insights generation"""
    
    def __init__(self):
        """Initialize Analytics Engine"""
        self.logger = self._setup_logger()
        self.analysis_cache = {}
        
    def _setup_logger(self) -> logging.Logger:
        """Setup logger"""
        logger = logging.getLogger('AnalyticsEngine')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def get_comprehensive_analysis(self, places_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Perform comprehensive analysis on places data"""
        try:
            if not places_data:
                return {"error": "No data provided for analysis"}
            
            # Convert to DataFrame for analysis
            df = pd.DataFrame(places_data)
            
            analysis = {
                "summary": self._get_summary_statistics(df),
                "price_analysis": self._analyze_prices(df),
                "rating_analysis": self._analyze_ratings(df),
                "category_distribution": self._analyze_categories(df),
                "location_insights": self._analyze_locations(df),
                "trends": self._identify_trends(df),
                "recommendations": self._generate_recommendations(df),
                "generated_at": datetime.now().isoformat()
            }
            
            self.logger.info(f"Comprehensive analysis completed for {len(places_data)} places")
            return analysis
            
        except Exception as e:
            self.logger.error(f"Error in comprehensive analysis: {e}")
            return {"error": str(e)}
    
    def _get_summary_statistics(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Get basic summary statistics"""
        summary = {
            "total_places": len(df),
            "unique_categories": df['category'].nunique() if 'category' in df.columns else 0,
            "unique_cities": df['city'].nunique() if 'city' in df.columns else 0,
            "average_rating": df['rating'].mean() if 'rating' in df.columns else 0,
            "price_range": {
                "min": df['price_level'].min() if 'price_level' in df.columns else 0,
                "max": df['price_level'].max() if 'price_level' in df.columns else 0,
                "mean": df['price_level'].mean() if 'price_level' in df.columns else 0
            }
        }
        return summary
    
    def _analyze_prices(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze price patterns"""
        if 'price_level' not in df.columns:
            return {"error": "Price data not available"}
        
        price_analysis = {
            "distribution": df['price_level'].value_counts().to_dict(),
            "percentiles": {
                "25th": df['price_level'].quantile(0.25),
                "50th": df['price_level'].quantile(0.50),
                "75th": df['price_level'].quantile(0.75),
                "90th": df['price_level'].quantile(0.90)
            },
            "price_by_category": df.groupby('category')['price_level'].mean().to_dict() if 'category' in df.columns else {},
            "price_by_city": df.groupby('city')['price_level'].mean().to_dict() if 'city' in df.columns else {}
        }
        return price_analysis
    
    def _analyze_ratings(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze rating patterns"""
        if 'rating' not in df.columns:
            return {"error": "Rating data not available"}
        
        rating_analysis = {
            "distribution": df['rating'].value_counts().to_dict(),
            "average_by_category": df.groupby('category')['rating'].mean().to_dict() if 'category' in df.columns else {},
            "average_by_city": df.groupby('city')['rating'].mean().to_dict() if 'city' in df.columns else {},
            "high_rated_places": df[df['rating'] >= 4.5]['name'].tolist() if 'name' in df.columns else [],
            "rating_trends": self._calculate_rating_trends(df)
        }
        return rating_analysis
    
    def _analyze_categories(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze category distribution"""
        if 'category' not in df.columns:
            return {"error": "Category data not available"}
        
        category_analysis = {
            "distribution": df['category'].value_counts().to_dict(),
            "top_categories": df['category'].value_counts().head(10).to_dict(),
            "category_diversity": df['category'].nunique(),
            "category_by_city": df.groupby('city')['category'].nunique().to_dict() if 'city' in df.columns else {}
        }
        return category_analysis
    
    def _analyze_locations(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze location patterns"""
        if 'city' not in df.columns:
            return {"error": "Location data not available"}
        
        location_analysis = {
            "city_distribution": df['city'].value_counts().to_dict(),
            "top_cities": df['city'].value_counts().head(10).to_dict(),
            "places_per_city": df.groupby('city').size().to_dict(),
            "city_diversity": df['city'].nunique()
        }
        return location_analysis
    
    def _identify_trends(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Identify trends in the data"""
        trends = {
            "popular_categories": df['category'].value_counts().head(5).to_dict() if 'category' in df.columns else {},
            "high_rated_categories": df.groupby('category')['rating'].mean().sort_values(ascending=False).head(5).to_dict() if 'category' in df.columns and 'rating' in df.columns else {},
            "expensive_categories": df.groupby('category')['price_level'].mean().sort_values(ascending=False).head(5).to_dict() if 'category' in df.columns and 'price_level' in df.columns else {},
            "budget_friendly_categories": df.groupby('category')['price_level'].mean().sort_values(ascending=True).head(5).to_dict() if 'category' in df.columns and 'price_level' in df.columns else {}
        }
        return trends
    
    def _generate_recommendations(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Generate actionable recommendations"""
        recommendations = {
            "best_value_places": self._find_best_value_places(df),
            "hidden_gems": self._find_hidden_gems(df),
            "must_visit": self._find_must_visit_places(df),
            "budget_options": self._find_budget_options(df),
            "premium_options": self._find_premium_options(df)
        }
        return recommendations
    
    def _find_best_value_places(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Find places with best value (high rating, low price)"""
        if 'rating' not in df.columns or 'price_level' not in df.columns:
            return []
        
        # Calculate value score (rating / price_level)
        df['value_score'] = df['rating'] / (df['price_level'] + 1)  # +1 to avoid division by zero
        
        best_value = df.nlargest(10, 'value_score')
        return best_value[['name', 'rating', 'price_level', 'value_score']].to_dict('records') if 'name' in df.columns else []
    
    def _find_hidden_gems(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Find hidden gems (high rating but not very popular)"""
        if 'rating' not in df.columns:
            return []
        
        # Places with high rating but not in top categories
        top_categories = df['category'].value_counts().head(3).index if 'category' in df.columns else []
        hidden_gems = df[(df['rating'] >= 4.0) & (~df['category'].isin(top_categories))]
        
        return hidden_gems[['name', 'rating', 'category']].to_dict('records') if 'name' in df.columns else []
    
    def _find_must_visit_places(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Find must-visit places (highest rated)"""
        if 'rating' not in df.columns:
            return []
        
        must_visit = df.nlargest(10, 'rating')
        return must_visit[['name', 'rating', 'category']].to_dict('records') if 'name' in df.columns else []
    
    def _find_budget_options(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Find budget-friendly options"""
        if 'price_level' not in df.columns:
            return []
        
        budget_options = df[df['price_level'] <= 2].nlargest(10, 'rating') if 'rating' in df.columns else df[df['price_level'] <= 2]
        return budget_options[['name', 'price_level', 'rating']].to_dict('records') if 'name' in df.columns else []
    
    def _find_premium_options(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Find premium options"""
        if 'price_level' not in df.columns:
            return []
        
        premium_options = df[df['price_level'] >= 4].nlargest(10, 'rating') if 'rating' in df.columns else df[df['price_level'] >= 4]
        return premium_options[['name', 'price_level', 'rating']].to_dict('records') if 'name' in df.columns else []
    
    def _calculate_rating_trends(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Calculate rating trends"""
        if 'rating' not in df.columns:
            return {}
        
        rating_trends = {
            "excellent_places": len(df[df['rating'] >= 4.5]),
            "good_places": len(df[(df['rating'] >= 4.0) & (df['rating'] < 4.5)]),
            "average_places": len(df[(df['rating'] >= 3.0) & (df['rating'] < 4.0)]),
            "poor_places": len(df[df['rating'] < 3.0]),
            "average_rating": df['rating'].mean()
        }
        return rating_trends
    
    def generate_insights(self, analysis_result: Dict[str, Any]) -> List[str]:
        """Generate human-readable insights from analysis"""
        insights = []
        
        if "summary" in analysis_result:
            summary = analysis_result["summary"]
            insights.append(f"Analyzed {summary['total_places']} places across {summary['unique_cities']} cities")
            insights.append(f"Average rating: {summary['average_rating']:.2f}")
        
        if "trends" in analysis_result:
            trends = analysis_result["trends"]
            if trends.get("popular_categories"):
                top_category = max(trends["popular_categories"], key=trends["popular_categories"].get)
                insights.append(f"Most popular category: {top_category}")
        
        if "recommendations" in analysis_result:
            recs = analysis_result["recommendations"]
            if recs.get("best_value_places"):
                insights.append(f"Found {len(recs['best_value_places'])} best value places")
            if recs.get("hidden_gems"):
                insights.append(f"Discovered {len(recs['hidden_gems'])} hidden gems")
        
        return insights
    
    def export_analysis(self, analysis_result: Dict[str, Any], format: str = "json") -> str:
        """Export analysis results in specified format"""
        if format == "json":
            import json
            return json.dumps(analysis_result, indent=2, default=str)
        elif format == "csv":
            # Export key metrics to CSV
            summary = analysis_result.get("summary", {})
            return f"total_places,unique_cities,average_rating\n{summary.get('total_places', 0)},{summary.get('unique_cities', 0)},{summary.get('average_rating', 0)}"
        else:
            return str(analysis_result)
