"""
Script để vector hóa TẤT CẢ dữ liệu từ database và thêm vào ChromaDB
=====================================================================
- Lấy tất cả DiaDiem từ database
- Tạo embeddings và thêm vào ChromaDB
- Xử lý batch để tối ưu hiệu suất
- Hiển thị progress chi tiết
"""
import os
import sys
import django
from pathlib import Path
import logging
from typing import List, Dict, Any

# Setup Django
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vivu_core.settings')
django.setup()

from apps.places.models import DiaDiem, TinhThanh
from agents.travel_agents.vector_db import get_vector_db_agent

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_document_text(place: DiaDiem) -> str:
    """
    Tạo text document từ DiaDiem model để embedding
    
    Args:
        place: DiaDiem instance
        
    Returns:
        Document text string
    """
    parts = []
    
    # Tên địa điểm
    if place.tenDiaDiem:
        parts.append(f"Tên: {place.tenDiaDiem}")
    
    # Tỉnh thành
    if place.maTinhThanh:
        parts.append(f"Tỉnh thành: {place.maTinhThanh.tenTinhThanh}")
    
    # Loại địa điểm
    if place.loaiDiaDiem:
        loai_map = {
            'dia_danh': 'Địa danh',
            'nha_hang': 'Nhà hàng',
            'khach_san': 'Khách sạn',
            'giai_tri': 'Giải trí',
            'mua_sam': 'Mua sắm',
            'khac': 'Khác'
        }
        loai_name = loai_map.get(place.loaiDiaDiem, place.loaiDiaDiem)
        parts.append(f"Loại: {loai_name}")
    
    # Mô tả
    if place.moTa:
        parts.append(f"Mô tả: {place.moTa}")
    
    # Địa chỉ
    if place.diaChi:
        parts.append(f"Địa chỉ: {place.diaChi}")
    
    # Đặc điểm
    if place.dacDiem:
        if isinstance(place.dacDiem, dict):
            dac_diem_text = ", ".join([f"{k}: {v}" for k, v in place.dacDiem.items()][:5])
            if dac_diem_text:
                parts.append(f"Đặc điểm: {dac_diem_text}")
        elif isinstance(place.dacDiem, list):
            dac_diem_text = ", ".join(str(x) for x in place.dacDiem[:5])
            if dac_diem_text:
                parts.append(f"Đặc điểm: {dac_diem_text}")
        else:
            parts.append(f"Đặc điểm: {str(place.dacDiem)[:200]}")
    
    # Tiện nghi
    if place.tienNghi:
        if isinstance(place.tienNghi, dict):
            tien_nghi_text = ", ".join([f"{k}: {v}" for k, v in place.tienNghi.items()][:5])
            if tien_nghi_text:
                parts.append(f"Tiện nghi: {tien_nghi_text}")
        elif isinstance(place.tienNghi, list):
            tien_nghi_text = ", ".join(str(x) for x in place.tienNghi[:5])
            if tien_nghi_text:
                parts.append(f"Tiện nghi: {tien_nghi_text}")
    
    # Đánh giá
    if place.danhGiaTrungBinh:
        parts.append(f"Đánh giá: {place.danhGiaTrungBinh}/5.0")
    
    # Giá vé
    if place.giaVe:
        parts.append(f"Giá vé: {place.giaVe:,} VND")
    
    return ". ".join(parts)


