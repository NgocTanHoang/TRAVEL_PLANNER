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

from django.db import connection, transaction  # noqa: E402

import chromadb  # noqa: E402

from apps.places.models import DiaDiem, TinhThanh  # noqa: E402


CHROMA_HOST = os.getenv("CHROMA_HOST", "127.0.0.1")
CHROMA_PORT = int(os.getenv("CHROMA_PORT", "8000"))
COLLECTION_NAME = "vietnam_places"

CANONICAL_REGIONS: list[tuple[str, str, str]] = [
    ("An Giang", "Tỉnh An Giang", "Tỉnh An Giang."),
    ("Bà Rịa - Vũng Tàu", "Tỉnh Bà Rịa - Vũng Tàu", "Tỉnh Bà Rịa - Vũng Tàu."),
    ("Bạc Liêu", "Tỉnh Bạc Liêu", "Tỉnh Bạc Liêu."),
    ("Bắc Kạn", "Tỉnh Bắc Kạn", "Tỉnh Bắc Kạn."),
    ("Bắc Giang", "Tỉnh Bắc Giang", "Tỉnh Bắc Giang."),
    ("Bắc Ninh", "Tỉnh Bắc Ninh", "Tỉnh Bắc Ninh."),
    ("Bến Tre", "Tỉnh Bến Tre", "Tỉnh Bến Tre."),
    ("Bình Định", "Tỉnh Bình Định", "Tỉnh Bình Định."),
    ("Bình Dương", "Tỉnh Bình Dương", "Tỉnh Bình Dương."),
    ("Bình Phước", "Tỉnh Bình Phước", "Tỉnh Bình Phước."),
    ("Bình Thuận", "Tỉnh Bình Thuận", "Tỉnh Bình Thuận."),
    ("Cà Mau", "Tỉnh Cà Mau", "Tỉnh Cà Mau."),
    ("Cần Thơ", "Thành phố Cần Thơ", "Thành phố Cần Thơ."),
    ("Cao Bằng", "Tỉnh Cao Bằng", "Tỉnh Cao Bằng."),
    ("Đà Nẵng", "Thành phố Đà Nẵng", "Thành phố Đà Nẵng."),
    ("Đắk Lắk", "Tỉnh Đắk Lắk", "Tỉnh Đắk Lắk."),
    ("Đắk Nông", "Tỉnh Đắk Nông", "Tỉnh Đắk Nông."),
    ("Điện Biên", "Tỉnh Điện Biên", "Tỉnh Điện Biên."),
    (
        "Đồng Nai",
        "Tỉnh Đồng Nai",
        "Tỉnh Đồng Nai. Trung tâm hành chính: Thành phố Biên Hòa. Đơn vị đô thị trực thuộc tỉnh tiêu biểu: Thành phố Biên Hòa, Thành phố Long Khánh.",
    ),
    ("Đồng Tháp", "Tỉnh Đồng Tháp", "Tỉnh Đồng Tháp."),
    ("Gia Lai", "Tỉnh Gia Lai", "Tỉnh Gia Lai."),
    ("Hà Giang", "Tỉnh Hà Giang", "Tỉnh Hà Giang."),
    ("Hà Nam", "Tỉnh Hà Nam", "Tỉnh Hà Nam."),
    ("Hà Nội", "Thành phố Hà Nội", "Thành phố Hà Nội."),
    ("Hà Tĩnh", "Tỉnh Hà Tĩnh", "Tỉnh Hà Tĩnh."),
    ("Hải Dương", "Tỉnh Hải Dương", "Tỉnh Hải Dương."),
    ("Hải Phòng", "Thành phố Hải Phòng", "Thành phố Hải Phòng."),
    ("Hậu Giang", "Tỉnh Hậu Giang", "Tỉnh Hậu Giang."),
    ("Hòa Bình", "Tỉnh Hòa Bình", "Tỉnh Hòa Bình."),
    ("Hưng Yên", "Tỉnh Hưng Yên", "Tỉnh Hưng Yên."),
    ("Khánh Hòa", "Tỉnh Khánh Hòa", "Tỉnh Khánh Hòa."),
    ("Kiên Giang", "Tỉnh Kiên Giang", "Tỉnh Kiên Giang."),
    ("Kon Tum", "Tỉnh Kon Tum", "Tỉnh Kon Tum."),
    ("Thành phố Hồ Chí Minh", "Thành phố Hồ Chí Minh", "Thành phố Hồ Chí Minh."),
]

