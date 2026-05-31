"""Services ghi nhan analytics cho travel planning."""
from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime
from typing import Any, Optional

from django.contrib.auth import get_user_model
from django.db import close_old_connections
from django.db.utils import OperationalError, ProgrammingError

from apps.places.models import TinhThanh
from utils.security import ensure_sensitive_log_filter, sanitize_sensitive_data

from .models import YeuCauLoTrinh

logger = logging.getLogger(__name__)
ensure_sensitive_log_filter(logger)
User = get_user_model()
_ANALYTICS_EXECUTOR = ThreadPoolExecutor(max_workers=2, thread_name_prefix="analytics-log")


def _chuan_hoa_ten_dia_diem(ten_dia_diem: str) -> str:
    """Chuan hoa ten dia diem de tang kha nang match voi TinhThanh."""
    return " ".join((ten_dia_diem or "").strip().lower().split())


def _tim_tinh_thanh_theo_ten(ten_dia_diem: str) -> Optional[TinhThanh]:
    """
    Tim TinhThanh gan dung tu chuoi nguoi dung nhap.

    Uu tien exact match, sau do fallback sang contains match.
    """
    ten_chuan_hoa = _chuan_hoa_ten_dia_diem(ten_dia_diem)
    if not ten_chuan_hoa:
        return None

    tinh_thanh = TinhThanh.objects.filter(tenTinhThanh__iexact=ten_chuan_hoa).first()
    if tinh_thanh:
        return tinh_thanh

    return TinhThanh.objects.filter(tenTinhThanh__icontains=ten_chuan_hoa).first()


def _to_iso_date(ngay: Any) -> Optional[date]:
    """Chuyen du lieu ngay ve `date` neu co the."""
    if ngay is None:
        return None
    if isinstance(ngay, date):
        return ngay
    if isinstance(ngay, str):
        try:
            return datetime.strptime(ngay, "%Y-%m-%d").date()
        except ValueError:
            return None
    return None


def _build_yeu_cau_lo_trinh_kwargs(
    *,
    user_id: Optional[int],
    loai_yeu_cau: str,
    trang_thai: str,
    diem_di: str,
    diem_den: str,
    so_ngay_di: int,
    so_nguoi: int,
    ngan_sach_du_kien: Optional[float],
    ngay_khoi_hanh_du_kien: Any,
    du_lieu_phan_hoi: Optional[dict[str, Any]],
) -> dict[str, Any]:
    nguoi_dung = User.objects.filter(pk=user_id).first() if user_id else None
    return {
        "maNguoiDung": nguoi_dung,
        "maTinhThanhDiemDi": _tim_tinh_thanh_theo_ten(diem_di),
        "maTinhThanhDiemDen": _tim_tinh_thanh_theo_ten(diem_den),
        "diemDi": diem_di or "",
        "diemDen": diem_den or "",
        "ngayKhoiHanhDuKien": _to_iso_date(ngay_khoi_hanh_du_kien),
        "soNgayDi": max(1, int(so_ngay_di or 1)),
        "soNguoi": max(1, int(so_nguoi or 1)),
        "nganSachDuKien": ngan_sach_du_kien,
        "loaiYeuCau": loai_yeu_cau,
        "trangThai": trang_thai,
        "duLieuPhanHoi": sanitize_sensitive_data(du_lieu_phan_hoi or {}),
    }


def _ghi_nhan_yeu_cau_lo_trinh(
    *,
    user_id: Optional[int],
    loai_yeu_cau: str,
    trang_thai: str,
    diem_di: str,
    diem_den: str,
    so_ngay_di: int,
    so_nguoi: int,
    ngan_sach_du_kien: Optional[float],
    ngay_khoi_hanh_du_kien: Any,
    du_lieu_phan_hoi: Optional[dict[str, Any]],
) -> None:
    """Ham chay nen de tao ban ghi analytics."""
    close_old_connections()

    try:
        YeuCauLoTrinh.objects.create(
            **_build_yeu_cau_lo_trinh_kwargs(
                user_id=user_id,
                loai_yeu_cau=loai_yeu_cau,
                trang_thai=trang_thai,
                diem_di=diem_di,
                diem_den=diem_den,
                so_ngay_di=so_ngay_di,
                so_nguoi=so_nguoi,
                ngan_sach_du_kien=ngan_sach_du_kien,
                ngay_khoi_hanh_du_kien=ngay_khoi_hanh_du_kien,
                du_lieu_phan_hoi=du_lieu_phan_hoi,
            )
        )
    except (OperationalError, ProgrammingError) as exc:
        logger.warning("Analytics table chua san sang de ghi log: %s", exc)
    except Exception as exc:
        logger.error("Khong the ghi nhan analytics cho yeu cau lo trinh: %s", exc, exc_info=True)
    finally:
        close_old_connections()


