"""Admin configuration for itineraries app."""
from django.contrib import admin
from .models import LichTrinh, LichTrinhDiaDiem, DongGop


class LichTrinhDiaDiemInline(admin.TabularInline):
    """Inline for LichTrinhDiaDiem."""
    model = LichTrinhDiaDiem
    extra = 1


@admin.register(LichTrinh)
class LichTrinhAdmin(admin.ModelAdmin):
    """Admin for LichTrinh."""
    list_display = ['tieuDe', 'maNguoiDung', 'ngayBatDau', 'ngayKetThuc', 'soNgay', 'trangThai', 'laCongKhai']
    list_filter = ['trangThai', 'laCongKhai']
    search_fields = ['tieuDe', 'moTa', 'maNguoiDung__username']
    readonly_fields = ['soNgay', 'soLuotXem', 'soLuotThich']
    inlines = [LichTrinhDiaDiemInline]


@admin.register(DongGop)
class DongGopAdmin(admin.ModelAdmin):
    """Admin for DongGop."""
    list_display = ['maNguoiDung', 'loaiDongGop', 'maDiaDiem', 'trangThai', 'ngayTao']
    list_filter = ['loaiDongGop', 'trangThai']
    search_fields = ['noiDung', 'maNguoiDung__username']

