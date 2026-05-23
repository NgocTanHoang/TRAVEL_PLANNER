#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Crawler/importer cho CSDL Du lịch Việt Nam.

Nguồn:
    https://csdl.vietnamtourism.gov.vn/

Mục tiêu:
    - Thu thập dữ liệu theo các danh mục public trên site
    - Chuẩn hóa dữ liệu theo schema TINHTHANH / DIADIEM / HINHANHDIADIEM
    - Upsert idempotent vào SQLite/Django DB của project
    - Lưu metadata nguồn trong trường `dacDiem`

Ví dụ:
    python vivu_backend/scripts/scrape_vietnam_tourism_db.py --max-pages-per-category 2
    python vivu_backend/scripts/scrape_vietnam_tourism_db.py --categories cslt,dest,rest --max-items-per-category 100
    python vivu_backend/scripts/scrape_vietnam_tourism_db.py --dry-run --no-detail
"""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import sqlite3
import sys
import time
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple
from urllib.parse import parse_qs, urljoin, urlparse

import requests
from bs4 import BeautifulSoup, Tag


if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent
BASE_URL = "https://csdl.vietnamtourism.gov.vn"
DEFAULT_OUTPUT = REPO_ROOT / "data" / "vietnam_tourism_db_scraped.json"
DB_PATH = BACKEND_DIR / "vivudb.sqlite3"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

CATEGORY_CONFIG: Dict[str, Dict[str, str]] = {
    "cslt": {"label": "Cơ sở lưu trú", "path": "/cslt", "loai": "khach_san"},
    "rest": {"label": "Nhà hàng", "path": "/rest", "loai": "nha_hang"},
    "dest": {"label": "Điểm đến", "path": "/dest", "loai": "dia_danh"},
    "shop": {"label": "Điểm mua sắm", "path": "/shop", "loai": "mua_sam"},
    "vcgt": {"label": "Vui chơi giải trí", "path": "/vcgt", "loai": "giai_tri"},
    "thethao": {"label": "Thể thao", "path": "/thethao", "loai": "giai_tri"},
    "vantai": {"label": "Vận tải khách du lịch", "path": "/vantai", "loai": "khac"},
    "cssk": {"label": "Chăm sóc sức khỏe", "path": "/cssk", "loai": "khac"},
    "hiephoi": {"label": "Hiệp hội", "path": "/hiephoi", "loai": "khac"},
    "daotao": {"label": "Cơ sở đào tạo", "path": "/daotao", "loai": "khac"},
    "nhanluc": {"label": "Nhân lực du lịch", "path": "/nhanluc", "loai": "khac"},
    "xuctien": {"label": "Xúc tiến du lịch", "path": "/xuctien", "loai": "khac"},
}

LIST_CONTAINER_CLASSES = [
    "cslt-items",
    "rest-items",
    "dest-items",
    "shop-items",
    "vcgt-items",
]


@dataclass
class ProvinceIndex:
    province_id: int
    province_name: str
    normalized_name: str
    plain_name: str


@dataclass
class ProvinceMatcher:
    province_dict: Dict[str, ProvinceIndex]
    match_keys: List[str]


def normalize_text(value: str) -> str:
    value = (value or "").strip()
    value = value.replace("\xa0", " ")
    value = re.sub(r"\s+", " ", value)
    return value


def slugify_vn(value: str) -> str:
    value = normalize_text(value).lower()
    value = value.replace("đ", "d")
    value = unicodedata.normalize("NFD", value)
    value = "".join(ch for ch in value if unicodedata.category(ch) != "Mn")
    value = re.sub(r"\b(thanh pho|tp\.?|tinh|thi xa|thi tran)\b", " ", value)
    value = re.sub(r"[^a-z0-9]+", " ", value)
    value = re.sub(r"\s+", " ", value).strip()

    alias_map = {
        "dac nong": "dak nong",
        "dac lak": "dak lak",
        "hoa binh": "hoa binh",
        "thua thien hue": "thua thien hue",
        "ba ria vung tau": "ba ria vung tau",
    }
    return alias_map.get(value, value)


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(str(DB_PATH))
    connection.row_factory = sqlite3.Row
    return connection


def build_province_index(connection: sqlite3.Connection) -> List[ProvinceIndex]:
    rows = connection.execute(
        "SELECT maTinhThanh, tenTinhThanh FROM TINHTHANH ORDER BY tenTinhThanh"
    ).fetchall()
    return [
        ProvinceIndex(
            province_id=int(row["maTinhThanh"]),
            province_name=row["tenTinhThanh"],
            normalized_name=slugify_vn(row["tenTinhThanh"]),
            plain_name=normalize_text(row["tenTinhThanh"]),
        )
        for row in rows
    ]


def build_province_matcher(connection: sqlite3.Connection) -> ProvinceMatcher:
    province_index = build_province_index(connection)

    alias_groups = {
        "ho chi minh": [
            "ho chi minh",
            "tp ho chi minh",
            "tp hcm",
            "tphcm",
            "hcm",
            "sai gon",
            "tp. hcm",
            "tp.hcm",
            "thanh pho ho chi minh",
        ],
        "ha noi": [
            "ha noi",
            "tp ha noi",
            "thanh pho ha noi",
        ],
        "hai phong": [
            "hai phong",
            "tp hai phong",
            "thanh pho hai phong",
        ],
        "da nang": [
            "da nang",
            "tp da nang",
            "thanh pho da nang",
        ],
        "can tho": [
            "can tho",
            "tp can tho",
            "thanh pho can tho",
        ],
        "thua thien hue": [
            "thua thien hue",
            "hue",
            "tp hue",
            "thanh pho hue",
        ],
        "ba ria vung tau": [
            "ba ria vung tau",
            "vung tau",
            "tp vung tau",
            "thanh pho vung tau",
        ],
        "dak nong": [
            "dak nong",
            "dac nong",
            "gia nghia",
            "dak mil",
            "dak glong",
            "ta dung",
        ],
        "dak lak": [
            "dak lak",
            "dac lak",
            "buon ho",
        ],
        "gia lai": [
            "pleiku",
        ],
        "an giang": [
            "long xuyen",
        ],
        "dong thap": [
            "cao lanh",
        ],
    }

    province_dict: Dict[str, ProvinceIndex] = {}
    for province in province_index:
        normalized_variants = {
            province.normalized_name,
            slugify_vn(province.province_name.replace("Tỉnh ", "")),
            slugify_vn(province.province_name.replace("Thành phố ", "")),
            slugify_vn(province.province_name),
        }
        for variant in normalized_variants:
            if variant:
                province_dict[variant] = province

    for province in province_index:
        key = slugify_vn(province.province_name)
        extra_aliases = alias_groups.get(key, [])
        for alias in extra_aliases:
            normalized_alias = slugify_vn(alias)
            if normalized_alias:
                province_dict[normalized_alias] = province

    match_keys = sorted(province_dict.keys(), key=len, reverse=True)
    return ProvinceMatcher(province_dict=province_dict, match_keys=match_keys)


def get_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(HEADERS)
    return session


def extract_item_id(detail_url: str) -> Optional[str]:
    if not detail_url:
        return None
    parsed = urlparse(detail_url)
    value = parse_qs(parsed.query).get("item", [None])[0]
    return str(value) if value else None


def get_text_lines(node: Tag) -> List[str]:
    raw = node.get_text("\n", strip=True)
    return [normalize_text(line) for line in raw.splitlines() if normalize_text(line)]


def extract_phone(text: str) -> str:
    match = re.search(r"((?:\+84|0)[0-9\-\.\s]{8,16}[0-9])", text)
    return re.sub(r"[^\d+]", "", match.group(1)) if match else ""


def extract_email(text: str) -> str:
    match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", text)
    return match.group(0) if match else ""


def extract_website(text: str) -> str:
    match = re.search(r"https?://[^\s<>\"]+", text, flags=re.I)
    if match:
        return match.group(0).rstrip(".,);")
    match = re.search(r"\bwww\.[^\s<>\"]+\b", text, flags=re.I)
    if match:
        return f"https://{match.group(0).rstrip('.,);')}"
    return ""


def extract_price(text: str) -> Optional[float]:
    match = re.search(r"([0-9][0-9\.\,]{2,})", text)
    if not match:
        return None
    cleaned = match.group(1).replace(".", "").replace(",", "")
    try:
        return float(cleaned)
    except ValueError:
        return None


def extract_opening_hours(text: str) -> Tuple[str, str]:
    matches = re.findall(r"(\d{1,2}[:h]\d{0,2})", text.lower())
    if not matches:
        return "", ""
    normalized = [m.replace("h", ":") if "h" in m else m for m in matches]
    if len(normalized) == 1:
        return normalized[0], ""
    return normalized[0], normalized[1]


def parse_info_line(data: Dict, line: str) -> None:
    lower = line.lower()
    if "địa chỉ" in lower and not data["diaChi"]:
        data["diaChi"] = normalize_text(line.split(":", 1)[1] if ":" in line else line)
    elif ("điện thoại" in lower or "hotline" in lower or "tel" in lower) and not data["dienThoai"]:
        data["dienThoai"] = extract_phone(line)
    elif ("email" in lower or "@" in line) and not data["email"]:
        data["email"] = extract_email(line)
    elif ("website" in lower or "http" in lower or "www." in lower) and not data["website"]:
        data["website"] = extract_website(line)
    elif ("giá" in lower or "giá vé" in lower) and data["giaVe"] is None:
        data["giaVe"] = extract_price(line)
    elif ("giờ mở cửa" in lower or "giờ hoạt động" in lower or "open" in lower) and not data["gioMoCua"]:
        open_at, close_at = extract_opening_hours(line)
        data["gioMoCua"] = open_at
        data["gioDongCua"] = close_at
    elif ("đặc điểm" in lower or "mô tả" in lower or "giới thiệu" in lower) and not data["moTa"]:
        content = normalize_text(line.split(":", 1)[1] if ":" in line else line)
        if content and content.lower() not in {"đặc điểm", "mô tả", "giới thiệu"}:
            data["moTa"] = content


def parse_place_item(item_node: Tag, category_slug: str) -> Optional[Dict]:
    caption = item_node.find("div", class_="verticle-listing-caption") or item_node
    title_link = caption.find("a", href=re.compile(r"item=\d+"))
    if not title_link:
        for heading in caption.find_all(["h3", "h4", "h5", "strong"]):
            title_link = heading.find("a", href=re.compile(r"item=\d+"))
            if title_link:
                break
    title_node = title_link or caption.find(["h3", "h4", "h5", "strong"])
    if not title_node:
        return None

    name = normalize_text(title_node.get_text(" ", strip=True))
    if not name or len(name) < 2:
        return None

    detail_href = title_link.get("href", "") if title_link else ""
    detail_url = urljoin(BASE_URL, detail_href) if detail_href else ""

    data = {
        "tenDiaDiem": name,
        "diaChi": "",
        "dienThoai": "",
        "email": "",
        "website": "",
        "moTa": "",
        "giaVe": None,
        "gioMoCua": "",
        "gioDongCua": "",
        "detail_url": detail_url,
        "item_id": extract_item_id(detail_url),
        "category": category_slug,
        "images": [],
    }

    for line in get_text_lines(caption):
        parse_info_line(data, line)

    return data


def parse_list_items(soup: BeautifulSoup) -> List[Tag]:
    items: List[Tag] = []
    for container_class in LIST_CONTAINER_CLASSES:
        found = soup.find_all("div", class_=re.compile(rf"\b{re.escape(container_class)}\b", re.I))
        if found:
            items.extend(found)
    if items:
        return items

    # Fallback: node nào có caption + link item=
    candidates = []
    for caption in soup.find_all("div", class_="verticle-listing-caption"):
        parent = caption.find_parent("div")
        if parent and parent not in candidates and caption.find("a", href=re.compile(r"item=\d+")):
            candidates.append(parent)
    return candidates


def scrape_detail_page(session: requests.Session, detail_url: str, delay_seconds: float) -> Dict:
    if not detail_url:
        return {}

    response = session.get(detail_url, timeout=30)
    response.raise_for_status()
    response.encoding = "utf-8"
    soup = BeautifulSoup(response.text, "html.parser")

    detail: Dict[str, object] = {"images": []}

    gallery_links = []
    for anchor in soup.select("a[data-gallery]"):
        href = anchor.get("href", "").strip()
        if href and "/uploads/" in href:
            gallery_links.append(urljoin(BASE_URL, href))
    if gallery_links:
        detail["images"] = list(dict.fromkeys(gallery_links))[:5]

    # Trang detail public thường vẫn chứa text của item đã chọn trong block đầu.
    # Dùng heuristic mềm để lấy các dòng thông tin đầu tiên có giá trị.
    candidate_blocks = soup.select("div.verticleilist, div.cslt-detail, div.content")
    seen_lines: List[str] = []
    for block in candidate_blocks[:8]:
        for line in get_text_lines(block):
            if line not in seen_lines:
                seen_lines.append(line)

    temp = {
        "diaChi": "",
        "dienThoai": "",
        "email": "",
        "website": "",
        "moTa": "",
        "giaVe": None,
        "gioMoCua": "",
        "gioDongCua": "",
    }
    for line in seen_lines:
        parse_info_line(temp, line)

    if temp["moTa"]:
        detail["moTa"] = temp["moTa"]
    if temp["diaChi"]:
        detail["diaChi"] = temp["diaChi"]
    if temp["dienThoai"]:
        detail["dienThoai"] = temp["dienThoai"]
    if temp["email"]:
        detail["email"] = temp["email"]
    if temp["website"]:
        detail["website"] = temp["website"]
    if temp["giaVe"] is not None:
        detail["giaVe"] = temp["giaVe"]
    if temp["gioMoCua"]:
        detail["gioMoCua"] = temp["gioMoCua"]
    if temp["gioDongCua"]:
        detail["gioDongCua"] = temp["gioDongCua"]

    if delay_seconds > 0:
        time.sleep(delay_seconds)

    return detail


def scrape_category(
    session: requests.Session,
    category_slug: str,
    max_pages: Optional[int],
    max_items: Optional[int],
    fetch_detail: bool,
    detail_delay_seconds: float,
) -> List[Dict]:
    config = CATEGORY_CONFIG[category_slug]
    print(f"\n{'=' * 72}")
    print(f"Danh mục: {config['label']} ({category_slug})")
    print(f"{'=' * 72}")

    results: List[Dict] = []
    page = 1

    while True:
        if max_pages is not None and page > max_pages:
            break

        url = f"{BASE_URL}{config['path']}" if page == 1 else f"{BASE_URL}{config['path']}?page={page}"
        print(f"[{category_slug}] Page {page}: {url}")

        response = session.get(url, timeout=30)
        if response.status_code != 200:
            print(f"[{category_slug}] HTTP {response.status_code}, dừng.")
            break

        response.encoding = "utf-8"
        soup = BeautifulSoup(response.text, "html.parser")
        item_nodes = parse_list_items(soup)
        if not item_nodes:
            print(f"[{category_slug}] Không tìm thấy item nào ở page {page}.")
            break

        page_items: List[Dict] = []
        for item_node in item_nodes:
            item = parse_place_item(item_node, category_slug)
            if not item:
                continue

            if fetch_detail and item.get("detail_url"):
                try:
                    detail = scrape_detail_page(session, item["detail_url"], detail_delay_seconds)
                    for key, value in detail.items():
                        if key == "images":
                            if value:
                                item["images"] = list(dict.fromkeys(item["images"] + value))[:5]
                        elif value and (not item.get(key)):
                            item[key] = value
                except Exception as exc:  # pragma: no cover - best effort crawl
                    print(f"[{category_slug}] Detail lỗi {item.get('detail_url')}: {exc}")

            page_items.append(item)
            if max_items is not None and len(results) + len(page_items) >= max_items:
                break

        if not page_items:
            print(f"[{category_slug}] Không parse được item nào ở page {page}.")
            break

        results.extend(page_items)
        print(f"[{category_slug}] Đã lấy {len(page_items)} item ở page {page}. Tổng: {len(results)}")

        if max_items is not None and len(results) >= max_items:
            results = results[:max_items]
            break

        pagination = soup.find(["ul", "div"], class_=re.compile(r"pagination|pager", re.I))
        has_next = False
        if pagination:
            for link in pagination.find_all("a", href=True):
                href = link.get("href", "")
                text = normalize_text(link.get_text(" ", strip=True)).lower()
                data_page = link.get("data-ci-pagination-page")
                if data_page and str(data_page) == str(page + 1):
                    has_next = True
                    break
                if f"page={page + 1}" in href or text in {"cuối cùng", "next", "tiếp", ">" }:
                    has_next = True
                    break

        if not has_next and len(page_items) < 15:
            break

        page += 1

    return results


def province_from_address(address: str, province_matcher: ProvinceMatcher) -> Optional[ProvinceIndex]:
    normalized_address = slugify_vn(address)
    if not normalized_address:
        return None

    compact_address = f" {normalized_address} "
    for key in province_matcher.match_keys:
        if not key:
            continue
        if f" {key} " in compact_address or normalized_address.endswith(key) or normalized_address.startswith(key):
            matched = province_matcher.province_dict.get(key)
            if matched:
                return matched

    for key in province_matcher.match_keys:
        if key and key in normalized_address:
            matched = province_matcher.province_dict.get(key)
            if matched:
                return matched

    return None


def build_source_metadata(item: Dict) -> str:
    payload = {
        "source": "csdl.vietnamtourism.gov.vn",
        "category": item.get("category"),
        "item_id": item.get("item_id"),
        "detail_url": item.get("detail_url"),
        "email": item.get("email", ""),
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def find_existing_place(
    connection: sqlite3.Connection,
    item: Dict,
    province_id: int,
) -> Optional[sqlite3.Row]:
    item_id = item.get("item_id")
    detail_url = item.get("detail_url")

    if item_id:
        existing = connection.execute(
            "SELECT * FROM DIADIEM WHERE dacDiem LIKE ? LIMIT 1",
            [f'%\"item_id\": \"{item_id}\"%'],
        ).fetchone()
        if existing:
            return existing

    if detail_url:
        existing = connection.execute(
            "SELECT * FROM DIADIEM WHERE dacDiem LIKE ? LIMIT 1",
            [f"%{detail_url}%"],
        ).fetchone()
        if existing:
            return existing

    sql = "SELECT * FROM DIADIEM WHERE tenDiaDiem = ? AND maTinhThanh = ?"
    params: List[Any] = [item["tenDiaDiem"], province_id]
    if item.get("diaChi"):
        sql += " AND diaChi = ?"
        params.append(item["diaChi"])
    sql += " LIMIT 1"
    return connection.execute(sql, params).fetchone()


def build_place_payload(existing: Optional[sqlite3.Row], item: Dict, province_id: int, loai: str) -> Dict[str, Any]:
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    existing_dict = dict(existing) if existing else {}
    return {
        "tenDiaDiem": item["tenDiaDiem"],
        "moTa": item.get("moTa") or existing_dict.get("moTa") or "",
        "diaChi": item.get("diaChi") or existing_dict.get("diaChi") or "",
        "maTinhThanh": province_id,
        "loaiDiaDiem": loai,
        "viDo": existing_dict.get("viDo", 0.0) if existing else 0.0,
        "kinhDo": existing_dict.get("kinhDo", 0.0) if existing else 0.0,
        "giaVe": item["giaVe"] if item.get("giaVe") is not None else existing_dict.get("giaVe", 0.0),
        "gioMoCua": item.get("gioMoCua") or existing_dict.get("gioMoCua") or "",
        "gioDongCua": item.get("gioDongCua") or existing_dict.get("gioDongCua") or "",
        "dienThoai": item.get("dienThoai") or existing_dict.get("dienThoai") or "",
        "website": item.get("website") or existing_dict.get("website") or "",
        "danhGiaTrungBinh": existing_dict.get("danhGiaTrungBinh", 0.0),
        "soLuotDanhGia": existing_dict.get("soLuotDanhGia", 0),
        "soLuotXem": existing_dict.get("soLuotXem", 0),
        "maNguoiTao": existing_dict.get("maNguoiTao"),
        "ngayTao": existing_dict.get("ngayTao", now),
        "lanCapNhatCuoi": now,
        "trangThai": existing_dict.get("trangThai", "active") or "active",
        "dacDiem": build_source_metadata(item),
        "tienNghi": existing_dict.get("tienNghi", "") or "",
    }


def upsert_place(connection: sqlite3.Connection, existing: Optional[sqlite3.Row], payload: Dict[str, Any]) -> int:
    if existing:
        connection.execute(
            """
            UPDATE DIADIEM
            SET tenDiaDiem = ?, moTa = ?, diaChi = ?, maTinhThanh = ?, loaiDiaDiem = ?,
                viDo = ?, kinhDo = ?, giaVe = ?, gioMoCua = ?, gioDongCua = ?, dienThoai = ?,
                website = ?, danhGiaTrungBinh = ?, soLuotDanhGia = ?, soLuotXem = ?,
                maNguoiTao = ?, lanCapNhatCuoi = ?, trangThai = ?, dacDiem = ?, tienNghi = ?
            WHERE maDiaDiem = ?
            """,
            [
                payload["tenDiaDiem"],
                payload["moTa"],
                payload["diaChi"],
                payload["maTinhThanh"],
                payload["loaiDiaDiem"],
                payload["viDo"],
                payload["kinhDo"],
                payload["giaVe"],
                payload["gioMoCua"],
                payload["gioDongCua"],
                payload["dienThoai"],
                payload["website"],
                payload["danhGiaTrungBinh"],
                payload["soLuotDanhGia"],
                payload["soLuotXem"],
                payload["maNguoiTao"],
                payload["lanCapNhatCuoi"],
                payload["trangThai"],
                payload["dacDiem"],
                payload["tienNghi"],
                existing["maDiaDiem"],
            ],
        )
        return int(existing["maDiaDiem"])

    cursor = connection.execute(
        """
        INSERT INTO DIADIEM (
            tenDiaDiem, moTa, diaChi, maTinhThanh, loaiDiaDiem, viDo, kinhDo, giaVe,
            gioMoCua, gioDongCua, dienThoai, website, danhGiaTrungBinh, soLuotDanhGia,
            soLuotXem, maNguoiTao, ngayTao, lanCapNhatCuoi, trangThai, dacDiem, tienNghi
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            payload["tenDiaDiem"],
            payload["moTa"],
            payload["diaChi"],
            payload["maTinhThanh"],
            payload["loaiDiaDiem"],
            payload["viDo"],
            payload["kinhDo"],
            payload["giaVe"],
            payload["gioMoCua"],
            payload["gioDongCua"],
            payload["dienThoai"],
            payload["website"],
            payload["danhGiaTrungBinh"],
            payload["soLuotDanhGia"],
            payload["soLuotXem"],
            payload["maNguoiTao"],
            payload["ngayTao"],
            payload["lanCapNhatCuoi"],
            payload["trangThai"],
            payload["dacDiem"],
            payload["tienNghi"],
        ],
    )
    return int(cursor.lastrowid)


