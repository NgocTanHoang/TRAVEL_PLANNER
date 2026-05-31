"""SQLite schema alignment script for ViVu project.

This script rewrites legacy foreign keys so that tables reference the
production tables (`TINHTHANH`, `DIADIEM`, ...), adds the `maTinhThanh`
column to `LICHTRINH`, and creates the AI itinerary tables when missing.

Usage:
    python manage.py shell -c "exec(open('scripts/align_database_schema.py', encoding='utf-8').read())"

The script only performs work when discrepancies are detected, so it can be
rerun safely.
"""

from __future__ import annotations

import sqlite3
from typing import Iterable

from django.conf import settings


DB_PATH = settings.DATABASES["default"]["NAME"]


def table_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone()
    return row is not None


def read_table_sql(conn: sqlite3.Connection, name: str) -> str:
    row = conn.execute(
        "SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (name,)
    ).fetchone()
    return row[0] if row else ""


def rebuild_table(
    conn: sqlite3.Connection,
    table: str,
    create_sql: str,
    columns: Iterable[str],
) -> None:
    col_string = ", ".join(columns)
    conn.executescript(
        f"""
        ALTER TABLE {table} RENAME TO {table}__old;
        {create_sql}
        INSERT INTO {table} ({col_string})
        SELECT {col_string} FROM {table}__old;
        DROP TABLE {table}__old;
        """
    )


def ensure_diadiem(conn: sqlite3.Connection) -> None:
    sql = read_table_sql(conn, "DIADIEM")
    if "REFERENCES TINHTHANH" in sql and "ON DELETE RESTRICT" in sql:
        print("[DIADIEM] Foreign keys already aligned")
        return

    print("[DIADIEM] Rebuilding with PROTECT/SET NULL on FKs")
    create_sql = """
    CREATE TABLE DIADIEM (
        maDiaDiem INTEGER PRIMARY KEY AUTOINCREMENT,
        tenDiaDiem varchar(255) NOT NULL,
        moTa TEXT NOT NULL,
        diaChi varchar(500) NOT NULL,
        maTinhThanh INTEGER NOT NULL,
        loaiDiaDiem varchar(50) NOT NULL,
        viDo REAL NOT NULL DEFAULT 0.0,
        kinhDo REAL NOT NULL DEFAULT 0.0,
        giaVe REAL NOT NULL DEFAULT 0.0,
        gioMoCua varchar(50) NOT NULL,
        gioDongCua varchar(50) NOT NULL,
        dienThoai varchar(20) NOT NULL,
        website varchar(200) NOT NULL,
        danhGiaTrungBinh REAL NOT NULL DEFAULT 0.0,
        soLuotDanhGia INTEGER NOT NULL DEFAULT 0,
        soLuotXem INTEGER NOT NULL DEFAULT 0,
        maNguoiTao INTEGER NULL,
        ngayTao datetime NOT NULL,
        lanCapNhatCuoi datetime NOT NULL,
        trangThai varchar(20) NOT NULL DEFAULT 'active',
        dacDiem TEXT NOT NULL,
        tienNghi TEXT NOT NULL,
        FOREIGN KEY (maTinhThanh) REFERENCES TINHTHANH(maTinhThanh)
            ON DELETE RESTRICT ON UPDATE CASCADE,
        FOREIGN KEY (maNguoiTao) REFERENCES NGUOIDUNG(maNguoiDung)
            ON DELETE SET NULL ON UPDATE CASCADE
    );
    """
    cols = [
        "maDiaDiem",
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
        "danhGiaTrungBinh",
        "soLuotDanhGia",
        "soLuotXem",
        "maNguoiTao",
        "ngayTao",
        "lanCapNhatCuoi",
        "trangThai",
        "dacDiem",
        "tienNghi",
    ]
    rebuild_table(conn, "DIADIEM", create_sql, cols)
    conn.executescript(
        """
        CREATE INDEX IF NOT EXISTS DIADIEM_maTinhThanh_loaiDiaDiem_idx
            ON DIADIEM(maTinhThanh, loaiDiaDiem);
        CREATE INDEX IF NOT EXISTS DIADIEM_trangThai_idx
            ON DIADIEM(trangThai);
        """
    )


def ensure_diadiem_child(
    conn: sqlite3.Connection,
    table: str,
    create_sql: str,
    columns: Iterable[str],
) -> None:
    sql = read_table_sql(conn, table)
    if "REFERENCES DIADIEM(" in sql and "ON DELETE CASCADE" in sql:
        print(f"[{table}] Already references DIADIEM")
        return
    print(f"[{table}] Rebuilding to reference DIADIEM")
    rebuild_table(conn, table, create_sql, columns)


