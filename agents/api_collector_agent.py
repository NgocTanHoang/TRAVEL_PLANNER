import os
import sys


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_collection.api_collector import APICollector  # noqa: E402


api_collector_agent = APICollector()


