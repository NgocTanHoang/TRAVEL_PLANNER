import os
import sys


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_collection.data_processor import DataProcessor  # noqa: E402


data_processor_agent = DataProcessor()


