"""
Travel Chatbot - Tư vấn du lịch thông minh
===========================================
Sử dụng LangChain + LLM để hỏi-đáp về điểm đến và gợi ý hành trình
"""

import os
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

# LangChain imports
try:
    from langchain_openai import ChatOpenAI
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
    from langchain.chains import LLMChain
    from langchain.memory import ConversationBufferMemory
    from langchain.schema import HumanMessage, AIMessage
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    logger.warning("LangChain not available, chatbot will be disabled")

# Optional: LLaMA support
try:
    from langchain_community.llms import LlamaCpp
    LLAMA_AVAILABLE = True
except ImportError:
    LLAMA_AVAILABLE = False


class TravelChatbot:
    """
    Chatbot tư vấn du lịch sử dụng LLM
    """
    
    def __init__(
        self,
        llm_provider: str = 'openai',
        model_name: Optional[str] = None,
        temperature: float = 0.7
    ):
        """
        Args:
            llm_provider: 'openai', 'gemini', hoặc 'llama'
            model_name: Tên model cụ thể
            temperature: Temperature cho LLM
        """
        self.llm_provider = llm_provider
        self.temperature = temperature
        self.llm = None
        self.memory = None
        self.vector_db = None
        
        # Initialize LLM
        self._initialize_llm(model_name)
        
        # Initialize memory
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # Initialize Vector DB for RAG
        try:
            from agents.travel_agents.vector_db import get_vector_db_agent
            self.vector_db = get_vector_db_agent()
        except Exception as e:
            logger.warning(f"Vector DB not available: {e}")
    
    def _initialize_llm(self, model_name: Optional[str]):
        """Initialize LLM based on provider"""
        if not LANGCHAIN_AVAILABLE:
            logger.error("LangChain not available")
            return
        
        if self.llm_provider == 'openai':
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                logger.error("OPENAI_API_KEY not found")
                return
            
            model = model_name or os.getenv('MODEL', 'gpt-4o-mini')
            self.llm = ChatOpenAI(
                model=model,
                temperature=self.temperature,
                api_key=api_key
            )
            logger.info(f"Initialized OpenAI LLM: {model}")
        
        elif self.llm_provider == 'gemini':
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                logger.error("GEMINI_API_KEY not found")
                return
            
            model = model_name or 'gemini-pro'
            self.llm = ChatGoogleGenerativeAI(
                model=model,
                temperature=self.temperature,
                google_api_key=api_key
            )
            logger.info(f"Initialized Gemini LLM: {model}")
        
        elif self.llm_provider == 'llama':
            if not LLAMA_AVAILABLE:
                logger.error("LlamaCpp not available")
                return
            
            # Cần đường dẫn đến model file
            model_path = model_name or os.getenv('LLAMA_MODEL_PATH')
            if not model_path:
                logger.error("LLAMA_MODEL_PATH not found")
                return
            
            self.llm = LlamaCpp(
                model_path=model_path,
                temperature=self.temperature,
                n_ctx=2048
            )
            logger.info(f"Initialized LLaMA LLM: {model_path}")
    
    def _get_context_from_vector_db(self, query: str, n_results: int = 5) -> str:
        """Lấy context từ Vector DB để làm RAG"""
        if not self.vector_db or not self.vector_db.collection:
            return ""
        
        try:
            results = self.vector_db.semantic_search(
                query=query,
                n_results=n_results
            )
            
            if not results:
                return ""
            
            # Format context
            context_parts = []
            for i, place in enumerate(results, 1):
                name = place.get('name', '')
                description = place.get('description', '')
                city = place.get('city', '')
                category = place.get('category', '')
                
                context_parts.append(
                    f"{i}. {name} ({city}, {category}): {description[:200]}"
                )
            
            return "\n".join(context_parts)
        
        except Exception as e:
            logger.error(f"Error getting context from Vector DB: {e}")
            return ""
    
    def chat(
        self,
        user_message: str,
        use_rag: bool = True,
        destination: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Chat với chatbot
        
        Args:
            user_message: Câu hỏi của user
            use_rag: Sử dụng RAG để lấy context từ Vector DB
            destination: Điểm đến (optional, để filter context)
        
        Returns:
            Dict với response và metadata
        """
        if not self.llm:
            return {
                'response': 'Xin lỗi, chatbot chưa được khởi tạo. Vui lòng kiểm tra API keys.',
                'error': 'LLM not initialized'
            }
        
        # System prompt
        system_prompt = """Bạn là một chatbot tư vấn du lịch chuyên nghiệp cho Việt Nam. 
Nhiệm vụ của bạn:
1. Trả lời các câu hỏi về điểm đến, địa điểm tham quan, ẩm thực, văn hóa Việt Nam
2. Gợi ý lịch trình du lịch phù hợp với nhu cầu của khách hàng
3. Tư vấn về ngân sách, phương tiện đi lại, chỗ ở
4. Cung cấp thông tin chi tiết về các địa danh nổi tiếng

Hãy trả lời một cách thân thiện, chi tiết và hữu ích. Sử dụng thông tin từ context được cung cấp.
Nếu không có thông tin trong context, hãy dựa vào kiến thức của bạn về du lịch Việt Nam.
"""
        
        # Lấy context từ Vector DB nếu sử dụng RAG
        context = ""
        if use_rag:
            # Cải thiện query để tìm context tốt hơn
            search_query = user_message
            if destination:
                search_query = f"{user_message} tại {destination}"
            
            context = self._get_context_from_vector_db(search_query)
            
            if context:
                system_prompt += f"\n\nContext từ database:\n{context}"
        
        # Tạo prompt template
        prompt_template = ChatPromptTemplate.from_messages([
            SystemMessagePromptTemplate.from_template(system_prompt),
            HumanMessagePromptTemplate.from_template("{user_message}")
        ])
        
        try:
            # Get chat history từ memory
            chat_history = self.memory.chat_memory.messages if self.memory else []
            
            # Tạo chain với memory
            chain = LLMChain(
                llm=self.llm,
                prompt=prompt_template,
                memory=self.memory,
                verbose=False
            )
            
            # Generate response
            response = chain.run(user_message=user_message)
            
            # Lưu vào memory
            if self.memory:
                self.memory.chat_memory.add_user_message(user_message)
                self.memory.chat_memory.add_ai_message(response)
            
            return {
                'response': response,
                'context_used': bool(context),
                'destination': destination
            }
        
        except Exception as e:
            logger.error(f"Error in chat: {e}")
            return {
                'response': 'Xin lỗi, đã có lỗi xảy ra khi xử lý câu hỏi của bạn.',
                'error': str(e)
            }
    
    def suggest_itinerary(
        self,
        destination: str,
        days: int,
        travelers: int,
        travel_style: str = 'standard',
        interests: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Gợi ý lịch trình du lịch
        
        Args:
            destination: Điểm đến
            days: Số ngày
            travelers: Số người
            travel_style: 'budget', 'standard', 'luxury'
            interests: Danh sách sở thích
        
        Returns:
            Dict với suggested itinerary
        """
        if not self.llm:
            return {'error': 'LLM not initialized'}
        
        # Lấy context từ Vector DB về destination
        context = self._get_context_from_vector_db(
            f"Điểm tham quan du lịch tại {destination}",
            n_results=10
        )
        
        interests_str = ', '.join(interests) if interests else 'không có sở thích đặc biệt'
        
        prompt = f"""Hãy tạo một lịch trình du lịch chi tiết cho chuyến đi đến {destination} trong {days} ngày.

Thông tin:
- Điểm đến: {destination}
- Số ngày: {days}
- Số người: {travelers}
- Phong cách: {travel_style}
- Sở thích: {interests_str}

Context về điểm đến:
{context}

Hãy tạo lịch trình bao gồm:
1. Ngày 1: Các hoạt động chính, địa điểm tham quan, nhà hàng đề xuất
2. Ngày 2: ...
(và tiếp tục cho các ngày còn lại)

Mỗi ngày nên có:
- Địa điểm tham quan vào buổi sáng
- Địa điểm tham quan vào buổi chiều
- Gợi ý nhà hàng cho bữa trưa và tối
- Tips và lưu ý

Hãy trả lời bằng tiếng Việt và chi tiết."""
        
        try:
            response = self.llm.invoke(prompt)
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            return {
                'itinerary': response_text,
                'destination': destination,
                'days': days,
                'travelers': travelers,
                'travel_style': travel_style
            }
        
        except Exception as e:
            logger.error(f"Error generating itinerary: {e}")
            return {'error': str(e)}
    
    def answer_question(
        self,
        question: str,
        destination: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Trả lời câu hỏi về điểm đến
        
        Args:
            question: Câu hỏi
            destination: Điểm đến (optional)
        
        Returns:
            Dict với answer và metadata
        """
        return self.chat(question, use_rag=True, destination=destination)
    
    def clear_memory(self):
        """Xóa lịch sử chat"""
        if self.memory:
            self.memory.clear()


# Singleton instance
_travel_chatbot = None

def get_travel_chatbot(
    llm_provider: str = 'openai',
    model_name: Optional[str] = None
) -> TravelChatbot:
    """Get singleton Travel Chatbot instance"""
    global _travel_chatbot
    if _travel_chatbot is None:
        _travel_chatbot = TravelChatbot(
            llm_provider=llm_provider,
            model_name=model_name
        )
    return _travel_chatbot

