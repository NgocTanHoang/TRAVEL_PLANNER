"""
Test workflow với LangSmith tự động tạo project
"""
import sys
import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv

project_root = Path(__file__).resolve().parent
load_dotenv(project_root / '.env', encoding='utf-8')

sys.path.insert(0, str(project_root))

print("=" * 70)
print("TEST WORKFLOW - LANGSMITH AUTO-CREATE PROJECT")
print("=" * 70)

# Check config
from config.langsmith_config import get_langsmith_config
cfg = get_langsmith_config()

print(f"\n✓ Tracing enabled: {cfg.tracing_enabled}")
print(f"✓ API Key: {'✓ Configured' if cfg.api_key else '✗ Not configured'}")
print(f"✓ Project: {cfg.project_name if cfg.project_name else 'None (LangSmith sẽ tự động tạo)'}")

# Setup Django
try:
    import django
    from django.conf import settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vivu_backend.vivu_core.settings')
    if not settings.configured:
        django.setup()
except:
    pass

# Run workflow
async def test():
    from agents.langgraph_workflow import LangGraphTravelWorkflow
    
    workflow = LangGraphTravelWorkflow()
    
    test_payload = {
        'origin': 'Hà Nội',
        'destination': 'Đà Nẵng',
        'start_date': '2025-02-01',
        'days': 2,
        'travelers': 2,
        'travel_style': 'standard'
    }
    
    print("\n⏳ Chạy workflow...")
    print("   LangSmith sẽ tự động tạo project mới nếu chưa có")
    
    result = await workflow.run(test_payload)
    
    print(f"\n✓ Workflow completed: {result.get('status')}")
    print(f"\n💡 Kiểm tra LangSmith dashboard:")
    print("   https://smith.langchain.com/")
    print("   LangSmith sẽ tự động tạo project mới với tên ngẫu nhiên")

asyncio.run(test())

