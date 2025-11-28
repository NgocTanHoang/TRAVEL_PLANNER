"""
Comprehensive Agent Testing Suite
==================================
Tests all agents individually and the complete workflow
"""
import sys
import os
from pathlib import Path
import json
from datetime import datetime
import asyncio

# Add paths
BACKEND_DIR = Path(__file__).parent / "vivu_backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Fix encoding for Windows PowerShell
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add parent directory to handle relative imports inside langgraph_workflow
CURRENT_DIR = Path(__file__).parent.absolute()
PARENT_DIR = CURRENT_DIR.parent
if str(PARENT_DIR) not in sys.path:
    sys.path.insert(0, str(PARENT_DIR))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vivu_core.settings')
import django
django.setup()

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*80)
    print(f" {title}")
    print("="*80)

def print_subsection(title):
    """Print a formatted subsection header"""
    print("\n" + "-"*80)
    print(f" {title}")
    print("-"*80)

def print_result(test_name, passed, details=""):
    """Print test result"""
    status = "[PASS]" if passed else "[FAIL]"
    print(f"{status} {test_name}")
    if details:
        print(f"      {details}")

# ============================================================================
# TEST 1: GEO TOOLS
# ============================================================================
def test_geo_tools():
    print_section("TEST 1: GEO TOOLS")
    
    from tools.geo_tools import get_geo_tools
    geo_tools = get_geo_tools()
    
    results = {'passed': 0, 'failed': 0}
    
    # Test 1.1: Geocoding
    print_subsection("1.1 Geocoding")
    test_locations = [
        "Ho Chi Minh City",
        "Da Nang",
        "Hanoi",
        "Nha Trang"
    ]
    
    for location in test_locations:
        try:
            result = geo_tools.geocode(location)
            passed = result and result.get('lat') and result.get('lon')
            print_result(f"Geocode: {location}", passed, 
                        f"Coords: ({result.get('lat')}, {result.get('lon')})" if passed else "Failed")
            if passed:
                results['passed'] += 1
            else:
                results['failed'] += 1
        except Exception as e:
            print_result(f"Geocode: {location}", False, str(e))
            results['failed'] += 1
    
    # Test 1.2: Distance Calculation
    print_subsection("1.2 Distance Calculation")
    test_routes = [
        ("Ho Chi Minh City", "Da Nang"),
        ("Hanoi", "Da Nang"),
        ("Ho Chi Minh City", "Vung Tau")
    ]
    
    for origin, dest in test_routes:
        try:
            result = geo_tools.calculate_distance_time(origin, dest)
            distance = result.get('distance_km', 0) if result else 0
            passed = result and distance > 0
            print_result(f"Route: {origin} -> {dest}", passed,
                        f"Distance: {distance:.2f} km" if passed else "Distance is 0 or None")
            if passed:
                results['passed'] += 1
            else:
                results['failed'] += 1
        except Exception as e:
            print_result(f"Route: {origin} -> {dest}", False, str(e))
            results['failed'] += 1
    
    print(f"\nGeo Tools Summary: {results['passed']} passed, {results['failed']} failed")
    return results

