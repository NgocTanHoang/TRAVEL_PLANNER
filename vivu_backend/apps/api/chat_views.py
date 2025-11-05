"""
Chat API Views with RAG Integration & Travel Chatbot
=====================================================
Sử dụng RAG Agent với Vector Database và Travel Chatbot với LLM
"""

import os
import sys
from pathlib import Path
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from django.core.cache import cache
import logging

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

logger = logging.getLogger(__name__)


class ChatView(APIView):
    """
    RAG Chat API với Travel Chatbot - Sử dụng Vector Database và LLM để trả lời câu hỏi
    
    POST /api/v1/chat/
    {
        "message": "Khách sạn nào tốt ở Hà Nội?",
        "destination": "Hà Nội",  # Optional
        "conversation_id": "optional-conversation-id",
        "use_chatbot": true  # Sử dụng Travel Chatbot (default: true)
    }
    """
    permission_classes = [AllowAny]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rag_agent = None
        self.travel_chatbot = None
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Khởi tạo RAG Agent và Travel Chatbot"""
        # Initialize RAG Agent
        try:
            from agents.travel_agents.rag import RAGAgent
            self.rag_agent = RAGAgent()
            logger.info("RAG Agent initialized successfully")
        except Exception as e:
            logger.warning(f"RAG Agent initialization failed: {e}")
            self.rag_agent = None
        
        # Initialize Travel Chatbot
        try:
            from ml.travel_chatbot import get_travel_chatbot
            self.travel_chatbot = get_travel_chatbot(llm_provider='openai')
            logger.info("Travel Chatbot initialized successfully")
        except Exception as e:
            logger.warning(f"Travel Chatbot initialization failed: {e}")
            self.travel_chatbot = None
    
    def post(self, request):
        """Xử lý câu hỏi từ user"""
        try:
            message = request.data.get('message', '').strip()
            destination = request.data.get('destination')
            conversation_id = request.data.get('conversation_id')
            use_chatbot = request.data.get('use_chatbot', True)
            
            if not message:
                return Response({
                    'error': 'Tin nhắn không được để trống'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Rate limiting
            user_id = request.user.id if request.user.is_authenticated else 0
            cache_key = f"chat_rate_limit:user_{user_id}"
            count = cache.get(cache_key, 0)
            if count >= 30:  # Max 30 requests per minute
                return Response({
                    'error': 'Quá nhiều yêu cầu. Vui lòng thử lại sau.'
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)
            cache.set(cache_key, count + 1, 60)
            
            # Ưu tiên sử dụng Travel Chatbot với LLM
            if use_chatbot and self.travel_chatbot:
                try:
                    chatbot_response = self.travel_chatbot.chat(
                        user_message=message,
                        use_rag=True,
                        destination=destination
                    )
                    
                    if 'error' not in chatbot_response:
                        return Response({
                            'status': 'success',
                            'message': chatbot_response.get('response', ''),
                            'context_used': chatbot_response.get('context_used', False),
                            'destination': chatbot_response.get('destination'),
                            'source': 'travel_chatbot',
                            'conversation_id': conversation_id
                        }, status=status.HTTP_200_OK)
                except Exception as e:
                    logger.error(f"Error in Travel Chatbot: {e}", exc_info=True)
                    # Fallback to RAG Agent
            
            # Fallback: Sử dụng RAG Agent nếu có
            if self.rag_agent:
                try:
                    # Retrieve relevant documents từ vector database
                    docs = self.rag_agent.retrieve(message, top_k=5)
                    
                    # Generate response với context từ vector DB
                    response_text = self.rag_agent.generate(
                        query=message,
                        context_docs=docs,
                        conversation_history=[]
                    )
                    
                    # Format response
                    response_data = {
                        'status': 'success',
                        'message': response_text,
                        'sources': [
                            {
                                'name': doc.metadata.get('name', ''),
                                'city': doc.metadata.get('city', ''),
                                'category': doc.metadata.get('category', ''),
                                'score': doc.score
                            }
                            for doc in docs[:3]  # Top 3 sources
                        ],
                        'source': 'rag_agent',
                        'conversation_id': conversation_id
                    }
                    
                    return Response(response_data, status=status.HTTP_200_OK)
                    
                except Exception as e:
                    logger.error(f"Error in RAG chat: {e}", exc_info=True)
                    # Fallback to simple response
                    response_text = self._fallback_response(message)
            else:
                # Fallback nếu không có agent nào
                response_text = self._fallback_response(message)
            
            return Response({
                'status': 'success',
                'message': response_text,
                'sources': [],
                'source': 'fallback',
                'conversation_id': conversation_id,
                'note': 'Vector database hoặc LLM chưa được khởi tạo. Vui lòng kiểm tra API keys.'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error in chat API: {e}", exc_info=True)
            return Response({
                'error': 'Có lỗi xảy ra khi xử lý tin nhắn'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _fallback_response(self, message: str) -> str:
        """Fallback response khi không có agent nào"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['khách sạn', 'hotel', 'nghỉ']):
            return "Tôi có thể giúp bạn tìm khách sạn phù hợp. Bạn muốn đi đâu và ngân sách như thế nào?"
        elif any(word in message_lower for word in ['nhà hàng', 'restaurant', 'ăn', 'ẩm thực']):
            return "Tôi có thể giúp bạn tìm nhà hàng ngon. Bạn muốn ăn ở đâu và loại món ăn nào?"
        elif any(word in message_lower for word in ['địa điểm', 'thăm quan', 'du lịch']):
            return "Tôi có thể giúp bạn tìm địa điểm du lịch thú vị. Bạn muốn đi đâu?"
        elif any(word in message_lower for word in ['lịch trình', 'kế hoạch', 'plan']):
            return "Tôi có thể giúp bạn tạo lịch trình du lịch. Hãy thử tính năng 'Tạo lịch trình' trên trang chủ!"
        else:
            return "Xin chào! Tôi là AI Assistant của Vi Vu. Tôi có thể giúp bạn tìm địa điểm, khách sạn, nhà hàng và tạo lịch trình du lịch. Bạn cần hỗ trợ gì?"


