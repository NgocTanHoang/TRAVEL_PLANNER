#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Clean and enrich audited province data using Django ORM."""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import subprocess
import sys
import time
import unicodedata
from pathlib import Path
from typing import Any

import django
import requests
from django.db import IntegrityError, connection, transaction
from django.db.models import Q


if sys.platform == "win32":
    if sys.stdout.encoding != "utf-8":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    if sys.stderr.encoding != "utf-8":
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace", line_buffering=True)


BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent
DATA_DIR = REPO_ROOT / "data"
DEFAULT_AUDIT_REPORT = DATA_DIR / "audit_quang_ninh.json"
AUDIT_SCRIPT = BACKEND_DIR / "scripts" / "audit_province_data.py"

sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "vivu_core.settings")
django.setup()

from apps.itineraries.models import DongGop, LichTrinhAIDiaDiem, LichTrinhDiaDiem  # noqa: E402
from apps.places.models import DanhGia, DiaDiem, DiaDiemYeuThich, HinhAnhDiaDiem, TinhThanh  # noqa: E402
from apps.users.models import LichSuTimKiem  # noqa: E402


VIETNAM_LAT_RANGE = (8.5, 23.5)
VIETNAM_LON_RANGE = (102.0, 110.0)
NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

FALLBACK_IMAGES = {
    "rest": [
        "https://images.unsplash.com/photo-1504674900247-0877df9cc836?auto=format&fit=crop&w=1600&q=80",
        "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=1600&q=80",
        "https://images.unsplash.com/photo-1559847844-5315695dadae?auto=format&fit=crop&w=1600&q=80",
        "https://images.unsplash.com/photo-1544025162-d76694265947?auto=format&fit=crop&w=1600&q=80",
        "https://images.unsplash.com/photo-1559339352-11d035aa65de?auto=format&fit=crop&w=1600&q=80",
    ],
    "cslt": [
        "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?auto=format&fit=crop&w=1600&q=80",
        "https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?auto=format&fit=crop&w=1600&q=80",
        "https://images.unsplash.com/photo-1505693416388-ac5ce068fe85?auto=format&fit=crop&w=1600&q=80",
        "https://images.unsplash.com/photo-1445019980597-93fa8acb246c?auto=format&fit=crop&w=1600&q=80",
        "https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&w=1600&q=80",
    ],
    "dest": [
        "https://images.unsplash.com/photo-1528127269322-539801943592?auto=format&fit=crop&w=1600&q=80",
        "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=1600&q=80",
        "https://images.unsplash.com/photo-1537996194471-e657df975ab4?auto=format&fit=crop&w=1600&q=80",
        "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=1600&q=80",
        "https://images.unsplash.com/photo-1469474968028-56623f02e42e?auto=format&fit=crop&w=1600&q=80",
    ],
    "shop": [
        "https://images.unsplash.com/photo-1481437156560-3205f6a55735?auto=format&fit=crop&w=1600&q=80",
        "https://images.unsplash.com/photo-1521334884684-d80222895322?auto=format&fit=crop&w=1600&q=80",
        "https://images.unsplash.com/photo-1512436991641-6745cdb1723f?auto=format&fit=crop&w=1600&q=80",
        "https://images.unsplash.com/photo-1483985988355-763728e1935b?auto=format&fit=crop&w=1600&q=80",
        "https://images.unsplash.com/photo-1555529669-e69e7aa0ba9a?auto=format&fit=crop&w=1600&q=80",
    ],
    "vcgt": [
        "https://images.unsplash.com/photo-1513151233558-d860c5398176?auto=format&fit=crop&w=1600&q=80",
        "https://images.unsplash.com/photo-1492684223066-81342ee5ff30?auto=format&fit=crop&w=1600&q=80",
        "https://images.unsplash.com/photo-1505236858219-8359eb29e329?auto=format&fit=crop&w=1600&q=80",
        "https://images.unsplash.com/photo-1514525253161-7a46d19cd819?auto=format&fit=crop&w=1600&q=80",
        "https://images.unsplash.com/photo-1500534623283-312aade485b7?auto=format&fit=crop&w=1600&q=80",
    ],
}

