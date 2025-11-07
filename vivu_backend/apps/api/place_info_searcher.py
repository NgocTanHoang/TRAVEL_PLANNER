"""
Công cụ tìm kiếm thông tin địa điểm trên mạng internet
Sử dụng nhiều nguồn miễn phí: DuckDuckGo, Wikipedia, SerpAPI, Tavily
"""
import logging
import json
import re
import requests
from typing import Dict, Optional, List
from django.conf import settings

logger = logging.getLogger(__name__)

# DuckDuckGo - hoàn toàn miễn phí, không cần API key
try:
    from duckduckgo_search import DDGS
    DUCKDUCKGO_AVAILABLE = True
except ImportError:
    DUCKDUCKGO_AVAILABLE = False
    logger.warning("duckduckgo-search not installed. Install with: pip install duckduckgo-search")

# Wikipedia API - miễn phí
WIKIPEDIA_API_URL = "https://vi.wikipedia.org/w/api.php"

# SerpAPI - có free tier
try:
    from serpapi import GoogleSearch
    SERPAPI_AVAILABLE = True
except ImportError:
    SERPAPI_AVAILABLE = False

# Tavily API - fallback
try:
    from tavily import TavilyClient
    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False
    logger.warning("tavily-python not installed. Install with: pip install tavily-python")


