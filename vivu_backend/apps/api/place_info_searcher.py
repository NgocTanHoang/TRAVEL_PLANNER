"""
Công cụ tìm kiếm thông tin địa điểm trên mạng internet sử dụng Google Gemini API
với Google Search Grounding
"""
import logging
import json
from typing import Dict, Optional
from django.conf import settings

logger = logging.getLogger(__name__)

try:
    import google.generativeai as genai
    from google.generativeai import types as genai_types
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    genai_types = None
    logger.warning("google-generativeai not installed. Install with: pip install google-generativeai")


class PlaceInfoSearcher:
    """Tìm kiếm và trích xuất thông tin địa điểm từ internet sử dụng Gemini API"""
    
    def __init__(self):
        self.api_key = getattr(settings, 'GEMINI_API_KEY', None)
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not configured in settings")
        
        if GEMINI_AVAILABLE and self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                # Sử dụng Gemini models (ưu tiên gemini-2.5-flash và gemini-2.0-flash-exp)
                models_to_try = [
                    'gemini-2.5-flash',  # Model mới nhất, không bị giới hạn nghiêm ngặt
                    'gemini-2.0-flash-exp',  # Experimental với nhiều tính năng
                    'gemini-2.0-flash',
                    'gemini-1.5-flash-latest',
                    'gemini-1.5-pro-latest',
                    'gemini-1.5-flash',
                    'gemini-pro'
                ]
                
                self.model = None
                for model_name in models_to_try:
                    try:
                        self.model = genai.GenerativeModel(model_name)
                        logger.info(f"Using Gemini model: {model_name}")
                        break
                    except Exception as e:
                        continue
                
                if not self.model:
                    raise Exception("Không tìm thấy model Gemini nào khả dụng")
                self.available = True
            except Exception as e:
                logger.error(f"Failed to initialize Gemini API: {e}")
                self.available = False
                self.model = None
        else:
            self.available = False
            self.model = None
    
    def search_place_info(self, place_name: str, city: str = None) -> Dict:
        """
        Tìm kiếm thông tin địa điểm trên mạng sử dụng Gemini với Google Search
        
        Args:
            place_name: Tên địa điểm
            city: Tên thành phố/tỉnh (optional)
        
        Returns:
            Dict chứa thông tin tìm được
        """
        if not self.available or not self.model:
            logger.warning("Gemini API not available, returning empty info")
            return self._get_fallback_info(place_name, city)
        
        try:
            # Tạo prompt để tìm kiếm thông tin
            query = f"{place_name}"
            if city:
                query += f" {city} Việt Nam"
            
            prompt = f"""Tìm kiếm và tóm tắt thông tin chi tiết về địa điểm du lịch sau đây:

Tên địa điểm: {place_name}
Tỉnh/Thành phố: {city or 'Việt Nam'}

Hãy tìm kiếm thông tin và cung cấp:
1. Mô tả chi tiết về địa điểm (lịch sử, ý nghĩa, đặc điểm nổi bật)
2. Thời gian tốt nhất để thăm quan
3. Thời gian ước tính cần để tham quan
4. Các hoạt động phổ biến tại địa điểm
5. Đánh giá tổng hợp từ du khách (nếu có)
6. Các thông tin thú vị khác

Trả về kết quả dưới dạng JSON với các trường:
- description: mô tả chi tiết
- best_time_to_visit: thời gian tốt nhất
- estimated_time: thời gian tham quan
- popular_activities: hoạt động phổ biến
- reviews_summary: đánh giá tổng hợp
- interesting_facts: sự kiện thú vị
- source_urls: các URL nguồn thông tin

Chỉ trả về JSON, không có text thêm."""

            # Gọi Gemini API với Google Search Grounding
            # Gemini 2.5 Flash có khả năng tìm kiếm thời gian thực
            # Thử enable Google Search Retrieval tool
            try:
                if genai_types:
                    response = self.model.generate_content(
                        prompt,
                        generation_config=genai_types.GenerationConfig(
                            temperature=0.7,
                            top_p=0.8,
                            top_k=40,
                            max_output_tokens=2048,
                        ),
                        tools=[genai_types.Tool(
                            google_search_retrieval={}
                        )]
                    )
                else:
                    raise AttributeError("genai_types not available")
            except (AttributeError, TypeError, Exception) as e:
                logger.info(f"Google Search Retrieval tool not available, using standard generation: {e}")
                # Fallback: Dùng generation config đơn giản
                # Gemini 2.0 Flash Exp có thể tự động search trong một số trường hợp
                response = self.model.generate_content(
                    prompt,
                    generation_config={
                        'temperature': 0.7,
                        'top_p': 0.8,
                        'top_k': 40,
                        'max_output_tokens': 2048,
                    }
                )
            
            # Parse response
            text = response.text.strip()
            
            # Cố gắng parse JSON từ response
            try:
                # Loại bỏ markdown code blocks nếu có
                if '```json' in text:
                    text = text.split('```json')[1].split('```')[0].strip()
                elif '```' in text:
                    text = text.split('```')[1].split('```')[0].strip()
                
                info_dict = json.loads(text)
                
                # Đảm bảo cấu trúc đúng
                result = {
                    'description': info_dict.get('description', ''),
                    'additional_info': {
                        'best_time_to_visit': info_dict.get('best_time_to_visit', 'Quanh năm'),
                        'estimated_time': info_dict.get('estimated_time', '2-4 giờ'),
                        'popular_activities': info_dict.get('popular_activities', 'Tham quan, tìm hiểu văn hóa'),
                        'interesting_facts': info_dict.get('interesting_facts', '')
                    },
                    'reviews_summary': info_dict.get('reviews_summary', 'Địa điểm được đánh giá cao bởi du khách.'),
                    'source_urls': info_dict.get('source_urls', [])
                }
                
                logger.info(f"Successfully retrieved info for {place_name} using Gemini API")
                return result
                
            except json.JSONDecodeError:
                # Nếu không parse được JSON, lấy text và tạo structure
                logger.warning(f"Could not parse JSON from Gemini response, using text directly")
                return {
                    'description': text[:500] if text else f"Thông tin về {place_name} tại {city or 'Việt Nam'}.",
                    'additional_info': {
                        'best_time_to_visit': 'Quanh năm',
                        'estimated_time': '2-4 giờ',
                        'popular_activities': 'Tham quan, tìm hiểu văn hóa'
                    },
                    'reviews_summary': 'Thông tin từ tìm kiếm mạng.',
                    'source_urls': []
                }
                
        except Exception as e:
            logger.error(f"Error searching place info for {place_name} using Gemini: {e}")
            return self._get_fallback_info(place_name, city)
    
    def _get_fallback_info(self, place_name: str, city: str = None) -> Dict:
        """Fallback info khi không có Gemini API"""
        return {
            'description': f"Thông tin về {place_name} tại {city or 'Việt Nam'}. Đây là một địa điểm nổi tiếng với nhiều hoạt động và trải nghiệm thú vị.",
            'additional_info': {
                'best_time_to_visit': 'Quanh năm',
                'estimated_time': '2-4 giờ',
                'popular_activities': 'Tham quan, chụp ảnh, tìm hiểu văn hóa'
            },
            'images': [],
            'reviews_summary': 'Địa điểm được đánh giá cao bởi du khách với nhiều trải nghiệm tích cực.',
            'contact_info': {},
            'source_urls': []
        }
    
    def enrich_place_data(self, place_data: Dict) -> Dict:
        """
        Làm giàu dữ liệu địa điểm bằng cách tìm kiếm thông tin bổ sung
        
        Args:
            place_data: Dict chứa thông tin địa điểm từ database
        
        Returns:
            Dict với thông tin đã được làm giàu
        """
        place_name = place_data.get('tenDiaDiem', '')
        city = None
        if place_data.get('maTinhThanh'):
            if isinstance(place_data['maTinhThanh'], dict):
                city = place_data['maTinhThanh'].get('tenTinhThanh', '')
            else:
                city = str(place_data['maTinhThanh'])
        
        # Luôn tìm kiếm thông tin bổ sung để làm giàu dữ liệu
        searched_info = self.search_place_info(place_name, city)
        
        # Nếu mô tả hiện tại quá ngắn, cập nhật bằng mô tả từ web
        current_description = place_data.get('moTa', '')
        if not current_description or len(current_description) < 100:
            if searched_info.get('description'):
                place_data['moTa'] = searched_info['description']
        
        # Thêm thông tin bổ sung
        place_data['additional_info'] = searched_info
        
        return place_data


# Singleton instance
_place_searcher = None

def get_place_searcher() -> PlaceInfoSearcher:
    """Get singleton instance of PlaceInfoSearcher"""
    global _place_searcher
    if _place_searcher is None:
        _place_searcher = PlaceInfoSearcher()
    return _place_searcher