def tao_ban_ghi_yeu_cau_lo_trinh(
    *,
    user_id: Optional[int],
    loai_yeu_cau: str,
    trang_thai: str,
    diem_di: str,
    diem_den: str,
    so_ngay_di: int,
    so_nguoi: int,
    ngan_sach_du_kien: Optional[float],
    ngay_khoi_hanh_du_kien: Any = None,
    du_lieu_phan_hoi: Optional[dict[str, Any]] = None,
) -> Optional[YeuCauLoTrinh]:
    """Tao ban ghi analytics dong bo de theo doi mot workflow dang chay."""
    close_old_connections()
    try:
        return YeuCauLoTrinh.objects.create(
            **_build_yeu_cau_lo_trinh_kwargs(
                user_id=user_id,
                loai_yeu_cau=loai_yeu_cau,
                trang_thai=trang_thai,
                diem_di=diem_di,
                diem_den=diem_den,
                so_ngay_di=so_ngay_di,
                so_nguoi=so_nguoi,
                ngan_sach_du_kien=ngan_sach_du_kien,
                ngay_khoi_hanh_du_kien=ngay_khoi_hanh_du_kien,
                du_lieu_phan_hoi=du_lieu_phan_hoi,
            )
        )
    except (OperationalError, ProgrammingError) as exc:
        logger.warning("Analytics table chua san sang de tao workflow ledger: %s", exc)
        return None
    except Exception as exc:
        logger.error("Khong the tao workflow ledger analytics: %s", exc, exc_info=True)
        return None
    finally:
        close_old_connections()


def cap_nhat_yeu_cau_lo_trinh(
    ma_yeu_cau: Optional[int],
    *,
    trang_thai: Optional[str] = None,
    du_lieu_phan_hoi: Optional[dict[str, Any]] = None,
    merge_du_lieu_phan_hoi: Optional[dict[str, Any]] = None,
) -> Optional[YeuCauLoTrinh]:
    """Cap nhat ban ghi analytics dang theo doi workflow theo maYeuCau."""
    if not ma_yeu_cau:
        return None

    close_old_connections()
    try:
        yeu_cau = YeuCauLoTrinh.objects.filter(pk=ma_yeu_cau).first()
        if yeu_cau is None:
            return None

        update_fields: list[str] = []
        if trang_thai:
            yeu_cau.trangThai = trang_thai
            update_fields.append("trangThai")

        if du_lieu_phan_hoi is not None:
            yeu_cau.duLieuPhanHoi = du_lieu_phan_hoi
            update_fields.append("duLieuPhanHoi")
        elif merge_du_lieu_phan_hoi:
            existing_payload = yeu_cau.duLieuPhanHoi if isinstance(yeu_cau.duLieuPhanHoi, dict) else {}
            merged_payload = dict(existing_payload)
            merged_payload.update(sanitize_sensitive_data(merge_du_lieu_phan_hoi))
            yeu_cau.duLieuPhanHoi = merged_payload
            update_fields.append("duLieuPhanHoi")

        if update_fields:
            yeu_cau.save(update_fields=update_fields + ["lanCapNhatCuoi"])
        return yeu_cau
    except (OperationalError, ProgrammingError) as exc:
        logger.warning("Analytics table chua san sang de cap nhat workflow ledger: %s", exc)
        return None
    except Exception as exc:
        logger.error("Khong the cap nhat workflow ledger analytics: %s", exc, exc_info=True)
        return None
    finally:
        close_old_connections()


def ghi_nhan_yeu_cau_lo_trinh_async(
    *,
    user_id: Optional[int],
    loai_yeu_cau: str,
    trang_thai: str,
    diem_di: str,
    diem_den: str,
    so_ngay_di: int,
    so_nguoi: int,
    ngan_sach_du_kien: Optional[float],
    ngay_khoi_hanh_du_kien: Any = None,
    du_lieu_phan_hoi: Optional[dict[str, Any]] = None,
) -> None:
    """
    Day ghi log analytics sang nen de khong block request chinh.

    Dung thread pool nho vi thao tac chu yeu la mot insert SQLite/PostgreSQL.
    """
    _ANALYTICS_EXECUTOR.submit(
        _ghi_nhan_yeu_cau_lo_trinh,
        user_id=user_id,
        loai_yeu_cau=loai_yeu_cau,
        trang_thai=trang_thai,
        diem_di=diem_di,
        diem_den=diem_den,
        so_ngay_di=so_ngay_di,
        so_nguoi=so_nguoi,
        ngan_sach_du_kien=ngan_sach_du_kien,
        ngay_khoi_hanh_du_kien=ngay_khoi_hanh_du_kien,
        du_lieu_phan_hoi=du_lieu_phan_hoi,
    )
