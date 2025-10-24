import os
import sys

# Ensure project root (TRAVEL_PLANNER) is on sys.path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class ResearcherAgent:
    """Research agent for gathering travel information"""
    
    def __init__(self):
        self.name = "research_agent"
        self.description = "Researches travel destinations and information"
    
    def research_destination(self, destination: str) -> dict:
        """Research a travel destination"""
        return {
            "destination": destination,
            "research_data": self._gather_research_data(destination),
            "status": "SUCCESS"
        }
    
    def _gather_research_data(self, destination: str) -> dict:
        """Gather research data about destination"""
        return {
            "attractions": f"Top attractions in {destination}",
            "culture": f"Cultural highlights of {destination}",
            "food": f"Local cuisine and dining in {destination}",
            "transportation": f"Getting around {destination}",
            "tips": f"Travel tips for {destination}"
        }

# Create agent instance
research_agent = ResearcherAgent()