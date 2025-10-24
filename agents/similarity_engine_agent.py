import os
import sys


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml_models.similarity_engine import SimilarityEngine  # noqa: E402


similarity_engine_agent = SimilarityEngine()


