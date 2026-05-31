"""Admin configuration for itineraries app."""
from __future__ import annotations

import json
import logging
import os
from typing import Any

from django.contrib import admin
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from apps.places.models import DiaDiem, TinhThanh

from .models import DongGop, LichTrinh, LichTrinhDiaDiem

logger = logging.getLogger(__name__)


def _is_admin_role(user) -> bool:
    if not user or not user.is_authenticated:
        return False
    if getattr(user, "is_superuser", False):
        return True
    role = str(getattr(user, "vaiTro", "") or "").strip().lower()
    return role == "admin"


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_json_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if value in (None, ""):
        return ""
    return json.dumps(value, ensure_ascii=False)


def _build_place_document(place: DiaDiem) -> str:
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


def _build_place_metadata(place: DiaDiem) -> dict[str, Any]:
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


def _sync_place_to_chroma(place: DiaDiem) -> None:
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
        documents=[_build_place_document(place)],
        metadatas=[_build_place_metadata(place)],
    )


def _resolve_tinh_thanh(payload: dict[str, Any], fallback_place: DiaDiem | None = None) -> TinhThanh:
    if fallback_place is not None:
        return fallback_place.maTinhThanh

    ma_tinh_thanh = payload.get("maTinhThanh")
    if ma_tinh_thanh:
        tinh_thanh = TinhThanh.objects.filter(pk=ma_tinh_thanh).first()
        if tinh_thanh:
            return tinh_thanh

    ten_tinh_thanh = str(payload.get("tenTinhThanh") or payload.get("province") or "").strip()
    if ten_tinh_thanh:
        tinh_thanh = TinhThanh.objects.filter(tenTinhThanh__iexact=ten_tinh_thanh).first()
        if tinh_thanh:
            return tinh_thanh

    raise ValidationError("Không xác định được tỉnh thành hợp lệ để duyệt đóng góp.")


def _approve_contribution(obj: DongGop, *, approver) -> DiaDiem | None:
    payload = obj.duLieuBoSung if isinstance(obj.duLieuBoSung, dict) else {}
    if obj.loaiDongGop not in {"THEM_MOI_POI", "SUA_DOI_POI"}:
        return obj.maDiaDiem

    source_place = obj.maDiaDiem if obj.loaiDongGop == "SUA_DOI_POI" else None
    tinh_thanh = _resolve_tinh_thanh(payload, fallback_place=source_place)

    defaults = {
        "tenDiaDiem": str(payload.get("tenDiaDiem") or payload.get("name") or obj.noiDung[:255]).strip()[:255],
        "moTa": str(payload.get("moTa") or payload.get("description") or obj.noiDung or "").strip(),
        "diaChi": str(payload.get("diaChi") or payload.get("address") or "").strip()[:500],
        "maTinhThanh": tinh_thanh,
        "loaiDiaDiem": str(payload.get("loaiDiaDiem") or payload.get("category") or "khac").strip() or "khac",
        "viDo": _safe_float(payload.get("viDo") or payload.get("latitude"), default=0.0),
        "kinhDo": _safe_float(payload.get("kinhDo") or payload.get("longitude"), default=0.0),
        "giaVe": _safe_float(payload.get("giaVe") or payload.get("price"), default=0.0),
        "gioMoCua": str(payload.get("gioMoCua") or payload.get("opening_hours") or "").strip()[:50],
        "gioDongCua": str(payload.get("gioDongCua") or payload.get("closing_hours") or "").strip()[:50],
        "dienThoai": str(payload.get("dienThoai") or payload.get("phone") or "").strip()[:20],
        "website": str(payload.get("website") or "").strip(),
        "trangThai": "active",
        "dacDiem": _safe_json_text(payload.get("dacDiem") or {"approved_from_dong_gop": obj.maDongGop}),
        "tienNghi": _safe_json_text(payload.get("tienNghi") or payload.get("amenities") or []),
        "maNguoiTao": obj.maNguoiDung,
    }

    if source_place is not None:
        for field_name, field_value in defaults.items():
            setattr(source_place, field_name, field_value)
        source_place.save()
        place = source_place
    else:
        place = DiaDiem.objects.create(**defaults)

    obj.maDiaDiem = place
    obj.ngayXuLy = timezone.now()
    obj.phanHoi = (obj.phanHoi or "").strip() or f"Đã duyệt bởi {approver.username} và đồng bộ vào hệ thống."
    obj.save(update_fields=["maDiaDiem", "ngayXuLy", "phanHoi", "trangThai"])
    _sync_place_to_chroma(place)
    return place


class LichTrinhDiaDiemInline(admin.TabularInline):
    """Inline for LichTrinhDiaDiem."""

    model = LichTrinhDiaDiem
    extra = 1


@admin.register(LichTrinh)
class LichTrinhAdmin(admin.ModelAdmin):
    """Admin for LichTrinh."""

    list_display = ["tieuDe", "maNguoiDung", "ngayBatDau", "ngayKetThuc", "soNgay", "trangThai", "laCongKhai", "is_ai_generated"]
    list_filter = ["trangThai", "laCongKhai", "is_ai_generated"]
    search_fields = ["tieuDe", "moTa", "maNguoiDung__username"]
    readonly_fields = ["soNgay", "soLuotXem", "soLuotThich"]
    inlines = [LichTrinhDiaDiemInline]


@admin.register(DongGop)
class DongGopAdmin(admin.ModelAdmin):
    """Admin for DongGop."""

    list_display = ["maNguoiDung", "loaiDongGop", "maDiaDiem", "trangThai", "ngayTao"]
    list_filter = ["loaiDongGop", "trangThai"]
    search_fields = ["noiDung", "maNguoiDung__username"]
    readonly_fields = ["duLieuBoSung"]

    def save_model(self, request, obj, form, change):
        previous_status = None
        if change and obj.pk:
            previous_status = DongGop.objects.filter(pk=obj.pk).values_list("trangThai", flat=True).first()

        if obj.trangThai == "approved" and previous_status != "approved" and not _is_admin_role(request.user):
            raise PermissionDenied("Chỉ tài khoản quản trị mới được phép duyệt đóng góp.")

        with transaction.atomic():
            super().save_model(request, obj, form, change)
            if obj.trangThai == "approved" and previous_status != "approved":
                try:
                    _approve_contribution(obj, approver=request.user)
                except Exception as exc:
                    logger.error("Khong the duyet dong gop %s: %s", obj.pk, exc, exc_info=True)
                    raise
