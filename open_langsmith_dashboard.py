"""
Script để mở LangSmith Dashboard trong browser
"""
import webbrowser
import os
from pathlib import Path
import sys

# Load config để có project name
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
_env_path = project_root / '.env'
if _env_path.exists():
    load_dotenv(_env_path, encoding='utf-8')

from config.langsmith_config import get_langsmith_config

cfg = get_langsmith_config()
project_name = cfg.project_name

print("=" * 70)
print("MỞ LANGSMITH DASHBOARD")
print("=" * 70)

# LangSmith dashboard URLs
dashboard_url = "https://smith.langchain.com/"
project_url = f"https://smith.langchain.com/o/default/projects/p/{project_name}"

print(f"\n📊 LangSmith Dashboard:")
print(f"   - Main Dashboard: {dashboard_url}")
print(f"   - Project: {project_name}")
print(f"   - Project URL: {project_url}")

print(f"\n🔑 Configuration:")
print(f"   - Tracing enabled: {cfg.tracing_enabled}")
print(f"   - Project: {cfg.project_name}")
print(f"   - API Key: {'✓ Configured' if cfg.api_key else '✗ Not configured'}")

print(f"\n🌐 Đang mở browser...")
try:
    # Mở project URL nếu có API key, nếu không thì mở main dashboard
    if cfg.api_key:
        webbrowser.open(project_url)
        print(f"   ✓ Đã mở project page: {project_name}")
    else:
        webbrowser.open(dashboard_url)
        print(f"   ✓ Đã mở main dashboard")
except Exception as e:
    print(f"   ✗ Error: {e}")
    print(f"\n💡 Bạn có thể mở thủ công:")
    print(f"   {project_url}")

print("\n" + "=" * 70)
print("HƯỚNG DẪN")
print("=" * 70)
print("\n1. Trên dashboard, bạn sẽ thấy:")
print("   - Tất cả các runs/traces từ workflow")
print("   - Chi tiết từng agent node")
print("   - LLM calls với prompts và responses")
print("   - Execution time và performance metrics")
print("\n2. Để xem traces mới nhất:")
print("   - Chọn project: vi-vu-travel-planner")
print("   - Xem runs mới nhất (sắp xếp theo thời gian)")
print("\n3. Mỗi trace sẽ hiển thị:")
print("   - Input/Output của từng agent")
print("   - Graph visualization của workflow")
print("   - Token usage và costs")
print("   - Error logs (nếu có)")

