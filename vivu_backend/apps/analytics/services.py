"""Services ghi nhận analytics cho travel planning."""
from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime
from typing import Any, Optional

from django.contrib.auth import get_user_model
from django.db import close_old_connections
from django.db.utils import OperationalError, ProgrammingError

from apps.places.models import TinhThanh

from .models import YeuCauLoTrinh

logger = logging.getLogger(__name__)
User = get_user_model()
_ANALYTICS_EXECUTOR = ThreadPoolExecutor(max_workers=2, thread_name_prefix="analytics-log")


def _chuan_hoa_ten_dia_diem(ten_dia_diem: str) -> str:
    """Chuẩn hóa tên địa điểm để tăng khả năng match với TinhThanh."""
    return " ".join((ten_dia_diem or "").strip().lower().split())


def _tim_tinh_thanh_theo_ten(ten_dia_diem: str) -> Optional[TinhThanh]:
    """
    Tìm TinhThanh gần đúng từ chuỗi người dùng nhập.

    Ưu tiên exact match, sau đó fallback sang contains match.
    """
    ten_chuan_hoa = _chuan_hoa_ten_dia_diem(ten_dia_diem)
    if not ten_chuan_hoa:
        return None

    tinh_thanh = TinhThanh.objects.filter(tenTinhThanh__iexact=ten_chuan_hoa).first()
    if tinh_thanh:
        return tinh_thanh

    return TinhThanh.objects.filter(tenTinhThanh__icontains=ten_chuan_hoa).first()


def _to_iso_date(ngay: Any) -> Optional[date]:
    """Chuyển dữ liệu ngày về `date` nếu có thể."""
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
    """Hàm chạy nền để tạo bản ghi analytics."""
    close_old_connections()

    try:
        nguoi_dung = User.objects.filter(pk=user_id).first() if user_id else None
        YeuCauLoTrinh.objects.create(
            maNguoiDung=nguoi_dung,
            maTinhThanhDiemDi=_tim_tinh_thanh_theo_ten(diem_di),
            maTinhThanhDiemDen=_tim_tinh_thanh_theo_ten(diem_den),
            diemDi=diem_di or "",
            diemDen=diem_den or "",
            ngayKhoiHanhDuKien=_to_iso_date(ngay_khoi_hanh_du_kien),
            soNgayDi=max(1, int(so_ngay_di or 1)),
            soNguoi=max(1, int(so_nguoi or 1)),
            nganSachDuKien=ngan_sach_du_kien,
            loaiYeuCau=loai_yeu_cau,
            trangThai=trang_thai,
            duLieuPhanHoi=du_lieu_phan_hoi or {},
        )
    except (OperationalError, ProgrammingError) as exc:
        # Không làm hỏng request chính nếu bảng analytics chưa được migrate.
        logger.warning("Analytics table chưa sẵn sàng để ghi log: %s", exc)
    except Exception as exc:
        logger.error("Không thể ghi nhận analytics cho yêu cầu lộ trình: %s", exc, exc_info=True)
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
    Đẩy ghi log analytics sang nền để không block request chính.

    Dùng thread pool nhỏ vì thao tác chủ yếu là một insert SQLite/PostgreSQL.
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