TARGET_BY_SOURCE: dict[str, str] = {
    "An Giang": "An Giang",
    "Bà Rịa - Vũng Tàu": "Bà Rịa - Vũng Tàu",
    "Bạc Liêu": "Bạc Liêu",
    "Bắc Giang": "Bắc Giang",
    "Bắc Kạn": "Bắc Kạn",
    "Bắc Ninh": "Bắc Ninh",
    "Bến Tre": "Bến Tre",
    "Bình Định": "Bình Định",
    "Bình Dương": "Bình Dương",
    "Bình Phước": "Bình Phước",
    "Bình Thuận": "Bình Thuận",
    "Cà Mau": "Cà Mau",
    "Cao Bằng": "Cao Bằng",
    "Cần Thơ": "Cần Thơ",
    "Đà Nẵng": "Đà Nẵng",
    "Đắk Lắk": "Đắk Lắk",
    "Đắk Nông": "Đắk Nông",
    "Điện Biên": "Điện Biên",
    "Đồng Nai": "Đồng Nai",
    "Đồng Tháp": "Đồng Tháp",
    "Gia Lai": "Gia Lai",
    "Hà Giang": "Hà Giang",
    "Hà Nam": "Hà Nam",
    "Hà Nội": "Hà Nội",
    "Hà Tĩnh": "Hà Tĩnh",
    "Hải Dương": "Hải Dương",
    "Hải Phòng": "Hải Phòng",
    "Hậu Giang": "Hậu Giang",
    "Hòa Bình": "Hòa Bình",
    "Hưng Yên": "Hưng Yên",
    "Khánh Hòa": "Khánh Hòa",
    "Kiên Giang": "Kiên Giang",
    "Kon Tum": "Kon Tum",
    "Lai Châu": "Điện Biên",
    "Lâm Đồng": "Bình Thuận",
    "Lạng Sơn": "Bắc Giang",
    "Lào Cai": "Hà Giang",
    "Long An": "Thành phố Hồ Chí Minh",
    "Nam Định": "Hà Nam",
    "Nghệ An": "Hà Tĩnh",
    "Ninh Bình": "Hà Nam",
    "Ninh Thuận": "Khánh Hòa",
    "Phú Thọ": "Hà Nội",
    "Phú Yên": "Khánh Hòa",
    "Quảng Bình": "Hà Tĩnh",
    "Quảng Nam": "Đà Nẵng",
    "Quảng Ngãi": "Bình Định",
    "Quảng Ninh": "Hải Phòng",
    "Quảng Trị": "Đà Nẵng",
    "Sóc Trăng": "Hậu Giang",
    "Sơn La": "Điện Biên",
    "Tây Ninh": "Bình Dương",
    "Thái Bình": "Hưng Yên",
    "Thái Nguyên": "Bắc Giang",
    "Thanh Hóa": "Hà Tĩnh",
    "Thành phố Hồ Chí Minh": "Thành phố Hồ Chí Minh",
    "Thừa Thiên - Huế": "Đà Nẵng",
    "Tiền Giang": "Đồng Tháp",
    "Trà Vinh": "Bến Tre",
    "Tuyên Quang": "Hà Giang",
    "Vĩnh Long": "Đồng Tháp",
    "Vĩnh Phúc": "Hà Nội",
    "Yên Bái": "Hà Giang",
}

DONG_NAI_BASE = "Đồng Nai"
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

PROVINCE_PATTERN = re.compile(r"(?i)\b(?:thành\s*phố|tp\.?)\s*đồng\s*nai\b")
PLAIN_DONG_NAI_PATTERN = re.compile(r"(?i)\b(?:t(?:ỉnh)?\.?\s*)?(?:đồng\s*na[iy]|dong\s*nai|đồng\s*nao)\b")
CITY_RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"(?i)\b(?:tp\.?\s*|thành\s*phố\s*|thị\s*xã\s*)?bi[eê]n\s*h[oò]a\b"), "Thành phố Biên Hòa"),
    (re.compile(r"(?i)\b(?:tp\.?\s*|thành\s*phố\s*|thị\s*xã\s*)?long\s*kh[aá]nh\b"), "Thành phố Long Khánh"),
]


def normalize_key(value: str) -> str:
    lowered = value.lower().strip()
    lowered = lowered.replace("đ", "d")
    lowered = unicodedata.normalize("NFD", lowered)
    lowered = "".join(ch for ch in lowered if unicodedata.category(ch) != "Mn")
    lowered = re.sub(r"\b(tinh|thanh pho)\b", " ", lowered)
    lowered = re.sub(r"[^a-z0-9]+", " ", lowered)
    return re.sub(r"\s+", " ", lowered).strip()


