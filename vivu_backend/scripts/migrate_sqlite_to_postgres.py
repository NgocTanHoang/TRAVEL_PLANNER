from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


BACKEND_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = BACKEND_DIR.parent
MANAGE_PY = BACKEND_DIR / "manage.py"
DEFAULT_DUMP_PATH = PROJECT_ROOT / "data" / "datadump_postgres_migration.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Tự động dump dữ liệu từ SQLite và nạp sang PostgreSQL cho Vi Vu."
    )
    parser.add_argument(
        "--mode",
        choices=("dump-sqlite", "migrate-postgres", "load-postgres", "full"),
        default="full",
        help="Bước cần chạy. Mặc định chạy trọn bộ full.",
    )
    parser.add_argument(
        "--dump-path",
        default=str(DEFAULT_DUMP_PATH),
        help="Đường dẫn file JSON dùng để trung chuyển dữ liệu.",
    )
    return parser.parse_args()


def run_manage_command(args: list[str], env_overrides: dict[str, str]) -> None:
    env = os.environ.copy()
    env.update(env_overrides)
    command = [sys.executable, str(MANAGE_PY), *args]
    subprocess.run(
        command,
        check=True,
        cwd=str(BACKEND_DIR),
        env=env,
    )


def dump_sqlite(dump_path: Path) -> None:
    dump_path.parent.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env.update(
        {
            "DATABASE_ENGINE": "django.db.backends.sqlite3",
            "SQLITE_DB_PATH": os.environ.get("SQLITE_DB_PATH", str(BACKEND_DIR / "vivudb.sqlite3")),
        }
    )
    command = [
        sys.executable,
        str(MANAGE_PY),
        "dumpdata",
        "--natural-foreign",
        "--natural-primary",
        "-e",
        "contenttypes",
        "-e",
        "auth.Permission",
        "--indent",
        "4",
    ]
    with dump_path.open("w", encoding="utf-8") as handle:
        subprocess.run(
            command,
            check=True,
            cwd=str(BACKEND_DIR),
            env=env,
            stdout=handle,
        )


def migrate_postgres() -> None:
    run_manage_command(
        ["migrate"],
        {
            "DATABASE_ENGINE": "django.db.backends.postgresql",
        },
    )


def load_postgres(dump_path: Path) -> None:
    run_manage_command(
        ["loaddata", str(dump_path)],
        {
            "DATABASE_ENGINE": "django.db.backends.postgresql",
        },
    )


def main() -> int:
    args = parse_args()
    dump_path = Path(args.dump_path).resolve()

    if args.mode in {"dump-sqlite", "full"}:
        dump_sqlite(dump_path)

    if args.mode in {"migrate-postgres", "full"}:
        migrate_postgres()

    if args.mode in {"load-postgres", "full"}:
        if not dump_path.exists():
            raise FileNotFoundError(f"Không tìm thấy file dump tại {dump_path}")
        load_postgres(dump_path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
