"""
Script để tải và load dataset "Vietnam tourism v2" từ Kaggle vào Vector DB
===========================================================================
Dataset: https://www.kaggle.com/datasets/8477459/vietnam-tourism-v2
"""

import json
import re
import requests
from pathlib import Path
import sys
import os
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents.travel_agents.vector_db import get_vector_db_agent

logger = logging.getLogger(__name__)

# URL của dataset
DATASET_URL = "https://storage.googleapis.com/kagglesdsdata/datasets/8477459/13364342/train_vietnam_tourism.json?X-Goog-Algorithm=GOOG4-RSA-SHA256&X-Goog-Credential=gcp-kaggle-com%40kaggle-161607.iam.gserviceaccount.com%2F20251104%2Fauto%2Fstorage%2Fgoog4_request&X-Goog-Date=20251104T123935Z&X-Goog-Expires=259200&X-Goog-SignedHeaders=host&X-Goog-Signature=1b0bf47d95f818f2bb1ba4c48ef553cd55b58780f3386828581256ea462862d2e91f64208ebcb3d572326cd82a41655fc464ed91ccf52baa42e0d149770eb9d05a8da8360b12c5d86e41d51207a7c07386e967aab1d52fa42631a88e39c6d1e23ac08f96df30a4dcdb1c7b20bb26077da5065212624a976b3afb888731d401c85893fdbaa78a32d0048dbe1dc2e4915eaa9db8227b4349c37b647b74a52d92f36d0f9e336f019f50610a8113c4a9d19202c415f7a36e6143564b80e137b015681cf17410e17f1202e678490e79fc3d8a48ca23afed9319c3dae9563f8da0f7efe8b8aa2de07f0cc66e0be88cc4218eca5e7f450ff9ffa02390dfc2d7702628de"

# Vietnamese city names patterns để extract từ text
CITY_PATTERNS = [
    r'hà nội', r'hồ chí minh', r'tp\.? hồ chí minh', r'tp\.?hcm', r'sài gòn',
    r'đà nẵng', r'hải phòng', r'cần thơ', r'hà giang', r'cao bằng', r'lào cai',
    r'sapa', r'điện biên', r'lai châu', r'sơn la', r'yên bái', r'hoà bình',
    r'thái nguyên', r'lạng sơn', r'quảng ninh', r'hạ long', r'cát bà',
    r'bắc giang', r'phú thọ', r'vĩnh phúc', r'bắc ninh', r'hải dương',
    r'hưng yên', r'thái bình', r'hà nam', r'nam định', r'ninh bình',
    r'thanh hóa', r'nghệ an', r'hà tĩnh', r'quảng bình', r'quảng trị',
    r'huế', r'thừa thiên huế', r'quảng nam', r'hội an', r'quảng ngãi',
    r'bình định', r'quy nhơn', r'phú yên', r'khánh hòa', r'nha trang',
    r'ninh thuận', r'bình thuận', r'phan thiết', r'mũi né', r'kon tum',
    r'gia lai', r'đắk lắk', r'đăk lăk', r'đắk nông', r'đăk nông',
    r'lâm đồng', r'đà lạt', r'bình phước', r'tây ninh', r'bình dương',
    r'đồng nai', r'bà rịa[-\s]?vũng tàu', r'vũng tàu', r'côn đảo',
    r'long an', r'tiền giang', r'bến tre', r'trà vinh', r'vĩnh long',
    r'đồng tháp', r'an giang', r'kiên giang', r'hậu giang', r'sóc trăng',
    r'bạc liêu', r'cà mau', r'phú quốc', r'tam đảo', r'ba vì'
]

