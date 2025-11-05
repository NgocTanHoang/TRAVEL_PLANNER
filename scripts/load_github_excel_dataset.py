"""
Script để tải và load dataset landmarks & attractions từ GitHub vào Vector DB
==============================================================================
Dataset: https://github.com/HongTin2104/VietNam-Travel-Recommendation-System/blob/main/data/DataSet.xlsx
63 tỉnh thành Việt Nam với landmarks và attractions
"""

import pandas as pd
import requests
from pathlib import Path
import sys
import os
from typing import List, Dict, Any, Optional
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agents.travel_agents.vector_db import get_vector_db_agent

logger = logging.getLogger(__name__)

# URL của dataset (raw GitHub URL)
DATASET_URL = "https://raw.githubusercontent.com/HongTin2104/VietNam-Travel-Recommendation-System/main/data/DataSet.xlsx"

# Map Vietnamese province names to normalized names
PROVINCE_MAP = {
    'hà nội': 'Hanoi',
    'hồ chí minh': 'Ho Chi Minh City',
    'tp hồ chí minh': 'Ho Chi Minh City',
    'tp.hcm': 'Ho Chi Minh City',
    'sài gòn': 'Ho Chi Minh City',
    'đà nẵng': 'Da Nang',
    'hải phòng': 'Hai Phong',
    'cần thơ': 'Can Tho',
    'hà giang': 'Ha Giang',
    'cao bằng': 'Cao Bang',
    'lào cai': 'Lao Cai',
    'sapa': 'Sapa',
    'điện biên': 'Dien Bien',
    'lai châu': 'Lai Chau',
    'sơn la': 'Son La',
    'yên bái': 'Yen Bai',
    'hoà bình': 'Hoa Binh',
    'thái nguyên': 'Thai Nguyen',
    'lạng sơn': 'Lang Son',
    'quảng ninh': 'Quang Ninh',
    'hạ long': 'Ha Long',
    'cát bà': 'Cat Ba',
    'bắc giang': 'Bac Giang',
    'phú thọ': 'Phu Tho',
    'vĩnh phúc': 'Vinh Phuc',
    'bắc ninh': 'Bac Ninh',
    'hải dương': 'Hai Duong',
    'hưng yên': 'Hung Yen',
    'thái bình': 'Thai Binh',
    'hà nam': 'Ha Nam',
    'nam định': 'Nam Dinh',
    'ninh bình': 'Ninh Binh',
    'thanh hóa': 'Thanh Hoa',
    'nghệ an': 'Nghe An',
    'hà tĩnh': 'Ha Tinh',
    'quảng bình': 'Quang Binh',
    'quảng trị': 'Quang Tri',
    'huế': 'Hue',
    'thừa thiên huế': 'Thua Thien Hue',
    'quảng nam': 'Quang Nam',
    'hội an': 'Hoi An',
    'quảng ngãi': 'Quang Ngai',
    'bình định': 'Binh Dinh',
    'quy nhơn': 'Quy Nhon',
    'phú yên': 'Phu Yen',
    'khánh hòa': 'Khanh Hoa',
    'nha trang': 'Nha Trang',
    'ninh thuận': 'Ninh Thuan',
    'bình thuận': 'Binh Thuan',
    'phan thiết': 'Phan Thiet',
    'mũi né': 'Mui Ne',
    'kon tum': 'Kon Tum',
    'gia lai': 'Gia Lai',
    'đắk lắk': 'Dak Lak',
    'đăk lăk': 'Dak Lak',
    'đắk nông': 'Dak Nong',
    'đăk nông': 'Dak Nong',
    'lâm đồng': 'Lam Dong',
    'đà lạt': 'Da Lat',
    'bình phước': 'Binh Phuoc',
    'tây ninh': 'Tay Ninh',
    'bình dương': 'Binh Duong',
    'đồng nai': 'Dong Nai',
    'bà rịa - vũng tàu': 'Ba Ria - Vung Tau',
    'ba ria vung tau': 'Ba Ria - Vung Tau',
    'vũng tàu': 'Vung Tau',
    'côn đảo': 'Con Dao',
    'long an': 'Long An',
    'tiền giang': 'Tien Giang',
    'bến tre': 'Ben Tre',
    'trà vinh': 'Tra Vinh',
    'vĩnh long': 'Vinh Long',
    'đồng tháp': 'Dong Thap',
    'an giang': 'An Giang',
    'kiên giang': 'Kien Giang',
    'hậu giang': 'Hau Giang',
    'sóc trăng': 'Soc Trang',
    'bạc liêu': 'Bac Lieu',
    'cà mau': 'Ca Mau',
    'phú quốc': 'Phu Quoc',
}


