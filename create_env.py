"""
Tạo file .env với UTF-8 encoding đúng cách
"""

env_content = """# API KEYS - TRAVEL PLANNER MULTI-AGENT SYSTEM
# NOTE: Do NOT commit real API keys. Replace the values below with your own keys locally or set them in a local .env file.

# OPENAI - REQUIRED (set as environment variable OPENAI_API_KEY)
OPENAI_API_KEY=REDACTED_OPENAI_API_KEY

# WEB SEARCH (set as TAVILY_API_KEY)
TAVILY_API_KEY=REDACTED_TAVILY_API_KEY

# WEATHER API
OPENWEATHER_API_KEY=REDACTED_OPENWEATHER_API_KEY

# PLACES APIs - FREE (set as environment variables)
LOCATIONIQ_API_KEY=REDACTED_LOCATIONIQ_API_KEY
GEOAPIFY_API_KEY=REDACTED_GEOAPIFY_API_KEY
"""

with open('.env', 'w', encoding='utf-8') as f:
    f.write(env_content)

print("✅ Đã tạo file .env với UTF-8 encoding!")


