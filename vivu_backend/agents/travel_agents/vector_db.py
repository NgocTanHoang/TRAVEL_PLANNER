"""
Vector Database Agent - RAG System
===================================
Agent quản lý Vector Database cho semantic search
Sử dụng ChromaDB + OpenAI Embeddings
"""

import pandas as pd
from typing import List, Dict, Any, Optional
import os
from pathlib import Path
import json
import unicodedata
import logging
import threading
import asyncio

from ..base_agent import BaseAgent

logger = logging.getLogger(__name__)

# Lazy import ChromaDB to avoid encoding issues on import
try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except Exception as e:
    logger.warning(f"ChromaDB not available: {e}")
    chromadb = None
    Settings = None
    CHROMADB_AVAILABLE = False


class VectorDatabaseAgent(BaseAgent):
    """
    Agent quản lý Vector Database với ChromaDB
    
    Thread-safe: Sử dụng lock để đảm bảo ChromaDB operations không bị concurrent access
    Async-safe: Tất cả ChromaDB operations được wrap trong sync_to_async
    """
    
    # Thread lock để đảm bảo thread-safe access cho ChromaDB
    _chromadb_lock = threading.Lock()
    
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
        super().__init__(
            agent_name="vector_db_agent",
            description="Vector database agent for semantic search"
        )
        self.persist_dir = Path(persist_directory)
        self.persist_dir.mkdir(exist_ok=True)
        
        # Initialize ChromaDB client (lazy)
        self.client = None
        self.collection = None
        
        if CHROMADB_AVAILABLE:
            try:
                self.client = chromadb.PersistentClient(
                    path=str(self.persist_dir),
                    settings=Settings(anonymized_telemetry=False)
                )
            except Exception as e:
                logger.error(f"Failed to initialize ChromaDB client: {e}")
                self.client = None
        
        # Collection name
        self.collection_name = "vietnam_places"
        
        # Get or create collection (if client available)
        if self.client:
            try:
                self.collection = self.client.get_collection(name=self.collection_name)
                logger.info(f"Loaded existing collection: {self.collection_name}")
                logger.info(f"   Documents: {self.collection.count()}")
            except:
                logger.info(f"Creating new collection: {self.collection_name}")
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    metadata={"hnsw:space": "cosine"}
                )
        else:
            logger.warning("ChromaDB client not available, vector search will be disabled")
    
    def add_places_from_csv(self, csv_path: str, batch_size: int = 100):
        """
        Thêm places từ CSV vào Vector Database
        
        Args:
            csv_path: Path đến CSV file
            batch_size: Số lượng documents mỗi batch
        """
        print(f"[LOAD] Loading data from {csv_path}...")
        
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
                
                # Add batch when reached batch_size - thread-safe
                if len(documents) >= batch_size:
                    with self._chromadb_lock:
                        self.collection.add(
                            documents=documents,
                            metadatas=metadatas,
                            ids=ids
                        )
                    print(f"   [OK] Added batch: {len(ids)} documents")
                    documents, metadatas, ids = [], [], []
            
            # Add remaining documents - thread-safe
            if documents:
                with self._chromadb_lock:
                    self.collection.add(
                        documents=documents,
                        metadatas=metadatas,
                        ids=ids
                    )
                print(f"   [OK] Added final batch: {len(ids)} documents")
            
            print(f"[OK] Successfully added {df.shape[0]} places to vector database")
            
        except Exception as e:
            print(f"❌ Error adding places: {e}")
    
    def add_places_from_json(self, json_data: List[Dict[str, Any]], batch_size: int = 100):
        """
        Thêm places từ JSON data vào Vector Database
        
        Args:
            json_data: List of dictionaries với các keys: name, city, category, description, etc.
            batch_size: Số lượng documents mỗi batch
        """
        if not self.collection:
            logger.error("Vector DB collection not available")
            return False
        
        print(f"[LOAD] Loading {len(json_data)} places from JSON data...")
        
        try:
            documents = []
            metadatas = []
            ids = []
            
            for idx, place_data in enumerate(json_data):
                # Normalize city name
                city = place_data.get('city', 'Vietnam')
                normalized_city = self._normalize_city_name(city)
                
                # Create document text
                doc_parts = []
                if place_data.get('name'):
                    doc_parts.append(f"Tên: {place_data['name']}")
                if normalized_city:
                    doc_parts.append(f"Thành phố: {normalized_city}")
                if place_data.get('category'):
                    doc_parts.append(f"Loại: {place_data['category']}")
                if place_data.get('description'):
                    doc_parts.append(f"Mô tả: {place_data['description']}")
                if place_data.get('keywords'):
                    keywords = place_data['keywords']
                    if isinstance(keywords, list):
                        doc_parts.append(f"Từ khóa: {', '.join(keywords[:10])}")
                    else:
                        doc_parts.append(f"Từ khóa: {keywords}")
                
                # Add full context if available
                if place_data.get('full_context'):
                    context_snippet = place_data['full_context'][:300]
                    doc_parts.append(f"Chi tiết: {context_snippet}")
                
                doc_text = ". ".join(doc_parts)
                
                # Create metadata
                metadata = {
                    'name': str(place_data.get('name', ''))[:200],
                    'city': normalized_city,
                    'category': str(place_data.get('category', 'attraction')),
                    'rating': float(place_data.get('rating', 0)),
                    'price': float(place_data.get('price', 0)),
                    'price_level': int(place_data.get('price_level', 0)),
                    'latitude': float(place_data.get('latitude', 0)) if place_data.get('latitude') else None,
                    'longitude': float(place_data.get('longitude', 0)) if place_data.get('longitude') else None,
                    'description': str(place_data.get('description', ''))[:500],
                    'source': str(place_data.get('source', 'json')),
                    'title': str(place_data.get('title', ''))[:200] if place_data.get('title') else '',
                    'image_url': str(place_data.get('image_url', ''))[:500] if place_data.get('image_url') else None,
                    'province': str(place_data.get('province', ''))[:100] if place_data.get('province') else None
                }
                
                documents.append(doc_text)
                metadatas.append(metadata)
                ids.append(f"json_{place_data.get('source', 'json')}_{idx}")
                
                # Add batch when reached batch_size - thread-safe
                if len(documents) >= batch_size:
                    try:
                        with self._chromadb_lock:
                            self.collection.add(
                                documents=documents,
                                metadatas=metadatas,
                                ids=ids
                            )
                        print(f"   [OK] Added batch: {len(ids)} documents")
                        documents, metadatas, ids = [], [], []
                    except Exception as e:
                        logger.error(f"Error adding batch: {e}")
                        documents, metadatas, ids = [], [], []
            
            # Add remaining documents - thread-safe
            if documents:
                try:
                    with self._chromadb_lock:
                        self.collection.add(
                            documents=documents,
                            metadatas=metadatas,
                            ids=ids
                        )
                    print(f"   [OK] Added final batch: {len(ids)} documents")
                except Exception as e:
                    logger.error(f"Error adding final batch: {e}")
            
            print(f"[OK] Successfully added {len(json_data)} places to vector database")
            return True
            
        except Exception as e:
            logger.error(f"Error adding places from JSON: {e}")
            return False
    
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
    
    def _semantic_search_sync(
        self, 
        query: str, 
        n_results: int = 10,
        city_filter: Optional[str] = None,
        category_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Synchronous semantic search - thread-safe với lock
        
        Args:
            query: Query text
            n_results: Số lượng kết quả
            city_filter: Lọc theo thành phố
            category_filter: Lọc theo category
        
        Returns:
            List of matching places
        """
        if not self.collection:
            logger.warning("Vector DB collection not available, returning empty results")
            return []
        
        # Thread-safe access với lock
        with self._chromadb_lock:
            try:
                # Build where clause for filtering
                where = None
                if city_filter:
                    normalized_city = self._normalize_city_name(city_filter)
                    where = {"city": {"$eq": normalized_city}}
                
                # Query vector database (blocking I/O)
                results = self.collection.query(
                    query_texts=[query],
                    n_results=n_results,
                    where=where
                )
                
                # KHÔNG retry không có filter - chỉ trả về kết quả đúng city
                # Nếu không có kết quả với city filter, log warning và trả về empty
                if not results or not results.get('metadatas') or len(results['metadatas'][0]) == 0:
                    if where:
                        logger.warning(f"No results with city filter '{normalized_city}' for query '{query}'. Returning empty results to avoid wrong city matches.")
                        # Trả về empty thay vì retry không có filter
                        return []
                
                # Format results
                places = []
                if results and results.get('metadatas') and len(results['metadatas'][0]) > 0:
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
                            'similarity_score': 1 - results['distances'][0][i] if results.get('distances') and len(results['distances'][0]) > i else 0,
                            'image_url': metadata.get('image_url'),
                            'province': metadata.get('province'),
                            'source': metadata.get('source', '')
                        }
                        places.append(place)
                
                return places
                
            except Exception as e:
                logger.error(f"Error in semantic search: {e}", exc_info=True)
                return []
    
    def semantic_search(
        self, 
        query: str, 
        n_results: int = 10,
        city_filter: Optional[str] = None,
        category_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Semantic search - sync method (backward compatible)
        Sử dụng _semantic_search_sync với thread-safe lock
        """
        return self._semantic_search_sync(query, n_results, city_filter, category_filter)
    
    async def semantic_search_async(
        self, 
        query: str, 
        n_results: int = 10,
        city_filter: Optional[str] = None,
        category_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Async semantic search - safe for async context
        Wraps sync method trong asyncio.to_thread để tránh blocking event loop
        """
        try:
            # Chạy sync method trong thread pool để không block event loop
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._semantic_search_sync,
                query,
                n_results,
                city_filter,
                category_filter
            )
            return result
        except Exception as e:
            logger.error(f"Error in async semantic search: {e}", exc_info=True)
            return []
    
    def _get_recommendations_sync(
        self,
        destination: str,
        interests: str,
        budget: int,
        days: int,
        travelers: int = 1,
        n_results: int = 20
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Synchronous get_recommendations - thread-safe
        
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
        results = {
            'hotels': [],
            'restaurants': [],
            'attractions': []
        }
        
        # Search hotels
        results['hotels'] = self._semantic_search_sync(
            query=f"Khách sạn hotel resort tại {destination}. Ngân sách {budget} VND. Phù hợp {travelers} người.",
            n_results=n_results,
            city_filter=destination
        )
        
        # Search restaurants
        results['restaurants'] = self._semantic_search_sync(
            query=f"Nhà hàng restaurant quán ăn tại {destination}. Ẩm thực {interests}. Đặc sản địa phương.",
            n_results=n_results,
            city_filter=destination
        )
        
        # Search attractions
        results['attractions'] = self._semantic_search_sync(
            query=f"Điểm tham quan attraction du lịch tại {destination}. Hoạt động {interests}. Văn hóa lịch sử.",
            n_results=n_results,
            city_filter=destination
        )
        
        return results
    
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
        Get recommendations - sync method (backward compatible)
        """
        return self._get_recommendations_sync(destination, interests, budget, days, travelers, n_results)
    
    async def get_recommendations_async(
        self,
        destination: str,
        interests: str,
        budget: int,
        days: int,
        travelers: int = 1,
        n_results: int = 20
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Async get_recommendations - safe for async context
        """
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                self._get_recommendations_sync,
                destination,
                interests,
                budget,
                days,
                travelers,
                n_results
            )
            return result
        except Exception as e:
            logger.error(f"Error in async get_recommendations: {e}", exc_info=True)
            return {'hotels': [], 'restaurants': [], 'attractions': []}
    
    def query(self, namespace: str, embedding: List[float], top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Query vector database by embedding.
        
        Args:
            namespace: Namespace/collection name (unused, using default collection)
            embedding: Query embedding vector
            top_k: Number of results
        
        Returns:
            List of document dictionaries
        """
        try:
            self.log_input({'namespace': namespace, 'top_k': top_k})
            
            # Note: ChromaDB uses query_texts, not embeddings directly
            # This method is kept for API compatibility
            # For embedding-based queries, use semantic_search with query text
            logger.warning("query() with embeddings not directly supported, use semantic_search()")
            
            # Fallback: return empty results
            return []
        
        except Exception as e:
            self.log_error(e, context={'namespace': namespace})
            return []
    
    def get_documents(self, ids: List[str]) -> List[Dict[str, Any]]:
        """
        Get documents by IDs.
        
        Args:
            ids: List of document IDs
        
        Returns:
            List of document dictionaries
        """
        try:
            self.log_input({'ids': ids})
            
            # Get documents from collection - thread-safe
            with self._chromadb_lock:
                results = self.collection.get(ids=ids)
            
            documents = []
            if results and results.get('metadatas'):
                for i, metadata in enumerate(results['metadatas']):
                    doc = {
                        'id': results['ids'][i] if results.get('ids') else f"doc_{i}",
                        'metadata': metadata,
                        'content': results['documents'][i] if results.get('documents') else ''
                    }
                    documents.append(doc)
            
            self.log_output({'doc_count': len(documents)})
            return documents
        
        except Exception as e:
            self.log_error(e, context={'ids': ids})
            return []
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Lấy statistics của database"""
        if not self.collection:
            return {
                'total_documents': 0,
                'cities': [],
                'categories': [],
                'collection_name': self.collection_name,
                'status': 'unavailable'
            }
        
        try:
            count = self.collection.count()
            
            # Sample some documents to get city/category distribution
            # Thread-safe access với lock
            with self._chromadb_lock:
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

def get_vector_db_agent() -> Optional[VectorDatabaseAgent]:
    """Get singleton instance of Vector DB Agent.

    Được harden để nếu ChromaDB hoặc Rust backend bị panic (PanicException)
    thì không làm crash toàn bộ process. Trong trường hợp lỗi, hàm sẽ log và
    trả về None để caller có thể gracefully tắt tính năng vector search.
    """
    global vector_db_agent
    if vector_db_agent is None:
        try:
            vector_db_agent = VectorDatabaseAgent()
        except BaseException as e:
            # Bắt rộng để catch cả PanicException từ chromadb_rust_bindings
            logger.warning(f"Vector DB agent initialization failed: {type(e).__name__}: {e}")
            vector_db_agent = None
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
    print(f"\n[STATS] Database Stats:")
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
    print("[OK] Test completed!")