def extract_base_name(full_name: str) -> str:
    if full_name.startswith("Tỉnh "):
        return full_name[5:]
    if full_name.startswith("Thành phố "):
        return full_name[10:]
    return full_name


def parse_source_metadata(raw_value: str | None) -> dict[str, Any]:
    if not raw_value:
        return {}
    try:
        parsed = json.loads(raw_value)
        return parsed if isinstance(parsed, dict) else {}
    except json.JSONDecodeError:
        return {}


def clean_segment(segment: str) -> str:
    value = re.sub(r"\s+", " ", segment.strip(" ,.;"))
    return value.strip()


def normalize_dong_nai_address(address: str) -> str:
    working = PROVINCE_PATTERN.sub("Tỉnh Đồng Nai", address or "")
    working = PLAIN_DONG_NAI_PATTERN.sub("Tỉnh Đồng Nai", working)
    for pattern, replacement in CITY_RULES:
        working = pattern.sub(replacement, working)

    parts = [clean_segment(part) for part in working.split(",") if clean_segment(part)]
    result: list[str] = []
    seen: set[str] = set()
    for part in parts:
        key = normalize_key(part)
        if key and key not in seen and key != normalize_key("Tỉnh Đồng Nai"):
            result.append(part)
            seen.add(key)
    return ", ".join(result + ["Tỉnh Đồng Nai"]) if result else "Tỉnh Đồng Nai"


def infer_city(address: str, province_name: str) -> str:
    if province_name == "Tỉnh Đồng Nai":
        for pattern, replacement in CITY_RULES:
            if pattern.search(address):
                return replacement
    return province_name


def build_document(place: DiaDiem, province_name: str, address: str, city_name: str, category_label: str) -> str:
    parts = [
        f"Tên: {place.tenDiaDiem}",
        f"Tỉnh thành: {province_name}",
        f"Khu vực: {city_name}",
        f"Loại: {category_label}",
    ]
    if address:
        parts.append(f"Địa chỉ: {address}")
    if place.moTa:
        parts.append(f"Mô tả: {place.moTa.strip()}")
    return ". ".join(parts)


def build_metadata(place: DiaDiem, province_name: str, address: str, city_name: str, source_meta: dict[str, Any]) -> dict[str, Any]:
    raw_category = str(source_meta.get("category") or place.loaiDiaDiem)
    return {
        "name": str(place.tenDiaDiem)[:200],
        "city": city_name[:100],
        "province": province_name[:100],
        "category": CATEGORY_MAPPING.get(raw_category, raw_category)[:100],
        "description": str(place.moTa or "")[:500],
        "address": str(address or "")[:300],
        "source": str(source_meta.get("source") or "database")[:100],
        "place_id": int(place.maDiaDiem),
        "item_id": str(source_meta.get("item_id") or ""),
        "detail_url": str(source_meta.get("detail_url") or "")[:500],
        "price": float(place.giaVe or 0.0),
        "rating": float(place.danhGiaTrungBinh or 0.0),
        "latitude": float(place.viDo or 0.0),
        "longitude": float(place.kinhDo or 0.0),
    }


