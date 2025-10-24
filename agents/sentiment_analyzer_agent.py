import os
import sys


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml_models.sentiment_analyzer import SentimentAnalyzer  # noqa: E402


sentiment_analyzer_agent = SentimentAnalyzer()