LOAI_TO_CATEGORY = {
    "khach_san": "cslt",
    "dia_danh": "dest",
    "nha_hang": "rest",
    "mua_sam": "shop",
    "giai_tri": "vcgt",
}

DISTRICT_HINTS = (
    "quận",
    "huyện",
    "thị xã",
    "thị trấn",
    "thành phố",
    "phường",
    "xã",
    "tp.",
    "tp ",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Dọn dữ liệu theo file audit và verify lại bằng audit script.")
    parser.add_argument(
        "--audit-report",
        default=str(DEFAULT_AUDIT_REPORT),
        help="Đường dẫn tới file audit JSON. Mặc định: data/audit_quang_ninh.json",
    )
    parser.add_argument(
        "--geocode-delay",
        type=float,
        default=1.0,
        help="Số giây nghỉ giữa các request Nominatim. Mặc định: 1.0",
    )
    parser.add_argument(
        "--province",
        default=None,
        help="Override tên/mã tỉnh khi chạy audit verify cuối. Nếu bỏ trống sẽ lấy từ report.",
    )
    parser.add_argument(
        "--min-pois",
        type=int,
        default=None,
        help="Override ngưỡng min-pois khi gọi lại audit verify.",
    )
    return parser.parse_args()


def load_report(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"[ERROR] Không tìm thấy file audit report tại {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def parse_json_object(raw_value: str | None) -> dict[str, Any]:
    if not raw_value:
        return {}
    try:
        data = json.loads(raw_value)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


def dump_json_object(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True)


def normalize_space(value: str | None) -> str:
    return re.sub(r"\s+", " ", (value or "").replace("\xa0", " ")).strip()


def ascii_fold(value: str | None) -> str:
    text = normalize_space(value).lower().replace("đ", "d")
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    text = re.sub(r"[^a-z0-9, ]+", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip(" ,")


def is_valid_coordinate(lat: float | None, lon: float | None) -> bool:
    if lat is None or lon is None:
        return False
    if lat == 0 or lon == 0:
        return False
    return VIETNAM_LAT_RANGE[0] <= lat <= VIETNAM_LAT_RANGE[1] and VIETNAM_LON_RANGE[0] <= lon <= VIETNAM_LON_RANGE[1]


def classify_category(place: DiaDiem) -> str:
    metadata = parse_json_object(place.dacDiem)
    category = metadata.get("category")
    if isinstance(category, str) and category in FALLBACK_IMAGES:
        return category
    return LOAI_TO_CATEGORY.get(place.loaiDiaDiem, "dest")


def extract_district(address: str | None) -> str | None:
    if not address:
        return None
    parts = [part.strip() for part in re.split(r"[,;/|-]+", normalize_space(address)) if part.strip()]
    for part in reversed(parts):
        lowered = part.lower()
        if any(hint in lowered for hint in DISTRICT_HINTS):
            return part
    return parts[-1] if parts else None


def build_duplicate_groups(province: TinhThanh) -> list[dict[str, Any]]:
    duplicate_map: dict[tuple[str, str], list[DiaDiem]] = {}
    for place in DiaDiem.objects.filter(maTinhThanh=province).only("maDiaDiem", "tenDiaDiem", "diaChi"):
        district = extract_district(place.diaChi)
        if not district:
            continue
        key = (ascii_fold(place.tenDiaDiem), ascii_fold(district))
        duplicate_map.setdefault(key, []).append(place)

    groups: list[dict[str, Any]] = []
    for places in duplicate_map.values():
        if len(places) > 1:
            groups.append(
                {
                    "tenDiaDiem": places[0].tenDiaDiem,
                    "district": extract_district(places[0].diaChi) or "",
                    "place_ids": [place.maDiaDiem for place in places],
                }
            )
    groups.sort(key=lambda item: (item["tenDiaDiem"], item["district"]))
    return groups


def text_score(value: str | None) -> int:
    return len((value or "").strip())


def metadata_score(place: DiaDiem) -> int:
    metadata = parse_json_object(place.dacDiem)
    score = 0
    score += text_score(place.tenDiaDiem) * 2
    score += text_score(place.moTa)
    score += text_score(place.diaChi)
    score += text_score(place.dacDiem)
    score += text_score(place.tienNghi)
    score += 40 if is_valid_coordinate(place.viDo, place.kinhDo) else 0
    score += 20 if place.giaVe not in (None, 0) else 0
    score += 10 if text_score(place.gioMoCua) else 0
    score += 10 if text_score(place.gioDongCua) else 0
    score += len([value for value in metadata.values() if value not in (None, "", [], {})]) * 3
    score += place.hinh_anhs.count() * 2
    return score


def merge_metadata(primary_raw: str | None, secondary_raw: str | None) -> str:
    primary_data = parse_json_object(primary_raw)
    secondary_data = parse_json_object(secondary_raw)
    if not primary_data and not secondary_data:
        return primary_raw or secondary_raw or ""

    merged = dict(primary_data)
    for key, value in secondary_data.items():
        existing = merged.get(key)
        if existing in (None, "", [], {}):
            merged[key] = value
        elif isinstance(existing, str) and isinstance(value, str) and len(value.strip()) > len(existing.strip()):
            merged[key] = value
    return dump_json_object(merged)


def choose_primary(places: list[DiaDiem]) -> DiaDiem:
    ranked = sorted(
        places,
        key=lambda place: (metadata_score(place), text_score(place.dacDiem), text_score(place.moTa), -place.maDiaDiem),
        reverse=True,
    )
    return ranked[0]


def merge_place_fields(primary: DiaDiem, secondary: DiaDiem) -> list[str]:
    updated_fields: list[str] = []

    string_fields = ["tenDiaDiem", "moTa", "diaChi", "dienThoai", "website", "gioMoCua", "gioDongCua", "tienNghi"]
    for field in string_fields:
        primary_value = getattr(primary, field) or ""
        secondary_value = getattr(secondary, field) or ""
        if not primary_value.strip() and secondary_value.strip():
            setattr(primary, field, secondary_value)
            updated_fields.append(field)
        elif field in {"moTa", "diaChi", "tienNghi"} and len(secondary_value.strip()) > len(primary_value.strip()):
            setattr(primary, field, secondary_value)
            updated_fields.append(field)

    merged_dacdiem = merge_metadata(primary.dacDiem, secondary.dacDiem)
    if merged_dacdiem != (primary.dacDiem or ""):
        primary.dacDiem = merged_dacdiem
        updated_fields.append("dacDiem")

    if not is_valid_coordinate(primary.viDo, primary.kinhDo) and is_valid_coordinate(secondary.viDo, secondary.kinhDo):
        primary.viDo = secondary.viDo
        primary.kinhDo = secondary.kinhDo
        updated_fields.extend(["viDo", "kinhDo"])

    if primary.giaVe in (None, 0) and secondary.giaVe not in (None, 0):
        primary.giaVe = secondary.giaVe
        updated_fields.append("giaVe")

    if secondary.danhGiaTrungBinh > primary.danhGiaTrungBinh:
        primary.danhGiaTrungBinh = secondary.danhGiaTrungBinh
        updated_fields.append("danhGiaTrungBinh")

    if secondary.soLuotDanhGia > primary.soLuotDanhGia:
        primary.soLuotDanhGia = secondary.soLuotDanhGia
        updated_fields.append("soLuotDanhGia")

    if secondary.soLuotXem > primary.soLuotXem:
        primary.soLuotXem = secondary.soLuotXem
        updated_fields.append("soLuotXem")

    return sorted(set(updated_fields))


def reassign_reviews(primary: DiaDiem, secondary: DiaDiem, stats: dict[str, int]) -> None:
    for review in DanhGia.objects.filter(maDiaDiem=secondary):
        existing = DanhGia.objects.filter(maDiaDiem=primary, maNguoiDung=review.maNguoiDung).exclude(pk=review.pk).first()
        if existing:
            if len(review.noiDung or "") > len(existing.noiDung or ""):
                existing.noiDung = review.noiDung
            if review.diemDanhGia > existing.diemDanhGia:
                existing.diemDanhGia = review.diemDanhGia
            existing.soLuotThich = max(existing.soLuotThich, review.soLuotThich)
            existing.save(update_fields=["noiDung", "diemDanhGia", "soLuotThich", "lanCapNhatCuoi"])
            review.delete()
            stats["dedupe_review_conflicts_resolved"] += 1
        else:
            review.maDiaDiem = primary
            review.save(update_fields=["maDiaDiem"])
            stats["dedupe_reviews_reassigned"] += 1


def reassign_favorites(primary: DiaDiem, secondary: DiaDiem, stats: dict[str, int]) -> None:
    for favorite in DiaDiemYeuThich.objects.filter(maDiaDiem=secondary):
        exists = DiaDiemYeuThich.objects.filter(maDiaDiem=primary, maNguoiDung=favorite.maNguoiDung).exclude(pk=favorite.pk).exists()
        if exists:
            favorite.delete()
            stats["dedupe_favorite_conflicts_resolved"] += 1
        else:
            favorite.maDiaDiem = primary
            favorite.save(update_fields=["maDiaDiem"])
            stats["dedupe_favorites_reassigned"] += 1


def reassign_itinerary_rows(primary: DiaDiem, secondary: DiaDiem, stats: dict[str, int]) -> None:
    for row in LichTrinhDiaDiem.objects.filter(maDiaDiem=secondary):
        exists = LichTrinhDiaDiem.objects.filter(
            maLichTrinh=row.maLichTrinh,
            maDiaDiem=primary,
            ngayThamQuan=row.ngayThamQuan,
        ).exclude(pk=row.pk).first()
        if exists:
            if not (exists.ghiChu or "").strip() and (row.ghiChu or "").strip():
                exists.ghiChu = row.ghiChu
            if exists.chiPhiUocTinh in (None, 0) and row.chiPhiUocTinh not in (None, 0):
                exists.chiPhiUocTinh = row.chiPhiUocTinh
            if exists.thuTu is None and row.thuTu is not None:
                exists.thuTu = row.thuTu
            exists.save(update_fields=["ghiChu", "chiPhiUocTinh", "thuTu"])
            row.delete()
            stats["dedupe_itinerary_conflicts_resolved"] += 1
        else:
            row.maDiaDiem = primary
            row.save(update_fields=["maDiaDiem"])
            stats["dedupe_itinerary_rows_reassigned"] += 1

    for row in LichTrinhAIDiaDiem.objects.filter(maDiaDiem=secondary):
        exists = LichTrinhAIDiaDiem.objects.filter(
            maLichTrinhAI=row.maLichTrinhAI,
            maDiaDiem=primary,
            ngayThamQuan=row.ngayThamQuan,
        ).exclude(pk=row.pk).first()
        if exists:
            if not (exists.ghiChu or "").strip() and (row.ghiChu or "").strip():
                exists.ghiChu = row.ghiChu
            if exists.chiPhiUocTinh in (None, 0) and row.chiPhiUocTinh not in (None, 0):
                exists.chiPhiUocTinh = row.chiPhiUocTinh
            if exists.thuTu is None and row.thuTu is not None:
                exists.thuTu = row.thuTu
            exists.save(update_fields=["ghiChu", "chiPhiUocTinh", "thuTu"])
            row.delete()
            stats["dedupe_ai_itinerary_conflicts_resolved"] += 1
        else:
            row.maDiaDiem = primary
            row.save(update_fields=["maDiaDiem"])
            stats["dedupe_ai_itinerary_rows_reassigned"] += 1


def reassign_misc_tables(primary: DiaDiem, secondary: DiaDiem, stats: dict[str, int]) -> None:
    updated = LichSuTimKiem.objects.filter(maDiaDiem=secondary).update(maDiaDiem=primary)
    stats["dedupe_search_rows_reassigned"] += updated

    updated = DongGop.objects.filter(maDiaDiem=secondary).update(maDiaDiem=primary)
    stats["dedupe_contribution_rows_reassigned"] += updated


def reassign_images(primary: DiaDiem, secondary: DiaDiem, stats: dict[str, int]) -> None:
    existing_urls = set(primary.hinh_anhs.values_list("urlHinhAnh", flat=True))
    for image in HinhAnhDiaDiem.objects.filter(maDiaDiem=secondary):
        if image.urlHinhAnh in existing_urls:
            image.delete()
            stats["dedupe_image_conflicts_resolved"] += 1
        else:
            image.maDiaDiem = primary
            image.save(update_fields=["maDiaDiem"])
            existing_urls.add(image.urlHinhAnh)
            stats["dedupe_images_reassigned"] += 1


def delete_place_record(place_id: int) -> None:
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM DIADIEM WHERE maDiaDiem = %s", [place_id])


def deduplicate_group(group: dict[str, Any], stats: dict[str, int]) -> None:
    places = list(
        DiaDiem.objects.filter(maDiaDiem__in=group["place_ids"]).prefetch_related("hinh_anhs")
    )
    if len(places) < 2:
        return

    primary = choose_primary(places)
    secondaries = [place for place in places if place.maDiaDiem != primary.maDiaDiem]

    primary_updates: list[str] = []
    for secondary in secondaries:
        primary_updates.extend(merge_place_fields(primary, secondary))
    if primary_updates:
        primary.save(update_fields=sorted(set(primary_updates)) + ["lanCapNhatCuoi"])
        stats["dedupe_primary_records_enriched"] += 1

    for secondary in secondaries:
        reassign_reviews(primary, secondary, stats)
        reassign_favorites(primary, secondary, stats)
        reassign_itinerary_rows(primary, secondary, stats)
        reassign_misc_tables(primary, secondary, stats)
        reassign_images(primary, secondary, stats)
        delete_place_record(secondary.maDiaDiem)
        stats["dedupe_secondary_deleted"] += 1

    stats["dedupe_groups_processed"] += 1


def repair_text_once(value: str) -> str:
    candidates: list[str] = [value]
    for source_encoding in ("latin1", "cp1252"):
        try:
            candidates.append(value.encode(source_encoding).decode("utf-8"))
        except (UnicodeEncodeError, UnicodeDecodeError):
            pass
    best = value
    best_score = mojibake_score(value)
    for candidate in candidates[1:]:
        score = mojibake_score(candidate)
        if score < best_score:
            best = candidate
            best_score = score
    return best


def mojibake_score(value: str | None) -> int:
    if not value:
        return 0
    score = 0
    for marker in ("Ã", "Â", "Ä", "Å", "Æ", "Ð", "Ñ", "�", "â€™", "â€œ", "â€", "á»", "áº"):
        score += value.count(marker) * 4
    score += value.count("?")
    return score


def repair_json_text(raw_value: str | None) -> tuple[str | None, bool]:
    if not raw_value:
        return raw_value, False
    try:
        data = json.loads(raw_value)
    except json.JSONDecodeError:
        repaired = repair_text_once(raw_value)
        return repaired, repaired != raw_value

    changed = False

    def walk(value: Any) -> Any:
        nonlocal changed
        if isinstance(value, str):
            repaired = repair_text_once(value)
            if repaired != value:
                changed = True
            return repaired
        if isinstance(value, list):
            return [walk(item) for item in value]
        if isinstance(value, dict):
            return {key: walk(item) for key, item in value.items()}
        return value

    repaired_data = walk(data)
    if not changed:
        return raw_value, False
    return json.dumps(repaired_data, ensure_ascii=False, sort_keys=True), True


def fix_mojibake_for_place(place: DiaDiem, stats: dict[str, int]) -> None:
    updated_fields: list[str] = []
    for field in ("tenDiaDiem", "moTa", "diaChi", "dienThoai", "website", "gioMoCua", "gioDongCua", "tienNghi"):
        value = getattr(place, field)
        if value:
            repaired = repair_text_once(value)
            if repaired != value:
                setattr(place, field, repaired)
                updated_fields.append(field)

    repaired_dacdiem, changed = repair_json_text(place.dacDiem)
    if changed:
        place.dacDiem = repaired_dacdiem
        updated_fields.append("dacDiem")

    if updated_fields:
        place.save(update_fields=sorted(set(updated_fields)) + ["lanCapNhatCuoi"])
        stats["mojibake_places_fixed"] += 1


class NominatimClient:
    def __init__(self, delay_seconds: float) -> None:
        self.delay_seconds = delay_seconds
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "ViVuDataCleaner/1.0 (+https://github.com/NgocTanHoang/TRAVEL_PLANNER)",
                "Accept-Language": "vi,en",
            }
        )
        self.cache: dict[str, tuple[float, float] | None] = {}

    def geocode(self, query: str) -> tuple[float, float] | None:
        if query in self.cache:
            return self.cache[query]

        params = {"q": query, "format": "jsonv2", "limit": 1, "countrycodes": "vn"}
        try:
            response = self.session.get(NOMINATIM_URL, params=params, timeout=20)
            response.raise_for_status()
            payload = response.json()
        except Exception:
            self.cache[query] = None
            time.sleep(self.delay_seconds)
            return None

        time.sleep(self.delay_seconds)
        if not payload:
            self.cache[query] = None
            return None

        try:
            lat = float(payload[0]["lat"])
            lon = float(payload[0]["lon"])
        except (KeyError, TypeError, ValueError):
            self.cache[query] = None
            return None

        result = (lat, lon) if is_valid_coordinate(lat, lon) else None
        self.cache[query] = result
        return result


def build_geocode_queries(place: DiaDiem, province: TinhThanh) -> list[str]:
    address = normalize_space(place.diaChi)
    district = extract_district(address)
    province_name = ascii_fold(province.tenTinhThanh.replace("Tỉnh", "").replace("Thành phố", ""))

    queries = [
        ", ".join(filter(None, [ascii_fold(place.tenDiaDiem), ascii_fold(address)])),
        ascii_fold(address),
        ", ".join(filter(None, [ascii_fold(place.tenDiaDiem), ascii_fold(district), province_name])),
        ", ".join(filter(None, [ascii_fold(district), province_name])),
        province_name,
    ]

    deduped: list[str] = []
    for query in queries:
        query = normalize_space(query)
        if query and query not in deduped:
            deduped.append(query)
    return deduped


def fix_invalid_coordinates(province: TinhThanh, client: NominatimClient, stats: dict[str, int]) -> None:
    invalid_places = list(
        DiaDiem.objects.filter(maTinhThanh=province).filter(
            Q(viDo__isnull=True)
            | Q(kinhDo__isnull=True)
            | Q(viDo=0)
            | Q(kinhDo=0)
            | Q(viDo__lt=VIETNAM_LAT_RANGE[0])
            | Q(viDo__gt=VIETNAM_LAT_RANGE[1])
            | Q(kinhDo__lt=VIETNAM_LON_RANGE[0])
            | Q(kinhDo__gt=VIETNAM_LON_RANGE[1])
        )
    )

    for place in invalid_places:
        coordinates = None
        for query in build_geocode_queries(place, province):
            coordinates = client.geocode(query)
            if coordinates:
                break

        if coordinates:
            place.viDo, place.kinhDo = coordinates
            if place.trangThai == "inactive":
                place.trangThai = "active"
                place.save(update_fields=["viDo", "kinhDo", "trangThai", "lanCapNhatCuoi"])
            else:
                place.save(update_fields=["viDo", "kinhDo", "lanCapNhatCuoi"])
            stats["coordinates_fixed"] += 1
        else:
            if place.trangThai != "inactive":
                place.trangThai = "inactive"
                place.save(update_fields=["trangThai", "lanCapNhatCuoi"])
            stats["coordinates_unresolved_inactivated"] += 1


def ensure_fallback_image(place: DiaDiem, stats: dict[str, int]) -> None:
    if place.hinh_anhs.exists():
        return
    category = classify_category(place)
    candidates = FALLBACK_IMAGES.get(category, FALLBACK_IMAGES["dest"])
    image_url = candidates[place.maDiaDiem % len(candidates)]
    HinhAnhDiaDiem.objects.create(
        maDiaDiem=place,
        urlHinhAnh=image_url,
        moTa=f"Fallback image for {place.tenDiaDiem}",
        laChinh=True,
    )
    stats["fallback_images_created"] += 1


def backfill_images(province: TinhThanh, stats: dict[str, int]) -> None:
    places = DiaDiem.objects.filter(maTinhThanh=province).prefetch_related("hinh_anhs")
    for place in places:
        ensure_fallback_image(place, stats)


def verify_with_audit(report: dict[str, Any], province_override: str | None, min_pois_override: int | None) -> int:
    province_arg = province_override or report["province"]["name"]
    min_pois = min_pois_override if min_pois_override is not None else int(report.get("min_pois", 500))
    command = [
        sys.executable,
        str(AUDIT_SCRIPT),
        "--province",
        str(province_arg),
        "--min-pois",
        str(min_pois),
    ]
    print()
    print("[VERIFY] Running audit again...")
    completed = subprocess.run(command, cwd=str(REPO_ROOT), check=False)
    return completed.returncode


def print_stats(stats: dict[str, int]) -> None:
    print("=" * 96)
    print("CLEAN & ENRICH SUMMARY")
    print("=" * 96)
    for key in sorted(stats):
        print(f"{key}: {stats[key]}")


def run_cleanup(args: argparse.Namespace) -> dict[str, int]:
    report = load_report(Path(args.audit_report))
    province_id = int(report["province"]["id"])
    province = TinhThanh.objects.get(maTinhThanh=province_id)
    stats: dict[str, int] = {
        "dedupe_groups_processed": 0,
        "dedupe_primary_records_enriched": 0,
        "dedupe_secondary_deleted": 0,
        "dedupe_reviews_reassigned": 0,
        "dedupe_review_conflicts_resolved": 0,
        "dedupe_favorites_reassigned": 0,
        "dedupe_favorite_conflicts_resolved": 0,
        "dedupe_itinerary_rows_reassigned": 0,
        "dedupe_itinerary_conflicts_resolved": 0,
        "dedupe_ai_itinerary_rows_reassigned": 0,
        "dedupe_ai_itinerary_conflicts_resolved": 0,
        "dedupe_search_rows_reassigned": 0,
        "dedupe_contribution_rows_reassigned": 0,
        "dedupe_images_reassigned": 0,
        "dedupe_image_conflicts_resolved": 0,
        "mojibake_places_fixed": 0,
        "coordinates_fixed": 0,
        "coordinates_unresolved_inactivated": 0,
        "fallback_images_created": 0,
    }

    duplicate_groups = build_duplicate_groups(province)
    mojibake_samples = report.get("anomalies", {}).get("mojibake_samples", [])
    mojibake_ids = [item["maDiaDiem"] for item in mojibake_samples]
    client = NominatimClient(delay_seconds=args.geocode_delay)

    connection.disable_constraint_checking()
    with transaction.atomic():
        for group in duplicate_groups:
            deduplicate_group(group, stats)

        for place in DiaDiem.objects.filter(maDiaDiem__in=mojibake_ids):
            fix_mojibake_for_place(place, stats)

        fix_invalid_coordinates(province, client, stats)
        backfill_images(province, stats)

    print_stats(stats)
    verify_with_audit(report, args.province, args.min_pois)
    return stats


def main() -> None:
    args = parse_args()
    try:
        run_cleanup(args)
    except IntegrityError as exc:
        raise SystemExit(f"[ERROR] Transaction bị rollback do lỗi integrity: {exc}") from exc
    except Exception as exc:  # pragma: no cover - operational safety
        raise SystemExit(f"[ERROR] Script thất bại và không commit thay đổi: {exc}") from exc


if __name__ == "__main__":
    main()
