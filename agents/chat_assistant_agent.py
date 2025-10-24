"""
Travel Assistant Chat Agent
============================
A conversational AI assistant for travel planning using multi-agent system

Features:
- Natural language conversation
- Context-aware responses
- Multi-agent coordination
- Travel recommendations
- Budget planning
- Itinerary suggestions
"""

import os
import sys
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


class TravelChatAssistant:
    """Intelligent Travel Assistant using Multi-Agent System"""
    
    def __init__(self):
        """Initialize the chat assistant"""
        self.conversation_history = []
        self.user_context = {}
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Initialize LLM
        try:
            from config.settings import OPENAI_API_KEY, MODEL
            from langchain_openai import ChatOpenAI
            
            self.llm = ChatOpenAI(
                model=MODEL,
                temperature=0.7,  # More creative for chat
                api_key=OPENAI_API_KEY
            )
            print("✅ OpenAI LLM initialized")
        except Exception as e:
            print(f"⚠️  LLM initialization warning: {e}")
            self.llm = None
        
        # Initialize Vector DB for RAG
        try:
            from agents.vector_db_agent import get_vector_db_agent
            self.vector_db = get_vector_db_agent()
            print("✅ Vector DB connected for RAG")
        except Exception as e:
            print(f"⚠️  Vector DB warning: {e}")
            self.vector_db = None
        
        # System prompt
        self.system_prompt = """You are an expert Travel Assistant for Vietnam tourism.

Your capabilities:
- Recommend destinations, hotels, restaurants, attractions
- Create customized itineraries
- Provide budget estimates
- Share local tips and cultural insights
- Answer travel-related questions
- Provide weather forecasts and packing recommendations

Guidelines:
1. Be friendly, helpful, and enthusiastic
2. Ask clarifying questions when needed
3. Provide specific, actionable recommendations
4. Consider budget, time, and preferences
5. Use data from 50,000+ real Vietnamese places
6. Give both popular and hidden gem suggestions
7. Include practical information (prices, locations, tips)
8. ALWAYS include weather info và gợi ý đồ mang theo khi nói về địa điểm

Your responses should be:
- Conversational and natural
- Informative and detailed
- Personalized to user needs
- Actionable with clear next steps

Available Vietnamese destinations:
- Hanoi, Ho Chi Minh City, Da Nang, Hoi An
- Nha Trang, Phu Quoc, Hue, Sapa
- Dalat, Can Tho, Halong Bay, Mui Ne
- And 40+ more cities

Start with a warm greeting and ask how you can help!"""
        
        # Initialize conversation with system message
        self.conversation_history.append(
            SystemMessage(content=self.system_prompt)
        )
    
    def _get_rag_context(self, user_message: str) -> str:
        """
        Get context from Vector DB for RAG + Weather info
        
        Args:
            user_message: User query
            
        Returns:
            Context string with real data and weather
        """
        if not self.vector_db:
            return ""
        
        try:
            # Detect if asking about specific place types
            message_lower = user_message.lower()
            context_parts = []
            
            # Search Vector DB
            results = self.vector_db.semantic_search(
                query=user_message,
                n_results=5
            )
            
            if results:
                context_parts.append("\n📊 THÔNG TIN THỰC TỪ DATABASE (50K+ địa điểm):\n")
                for i, place in enumerate(results, 1):
                    context_parts.append(
                        f"{i}. **{place['name']}** - {place['city']}\n"
                        f"   ⭐ Rating: {place['rating']}/5.0\n"
                        f"   💰 Giá: {place['price']:,} VND\n"
                        f"   📍 Vị trí: {place['city']}\n"
                        f"   📝 {place.get('description', '')[:100]}...\n"
                    )
                
                # Add weather info for the city
                if results:
                    city = results[0]['city']
                    try:
                        from utils.weather_helper import get_weather_recommendations
                        weather_info = get_weather_recommendations(city)
                        context_parts.append(f"\n{weather_info}\n")
                    except Exception as e:
                        print(f"⚠️  Weather info error: {e}")
            
            return "".join(context_parts) if context_parts else ""
            
        except Exception as e:
            print(f"⚠️  RAG context error: {e}")
            return ""
    
    def chat(self, user_message: str) -> str:
        """
        Process user message and return assistant response
        
        Args:
            user_message: User's input message
            
        Returns:
            Assistant's response
        """
        try:
            # Get RAG context from Vector DB
            rag_context = self._get_rag_context(user_message)
            
            # Build enhanced message with RAG context
            if rag_context:
                enhanced_message = f"""{user_message}

{rag_context}

Hãy sử dụng thông tin THỰC từ database ở trên để trả lời. Đừng tự nghĩ ra tên khách sạn, hãy dùng đúng tên từ database."""
            else:
                enhanced_message = user_message
            
            # Add user message to history
            self.conversation_history.append(
                HumanMessage(content=enhanced_message)
            )
            
            # Extract intent and context
            self._update_context(user_message)
            
            # Generate response
            if self.llm:
                response = self.llm.invoke(self.conversation_history)
                assistant_message = response.content
            else:
                assistant_message = self._fallback_response(user_message)
            
            # Add assistant response to history
            self.conversation_history.append(
                AIMessage(content=assistant_message)
            )
            
            return assistant_message
            
        except Exception as e:
            error_msg = f"Xin lỗi, tôi gặp lỗi: {str(e)}. Vui lòng thử lại!"
            self.conversation_history.append(AIMessage(content=error_msg))
            return error_msg
    
    def _update_context(self, message: str):
        """Extract and update user context from message"""
        message_lower = message.lower()
        
        # Extract destination
        cities = [
            "hanoi", "ho chi minh", "saigon", "da nang", "hoi an",
            "nha trang", "phu quoc", "hue", "sapa", "dalat",
            "can tho", "halong", "mui ne", "vung tau"
        ]
        for city in cities:
            if city in message_lower:
                self.user_context['destination'] = city.title()
                break
        
        # Extract budget (numbers in VND or USD)
        import re
        budget_match = re.search(r'(\d+(?:,\d+)*)\s*(?:vnd|dong|million|triệu)', message_lower)
        if budget_match:
            budget_str = budget_match.group(1).replace(',', '')
            self.user_context['budget'] = int(budget_str)
        
        # Extract duration
        days_match = re.search(r'(\d+)\s*(?:day|days|ngày)', message_lower)
        if days_match:
            self.user_context['days'] = int(days_match.group(1))
        
        # Extract interests
        interests = []
        interest_keywords = {
            'food': ['food', 'eat', 'restaurant', 'cuisine', 'ăn', 'món'],
            'history': ['history', 'historical', 'museum', 'temple', 'lịch sử'],
            'nature': ['nature', 'beach', 'mountain', 'hiking', 'thiên nhiên', 'biển'],
            'culture': ['culture', 'traditional', 'local', 'văn hóa'],
            'shopping': ['shopping', 'market', 'mall', 'mua sắm'],
            'nightlife': ['nightlife', 'bar', 'club', 'party', 'đêm']
        }
        
        for category, keywords in interest_keywords.items():
            if any(kw in message_lower for kw in keywords):
                interests.append(category)
        
        if interests:
            self.user_context['interests'] = interests
    
    def _fallback_response(self, user_message: str) -> str:
        """Fallback response when LLM is not available"""
        responses = {
            'greeting': "Hello! I'm your Vietnam Travel Assistant. I can help you plan trips, recommend places, and answer travel questions. How can I help you today?",
            'destination': "I can help you explore amazing destinations in Vietnam! Some popular choices are Hanoi, Ho Chi Minh City, Da Nang, Hoi An, Nha Trang, and Phu Quoc. Which one interests you?",
            'budget': "I can help you plan trips for various budgets. Could you tell me your budget and how many days you'd like to travel?",
            'recommendation': "I have information on 50,000+ places in Vietnam including hotels, restaurants, and attractions. What type of recommendations are you looking for?"
        }
        
        message_lower = user_message.lower()
        
        if any(word in message_lower for word in ['hello', 'hi', 'hey', 'xin chào']):
            return responses['greeting']
        elif any(word in message_lower for word in ['where', 'destination', 'visit', 'đi đâu']):
            return responses['destination']
        elif any(word in message_lower for word in ['budget', 'cost', 'price', 'chi phí']):
            return responses['budget']
        elif any(word in message_lower for word in ['recommend', 'suggest', 'hotel', 'restaurant']):
            return responses['recommendation']
        else:
            return "I'm here to help with your Vietnam travel plans! You can ask me about destinations, hotels, restaurants, itineraries, or any travel-related questions."
    
    def get_recommendations(self, category: str = "all") -> Dict[str, Any]:
        """
        Get recommendations based on current context
        
        Args:
            category: Type of recommendations (hotels, restaurants, attractions, all)
            
        Returns:
            Dictionary with recommendations
        """
        try:
            from data_collection.real_data_provider import RealDataProvider
            
            provider = RealDataProvider()
            destination = self.user_context.get('destination', 'Hanoi')
            
            if category == "all":
                places = provider.get_places_data(destination, limit=5)
            else:
                places = {category: provider.get_places_data(destination, limit=5).get(category, [])}
            
            return {
                'destination': destination,
                'recommendations': places,
                'context': self.user_context
            }
            
        except Exception as e:
            return {
                'error': str(e),
                'message': 'Unable to fetch recommendations at the moment'
            }
    
    def create_itinerary(self) -> str:
        """Create an itinerary based on conversation context"""
        destination = self.user_context.get('destination', 'Hanoi')
        days = self.user_context.get('days', 3)
        budget = self.user_context.get('budget', 10000000)
        interests = self.user_context.get('interests', ['food', 'culture'])
        
        try:
            # Use the multi-agent workflow
            from multi_agent_system.langgraph_workflow import run_travel_workflow
            
            result = run_travel_workflow(
                destination=destination,
                budget=budget,
                days=days,
                travelers=1
            )
            
            # Format the itinerary nicely
            if 'travel_plan' in result:
                plan = result['travel_plan']
                itinerary_text = f"Here's your {days}-day itinerary for {destination}:\n\n"
                
                for day, activities in plan.get('itinerary', {}).items():
                    itinerary_text += f"\n**{day}:**\n"
                    for time, activity in activities.items():
                        itinerary_text += f"- {time.title()}: {activity}\n"
                
                return itinerary_text
            else:
                return "I can help you create a custom itinerary! Please provide your destination, budget, and number of days."
                
        except Exception as e:
            return f"I'd love to help create an itinerary! Based on our conversation, I suggest a {days}-day trip to {destination} focusing on {', '.join(interests)}. Would you like me to provide more details?"
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get summary of current conversation"""
        return {
            'session_id': self.session_id,
            'messages_count': len(self.conversation_history),
            'user_context': self.user_context,
            'timestamp': datetime.now().isoformat()
        }
    
    def reset_conversation(self):
        """Reset conversation history but keep system prompt"""
        self.conversation_history = [
            SystemMessage(content=self.system_prompt)
        ]
        self.user_context = {}
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        print("✅ Conversation reset")
    
    def save_conversation(self, filename: Optional[str] = None):
        """Save conversation to file"""
        if not filename:
            filename = f"chat_history_{self.session_id}.json"
        
        try:
            conversation_data = {
                'session_id': self.session_id,
                'context': self.user_context,
                'messages': [
                    {
                        'role': 'user' if isinstance(msg, HumanMessage) else 'assistant',
                        'content': msg.content,
                        'timestamp': datetime.now().isoformat()
                    }
                    for msg in self.conversation_history
                    if not isinstance(msg, SystemMessage)
                ]
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(conversation_data, f, ensure_ascii=False, indent=2)
            
            print(f"💾 Conversation saved to {filename}")
            return filename
            
        except Exception as e:
            print(f"❌ Error saving conversation: {e}")
            return None


# Create global instance
chat_assistant = TravelChatAssistant()


# Quick test
if __name__ == "__main__":
    print("="*60)
    print("TRAVEL ASSISTANT CHAT - TEST")
    print("="*60)
    
    assistant = TravelChatAssistant()
    
    # Test conversation
    test_messages = [
        "Hello! I want to visit Vietnam",
        "I'm interested in Hanoi for 5 days with a budget of 50 million VND",
        "What are the best places to eat?",
        "Can you create an itinerary for me?"
    ]
    
    for msg in test_messages:
        print(f"\n👤 User: {msg}")
        response = assistant.chat(msg)
        print(f"🤖 Assistant: {response}")
    
    # Show context
    print(f"\n📊 Context: {assistant.user_context}")
    
    print("\n" + "="*60)
    print("✅ Test completed!")


