"""
Quick test script để verify LangSmith tracing đang hoạt động
"""
import os
import sys
from pathlib import Path

# Load config TRƯỚC khi check environment variables
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

# Load .env file nếu có
from dotenv import load_dotenv
_env_path = project_root / '.env'
if _env_path.exists():
    load_dotenv(_env_path, encoding='utf-8')

# Import config để set environment variables
from config.langsmith_config import get_langsmith_config

print("=" * 70)
print("KIỂM TRA NHANH LANGSMITH TRACING")
print("=" * 70)

# Initialize config để set environment variables
cfg = get_langsmith_config()

print("\n1. Environment Variables (sau khi load config):")
print(f"   LANGCHAIN_TRACING_V2: {os.getenv('LANGCHAIN_TRACING_V2', 'Not set')}")
print(f"   LANGCHAIN_PROJECT: {os.getenv('LANGCHAIN_PROJECT', 'Not set')}")
print(f"   LANGCHAIN_API_KEY: {'✓ Set' if os.getenv('LANGCHAIN_API_KEY') else '✗ Not set'}")
print(f"   LANGCHAIN_ENDPOINT: {os.getenv('LANGCHAIN_ENDPOINT', 'Not set')}")

print("\n2. LangSmith Config:")
print(f"   ✓ Config loaded")
print(f"   - Tracing enabled: {cfg.tracing_enabled}")
print(f"   - Project: {cfg.project_name}")
print(f"   - Endpoint: {cfg.endpoint}")
print(f"   - API Key: {'✓ Configured' if cfg.api_key else '✗ Not configured'}")
print(f"   - Is configured: {cfg.is_configured()}")

print("\n3. Tracing Status:")
tracing_enabled = os.getenv('LANGCHAIN_TRACING_V2', '').lower() == 'true'
if tracing_enabled:
    print("   ✅ TRACING ĐANG BẬT")
    print(f"   📊 Dashboard: https://smith.langchain.com/")
    print(f"   📁 Project: {os.getenv('LANGCHAIN_PROJECT', 'Not set')}")
else:
    print("   ⚠ TRACING CHƯA BẬT")
    print("   💡 Set LANGCHAIN_TRACING_V2=true để enable")

print("\n" + "=" * 70)

