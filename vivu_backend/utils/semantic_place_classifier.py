"""
Semantic Place Classifier - Module hiểu ngữ nghĩa và phân loại địa điểm
=======================================================================
Module này cung cấp khả năng:
- Phân loại địa điểm dựa trên tên, mô tả, và context
- Hiểu ngữ nghĩa của địa điểm (đặc điểm, tiện nghi, phù hợp với loại du lịch nào)
- Trích xuất thông tin từ mô tả tự nhiên
"""
import re
import logging
from typing import Dict, Optional, List, Tuple, Any
import unicodedata

logger = logging.getLogger(__name__)


# Mapping từ types trong Excel/API sang loaiDiaDiem trong database
TYPE_MAPPING = {
    # Địa danh
    'attraction': 'dia_danh',
    'landmark': 'dia_danh',
    'monument': 'dia_danh',
    'temple': 'dia_danh',
    'pagoda': 'dia_danh',
    'church': 'dia_danh',
    'museum': 'dia_danh',
    'park': 'dia_danh',
    'beach': 'dia_danh',
    'mountain': 'dia_danh',
    'cave': 'dia_danh',
    'waterfall': 'dia_danh',
    'lake': 'dia_danh',
    'island': 'dia_danh',
    'bridge': 'dia_danh',
    'tower': 'dia_danh',
    'palace': 'dia_danh',
    'fortress': 'dia_danh',
    'ruin': 'dia_danh',
    'historical_site': 'dia_danh',
    'cultural_site': 'dia_danh',
    'natural_attraction': 'dia_danh',
    'sightseeing': 'dia_danh',
    'viewpoint': 'dia_danh',
    'scenic': 'dia_danh',
    
    # Nhà hàng
    'restaurant': 'nha_hang',
    'cafe': 'nha_hang',
    'café': 'nha_hang',
    'coffee': 'nha_hang',
    'bar': 'nha_hang',
    'pub': 'nha_hang',
    'bistro': 'nha_hang',
    'buffet': 'nha_hang',
    'food_court': 'nha_hang',
    'street_food': 'nha_hang',
    'bakery': 'nha_hang',
    'fast_food': 'nha_hang',
    'dining': 'nha_hang',
    'food': 'nha_hang',
    
    # Khách sạn
    'hotel': 'khach_san',
    'resort': 'khach_san',
    'hostel': 'khach_san',
    'homestay': 'khach_san',
    'guesthouse': 'khach_san',
    'apartment': 'khach_san',
    'villa': 'khach_san',
    'lodge': 'khach_san',
    'inn': 'khach_san',
    'accommodation': 'khach_san',
    'stay': 'khach_san',
    
    # Giải trí
    'entertainment': 'giai_tri',
    'nightclub': 'giai_tri',
    'club': 'giai_tri',
    'disco': 'giai_tri',
    'cinema': 'giai_tri',
    'theater': 'giai_tri',
    'amusement_park': 'giai_tri',
    'zoo': 'giai_tri',
    'aquarium': 'giai_tri',
    'spa': 'giai_tri',
    'massage': 'giai_tri',
    'karaoke': 'giai_tri',
    'bowling': 'giai_tri',
    'casino': 'giai_tri',
    'wellness': 'giai_tri',
    'relaxation': 'giai_tri',
    
    # Mua sắm
    'shopping': 'mua_sam',
    'mall': 'mua_sam',
    'market': 'mua_sam',
    'supermarket': 'mua_sam',
    'convenience_store': 'mua_sam',
    'souvenir_shop': 'mua_sam',
    'boutique': 'mua_sam',
    'store': 'mua_sam',
    'shop': 'mua_sam',
    
    # Khác
    'other': 'khac',
    'unknown': 'khac',
}