def get_collection():
    client = chromadb.HttpClient(host=CHROMA_HOST, port=CHROMA_PORT)
    return client.get_or_create_collection(name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"})


def main() -> None:
    collection = get_collection()
    canonical_by_base = {base: {"full_name": full_name, "description": description} for base, full_name, description in CANONICAL_REGIONS}
    changed_place_ids: set[int] = set()
    upsert_payloads: list[dict[str, Any]] = []
    counters = {
        "regions_after": 0,
        "fk_moves": 0,
        "province_rows_deleted": 0,
        "province_rows_updated": 0,
        "dong_nai_address_updates": 0,
        "vector_upserts": 0,
    }

    with transaction.atomic():
        existing_rows = list(TinhThanh.objects.select_for_update().all().order_by("maTinhThanh"))
        existing_by_norm = {normalize_key(row.tenTinhThanh): row for row in existing_rows}
        canonical_rows: dict[str, TinhThanh] = {}

        for base, meta in canonical_by_base.items():
            norm_full = normalize_key(meta["full_name"])
            norm_base = normalize_key(base)
            row = existing_by_norm.get(norm_full) or existing_by_norm.get(norm_base)
            if row is None:
                row = TinhThanh.objects.create(
                    tenTinhThanh=meta["full_name"],
                    moTa=meta["description"],
                )
                counters["province_rows_updated"] += 1
            else:
                changed = False
                if row.tenTinhThanh != meta["full_name"]:
                    row.tenTinhThanh = meta["full_name"]
                    changed = True
                if (row.moTa or "").strip() != meta["description"]:
                    row.moTa = meta["description"]
                    changed = True
                if changed:
                    row.save(update_fields=["tenTinhThanh", "moTa", "updated_at"])
                    counters["province_rows_updated"] += 1
            canonical_rows[base] = row

        # Reload after potential creates/renames to avoid stale uniqueness collisions.
        existing_rows = list(TinhThanh.objects.select_for_update().all().order_by("maTinhThanh"))
        for row in existing_rows:
            source_base = extract_base_name(row.tenTinhThanh)
            target_base = TARGET_BY_SOURCE.get(source_base)
            if not target_base:
                continue
            target_row = canonical_rows[target_base]
            if row.pk != target_row.pk:
                moved = DiaDiem.objects.filter(maTinhThanh=row).update(maTinhThanh=target_row)
                if moved:
                    counters["fk_moves"] += moved
                    changed_place_ids.update(
                        DiaDiem.objects.filter(maTinhThanh=target_row).values_list("maDiaDiem", flat=True)
                    )
                with connection.cursor() as cursor:
                    cursor.execute("UPDATE LICHTRINH SET maTinhThanh = %s WHERE maTinhThanh = %s", [target_row.pk, row.pk])
                    cursor.execute("UPDATE YEUCAULOTRINH SET maTinhThanhDiemDi = %s WHERE maTinhThanhDiemDi = %s", [target_row.pk, row.pk])
                    cursor.execute("UPDATE YEUCAULOTRINH SET maTinhThanhDiemDen = %s WHERE maTinhThanhDiemDen = %s", [target_row.pk, row.pk])

        rows_to_delete = [
            row.pk
            for row in list(TinhThanh.objects.select_for_update().all())
            if row.pk not in {item.pk for item in canonical_rows.values()}
            and not DiaDiem.objects.filter(maTinhThanh=row).exists()
        ]
        if rows_to_delete:
            with connection.cursor() as cursor:
                for row_id in rows_to_delete:
                    cursor.execute("DELETE FROM TINHTHANH WHERE maTinhThanh = %s", [row_id])
                    counters["province_rows_deleted"] += 1

        dong_nai_row = canonical_rows[DONG_NAI_BASE]
        for place in DiaDiem.objects.select_for_update().filter(maTinhThanh=dong_nai_row).order_by("maDiaDiem"):
            normalized_address = normalize_dong_nai_address(place.diaChi or "")
            if normalized_address != (place.diaChi or ""):
                place.diaChi = normalized_address
                place.save(update_fields=["diaChi", "lanCapNhatCuoi"])
                counters["dong_nai_address_updates"] += 1
                changed_place_ids.add(place.maDiaDiem)

        # Sync all POIs under canonical rows whose province label might have changed.
        sync_queryset = DiaDiem.objects.filter(maTinhThanh__in=canonical_rows.values()).select_related("maTinhThanh")
        if changed_place_ids:
            sync_queryset = sync_queryset.filter(maDiaDiem__in=changed_place_ids)
        else:
            sync_queryset = DiaDiem.objects.none()

        for place in sync_queryset.iterator():
            source_meta = parse_source_metadata(place.dacDiem)
            province_name = place.maTinhThanh.tenTinhThanh
            address = place.diaChi or ""
            city_name = infer_city(address, province_name)
            category_label = LOAI_MAPPING.get(str(source_meta.get("category") or place.loaiDiaDiem), place.loaiDiaDiem)
            vector_id = str(source_meta.get("item_id") or f"db_place_{place.maDiaDiem}")
            upsert_payloads.append(
                {
                    "id": vector_id,
                    "document": build_document(place, province_name, address, city_name, category_label),
                    "metadata": build_metadata(place, province_name, address, city_name, source_meta),
                }
            )

        counters["regions_after"] = TinhThanh.objects.count()

        def sync_vectors() -> None:
            batch_size = 200
            for index in range(0, len(upsert_payloads), batch_size):
                batch = upsert_payloads[index:index + batch_size]
                collection.upsert(
                    ids=[item["id"] for item in batch],
                    documents=[item["document"] for item in batch],
                    metadatas=[item["metadata"] for item in batch],
                )
            counters["vector_upserts"] = len(upsert_payloads)

        transaction.on_commit(sync_vectors)

    print(json.dumps(counters, ensure_ascii=False))


if __name__ == "__main__":
    main()
