"""
POI Harvester for Vietnam (50k+ places) -> SQLite

Sources:
- Overpass (OpenStreetMap) for discovery (tourism/amenity/natural/historic)
- Nominatim (reverse) for admin divisions in Vietnamese
- Wikipedia (vi) for short description when available

Run:
  python -m scripts.poi_harvest --limit 60000 --db "D:/KLTN/MAS (1)/MAS/TRAVEL_PLANNER/vivu_backend/db.sqlite3"

Notes:
- This script respects public rate-limits. Keep concurrency low.
- Wikipedia/Nominatim requests include a custom User-Agent.
"""
from __future__ import annotations

import asyncio
import aiohttp
import aiosignal  # noqa: F401  # ensure aiohttp deps available
import json
import math
import re
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# =============================
# Configuration
# =============================
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
NOMINATIM_REVERSE_URL = "https://nominatim.openstreetmap.org/reverse"
WIKI_SEARCH_URL = "https://vi.wikipedia.org/w/api.php"

USER_AGENT = (
    "ViVuCrawler/1.0 (+contact@example.com; https://vivu.example)"
)

# Categories to target (expand as needed)
OSM_FILTER = (
    "[out:json][timeout:60];"
    "area[\"ISO3166-1\"=\"VN\"][admin_level=2]->.vn;"
    "(\n"
    " node[\"tourism\"~\"attraction|museum|viewpoint|artwork\"](area.vn);\n"
    " way[\"tourism\"~\"attraction|museum|viewpoint|artwork\"](area.vn);\n"
    " relation[\"tourism\"~\"attraction|museum|viewpoint|artwork\"](area.vn);\n"
    " node[\"amenity\"~\"cafe|restaurant|fast_food|bar|pub\"](area.vn);\n"
    " node[\"historic\"](area.vn);\n"
    " node[\"natural\"~\"peak|bay|beach|cave|spring|waterfall\"](area.vn);\n"
    ") ;\n"
    "out center tags;"
)


PROVINCES = [
    "Thành phố Hà Nội",
    "Thành phố Hồ Chí Minh",
    "Tỉnh Bắc Giang", "Tỉnh Bắc Kạn", "Tỉnh Bắc Ninh", "Tỉnh Bạc Liêu",
    "Tỉnh Bà Rịa - Vũng Tàu", "Tỉnh Bến Tre", "Tỉnh Bình Dương", "Tỉnh Bình Định",
    "Tỉnh Bình Phước", "Tỉnh Bình Thuận", "Tỉnh Cà Mau", "Tỉnh Cao Bằng",
    "Thành phố Cần Thơ", "Tỉnh Đà Nẵng", "Tỉnh Đắk Lắk", "Tỉnh Đắk Nông",
    "Tỉnh Điện Biên", "Tỉnh Đồng Nai", "Tỉnh Đồng Tháp", "Tỉnh Gia Lai",
    "Tỉnh Hà Giang", "Tỉnh Hà Nam", "Tỉnh Hà Tĩnh", "Tỉnh Hải Dương",
    "Thành phố Hải Phòng", "Tỉnh Hậu Giang", "Tỉnh Hòa Bình", "Tỉnh Hưng Yên",
    "Tỉnh Khánh Hòa", "Tỉnh Kiên Giang", "Tỉnh Kon Tum", "Tỉnh Lai Châu",
    "Tỉnh Lâm Đồng", "Tỉnh Lạng Sơn", "Tỉnh Lào Cai", "Tỉnh Long An",
    "Tỉnh Nam Định", "Tỉnh Nghệ An", "Tỉnh Ninh Bình", "Tỉnh Ninh Thuận",
    "Tỉnh Phú Thọ", "Tỉnh Phú Yên", "Tỉnh Quảng Bình", "Tỉnh Quảng Nam",
    "Tỉnh Quảng Ngãi", "Tỉnh Quảng Ninh", "Tỉnh Quảng Trị", "Tỉnh Sóc Trăng",
    "Tỉnh Sơn La", "Tỉnh Tây Ninh", "Tỉnh Thái Bình", "Tỉnh Thái Nguyên",
    "Tỉnh Thanh Hóa", "Tỉnh Thừa Thiên Huế", "Tỉnh Tiền Giang", "Tỉnh Trà Vinh",
    "Tỉnh Tuyên Quang", "Tỉnh Vĩnh Long", "Tỉnh Vĩnh Phúc", "Tỉnh Yên Bái",
    "Tỉnh An Giang", "Tỉnh Bà Rịa - Vũng Tàu"
]


# =============================
# SQLite
# =============================
SCHEMA = """
CREATE TABLE IF NOT EXISTS places (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name_vi TEXT NOT NULL,
    name_ascii TEXT,
    description_vi TEXT,
    category TEXT,
    source TEXT NOT NULL,
    source_ids TEXT,
    lat REAL NOT NULL,
    lon REAL NOT NULL,
    province TEXT,
    district TEXT,
    ward TEXT,
    website TEXT,
    image_url TEXT,
    confidence REAL DEFAULT 0.5,
    last_verified_at TEXT DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(name_vi, lat, lon)
);
"""


def get_db(path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(path))
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute(SCHEMA)
    return conn


def normalize_name(name: str) -> str:
    return re.sub(r"\s+", " ", name or "").strip()


def name_ascii(name: str) -> str:
    import unicodedata
    return unicodedata.normalize("NFD", name).encode("ascii", "ignore").decode("ascii")