# Từ khóa để phân loại dựa trên tên và mô tả (tiếng Việt)
SEMANTIC_KEYWORDS = {
    'dia_danh': [
        # Tôn giáo, tâm linh
        'chùa', 'đền', 'miếu', 'phủ', 'đình', 'lăng', 'mộ', 'tượng', 'tượng đài',
        'nhà thờ', 'nhà nguyện', 'thánh đường', 'giáo đường',
        # Văn hóa, lịch sử
        'bảo tàng', 'di tích', 'lịch sử', 'văn hóa', 'cổ', 'xưa', 'cổ kính',
        'di sản', 'di sản thế giới', 'unesco',
        # Thiên nhiên
        'núi', 'đồi', 'đèo', 'hang', 'động', 'thác', 'suối', 'hồ', 'sông', 'biển', 'bãi biển',
        'vườn quốc gia', 'khu bảo tồn', 'rừng', 'công viên', 'quảng trường',
        'đảo', 'quần đảo', 'bán đảo', 'mũi', 'vịnh', 'vũng', 'bờ biển',
        # Kiến trúc
        'cầu', 'tháp', 'lâu đài', 'pháo đài', 'thành cổ', 'phố cổ', 'phố đi bộ',
        'đài tưởng niệm', 'khu tưởng niệm', 'tượng đài',
        # Khác
        'điểm tham quan', 'thắng cảnh', 'danh lam', 'thắng tích',
    ],
    'nha_hang': [
        'nhà hàng', 'quán ăn', 'quán cà phê', 'café', 'coffee', 'cafe',
        'bar', 'pub', 'bistro', 'buffet', 'steakhouse', 'grill',
        'phở', 'bún', 'bánh mì', 'bánh', 'chè', 'nước', 'trà',
        'food court', 'food center', 'ăn uống', 'ẩm thực', 'món ăn',
        'bakery', 'tiệm bánh', 'bánh ngọt', 'bánh kẹo',
        'quán nhậu', 'nhậu', 'rượu', 'bia',
    ],
    'khach_san': [
        'khách sạn', 'hotel', 'resort', 'residence', 'apartment',
        'hostel', 'homestay', 'guesthouse', 'lodge', 'inn',
        'villa', 'bungalow', 'cabin', 'suite', 'room', 'phòng',
        'nghỉ dưỡng', 'lưu trú', 'chỗ ở', 'nơi ở',
        'khu nghỉ', 'khu nghỉ dưỡng', 'resort',
    ],
    'giai_tri': [
        'khu vui chơi', 'giải trí', 'entertainment', 'amusement',
        'nightclub', 'club', 'disco', 'pub', 'bar',
        'cinema', 'rạp chiếu phim', 'movie theater', 'phim',
        'theater', 'nhà hát', 'sân khấu', 'kịch',
        'spa', 'massage', 'thư giãn', 'relax', 'wellness',
        'karaoke', 'bowling', 'casino', 'sòng bạc',
        'zoo', 'sở thú', 'aquarium', 'thủy cung',
        'công viên giải trí', 'theme park', 'công viên nước',
        'khu vui chơi', 'vui chơi', 'giải trí',
    ],
    'mua_sam': [
        'trung tâm thương mại', 'shopping mall', 'mall', 'plaza',
        'chợ', 'market', 'siêu thị', 'supermarket', 'convenience store',
        'cửa hàng', 'shop', 'store', 'boutique', 'souvenir',
        'mua sắm', 'shopping', 'bán hàng', 'quầy hàng',
        'chợ đêm', 'chợ nổi', 'chợ truyền thống',
    ],
}


def remove_accents(text: str) -> str:
    """Loại bỏ dấu tiếng Việt để so sánh tốt hơn"""
    if not text:
        return ""
    accents = {
        'à': 'a', 'á': 'a', 'ạ': 'a', 'ả': 'a', 'ã': 'a',
        'â': 'a', 'ầ': 'a', 'ấ': 'a', 'ậ': 'a', 'ẩ': 'a', 'ẫ': 'a',
        'ă': 'a', 'ằ': 'a', 'ắ': 'a', 'ặ': 'a', 'ẳ': 'a', 'ẵ': 'a',
        'è': 'e', 'é': 'e', 'ẹ': 'e', 'ẻ': 'e', 'ẽ': 'e',
        'ê': 'e', 'ề': 'e', 'ế': 'e', 'ệ': 'e', 'ể': 'e', 'ễ': 'e',
        'ì': 'i', 'í': 'i', 'ị': 'i', 'ỉ': 'i', 'ĩ': 'i',
        'ò': 'o', 'ó': 'o', 'ọ': 'o', 'ỏ': 'o', 'õ': 'o',
        'ô': 'o', 'ồ': 'o', 'ố': 'o', 'ộ': 'o', 'ổ': 'o', 'ỗ': 'o',
        'ơ': 'o', 'ờ': 'o', 'ớ': 'o', 'ợ': 'o', 'ở': 'o', 'ỡ': 'o',
        'ù': 'u', 'ú': 'u', 'ụ': 'u', 'ủ': 'u', 'ũ': 'u',
        'ư': 'u', 'ừ': 'u', 'ứ': 'u', 'ự': 'u', 'ử': 'u', 'ữ': 'u',
        'ỳ': 'y', 'ý': 'y', 'ỵ': 'y', 'ỷ': 'y', 'ỹ': 'y',
        'đ': 'd',
    }
    result = text.lower()
    for accented, unaccented in accents.items():
        result = result.replace(accented, unaccented)
    return result


