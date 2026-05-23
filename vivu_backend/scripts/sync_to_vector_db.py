#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Đồng bộ các địa điểm crawl từ csdl.vietnamtourism.gov.vn sang ChromaDB.

Ví dụ:
    python vivu_backend/scripts/sync_to_vector_db.py
    python vivu_backend/scripts/sync_to_vector_db.py --limit 100
    python vivu_backend/scripts/sync_to_vector_db.py --purge-only
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings


if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent
SQLITE_PATH = BACKEND_DIR / "vivudb.sqlite3"
CHROMA_DIRS = [
    REPO_ROOT / "vector_db",
    BACKEND_DIR / "vector_db",
]
COLLECTION_NAME = "vietnam_places"
SOURCE_URL = "csdl.vietnamtourism.gov.vn"


def get_sqlite_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(SQLITE_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def get_chroma_collection():
    chroma_host = os.getenv("CHROMA_HOST")
    if chroma_host:
        chroma_port = int(os.getenv("CHROMA_PORT", "8000"))
        client = chromadb.HttpClient(host=chroma_host, port=chroma_port)
        collection = client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
        return collection, f"http://{chroma_host}:{chroma_port}"

    last_error: Optional[BaseException] = None
    for chroma_dir in CHROMA_DIRS:
        try:
            client = chromadb.PersistentClient(
                path=str(chroma_dir),
                settings=Settings(anonymized_telemetry=False),
            )
            collection = client.get_or_create_collection(
                name=COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"},
            )
            return collection, chroma_dir
        except BaseException as exc:
            last_error = exc
            continue
    raise RuntimeError(f"Không thể mở ChromaDB ở các path cấu hình: {last_error}")


def iter_collection_ids(collection, page_size: int = 1000) -> List[str]:
    ids: List[str] = []
    total = collection.count()
    offset = 0
    while offset < total:
        batch = collection.get(limit=page_size, offset=offset, include=[])
        batch_ids = batch.get("ids", []) if batch else []
        if not batch_ids:
            break
        ids.extend(batch_ids)
        offset += len(batch_ids)
    return ids


def purge_legacy_ids(collection, page_size: int = 1000) -> Dict[str, int]:
    all_ids = iter_collection_ids(collection, page_size=page_size)
    legacy_ids = [value for value in all_ids if isinstance(value, str) and value.startswith("place_")]
    if legacy_ids:
        collection.delete(ids=legacy_ids)
    return {
        "scanned": len(all_ids),
        "deleted": len(legacy_ids),
    }


def parse_source_metadata(raw_value: Optional[str]) -> Dict[str, Any]:
    if not raw_value:
        return {}
    try:
        parsed = json.loads(raw_value)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}


def load_source_places(limit: Optional[int] = None) -> List[sqlite3.Row]:
    conn = get_sqlite_connection()
    try:
        sql = """
        SELECT
            d.maDiaDiem,
            d.tenDiaDiem,
            d.moTa,
            d.diaChi,
            d.loaiDiaDiem,
            d.viDo,
            d.kinhDo,
            d.giaVe,
            d.danhGiaTrungBinh,
            d.dacDiem,
            t.tenTinhThanh
        FROM DIADIEM d
        JOIN TINHTHANH t ON t.maTinhThanh = d.maTinhThanh
        WHERE d.dacDiem LIKE ?
        ORDER BY d.maDiaDiem
        """
        params: List[Any] = [f"%{SOURCE_URL}%"]
        if limit is not None:
            sql += " LIMIT ?"
            params.append(limit)
        return conn.execute(sql, params).fetchall()
    finally:
        conn.close()


def build_document(row: sqlite3.Row, metadata: Dict[str, Any]) -> str:
    source_features = row["dacDiem"] or "{}"
    base = f"{row['tenDiaDiem']} tại {row['tenTinhThanh']}. Đặc điểm: {source_features}"
    description = (row["moTa"] or "").strip()
    if description:
        return f"{base}. Mô tả: {description}"
    return base


