import os
import sys

# Ensure project root (TRAVEL_PLANNER) is on sys.path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class PlannerAgent:
    """Travel planning agent for creating itineraries"""
    
    def __init__(self):
        self.name = "planner_agent"
        self.description = "Creates travel itineraries and plans"
    
    def create_itinerary(self, destination: str, days: int, budget: int, travelers: int) -> dict:
        """Create a travel itinerary"""
        return {
            "destination": destination,
            "days": days,
            "budget": budget,
            "travelers": travelers,
            "itinerary": self._generate_itinerary(destination, days),
            "status": "SUCCESS"
        }
    
    def _generate_itinerary(self, destination: str, days: int) -> dict:
        """Generate day-by-day itinerary"""
        itinerary = {}
        
        for day in range(1, days + 1):
            itinerary[f"Day {day}"] = {
                "morning": f"Explore {destination} attractions",
                "afternoon": f"Visit local restaurants and markets",
                "evening": f"Enjoy {destination} nightlife"
            }
        
        return itinerary

# Create agent instance
planner_agent = PlannerAgent()