def classify_place_by_semantics(
    name: str,
    description: str = '',
    type_hint: str = '',
    category: str = ''
) -> str:
    """
    Phân loại địa điểm dựa trên ngữ nghĩa (tên, mô tả, type hint, category).
    Trả về loaiDiaDiem phù hợp nhất.
    
    Args:
        name: Tên địa điểm
        description: Mô tả địa điểm
        type_hint: Type hint từ API hoặc nguồn dữ liệu
        category: Category từ database hoặc API
    
    Returns:
        loaiDiaDiem: 'dia_danh', 'nha_hang', 'khach_san', 'giai_tri', 'mua_sam', hoặc 'khac'
    """
    # Chuẩn hóa text để so sánh
    text = f"{name} {description} {type_hint} {category}".lower()
    text_no_accent = remove_accents(text)
    
    # Đếm điểm cho mỗi loại
    scores = {
        'dia_danh': 0,
        'nha_hang': 0,
        'khach_san': 0,
        'giai_tri': 0,
        'mua_sam': 0,
        'khac': 0,
    }
    
    # Kiểm tra từ khóa
    for category_type, keywords in SEMANTIC_KEYWORDS.items():
        for keyword in keywords:
            keyword_no_accent = remove_accents(keyword)
            if keyword_no_accent in text_no_accent or keyword in text:
                scores[category_type] += 1
    
    # Nếu có type_hint hoặc category, map nó (ưu tiên cao hơn)
    for hint in [type_hint, category]:
        if hint:
            hint_lower = str(hint).lower().strip()
            mapped_type = TYPE_MAPPING.get(hint_lower)
            if mapped_type:
                scores[mapped_type] += 3  # Tăng điểm cho type hint
    
    # Tìm loại có điểm cao nhất
    max_score = max(scores.values())
    if max_score == 0:
        return 'khac'  # Mặc định là "Khác"
    
    # Trả về loại có điểm cao nhất
    for category_type, score in scores.items():
        if score == max_score:
            return category_type
    
    return 'khac'


def extract_place_features(
    name: str,
    description: str = '',
    category: str = ''
) -> Dict[str, Any]:
    """
    Trích xuất đặc điểm của địa điểm từ tên và mô tả.
    
    Returns:
        Dict chứa các đặc điểm như:
        - suitable_for: ['family', 'couple', 'solo', 'group', 'romantic', 'adventure', ...]
        - best_time: ['morning', 'afternoon', 'evening', 'night', 'anytime']
        - duration_hours: Ước tính thời gian tham quan (giờ)
        - price_level: 'free', 'budget', 'moderate', 'expensive'
        - tags: List các tags
    """
    text = f"{name} {description}".lower()
    text_no_accent = remove_accents(text)
    
    features = {
        'suitable_for': [],
        'best_time': ['anytime'],
        'duration_hours': 2.0,  # Mặc định 2 giờ
        'price_level': 'moderate',
        'tags': [],
    }
    
    # Phân tích suitable_for
    if any(word in text_no_accent for word in ['gia đình', 'family', 'trẻ em', 'children', 'kids']):
        features['suitable_for'].append('family')
    if any(word in text_no_accent for word in ['cặp đôi', 'couple', 'lãng mạn', 'romantic', 'honeymoon']):
        features['suitable_for'].append('couple')
        features['suitable_for'].append('romantic')
    if any(word in text_no_accent for word in ['một mình', 'solo', 'độc thân']):
        features['suitable_for'].append('solo')
    if any(word in text_no_accent for word in ['nhóm', 'group', 'đoàn']):
        features['suitable_for'].append('group')
    if any(word in text_no_accent for word in ['mạo hiểm', 'adventure', 'thể thao', 'sport']):
        features['suitable_for'].append('adventure')
    if any(word in text_no_accent for word in ['tâm linh', 'spiritual', 'tôn giáo', 'religious']):
        features['suitable_for'].append('spiritual')
    if any(word in text_no_accent for word in ['văn hóa', 'cultural', 'lịch sử', 'history']):
        features['suitable_for'].append('cultural')
    
    # Phân tích best_time
    if any(word in text_no_accent for word in ['bình minh', 'sunrise', 'sáng sớm', 'early morning']):
        features['best_time'] = ['morning', 'early_morning']
    elif any(word in text_no_accent for word in ['hoàng hôn', 'sunset', 'chiều tối', 'evening']):
        features['best_time'] = ['evening', 'sunset']
    elif any(word in text_no_accent for word in ['đêm', 'night', 'nightlife', 'nightclub']):
        features['best_time'] = ['night', 'evening']
    elif any(word in text_no_accent for word in ['bảo tàng', 'museum', 'nhà thờ', 'church']):
        features['best_time'] = ['morning', 'afternoon']
    
    # Ước tính duration_hours
    if any(word in text_no_accent for word in ['bảo tàng', 'museum', 'di tích', 'historical']):
        features['duration_hours'] = 1.5
    elif any(word in text_no_accent for word in ['công viên', 'park', 'vườn', 'garden']):
        features['duration_hours'] = 2.0
    elif any(word in text_no_accent for word in ['núi', 'mountain', 'trekking', 'hiking']):
        features['duration_hours'] = 4.0
    elif any(word in text_no_accent for word in ['spa', 'massage', 'wellness']):
        features['duration_hours'] = 2.0
    elif any(word in text_no_accent for word in ['chợ', 'market', 'shopping']):
        features['duration_hours'] = 1.5
    
    # Phân tích price_level
    if any(word in text_no_accent for word in ['miễn phí', 'free', 'không mất phí']):
        features['price_level'] = 'free'
    elif any(word in text_no_accent for word in ['rẻ', 'budget', 'giá rẻ', 'bình dân']):
        features['price_level'] = 'budget'
    elif any(word in text_no_accent for word in ['đắt', 'expensive', 'luxury', 'cao cấp', 'premium']):
        features['price_level'] = 'expensive'
    
    # Trích xuất tags
    tag_keywords = {
        'outdoor': ['ngoài trời', 'outdoor', 'thiên nhiên', 'nature'],
        'indoor': ['trong nhà', 'indoor', 'máy lạnh', 'air-conditioned'],
        'photography': ['chụp ảnh', 'photography', 'instagram', 'đẹp', 'scenic'],
        'historical': ['lịch sử', 'historical', 'cổ', 'ancient'],
        'religious': ['tôn giáo', 'religious', 'tâm linh', 'spiritual'],
        'nature': ['thiên nhiên', 'nature', 'rừng', 'forest', 'biển', 'beach'],
        'cultural': ['văn hóa', 'cultural', 'truyền thống', 'traditional'],
    }
    
    for tag, keywords in tag_keywords.items():
        if any(keyword in text_no_accent for keyword in keywords):
            features['tags'].append(tag)
    
    return features


