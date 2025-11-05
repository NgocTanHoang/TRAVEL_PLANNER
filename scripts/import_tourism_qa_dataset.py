"""
Script để import bộ dữ liệu Q&A về Du lịch Việt Nam từ Kaggle
vào Vector Database (ChromaDB) để RAG Agent sử dụng.

Dataset: Vietnam Tourism Q&A Dataset
URL: https://www.kaggle.com/datasets/...
"""
import json
import logging
import asyncio
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agents.travel_agents.vector_db import VectorDatabaseAgent
from agents.base_agent import BaseAgent

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TourismQAIngestor:
    """Ingest Vietnam Tourism Q&A dataset into Vector DB."""
    
    def __init__(self):
        self.vector_db = VectorDatabaseAgent()
        self.collection_name = "vietnam_tourism_qa"
    
    def download_dataset(self, url: str, output_path: Path) -> bool:
        """Download dataset from URL."""
        try:
            import requests
            
            logger.info(f"Downloading dataset from: {url[:80]}...")
            response = requests.get(url, stream=True, timeout=30)
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
                            if downloaded % (1024 * 1024) == 0:  # Log every MB
                                logger.info(f"Downloaded: {downloaded / (1024*1024):.1f} MB ({progress:.1f}%)")
            
            logger.info(f"Downloaded dataset to: {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error downloading dataset: {e}")
            return False
    
    def parse_dataset(self, json_path: Path) -> List[Dict[str, Any]]:
        """Parse JSON dataset and extract contexts, questions, and answers."""
        logger.info(f"Parsing dataset from: {json_path}")
        
        documents = []
        
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Dataset structure: {"data": [{"title": "...", "paragraphs": [...]}]}
            dataset_data = data.get('data', [])
            
            total_contexts = 0
            total_qa_pairs = 0
            
            for topic in dataset_data:
                title = topic.get('title', 'Unknown Topic')
                paragraphs = topic.get('paragraphs', [])
                
                for para_idx, paragraph in enumerate(paragraphs):
                    context = paragraph.get('context', '').strip()
                    qas = paragraph.get('qas', [])
                    
                    if not context:
                        continue
                    
                    total_contexts += 1
                    
                    # Create document for context with unique ID
                    topic_safe = title[:30].replace(' ', '_').replace('/', '_')
                    context_id = f"context_{topic_safe}_{para_idx}"
                    
                    context_doc = {
                        'id': context_id,
                        'text': context,
                        'metadata': {
                            'type': 'context',
                            'topic': title,
                            'paragraph_index': para_idx,
                            'source': 'vietnam_tourism_qa',
                            'qa_pairs_count': len(qas)
                        }
                    }
                    documents.append(context_doc)
                    
                    # Create documents for Q&A pairs
                    for qa_idx, qa in enumerate(qas):
                        question = qa.get('question', '').strip()
                        answers = qa.get('answers', [])
                        qa_id = qa.get('id', f'qa_{para_idx}_{qa_idx}')
                        
                        if not question or not answers:
                            continue
                        
                        total_qa_pairs += 1
                        
                        # Combine question and answers
                        answer_text = answers[0].get('text', '').strip() if answers else ''
                        
                        # Create a document that combines question and answer
                        qa_text = f"Câu hỏi: {question}\n\nCâu trả lời: {answer_text}"
                        if context:
                            qa_text = f"{qa_text}\n\nNgữ cảnh: {context[:500]}"
                        
                        # Create unique ID by combining topic, paragraph, and QA index
                        unique_id = f"qa_{title[:20].replace(' ', '_')}_{para_idx}_{qa_idx}"
                        
                        qa_doc = {
                            'id': unique_id,
                            'text': qa_text,
                            'metadata': {
                                'type': 'qa_pair',
                                'topic': title,
                                'question': question,
                                'answer': answer_text,
                                'answer_start': answers[0].get('answer_start', 0) if answers else 0,
                                'source': 'vietnam_tourism_qa',
                                'context_id': context_doc['id'],
                                'qa_id': qa_id  # Keep original ID in metadata
                            }
                        }
                        documents.append(qa_doc)
            
            logger.info(f"Parsed: {total_contexts} contexts, {total_qa_pairs} Q&A pairs")
            logger.info(f"Total documents: {len(documents)}")
            
            return documents
            
        except Exception as e:
            logger.error(f"Error parsing dataset: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def normalize_vietnamese_text(self, text: str) -> str:
        """Normalize Vietnamese text to ensure proper diacritics."""
        if not text or not isinstance(text, str):
            return text
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Common corrections
        replacements = {
            'Viet Nam': 'Việt Nam',
            'TP.HCM': 'TP. Hồ Chí Minh',
            'Ha Noi': 'Hà Nội',
            'Da Nang': 'Đà Nẵng',
            'Hue': 'Huế',
            'Hoi An': 'Hội An',
            'Sapa': 'Sa Pa',
            'Da Lat': 'Đà Lạt',
            'Phu Quoc': 'Phú Quốc',
        }
        
        for eng, vn in replacements.items():
            text = text.replace(eng, vn)
        
        return text
    
    async def ingest_to_vector_db(self, documents: List[Dict[str, Any]], batch_size: int = 100):
        """Ingest documents into ChromaDB vector database."""
        logger.info(f"Ingesting {len(documents)} documents into vector database...")
        
        # Normalize text
        for doc in documents:
            if 'text' in doc:
                doc['text'] = self.normalize_vietnamese_text(doc['text'])
        
        try:
            # Get or create collection
            try:
                collection = self.vector_db.client.get_collection(self.collection_name)
                logger.info(f"Using existing collection: {self.collection_name}")
            except:
                collection = self.vector_db.client.create_collection(
                    name=self.collection_name,
                    metadata={"description": "Vietnam Tourism Q&A Dataset"}
                )
                logger.info(f"Created new collection: {self.collection_name}")
            
            # Batch processing
            total_batches = (len(documents) + batch_size - 1) // batch_size
            ingested = 0
            
            for batch_idx in range(0, len(documents), batch_size):
                batch = documents[batch_idx:batch_idx + batch_size]
                
                # Prepare data for ChromaDB
                ids = [doc['id'] for doc in batch]
                texts = [doc['text'] for doc in batch]
                metadatas = [doc.get('metadata', {}) for doc in batch]
                
                # Add to collection
                collection.add(
                    ids=ids,
                    documents=texts,
                    metadatas=metadatas
                )
                
                ingested += len(batch)
                current_batch = (batch_idx // batch_size) + 1
                logger.info(f"Batch {current_batch}/{total_batches}: Ingested {ingested}/{len(documents)} documents")
            
            logger.info(f"✓ Successfully ingested {ingested} documents into '{self.collection_name}' collection")
            
            # Get collection stats
            count = collection.count()
            logger.info(f"Total documents in collection: {count}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error ingesting to vector DB: {e}")
            import traceback
            traceback.print_exc()
            return False


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Import Vietnam Tourism Q&A dataset to Vector DB')
    parser.add_argument(
        '--url',
        type=str,
        default='https://storage.googleapis.com/kagglesdsdata/datasets/8477459/13364342/train_vietnam_tourism.json',
        help='URL to download dataset'
    )
    parser.add_argument(
        '--file',
        type=str,
        default=None,
        help='Path to local JSON file (skip download if provided)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/tourism_qa_dataset.json',
        help='Output path for downloaded file'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Batch size for ingestion'
    )
    
    args = parser.parse_args()
    
    ingestor = TourismQAIngestor()
    
    # Step 1: Download dataset if needed
    json_path = Path(args.output)
    if args.file:
        json_path = Path(args.file)
    elif not json_path.exists():
        json_path.parent.mkdir(parents=True, exist_ok=True)
        if not ingestor.download_dataset(args.url, json_path):
            logger.error("Failed to download dataset")
            sys.exit(1)
    
    # Step 2: Parse dataset
    documents = ingestor.parse_dataset(json_path)
    if not documents:
        logger.error("Failed to parse dataset or dataset is empty")
        sys.exit(1)
    
    # Step 3: Ingest to vector DB
    success = await ingestor.ingest_to_vector_db(documents, batch_size=args.batch_size)
    
    if success:
        logger.info("\n" + "="*70)
        logger.info("  [SUCCESS] Dataset imported to Vector DB!")
        logger.info("="*70)
        logger.info(f"\nCollection: {ingestor.collection_name}")
        logger.info(f"Documents: {len(documents):,}")
        logger.info("\nThe RAG agent can now use this data for answering questions.")
        sys.exit(0)
    else:
        logger.error("\n[ERROR] Failed to import dataset")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