# ============================================================================
# TEST 2: TRANSPORT AGENT
# ============================================================================
async def test_transport_agent_async():
    print_section("TEST 2: TRANSPORT AGENT")
    
    from agents.travel_agents.transport_agent import TransportAgent
    from tools.transport_tools import TransportTools
    
    agent = TransportAgent()
    transport_tools = TransportTools()
    
    results = {'passed': 0, 'failed': 0}
    
    # Test 2.1: Transport Suggestions
    print_subsection("2.1 Transport Suggestions")
    test_routes = [
        ("Ho Chi Minh City", "Da Nang", "flight"),  # Long distance
        ("Hanoi", "Haiphong", "car"),  # Medium distance
        ("District 1", "District 3", "grab"),  # Short distance
    ]
    
    for origin, dest, expected_method in test_routes:
        try:
            # Transport Agent execute is async
            state = {'origin': origin, 'destination': dest, 'travelers': 1}
            result_state = await agent.execute(state)
            
            # Correct key is 'transport'
            transport_info = result_state.get('transport', {})
            method = transport_info.get('suggested_method')
            distance = transport_info.get('distance_km', 0)
            
            passed = method and distance > 0 and not result_state.get('transport_error')
            
            details = f"Method: {method}, Distance: {distance:.2f} km"
            if not passed:
                details = f"Failed. Transport info: {transport_info}. Error: {result_state.get('transport_error')}. State: {result_state}"
            
            print_result(f"Suggest: {origin} -> {dest}", passed, details)
            if passed:
                results['passed'] += 1
            else:
                results['failed'] += 1
        except Exception as e:
            print_result(f"Suggest: {origin} -> {dest}", False, str(e))
            results['failed'] += 1
    
    # Test 2.2: Cost Calculation (Sync method in tools)
    print_subsection("2.2 Cost Calculation")
    test_costs = [
        (100, "grab", 1),
        (500, "long_distance_bus", 2),
        (50, "motorbike", 1)
    ]
    
    for distance, method, travelers in test_costs:
        try:
            cost_info = transport_tools.calculate_transport_cost(distance, method, travelers)
            cost = cost_info.get('cost_vnd', 0)
            passed = cost > 0
            print_result(f"Cost: {distance}km by {method}", passed,
                        f"Cost: {cost:,.0f} VND for {travelers} pax" if passed else "Cost is 0")
            if passed:
                results['passed'] += 1
            else:
                results['failed'] += 1
        except Exception as e:
            print_result(f"Cost: {distance}km by {method}", False, str(e))
            results['failed'] += 1
    
    print(f"\nTransport Agent Summary: {results['passed']} passed, {results['failed']} failed")
    return results

def test_transport_agent():
    return asyncio.run(test_transport_agent_async())

# ============================================================================
# TEST 3: ACCOMMODATION AGENT
# ============================================================================
async def test_accommodation_agent_async():
    print_section("TEST 3: ACCOMMODATION AGENT")
    
    from agents.travel_agents.accommodation_agent import AccommodationAgent
    
    agent = AccommodationAgent()
    results = {'passed': 0, 'failed': 0}
    
    # Test 3.1: Hotel Search
    print_subsection("3.1 Hotel Search")
    test_searches = [
        ("Da Nang", "2025-12-01", "2025-12-03", 2),
        ("Ho Chi Minh City", "2025-12-10", "2025-12-12", 1),
    ]
    
    for location, checkin, checkout, guests in test_searches:
        try:
            state = {
                'destination': location,
                'check_in': checkin,   # Correct key
                'check_out': checkout, # Correct key
                'guests': guests,      # Correct key
                'rooms': 1
            }
            # Execute is async
            result = await agent.execute(state)
            
            # Correct key is 'hotels'
            hotels = result.get('hotels', [])
            passed = len(hotels) > 0
            
            details = f"Found {len(hotels)} hotels"
            if not passed:
                details = f"No hotels found. Error: {result.get('accommodation_error', 'None')}. Keys: {list(result.keys())}"
            
            print_result(f"Search: {location} ({checkin} to {checkout})", passed, details)
            if passed:
                results['passed'] += 1
            else:
                results['failed'] += 1
        except Exception as e:
            print_result(f"Search: {location}", False, str(e))
            results['failed'] += 1
    
    print(f"\nAccommodation Agent Summary: {results['passed']} passed, {results['failed']} failed")
    return results

def test_accommodation_agent():
    return asyncio.run(test_accommodation_agent_async())

# ============================================================================
# TEST 4: ACTIVITIES AGENT
# ============================================================================
async def test_activities_agent_async():
    print_section("TEST 4: ACTIVITIES AGENT")
    
    from agents.travel_agents.activities_agent import ActivitiesAgent
    
    agent = ActivitiesAgent()
    results = {'passed': 0, 'failed': 0}
    
    # Test 4.1: Activity Search
    print_subsection("4.1 Activity Search")
    test_searches = [
        ("Da Nang", ["beach", "culture"]),
        ("Ho Chi Minh City", ["food", "history"]),
        ("Hanoi", ["culture", "shopping"])
    ]
    
    for destination, interests in test_searches:
        try:
            state = {
                'destination': destination,
                'interests': interests,
                'travelers': 2
            }
            # Execute is async
            result = await agent.execute(state)
            activities = result.get('activities', [])
            passed = len(activities) > 0
            print_result(f"Activities: {destination} ({', '.join(interests)})", passed,
                        f"Found {len(activities)} activities" if passed else "No activities found")
            if passed:
                results['passed'] += 1
            else:
                results['failed'] += 1
        except Exception as e:
            print_result(f"Activities: {destination}", False, str(e))
            results['failed'] += 1
    
    print(f"\nActivities Agent Summary: {results['passed']} passed, {results['failed']} failed")
    return results

