#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import annotations

import io
import json
import os
import re
import sys
import unicodedata
from pathlib import Path
from typing import Any

import django


if sys.platform == "win32":
    if sys.stdout.encoding != "utf-8":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    if sys.stderr.encoding != "utf-8":
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace", line_buffering=True)


BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "vivu_core.settings")
django.setup()

from django.db import transaction  # noqa: E402

import chromadb  # noqa: E402

from apps.places.models import DiaDiem, TinhThanh  # noqa: E402


DONG_NAI_ID = 16
DONG_NAI_NAME = "Tỉnh Đồng Nai"
DONG_NAI_DESCRIPTION = (
    "Tỉnh Đồng Nai. Trung tâm hành chính: Thành phố Biên Hòa. "
    "Đơn vị đô thị trực thuộc tỉnh tiêu biểu: Thành phố Biên Hòa, Thành phố Long Khánh."
)
COLLECTION_NAME = "vietnam_places"
CHROMA_HOST = os.getenv("CHROMA_HOST", "127.0.0.1")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))

PROVINCE_PATTERN = re.compile(
    r"(?i)\b(?:t(?:ỉnh)?\.?\s*)?(?:đồng\s*na[iy]|dong\s*nai|đồng\s*nao)\b"
)
CITY_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"(?i)\b(?:tp\.?\s*|thành\s*phố\s*|thị\s*xã\s*)?bi[eê]n\s*h[oò]a\b"), "Thành phố Biên Hòa"),
    (re.compile(r"(?i)\b(?:tp\.?\s*|thành\s*phố\s*|thị\s*xã\s*)?long\s*kh[aá]nh\b"), "Thành phố Long Khánh"),
]

DISTRICT_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"(?i)\bhuy[eệ]n\s*long\s*thành\b"), "Huyện Long Thành"),
    (re.compile(r"(?i)\bhuy[eệ]n\s*tr[aả]ng\s*bom\b"), "Huyện Trảng Bom"),
    (re.compile(r"(?i)\bhuy[eệ]n\s*th[oố]ng\s*nh[aấ]t\b"), "Huyện Thống Nhất"),
    (re.compile(r"(?i)\bhuy[eệ]n\s*t[aâ]n\s*ph[uú]\b"), "Huyện Tân Phú"),
    (re.compile(r"(?i)\bhuy[eệ]n\s*v[iĩ]nh\s*c[uử]u\b"), "Huyện Vĩnh Cửu"),
    (re.compile(r"(?i)\bhuy[eệ]n\s*xu[aâ]n\s*l[oộ]c\b"), "Huyện Xuân Lộc"),
    (re.compile(r"(?i)\bhuy[eệ]n\s*định\s*qu[aá]n\b"), "Huyện Định Quán"),
    (re.compile(r"(?i)\bhuy[eệ]n\s*nhơn\s*trạch\b"), "Huyện Nhơn Trạch"),
    (re.compile(r"(?i)\bhuy[eệ]n\s*cẩm\s*mỹ\b"), "Huyện Cẩm Mỹ"),
    (re.compile(r"(?i)\bhuy[eệ]n\s*tân\s*phú\b"), "Huyện Tân Phú"),
    (re.compile(r"(?i)\bthị\s*trấn\s*dầu\s*giây\b"), "Thị trấn Dầu Giây"),
]

LOAI_MAPPING = {
    "dia_danh": "Địa danh",
    "nha_hang": "Nhà hàng",
    "khach_san": "Khách sạn",
    "giai_tri": "Giải trí",
    "mua_sam": "Mua sắm",
    "khac": "Khác",
    "cslt": "Khách sạn",
    "rest": "Nhà hàng",
    "shop": "Mua sắm",
    "dest": "Địa danh",
    "vcgt": "Giải trí",
}

CATEGORY_MAPPING = {
    "dia_danh": "attraction",
    "nha_hang": "restaurant",
    "khach_san": "hotel",
    "giai_tri": "entertainment",
    "mua_sam": "shopping",
    "khac": "other",
    "cslt": "hotel",
    "rest": "restaurant",
    "shop": "shopping",
    "dest": "attraction",
    "vcgt": "entertainment",
}


def fold_text(value: str) -> str:
    normalized = unicodedata.normalize("NFD", value.lower().strip())
    normalized = normalized.replace("đ", "d")
    normalized = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def parse_source_metadata(raw_value: str | None) -> dict[str, Any]:
    if not raw_value:
        return {}
    try:
        parsed = json.loads(raw_value)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}


