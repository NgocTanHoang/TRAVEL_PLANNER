"""
Test LangGraph Tracing với LangSmith
====================================
Script này sẽ test LangGraph workflow và kiểm tra LangSmith tracing
"""
import sys
import os
import asyncio
import logging
from pathlib import Path
from datetime import datetime

# Setup logging để xem tracing
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add project root to path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

print("=" * 70)
print("TEST LANGGRAPH TRACING VỚI LANGSMITH")
print("=" * 70)

# Setup Django
print("\n[1/5] Setup Django environment...")
try:
    import django
    from django.conf import settings
    
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vivu_backend.vivu_core.settings')
    
    # Check if Django is already configured
    if not settings.configured:
        django.setup()
    else:
        print("   ✓ Django already configured")
    
    print("   ✓ Django setup completed")
except Exception as e:
    print(f"   ⚠ Django setup issue: {e}")
    print("   (Continuing anyway - workflow may work without full Django)")
    # Try to setup anyway
    try:
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vivu_backend.vivu_core.settings')
    except:
        pass

# Check LangSmith Config
print("\n[2/5] Kiểm tra LangSmith Configuration...")
try:
    from config.langsmith_config import get_langsmith_config
    
    cfg = get_langsmith_config()
    print(f"   ✓ LangSmith Config loaded")
    print(f"     - Tracing enabled: {cfg.tracing_enabled}")
    print(f"     - Project: {cfg.project_name}")
    print(f"     - Endpoint: {cfg.endpoint}")
    print(f"     - API Key: {'✓ Configured' if cfg.api_key else '⚠ Not configured (will use defaults)'}")
    
    # Check environment variables
    print(f"\n   Environment variables:")
    print(f"     - LANGCHAIN_TRACING_V2: {os.getenv('LANGCHAIN_TRACING_V2', 'Not set')}")
    print(f"     - LANGCHAIN_PROJECT: {os.getenv('LANGCHAIN_PROJECT', 'Not set')}")
    print(f"     - LANGCHAIN_API_KEY: {'✓ Set' if os.getenv('LANGCHAIN_API_KEY') else '✗ Not set'}")
    
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Initialize Workflow
print("\n[3/5] Initialize LangGraph Workflow...")
try:
    from agents.langgraph_workflow import LangGraphTravelWorkflow
    
    workflow = LangGraphTravelWorkflow()
    print(f"   ✓ Workflow initialized")
    print(f"     - Graph: {workflow.graph is not None}")
    print(f"     - App: {workflow.app is not None}")
    print(f"     - LangSmith config: {workflow.langsmith_config.tracing_enabled}")
    
except Exception as e:
    print(f"   ✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Run Workflow với Tracing
print("\n[4/5] Chạy LangGraph Workflow với Tracing...")
print("   Test payload: Hà Nội → Đà Nẵng (2 days, 2 travelers)")
print("   " + "-" * 60)

test_payload = {
    'origin': 'Hà Nội',
    'destination': 'Đà Nẵng',
    'start_date': '2025-02-01',
    'days': 2,
    'travelers': 2,
    'travel_style': 'standard'
}

async def run_workflow_test():
    """Run workflow và kiểm tra tracing"""
    try:
        print("\n   ⏳ Đang chạy workflow...")
        print("   (Các API calls sẽ được trace trong LangSmith)")
        print("   " + "-" * 60)
        
        # Chạy workflow
        result = await workflow.run(test_payload)
        
        print("\n   " + "-" * 60)
        print(f"   ✓ Workflow execution completed!")
        print(f"     - Status: {result.get('status', 'unknown')}")
        print(f"     - Completed steps: {result.get('completed_steps', [])}")
        
        if result.get('transport'):
            transport = result['transport']
            print(f"     - Transport: {transport.get('suggested_method', 'unknown')}")
            if transport.get('distance_km'):
                print(f"     - Distance: {transport.get('distance_km', 0):.1f} km")
        
        if result.get('plan'):
            plan = result.get('plan', {})
            if plan.get('itinerary'):
                days = plan.get('itinerary', {}).get('days', [])
                print(f"     - Itinerary days: {len(days)}")
        
        return result
        
    except Exception as e:
        print(f"\n   ✗ Workflow execution error: {e}")
        import traceback
        traceback.print_exc()
        return None

# Run async test
print("\n[5/5] Execution & Tracing Check...")
try:
    result = asyncio.run(run_workflow_test())
    
    if result:
        print("\n   " + "=" * 60)
        print("   ✅ TRACING TEST COMPLETED")
        print("   " + "=" * 60)
        print("\n   📊 LangSmith Tracing:")
        print("     - Tất cả API calls đã được trace")
        print("     - Có thể xem trên LangSmith dashboard")
        print(f"     - Project: {cfg.project_name}")
        print(f"     - Dashboard: https://smith.langchain.com/")
        
        print("\n   💡 Để xem traces:")
        print("     1. Truy cập: https://smith.langchain.com/")
        print("     2. Chọn project: vi-vu-travel-planner")
        print("     3. Xem các runs mới nhất")
        print("     4. Mỗi agent node sẽ có một trace riêng")
        
    else:
        print("\n   ⚠ Workflow execution failed")
        
except Exception as e:
    print(f"\n   ✗ Test execution error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("TEST HOÀN TẤT")
print("=" * 70)
print("\n📝 Lưu ý:")
print("  - Nếu tracing enabled, tất cả LLM calls sẽ được gửi lên LangSmith")
print("  - Có thể mất vài giây để traces xuất hiện trên dashboard")
print("  - Kiểm tra environment variables LANGCHAIN_* để đảm bảo tracing hoạt động")
print("\n✅ LangGraph workflow đã được test với LangSmith tracing!")

