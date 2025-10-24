"""
Vector Database Agent - RAG System
===================================
Agent quản lý Vector Database cho semantic search
Sử dụng ChromaDB + OpenAI Embeddings
"""

import chromadb
from chromadb.config import Settings
import pandas as pd
from typing import List, Dict, Any, Optional
import os
from pathlib import Path
import json
import unicodedata


class VectorDatabaseAgent:
    """Agent quản lý Vector Database với ChromaDB"""
    
    # City name mapping (Vietnamese with diacritics -> English)
    # Bao gồm 64 tỉnh thành Việt Nam
    CITY_MAP = {
        # Thành phố lớn
        'hà nội': 'Hanoi',
        'hồ chí minh': 'Ho Chi Minh City',
        'tp hồ chí minh': 'Ho Chi Minh City',
        'tp.hcm': 'Ho Chi Minh City',
        'sài gòn': 'Ho Chi Minh City',
        'đà nẵng': 'Da Nang',
        'hải phòng': 'Hai Phong',
        'cần thơ': 'Can Tho',
        
        # Miền Bắc
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
        'tam đảo': 'Tam Dao',
        'ba vì': 'Ba Vi',
        'tuyên quang': 'Tuyen Quang',
        'bắc kạn': 'Bac Kan',
        
        # Miền Trung
        'thanh hóa': 'Thanh Hoa',
        'nghệ an': 'Nghe An',
        'hà tĩnh': 'Ha Tinh',
        'quảng bình': 'Quang Binh',
        'quảng trị': 'Quang Tri',
        'huế': 'Hue',
        'thừa thiên huế': 'Thua Thien Hue',
        'đà nẵng': 'Da Nang',
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
        
        # Tây Nguyên
        'kon tum': 'Kon Tum',
        'gia lai': 'Gia Lai',
        'đắk lắk': 'Dak Lak',
        'đăk lăk': 'Dak Lak',
        'đắk nông': 'Dak Nong',
        'đăk nông': 'Dak Nong',
        'lâm đồng': 'Lam Dong',
        'đà lạt': 'Da Lat',
        
        # Miền Nam
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
        'cần thơ': 'Can Tho',
        'hậu giang': 'Hau Giang',
        'sóc trăng': 'Soc Trang',
        'bạc liêu': 'Bac Lieu',
        'cà mau': 'Ca Mau',
        'phú quốc': 'Phu Quoc',
    }
    
    def __init__(self, persist_directory: str = "vector_db"):
        """
        Initialize Vector Database Agent
        
        Args:
            persist_directory: Thư mục lưu trữ vector database
        """
        self.persist_dir = Path(persist_directory)
        self.persist_dir.mkdir(exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(self.persist_dir),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # Collection name
        self.collection_name = "vietnam_places"
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(name=self.collection_name)
            print(f"✅ Loaded existing collection: {self.collection_name}")
            print(f"   Documents: {self.collection.count()}")
        except:
            print(f"📦 Creating new collection: {self.collection_name}")
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
    
    def add_places_from_csv(self, csv_path: str, batch_size: int = 100):
        """
        Thêm places từ CSV vào Vector Database
        
        Args:
            csv_path: Path đến CSV file
            batch_size: Số lượng documents mỗi batch
        """
        print(f"📥 Loading data from {csv_path}...")
        
        try:
            df = pd.read_csv(csv_path)
            print(f"   Found {len(df)} places")
            
            # Prepare data
            documents = []
            metadatas = []
            ids = []
            
            for idx, row in df.iterrows():
                # Create document text (for embedding)
                doc_text = self._create_document_text(row)
                
                # Create metadata
                metadata = {
                    'name': str(row.get('name', '')),
                    'city': str(row.get('city', '')),
                    'category': str(row.get('category', '')),
                    'rating': float(row.get('rating', 0)),
                    'price': float(row.get('price', 0)),
                    'price_level': int(row.get('price_level', 0)),
                    'latitude': float(row.get('latitude', 0)) if pd.notna(row.get('latitude')) else None,
                    'longitude': float(row.get('longitude', 0)) if pd.notna(row.get('longitude')) else None,
                    'description': str(row.get('description', ''))[:500]  # Limit length
                }
                
                documents.append(doc_text)
                metadatas.append(metadata)
                ids.append(f"place_{idx}")
                
                # Add batch when reached batch_size
                if len(documents) >= batch_size:
                    self.collection.add(
                        documents=documents,
                        metadatas=metadatas,
                        ids=ids
                    )
                    print(f"   ✅ Added batch: {len(ids)} documents")
                    documents, metadatas, ids = [], [], []
            
            # Add remaining documents
            if documents:
                self.collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
                print(f"   ✅ Added final batch: {len(ids)} documents")
            
            print(f"✅ Successfully added {df.shape[0]} places to vector database")
            
        except Exception as e:
            print(f"❌ Error adding places: {e}")
    
    def _normalize_city_name(self, city: str) -> str:
        """Normalize city name to match database format"""
        if not city:
            return city
        
        # Try exact mapping first
        city_lower = city.lower().strip()
        if city_lower in self.CITY_MAP:
            return self.CITY_MAP[city_lower]
        
        # Return as-is if no mapping found
        return city
    
    def _create_document_text(self, row: pd.Series) -> str:
        """Tạo text document từ row data"""
        parts = []
        
        # Name
        if pd.notna(row.get('name')):
            parts.append(f"Tên: {row['name']}")
        
        # City
        if pd.notna(row.get('city')):
            parts.append(f"Thành phố: {row['city']}")
        
        # Category
        if pd.notna(row.get('category')):
            parts.append(f"Loại: {row['category']}")
        
        # Description
        if pd.notna(row.get('description')):
            parts.append(f"Mô tả: {row['description']}")
        
        # Rating
        if pd.notna(row.get('rating')):
            parts.append(f"Đánh giá: {row['rating']}/5.0")
        
        return ". ".join(parts)
    
    def semantic_search(
        self, 
        query: str, 
        n_results: int = 10,
        city_filter: Optional[str] = None,
        category_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Semantic search trong vector database
        
        Args:
            query: Query text
            n_results: Số lượng kết quả
            city_filter: Lọc theo thành phố
            category_filter: Lọc theo category
        
        Returns:
            List of matching places
        """
        try:
            # Build where clause for filtering
            # Note: Only use city_filter, let semantic search handle category matching
            where = None
            if city_filter:
                # Normalize city name
                normalized_city = self._normalize_city_name(city_filter)
                where = {"city": {"$eq": normalized_city}}
            
            # Query vector database
            results = self.collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where
            )
            
            # Format results
            places = []
            if results and results['metadatas'] and len(results['metadatas'][0]) > 0:
                for i, metadata in enumerate(results['metadatas'][0]):
                    place = {
                        'name': metadata.get('name', ''),
                        'city': metadata.get('city', ''),
                        'category': metadata.get('category', ''),
                        'rating': metadata.get('rating', 0),
                        'price': metadata.get('price', 0),
                        'price_level': metadata.get('price_level', 0),
                        'description': metadata.get('description', ''),
                        'latitude': metadata.get('latitude'),
                        'longitude': metadata.get('longitude'),
                        'similarity_score': 1 - results['distances'][0][i] if results['distances'] else 0
                    }
                    places.append(place)
            
            return places
            
        except Exception as e:
            print(f"❌ Error in semantic search: {e}")
            return []
    
    def get_recommendations(
        self,
        destination: str,
        interests: str,
        budget: int,
        days: int,
        travelers: int = 1,
        n_results: int = 20
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Lấy recommendations cho travel plan
        
        Args:
            destination: Điểm đến
            interests: Sở thích
            budget: Ngân sách
            days: Số ngày
            travelers: Số người đi
            n_results: Số kết quả mỗi category
        
        Returns:
            Dict với hotels, restaurants, attractions
        """
        # Build search query
        query = f"Du lịch {destination}. Sở thích: {interests}. Ngân sách: {budget} VND. {days} ngày. {travelers} người."
        
        results = {
            'hotels': [],
            'restaurants': [],
            'attractions': []
        }
        
        # Search hotels (semantic search will understand "hotel" from query)
        results['hotels'] = self.semantic_search(
            query=f"Khách sạn hotel resort tại {destination}. Ngân sách {budget} VND. Phù hợp {travelers} người.",
            n_results=n_results,
            city_filter=destination
        )
        
        # Search restaurants (semantic search will understand "restaurant" from query)
        results['restaurants'] = self.semantic_search(
            query=f"Nhà hàng restaurant quán ăn tại {destination}. Ẩm thực {interests}. Đặc sản địa phương.",
            n_results=n_results,
            city_filter=destination
        )
        
        # Search attractions (semantic search will understand "attraction" from query)
        results['attractions'] = self.semantic_search(
            query=f"Điểm tham quan attraction du lịch tại {destination}. Hoạt động {interests}. Văn hóa lịch sử.",
            n_results=n_results,
            city_filter=destination
        )
        
        return results
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Lấy statistics của database"""
        try:
            count = self.collection.count()
            
            # Sample some documents to get city/category distribution
            sample = self.collection.get(limit=1000)
            
            cities = set()
            categories = set()
            
            if sample and sample['metadatas']:
                for metadata in sample['metadatas']:
                    if metadata.get('city'):
                        cities.add(metadata['city'])
                    if metadata.get('category'):
                        categories.add(metadata['category'])
            
            return {
                'total_documents': count,
                'cities': list(cities),
                'categories': list(categories),
                'collection_name': self.collection_name
            }
            
        except Exception as e:
            print(f"❌ Error getting stats: {e}")
            return {}


# Global instance
vector_db_agent = None

def get_vector_db_agent() -> VectorDatabaseAgent:
    """Get singleton instance of Vector DB Agent"""
    global vector_db_agent
    if vector_db_agent is None:
        vector_db_agent = VectorDatabaseAgent()
    return vector_db_agent


# Test
if __name__ == "__main__":
    print("="*60)
    print("VECTOR DATABASE AGENT - TEST")
    print("="*60)
    
    # Initialize agent
    agent = VectorDatabaseAgent()
    
    # Get stats
    stats = agent.get_database_stats()
    print(f"\n📊 Database Stats:")
    print(f"   Total documents: {stats.get('total_documents', 0)}")
    print(f"   Cities: {len(stats.get('cities', []))}")
    print(f"   Categories: {len(stats.get('categories', []))}")
    
    # Test search
    print(f"\n🔍 Testing semantic search...")
    results = agent.semantic_search("khách sạn sang trọng ở Hà Nội", n_results=5, city_filter="Hà Nội")
    print(f"   Found {len(results)} results")
    for i, place in enumerate(results[:3], 1):
        print(f"   {i}. {place['name']} - {place['city']} ({place['similarity_score']:.2f})")
    
    # Test recommendations
    print(f"\n🎯 Testing recommendations...")
    recs = agent.get_recommendations(
        destination="Hà Nội",
        interests="văn hóa, ẩm thực",
        budget=10000000,
        days=3,
        travelers=2
    )
    print(f"   Hotels: {len(recs['hotels'])}")
    print(f"   Restaurants: {len(recs['restaurants'])}")
    print(f"   Attractions: {len(recs['attractions'])}")
    
    print("\n" + "="*60)
    print("✅ Test completed!")

