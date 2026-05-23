"""Admin configuration cho analytics."""
from django.contrib import admin

from .models import YeuCauLoTrinh


@admin.register(YeuCauLoTrinh)
class YeuCauLoTrinhAdmin(admin.ModelAdmin):
    list_display = (
        "maYeuCau",
        "loaiYeuCau",
        "trangThai",
        "diemDi",
        "diemDen",
        "soNgayDi",
        "soNguoi",
        "nganSachDuKien",
        "ngayTao",
    )
    list_filter = ("loaiYeuCau", "trangThai", "ngayTao")
    search_fields = ("diemDi", "diemDen", "maNguoiDung__username")
    autocomplete_fields = ("maNguoiDung", "maTinhThanhDiemDi", "maTinhThanhDiemDen")
    readonly_fields = ("ngayTao", "lanCapNhatCuoi")
