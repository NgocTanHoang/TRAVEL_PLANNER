"""Admin configuration for itineraries app."""
from __future__ import annotations

import logging

from django.contrib import admin
from django.core.exceptions import PermissionDenied
from django.db import transaction

from apps.places.contribution_service import approve_contribution, is_admin_role

from .models import DongGop, LichTrinh, LichTrinhDiaDiem

logger = logging.getLogger(__name__)


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

        if obj.trangThai == "approved" and previous_status != "approved" and not is_admin_role(request.user):
            raise PermissionDenied("Chỉ tài khoản quản trị mới được phép duyệt đóng góp.")

        with transaction.atomic():
            super().save_model(request, obj, form, change)
            if obj.trangThai == "approved" and previous_status != "approved":
                try:
                    approve_contribution(obj, approver=request.user)
                except Exception as exc:
                    logger.error("Khong the duyet dong gop %s: %s", obj.pk, exc, exc_info=True)
                    raise
