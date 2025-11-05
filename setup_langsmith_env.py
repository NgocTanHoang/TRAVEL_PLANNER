"""
Script để set các environment variables cho LangSmith tracing
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv, set_key

# Get project root
project_root = Path(__file__).resolve().parent
env_path = project_root / '.env'

print("=" * 70)
print("SETUP LANGSMITH ENVIRONMENT VARIABLES")
print("=" * 70)

# Load existing .env nếu có
if env_path.exists():
    load_dotenv(env_path, encoding='utf-8')
    print(f"\n✓ File .env đã tồn tại: {env_path}")
else:
    print(f"\n⚠ File .env chưa tồn tại, sẽ tạo mới: {env_path}")
    env_path.touch()

# Get current values hoặc ask user
print("\n[1/4] LANGCHAIN_TRACING_V2:")
current_tracing = os.getenv('LANGCHAIN_TRACING_V2', 'true')
print(f"   Current: {current_tracing}")
print(f"   Setting to: true")
set_key(str(env_path), 'LANGCHAIN_TRACING_V2', 'true')

print("\n[2/4] LANGCHAIN_PROJECT:")
current_project = os.getenv('LANGCHAIN_PROJECT', 'vi-vu-travel-planner')
print(f"   Current: {current_project}")
print(f"   Setting to: vi-vu-travel-planner")
set_key(str(env_path), 'LANGCHAIN_PROJECT', 'vi-vu-travel-planner')

print("\n[3/4] LANGCHAIN_ENDPOINT:")
current_endpoint = os.getenv('LANGCHAIN_ENDPOINT', 'https://api.smith.langchain.com')
print(f"   Current: {current_endpoint}")
print(f"   Setting to: https://api.smith.langchain.com")
set_key(str(env_path), 'LANGCHAIN_ENDPOINT', 'https://api.smith.langchain.com')

print("\n[4/4] LANGCHAIN_API_KEY:")
current_api_key = os.getenv('LANGCHAIN_API_KEY', '')
if current_api_key:
    print(f"   Current: {'*' * min(len(current_api_key), 20)}... (hidden)")
    print(f"   ✓ API Key đã có trong .env")
else:
    print(f"   Current: Not set")
    print(f"   ⚠ LANGCHAIN_API_KEY chưa được set trong .env")
    print(f"   💡 Bạn cần thêm LANGCHAIN_API_KEY vào file .env")
    print(f"   💡 Hoặc set environment variable trong system")

# Reload và verify
load_dotenv(env_path, override=True, encoding='utf-8')

print("\n" + "=" * 70)
print("KẾT QUẢ")
print("=" * 70)

print("\n✓ Đã set các biến sau vào .env:")
print(f"   - LANGCHAIN_TRACING_V2=true")
print(f"   - LANGCHAIN_PROJECT=vi-vu-travel-planner")
print(f"   - LANGCHAIN_ENDPOINT=https://api.smith.langchain.com")
if os.getenv('LANGCHAIN_API_KEY'):
    print(f"   - LANGCHAIN_API_KEY=✓ (đã có)")
else:
    print(f"   - LANGCHAIN_API_KEY=✗ (chưa có)")

print("\n💡 Lưu ý:")
print("   - Các biến đã được set vào file .env")
print("   - Nếu LANGCHAIN_API_KEY chưa có, bạn cần:")
print("     1. Lấy API key từ: https://smith.langchain.com/settings")
print("     2. Thêm vào file .env: LANGCHAIN_API_KEY=your_api_key_here")
print("   - Sau khi thêm API key, chạy lại: python check_tracing.py")

print("\n✅ Setup hoàn tất!")