def create_metadata(place: DiaDiem) -> Dict[str, Any]:
    """
    Tạo metadata từ DiaDiem model
    
    Args:
        place: DiaDiem instance
        
    Returns:
        Metadata dictionary
    """
    # Normalize city name
    city_name = place.maTinhThanh.tenTinhThanh if place.maTinhThanh else "Vietnam"
    
    # Map loaiDiaDiem to category
    category_map = {
        'dia_danh': 'attraction',
        'nha_hang': 'restaurant',
        'khach_san': 'hotel',
        'giai_tri': 'entertainment',
        'mua_sam': 'shopping',
        'khac': 'other'
    }
    category = category_map.get(place.loaiDiaDiem, 'other')
    
    metadata = {
        'name': str(place.tenDiaDiem)[:200],
        'city': city_name[:100],
        'category': category,
        'rating': float(place.danhGiaTrungBinh) if place.danhGiaTrungBinh else 0.0,
        'price': float(place.giaVe) if place.giaVe else 0.0,
        'price_level': int(place.giaVe // 100000) if place.giaVe else 0,  # Price level based on 100k increments
        'latitude': float(place.viDo) if place.viDo else None,
        'longitude': float(place.kinhDo) if place.kinhDo else None,
        'description': str(place.moTa)[:500] if place.moTa else '',
        'address': str(place.diaChi)[:200] if place.diaChi else '',
        'source': 'database',
        'place_id': int(place.maDiaDiem),
        'province': city_name[:100]
    }
    
    return metadata


def vectorize_all_places(batch_size: int = 100, clear_existing: bool = False):
    """
    Vector hóa tất cả places từ database vào ChromaDB
    
    Args:
        batch_size: Số lượng documents mỗi batch
        clear_existing: Có xóa dữ liệu cũ không
    """
    print("=" * 80)
    print("VECTOR HÓA TẤT CẢ DỮ LIỆU VÀO CHROMADB")
    print("=" * 80)
    
    # Initialize Vector DB Agent
    print("\n[1/5] Khởi tạo Vector DB Agent...")
    vector_db = get_vector_db_agent()
    
    if not vector_db or not vector_db.collection:
        print("❌ Lỗi: Không thể khởi tạo Vector DB Agent hoặc ChromaDB collection")
        return
    
    print("✅ Vector DB Agent đã sẵn sàng")
    
    # Get current stats
    print("\n[2/5] Kiểm tra dữ liệu hiện tại...")
    stats = vector_db.get_database_stats()
    current_count = stats.get('total_documents', 0)
    print(f"   Số documents hiện tại: {current_count}")
    
    if clear_existing and current_count > 0:
        print(f"\n⚠️  Xóa {current_count} documents cũ...")
        try:
            # Get all IDs
            all_docs = vector_db.collection.get()
            if all_docs and all_docs.get('ids'):
                vector_db.collection.delete(ids=all_docs['ids'])
                print(f"✅ Đã xóa {len(all_docs['ids'])} documents")
        except Exception as e:
            print(f"❌ Lỗi khi xóa: {e}")
    
    # Get all places from database
    print("\n[3/5] Lấy dữ liệu từ database...")
    places = DiaDiem.objects.select_related('maTinhThanh').all()
    total_count = places.count()
    print(f"   Tổng số địa điểm: {total_count}")
    
    if total_count == 0:
        print("❌ Không có dữ liệu để vector hóa")
        return
    
    # Process places in batches
    print(f"\n[4/5] Vector hóa dữ liệu (batch size: {batch_size})...")
    documents = []
    metadatas = []
    ids = []
    
    processed = 0
    skipped = 0
    failed = 0
    
    # Check existing IDs to avoid duplicates
    existing_ids = set()
    try:
        existing_docs = vector_db.collection.get()
        if existing_docs and existing_docs.get('ids'):
            existing_ids = {id.replace('place_', '') for id in existing_docs['ids'] if id.startswith('place_')}
            print(f"   Đã có {len(existing_ids)} documents trong database (sẽ bỏ qua)")
    except Exception as e:
        logger.warning(f"Could not check existing IDs: {e}")
    
    for place in places:
        try:
            # Skip if already exists
            place_id_str = str(place.maDiaDiem)
            if place_id_str in existing_ids:
                skipped += 1
                continue
            
            # Create document text
            doc_text = create_document_text(place)
            if not doc_text or len(doc_text.strip()) < 10:
                skipped += 1
                logger.warning(f"Skipping place {place.maDiaDiem}: empty document text")
                continue
            
            # Create metadata
            metadata = create_metadata(place)
            
            documents.append(doc_text)
            metadatas.append(metadata)
            ids.append(f"place_{place.maDiaDiem}")
            
            processed += 1
            
            # Show progress
            if processed % 50 == 0:
                print(f"   Đã xử lý: {processed}/{total_count} (Skipped: {skipped}, Failed: {failed})...", end='\r')
            
            # Add batch when reached batch_size
            if len(documents) >= batch_size:
                try:
                    vector_db.collection.add(
                        documents=documents,
                        metadatas=metadatas,
                        ids=ids
                    )
                    print(f"\n   ✅ Đã thêm batch: {len(ids)} documents (Total processed: {processed}/{total_count})")
                    documents, metadatas, ids = [], [], []
                except Exception as e:
                    logger.error(f"Error adding batch: {e}")
                    failed += len(ids)
                    documents, metadatas, ids = [], [], []
        
        except Exception as e:
            failed += 1
            logger.error(f"Error processing place {place.maDiaDiem}: {e}")
            continue
    
    # Add remaining documents
    if documents:
        try:
            vector_db.collection.add(
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            print(f"\n   ✅ Đã thêm batch cuối: {len(ids)} documents")
        except Exception as e:
            logger.error(f"Error adding final batch: {e}")
            failed += len(ids)
    
    # Final stats
    print("\n[5/5] Hoàn tất!")
    print("=" * 80)
    print("KẾT QUẢ:")
    print(f"   ✅ Đã xử lý: {processed}")
    print(f"   ⏭️  Đã bỏ qua (trùng lặp): {skipped}")
    print(f"   ❌ Lỗi: {failed}")
    print(f"   📊 Tổng số mới: {processed - failed}")
    
    # Get final stats
    final_stats = vector_db.get_database_stats()
    final_count = final_stats.get('total_documents', 0)
    print(f"\n   📈 Tổng số documents trong ChromaDB: {final_count}")
    print(f"   🏙️  Số thành phố: {len(final_stats.get('cities', []))}")
    print(f"   📂 Số categories: {len(final_stats.get('categories', []))}")
    
    if final_stats.get('cities'):
        print(f"\n   Thành phố: {', '.join(sorted(final_stats['cities'])[:10])}...")
    if final_stats.get('categories'):
        print(f"   Categories: {', '.join(sorted(final_stats['categories']))}")
    
    print("=" * 80)
    print("✅ Hoàn tất vector hóa dữ liệu!")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Vector hóa tất cả dữ liệu vào ChromaDB')
    parser.add_argument(
        '--batch-size',
        type=int,
        default=100,
        help='Số lượng documents mỗi batch (default: 100)'
    )
    parser.add_argument(
        '--clear',
        action='store_true',
        help='Xóa dữ liệu cũ trước khi thêm mới'
    )
    
    args = parser.parse_args()
    
    try:
        vectorize_all_places(
            batch_size=args.batch_size,
            clear_existing=args.clear
        )
    except KeyboardInterrupt:
        print("\n\n⚠️  Đã dừng bởi người dùng")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        print(f"\n❌ Lỗi nghiêm trọng: {e}")