# =============================
# Fetchers
# =============================
async def fetch_overpass(session: aiohttp.ClientSession) -> List[Dict[str, Any]]:
    """Fetch POIs nationwide using a broad filter.
    We purposely do one broad query; for robustness you can chunk by bbox later.
    """
    payload = {"data": OSM_FILTER}
    async with session.post(OVERPASS_URL, data=payload, headers={"User-Agent": USER_AGENT}) as r:
        r.raise_for_status()
        data = await r.json()
    return data.get("elements", [])


async def reverse_admin(session: aiohttp.ClientSession, lat: float, lon: float) -> Tuple[str, str, str]:
    params = {
        "lat": lat,
        "lon": lon,
        "format": "jsonv2",
        "accept-language": "vi",
        "zoom": 18,
    }
    async with session.get(NOMINATIM_REVERSE_URL, params=params, headers={"User-Agent": USER_AGENT}) as r:
        if r.status != 200:
            return "", "", ""
        data = await r.json()
    address = data.get("address", {})
    return (
        address.get("state", ""),
        address.get("county", ""),
        address.get("suburb", "") or address.get("city_district", "") or address.get("town", "")
    )


async def wiki_description(session: aiohttp.ClientSession, name: str) -> str:
    params = {
        "action": "query",
        "prop": "extracts",
        "exintro": 1,
        "explaintext": 1,
        "titles": name,
        "format": "json",
        "redirects": 1,
    }
    async with session.get(WIKI_SEARCH_URL, params=params, headers={"User-Agent": USER_AGENT}) as r:
        if r.status != 200:
            return ""
        data = await r.json()
    pages = data.get("query", {}).get("pages", {})
    if not pages:
        return ""
    page = next(iter(pages.values()))
    if page.get("missing"):
        return ""
    text = page.get("extract") or ""
    # Shorten to ~400 chars
    return (text[:400] + "…") if len(text) > 400 else text


# =============================
# Pipeline
# =============================
@dataclass
class POI:
    name_vi: str
    lat: float
    lon: float
    category: str
    source: str
    source_ids: str
    province: str = ""
    district: str = ""
    ward: str = ""
    description_vi: str = ""
    website: str = ""
    image_url: str = ""
    confidence: float = 0.6


async def enrich_one(session: aiohttp.ClientSession, poi: POI) -> POI:
    # Reverse geocode for admin divisions
    try:
        province, district, ward = await reverse_admin(session, poi.lat, poi.lon)
        poi.province, poi.district, poi.ward = province, district, ward
    except Exception:
        pass

    # Wikipedia description (best effort)
    try:
        desc = await wiki_description(session, poi.name_vi)
        poi.description_vi = desc
        if desc:
            poi.confidence = min(1.0, poi.confidence + 0.2)
    except Exception:
        pass

    return poi


def save_batch(conn: sqlite3.Connection, batch: List[POI]) -> None:
    rows = [
        (
            p.name_vi,
            name_ascii(p.name_vi),
            p.description_vi,
            p.category,
            p.source,
            p.source_ids,
            float(p.lat),
            float(p.lon),
            p.province,
            p.district,
            p.ward,
            p.website,
            p.image_url,
            p.confidence,
        )
        for p in batch
    ]
    conn.executemany(
        """
        INSERT OR IGNORE INTO places (
            name_vi, name_ascii, description_vi, category, source, source_ids,
            lat, lon, province, district, ward, website, image_url, confidence
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """,
        rows,
    )
    conn.commit()


async def main(limit: int, db_path: str) -> None:
    db = get_db(Path(db_path))
    timeout = aiohttp.ClientTimeout(total=120)
    async with aiohttp.ClientSession(timeout=timeout, headers={"User-Agent": USER_AGENT}) as session:
        print("Fetching POIs from Overpass…")
        elements = await fetch_overpass(session)
        print(f"Overpass returned {len(elements)} elements")

        pois: List[POI] = []
        for el in elements:
            tags = el.get("tags", {})
            name = normalize_name(tags.get("name:vi") or tags.get("name") or "")
            if not name:
                continue
            lat = el.get("lat") or (el.get("center") or {}).get("lat")
            lon = el.get("lon") or (el.get("center") or {}).get("lon")
            if lat is None or lon is None:
                continue
            category = (
                tags.get("tourism") or tags.get("amenity") or tags.get("natural") or tags.get("historic") or "poi"
            )
            source_ids = json.dumps({"osm_id": el.get("id"), "type": el.get("type")})
            poi = POI(name_vi=name, lat=float(lat), lon=float(lon), category=category, source="osm", source_ids=source_ids)
            pois.append(poi)

        if limit:
            pois = pois[:limit]

        print(f"Enriching {len(pois)} POIs (reverse geocode + wikipedia)…")
        out: List[POI] = []
        # Concurrency control (respect public services)
        sem = asyncio.Semaphore(5)

        async def _wrap(p: POI) -> Optional[POI]:
            async with sem:
                try:
                    return await enrich_one(session, p)
                finally:
                    await asyncio.sleep(0.2)  # gentle pacing

        tasks = [asyncio.create_task(_wrap(p)) for p in pois]
        for chunk_start in range(0, len(tasks), 100):
            chunk = tasks[chunk_start:chunk_start+100]
            results = await asyncio.gather(*chunk, return_exceptions=True)
            good = [r for r in results if isinstance(r, POI)]
            save_batch(db, good)
            out.extend(good)
            print(f"Saved {len(out)}/{len(pois)}…")

        print("Done. Rows in SQLite may be < input due to dedup/IGNORE.")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Harvest Vietnam POIs into SQLite")
    parser.add_argument("--limit", type=int, default=50000, help="Max POIs to process")
    parser.add_argument("--db", type=str, required=True, help="Path to SQLite database")
    args = parser.parse_args()

    asyncio.run(main(args.limit, args.db))


