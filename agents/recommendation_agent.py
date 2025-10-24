import os
import sys


# Ensure project root (TRAVEL_PLANNER) is on sys.path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml_models.recommendation_engine import RecommendationEngine  # noqa: E402


recommendation_agent = RecommendationEngine()