def is_suitable_for_travel_style(
    place_features: Dict[str, Any],
    travel_style: str
) -> bool:
    """
    Kiểm tra xem địa điểm có phù hợp với travel_style không.
    
    Args:
        place_features: Kết quả từ extract_place_features
        travel_style: 'budget', 'standard', 'luxury', 'romantic', 'adventure', 'family', ...
    
    Returns:
        True nếu phù hợp, False nếu không
    """
    travel_style_lower = str(travel_style).lower()
    
    # Kiểm tra suitable_for
    suitable_for = place_features.get('suitable_for', [])
    if travel_style_lower in ['romantic', 'couple']:
        return 'romantic' in suitable_for or 'couple' in suitable_for
    elif travel_style_lower in ['family', 'kid-friendly']:
        return 'family' in suitable_for
    elif travel_style_lower in ['adventure', 'outdoor']:
        return 'adventure' in suitable_for
    elif travel_style_lower in ['cultural', 'history']:
        return 'cultural' in suitable_for or 'spiritual' in suitable_for
    
    # Kiểm tra price_level
    price_level = place_features.get('price_level', 'moderate')
    if travel_style_lower == 'budget':
        return price_level in ['free', 'budget', 'moderate']
    elif travel_style_lower == 'luxury':
        return price_level in ['moderate', 'expensive']
    
    return True  # Mặc định phù hợp với standard


def understand_place_semantics(
    name: str,
    description: str = '',
    type_hint: str = '',
    category: str = ''
) -> Dict[str, Any]:
    """
    Hiểu ngữ nghĩa đầy đủ của địa điểm.
    
    Returns:
        Dict chứa:
        - loaiDiaDiem: Phân loại địa điểm
        - features: Đặc điểm của địa điểm
        - confidence: Độ tin cậy của phân loại (0-1)
    """
    # Phân loại
    loai_dia_diem = classify_place_by_semantics(name, description, type_hint, category)
    
    # Trích xuất đặc điểm
    features = extract_place_features(name, description, category)
    
    # Tính confidence dựa trên số lượng từ khóa match
    text = f"{name} {description}".lower()
    text_no_accent = remove_accents(text)
    
    keyword_matches = 0
    total_keywords = 0
    for keywords in SEMANTIC_KEYWORDS.values():
        for keyword in keywords:
            total_keywords += 1
            if remove_accents(keyword) in text_no_accent or keyword in text:
                keyword_matches += 1
    
    confidence = min(1.0, keyword_matches / max(1, total_keywords / 10))  # Normalize
    
    return {
        'loaiDiaDiem': loai_dia_diem,
        'features': features,
        'confidence': confidence,
    }

