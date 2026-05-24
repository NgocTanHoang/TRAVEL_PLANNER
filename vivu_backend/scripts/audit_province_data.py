#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Read-only data quality and coverage audit for a single province."""
from __future__ import annotations

import argparse
import io
import json
import os
import re
import sqlite3
import sys
import unicodedata
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import django


if sys.platform == "win32":
    if sys.stdout.encoding != "utf-8":
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    if sys.stderr.encoding != "utf-8":
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace", line_buffering=True)


BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent
DATA_DIR = REPO_ROOT / "data"
DB_PATH = BACKEND_DIR / "vivudb.sqlite3"

sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "vivu_core.settings")
django.setup()

from apps.places.models import DiaDiem, TinhThanh  # noqa: E402

try:
    from tabulate import tabulate
except ImportError:  # pragma: no cover - optional dependency
    tabulate = None


CATEGORY_LABELS = {
    "cslt": "Khách sạn/Lưu trú",
    "dest": "Điểm tham quan",
    "rest": "Nhà hàng/Ăn uống",
    "shop": "Mua sắm",
    "vcgt": "Giải trí",
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
    "thanh pho",
    "thành phố",
    "tp.",
    "tp ",
    "tx.",
    "tx ",
)

MOJIBAKE_MARKERS = (
    "Ã",
    "Â",
    "Ä",
    "Å",
    "Æ",
    "Ð",
    "Ñ",
    "�",
    "â€™",
    "â€œ",
    "â€",
    "á»",
    "áº",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit chất lượng và độ phủ dữ liệu địa điểm của một tỉnh/thành."
    )
    parser.add_argument(
        "--province",
        required=True,
        help="Tên hoặc mã tỉnh/thành cần kiểm tra. Ví dụ: Quang Ninh hoặc 22",
    )
    parser.add_argument(
        "--min-pois",
        type=int,
        default=500,
        help="Số lượng POI tối thiểu kỳ vọng để đánh giá độ phủ. Mặc định: 500.",
    )
    return parser.parse_args()


def normalize_text(value: str | None) -> str:
    text = (value or "").strip().lower()
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)
    return text


def slugify_vn(value: str) -> str:
    normalized = normalize_text(value).replace("đ", "d")
    normalized = unicodedata.normalize("NFD", normalized)
    normalized = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    normalized = re.sub(r"\b(tinh|thanh pho|tp\.?|thi xa|thi tran)\b", " ", normalized)
    normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
    return re.sub(r"\s+", " ", normalized).strip()


def format_table(rows: list[list[Any]], headers: list[str]) -> str:
    if tabulate is not None:
        return tabulate(rows, headers=headers, tablefmt="github", stralign="left", numalign="right")

    widths = [len(header) for header in headers]
    for row in rows:
        for idx, cell in enumerate(row):
            widths[idx] = max(widths[idx], len(str(cell)))

    def format_row(row: Iterable[Any]) -> str:
        cells = [str(cell).ljust(widths[idx]) for idx, cell in enumerate(row)]
        return " | ".join(cells)

    separator = "-+-".join("-" * width for width in widths)
    body = [format_row(headers), separator]
    body.extend(format_row(row) for row in rows)
    return "\n".join(body)


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def resolve_province(province_arg: str) -> TinhThanh:
    province_arg = province_arg.strip()

    if province_arg.isdigit():
        province = TinhThanh.objects.filter(maTinhThanh=int(province_arg)).first()
        if province:
            return province

    provinces = list(TinhThanh.objects.all().only("maTinhThanh", "tenTinhThanh"))
    exact_matches: list[TinhThanh] = []
    fuzzy_matches: list[TinhThanh] = []
    wanted_slug = slugify_vn(province_arg)
    wanted_norm = normalize_text(province_arg)

    for province in provinces:
        name = province.tenTinhThanh
        name_slug = slugify_vn(name)
        name_norm = normalize_text(name)
        if wanted_slug and wanted_slug == name_slug:
            exact_matches.append(province)
            continue
        if wanted_norm and wanted_norm == name_norm:
            exact_matches.append(province)
            continue
        if wanted_slug and (wanted_slug in name_slug or name_slug in wanted_slug):
            fuzzy_matches.append(province)

    if exact_matches:
        return exact_matches[0]
    if len(fuzzy_matches) == 1:
        return fuzzy_matches[0]

    candidates = ", ".join(
        f"{item.maTinhThanh}:{item.tenTinhThanh}" for item in fuzzy_matches[:10]
    ) or "không có gợi ý"
    raise SystemExit(
        f"[ERROR] Không tìm thấy tỉnh/thành cho input '{province_arg}'. Gợi ý: {candidates}"
    )


def parse_dac_diem(raw_value: str | None) -> dict[str, Any]:
    if not raw_value:
        return {}
    try:
        data = json.loads(raw_value)
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


