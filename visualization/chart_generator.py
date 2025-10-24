"""
Chart Generator for Travel Planner Analytics
Provides visualization capabilities for travel data
"""

import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Any, Optional
import pandas as pd

class ChartGenerator:
    """Generate various charts for travel analytics"""
    
    def __init__(self):
        self.style = "seaborn-v0_8"
        plt.style.use(self.style)
    
    def create_rating_distribution_chart(self, data: Dict[str, Any]) -> str:
        """Create rating distribution chart"""
        try:
            ratings = data.get('ratings', [4.0, 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7, 4.8, 4.9])
            
            plt.figure(figsize=(10, 6))
            plt.hist(ratings, bins=10, alpha=0.7, color='skyblue', edgecolor='black')
            plt.title('Rating Distribution')
            plt.xlabel('Rating')
            plt.ylabel('Frequency')
            plt.grid(True, alpha=0.3)
            
            return "Rating distribution chart created successfully"
        except Exception as e:
            return f"Error creating rating chart: {str(e)}"
    
    def create_price_vs_rating_chart(self, data: Dict[str, Any]) -> str:
        """Create price vs rating scatter plot"""
        try:
            prices = data.get('prices', [100, 150, 200, 250, 300])
            ratings = data.get('ratings', [4.0, 4.2, 4.4, 4.6, 4.8])
            
            plt.figure(figsize=(10, 6))
            plt.scatter(prices, ratings, alpha=0.7, s=100, color='green')
            plt.title('Price vs Rating')
            plt.xlabel('Price ($)')
            plt.ylabel('Rating')
            plt.grid(True, alpha=0.3)
            
            return "Price vs rating chart created successfully"
        except Exception as e:
            return f"Error creating price chart: {str(e)}"
    
    def create_category_distribution_chart(self, data: Dict[str, Any]) -> str:
        """Create category distribution pie chart"""
        try:
            categories = data.get('categories', ['Hotels', 'Restaurants', 'Attractions', 'Entertainment'])
            counts = data.get('counts', [25, 30, 20, 15])
            
            plt.figure(figsize=(8, 8))
            plt.pie(counts, labels=categories, autopct='%1.1f%%', startangle=90)
            plt.title('Category Distribution')
            
            return "Category distribution chart created successfully"
        except Exception as e:
            return f"Error creating category chart: {str(e)}"
    
    def create_trend_analysis_chart(self, data: Dict[str, Any]) -> str:
        """Create trend analysis line chart"""
        try:
            months = data.get('months', ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'])
            values = data.get('values', [100, 120, 110, 140, 130, 150])
            
            plt.figure(figsize=(12, 6))
            plt.plot(months, values, marker='o', linewidth=2, markersize=8)
            plt.title('Travel Trend Analysis')
            plt.xlabel('Month')
            plt.ylabel('Travel Volume')
            plt.grid(True, alpha=0.3)
            
            return "Trend analysis chart created successfully"
        except Exception as e:
            return f"Error creating trend chart: {str(e)}"
    
    def generate_all_charts(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Generate all available charts"""
        results = {}
        
        results['rating_distribution'] = self.create_rating_distribution_chart(data)
        results['price_vs_rating'] = self.create_price_vs_rating_chart(data)
        results['category_distribution'] = self.create_category_distribution_chart(data)
        results['trend_analysis'] = self.create_trend_analysis_chart(data)
        
        return results