def normalize_province_name(province: str) -> str:
    """Normalize province name"""
    if not province:
        return 'Vietnam'
    
    province_lower = province.lower().strip()
    return PROVINCE_MAP.get(province_lower, province.title())


def infer_category_from_data(name: str, description: str = '') -> str:
    """Infer category từ name và description"""
    text = f"{name} {description}".lower()
    
    # Keywords for categorization
    if any(kw in text for kw in ['khách sạn', 'resort', 'hotel', 'homestay', 'nghỉ dưỡng', 'lưu trú']):
        return 'hotel'
    elif any(kw in text for kw in ['nhà hàng', 'quán ăn', 'ẩm thực', 'đặc sản', 'món ăn', 'cafe', 'cà phê']):
        return 'restaurant'
    else:
        return 'attraction'  # Default cho landmarks và attractions


def download_excel_dataset(url: str, output_path: Path) -> bool:
    """Download Excel dataset từ URL"""
    try:
        logger.info(f"Downloading Excel dataset from {url}...")
        response = requests.get(url, stream=True, timeout=300)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0 and downloaded % (1024 * 1024) == 0:  # Log mỗi MB
                        progress = (downloaded / total_size) * 100
                        logger.info(f"Downloaded {downloaded / (1024*1024):.1f} MB / {total_size / (1024*1024):.1f} MB ({progress:.1f}%)")
        
        logger.info(f"✅ Downloaded dataset to {output_path}")
        return True
    except Exception as e:
        logger.error(f"❌ Error downloading dataset: {e}")
        return False


