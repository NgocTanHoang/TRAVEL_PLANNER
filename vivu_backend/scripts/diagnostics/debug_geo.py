"""Quick diagnostic script for geo distance calculations."""
from __future__ import annotations

import os
import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parents[2]
REPO_ROOT = BACKEND_DIR.parent

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "vivu_core.settings")

import django  # noqa: E402

django.setup()

from tools.geo_tools import get_geo_tools  # noqa: E402


def test_geo() -> None:
    geo = get_geo_tools()

    print("Testing HCM -> Vung Tau")
    print(f"Result: {geo.calculate_distance_time('Ho Chi Minh City', 'Vung Tau')}")

    print("Testing Hanoi -> Haiphong")
    print(f"Result: {geo.calculate_distance_time('Hanoi', 'Haiphong')}")

    print("Testing HCM -> Da Nang")
    print(f"Result: {geo.calculate_distance_time('Ho Chi Minh City', 'Da Nang')}")


if __name__ == "__main__":
    test_geo()