def clean_segment(segment: str) -> str:
    value = segment.strip(" ,.;")
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def normalize_dong_nai_address(address: str) -> str:
    working = PROVINCE_PATTERN.sub(DONG_NAI_NAME, address or "")
    for pattern, replacement in CITY_RULES:
        working = pattern.sub(replacement, working)
    for pattern, replacement in DISTRICT_RULES:
        working = pattern.sub(replacement, working)

    segments = [clean_segment(part) for part in working.split(",") if clean_segment(part)]
    deduped: list[str] = []
    seen: set[str] = set()
    for segment in segments:
        key = fold_text(segment)
        if key and key not in seen and key != fold_text(DONG_NAI_NAME):
            deduped.append(segment)
            seen.add(key)

    if not deduped:
        deduped = [DONG_NAI_NAME]

    return ", ".join(deduped + [DONG_NAI_NAME])


def extract_admin_unit(address: str) -> str:
    for pattern, replacement in CITY_RULES + DISTRICT_RULES:
        if pattern.search(address):
            return replacement
    return DONG_NAI_NAME


def build_document(place: DiaDiem, address: str, admin_unit: str, category_label: str) -> str:
    parts = [
        f"Tên: {place.tenDiaDiem}",
        f"Đơn vị hành chính cấp dưới: {admin_unit}",
        f"Tỉnh thành: {DONG_NAI_NAME}",
        f"Loại: {category_label}",
        f"Địa chỉ: {address}",
    ]
    description = (place.moTa or "").strip()
    if description:
        parts.append(f"Mô tả: {description}")
    return ". ".join(parts)


def build_metadata(place: DiaDiem, address: str, admin_unit: str, source_meta: dict[str, Any]) -> dict[str, Any]:
    raw_category = source_meta.get("category") or place.loaiDiaDiem
    category = CATEGORY_MAPPING.get(str(raw_category), str(raw_category))
    return {
        "name": str(place.tenDiaDiem)[:200],
        "city": admin_unit[:100],
        "province": DONG_NAI_NAME,
        "category": category[:100],
        "description": str(place.moTa or "")[:500],
        "address": address[:300],
        "source": str(source_meta.get("source") or "database")[:100],
        "place_id": int(place.maDiaDiem),
        "item_id": str(source_meta.get("item_id") or ""),
        "detail_url": str(source_meta.get("detail_url") or "")[:500],
        "price": float(place.giaVe or 0.0),
        "rating": float(place.danhGiaTrungBinh or 0.0),
        "latitude": float(place.viDo or 0.0),
        "longitude": float(place.kinhDo or 0.0),
    }


def get_chroma_collection():
    client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def main() -> None:
    collection = get_chroma_collection()
    sync_payloads: list[dict[str, Any]] = []
    counters = {
        "province_updated": 0,
        "fk_checked": 0,
        "poi_updated": 0,
        "vector_upserts": 0,
    }

    with transaction.atomic():
        province = TinhThanh.objects.select_for_update().get(maTinhThanh=DONG_NAI_ID)
        if province.tenTinhThanh != DONG_NAI_NAME or (province.moTa or "").strip() != DONG_NAI_DESCRIPTION:
            province.tenTinhThanh = DONG_NAI_NAME
            province.moTa = DONG_NAI_DESCRIPTION
            province.save(update_fields=["tenTinhThanh", "moTa", "updated_at"])
            counters["province_updated"] = 1

        places = list(
            DiaDiem.objects.select_for_update()
            .filter(maTinhThanh=province)
            .order_by("maDiaDiem")
        )

        for place in places:
            counters["fk_checked"] += 1
            changed = False

            if place.maTinhThanh_id != DONG_NAI_ID:
                place.maTinhThanh = province
                changed = True

            normalized_address = normalize_dong_nai_address(place.diaChi or "")
            if normalized_address != (place.diaChi or ""):
                place.diaChi = normalized_address
                changed = True

            if changed:
                place.save(update_fields=["maTinhThanh", "diaChi", "lanCapNhatCuoi"])
                counters["poi_updated"] += 1

            source_meta = parse_source_metadata(place.dacDiem)
            category_label = LOAI_MAPPING.get(
                str(source_meta.get("category") or place.loaiDiaDiem),
                place.loaiDiaDiem,
            )
            admin_unit = extract_admin_unit(place.diaChi or normalized_address)
            vector_id = str(source_meta.get("item_id") or f"db_place_{place.maDiaDiem}")
            sync_payloads.append(
                {
                    "id": vector_id,
                    "document": build_document(place, place.diaChi or normalized_address, admin_unit, category_label),
                    "metadata": build_metadata(place, place.diaChi or normalized_address, admin_unit, source_meta),
                }
            )

        def sync_to_chroma() -> None:
            ids = [item["id"] for item in sync_payloads]
            documents = [item["document"] for item in sync_payloads]
            metadatas = [item["metadata"] for item in sync_payloads]
            collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
            counters["vector_upserts"] = len(ids)

        transaction.on_commit(sync_to_chroma)

    print(json.dumps(counters, ensure_ascii=False))


if __name__ == "__main__":
    main()