def classify_category(place: dict[str, Any]) -> str | None:
    metadata = parse_dac_diem(place.get("dacDiem"))
    category = metadata.get("category")
    if isinstance(category, str) and category in CATEGORY_LABELS:
        return category
    loai = place.get("loaiDiaDiem")
    return LOAI_TO_CATEGORY.get(loai)


def extract_district(address: str | None) -> str | None:
    if not address:
        return None
    normalized = normalize_text(address)
    parts = [part.strip() for part in re.split(r"[,;/|-]+", normalized) if part.strip()]
    for part in reversed(parts):
        if any(hint in part for hint in DISTRICT_HINTS):
            return part
    return None


def has_mojibake(value: str | None) -> bool:
    if not value:
        return False
    return any(marker in value for marker in MOJIBAKE_MARKERS)


def build_warning_messages(total_pois: int, category_counts: dict[str, int], min_pois: int) -> list[str]:
    warnings: list[str] = []
    if total_pois < min_pois:
        warnings.append(
            f"[WARNING] Độ phủ chỉ có {total_pois} POI, thấp hơn ngưỡng kỳ vọng {min_pois}. Agent lập lịch trình sẽ dễ lặp điểm hoặc thiếu lựa chọn."
        )
    for category_key, label in CATEGORY_LABELS.items():
        count = category_counts.get(category_key, 0)
        if count == 0:
            warnings.append(
                f"[WARNING] Thiếu hụt dữ liệu danh mục {label} - Agent lập lịch trình chắc chắn sẽ bị lặp hoặc gãy luồng ăn uống/lưu trú."
            )
    return warnings


def query_scalar(cursor: sqlite3.Cursor, query: str, params: tuple[Any, ...]) -> int:
    cursor.execute(query, params)
    row = cursor.fetchone()
    return int(row[0] if row and row[0] is not None else 0)


def audit_province(province: TinhThanh, min_pois: int) -> dict[str, Any]:
    province_places = list(
        DiaDiem.objects.filter(maTinhThanh=province)
        .values(
            "maDiaDiem",
            "tenDiaDiem",
            "moTa",
            "diaChi",
            "loaiDiaDiem",
            "viDo",
            "kinhDo",
            "dacDiem",
        )
    )
    total_pois = len(province_places)

    category_counts: Counter[str] = Counter()
    duplicate_groups: list[dict[str, Any]] = []
    duplicate_map: defaultdict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    mojibake_rows: list[dict[str, Any]] = []

    for place in province_places:
        category = classify_category(place)
        if category:
            category_counts[category] += 1

        district = extract_district(place.get("diaChi"))
        if district:
            duplicate_key = (slugify_vn(place["tenDiaDiem"]), slugify_vn(district))
            duplicate_map[duplicate_key].append(place | {"district": district})

        fields_to_scan = (
            place.get("tenDiaDiem"),
            place.get("moTa"),
            place.get("diaChi"),
            place.get("dacDiem"),
        )
        if any(has_mojibake(field) for field in fields_to_scan):
            mojibake_rows.append(
                {
                    "maDiaDiem": place["maDiaDiem"],
                    "tenDiaDiem": place["tenDiaDiem"],
                    "diaChi": place.get("diaChi") or "",
                }
            )

    for group in duplicate_map.values():
        if len(group) > 1:
            duplicate_groups.append(
                {
                    "tenDiaDiem": group[0]["tenDiaDiem"],
                    "district": group[0]["district"],
                    "count": len(group),
                    "place_ids": [item["maDiaDiem"] for item in group],
                }
            )

    with get_connection() as conn:
        cursor = conn.cursor()
        province_id = province.maTinhThanh

        invalid_coords_count = query_scalar(
            cursor,
            """
            SELECT COUNT(*)
            FROM DIADIEM
            WHERE maTinhThanh = ?
              AND (
                    viDo IS NULL OR kinhDo IS NULL
                    OR viDo = 0 OR kinhDo = 0
                    OR viDo < 8.5 OR viDo > 23.5
                    OR kinhDo < 102.0 OR kinhDo > 110.0
              )
            """,
            (province_id,),
        )

        missing_dacdiem_count = query_scalar(
            cursor,
            """
            SELECT COUNT(*)
            FROM DIADIEM
            WHERE maTinhThanh = ?
              AND (
                    dacDiem IS NULL
                    OR LENGTH(TRIM(dacDiem)) < 20
              )
            """,
            (province_id,),
        )

        missing_images_count = query_scalar(
            cursor,
            """
            SELECT COUNT(*)
            FROM DIADIEM d
            WHERE d.maTinhThanh = ?
              AND NOT EXISTS (
                    SELECT 1
                    FROM HINHANHDIADIEM h
                    WHERE h.maDiaDiem = d.maDiaDiem
              )
            """,
            (province_id,),
        )

    warnings = build_warning_messages(total_pois, dict(category_counts), min_pois)

    return {
        "province": {
            "id": province.maTinhThanh,
            "name": province.tenTinhThanh,
            "slug": slugify_vn(province.tenTinhThanh).replace(" ", "_"),
        },
        "min_pois": min_pois,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "coverage": {
            "total_pois": total_pois,
            "meets_min_pois": total_pois >= min_pois,
            "category_breakdown": {
                key: int(category_counts.get(key, 0))
                for key in CATEGORY_LABELS
            },
        },
        "integrity": {
            "invalid_coordinates": invalid_coords_count,
            "missing_or_short_dacDiem": missing_dacdiem_count,
            "missing_image_links": missing_images_count,
        },
        "anomalies": {
            "duplicate_group_count": len(duplicate_groups),
            "duplicate_groups": duplicate_groups[:25],
            "mojibake_count": len(mojibake_rows),
            "mojibake_samples": mojibake_rows[:25],
        },
        "warnings": warnings,
    }