# Category keywords để phân loại
CATEGORY_KEYWORDS = {
    'attraction': ['di tích', 'thắng cảnh', 'điểm tham quan', 'du lịch', 'danh lam', 
                   'hang động', 'chùa', 'đền', 'lăng', 'bảo tàng', 'công viên',
                   'vườn quốc gia', 'bãi biển', 'núi', 'thác', 'đảo'],
    'restaurant': ['nhà hàng', 'quán ăn', 'ẩm thực', 'đặc sản', 'món ăn',
                   'phở', 'bánh mì', 'cafe', 'quán cà phê'],
    'hotel': ['khách sạn', 'resort', 'homestay', 'lưu trú', 'nghỉ dưỡng']
}


def extract_city_from_text(text: str) -> Optional[str]:
    """Extract city name từ text"""
    if not text:
        return None
    
    text_lower = text.lower()
    
    # Check các patterns
    for pattern in CITY_PATTERNS:
        match = re.search(pattern, text_lower)
        if match:
            city_name = match.group(0)
            # Normalize city name
            city_mapping = {
                'hà nội': 'Hanoi',
                'hồ chí minh': 'Ho Chi Minh City',
                'tp hồ chí minh': 'Ho Chi Minh City',
                'tp.hcm': 'Ho Chi Minh City',
                'sài gòn': 'Ho Chi Minh City',
                'đà nẵng': 'Da Nang',
                'hải phòng': 'Hai Phong',
                'cần thơ': 'Can Tho',
                'hạ long': 'Ha Long',
                'cát bà': 'Cat Ba',
                'hội an': 'Hoi An',
                'huế': 'Hue',
                'nha trang': 'Nha Trang',
                'đà lạt': 'Da Lat',
                'sapa': 'Sapa',
                'phú quốc': 'Phu Quoc',
                'vũng tàu': 'Vung Tau',
                'mũi né': 'Mui Ne',
                'phan thiết': 'Phan Thiet'
            }
            return city_mapping.get(city_name, city_name.title())
    
    return None


def categorize_text(text: str) -> str:
    """Phân loại text thành category"""
    text_lower = text.lower()
    
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                return category
    
    return 'attraction'  # Default


