# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import re
import sys
import time
import unicodedata
import uuid
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import requests
from bs4 import BeautifulSoup, Tag
from django import setup as django_setup
from django.db import transaction
from django.utils import timezone


REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = REPO_ROOT / "vivu_backend"
SCRAPER_DIR = REPO_ROOT / "vivu_scraper"
OUTPUT_DIR = SCRAPER_DIR / "outputs"
STATE_PATH = OUTPUT_DIR / "scraping_state.json"

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "vivu_core.settings")
django_setup()

from apps.places.models import DiaDiem, TinhThanh  # noqa: E402
import scripts.scrape_vietnam_tourism_db as tourism_scraper  # noqa: E402


OVERPASS_ENDPOINTS: Tuple[str, ...] = (
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://lz4.overpass-api.de/api/interpreter",
)
DEFAULT_TIMEOUT = 90
DEFAULT_BATCH_SIZE = 500
DEFAULT_GIO_MO_CUA = "00:00:00"
DEFAULT_GIO_DONG_CUA = "23:59:59"
DEFAULT_TRANG_THAI = "active"
VECTOR_SYNC_BATCH_SIZE = 200

VIETNAM_PROVINCE_ALIASES: Dict[str, Sequence[str]] = {
    "ho chi minh": ("tp ho chi minh", "tphcm", "tp hcm", "sai gon"),
    "ha noi": ("tp ha noi",),
    "hai phong": ("tp hai phong",),
    "da nang": ("tp da nang",),
    "can tho": ("tp can tho",),
    "thua thien hue": ("hue", "tp hue"),
    "ba ria vung tau": ("vung tau", "tp vung tau"),
    "dak nong": ("dac nong", "gia nghia", "ta dung"),
    "dak lak": ("dac lak", "buon ma thuot", "buon ho"),
    "dong nai": ("bien hoa", "long khanh"),
    "quang ninh": ("ha long",),
    "lam dong": ("da lat",),
    "khanh hoa": ("nha trang",),
    "kien giang": ("phu quoc", "rach gia"),
}

OSM_CATEGORY_MAP: Tuple[Tuple[str, str, str], ...] = (
    ("tourism", "hotel", "khach_san"),
    ("tourism", "motel", "khach_san"),
    ("tourism", "guest_house", "khach_san"),
    ("amenity", "restaurant", "nha_hang"),
    ("amenity", "cafe", "nha_hang"),
    ("amenity", "fast_food", "nha_hang"),
    ("amenity", "bar", "nha_hang"),
    ("amenity", "pub", "nha_hang"),
    ("shop", "*", "mua_sam"),
    ("tourism", "*", "dia_danh"),
    ("historic", "*", "dia_danh"),
    ("natural", "*", "dia_danh"),
    ("leisure", "*", "giai_tri"),
    ("amenity", "*", "khac"),
)

OSM_QUERY_TEMPLATE = """
[out:json][timeout:{timeout}];
area["name"="{province_name}"]["boundary"="administrative"]->.searchArea;
(
  nwr["tourism"](area.searchArea);
  nwr["amenity"~"restaurant|cafe|fast_food|bar|pub"](area.searchArea);
  nwr["historic"](area.searchArea);
  nwr["natural"~"peak|bay|beach|cave|spring|waterfall|island"](area.searchArea);
  nwr["leisure"~"park|water_park|sports_centre|resort"](area.searchArea);
  nwr["shop"](area.searchArea);
);
out center tags;
"""


@dataclass(frozen=True)
class ProvinceRuntime:
    province_id: int
    province_name: str
    normalized_name: str
    latitude: Optional[float]
    longitude: Optional[float]


@dataclass
class BatchStats:
    created: int = 0
    updated: int = 0
    skipped: int = 0
    processed: int = 0


