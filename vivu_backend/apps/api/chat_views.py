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
from django.db.models import Q
import logging

# Add backend directory to path for agents, tools, ml, etc.
# BASE_DIR (vivu_backend) is already added in settings.py, but adding here for safety
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

# Django imports
from apps.places.models import DiaDiem, TinhThanh

logger = logging.getLogger(__name__)

CHAT_HISTORY_TTL_SECONDS = 60 * 60 * 6
CHAT_HISTORY_MAX_MESSAGES = 20


def _conversation_cache_key(conversation_id: str) -> str:
    return f"travel_chat:conversation:{conversation_id}"


def _load_conversation_history(conversation_id: str) -> list:
    if not conversation_id:
        return []
    return cache.get(_conversation_cache_key(conversation_id), [])


def _save_conversation_history(conversation_id: str, history: list) -> None:
    if not conversation_id:
        return
    cache.set(_conversation_cache_key(conversation_id), history[-CHAT_HISTORY_MAX_MESSAGES:], CHAT_HISTORY_TTL_SECONDS)


def _record_conversation_turn(conversation_id: str, role: str, content: str) -> list:
    history = _load_conversation_history(conversation_id)
    history.append({'role': role, 'content': content})
    _save_conversation_history(conversation_id, history)
    return history


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
    
    def _search_places_from_db(self, query: str, destination: str = None, limit: int = 10) -> list:
        """Tìm kiếm địa điểm từ database"""
        try:
            places_query = DiaDiem.objects.filter(trangThai='active').select_related('maTinhThanh')
            
            # Filter by destination if provided
            if destination:
                places_query = places_query.filter(
                    Q(maTinhThanh__tenTinhThanh__icontains=destination) |
                    Q(diaChi__icontains=destination)
                )
            
            # Search by query
            if query:
                places_query = places_query.filter(
                    Q(tenDiaDiem__icontains=query) |
                    Q(moTa__icontains=query) |
                    Q(diaChi__icontains=query)
                )
            
            places = places_query.order_by('-danhGiaTrungBinh', '-soLuotDanhGia')[:limit]
            
            results = []
            for place in places:
                results.append({
                    'name': place.tenDiaDiem,
                    'description': place.moTa or '',
                    'address': place.diaChi or '',
                    'city': place.maTinhThanh.tenTinhThanh if place.maTinhThanh else '',
                    'category': place.loaiDiaDiem,
                    'rating': float(place.danhGiaTrungBinh) if place.danhGiaTrungBinh else 0,
                    'price': place.giaVe or 0
                })
            
            return results
        except Exception as e:
            logger.error(f"Error searching places from DB: {e}", exc_info=True)
            return []
    
    def _get_context_from_multiple_sources(self, message: str, destination: str = None) -> str:
        """Lấy context từ nhiều nguồn: Database, Vector DB, Web search"""
        context_parts = []
        
        # 1. Search từ Database
        try:
            db_places = self._search_places_from_db(message, destination, limit=5)
            if db_places:
                context_parts.append("=== Địa điểm từ Database ===")
                for place in db_places:
                    context_parts.append(
                        f"- {place['name']} ({place['city']}, {place['category']}): "
                        f"{place['description'][:150] if place['description'] else 'Không có mô tả'}. "
                        f"Đánh giá: {place['rating']}/5"
                    )
        except Exception as e:
            logger.error(f"Error getting DB context: {e}")
        
        # 2. Search từ Vector DB (semantic search)
        try:
            if self.rag_agent and hasattr(self.rag_agent, 'vector_db') and self.rag_agent.vector_db:
                vector_results = self.rag_agent.vector_db.semantic_search(
                    query=message,
                    n_results=5,
                    city_filter=destination
                )
                if vector_results:
                    context_parts.append("\n=== Địa điểm từ Vector DB (Semantic Search) ===")
                    for place in vector_results[:5]:
                        name = place.get('name', '')
                        desc = place.get('description', '')
                        city = place.get('city', '')
                        if name:
                            context_parts.append(f"- {name} ({city}): {desc[:150] if desc else 'Không có mô tả'}")
        except Exception as e:
            logger.error(f"Error getting Vector DB context: {e}")
        
        # 3. Search từ Travel Chatbot Vector DB nếu có
        try:
            if self.travel_chatbot and self.travel_chatbot.vector_db:
                vector_context = self.travel_chatbot._get_context_from_vector_db(
                    f"{message} {destination}" if destination else message,
                    n_results=5
                )
                if vector_context:
                    context_parts.append("\n=== Thông tin bổ sung ===")
                    context_parts.append(vector_context)
        except Exception as e:
            logger.error(f"Error getting Travel Chatbot context: {e}")
        
        return "\n".join(context_parts)
    
    def post(self, request):
        """Xử lý câu hỏi từ user với workflow tìm kiếm thông tin"""
        try:
            message = request.data.get('message', '').strip()
            destination = request.data.get('destination')
            conversation_id = (request.data.get('conversation_id') or '').strip()
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
            conversation_history = _load_conversation_history(conversation_id)
            recent_history = conversation_history[-10:]
            
            # Bước 1: Tìm kiếm thông tin từ nhiều nguồn
            logger.info(f"Searching information for query: {message}, destination: {destination}")
            context = self._get_context_from_multiple_sources(message, destination)
            
            # Bước 2: Sử dụng Travel Chatbot với context đã tìm được
            if use_chatbot and self.travel_chatbot and self.travel_chatbot.llm:
                try:
                    # Tạo enhanced message với context
                    enhanced_message = message
                    if context:
                        enhanced_message = f"{message}\n\nThông tin tìm được:\n{context}"
                    
                    if recent_history:
                        history_prompt = "\n".join(
                            f"{item.get('role', 'user')}: {item.get('content', '')}"
                            for item in recent_history
                        )
                        enhanced_message = (
                            f"Lá»‹ch sá»­ há»™i thoáº¡i gáº§n Ä‘Ã¢y:\n{history_prompt}\n\n"
                            f"CÃ¢u há»i má»›i: {enhanced_message}"
                        )

                    chatbot_response = self.travel_chatbot.chat(
                        user_message=enhanced_message,
                        use_rag=False,  # Đã có context rồi, không cần RAG nữa
                        destination=destination
                    )
                    
                    if 'error' not in chatbot_response:
                        # Lấy sources từ database search
                        db_places = self._search_places_from_db(message, destination, limit=3)
                        sources = [
                            {
                                'name': place['name'],
                                'city': place['city'],
                                'category': place['category']
                            }
                            for place in db_places
                        ]
                        _record_conversation_turn(conversation_id, 'user', message)
                        updated_history = _record_conversation_turn(
                            conversation_id,
                            'assistant',
                            chatbot_response.get('response', ''),
                        )
                        
                        return Response({
                            'status': 'success',
                            'message': chatbot_response.get('response', ''),
                            'context_used': bool(context),
                            'destination': destination or chatbot_response.get('destination'),
                            'sources': sources,
                            'source': 'travel_chatbot_with_search',
                            'conversation_id': conversation_id,
                            'conversation_turns': len(updated_history)
                        }, status=status.HTTP_200_OK)
                except Exception as e:
                    logger.error(f"Error in Travel Chatbot with search: {e}", exc_info=True)
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
                    _record_conversation_turn(conversation_id, 'user', message)
                    updated_history = _record_conversation_turn(conversation_id, 'assistant', response_text)
                    response_data['conversation_turns'] = len(updated_history)
                    
                    return Response(response_data, status=status.HTTP_200_OK)
                    
                except Exception as e:
                    logger.error(f"Error in RAG chat: {e}", exc_info=True)
            
            # Final fallback: Sử dụng database search và format response
            db_places = self._search_places_from_db(message, destination, limit=5)
            if db_places:
                response_text = self._format_response_from_places(message, db_places)
                sources = [
                    {
                        'name': place['name'],
                        'city': place['city'],
                        'category': place['category']
                    }
                    for place in db_places[:3]
                ]
                _record_conversation_turn(conversation_id, 'user', message)
                return Response({
                    'status': 'success',
                    'message': response_text,
                    'sources': sources,
                    'source': 'database_search',
                    'conversation_id': conversation_id,
                    'conversation_turns': len(
                        _record_conversation_turn(
                            conversation_id,
                            'assistant',
                            response_text,
                        )
                    )
                }, status=status.HTTP_200_OK)
            
            # Ultimate fallback
            fallback_message = self._fallback_response(message)
            _record_conversation_turn(conversation_id, 'user', message)
            updated_history = _record_conversation_turn(conversation_id, 'assistant', fallback_message)
            return Response({
                'status': 'success',
                'message': fallback_message,
                'sources': [],
                'source': 'fallback',
                'conversation_id': conversation_id,
                'conversation_turns': len(updated_history),
                'note': 'Không tìm thấy thông tin. Vui lòng kiểm tra API keys hoặc thử lại với câu hỏi khác.'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error in chat API: {e}", exc_info=True)
            return Response({
                'error': 'Có lỗi xảy ra khi xử lý tin nhắn'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _format_response_from_places(self, query: str, places: list) -> str:
        """Format response từ danh sách địa điểm tìm được"""
        if not places:
            return self._fallback_response(query)
        
        message_lower = query.lower()
        
        # Phân loại câu hỏi
        if any(word in message_lower for word in ['địa điểm', 'thăm quan', 'du lịch', 'đâu đẹp', 'nơi nào']):
            response = f"Dựa trên thông tin từ database, đây là các địa điểm phù hợp:\n\n"
            for i, place in enumerate(places[:5], 1):
                response += f"{i}. **{place['name']}** ({place['city']})\n"
                if place['description']:
                    response += f"   {place['description'][:200]}...\n"
                if place['rating'] > 0:
                    response += f"   ⭐ Đánh giá: {place['rating']}/5\n"
                response += "\n"
            return response
        
        elif any(word in message_lower for word in ['khách sạn', 'hotel', 'nghỉ']):
            hotels = [p for p in places if p['category'] == 'khach_san']
            if hotels:
                response = f"Tìm thấy {len(hotels)} khách sạn phù hợp:\n\n"
                for i, hotel in enumerate(hotels[:5], 1):
                    response += f"{i}. **{hotel['name']}** ({hotel['city']})\n"
                    if hotel['address']:
                        response += f"   📍 {hotel['address']}\n"
                    if hotel['rating'] > 0:
                        response += f"   ⭐ {hotel['rating']}/5\n"
                    response += "\n"
                return response
        
        elif any(word in message_lower for word in ['nhà hàng', 'restaurant', 'ăn', 'ẩm thực']):
            restaurants = [p for p in places if p['category'] == 'nha_hang']
            if restaurants:
                response = f"Tìm thấy {len(restaurants)} nhà hàng:\n\n"
                for i, restaurant in enumerate(restaurants[:5], 1):
                    response += f"{i}. **{restaurant['name']}** ({restaurant['city']})\n"
                    if restaurant['address']:
                        response += f"   📍 {restaurant['address']}\n"
                    if restaurant['rating'] > 0:
                        response += f"   ⭐ {restaurant['rating']}/5\n"
                    response += "\n"
                return response
        
        # Default response
        response = f"Tìm thấy {len(places)} địa điểm liên quan:\n\n"
        for i, place in enumerate(places[:5], 1):
            response += f"{i}. **{place['name']}** - {place['city']}\n"
        return response
    
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
