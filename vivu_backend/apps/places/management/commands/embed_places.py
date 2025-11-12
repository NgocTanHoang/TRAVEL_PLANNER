"""
Django Management Command: Embed Places vào Vector Database
===========================================================
Sử dụng để mã hóa các địa điểm từ database vào ChromaDB vector database.
Có thể tích hợp Tavily API để enrich dữ liệu trước khi embed.

Usage:
    python manage.py embed_places
    python manage.py embed_places --batch-size 100
    python manage.py embed_places --use-tavily
    python manage.py embed_places --reset  # Xóa và tạo lại collection
"""

import os
import sys
import logging
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from apps.places.models import DiaDiem, TinhThanh, HinhAnhDiaDiem

# Add backend directory to path for agents, etc.
# BASE_DIR (vivu_backend) is already added in settings.py, but adding here for safety
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Embed địa điểm từ database vào ChromaDB vector database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Số lượng địa điểm xử lý mỗi batch (default: 100)'
        )
        parser.add_argument(
            '--use-tavily',
            action='store_true',
            help='Sử dụng Tavily API để enrich dữ liệu trước khi embed'
        )
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Xóa và tạo lại collection (mất toàn bộ dữ liệu cũ)'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Giới hạn số lượng địa điểm xử lý (để test)'
        )

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        use_tavily = options['use_tavily']
        reset = options['reset']
        limit = options['limit']

        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS('EMBED PLACES TO VECTOR DATABASE'))
        self.stdout.write(self.style.SUCCESS('=' * 60))

        # Import vector database agent
        try:
            from agents.travel_agents.vector_db import VectorDatabaseAgent
        except ImportError as e:
            raise CommandError(f"Không thể import VectorDatabaseAgent: {e}")

        # Initialize vector DB agent
        vector_db = VectorDatabaseAgent()
        
        if not vector_db.client:
            raise CommandError("ChromaDB không khả dụng. Vui lòng cài đặt chromadb.")

        # Reset collection nếu cần
        if reset:
            self.stdout.write(self.style.WARNING('⚠️  Xóa collection cũ...'))
            try:
                vector_db.client.delete_collection(name=vector_db.collection_name)
                self.stdout.write(self.style.SUCCESS(f'✓ Đã xóa collection: {vector_db.collection_name}'))
            except:
                pass
            
            # Tạo lại collection
            vector_db.collection = vector_db.client.create_collection(
                name=vector_db.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            self.stdout.write(self.style.SUCCESS(f'✓ Đã tạo collection mới: {vector_db.collection_name}'))
        
        # Initialize Tavily nếu cần
        tavily_client = None
        if use_tavily:
            tavily_api_key = os.getenv('TAVILY_API_KEY')
            if not tavily_api_key:
                self.stdout.write(self.style.WARNING(
                    '⚠️  TAVILY_API_KEY không được tìm thấy. Bỏ qua Tavily enrichment.'
                ))
            else:
                try:
                    from tavily import TavilyClient
                    tavily_client = TavilyClient(api_key=tavily_api_key)
                    self.stdout.write(self.style.SUCCESS('✓ Tavily client đã được khởi tạo'))
                except Exception as e:
                    self.stdout.write(self.style.WARNING(
                        f'⚠️  Không thể khởi tạo Tavily client: {e}. Bỏ qua Tavily enrichment.'
                    ))

        # Lấy địa điểm từ database
        places = DiaDiem.objects.filter(trangThai='active').select_related('maTinhThanh')
        
        if limit:
            places = places[:limit]
        
        total_count = places.count()
        self.stdout.write(self.style.SUCCESS(f'\n📊 Tổng số địa điểm: {total_count}'))

        if total_count == 0:
            self.stdout.write(self.style.WARNING('⚠️  Không có địa điểm nào để embed.'))
            return

        # Kiểm tra địa điểm đã tồn tại trong vector DB
        existing_ids = set()
        try:
            existing_docs = vector_db.collection.get(limit=10000)
            if existing_docs and existing_docs.get('ids'):
                existing_ids = {doc_id.replace('place_', '') for doc_id in existing_docs['ids'] if doc_id.startswith('place_')}
                self.stdout.write(self.style.SUCCESS(f'✓ Tìm thấy {len(existing_ids)} địa điểm đã embed'))
        except:
            pass

        # Batch processing
        documents = []
        metadatas = []
        ids = []
        processed = 0
        skipped = 0
        failed = 0

        self.stdout.write(self.style.SUCCESS(f'\n🔄 Bắt đầu embed...\n'))

        for place in places:
            try:
                # Bỏ qua nếu đã tồn tại
                if str(place.maDiaDiem) in existing_ids:
                    skipped += 1
                    continue

                # Tạo document text
                doc_text = self._create_document_text(place, tavily_client)
                
                # Tạo metadata
                metadata = self._create_metadata(place)
                
                documents.append(doc_text)
                metadatas.append(metadata)
                ids.append(f"place_{place.maDiaDiem}")
                
                processed += 1
                
                # Hiển thị tiến trình
                if processed % 10 == 0:
                    self.stdout.write(f'   Đã xử lý: {processed}/{total_count}...', ending='\r')

                # Thêm batch vào vector DB
                if len(documents) >= batch_size:
                    vector_db.collection.add(
                        documents=documents,
                        metadatas=metadatas,
                        ids=ids
                    )
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ Đã embed batch: {len(ids)} địa điểm (Total: {processed}/{total_count})'
                        )
                    )
                    documents, metadatas, ids = [], [], []

            except Exception as e:
                failed += 1
                logger.error(f"Error embedding place {place.maDiaDiem}: {e}")
                self.stdout.write(
                    self.style.ERROR(f'   ✗ Lỗi với địa điểm {place.maDiaDiem}: {str(e)[:100]}')
                )

        # Thêm batch cuối cùng
        if documents:
            try:
                vector_db.collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Đã embed batch cuối: {len(ids)} địa điểm'
                    )
                )
            except Exception as e:
                failed += len(documents)
                logger.error(f"Error adding final batch: {e}")
                self.stdout.write(self.style.ERROR(f'✗ Lỗi với batch cuối: {e}'))

        # Tổng kết
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 60))
        self.stdout.write(self.style.SUCCESS('KẾT QUẢ:'))
        self.stdout.write(self.style.SUCCESS('=' * 60))
        self.stdout.write(self.style.SUCCESS(f'✓ Đã embed: {processed} địa điểm'))
        if skipped > 0:
            self.stdout.write(self.style.WARNING(f'⚠ Đã bỏ qua: {skipped} địa điểm (đã tồn tại)'))
        if failed > 0:
            self.stdout.write(self.style.ERROR(f'✗ Lỗi: {failed} địa điểm'))
        
        # Hiển thị stats của vector DB
        try:
            stats = vector_db.get_database_stats()
            self.stdout.write(self.style.SUCCESS(f'\n📊 Vector DB Stats:'))
            self.stdout.write(self.style.SUCCESS(f'   Tổng documents: {stats.get("total_documents", 0)}'))
            self.stdout.write(self.style.SUCCESS(f'   Cities: {len(stats.get("cities", []))}'))
            self.stdout.write(self.style.SUCCESS(f'   Categories: {len(stats.get("categories", []))}'))
        except:
            pass

        self.stdout.write(self.style.SUCCESS('\n✓ Hoàn tất!'))

    def _create_document_text(self, place: DiaDiem, tavily_client=None) -> str:
        """
        Tạo text document từ địa điểm để embed.
        Có thể enrich với Tavily nếu được cung cấp.
        """
        parts = []
        
        # Tên địa điểm
        parts.append(f"Tên: {place.tenDiaDiem}")
        
        # Tỉnh thành
        parts.append(f"Tỉnh thành: {place.maTinhThanh.tenTinhThanh}")
        
        # Loại địa điểm
        loai_display = dict(DiaDiem.LOAI_DIA_DIEM_CHOICES).get(place.loaiDiaDiem, place.loaiDiaDiem)
        parts.append(f"Loại: {loai_display}")
        
        # Địa chỉ
        if place.diaChi:
            parts.append(f"Địa chỉ: {place.diaChi}")
        
        # Mô tả
        if place.moTa:
            parts.append(f"Mô tả: {place.moTa}")
        
        # Giá vé
        if place.giaVe:
            parts.append(f"Giá vé: {place.giaVe:,.0f} VNĐ")
        
        # Giờ mở cửa
        if place.gioMoCua:
            parts.append(f"Giờ mở cửa: {place.gioMoCua}")
        
        # Đánh giá
        if place.danhGiaTrungBinh > 0:
            parts.append(f"Đánh giá: {place.danhGiaTrungBinh:.1f}/5.0 ({place.soLuotDanhGia} lượt)")
        
        # Enrich với Tavily (optional)
        if tavily_client:
            try:
                # Search với tên địa điểm + tỉnh thành
                search_query = f"{place.tenDiaDiem} {place.maTinhThanh.tenTinhThanh} Việt Nam"
                tavily_results = tavily_client.search(
                    query=search_query,
                    max_results=1,
                    search_depth="basic"
                )
                
                if tavily_results and tavily_results.get('results'):
                    result = tavily_results['results'][0]
                    content = result.get('content', '')
                    if content:
                        # Thêm thông tin từ Tavily vào mô tả
                        parts.append(f"Thông tin bổ sung: {content[:500]}")  # Giới hạn 500 ký tự
            except Exception as e:
                logger.debug(f"Tavily search failed for {place.tenDiaDiem}: {e}")
        
        return ". ".join(parts)

    def _create_metadata(self, place: DiaDiem) -> dict:
        """Tạo metadata cho vector database"""
        # Lấy ảnh chính nếu có
        image_url = ''
        try:
            main_image = place.hinh_anhs.filter(laChinh=True).first()
            if main_image:
                image_url = main_image.urlHinhAnh
            elif place.hinh_anhs.exists():
                # Lấy ảnh đầu tiên nếu không có ảnh chính
                image_url = place.hinh_anhs.first().urlHinhAnh
        except:
            pass
        
        return {
            'name': place.tenDiaDiem,
            'city': place.maTinhThanh.tenTinhThanh,
            'category': dict(DiaDiem.LOAI_DIA_DIEM_CHOICES).get(place.loaiDiaDiem, place.loaiDiaDiem),
            'category_code': place.loaiDiaDiem,
            'rating': float(place.danhGiaTrungBinh) if place.danhGiaTrungBinh else 0.0,
            'price': float(place.giaVe) if place.giaVe else 0.0,
            'price_level': self._get_price_level(place.giaVe),
            'latitude': float(place.viDo) if place.viDo else None,
            'longitude': float(place.kinhDo) if place.kinhDo else None,
            'address': place.diaChi or '',
            'description': (place.moTa or '')[:500],  # Giới hạn 500 ký tự
            'opening_hours': place.gioMoCua or '',
            'phone': place.dienThoai or '',
            'website': place.website or '',
            'review_count': int(place.soLuotDanhGia) if place.soLuotDanhGia else 0,
            'view_count': int(place.soLuotXem) if place.soLuotXem else 0,
            'image_url': image_url,
            'place_id': int(place.maDiaDiem),
            'province_id': int(place.maTinhThanh.maTinhThanh),
        }

    def _get_price_level(self, price: float) -> int:
        """Xác định mức giá (0-4)"""
        if not price or price == 0:
            return 0
        elif price < 50000:
            return 1  # Rất rẻ
        elif price < 200000:
            return 2  # Rẻ
        elif price < 500000:
            return 3  # Trung bình
        else:
            return 4  # Đắt