def print_report(report: dict[str, Any]) -> None:
    province = report["province"]
    coverage = report["coverage"]
    integrity = report["integrity"]
    anomalies = report["anomalies"]

    print("=" * 96)
    print(f"DATA QUALITY & COVERAGE AUDIT: {province['name']} (maTinhThanh={province['id']})")
    print("=" * 96)
    print(f"Ngưỡng POI tối thiểu kỳ vọng: {report['min_pois']}")
    print()

    coverage_rows = [
        ["Tổng số POI", coverage["total_pois"]],
        ["Đạt ngưỡng tối thiểu", "YES" if coverage["meets_min_pois"] else "NO"],
    ]
    print("[Phần A] Coverage & Density Audit")
    print(format_table(coverage_rows, ["Chỉ số", "Giá trị"]))
    print()

    category_rows = [
        [CATEGORY_LABELS[key], coverage["category_breakdown"][key]]
        for key in CATEGORY_LABELS
    ]
    print(format_table(category_rows, ["Danh mục", "Số lượng"]))
    print()

    integrity_rows = [
        ["Tọa độ NULL/0/out-of-range", integrity["invalid_coordinates"]],
        ["dacDiem thiếu hoặc quá ngắn", integrity["missing_or_short_dacDiem"]],
        ["Địa điểm không có hình ảnh liên kết", integrity["missing_image_links"]],
    ]
    print("[Phần B] Schema & Integrity Validation")
    print(format_table(integrity_rows, ["Lỗi kỹ thuật", "Số lượng"]))
    print()

    anomaly_rows = [
        ["Nhóm tiêu đề trùng trong cùng quận/huyện", anomalies["duplicate_group_count"]],
        ["Bản ghi nghi lỗi font/bảng mã", anomalies["mojibake_count"]],
    ]
    print("[Phần C] Anomaly & Duplicate Detection")
    print(format_table(anomaly_rows, ["Phát hiện", "Số lượng"]))
    print()

    if anomalies["duplicate_groups"]:
        duplicate_rows = [
            [
                item["tenDiaDiem"],
                item["district"],
                item["count"],
                ", ".join(str(place_id) for place_id in item["place_ids"][:5]),
            ]
            for item in anomalies["duplicate_groups"][:10]
        ]
        print("Mẫu nhóm trùng lặp:")
        print(format_table(duplicate_rows, ["Tên địa điểm", "Quận/Huyện", "Count", "Place IDs"]))
        print()

    if anomalies["mojibake_samples"]:
        mojibake_rows = [
            [item["maDiaDiem"], item["tenDiaDiem"], item["diaChi"][:60]]
            for item in anomalies["mojibake_samples"][:10]
        ]
        print("Mẫu bản ghi nghi lỗi font:")
        print(format_table(mojibake_rows, ["maDiaDiem", "Tên địa điểm", "Địa chỉ"]))
        print()

    if report["warnings"]:
        print("CẢNH BÁO:")
        for warning in report["warnings"]:
            print(warning)
    else:
        print("[OK] Không phát hiện cảnh báo coverage nghiêm trọng theo ngưỡng hiện tại.")


def write_report(report: dict[str, Any]) -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    file_path = DATA_DIR / f"audit_{report['province']['slug']}.json"
    file_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return file_path


def main() -> None:
    args = parse_args()
    if not DB_PATH.exists():
        raise SystemExit(f"[ERROR] Không tìm thấy database tại {DB_PATH}")

    province = resolve_province(args.province)
    report = audit_province(province, args.min_pois)
    print_report(report)
    output_path = write_report(report)
    print()
    print(f"Đã ghi file JSON: {output_path}")


if __name__ == "__main__":
    main()
