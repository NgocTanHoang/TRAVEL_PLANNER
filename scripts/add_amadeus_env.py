"""Script to add Amadeus API keys to .env file"""
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / '.env'

# Amadeus credentials
# NOTE: Replace with your own API keys from https://developers.amadeus.com/
AMADEUS_CONFIG = """
# Amadeus API (Test Environment)
AMADEUS_API_KEY=your_amadeus_api_key_here
AMADEUS_API_SECRET=your_amadeus_api_secret_here
AMADEUS_ENVIRONMENT=test
"""

print(f"Adding Amadeus API configuration to {ENV_FILE}")

# Read existing content
existing_content = ""
if ENV_FILE.exists():
    try:
        with open(ENV_FILE, 'r', encoding='utf-8') as f:
            existing_content = f.read()
    except Exception as e:
        print(f"Warning: Could not read existing .env file: {e}")

# Check if already exists
if 'AMADEUS_API_KEY' in existing_content:
    print("Amadeus API keys already exist in .env file")
    print("Skipping...")
else:
    # Append to file
    try:
        with open(ENV_FILE, 'a', encoding='utf-8') as f:
            f.write(AMADEUS_CONFIG)
        print("✓ Successfully added Amadeus API configuration to .env")
    except Exception as e:
        print(f"✗ Error writing to .env file: {e}")