def parse_excel_dataset(excel_path: Path) -> List[Dict[str, Any]]:
    """
    Parse Excel file và extract landmarks/attractions
    
    Args:
        excel_path: Path đến Excel file
        
    Returns:
        List of destination dictionaries
    """
    try:
        logger.info(f"Reading Excel file: {excel_path}")
        
        # Read Excel file
        df = pd.read_excel(excel_path, engine='openpyxl')
        
        logger.info(f"   Found {len(df)} rows")
        logger.info(f"   Columns: {list(df.columns)}")
        
        # Display first few rows to understand structure
        if len(df) > 0:
            logger.info(f"\n   Sample row:")
            for col in df.columns[:5]:  # Show first 5 columns
                logger.info(f"      {col}: {df.iloc[0].get(col, 'N/A')}")
        
        destinations = []
        
        # Common column name mappings (cần điều chỉnh dựa trên actual structure)
        name_cols = ['name', 'ten', 'tên', 'landmark', 'attraction', 'diadiem', 'địa điểm']
        province_cols = ['province', 'tinh', 'tỉnh', 'thanhpho', 'thành phố', 'city']
        description_cols = ['description', 'mota', 'mô tả', 'detail', 'chi tiết', 'info']
        image_cols = ['image', 'anh', 'ảnh', 'picture', 'photo', 'url', 'link']
        lat_cols = ['lat', 'latitude', 'vido', 'vĩ độ']
        lon_cols = ['lon', 'longitude', 'kinhdo', 'kinh độ', 'long']
        
        # Find actual column names
        name_col = None
        province_col = None
        description_col = None
        image_col = None
        lat_col = None
        lon_col = None
        
        for col in df.columns:
            col_lower = str(col).lower()
            if not name_col and any(nc in col_lower for nc in name_cols):
                name_col = col
            if not province_col and any(pc in col_lower for pc in province_cols):
                province_col = col
            if not description_col and any(dc in col_lower for dc in description_cols):
                description_col = col
            if not image_col and any(ic in col_lower for ic in image_cols):
                image_col = col
            if not lat_col and any(lc in col_lower for lc in lat_cols):
                lat_col = col
            if not lon_col and any(loc in col_lower for loc in lon_cols):
                lon_col = col
        
        logger.info(f"\n   Detected columns:")
        logger.info(f"      Name: {name_col}")
        logger.info(f"      Province: {province_col}")
        logger.info(f"      Description: {description_col}")
        logger.info(f"      Image: {image_col}")
        logger.info(f"      Latitude: {lat_col}")
        logger.info(f"      Longitude: {lon_col}")
        
        # Extract destinations
        for idx, row in df.iterrows():
            name = str(row.get(name_col, '')).strip() if name_col else f"Địa điểm {idx + 1}"
            province = str(row.get(province_col, '')).strip() if province_col else ''
            description = str(row.get(description_col, '')).strip() if description_col else ''
            image_url = str(row.get(image_col, '')).strip() if image_col else None
            
            # Extract coordinates
            latitude = None
            longitude = None
            if lat_col and pd.notna(row.get(lat_col)):
                try:
                    latitude = float(row[lat_col])
                except (ValueError, TypeError):
                    pass
            if lon_col and pd.notna(row.get(lon_col)):
                try:
                    longitude = float(row[lon_col])
                except (ValueError, TypeError):
                    pass
            
            # Skip empty rows
            if not name or name == 'nan' or name.lower() in ['n/a', 'none', '']:
                continue
            
            # Normalize province
            normalized_province = normalize_province_name(province) if province else 'Vietnam'
            
            # Infer category
            category = infer_category_from_data(name, description)
            
            destination = {
                'name': name,
                'city': normalized_province,
                'province': province,  # Keep original province name
                'category': category,
                'description': description[:500] if description else '',  # Limit description
                'full_description': description,  # Keep full description for search
                'image_url': image_url,
                'latitude': latitude,
                'longitude': longitude,
                'source': 'github_vietnam_travel_recommendation',
                'rating': 0.0,  # Dataset có thể không có rating
                'price': 0.0,
                'price_level': 0
            }
            
            destinations.append(destination)
        
        logger.info(f"✅ Extracted {len(destinations)} destinations from Excel")
        return destinations
        
    except Exception as e:
        logger.error(f"❌ Error parsing Excel: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return []


def load_excel_dataset_to_vector_db(excel_path: Optional[Path] = None,
                                     download_url: Optional[str] = None,
                                     batch_size: int = 100):
    """
    Load Excel dataset vào Vector DB
    
    Args:
        excel_path: Path đến Excel file (nếu None, sẽ download)
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
    if excel_path is None or not excel_path.exists():
        if download_url:
            excel_path = Path(__file__).parent.parent / "data" / "DataSet.xlsx"
            excel_path.parent.mkdir(exist_ok=True)
            
            if not download_excel_dataset(download_url, excel_path):
                return False
        else:
            logger.error("❌ No Excel path provided and no download URL!")
            return False
    
    # Parse Excel
    logger.info("Parsing Excel dataset...")
    destinations = parse_excel_dataset(excel_path)
    
    if not destinations:
        logger.warning("⚠️ No destinations extracted!")
        return False
    
    # Add to Vector DB using the existing method
    logger.info(f"Adding {len(destinations)} destinations to Vector DB...")
    
    # Convert to format compatible with add_places_from_json
    places_data = []
    for dest in destinations:
        place = {
            'name': dest['name'],
            'city': dest['city'],
            'category': dest['category'],
            'description': dest['description'],
            'full_context': dest.get('full_description', dest['description']),
            'latitude': dest.get('latitude'),
            'longitude': dest.get('longitude'),
            'rating': dest.get('rating', 0),
            'price': dest.get('price', 0),
            'price_level': dest.get('price_level', 0),
            'source': dest['source'],
            'image_url': dest.get('image_url'),
            'province': dest.get('province', '')
        }
        places_data.append(place)
    
    success = vector_db.add_places_from_json(places_data, batch_size=batch_size)
    
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
    print("LOADING GITHUB VIETNAM TRAVEL RECOMMENDATION DATASET INTO VECTOR DB")
    print("="*80)
    print()
    
    # Check if dataset file exists locally
    data_dir = Path(__file__).resolve().parent.parent / "data"
    excel_path = data_dir / "DataSet.xlsx"
    
    if excel_path.exists():
        print(f"📁 Found existing dataset: {excel_path}")
        response = input("   Use existing file? (y/n): ").strip().lower()
        if response != 'y':
            excel_path = None
    else:
        excel_path = None
    
    # Load dataset
    success = load_excel_dataset_to_vector_db(
        excel_path=excel_path,
        download_url=DATASET_URL if excel_path is None else None,
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

