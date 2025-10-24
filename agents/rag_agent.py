"""
RAG Agent - Retrieval Augmented Generation
===========================================
Kết hợp Vector DB + Tavily Search + OpenAI GPT-4
"""

import os
from typing import List, Dict, Any, Optional
from pathlib import Path
import sys

# Add parent to path
sys.path.append(str(Path(__file__).parent.parent))

from agents.vector_db_agent import get_vector_db_agent
from config.settings import OPENAI_API_KEY, MODEL


class RAGAgent:
    """RAG Agent cho travel recommendations"""
    
    def __init__(self):
        """Initialize RAG Agent"""
        # Vector Database
        self.vector_db = get_vector_db_agent()
        
        # OpenAI
        try:
            from langchain_openai import ChatOpenAI
            self.llm = ChatOpenAI(
                model=MODEL,
                temperature=0.7,
                api_key=OPENAI_API_KEY
            )
            print("✅ RAG Agent initialized with OpenAI")
        except Exception as e:
            print(f"⚠️  OpenAI initialization warning: {e}")
            self.llm = None
        
        # Tavily (optional)
        self.tavily_api_key = os.getenv('TAVILY_API_KEY')
        if self.tavily_api_key:
            try:
                from tavily import TavilyClient
                self.tavily = TavilyClient(api_key=self.tavily_api_key)
                print("✅ Tavily search enabled")
            except:
                self.tavily = None
                print("⚠️  Tavily not available")
        else:
            self.tavily = None
    
    def get_recommendations(
        self,
        destination: str,
        budget: int,
        days: int,
        travelers: int,
        interests: str = ""
    ) -> Dict[str, Any]:
        """
        Get RAG-enhanced recommendations
        
        Flow:
        1. Vector DB semantic search (local data)
        2. Tavily real-time search (web data) 
        3. Combine context
        4. OpenAI generation
        
        Args:
            destination: Điểm đến
            budget: Ngân sách
            days: Số ngày
            travelers: Số người
            interests: Sở thích
        
        Returns:
            Comprehensive recommendations
        """
        print(f"\n🤖 RAG Agent processing...")
        print(f"   Destination: {destination}")
        print(f"   Budget: {budget:,} VND")
        print(f"   Days: {days}")
        print(f"   Interests: {interests}")
        
        # Step 1: Vector DB Search (Semantic)
        print(f"\n1️⃣  Searching Vector Database...")
        vector_results = self.vector_db.get_recommendations(
            destination=destination,
            interests=interests,
            budget=budget,
            days=days,
            travelers=travelers,
            n_results=15
        )
        
        print(f"   ✅ Hotels: {len(vector_results['hotels'])}")
        print(f"   ✅ Restaurants: {len(vector_results['restaurants'])}")
        print(f"   ✅ Attractions: {len(vector_results['attractions'])}")
        
        # Step 2: Tavily Search (Real-time Web)
        web_results = {}
        if self.tavily:
            print(f"\n2️⃣  Searching Web (Tavily)...")
            web_results = self._tavily_search(destination, interests)
            print(f"   ✅ Found {len(web_results.get('results', []))} web results")
        else:
            print(f"\n2️⃣  Tavily search skipped (not configured)")
        
        # Step 3: Combine Context
        print(f"\n3️⃣  Combining context...")
        context = self._combine_context(vector_results, web_results, {
            'destination': destination,
            'budget': budget,
            'days': days,
            'travelers': travelers,
            'interests': interests
        })
        
        # Step 4: Generate with OpenAI (Optional enhancement)
        if self.llm and interests:  # Only if user has specific interests
            print(f"\n4️⃣  Enhancing with OpenAI...")
            enhanced = self._enhance_with_openai(context)
            context['ai_insights'] = enhanced
        
        print(f"\n✅ RAG processing completed!")
        return context
    
    def _tavily_search(self, destination: str, interests: str) -> Dict[str, Any]:
        """Search web với Tavily"""
        try:
            query = f"du lịch {destination} {interests} 2025 địa điểm ngon bổ rẻ"
            results = self.tavily.search(
                query=query,
                search_depth="basic",
                max_results=5
            )
            return results
        except Exception as e:
            print(f"   ⚠️  Tavily search error: {e}")
            return {}
    
    def _combine_context(
        self,
        vector_results: Dict[str, List[Dict]],
        web_results: Dict[str, Any],
        user_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Combine all context sources"""
        
        # Filter and rank by budget
        budget_per_day = user_input['budget'] / user_input['days']
        
        # Hotels: Filter by budget
        hotels = self._filter_by_budget(
            vector_results['hotels'],
            budget_per_day * 0.4,  # 40% for hotel
            'hotel'
        )
        
        # Restaurants: Filter by budget
        restaurants = self._filter_by_budget(
            vector_results['restaurants'],
            budget_per_day * 0.3 / 3,  # 30% for 3 meals
            'restaurant'
        )
        
        # Attractions
        attractions = vector_results['attractions'][:10]
        
        return {
            'recommendations': {
                'hotels': hotels[:5],
                'restaurants': restaurants[:5],
                'attractions': attractions[:5]
            },
            'all_options': {
                'hotels': hotels[:10],
                'restaurants': restaurants[:10],
                'attractions': attractions[:10]
            },
            'web_insights': web_results.get('results', []),
            'user_context': user_input
        }
    
    def _filter_by_budget(
        self,
        places: List[Dict],
        budget_limit: float,
        place_type: str
    ) -> List[Dict]:
        """Filter places by budget"""
        filtered = []
        
        for place in places:
            price = place.get('price', 0)
            
            # Skip if price unknown
            if price == 0:
                continue
            
            # Check if within budget (with 20% flexibility)
            if price <= budget_limit * 1.2:
                filtered.append(place)
        
        # If nothing found, return best rated regardless of price
        if not filtered and places:
            filtered = sorted(places, key=lambda x: x.get('rating', 0), reverse=True)
        
        # Sort by rating
        filtered.sort(key=lambda x: (x.get('rating', 0), -x.get('price', 0)), reverse=True)
        
        return filtered
    
    def _enhance_with_openai(self, context: Dict[str, Any]) -> str:
        """Generate insights với OpenAI"""
        try:
            user_ctx = context['user_context']
            hotels = context['recommendations']['hotels']
            restaurants = context['recommendations']['restaurants']
            attractions = context['recommendations']['attractions']
            
            prompt = f"""Bạn là chuyên gia du lịch Việt Nam. 
            
Dựa trên thông tin:
- Điểm đến: {user_ctx['destination']}
- Ngân sách: {user_ctx['budget']:,} VND
- Số ngày: {user_ctx['days']}
- Sở thích: {user_ctx['interests']}

Top địa điểm được gợi ý:
Hotels: {', '.join([h['name'] for h in hotels[:3]])}
Restaurants: {', '.join([r['name'] for r in restaurants[:3]])}
Attractions: {', '.join([a['name'] for a in attractions[:3]])}

Hãy đưa ra 3 insights ngắn gọn (mỗi insight 1-2 câu) để giúp du khách có trải nghiệm tốt nhất."""
            
            response = self.llm.invoke(prompt)
            return response.content
            
        except Exception as e:
            print(f"   ⚠️  OpenAI enhancement error: {e}")
            return ""


# Global instance
rag_agent = None

def get_rag_agent() -> RAGAgent:
    """Get singleton RAG Agent"""
    global rag_agent
    if rag_agent is None:
        rag_agent = RAGAgent()
    return rag_agent


# Test
if __name__ == "__main__":
    print("="*60)
    print("RAG AGENT - TEST")
    print("="*60)
    
    agent = get_rag_agent()
    
    # Test recommendations
    results = agent.get_recommendations(
        destination="Hà Nội",
        budget=10000000,
        days=3,
        travelers=2,
        interests="văn hóa, ẩm thực"
    )
    
    print(f"\n📊 Results:")
    print(f"   Hotels: {len(results['recommendations']['hotels'])}")
    print(f"   Restaurants: {len(results['recommendations']['restaurants'])}")
    print(f"   Attractions: {len(results['recommendations']['attractions'])}")
    
    if results['recommendations']['hotels']:
        print(f"\n🏨 Top Hotel:")
        hotel = results['recommendations']['hotels'][0]
        print(f"   {hotel['name']} - {hotel['rating']}/5.0 - {hotel['price']:,} VND")
    
    print("\n" + "="*60)
    print("✅ Test completed!")