def save_images(connection: sqlite3.Connection, place_id: int, images: Iterable[str], source_label: str) -> int:
    created = 0
    for index, image_url in enumerate(dict.fromkeys(images)):
        if not image_url:
            continue
        exists = connection.execute(
            "SELECT maHinhAnh FROM HINHANHDIADIEM WHERE maDiaDiem = ? AND urlHinhAnh = ? LIMIT 1",
            [place_id, image_url],
        ).fetchone()
        if not exists:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            connection.execute(
                """
                INSERT INTO HINHANHDIADIEM (urlHinhAnh, moTa, laChinh, ngayTao, maDiaDiem)
                VALUES (?, ?, ?, ?, ?)
                """,
                [image_url, source_label[:500], 1 if index == 0 else 0, now, place_id],
            )
            created += 1
    return created


def import_places(places: Sequence[Dict], dry_run: bool = False) -> Dict[str, int]:
    connection = get_connection()
    province_matcher = build_province_matcher(connection)
    stats = {"created": 0, "updated": 0, "skipped": 0, "errors": 0, "images_created": 0}

    try:
        for item in places:
            try:
                province = province_from_address(item.get("diaChi", ""), province_matcher)
                if not province:
                    print(f"[SKIP] Không map được tỉnh thành: {item['tenDiaDiem']} | {item.get('diaChi', '')}")
                    stats["skipped"] += 1
                    continue

                config = CATEGORY_CONFIG[item["category"]]
                existing = find_existing_place(connection, item, province.province_id)
                created = existing is None
                payload = build_place_payload(existing, item, province.province_id, config["loai"])

                if dry_run:
                    stats["created" if created else "updated"] += 1
                    continue

                place_id = upsert_place(connection, existing, payload)
                stats["created" if created else "updated"] += 1

                image_count = save_images(connection, place_id, item.get("images", []), f"Nguồn {item['category']}")
                stats["images_created"] += image_count
            except Exception as exc:
                print(f"[ERROR] {item.get('tenDiaDiem', 'Unknown')}: {exc}")
                stats["errors"] += 1

        if not dry_run:
            connection.commit()
        return stats
    finally:
        connection.close()