def test_activities_agent():
    return asyncio.run(test_activities_agent_async())

# ============================================================================
# TEST 5: FLIGHT AGENT
# ============================================================================
async def test_flight_agent_async():
    print_section("TEST 5: FLIGHT AGENT")
    
    from agents.travel_agents.flight_agent import FlightAgent
    
    agent = FlightAgent()
    results = {'passed': 0, 'failed': 0}
    
    # Test 5.1: Flight Search
    print_subsection("5.1 Flight Search")
    test_searches = [
        ("Ho Chi Minh City", "Da Nang", "2025-12-01", 2),
        ("Hanoi", "Ho Chi Minh City", "2025-12-15", 1),
    ]
    
    for origin, dest, date, passengers in test_searches:
        try:
            state = {
                'origin': origin,
                'destination': dest,
                'departure_date': date, # Correct key
                'passengers': passengers # Correct key
            }
            # Execute is async
            result = await agent.execute(state)
            
            # Correct key is 'flight'
            flight_info = result.get('flight')
            # Check if flight info exists and has price
            passed = flight_info and flight_info.get('price_vnd', 0) > 0
            
            details = f"Found flight: {flight_info.get('price_vnd', 0):,.0f} VND" if passed else f"No flights found. Error: {result.get('flight_error', 'None')}"
            
            print_result(f"Flights: {origin} -> {dest} on {date}", passed, details)
            if passed:
                results['passed'] += 1
            else:
                results['failed'] += 1
        except Exception as e:
            print_result(f"Flights: {origin} -> {dest}", False, str(e))
            results['failed'] += 1
    
    print(f"\nFlight Agent Summary: {results['passed']} passed, {results['failed']} failed")
    return results

def test_flight_agent():
    return asyncio.run(test_flight_agent_async())