class PlaceInfoSearcher:
    """Tìm kiếm và trích xuất thông tin địa điểm từ internet với nhiều nguồn miễn phí"""
    
    def __init__(self):
        # DuckDuckGo - luôn có sẵn nếu đã cài đặt
        self.ddg_available = DUCKDUCKGO_AVAILABLE
        
        # Wikipedia - luôn có sẵn
        self.wikipedia_available = True
        
        # SerpAPI
        self.serpapi_key = getattr(settings, 'SERPAPI_API_KEY', None)
        self.serpapi_available = SERPAPI_AVAILABLE and bool(self.serpapi_key)
        
        # Tavily
        self.tavily_key = getattr(settings, 'TAVILY_API_KEY', None)
        self.tavily = None
        if TAVILY_AVAILABLE and self.tavily_key:
            try:
                self.tavily = TavilyClient(api_key=self.tavily_key)
                logger.info("Tavily client initialized")
            except Exception as e:
                logger.warning(f"Tavily initialization failed: {e}")
        
        self.available = self.ddg_available or self.wikipedia_available or self.serpapi_available or (self.tavily is not None)
        
        if not self.available:
            logger.warning("No search APIs available. Install duckduckgo-search for free search.")
    
    def search_place_info(self, place_name: str, city: str = None) -> Dict:
        """
        Tìm kiếm thông tin địa điểm với nhiều nguồn (DuckDuckGo -> Wikipedia -> SerpAPI -> Tavily)
        
        Args:
            place_name: Tên địa điểm
            city: Tên thành phố/tỉnh (optional)
        
        Returns:
            Dict chứa thông tin tìm được
        """
        # Chuẩn hóa city - loại bỏ số nếu là ID
        normalized_city = city
        if city and city.isdigit():
            normalized_city = None  # Bỏ qua nếu city là số
        
        # Tạo nhiều biến thể query để tìm kiếm tốt hơn
        queries = [
            f"{place_name} du lịch lịch sử văn hóa",
            f"{place_name} Việt Nam",
            place_name,  # Query đơn giản nhất
        ]
        if normalized_city:
            queries.insert(0, f"{place_name} {normalized_city} Việt Nam du lịch")
            queries.insert(1, f"{place_name} {normalized_city}")
        
        all_content = []
        source_urls = []
        ratings = []
        
        # 1. Thử Wikipedia trước (thường có thông tin tốt nhất cho địa điểm lịch sử)
        try:
            wiki_result = self._search_wikipedia(place_name, normalized_city)
            if wiki_result and wiki_result.get('content'):
                all_content.append(wiki_result['content'])
                if wiki_result.get('url'):
                    source_urls.append(wiki_result['url'])
                logger.info(f"Found Wikipedia result for {place_name}")
        except Exception as e:
            logger.debug(f"Wikipedia search failed: {e}")
        
        # 2. Thử DuckDuckGo với nhiều queries
        if self.ddg_available:
            for query in queries[:2]:  # Thử 2 queries đầu
                try:
                    ddg_results = self._search_duckduckgo(query)
                    if ddg_results and ddg_results.get('content'):
                        all_content.extend(ddg_results.get('content', []))
                        source_urls.extend(ddg_results.get('urls', []))
                        ratings.extend(ddg_results.get('ratings', []))
                        logger.info(f"Found {len(ddg_results.get('content', []))} results from DuckDuckGo with query: {query}")
                        break  # Chỉ cần 1 query thành công
                except Exception as e:
                    logger.debug(f"DuckDuckGo search failed for '{query}': {e}")
        
        # 3. Thử SerpAPI (nếu có API key)
        if self.serpapi_available:
            try:
                serpapi_results = self._search_serpapi(queries[0])
                if serpapi_results and serpapi_results.get('content'):
                    all_content.extend(serpapi_results.get('content', []))
                    source_urls.extend(serpapi_results.get('urls', []))
                    ratings.extend(serpapi_results.get('ratings', []))
                    logger.info(f"Found {len(serpapi_results.get('content', []))} results from SerpAPI")
            except Exception as e:
                logger.debug(f"SerpAPI search failed: {e}")
        
        # 4. Thử Tavily (nếu có API key)
        if self.tavily:
            try:
                tavily_results = self._search_tavily(queries[0])
                if tavily_results and tavily_results.get('content'):
                    all_content.extend(tavily_results.get('content', []))
                    source_urls.extend(tavily_results.get('urls', []))
                    ratings.extend(tavily_results.get('ratings', []))
                    logger.info(f"Found {len(tavily_results.get('content', []))} results from Tavily")
            except Exception as e:
                logger.debug(f"Tavily search failed: {e}")
        
        # Xử lý và làm sạch nội dung
        if not all_content:
            logger.warning(f"No results found for {place_name} (city: {city})")
            return self._get_fallback_info(place_name, normalized_city)
        
        # Làm sạch và tổng hợp nội dung
        cleaned_content = self._clean_content(all_content)
        combined_content = ' '.join(cleaned_content)
        
        # Tăng độ dài mô tả (từ 800 lên 2000 ký tự)
        description = combined_content[:2000] if combined_content else ''
        
        # Đảm bảo không cắt giữa câu
        if len(description) == 2000 and description[-1] not in '.!?':
            last_sentence_end = max(
                description.rfind('.'),
                description.rfind('!'),
                description.rfind('?')
            )
            if last_sentence_end > 1000:  # Chỉ cắt nếu tìm thấy câu kết thúc hợp lý
                description = description[:last_sentence_end + 1]
        
        # Trích xuất thông tin từ nội dung
        best_time = self._extract_best_time(combined_content)
        estimated_time = self._extract_estimated_time(combined_content)
        activities = self._extract_activities(combined_content)
        interesting_facts = self._extract_interesting_facts(combined_content)
        
        # Tính rating trung bình nếu có
        avg_rating = sum(ratings) / len(ratings) if ratings else None
        reviews_summary = f"Địa điểm được đánh giá {avg_rating:.1f}/5 bởi du khách." if avg_rating else "Địa điểm được đánh giá cao bởi du khách."
        
        result = {
            'description': description or f"Thông tin về {place_name} tại {city or 'Việt Nam'}. Đây là một địa điểm nổi tiếng với nhiều hoạt động và trải nghiệm thú vị.",
            'additional_info': {
                'best_time_to_visit': best_time,
                'estimated_time': estimated_time,
                'popular_activities': activities,
                'interesting_facts': interesting_facts
            },
            'reviews_summary': reviews_summary,
            'source_urls': list(set(source_urls))[:10]  # Loại bỏ trùng lặp, giới hạn 10 URL
        }
        
        logger.info(f"Successfully retrieved info for {place_name} from {len(cleaned_content)} sources")
        return result
    
    def _search_duckduckgo(self, query: str) -> Optional[Dict]:
        """Tìm kiếm với DuckDuckGo (miễn phí)"""
        if not self.ddg_available:
            return None
        
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=8))  # Tăng số lượng kết quả
            
            content = []
            urls = []
            ratings = []
            
            for result in results:
                text = result.get('body', '')
                if text and len(text.strip()) > 50:  # Chỉ lấy nội dung có ý nghĩa
                    content.append(text)
                url = result.get('href', '')
                if url:
                    urls.append(url)
                
                # Tìm rating
                rating_match = re.search(r'(\d+\.?\d*)\s*/\s*5|(\d+\.?\d*)\s*star|đánh giá\s*(\d+\.?\d*)', text, re.IGNORECASE)
                if rating_match:
                    rating = float(rating_match.group(1) or rating_match.group(2) or rating_match.group(3))
                    ratings.append(rating)
            
            if content:
                return {'content': content, 'urls': urls, 'ratings': ratings}
            return None
        except Exception as e:
            logger.warning(f"DuckDuckGo error for query '{query}': {e}")
            return None
    
    def _search_wikipedia(self, place_name: str, city: str = None) -> Optional[Dict]:
        """Tìm kiếm với Wikipedia API (miễn phí)"""
        # Thử nhiều biến thể tên
        search_queries = [place_name]
        
        # Thêm biến thể nếu có tên trong ngoặc
        if '(' in place_name and ')' in place_name:
            # Ví dụ: "Bến Nhà Rồng (Bảo tàng Hồ Chí Minh)" -> thử cả 2
            main_name = place_name.split('(')[0].strip()
            alt_name = place_name.split('(')[1].split(')')[0].strip()
            search_queries.extend([main_name, alt_name, f"{main_name} {alt_name}"])
        
        if city:
            search_queries.append(f"{place_name} {city}")
        
        for search_query in search_queries:
            try:
                params = {
                    'action': 'query',
                    'format': 'json',
                    'list': 'search',
                    'srsearch': search_query,
                    'srlimit': 3,  # Tăng số lượng kết quả tìm kiếm
                    'srnamespace': 0
                }
                
                response = requests.get(WIKIPEDIA_API_URL, params=params, timeout=10)
                if response.status_code != 200:
                    continue
                
                data = response.json()
                search_results = data.get('query', {}).get('search', [])
                if not search_results:
                    continue
                
                # Thử từng kết quả tìm được
                for result in search_results:
                    page_title = result['title']
                    
                    # Lấy nội dung trang
                    params = {
                        'action': 'query',
                        'format': 'json',
                        'prop': 'extracts',
                        'exintro': False,  # Lấy nhiều nội dung hơn
                        'exchars': 1000,  # Lấy 1000 ký tự
                        'explaintext': True,
                        'titles': page_title
                    }
                    
                    response = requests.get(WIKIPEDIA_API_URL, params=params, timeout=10)
                    if response.status_code != 200:
                        continue
                    
                    data = response.json()
                    pages = data.get('query', {}).get('pages', {})
                    if not pages:
                        continue
                    
                    page = list(pages.values())[0]
                    extract = page.get('extract', '')
                    
                    if extract and len(extract) > 100:  # Chỉ lấy nội dung đủ dài
                        logger.info(f"Found Wikipedia page: {page_title}")
                        return {
                            'content': extract,
                            'url': f"https://vi.wikipedia.org/wiki/{page_title.replace(' ', '_')}"
                        }
            except Exception as e:
                logger.debug(f"Wikipedia error for query '{search_query}': {e}")
                continue
        
        return None
    
    def _search_serpapi(self, query: str) -> Optional[Dict]:
        """Tìm kiếm với SerpAPI"""
        if not self.serpapi_available:
            return None
        
        try:
            params = {
                'engine': 'google',
                'q': query,
                'api_key': self.serpapi_key,
                'hl': 'vi',
                'gl': 'vn',
                'num': 5
            }
            
            search = GoogleSearch(params)
            results = search.get_dict()
            
            content = []
            urls = []
            ratings = []
            
            # Lấy kết quả tìm kiếm
            organic_results = results.get('organic_results', [])
            for result in organic_results:
                snippet = result.get('snippet', '')
                if snippet:
                    content.append(snippet)
                url = result.get('link', '')
                if url:
                    urls.append(url)
            
            return {'content': content, 'urls': urls, 'ratings': ratings}
        except Exception as e:
            logger.debug(f"SerpAPI error: {e}")
            return None
    
    def _search_tavily(self, query: str) -> Optional[Dict]:
        """Tìm kiếm với Tavily"""
        if not self.tavily:
            return None
        
        try:
            results = self.tavily.search(
                query=query,
                search_depth="advanced",
                max_results=5
            )
            
            if not results or not results.get('results'):
                return None
            
            content = []
            urls = []
            ratings = []
            
            for result in results['results']:
                text = result.get('content', '')
                if text:
                    content.append(text)
                url = result.get('url', '')
                if url:
                    urls.append(url)
                
                # Tìm rating
                rating_match = re.search(r'(\d+\.?\d*)\s*/\s*5|(\d+\.?\d*)\s*star|đánh giá\s*(\d+\.?\d*)', text, re.IGNORECASE)
                if rating_match:
                    rating = float(rating_match.group(1) or rating_match.group(2) or rating_match.group(3))
                    ratings.append(rating)
            
            return {'content': content, 'urls': urls, 'ratings': ratings}
        except Exception as e:
            logger.debug(f"Tavily error: {e}")
            return None
    
    def _clean_content(self, content_list: List[str]) -> List[str]:
        """Làm sạch nội dung, loại bỏ các cụm từ không cần thiết và chỉ giữ tiếng Việt"""
        cleaned = []
        
        # Các pattern cần loại bỏ
        unwanted_patterns = [
            r'\[sửa\s*\|\s*sửa\s*mã\s*nguồn\]',
            r'\[sửa\]',
            r'\[sửa\s*mã\s*nguồn\]',
            r'##\s*Lịch\s*sử\s*\[sửa',
            r'\[.*?sửa.*?\]',
            r'\[.*?edit.*?\]',
            r'\[.*?source.*?\]',
            r'##\s*Tham\s*khảo.*',
            r'##\s*Chú\s*thích.*',
            r'##\s*Xem\s*thêm.*',
            r'##\s*Liên\s*kết\s*ngoài.*',
            r'\(English below\)',  # Loại bỏ "English below"
            r'Dear\s+[A-Za-z0-9]+,.*?\.',  # Loại bỏ email greetings
            r'Thank\s+you.*?\.',
            r'We\s+hope.*?\.',
            r'Rest\s+assured.*?\.',
            r'Once\s+again.*?\.',
            r'This\s+is\s+our.*?\.',
        ]
        
        # Pattern để nhận diện tiếng Việt (có dấu)
        vietnamese_chars = r'[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđÀÁẠẢÃÂẦẤẬẨẪĂẰẮẶẲẴÈÉẸẺẼÊỀẾỆỂỄÌÍỊỈĨÒÓỌỎÕÔỒỐỘỔỖƠỜỚỢỞỠÙÚỤỦŨƯỪỨỰỬỮỲÝỴỶỸĐ]'
        
        for text in content_list:
            if not text:
                continue
            
            # Loại bỏ các pattern không mong muốn
            for pattern in unwanted_patterns:
                text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.MULTILINE | re.DOTALL)
            
            # Loại bỏ các dấu ngoặc vuông còn sót lại
            text = re.sub(r'\[.*?\]', '', text)
            
            # Loại bỏ email patterns
            text = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', '', text)
            
            # Tách thành câu và lọc chỉ giữ câu tiếng Việt
            sentences = re.split(r'[.!?]\s+', text)
            vietnamese_sentences = []
            
            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence or len(sentence) < 10:
                    continue
                
                # Đếm số ký tự tiếng Việt
                vietnamese_count = len(re.findall(vietnamese_chars, sentence))
                total_chars = len(re.sub(r'\s+', '', sentence))
                
                # Chỉ giữ câu có ít nhất 20% ký tự tiếng Việt (giảm threshold để giữ nhiều nội dung hơn)
                if total_chars > 0 and (vietnamese_count / total_chars) >= 0.2:
                    # Loại bỏ các cụm từ tiếng Anh phổ biến
                    sentence = re.sub(r'\b(Park Hyatt|Saigon|Ho Chi Minh City|Vietnam|hotel|restaurant|spa|pool|lounge)\b', '', sentence, flags=re.IGNORECASE)
                    vietnamese_sentences.append(sentence)
            
            # Ghép lại và làm sạch
            if vietnamese_sentences:
                text = '. '.join(vietnamese_sentences)
                text = re.sub(r'\s+', ' ', text)  # Nhiều khoảng trắng thành 1
                text = re.sub(r'\s*##\s*', ' ', text)  # Loại bỏ markdown headers
                text = re.sub(r'\s*#\s*', ' ', text)
                text = text.strip()
                
                if len(text) > 50:  # Chỉ giữ nội dung có ý nghĩa
                    cleaned.append(text)
        
        return cleaned
    
    def _extract_best_time(self, content: str) -> str:
        """Trích xuất thời gian tốt nhất để tham quan từ nội dung"""
        if not content:
            return 'Quanh năm'
        
        time_patterns = [
            r'mùa\s+(\w+)',
            r'tháng\s+(\d+)',
            r'(\d+)\s*-\s*(\d+)\s*tháng',
            r'từ\s+tháng\s+(\d+)\s+đến\s+tháng\s+(\d+)',
            r'mùa\s+xuân|mùa\s+hè|mùa\s+thu|mùa\s+đông',
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                return match.group(0)
        
        return 'Quanh năm'
    
    def _extract_estimated_time(self, content: str) -> str:
        """Trích xuất thời gian ước tính tham quan"""
        if not content:
            return '2-4 giờ'
        
        time_patterns = [
            r'(\d+)\s*-\s*(\d+)\s*giờ',
            r'(\d+)\s*giờ',
            r'khoảng\s+(\d+)\s*giờ',
            r'(\d+)\s*-\s*(\d+)\s*tiếng',
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                if match.lastindex >= 2:
                    return f"{match.group(1)}-{match.group(2)} giờ"
                else:
                    return f"{match.group(1)} giờ"
        
        return '2-4 giờ'
    
    def _extract_activities(self, content: str) -> str:
        """Trích xuất các hoạt động phổ biến"""
        if not content:
            return 'Tham quan, tìm hiểu văn hóa'
        
        activity_keywords = [
            'tham quan', 'chụp ảnh', 'tìm hiểu', 'khám phá', 'thưởng thức',
            'ngắm cảnh', 'cắm trại', 'leo núi', 'tắm biển', 'mua sắm'
        ]
        
        found_activities = []
        for keyword in activity_keywords:
            if keyword in content.lower():
                found_activities.append(keyword)
        
        if found_activities:
            return ', '.join(found_activities[:3])
        
        return 'Tham quan, tìm hiểu văn hóa'
    
    def _extract_interesting_facts(self, content: str) -> str:
        """Trích xuất các sự kiện thú vị"""
        if not content:
            return ''
        
        sentences = re.split(r'[.!?]\s+', content)
        interesting_sentences = []
        
        keywords = ['nổi tiếng', 'độc đáo', 'thú vị', 'lịch sử', 'văn hóa', 'di tích']
        for sentence in sentences:
            if any(keyword in sentence.lower() for keyword in keywords):
                if len(sentence) > 20 and len(sentence) < 200:
                    interesting_sentences.append(sentence.strip())
                    if len(interesting_sentences) >= 2:
                        break
        
        return ' '.join(interesting_sentences) if interesting_sentences else ''
    
    def _get_fallback_info(self, place_name: str, city: str = None) -> Dict:
        """Fallback info khi không có API nào khả dụng"""
        return {
            'description': f"Thông tin về {place_name} tại {city or 'Việt Nam'}. Đây là một địa điểm nổi tiếng với nhiều hoạt động và trải nghiệm thú vị.",
            'additional_info': {
                'best_time_to_visit': 'Quanh năm',
                'estimated_time': '2-4 giờ',
                'popular_activities': 'Tham quan, chụp ảnh, tìm hiểu văn hóa'
            },
            'reviews_summary': 'Địa điểm được đánh giá cao bởi du khách với nhiều trải nghiệm tích cực.',
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
