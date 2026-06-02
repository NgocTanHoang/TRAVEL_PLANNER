from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import List


REPO_ROOT = Path(__file__).resolve().parents[2]
BACKEND_DIR = REPO_ROOT / "vivu_backend"
OUTPUT_DIR = REPO_ROOT / "vivu_scraper" / "outputs"


def run_command(cmd: List[str]) -> int:
    print(">>>", " ".join(cmd))
    completed = subprocess.run(cmd, cwd=str(REPO_ROOT))
    return completed.returncode


def run_schema() -> int:
    return run_command([sys.executable, str(REPO_ROOT / "vivu_scraper" / "scripts" / "export_diadiem_schema.py")])


def run_tourism_db(args: argparse.Namespace) -> int:
    cmd = [
        sys.executable,
        str(BACKEND_DIR / "scripts" / "scrape_vietnam_tourism_db.py"),
        "--categories",
        args.categories,
        "--output",
        str(OUTPUT_DIR / "tourism_db_raw.json"),
        "--csv-output",
        str(OUTPUT_DIR / "tourism_db_diadiem.csv"),
    ]
    if args.max_pages_per_category is not None:
        cmd.extend(["--max-pages-per-category", str(args.max_pages_per_category)])
    if args.max_items_per_category is not None:
        cmd.extend(["--max-items-per-category", str(args.max_items_per_category)])
    if args.dry_run:
        cmd.append("--dry-run")
    if args.no_detail:
        cmd.append("--no-detail")
    return run_command(cmd)


def run_osm(args: argparse.Namespace) -> int:
    sqlite_path = OUTPUT_DIR / "osm_places.sqlite3"
    cmd = [
        sys.executable,
        str(BACKEND_DIR / "scripts" / "poi_harvest.py"),
        "--limit",
        str(args.limit),
        "--db",
        str(sqlite_path),
    ]
    return run_command(cmd)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Public data crawling pipeline cho Vi Vu. Tap trung vao nguon cong khai, khong bypass anti-bot."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("schema", help="Xuat schema bang DIADIEM tu Django model")

    tourism = subparsers.add_parser("tourism-db", help="Chay pipeline crawl nguon public csdl.vietnamtourism.gov.vn")
    tourism.add_argument("--categories", default="all")
    tourism.add_argument("--max-pages-per-category", type=int, default=None)
    tourism.add_argument("--max-items-per-category", type=int, default=None)
    tourism.add_argument("--dry-run", action="store_true")
    tourism.add_argument("--no-detail", action="store_true")

    osm = subparsers.add_parser("osm", help="Harvest POI cong khai tu OSM/Overpass vao SQLite rieng")
    osm.add_argument("--limit", type=int, default=20000)

    return parser


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "schema":
        return run_schema()
    if args.command == "tourism-db":
        return run_tourism_db(args)
    if args.command == "osm":
        return run_osm(args)
    parser.error("Unsupported command")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