def ensure_diadiem_children(conn: sqlite3.Connection) -> None:
    ensure_diadiem_child(
        conn,
        "HINHANHDIADIEM",
        """
        CREATE TABLE HINHANHDIADIEM (
            maHinhAnh INTEGER PRIMARY KEY AUTOINCREMENT,
            urlHinhAnh varchar(500) NOT NULL,
            moTa varchar(500) NOT NULL,
            laChinh bool NOT NULL,
            ngayTao datetime NOT NULL,
            maDiaDiem INTEGER NOT NULL,
            FOREIGN KEY (maDiaDiem) REFERENCES DIADIEM(maDiaDiem)
                ON DELETE CASCADE ON UPDATE CASCADE
        );
        """,
        ["maHinhAnh", "urlHinhAnh", "moTa", "laChinh", "ngayTao", "maDiaDiem"],
    )

    ensure_diadiem_child(
        conn,
        "DIADIEM_YEUTHICH",
        """
        CREATE TABLE DIADIEM_YEUTHICH (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ngayThem datetime NOT NULL,
            ghiChu TEXT NOT NULL,
            maDiaDiem INTEGER NOT NULL,
            maNguoiDung INTEGER NOT NULL,
            FOREIGN KEY (maDiaDiem) REFERENCES DIADIEM(maDiaDiem)
                ON DELETE CASCADE ON UPDATE CASCADE,
            FOREIGN KEY (maNguoiDung) REFERENCES NGUOIDUNG(maNguoiDung)
                ON DELETE CASCADE ON UPDATE CASCADE
        );
        """,
        ["id", "ngayThem", "ghiChu", "maDiaDiem", "maNguoiDung"],
    )

    ensure_diadiem_child(
        conn,
        "DANHGIA",
        """
        CREATE TABLE DANHGIA (
            maDanhGia INTEGER PRIMARY KEY AUTOINCREMENT,
            diemDanhGia INTEGER NOT NULL,
            tieuDe varchar(255) NOT NULL,
            noiDung TEXT NOT NULL,
            ngayTao datetime NOT NULL,
            lanCapNhatCuoi datetime NOT NULL,
            soLuotThich INTEGER NOT NULL,
            trangThai varchar(20) NOT NULL,
            maNguoiDung INTEGER NOT NULL,
            maDiaDiem INTEGER NOT NULL,
            FOREIGN KEY (maDiaDiem) REFERENCES DIADIEM(maDiaDiem)
                ON DELETE CASCADE ON UPDATE CASCADE,
            FOREIGN KEY (maNguoiDung) REFERENCES NGUOIDUNG(maNguoiDung)
                ON DELETE CASCADE ON UPDATE CASCADE
        );
        """,
        [
            "maDanhGia",
            "diemDanhGia",
            "tieuDe",
            "noiDung",
            "ngayTao",
            "lanCapNhatCuoi",
            "soLuotThich",
            "trangThai",
            "maNguoiDung",
            "maDiaDiem",
        ],
    )

    ensure_diadiem_child(
        conn,
        "LICHTRINH_DIADIEM",
        """
        CREATE TABLE LICHTRINH_DIADIEM (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ngayThamQuan date NOT NULL,
            thoiGianThamQuan varchar(50) NOT NULL,
            thuTu INTEGER NULL,
            ghiChu TEXT NOT NULL,
            chiPhiUocTinh REAL NULL,
            maDiaDiem INTEGER NOT NULL,
            maLichTrinh INTEGER NOT NULL,
            FOREIGN KEY (maDiaDiem) REFERENCES DIADIEM(maDiaDiem)
                ON DELETE CASCADE ON UPDATE CASCADE,
            FOREIGN KEY (maLichTrinh) REFERENCES LICHTRINH(maLichTrinh)
                ON DELETE CASCADE ON UPDATE CASCADE
        );
        CREATE UNIQUE INDEX IF NOT EXISTS LICHTRINH_DIADIEM_unique
            ON LICHTRINH_DIADIEM(maLichTrinh, maDiaDiem, ngayThamQuan);
        """,
        [
            "id",
            "ngayThamQuan",
            "thoiGianThamQuan",
            "thuTu",
            "ghiChu",
            "chiPhiUocTinh",
            "maDiaDiem",
            "maLichTrinh",
        ],
    )