class ItineraryChatView(APIView):
    """
    Chat API để tạo lịch trình du lịch
    
    POST /api/v1/chat/itinerary/
    {
        "destination": "Hà Nội",
        "days": 3,
        "travelers": 2,
        "travel_style": "standard",
        "interests": ["văn hóa", "ẩm thực"]
    }
    """
    permission_classes = [AllowAny]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.travel_chatbot = None
        self._initialize_chatbot()
    
    def _initialize_chatbot(self):
        """Khởi tạo Travel Chatbot"""
        try:
            from ml.travel_chatbot import get_travel_chatbot
            self.travel_chatbot = get_travel_chatbot(llm_provider='openai')
            logger.info("Travel Chatbot initialized for itinerary generation")
        except Exception as e:
            logger.warning(f"Travel Chatbot initialization failed: {e}")
            self.travel_chatbot = None
    
    def post(self, request):
        """Generate itinerary using chatbot"""
        try:
            destination = request.data.get('destination')
            days = int(request.data.get('days', 3))
            travelers = int(request.data.get('travelers', 2))
            travel_style = request.data.get('travel_style', 'standard')
            interests = request.data.get('interests', [])
            
            if not destination:
                return Response({
                    'error': 'Điểm đến không được để trống'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not self.travel_chatbot:
                return Response({
                    'error': 'Chatbot chưa được khởi tạo. Vui lòng kiểm tra API keys.'
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
            # Generate itinerary
            result = self.travel_chatbot.suggest_itinerary(
                destination=destination,
                days=days,
                travelers=travelers,
                travel_style=travel_style,
                interests=interests
            )
            
            if 'error' in result:
                return Response({
                    'error': result['error']
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            return Response({
                'status': 'success',
                'itinerary': result.get('itinerary', ''),
                'destination': destination,
                'days': days,
                'travelers': travelers,
                'travel_style': travel_style
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error generating itinerary: {e}", exc_info=True)
            return Response({
                'error': 'Có lỗi xảy ra khi tạo lịch trình'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)