def build_metadata(row: sqlite3.Row, source_meta: Dict[str, Any]) -> Dict[str, Any]:
    item_id = source_meta.get("item_id")
    detail_url = source_meta.get("detail_url", "")
    category = source_meta.get("category", row["loaiDiaDiem"])
    return {
        "name": str(row["tenDiaDiem"])[:200],
        "city": str(row["tenTinhThanh"])[:100],
        "category": str(category)[:100],
        "description": str(row["moTa"] or "")[:500],
        "address": str(row["diaChi"] or "")[:300],
        "source": SOURCE_URL,
        "place_id": int(row["maDiaDiem"]),
        "item_id": str(item_id) if item_id is not None else "",
        "detail_url": str(detail_url)[:500],
        "province": str(row["tenTinhThanh"])[:100],
        "price": float(row["giaVe"] or 0.0),
        "rating": float(row["danhGiaTrungBinh"] or 0.0),
        "latitude": float(row["viDo"] or 0.0),
        "longitude": float(row["kinhDo"] or 0.0),
    }


def sync_places(
    limit: Optional[int] = None,
    batch_size: int = 100,
    purge_legacy: bool = True,
) -> Dict[str, int]:
    rows = load_source_places(limit=limit)
    collection, chroma_dir = get_chroma_collection()

    synced = 0
    skipped = 0
    batches = 0
    purge_stats = {"scanned": 0, "deleted": 0}

    if purge_legacy:
        purge_stats = purge_legacy_ids(collection)

    ids: List[str] = []
    documents: List[str] = []
    metadatas: List[Dict[str, Any]] = []

    def flush() -> None:
        nonlocal ids, documents, metadatas, batches, synced
        if not ids:
            return
        collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
        synced += len(ids)
        batches += 1
        ids, documents, metadatas = [], [], []

    for row in rows:
        source_meta = parse_source_metadata(row["dacDiem"])
        item_id = source_meta.get("item_id")
        if item_id is None or str(item_id).strip() == "":
            skipped += 1
            continue

        ids.append(str(item_id))
        documents.append(build_document(row, source_meta))
        metadatas.append(build_metadata(row, source_meta))

        if len(ids) >= batch_size:
            flush()

    flush()
    return {
        "selected": len(rows),
        "synced": synced,
        "skipped": skipped,
        "batches": batches,
        "collection_count": collection.count(),
        "chroma_dir": str(chroma_dir),
        "legacy_scanned": purge_stats["scanned"],
        "legacy_deleted": purge_stats["deleted"],
    }


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sync địa điểm crawl từ SQLite sang ChromaDB.")
    parser.add_argument("--limit", type=int, default=None, help="Giới hạn số bản ghi cần sync")
    parser.add_argument("--batch-size", type=int, default=100, help="Số bản ghi mỗi batch upsert")
    parser.add_argument("--no-purge-legacy", action="store_true", help="Không xóa legacy IDs bắt đầu bằng place_")
    parser.add_argument("--purge-only", action="store_true", help="Chỉ dọn legacy IDs, không sync dữ liệu")
    return parser


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()

    print("=" * 72)
    print("SYNC SQLITE -> CHROMADB")
    print(f"SQLite: {SQLITE_PATH}")
    print(f"Chroma candidates: {', '.join(str(path) for path in CHROMA_DIRS)}")
    print(f"Collection: {COLLECTION_NAME}")
    print("=" * 72)

    if args.purge_only:
        collection, chroma_dir = get_chroma_collection()
        purge_stats = purge_legacy_ids(collection)
        print(f"Chroma path used: {chroma_dir}")
        print(f"Legacy scanned: {purge_stats['scanned']}")
        print(f"Legacy deleted: {purge_stats['deleted']}")
        print(f"Collection count: {collection.count()}")
        return

    stats = sync_places(
        limit=args.limit,
        batch_size=args.batch_size,
        purge_legacy=not args.no_purge_legacy,
    )

    print(f"Chroma path used: {stats['chroma_dir']}")
    print(f"Legacy scanned: {stats['legacy_scanned']}")
    print(f"Legacy deleted: {stats['legacy_deleted']}")
    print(f"Selected: {stats['selected']}")
    print(f"Synced: {stats['synced']}")
    print(f"Skipped (missing item_id): {stats['skipped']}")
    print(f"Batches: {stats['batches']}")
    print(f"Collection count: {stats['collection_count']}")


if __name__ == "__main__":
    main()
