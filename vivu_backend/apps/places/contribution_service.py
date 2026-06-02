"""Utilities for unified POI contribution submission and approval flows."""
from __future__ import annotations

import json
import logging
import os
from typing import Any

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from apps.itineraries.models import DongGop

from .models import DiaDiem, TinhThanh

logger = logging.getLogger(__name__)


def is_admin_role(user) -> bool:
    """Return True when the account can approve contributions."""
    if not user or not user.is_authenticated:
        return False
    if getattr(user, "is_superuser", False):
        return True
    role = str(getattr(user, "vaiTro", "") or "").strip().lower()
    return role == "admin"


def ensure_admin_role(user) -> None:
    """Raise when a non-admin attempts to approve a contribution."""
    if not is_admin_role(user):
        raise PermissionDenied("Chỉ tài khoản quản trị mới được phép duyệt đóng góp.")


def safe_float(value: Any, default: float = 0.0) -> float:
    """Best-effort float conversion for contribution payloads."""
    try:
        if value in (None, ""):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_json_text(value: Any) -> str:
    """Serialize structured contribution payloads into JSON text fields."""
    if isinstance(value, str):
        return value
    if value in (None, ""):
        return ""
    return json.dumps(value, ensure_ascii=False)


def build_place_document(place: DiaDiem) -> str:
    """Create a normalized Chroma document for an approved place."""
    parts = [
        f"Tên: {place.tenDiaDiem}",
        f"Tỉnh thành: {place.maTinhThanh.tenTinhThanh}",
        f"Loại: {place.loaiDiaDiem}",
    ]
    if place.diaChi:
        parts.append(f"Địa chỉ: {place.diaChi}")
    if place.moTa:
        parts.append(f"Mô tả: {place.moTa}")
    return ". ".join(parts)


def build_place_metadata(place: DiaDiem) -> dict[str, Any]:
    """Create Chroma metadata bound to the relational primary key."""
    return {
        "name": place.tenDiaDiem[:200],
        "city": place.maTinhThanh.tenTinhThanh[:100],
        "province": place.maTinhThanh.tenTinhThanh[:100],
        "category": place.loaiDiaDiem[:100],
        "description": (place.moTa or "")[:1000],
        "address": (place.diaChi or "")[:500],
        "source": "dong_gop_approval",
        "place_id": int(place.maDiaDiem),
        "item_id": f"donggop-{place.maDiaDiem}",
        "detail_url": "",
        "price": float(place.giaVe or 0.0),
        "rating": float(place.danhGiaTrungBinh or 0.0),
        "latitude": float(place.viDo or 0.0),
        "longitude": float(place.kinhDo or 0.0),
    }


def sync_place_to_chroma(place: DiaDiem) -> None:
    """Mirror an approved POI into the running ChromaDB node."""
    import chromadb

    client = chromadb.HttpClient(
        host=os.getenv("CHROMA_HOST", "127.0.0.1"),
        port=int(os.getenv("CHROMA_PORT", "8000")),
    )
    collection = client.get_or_create_collection(
        name="vietnam_places",
        metadata={"hnsw:space": "cosine"},
    )
    collection.upsert(
        ids=[str(place.maDiaDiem)],
        documents=[build_place_document(place)],
        metadatas=[build_place_metadata(place)],
    )


def resolve_tinh_thanh(payload: dict[str, Any], fallback_place: DiaDiem | None = None) -> TinhThanh:
    """Resolve the target province for a contribution payload."""
    if fallback_place is not None:
        return fallback_place.maTinhThanh

    ma_tinh_thanh = payload.get("maTinhThanh") or payload.get("ma_tinh_thanh")
    if ma_tinh_thanh:
        tinh_thanh = TinhThanh.objects.filter(pk=ma_tinh_thanh).first()
        if tinh_thanh:
            return tinh_thanh

    ten_tinh_thanh = str(
        payload.get("tenTinhThanh")
        or payload.get("ten_tinh_thanh")
        or payload.get("province")
        or ""
    ).strip()
    if ten_tinh_thanh:
        tinh_thanh = TinhThanh.objects.filter(tenTinhThanh__iexact=ten_tinh_thanh).first()
        if tinh_thanh:
            return tinh_thanh

    raise ValidationError("Không xác định được tỉnh thành hợp lệ để duyệt đóng góp.")


def approve_contribution(obj: DongGop, *, approver) -> DiaDiem | None:
    """Approve a unified contribution and merge it into DIADIEM."""
    payload = obj.duLieuBoSung if isinstance(obj.duLieuBoSung, dict) else {}
    if obj.loaiDongGop not in {"THEM_MOI_POI", "SUA_DOI_POI"}:
        return obj.maDiaDiem

    source_place = obj.maDiaDiem if obj.loaiDongGop == "SUA_DOI_POI" else None
    tinh_thanh = resolve_tinh_thanh(payload, fallback_place=source_place)

    defaults = {
        "tenDiaDiem": str(payload.get("tenDiaDiem") or payload.get("ten_dia_diem") or payload.get("name") or obj.noiDung[:255]).strip()[:255],
        "moTa": str(payload.get("moTa") or payload.get("mo_ta") or payload.get("description") or obj.noiDung or "").strip(),
        "diaChi": str(payload.get("diaChi") or payload.get("dia_chi") or payload.get("address") or "").strip()[:500],
        "maTinhThanh": tinh_thanh,
        "loaiDiaDiem": str(payload.get("loaiDiaDiem") or payload.get("loai_dia_diem") or payload.get("category") or "khac").strip() or "khac",
        "viDo": safe_float(payload.get("viDo") or payload.get("latitude") or (payload.get("toa_do") or {}).get("vi_do"), default=0.0),
        "kinhDo": safe_float(payload.get("kinhDo") or payload.get("longitude") or (payload.get("toa_do") or {}).get("kinh_do"), default=0.0),
        "giaVe": safe_float(payload.get("giaVe") or payload.get("price"), default=0.0),
        "gioMoCua": str(payload.get("gioMoCua") or payload.get("opening_hours") or "").strip()[:50],
        "gioDongCua": str(payload.get("gioDongCua") or payload.get("closing_hours") or "").strip()[:50],
        "dienThoai": str(payload.get("dienThoai") or payload.get("so_dien_thoai") or payload.get("phone") or "").strip()[:20],
        "website": str(payload.get("website") or "").strip(),
        "trangThai": "active",
        "dacDiem": safe_json_text(payload.get("dacDiem") or {"approved_from_dong_gop": obj.maDongGop}),
        "tienNghi": safe_json_text(payload.get("tienNghi") or payload.get("amenities") or []),
        "maNguoiTao": obj.maNguoiDung,
    }

    with transaction.atomic():
        if source_place is not None:
            for field_name, field_value in defaults.items():
                setattr(source_place, field_name, field_value)
            source_place.save()
            place = source_place
        else:
            place = DiaDiem.objects.create(**defaults)

        obj.maDiaDiem = place
        obj.trangThai = "approved"
        obj.ngayXuLy = timezone.now()
        obj.phanHoi = (obj.phanHoi or "").strip() or f"Đã duyệt bởi {approver.username} và đồng bộ vào hệ thống."
        obj.save(update_fields=["maDiaDiem", "trangThai", "ngayXuLy", "phanHoi"])

    sync_place_to_chroma(place)
    logger.info("Approved contribution %s into DIADIEM %s", obj.pk, place.maDiaDiem)
    return place