# ============================================================================
# TEST 6: COMPLETE WORKFLOW
# ============================================================================
async def test_complete_workflow_async():
    print_section("TEST 6: COMPLETE WORKFLOW")
    
    results = {'passed': 0, 'failed': 0}
    
    # Test 6.1: 4-Step Workflow
    print_subsection("6.1 Complete Travel Planning Workflow")
    
    test_cases = [
        {
            'name': 'HCM to Da Nang - Beach Vacation',
            'input': {
                'origin': 'Ho Chi Minh City',
                'destination': 'Da Nang',
                'start_date': '2025-12-01',
                'end_date': '2025-12-05',
                'travelers': 2,
                'interests': ['beach', 'culture', 'food']
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\nTest Case: {test_case['name']}")
        print("-" * 60)
        
        try:
            # Adjust path for workflow import
            current_dir = Path(__file__).parent.absolute()
            if str(current_dir) not in sys.path:
                sys.path.insert(0, str(current_dir))
            
            # Import workflow
            try:
                from agents.langgraph_workflow import LangGraphTravelWorkflow
            except ImportError as e:
                print(f"[ERROR] Import failed: {e}")
                print(f"Current sys.path: {sys.path}")
                raise
            
            # Create workflow instance
            workflow = LangGraphTravelWorkflow()
            
            # Run workflow
            initial_state = test_case['input']
            
            # Ensure 'days' is present
            if 'days' not in initial_state and 'start_date' in initial_state and 'end_date' in initial_state:
                 from datetime import datetime
                 start = datetime.strptime(initial_state['start_date'], '%Y-%m-%d')
                 end = datetime.strptime(initial_state['end_date'], '%Y-%m-%d')
                 initial_state['days'] = max(1, (end - start).days)
            
            print(f"Input: {json.dumps(initial_state, indent=2)}")
            
            # Run workflow
            final_state = await workflow.run(initial_state)
            
            # Check results
            checks = {
                'Transport': 'transport' in final_state and final_state.get('transport'),
                'Accommodation': 'hotels' in final_state and len(final_state.get('hotels', [])) > 0,
                'Activities': 'activities' in final_state and len(final_state.get('activities', [])) > 0,
                'Itinerary': 'itinerary' in final_state and final_state.get('itinerary')
            }
            
            print("\nResults:")
            for component, passed in checks.items():
                print_result(component, passed)
                if passed:
                    results['passed'] += 1
                else:
                    results['failed'] += 1
            
            # Print summary
            if all(checks.values()):
                print(f"\n[SUCCESS] Complete workflow passed for: {test_case['name']}")
                
                # Print key results
                print("\nKey Results:")
                print(f"  Transport: {final_state.get('transport_method')}")
                print(f"  Hotels: {len(final_state.get('accommodation_options', []))} options")
                print(f"  Activities: {len(final_state.get('activities', []))} activities")
                print(f"  Itinerary: {len(final_state.get('itinerary', {}).get('days', []))} days")
            else:
                print(f"\n[FAILURE] Workflow incomplete for: {test_case['name']}")
                
        except Exception as e:
            print_result(f"Workflow: {test_case['name']}", False, str(e))
            results['failed'] += 4  # All 4 components failed
            import traceback
            traceback.print_exc()
    
    print(f"\nWorkflow Summary: {results['passed']} passed, {results['failed']} failed")
    return results

def test_complete_workflow():
    return asyncio.run(test_complete_workflow_async())

# ============================================================================
# MAIN TEST RUNNER
# ============================================================================
def run_all_tests():
    print_section("COMPREHENSIVE AGENT & WORKFLOW TEST SUITE")
    print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    all_results = {
        'geo_tools': None,
        'transport_agent': None,
        'accommodation_agent': None,
        'activities_agent': None,
        'flight_agent': None,
        'workflow': None
    }
    
    # Run all tests
    try:
        all_results['geo_tools'] = test_geo_tools()
    except Exception as e:
        print(f"\n[ERROR] Geo Tools test failed: {e}")
    
    try:
        all_results['transport_agent'] = test_transport_agent()
    except Exception as e:
        print(f"\n[ERROR] Transport Agent test failed: {e}")
    
    try:
        all_results['accommodation_agent'] = test_accommodation_agent()
    except Exception as e:
        print(f"\n[ERROR] Accommodation Agent test failed: {e}")
    
    try:
        all_results['activities_agent'] = test_activities_agent()
    except Exception as e:
        print(f"\n[ERROR] Activities Agent test failed: {e}")
    
    try:
        all_results['flight_agent'] = test_flight_agent()
    except Exception as e:
        print(f"\n[ERROR] Flight Agent test failed: {e}")
    
    try:
        all_results['workflow'] = test_complete_workflow()
    except Exception as e:
        print(f"\n[ERROR] Workflow test failed: {e}")
    
    # Print final summary
    print_section("FINAL SUMMARY")
    
    total_passed = 0
    total_failed = 0
    
    for component, result in all_results.items():
        if result:
            passed = result['passed']
            failed = result['failed']
            total_passed += passed
            total_failed += failed
            status = "[PASS]" if failed == 0 else "[FAIL]"
            print(f"{status} {component.replace('_', ' ').title()}: {passed} passed, {failed} failed")
        else:
            print(f"[SKIP] {component.replace('_', ' ').title()}: Not tested")
    
    print("\n" + "="*80)
    print(f"TOTAL: {total_passed} passed, {total_failed} failed")
    success_rate = (total_passed / (total_passed + total_failed) * 100) if (total_passed + total_failed) > 0 else 0
    print(f"Success Rate: {success_rate:.1f}%")
    print(f"End Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # Save results to file
    output_file = 'test_results_comprehensive.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'timestamp': datetime.now().isoformat(),
            'total_passed': total_passed,
            'total_failed': total_failed,
            'success_rate': success_rate,
            'results': all_results
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\nResults saved to: {output_file}")
    
    return total_failed == 0

if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[FATAL ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
