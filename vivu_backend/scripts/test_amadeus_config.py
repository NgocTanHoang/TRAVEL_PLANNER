"""Test Amadeus API configuration"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
load_dotenv(PROJECT_ROOT / '.env')

print("="*60)
print("AMADEUS API CONFIGURATION TEST")
print("="*60)
print(f"AMADEUS_API_KEY: {os.getenv('AMADEUS_API_KEY', 'NOT SET')}")
secret = os.getenv('AMADEUS_API_SECRET', 'NOT SET')
if secret != 'NOT SET':
    print(f"AMADEUS_API_SECRET: {secret[:10]}...{secret[-5:]}")
else:
    print(f"AMADEUS_API_SECRET: {secret}")
print(f"AMADEUS_ENVIRONMENT: {os.getenv('AMADEUS_ENVIRONMENT', 'NOT SET')}")
print("="*60)

# Test import
try:
    from tools.amadeus_tools import get_amadeus_tools
    amadeus = get_amadeus_tools()
    if amadeus.is_available():
        print("✓ Amadeus API client initialized successfully")
        print(f"  Environment: {amadeus.environment}")
    else:
        print("✗ Amadeus API client not available")
        print("  Check your API keys and ensure 'amadeus' package is installed")
        print("  Install with: pip install amadeus")
except ImportError as e:
    print(f"✗ Failed to import amadeus_tools: {e}")
except Exception as e:
    print(f"✗ Error: {e}")





