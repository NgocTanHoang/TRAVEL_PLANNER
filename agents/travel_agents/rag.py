"""
RAG Agent - Retrieval Augmented Generation
===========================================
Kết hợp Vector DB + Tavily Search + OpenAI GPT-4
"""

import os
from typing import List, Dict, Any, Optional
from pathlib import Path
import sys
import logging

# Add parent to path
sys.path.append(str(Path(__file__).parent.parent))

from agents.travel_agents.vector_db import get_vector_db_agent
from ..base_agent import BaseAgent

logger = logging.getLogger(__name__)


class Doc:
    """Document structure for RAG results"""
    def __init__(self, content: str, metadata: Dict[str, Any], score: float = 0.0):
        self.content = content
        self.metadata = metadata
        self.score = score
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'content': self.content,
            'metadata': self.metadata,
            'score': self.score
        }


class RAGAgent(BaseAgent):
    """RAG Agent cho travel recommendations"""
    
    def __init__(self):
        """Initialize RAG Agent"""
        super().__init__(
            agent_name="rag_agent",
            description="Retrieval Augmented Generation agent"
        )
        # Vector Database
        self.vector_db = get_vector_db_agent()
        
        # OpenAI
        try:
            OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
            MODEL = os.getenv('MODEL', 'gpt-4o-mini')
            
            if OPENAI_API_KEY:
                from langchain_openai import ChatOpenAI
                self.llm = ChatOpenAI(
                    model=MODEL,
                    temperature=0.7,
                    api_key=OPENAI_API_KEY
                )
            else:
                self.llm = None
                logger.warning("OPENAI_API_KEY not found, LLM disabled")
            logger.info("RAG Agent initialized with OpenAI")
        except Exception as e:
            logger.warning(f"OpenAI initialization warning: {e}")
            self.llm = None
        
        # Tavily (optional)
        self.tavily_api_key = os.getenv('TAVILY_API_KEY')
        if self.tavily_api_key:
            try:
                from tavily import TavilyClient
                self.tavily = TavilyClient(api_key=self.tavily_api_key)
                logger.info("Tavily search enabled")
            except:
                self.tavily = None
                logger.warning("Tavily not available")
        else:
            self.tavily = None
    
    def retrieve(self, query: str, top_k: int = 6) -> List[Doc]:
        """
        Retrieve documents from vector database.
        
        Args:
            query: Search query
            top_k: Number of results to return
        
        Returns:
            List of Doc objects
        """
        try:
            self.log_input({'query': query, 'top_k': top_k})
            
            # Use cache if available
            try:
                from ..utils.cache import cache_get, cache_set
                cache_key = f"rag_retrieve:{hash(query)}:{top_k}"
                cached = cache_get(cache_key)
                if cached:
                    logger.info(f"Cache hit for query: {query[:50]}")
                    return [Doc(**doc) if isinstance(doc, dict) else doc for doc in cached]
            except ImportError:
                pass  # Cache not available
            
            # Query vector database với retry
            from ..utils.retry import retry_with_backoff, RetryConfig
            
            @retry_with_backoff(
                max_retries=RetryConfig.VECTOR_DB_RETRY['max_retries'],
                backoff_factor=RetryConfig.VECTOR_DB_RETRY['backoff_factor'],
                initial_delay=RetryConfig.VECTOR_DB_RETRY['initial_delay'],
                max_delay=RetryConfig.VECTOR_DB_RETRY['max_delay'],
                exceptions=(Exception,)
            )
            def _search_with_retry():
                return self.vector_db.semantic_search(query, n_results=top_k)
            
            try:
                results = _search_with_retry()
            except Exception as e:
                logger.warning(f"Vector DB search failed after retries: {e}, returning empty results")
                results = []
            
            # Convert to Doc objects
            docs = []
            for result in results:
                content = f"{result.get('name', '')} - {result.get('city', '')}\n"
                content += f"Rating: {result.get('rating', 0)}/5.0\n"
                content += f"Price: {result.get('price', 0):,} VND\n"
                content += f"{result.get('description', '')}"
                
                doc = Doc(
                    content=content,
                    metadata={
                        'name': result.get('name', ''),
                        'city': result.get('city', ''),
                        'category': result.get('category', ''),
                        'rating': result.get('rating', 0),
                        'price': result.get('price', 0),
                        'latitude': result.get('latitude'),
                        'longitude': result.get('longitude')
                    },
                    score=result.get('similarity_score', 0.0)
                )
                docs.append(doc)
            
            # Cache results (TTL: 6 hours)
            try:
                from ..utils.cache import cache_set
                cache_set(cache_key, [doc.to_dict() for doc in docs], ttl=21600)
            except ImportError:
                pass
            
            self.log_output({'doc_count': len(docs)})
            return docs
        
        except Exception as e:
            self.log_error(e, context={'query': query})
            return []
    
    @staticmethod
    def _should_retry_exception(e: Exception) -> bool:
        """Check if exception should trigger retry"""
        import requests
        retryable_exceptions = (
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
            requests.exceptions.HTTPError,
        )
        return isinstance(e, retryable_exceptions) or "rate limit" in str(e).lower()
    
    def answer(self, query: str, context_docs: List[Doc]) -> dict:
        """
        Generate answer using retrieved documents.
        
        Args:
            query: User query
            context_docs: List of Doc objects from retrieve()
        
        Returns:
            Dictionary with answer and metadata
        """
        try:
            self.log_input({'query': query, 'doc_count': len(context_docs)})
            
            # Prepare context
            context_text = "\n\n".join([
                f"[Document {i+1}]\n{doc.content}"
                for i, doc in enumerate(context_docs[:5])  # Limit to top 5
            ])
            
            # Generate answer with LLM
            if self.llm:
                prompt = f"""Bạn là trợ lý du lịch chuyên nghiệp cho Việt Nam.

Câu hỏi của người dùng: {query}

Thông tin từ database:
{context_text}

Hãy trả lời câu hỏi dựa trên thông tin trên. Nếu không có thông tin đủ, hãy nói rõ.
Hãy trả lời bằng tiếng Việt, thân thiện và chi tiết."""

                response = self.llm.invoke(prompt)
                answer = response.content if hasattr(response, 'content') else str(response)
            else:
                # Fallback answer
                answer = f"Dựa trên {len(context_docs)} kết quả tìm kiếm, tôi có thể giúp bạn với: {query}. "
                if context_docs:
                    answer += f"Tìm thấy {len(context_docs)} địa điểm liên quan."
                else:
                    answer += "Không tìm thấy thông tin liên quan."
            
            result = {
                'answer': answer,
                'sources': [doc.to_dict() for doc in context_docs],
                'source_count': len(context_docs),
                'query': query
            }
            
            self.log_output(result)
            return result
        
        except Exception as e:
            self.log_error(e, context={'query': query})
            return {
                'answer': 'Xin lỗi, tôi gặp lỗi khi tạo câu trả lời.',
                'error': str(e),
                'sources': [],
                'source_count': 0
            }
    
    def retrieve_and_answer(self, payload: dict) -> dict:
        """
        Combined retrieve and answer for interactive workflow.
        
        Args:
            payload: Dictionary với:
                - query: User query
                - top_k: Number of documents (default: 6)
        
        Returns:
            Result dictionary compatible with interactive_workflow
        """
        query = payload.get('query', '')
        top_k = payload.get('top_k', 6)
        
        docs = self.retrieve(query, top_k=top_k)
        answer_result = self.answer(query, docs)
        
        return {
            'status': 'ok',
            'result': answer_result,
            'sources': answer_result.get('sources', [])
        }
    
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
            
            # LLM invoke với retry
            from ..utils.retry import retry_with_backoff, RetryConfig
            
            @retry_with_backoff(
                max_retries=RetryConfig.LLM_RETRY['max_retries'],
                backoff_factor=RetryConfig.LLM_RETRY['backoff_factor'],
                initial_delay=RetryConfig.LLM_RETRY['initial_delay'],
                max_delay=RetryConfig.LLM_RETRY['max_delay'],
                exceptions=(Exception,)
            )
            def _invoke_with_retry():
                response = self.llm.invoke(prompt)
                return response.content if hasattr(response, 'content') else str(response)
            
            try:
                return _invoke_with_retry()
            except Exception as e:
                logger.warning(f"LLM enhance failed after retries: {e}")
                return "Không thể tạo insights từ AI."
            
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

