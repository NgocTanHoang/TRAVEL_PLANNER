import os
import sys


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml_models.price_predictor import PricePredictor  # noqa: E402


price_predictor_agent = PricePredictor()