def parse_categories(raw: str) -> List[str]:
    if raw.lower() == "all":
        return list(CATEGORY_CONFIG.keys())
    categories = [value.strip() for value in raw.split(",") if value.strip()]
    invalid = [value for value in categories if value not in CATEGORY_CONFIG]
    if invalid:
        raise SystemExit(f"Danh mục không hợp lệ: {', '.join(invalid)}")
    return categories


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Crawl dữ liệu từ csdl.vietnamtourism.gov.vn vào DB project.")
    parser.add_argument("--categories", default="all", help="Danh mục, ví dụ: cslt,dest,rest hoặc all")
    parser.add_argument("--max-pages-per-category", type=int, default=None, help="Giới hạn số page mỗi danh mục")
    parser.add_argument("--max-items-per-category", type=int, default=None, help="Giới hạn số item mỗi danh mục")
    parser.add_argument("--detail-delay", type=float, default=0.25, help="Delay giữa các request detail")
    parser.add_argument("--no-detail", action="store_true", help="Không gọi trang detail")
    parser.add_argument("--dry-run", action="store_true", help="Chỉ parse và map, không ghi DB")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="File JSON output")
    return parser


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()
    categories = parse_categories(args.categories)

    print("=" * 72)
    print("CRAWL CSDL DU LỊCH VIỆT NAM")
    print(f"Nguồn: {BASE_URL}")
    print(f"Danh mục: {', '.join(categories)}")
    print(f"Max pages/category: {args.max_pages_per_category or 'không giới hạn'}")
    print(f"Max items/category: {args.max_items_per_category or 'không giới hạn'}")
    print(f"Fetch detail: {'không' if args.no_detail else 'có'}")
    print(f"Dry run: {'có' if args.dry_run else 'không'}")
    print("=" * 72)

    session = get_session()
    all_places: List[Dict] = []

    for category_slug in categories:
        places = scrape_category(
            session=session,
            category_slug=category_slug,
            max_pages=args.max_pages_per_category,
            max_items=args.max_items_per_category,
            fetch_detail=not args.no_detail,
            detail_delay_seconds=args.detail_delay,
        )
        all_places.extend(places)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(all_places, ensure_ascii=False, indent=2), encoding="utf-8")

    stats = import_places(all_places, dry_run=args.dry_run)

    print("\n" + "=" * 72)
    print("KẾT QUẢ")
    print(f"Tổng item crawl được: {len(all_places)}")
    print(f"Tạo mới DIADIEM: {stats['created']}")
    print(f"Cập nhật DIADIEM: {stats['updated']}")
    print(f"Bỏ qua: {stats['skipped']}")
    print(f"Lỗi: {stats['errors']}")
    print(f"Ảnh mới: {stats['images_created']}")
    print(f"JSON output: {output_path}")
    print("=" * 72)


if __name__ == "__main__":
    main()
