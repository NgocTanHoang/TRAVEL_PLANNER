import os
import sys


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from visualization.analytics_engine import AnalyticsEngine  # noqa: E402


analytics_engine_agent = AnalyticsEngine()