def ensure_lichtrinh(conn: sqlite3.Connection) -> None:
    sql = read_table_sql(conn, "LICHTRINH")
    fk_ok = (
        "REFERENCES TINHTHANH" in sql
        and "ON DELETE RESTRICT" in sql
        and "ON DELETE SET NULL" in sql
        and "is_ai_generated" in sql
    )
    if fk_ok:
        print("[LICHTRINH] Foreign keys already aligned")
    else:
        print("[LICHTRINH] Rebuilding with PROTECT/SET NULL FKs")
        create_sql = """
    CREATE TABLE LICHTRINH (
        maLichTrinh INTEGER PRIMARY KEY AUTOINCREMENT,
        tieuDe varchar(255) NOT NULL,
        moTa TEXT NOT NULL,
        ngayBatDau date NOT NULL,
        ngayKetThuc date NOT NULL,
        soNgay INTEGER NULL,
        soNguoi INTEGER NOT NULL,
        nganSach REAL NULL,
        chiPhiUocTinh REAL NULL,
        trangThai varchar(20) NOT NULL,
        laCongKhai bool NOT NULL,
        is_ai_generated bool NOT NULL DEFAULT 0,
        soLuotXem INTEGER NOT NULL,
        soLuotThich INTEGER NOT NULL,
        ngayTao datetime NOT NULL,
        lanCapNhatCuoi datetime NOT NULL,
        chiTiet TEXT NOT NULL,
        maNguoiDung INTEGER NULL,
        maTinhThanh INTEGER NULL,
        FOREIGN KEY (maNguoiDung) REFERENCES NGUOIDUNG(maNguoiDung)
            ON DELETE SET NULL ON UPDATE CASCADE,
        FOREIGN KEY (maTinhThanh) REFERENCES TINHTHANH(maTinhThanh)
            ON DELETE RESTRICT ON UPDATE CASCADE
    );
    """
        columns = [
            "maLichTrinh",
            "tieuDe",
            "moTa",
            "ngayBatDau",
            "ngayKetThuc",
            "soNgay",
            "soNguoi",
            "nganSach",
            "chiPhiUocTinh",
            "trangThai",
            "laCongKhai",
            "is_ai_generated",
            "soLuotXem",
            "soLuotThich",
            "ngayTao",
            "lanCapNhatCuoi",
            "chiTiet",
            "maNguoiDung",
            "maTinhThanh",
        ]
        rebuild_table(conn, "LICHTRINH", create_sql, columns)

    # Ensure junction table points to the rebuilt LICHTRINH table
    ensure_diadiem_child(
        conn,
        "LICHTRINH_DIADIEM",
        """
        CREATE TABLE LICHTRINH_DIADIEM (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ngayThamQuan date NOT NULL,
            thoiGianThamQuan varchar(50) NOT NULL,
            thuTu INTEGER NULL,
            ghiChu TEXT NOT NULL,
            chiPhiUocTinh REAL NULL,
            maDiaDiem INTEGER NOT NULL,
            maLichTrinh INTEGER NOT NULL,
            FOREIGN KEY (maDiaDiem) REFERENCES DIADIEM(maDiaDiem)
                ON DELETE CASCADE ON UPDATE CASCADE,
            FOREIGN KEY (maLichTrinh) REFERENCES LICHTRINH(maLichTrinh)
                ON DELETE CASCADE ON UPDATE CASCADE
        );
        CREATE UNIQUE INDEX IF NOT EXISTS LICHTRINH_DIADIEM_unique
            ON LICHTRINH_DIADIEM(maLichTrinh, maDiaDiem, ngayThamQuan);
        """,
        [
            "id",
            "ngayThamQuan",
            "thoiGianThamQuan",
            "thuTu",
            "ghiChu",
            "chiPhiUocTinh",
            "maDiaDiem",
            "maLichTrinh",
        ],
    )


def ensure_ai_tables(conn: sqlite3.Connection) -> None:
    for table_name in ("LICHTRINHAI_DIADIEM", "LICHTRINHAI"):
        if table_exists(conn, table_name):
            print(f"[{table_name}] Gỡ bỏ bảng AI đã deprecate")
            conn.execute(f"DROP TABLE {table_name}")


def drop_legacy_tables(conn: sqlite3.Connection) -> None:
    for name in ["DIADIEM_BACKUP", "DIADIEM_OLD", "TINHTHANH_OLD", "DIADIEMYEUTHICH"]:
        if table_exists(conn, name):
            print(f"[{name}] Gỡ bỏ bảng legacy")
            conn.execute(f"DROP TABLE {name}")


def main() -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys=OFF")
    try:
        ensure_diadiem(conn)
        ensure_diadiem_children(conn)
        ensure_lichtrinh(conn)
        ensure_ai_tables(conn)
        drop_legacy_tables(conn)
        conn.commit()
    finally:
        conn.execute("PRAGMA foreign_keys=ON")
        conn.commit()
        conn.close()


if __name__ == "__main__":
    main()