def extract_destinations_from_json(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract destination information từ JSON dataset
    
    Args:
        data: JSON data từ Kaggle dataset
        
    Returns:
        List of destination dictionaries
    """
    destinations = []
    
    if 'data' not in data:
        logger.warning("No 'data' key found in JSON")
        return destinations
    
    doc_id = 0
    
    for item in data['data']:
        title = item.get('title', '')
        paragraphs = item.get('paragraphs', [])
        
        for para_idx, paragraph in enumerate(paragraphs):
            context = paragraph.get('context', '')
            
            if not context or len(context.strip()) < 50:  # Skip very short contexts
                continue
            
            # Extract city từ context
            city = extract_city_from_text(context)
            
            # Extract category
            category = categorize_text(context)
            
            # Extract destination name từ title hoặc context
            # Tìm tên địa điểm trong text (thường là chữ in hoa hoặc sau "tại", "ở")
            name_match = re.search(r'(?:tại|ở|đến|thăm)\s+([A-ZĐ][a-zàáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđ\s]+?)(?:,|\.|$)', context, re.IGNORECASE)
            if name_match:
                name = name_match.group(1).strip()
            else:
                # Fallback: lấy một phần của title hoặc context
                name = title[:100] if title else context[:100]
            
            # Tạo description từ context (giới hạn 500 ký tự)
            description = context[:500] if len(context) > 500 else context
            
            # Extract keywords từ context để tạo document text tốt hơn
            # Tìm các từ khóa quan trọng về du lịch
            keywords = []
            tourism_keywords = re.findall(r'\b(?:di tích|thắng cảnh|du lịch|ẩm thực|văn hóa|lịch sử|di sản|đặc sản|khách sạn|resort|bãi biển|hang động|núi|thác|đảo|chùa|đền|lăng|bảo tàng|công viên|vườn quốc gia)\b', context, re.IGNORECASE)
            keywords.extend(set(tourism_keywords))
            
            destination = {
                'name': name,
                'city': city or 'Vietnam',  # Default to Vietnam nếu không tìm thấy
                'category': category,
                'description': description,
                'full_context': context,  # Giữ nguyên full context để search tốt hơn
                'title': title,
                'keywords': keywords,
                'source': 'kaggle_vietnam_tourism_v2'
            }
            
            destinations.append(destination)
            doc_id += 1
    
    logger.info(f"Extracted {len(destinations)} destinations from dataset")
    return destinations


def download_dataset(url: str, output_path: Path) -> bool:
    """Download dataset từ URL"""
    try:
        logger.info(f"Downloading dataset from {url[:100]}...")
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        progress = (downloaded / total_size) * 100
                        if downloaded % (1024 * 1024) == 0:  # Log mỗi MB
                            logger.info(f"Downloaded {downloaded / (1024*1024):.1f} MB / {total_size / (1024*1024):.1f} MB ({progress:.1f}%)")
        
        logger.info(f"✅ Downloaded dataset to {output_path}")
        return True
    except Exception as e:
        logger.error(f"❌ Error downloading dataset: {e}")
        return False


def load_dataset_to_vector_db(json_path: Optional[Path] = None, 
                               download_url: Optional[str] = None,
                               batch_size: int = 100):
    """
    Load dataset vào Vector DB
    
    Args:
        json_path: Path đến JSON file (nếu None, sẽ download)
        download_url: URL để download dataset
        batch_size: Batch size cho việc add vào Vector DB
    """
    # Initialize Vector DB agent
    logger.info("Initializing Vector DB agent...")
    vector_db = get_vector_db_agent()
    
    if not vector_db.collection:
        logger.error("❌ Vector DB collection not available!")
        return False
    
    # Download dataset nếu chưa có
    if json_path is None or not json_path.exists():
        if download_url:
            json_path = Path(__file__).parent.parent / "data" / "train_vietnam_tourism.json"
            json_path.parent.mkdir(exist_ok=True)
            
            if not download_dataset(download_url, json_path):
                return False
        else:
            logger.error("❌ No JSON path provided and no download URL!")
            return False
    
    # Load và parse JSON
    logger.info(f"Loading JSON from {json_path}...")
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        logger.error(f"❌ Error loading JSON: {e}")
        return False
    
    # Extract destinations
    logger.info("Extracting destinations from dataset...")
    destinations = extract_destinations_from_json(data)
    
    if not destinations:
        logger.warning("⚠️ No destinations extracted!")
        return False
    
    # Add to Vector DB using the new method
    logger.info(f"Adding {len(destinations)} destinations to Vector DB...")
    
    success = vector_db.add_places_from_json(destinations, batch_size=batch_size)
    
    if success:
        # Get stats
        stats = vector_db.get_database_stats()
        logger.info(f"\n✅ Successfully loaded dataset!")
        logger.info(f"   Total documents in Vector DB: {stats.get('total_documents', 0)}")
        logger.info(f"   Cities: {len(stats.get('cities', []))}")
        logger.info(f"   Categories: {len(stats.get('categories', []))}")
    
    return success


if __name__ == "__main__":
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("="*80)
    print("LOADING KAGGLE VIETNAM TOURISM V2 DATASET INTO VECTOR DB")
    print("="*80)
    print()
    
    # Check if dataset file exists locally
    data_dir = Path(__file__).resolve().parent.parent / "data"
    json_path = data_dir / "train_vietnam_tourism.json"
    
    if json_path.exists():
        print(f"📁 Found existing dataset: {json_path}")
        response = input("   Use existing file? (y/n): ").strip().lower()
        if response != 'y':
            json_path = None
    else:
        json_path = None
    
    # Load dataset
    success = load_dataset_to_vector_db(
        json_path=json_path,
        download_url=DATASET_URL if json_path is None else None,
        batch_size=100
    )
    
    if success:
        print("\n" + "="*80)
        print("✅ DATASET LOADED SUCCESSFULLY!")
        print("="*80)
    else:
        print("\n" + "="*80)
        print("❌ FAILED TO LOAD DATASET")
        print("="*80)
        sys.exit(1)

