#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Đồng bộ delta địa điểm active từ SQLite sang ChromaDB qua HttpClient.

Mục tiêu:
- So sánh tập `maDiaDiem` active trong SQLite với `place_id` đã có trong collection.
- Chỉ upsert các bản ghi còn thiếu vào `vietnam_places`.
- Chunk size mặc định: 100.
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

import chromadb


if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


BACKEND_DIR = Path(__file__).resolve().parent.parent
SQLITE_PATH = BACKEND_DIR / "vivudb.sqlite3"
COLLECTION_NAME = "vietnam_places"
CHROMA_HOST = os.getenv("CHROMA_HOST", "127.0.0.1")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))
DEFAULT_BATCH_SIZE = 100


def get_sqlite_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(str(SQLITE_PATH))
    connection.row_factory = sqlite3.Row
    return connection


def get_chroma_collection():
    client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
    return collection


def parse_source_metadata(raw_value: Optional[str]) -> Dict[str, Any]:
    if not raw_value:
        return {}
    try:
        parsed = json.loads(raw_value)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}


def load_active_place_ids() -> List[int]:
    connection = get_sqlite_connection()
    try:
        rows = connection.execute(
            """
            SELECT maDiaDiem
            FROM DIADIEM
            WHERE trangThai = 'active'
            ORDER BY maDiaDiem
            """
        ).fetchall()
        return [int(row["maDiaDiem"]) for row in rows]
    finally:
        connection.close()


def load_active_places_by_ids(place_ids: Sequence[int]) -> List[sqlite3.Row]:
    if not place_ids:
        return []

    placeholders = ",".join("?" for _ in place_ids)
    connection = get_sqlite_connection()
    try:
        rows = connection.execute(
            f"""
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
            WHERE d.trangThai = 'active'
              AND d.maDiaDiem IN ({placeholders})
            ORDER BY d.maDiaDiem
            """,
            [int(place_id) for place_id in place_ids],
        ).fetchall()
        return list(rows)
    finally:
        connection.close()


def iter_existing_place_ids(collection, page_size: int = 500) -> Tuple[Set[int], int]:
    existing_place_ids: Set[int] = set()
    total = collection.count()
    offset = 0

    while offset < total:
        batch = collection.get(limit=page_size, offset=offset, include=["metadatas"])
        metadatas = batch.get("metadatas", []) if batch else []
        ids = batch.get("ids", []) if batch else []
        if not ids:
            break

        for metadata, raw_id in zip(metadatas, ids):
            place_id = None
            if isinstance(metadata, dict):
                place_id = metadata.get("place_id")
            if place_id is None:
                place_id = raw_id

            try:
                existing_place_ids.add(int(place_id))
            except (TypeError, ValueError):
                continue

        offset += len(ids)

    return existing_place_ids, total


def build_document(row: sqlite3.Row, source_meta: Dict[str, Any]) -> str:
    description = str(row["moTa"] or "").strip()
    address = str(row["diaChi"] or "").strip()
    category = str(source_meta.get("category") or row["loaiDiaDiem"] or "").strip()
    base_parts = [
        f"Tên: {row['tenDiaDiem']}",
        f"Tỉnh thành: {row['tenTinhThanh']}",
        f"Khu vực: {row['tenTinhThanh']}",
    ]
    if category:
        base_parts.append(f"Loại: {category}")
    if address:
        base_parts.append(f"Địa chỉ: {address}")
    if description:
        base_parts.append(f"Mô tả: {description}")
    return ". ".join(base_parts)


def build_metadata(row: sqlite3.Row, source_meta: Dict[str, Any]) -> Dict[str, Any]:
    detail_url = str(source_meta.get("detail_url") or "").strip()
    item_id = str(source_meta.get("item_id") or "").strip()
    source = str(source_meta.get("source") or source_meta.get("source_url") or "sqlite_active_sync").strip()
    category = str(source_meta.get("category") or row["loaiDiaDiem"] or "").strip()

    return {
        "name": str(row["tenDiaDiem"])[:200],
        "city": str(row["tenTinhThanh"])[:100],
        "province": str(row["tenTinhThanh"])[:100],
        "category": category[:100],
        "description": str(row["moTa"] or "")[:1000],
        "address": str(row["diaChi"] or "")[:500],
        "source": source[:100],
        "place_id": int(row["maDiaDiem"]),
        "item_id": item_id[:100],
        "detail_url": detail_url[:500],
        "price": float(row["giaVe"] or 0.0),
        "rating": float(row["danhGiaTrungBinh"] or 0.0),
        "latitude": float(row["viDo"] or 0.0),
        "longitude": float(row["kinhDo"] or 0.0),
    }


def iter_chunks(values: Sequence[int], chunk_size: int) -> Iterable[Sequence[int]]:
    for start in range(0, len(values), chunk_size):
        yield values[start:start + chunk_size]


def sync_missing_places(batch_size: int = DEFAULT_BATCH_SIZE, limit: Optional[int] = None) -> Dict[str, Any]:
    collection = get_chroma_collection()
    sqlite_place_ids = load_active_place_ids()
    existing_place_ids, collection_count_before = iter_existing_place_ids(collection)

    missing_place_ids = [place_id for place_id in sqlite_place_ids if place_id not in existing_place_ids]
    if limit is not None:
        missing_place_ids = missing_place_ids[:limit]

    upserted = 0
    batches = 0

    for place_id_chunk in iter_chunks(missing_place_ids, batch_size):
        rows = load_active_places_by_ids(place_id_chunk)
        if not rows:
            continue

        ids: List[str] = []
        documents: List[str] = []
        metadatas: List[Dict[str, Any]] = []

        for row in rows:
            source_meta = parse_source_metadata(row["dacDiem"])
            ids.append(str(int(row["maDiaDiem"])))
            documents.append(build_document(row, source_meta))
            metadatas.append(build_metadata(row, source_meta))

        collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
        upserted += len(ids)
        batches += 1

    collection_count_after = collection.count()
    return {
        "sqlite_active_total": len(sqlite_place_ids),
        "collection_count_before": collection_count_before,
        "collection_count_after": collection_count_after,
        "existing_place_ids": len(existing_place_ids),
        "missing_detected": len(missing_place_ids),
        "upserted": upserted,
        "batches": batches,
        "batch_size": batch_size,
        "chroma_endpoint": f"http://{CHROMA_HOST}:{CHROMA_PORT}",
    }


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Đồng bộ delta DIADIEM active từ SQLite sang ChromaDB.")
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE, help="Số bản ghi mỗi lần upsert.")
    parser.add_argument("--limit", type=int, default=None, help="Giới hạn số bản ghi thiếu cần xử lý.")
    return parser


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()

    print("=" * 72)
    print("DELTA SYNC SQLITE ACTIVE -> CHROMADB")
    print(f"SQLite: {SQLITE_PATH}")
    print(f"Chroma: http://{CHROMA_HOST}:{CHROMA_PORT}")
    print(f"Collection: {COLLECTION_NAME}")
    print("=" * 72)

    stats = sync_missing_places(batch_size=args.batch_size, limit=args.limit)
    print(f"SQLite active total: {stats['sqlite_active_total']}")
    print(f"Collection count before: {stats['collection_count_before']}")
    print(f"Existing place IDs in collection: {stats['existing_place_ids']}")
    print(f"Missing detected: {stats['missing_detected']}")
    print(f"Upserted: {stats['upserted']}")
    print(f"Batches: {stats['batches']}")
    print(f"Batch size: {stats['batch_size']}")
    print(f"Collection count after: {stats['collection_count_after']}")


if __name__ == "__main__":
    main()
