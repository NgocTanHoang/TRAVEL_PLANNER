import os
import sys


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_collection.web_scraper import WebScraper  # noqa: E402


web_scraper_agent = WebScraper()