class CheckpointStore:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> Dict[str, Any]:
        if not self.path.exists():
            return self._default_state()
        try:
            state = json.loads(self.path.read_text(encoding="utf-8"))
            if not isinstance(state, dict):
                return self._default_state()
            merged = self._default_state()
            merged.update(state)
            return merged
        except (OSError, json.JSONDecodeError):
            return self._default_state()

    def save(self, state: Dict[str, Any]) -> None:
        serializable = dict(state)
        serializable["updated_at"] = timezone.now().isoformat()
        self.path.write_text(
            json.dumps(serializable, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )

    def mark_completed(self, state: Dict[str, Any]) -> None:
        state["status"] = "completed"
        state["current_province"] = None
        state["last_successful_page"] = 0
        self.save(state)

    @staticmethod
    def _default_state() -> Dict[str, Any]:
        return {
            "status": "idle",
            "source": None,
            "current_province": None,
            "completed_provinces": [],
            "last_successful_page": 0,
            "imported_records_count": 0,
            "updated_records_count": 0,
            "skipped_records_count": 0,
            "last_checkpoint_reason": "",
            "updated_at": None,
        }


class PlaceNormalizer:
    def __init__(self, province_lookup: Dict[str, ProvinceRuntime]) -> None:
        self.province_lookup = province_lookup
        self.alias_lookup = self._build_alias_lookup(province_lookup)

    def normalize_tourism_record(self, raw: Dict[str, Any], province: ProvinceRuntime) -> Dict[str, Any]:
        resolved_province = self._match_province(raw.get("diaChi"), province)
        source_item_id = raw.get("item_id") or self._extract_item_id(raw.get("detail_url", ""))
        source_identifier = str(source_item_id or raw.get("detail_url") or raw.get("tenDiaDiem") or "")
        record = self._base_record(
            source="tourism",
            province=resolved_province,
            source_identifier=source_identifier,
            name=str(raw.get("tenDiaDiem") or "").strip(),
            address=str(raw.get("diaChi") or "").strip(),
            description=str(raw.get("moTa") or "").strip(),
            category=self._map_tourism_category(str(raw.get("category") or "")),
            latitude=None,
            longitude=None,
            ticket_price=self._parse_price(raw.get("giaVe")),
            opening_hours=self._parse_opening_hours(
                raw.get("gioMoCua"),
                raw.get("gioDongCua"),
            ),
            phone=str(raw.get("dienThoai") or "").strip(),
            website=str(raw.get("website") or "").strip(),
            source_metadata={
                "category": raw.get("category"),
                "item_id": source_item_id,
                "detail_url": raw.get("detail_url"),
                "images": list(raw.get("images") or []),
                "email": raw.get("email") or "",
            },
        )
        return record

    def normalize_osm_record(self, raw: Dict[str, Any], province: ProvinceRuntime) -> Dict[str, Any]:
        tags = raw.get("tags") or {}
        name = str(tags.get("name:vi") or tags.get("name") or "").strip()
        source_identifier = f"{raw.get('type', 'nwr')}:{raw.get('id', '')}"
        latitude = self._parse_coordinate(raw.get("lat") or (raw.get("center") or {}).get("lat"), province.latitude)
        longitude = self._parse_coordinate(raw.get("lon") or (raw.get("center") or {}).get("lon"), province.longitude)
        opening_hours = tags.get("opening_hours") or tags.get("service_times") or ""
        record = self._base_record(
            source="osm",
            province=province,
            source_identifier=source_identifier,
            name=name,
            address=self._build_osm_address(tags, province),
            description=self._build_osm_description(tags),
            category=self._map_osm_category(tags),
            latitude=latitude,
            longitude=longitude,
            ticket_price=self._parse_price(tags.get("fee") or tags.get("charge")),
            opening_hours=self._parse_opening_hours(opening_hours, ""),
            phone=str(tags.get("phone") or tags.get("contact:phone") or "").strip(),
            website=str(tags.get("website") or tags.get("contact:website") or "").strip(),
            source_metadata={
                "osm_id": raw.get("id"),
                "osm_type": raw.get("type"),
                "tags": tags,
            },
        )
        return record

    def build_existing_key(self, place: DiaDiem) -> Optional[str]:
        source_meta = self._safe_json_dict(place.dacDiem)
        harvest_key = source_meta.get("harvest_key")
        if harvest_key:
            return str(harvest_key)
        province = self.province_lookup.get(str(place.maTinhThanh_id))
        if province is None:
            return None
        return self._compose_harvest_key(
            source=str(source_meta.get("source") or "legacy"),
            province=province,
            source_identifier=str(source_meta.get("item_id") or source_meta.get("detail_url") or place.tenDiaDiem),
            name=place.tenDiaDiem,
            address=place.diaChi,
            latitude=place.viDo,
            longitude=place.kinhDo,
        )

    def _base_record(
        self,
        *,
        source: str,
        province: ProvinceRuntime,
        source_identifier: str,
        name: str,
        address: str,
        description: str,
        category: str,
        latitude: Optional[float],
        longitude: Optional[float],
        ticket_price: float,
        opening_hours: Tuple[str, str],
        phone: str,
        website: str,
        source_metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        opening_from, opening_to = opening_hours
        lat = latitude if latitude is not None else province.latitude
        lon = longitude if longitude is not None else province.longitude
        harvest_key = self._compose_harvest_key(
            source=source,
            province=province,
            source_identifier=source_identifier,
            name=name,
            address=address,
            latitude=lat,
            longitude=lon,
        )
        normalized_meta = dict(source_metadata)
        normalized_meta.update(
            {
                "source": source,
                "harvest_key": harvest_key,
                "province_name": province.province_name,
            }
        )
        return {
            "harvest_key": harvest_key,
            "tenDiaDiem": name or "Địa điểm chưa rõ tên",
            "moTa": description,
            "diaChi": address,
            "maTinhThanh_id": province.province_id,
            "loaiDiaDiem": category,
            "viDo": lat,
            "kinhDo": lon,
            "giaVe": ticket_price,
            "gioMoCua": opening_from,
            "gioDongCua": opening_to,
            "dienThoai": phone,
            "website": website,
            "danhGiaTrungBinh": 0.0,
            "soLuotDanhGia": 0,
            "soLuotXem": 0,
            "maNguoiTao_id": None,
            "trangThai": DEFAULT_TRANG_THAI,
            "dacDiem": json.dumps(normalized_meta, ensure_ascii=False, sort_keys=True),
            "tienNghi": "[]",
        }

    def _compose_harvest_key(
        self,
        *,
        source: str,
        province: ProvinceRuntime,
        source_identifier: str,
        name: str,
        address: str,
        latitude: Optional[float],
        longitude: Optional[float],
    ) -> str:
        normalized_name = self._slugify(name)
        normalized_address = self._slugify(address)
        coordinate_signature = f"{self._format_coord(latitude)}:{self._format_coord(longitude)}"
        raw_key = "|".join(
            [
                source,
                province.normalized_name,
                self._slugify(source_identifier),
                normalized_name,
                normalized_address,
                coordinate_signature,
            ]
        )
        return str(uuid.uuid5(uuid.NAMESPACE_URL, raw_key))

    @staticmethod
    def _format_coord(value: Optional[float]) -> str:
        if value is None:
            return "na"
        return f"{value:.6f}"

    @staticmethod
    def _slugify(value: str) -> str:
        normalized = unicodedata.normalize("NFD", (value or "").strip().lower())
        normalized = normalized.replace("đ", "d")
        normalized = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
        normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
        return normalized.strip("-")

    def _build_alias_lookup(self, province_lookup: Dict[str, ProvinceRuntime]) -> Dict[str, ProvinceRuntime]:
        alias_lookup: Dict[str, ProvinceRuntime] = {}
        for province in province_lookup.values():
            normalized = province.normalized_name
            alias_lookup[normalized] = province
            alias_lookup[normalized.replace("tinh-", "")] = province
            alias_lookup[normalized.replace("thanh-pho-", "")] = province
            compact = normalized.replace("-", " ")
            for alias in VIETNAM_PROVINCE_ALIASES.get(compact, ()):
                alias_lookup[self._slugify(alias)] = province
        return alias_lookup

    def _match_province(self, address: Optional[str], default: ProvinceRuntime) -> ProvinceRuntime:
        normalized_address = self._slugify(address or "")
        if not normalized_address:
            return default
        for alias, province in self.alias_lookup.items():
            if alias and alias in normalized_address:
                return province
        return default

    def _map_tourism_category(self, category_slug: str) -> str:
        config = tourism_scraper.CATEGORY_CONFIG.get(category_slug, {})
        value = config.get("loai") or "khac"
        return value if value in dict(DiaDiem.LOAI_DIA_DIEM_CHOICES) else "khac"

    def _map_osm_category(self, tags: Dict[str, Any]) -> str:
        for key, expected, mapped in OSM_CATEGORY_MAP:
            raw_value = tags.get(key)
            if raw_value is None:
                continue
            if expected == "*" or str(raw_value) == expected:
                return mapped
        return "khac"

    def _parse_coordinate(self, raw_value: Any, fallback: Optional[float]) -> Optional[float]:
        if raw_value in (None, ""):
            return fallback
        try:
            return float(str(raw_value).replace(",", "."))
        except (TypeError, ValueError):
            return fallback

    def _parse_price(self, raw_value: Any) -> float:
        if raw_value in (None, "", False):
            return 0.0
        if isinstance(raw_value, (int, float)):
            return float(max(0, raw_value))
        lowered = str(raw_value).strip().lower()
        if lowered in {"free", "miễn phí", "mien phi", "0", "không", "khong"}:
            return 0.0
        digits = re.sub(r"[^\d]", "", lowered)
        if not digits:
            return 0.0
        try:
            return float(int(digits))
        except ValueError:
            return 0.0

    def _parse_opening_hours(self, raw_open: Any, raw_close: Any) -> Tuple[str, str]:
        open_value = self._parse_time_string(raw_open)
        close_value = self._parse_time_string(raw_close)
        if raw_open and not raw_close and isinstance(raw_open, str) and "-" in raw_open:
            parts = re.split(r"\s*-\s*", raw_open, maxsplit=1)
            open_value = self._parse_time_string(parts[0])
            close_value = self._parse_time_string(parts[1])
        if not open_value:
            open_value = DEFAULT_GIO_MO_CUA
        if not close_value:
            close_value = DEFAULT_GIO_DONG_CUA
        return open_value, close_value

    @staticmethod
    def _parse_time_string(raw_value: Any) -> str:
        if raw_value in (None, ""):
            return ""
        text = str(raw_value).strip()
        match = re.search(r"(\d{1,2})[:hH]?(\d{2})?", text)
        if not match:
            return ""
        hours = int(match.group(1))
        minutes = int(match.group(2) or 0)
        hours = max(0, min(hours, 23))
        minutes = max(0, min(minutes, 59))
        return f"{hours:02d}:{minutes:02d}:00"

    @staticmethod
    def _build_osm_address(tags: Dict[str, Any], province: ProvinceRuntime) -> str:
        fragments = [
            str(tags.get("addr:housenumber") or "").strip(),
            str(tags.get("addr:street") or "").strip(),
            str(tags.get("addr:suburb") or "").strip(),
            str(tags.get("addr:city") or "").strip(),
            province.province_name,
        ]
        return ", ".join(fragment for fragment in fragments if fragment)

    @staticmethod
    def _build_osm_description(tags: Dict[str, Any]) -> str:
        description_fields = [
            "description",
            "description:vi",
            "short_description",
            "wikidata",
            "wikipedia",
        ]
        chunks: List[str] = []
        for field_name in description_fields:
            value = str(tags.get(field_name) or "").strip()
            if value:
                chunks.append(value)
        return " | ".join(chunks)[:2000]

    @staticmethod
    def _extract_item_id(detail_url: str) -> str:
        match = re.search(r"item=(\d+)", detail_url or "")
        return match.group(1) if match else ""

    @staticmethod
    def _safe_json_dict(raw_value: str) -> Dict[str, Any]:
        if not raw_value:
            return {}
        try:
            parsed = json.loads(raw_value)
            return parsed if isinstance(parsed, dict) else {}
        except json.JSONDecodeError:
            return {}


class HarvestOrchestrator:
    def __init__(self, *, source: str, batch_size: int = DEFAULT_BATCH_SIZE, request_timeout: int = DEFAULT_TIMEOUT) -> None:
        self.source = source
        self.batch_size = max(100, batch_size)
        self.request_timeout = request_timeout
        self.checkpoint_store = CheckpointStore(STATE_PATH)
        self.province_lookup = self._load_province_lookup()
        self.normalizer = PlaceNormalizer(self.province_lookup)

    def run(
        self,
        *,
        limit: Optional[int] = None,
        max_pages_per_category: Optional[int] = None,
        categories: Optional[Sequence[str]] = None,
        skip_vector_sync: bool = False,
    ) -> Dict[str, Any]:
        state = self.checkpoint_store.load()
        state.update(
            {
                "status": "running",
                "source": self.source,
                "last_checkpoint_reason": "Khởi tạo pipeline",
            }
        )
        self.checkpoint_store.save(state)

        totals = BatchStats(
            created=int(state.get("imported_records_count", 0)),
            updated=int(state.get("updated_records_count", 0)),
            skipped=int(state.get("skipped_records_count", 0)),
            processed=0,
        )

        if self.source == "osm":
            self._run_osm_pipeline(state, totals, limit=limit, skip_vector_sync=skip_vector_sync)
        elif self.source == "tourism":
            self._run_tourism_pipeline(
                state,
                totals,
                categories=list(categories or tourism_scraper.CATEGORY_CONFIG.keys()),
                max_pages_per_category=max_pages_per_category,
                limit=limit,
                skip_vector_sync=skip_vector_sync,
            )
        else:
            raise ValueError(f"Nguồn không được hỗ trợ: {self.source}")

        state["imported_records_count"] = totals.created
        state["updated_records_count"] = totals.updated
        state["skipped_records_count"] = totals.skipped
        self.checkpoint_store.mark_completed(state)
        return {
            "source": self.source,
            "created": totals.created,
            "updated": totals.updated,
            "skipped": totals.skipped,
        }

    def _run_osm_pipeline(
        self,
        state: Dict[str, Any],
        totals: BatchStats,
        *,
        limit: Optional[int],
        skip_vector_sync: bool,
    ) -> None:
        session = requests.Session()
        session.headers.update({"User-Agent": "ViVuHarvestOrchestrator/1.0"})
        completed = set(state.get("completed_provinces", []))
        global_limit = limit if limit and limit > 0 else None
        remaining = global_limit

        for province in self._iter_provinces(state):
            if province.province_name in completed:
                continue
            if remaining is not None and remaining <= 0:
                break
            state["current_province"] = province.province_name
            state["last_checkpoint_reason"] = "Đang lấy dữ liệu OSM"
            self.checkpoint_store.save(state)

            raw_records = self._fetch_osm_records_for_province(session, province)
            if remaining is not None:
                raw_records = raw_records[:remaining]
            normalized_records = [
                self.normalizer.normalize_osm_record(raw_record, province)
                for raw_record in raw_records
                if (raw_record.get("tags") or {}).get("name:vi") or (raw_record.get("tags") or {}).get("name")
            ]

            province_stats = self._upsert_records_for_province(
                province,
                normalized_records,
                state=state,
                totals=totals,
                skip_vector_sync=skip_vector_sync,
            )
            remaining = None if remaining is None else max(0, remaining - province_stats.processed)
            completed.add(province.province_name)
            state["completed_provinces"] = sorted(completed)
            state["last_successful_page"] = 1
            state["last_checkpoint_reason"] = "Hoàn tất tỉnh"
            self.checkpoint_store.save(state)

    def _run_tourism_pipeline(
        self,
        state: Dict[str, Any],
        totals: BatchStats,
        *,
        categories: Sequence[str],
        max_pages_per_category: Optional[int],
        limit: Optional[int],
        skip_vector_sync: bool,
    ) -> None:
        session = tourism_scraper.get_session()
        request_policy = tourism_scraper.RequestPolicy()
        crawl_state = tourism_scraper.CrawlState()
        completed = set(state.get("completed_provinces", []))
        category_list = list(categories)
        global_limit = limit if limit and limit > 0 else None
        processed_total = 0

        for category_slug in category_list:
            config = tourism_scraper.CATEGORY_CONFIG[category_slug]
            page = int(state.get("last_successful_page", 0)) + 1 if state.get("source") == "tourism" else 1
            while True:
                if max_pages_per_category is not None and page > max_pages_per_category:
                    break
                if global_limit is not None and processed_total >= global_limit:
                    break

                url = f"{tourism_scraper.BASE_URL}{config['path']}" if page == 1 else f"{tourism_scraper.BASE_URL}{config['path']}?page={page}"
                state["current_province"] = config["label"]
                state["last_checkpoint_reason"] = f"Đang lấy page {page}"
                self.checkpoint_store.save(state)

                response = tourism_scraper.fetch_url(
                    session,
                    url,
                    request_policy,
                    crawl_state,
                    label=f"{category_slug} page {page}",
                )
                soup = BeautifulSoup(response.text, "html.parser")
                item_nodes = tourism_scraper.parse_list_items(soup)
                if not item_nodes:
                    break

                page_items: List[Dict[str, Any]] = []
                for item_node in item_nodes:
                    item = tourism_scraper.parse_place_item(item_node, category_slug)
                    if not item:
                        continue
                    if item.get("detail_url"):
                        try:
                            detail = tourism_scraper.scrape_detail_page(
                                session,
                                item["detail_url"],
                                0.0,
                                request_policy,
                                crawl_state,
                            )
                            for key, value in detail.items():
                                if key == "images":
                                    if value:
                                        item["images"] = list(dict.fromkeys((item.get("images") or []) + value))[:5]
                                elif value and not item.get(key):
                                    item[key] = value
                        except Exception:
                            pass
                    page_items.append(item)
                    if global_limit is not None and processed_total + len(page_items) >= global_limit:
                        break

                if not page_items:
                    break

                grouped: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
                for item in page_items:
                    province = self._match_tourism_item_province(item)
                    if province is None:
                        totals.skipped += 1
                        continue
                    normalized = self.normalizer.normalize_tourism_record(item, province)
                    grouped[province.province_id].append(normalized)

                for province_id, records in grouped.items():
                    province = self.province_lookup[str(province_id)]
                    province_stats = self._upsert_records_for_province(
                        province,
                        records,
                        state=state,
                        totals=totals,
                        skip_vector_sync=skip_vector_sync,
                    )
                    completed.add(province.province_name)
                    state["completed_provinces"] = sorted(completed)
                    processed_total += province_stats.processed

                state["last_successful_page"] = page
                state["last_checkpoint_reason"] = f"Hoàn tất page {page}"
                self.checkpoint_store.save(state)
                page += 1

            state["last_successful_page"] = 0
            self.checkpoint_store.save(state)

    def _upsert_records_for_province(
        self,
        province: ProvinceRuntime,
        records: Sequence[Dict[str, Any]],
        *,
        state: Dict[str, Any],
        totals: BatchStats,
        skip_vector_sync: bool,
    ) -> BatchStats:
        existing_places = DiaDiem.objects.filter(maTinhThanh_id=province.province_id).only(
            "maDiaDiem",
            "tenDiaDiem",
            "diaChi",
            "viDo",
            "kinhDo",
            "maTinhThanh",
            "dacDiem",
        )
        existing_by_key: Dict[str, DiaDiem] = {}
        for place in existing_places:
            harvest_key = self.normalizer.build_existing_key(place)
            if harvest_key:
                existing_by_key[harvest_key] = place

        stats = BatchStats()
        for offset in range(0, len(records), self.batch_size):
            batch = list(records[offset:offset + self.batch_size])
            if not batch:
                continue

            model_instances: List[DiaDiem] = []
            created_in_batch = 0
            updated_in_batch = 0
            batch_started = time.perf_counter()
            for payload in batch:
                harvest_key = payload["harvest_key"]
                existing = existing_by_key.get(harvest_key)
                batch_now = timezone.now()
                instance_kwargs = {
                    "tenDiaDiem": payload["tenDiaDiem"],
                    "moTa": payload["moTa"],
                    "diaChi": payload["diaChi"],
                    "maTinhThanh_id": payload["maTinhThanh_id"],
                    "loaiDiaDiem": payload["loaiDiaDiem"],
                    "viDo": payload["viDo"],
                    "kinhDo": payload["kinhDo"],
                    "giaVe": payload["giaVe"],
                    "gioMoCua": payload["gioMoCua"],
                    "gioDongCua": payload["gioDongCua"],
                    "dienThoai": payload["dienThoai"],
                    "website": payload["website"],
                    "danhGiaTrungBinh": payload["danhGiaTrungBinh"],
                    "soLuotDanhGia": payload["soLuotDanhGia"],
                    "soLuotXem": payload["soLuotXem"],
                    "maNguoiTao_id": payload["maNguoiTao_id"],
                    "ngayTao": batch_now,
                    "lanCapNhatCuoi": batch_now,
                    "trangThai": payload["trangThai"],
                    "dacDiem": payload["dacDiem"],
                    "tienNghi": payload["tienNghi"],
                }
                if existing is not None:
                    instance_kwargs["maDiaDiem"] = existing.maDiaDiem
                    updated_in_batch += 1
                else:
                    created_in_batch += 1
                model_instances.append(DiaDiem(**instance_kwargs))

            with transaction.atomic():
                DiaDiem.objects.bulk_create(
                    model_instances,
                    batch_size=self.batch_size,
                    update_conflicts=True,
                    unique_fields=["maDiaDiem"],
                    update_fields=[
                        "tenDiaDiem",
                        "moTa",
                        "diaChi",
                        "maTinhThanh",
                        "loaiDiaDiem",
                        "viDo",
                        "kinhDo",
                        "giaVe",
                        "gioMoCua",
                        "gioDongCua",
                        "dienThoai",
                        "website",
                        "trangThai",
                        "dacDiem",
                        "tienNghi",
                        "lanCapNhatCuoi",
                    ],
                )

            duration_ms = int((time.perf_counter() - batch_started) * 1000)
            stats.created += created_in_batch
            stats.updated += updated_in_batch
            stats.processed += len(batch)
            totals.created += created_in_batch
            totals.updated += updated_in_batch
            totals.processed += len(batch)
            state["imported_records_count"] = totals.created
            state["updated_records_count"] = totals.updated
            state["skipped_records_count"] = totals.skipped
            state["current_province"] = province.province_name
            state["last_checkpoint_reason"] = f"Đã ghi batch {offset // self.batch_size + 1}"
            self.checkpoint_store.save(state)
            print(
                f"[BATCH - {province.province_name.upper()}] "
                f"Đang nạp {len(batch)} POIs... Hoàn tất bulk_create trong {duration_ms}ms. "
                f"[Tổng: {totals.created + totals.updated:,} records]"
            )

        if stats.processed and not skip_vector_sync:
            self._sync_vector_store(province)
        return stats

    def _sync_vector_store(self, province: ProvinceRuntime) -> None:
        try:
            from scripts.sync_to_vector_db import sync_missing_places

            result = sync_missing_places(batch_size=VECTOR_SYNC_BATCH_SIZE)
            upserted = int(result.get("upserted", 0))
            print(f"[VECTOR - {province.province_name.upper()}] Đồng bộ Chroma hoàn tất. [Upserted: {upserted:,}]")
        except Exception as exc:
            print(f"[VECTOR - {province.province_name.upper()}] Đồng bộ Chroma thất bại: {exc}")

    def _fetch_osm_records_for_province(self, session: requests.Session, province: ProvinceRuntime) -> List[Dict[str, Any]]:
        province_query_name = re.sub(r"^(Tỉnh|Thành phố)\s+", "", province.province_name, flags=re.IGNORECASE).strip()
        query = OSM_QUERY_TEMPLATE.format(timeout=self.request_timeout, province_name=province_query_name or province.province_name)
        last_error: Optional[Exception] = None
        for endpoint in OVERPASS_ENDPOINTS:
            for attempt in range(1, 4):
                try:
                    response = session.post(
                        endpoint,
                        data={"data": query},
                        timeout=self.request_timeout,
                    )
                    response.raise_for_status()
                    payload = response.json()
                    return list(payload.get("elements") or [])
                except requests.RequestException as exc:
                    last_error = exc
                    wait_seconds = attempt * 2
                    print(
                        f"[OSM - {province.province_name.upper()}] "
                        f"Lỗi endpoint {endpoint} (lần {attempt}/3): {exc}. "
                        f"Thử lại sau {wait_seconds}s."
                    )
                    time.sleep(wait_seconds)
                    continue
        if last_error is not None:
            raise last_error
        return []

    def _load_province_lookup(self) -> Dict[str, ProvinceRuntime]:
        provinces = TinhThanh.objects.all().only("maTinhThanh", "tenTinhThanh", "viDo", "kinhDo")
        lookup: Dict[str, ProvinceRuntime] = {}
        for province in provinces:
            lookup[str(province.maTinhThanh)] = ProvinceRuntime(
                province_id=int(province.maTinhThanh),
                province_name=province.tenTinhThanh,
                normalized_name=self._slugify_province(province.tenTinhThanh),
                latitude=province.viDo,
                longitude=province.kinhDo,
            )
        return lookup

    def _iter_provinces(self, state: Dict[str, Any]) -> Iterable[ProvinceRuntime]:
        current = state.get("current_province")
        provinces = sorted(self.province_lookup.values(), key=lambda item: item.province_name)
        if not current:
            return provinces
        start_index = 0
        for idx, province in enumerate(provinces):
            if province.province_name == current:
                start_index = idx
                break
        return provinces[start_index:]

    def _match_tourism_item_province(self, item: Dict[str, Any]) -> Optional[ProvinceRuntime]:
        address = str(item.get("diaChi") or "")
        normalized_address = self._slugify_province(address)
        if not normalized_address:
            return None
        for province in self.province_lookup.values():
            normalized_name = province.normalized_name
            aliases = [normalized_name, normalized_name.replace("tinh-", ""), normalized_name.replace("thanh-pho-", "")]
            alias_group = VIETNAM_PROVINCE_ALIASES.get(normalized_name.replace("-", " "), ())
            aliases.extend(self._slugify_province(alias) for alias in alias_group)
            if any(alias and alias in normalized_address for alias in aliases):
                return province
        return None

    @staticmethod
    def _slugify_province(value: str) -> str:
        normalized = unicodedata.normalize("NFD", (value or "").strip().lower())
        normalized = normalized.replace("đ", "d")
        normalized = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
        normalized = re.sub(r"\b(tinh|thanh pho|tp\.?)\b", " ", normalized)
        normalized = re.sub(r"[^a-z0-9]+", "-", normalized)
        return normalized.strip("-")
