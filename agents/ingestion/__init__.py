"""
Ingestion Agents Module
========================
Các agent nặng chỉ chạy nền (offline jobs), không chạy trong luồng tương tác.
"""

# Import các agent nặng
from .api_collector import APICollectorAgent
from .web_scraper import WebScraperAgent
from .data_validator import DataValidatorAgent
from .data_processor import DataProcessorAgent
from .place_classifier import PlaceClassifierAgent

__all__ = [
    'APICollectorAgent',
    'WebScraperAgent',
    'DataValidatorAgent',
    'DataProcessorAgent',
    'PlaceClassifierAgent'
]

