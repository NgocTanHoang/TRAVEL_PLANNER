import sys
import os
from pathlib import Path
import asyncio
import logging

# Setup paths
BACKEND_DIR = Path(__file__).parent / "vivu_backend"
sys.path.append(str(BACKEND_DIR)) # Append to end to prioritize root 'agents' package
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vivu_core.settings')
import django
django.setup()

# Setup logging
logging.basicConfig(level=logging.DEBUG)

async def debug_transport():
    from agents.travel_agents.transport_agent import TransportAgent
    import sys
    print(f"TransportAgent loaded from: {sys.modules['agents.travel_agents.transport_agent'].__file__}")
    agent = TransportAgent()
    
    origin = "Ho Chi Minh City"
    dest = "Da Nang"
    
    print(f"\nTesting Transport: {origin} -> {dest}")
    state = {'origin': origin, 'destination': dest, 'travelers': 1}
    
    result_state = await agent.execute(state)
    
    transport_info = result_state.get('transport', {})
    method = transport_info.get('suggested_method')
    distance = transport_info.get('distance_km', 0)
    error = result_state.get('transport_error')
    
    print(f"\nResult State Keys: {list(result_state.keys())}")
    print(f"Transport Info: {transport_info}")
    print(f"Method: '{method}' (Type: {type(method)})")
    print(f"Distance: {distance} (Type: {type(distance)})")
    print(f"Error: {error} (Type: {type(error)})")
    
    passed = method and distance > 0 and not error
    print(f"\nPassed: {passed}")
    
    if not passed:
        print("Why failed?")
        print(f"  method check: {bool(method)}")
        print(f"  distance check: {distance > 0}")
        print(f"  error check: {not error}")

if __name__ == "__main__":
    asyncio.run(debug_transport())
