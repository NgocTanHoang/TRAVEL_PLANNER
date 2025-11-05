"""Admin configuration for places app."""
from django.contrib import admin
from .models import TinhThanh, DiaDiem, HinhAnhDiaDiem, DanhGia, DiaDiemYeuThich


@admin.register(TinhThanh)
class TinhThanhAdmin(admin.ModelAdmin):
    """Admin for TinhThanh."""
    list_display = ['tenTinhThanh', 'moTa', 'created_at']
    search_fields = ['tenTinhThanh']


@admin.register(DiaDiem)
class DiaDiemAdmin(admin.ModelAdmin):
    """Admin for DiaDiem."""
    list_display = ['tenDiaDiem', 'maTinhThanh', 'loaiDiaDiem', 'danhGiaTrungBinh', 'soLuotDanhGia', 'trangThai']
    list_filter = ['loaiDiaDiem', 'trangThai', 'maTinhThanh']
    search_fields = ['tenDiaDiem', 'moTa', 'diaChi']
    readonly_fields = ['danhGiaTrungBinh', 'soLuotDanhGia', 'soLuotXem']


@admin.register(HinhAnhDiaDiem)
class HinhAnhDiaDiemAdmin(admin.ModelAdmin):
    """Admin for HinhAnhDiaDiem."""
    list_display = ['maDiaDiem', 'urlHinhAnh', 'laChinh', 'ngayTao']
    list_filter = ['laChinh']


@admin.register(DanhGia)
class DanhGiaAdmin(admin.ModelAdmin):
    """Admin for DanhGia."""
    list_display = ['maDiaDiem', 'maNguoiDung', 'diemDanhGia', 'trangThai', 'ngayTao']
    list_filter = ['diemDanhGia', 'trangThai']
    search_fields = ['noiDung', 'tieuDe']


@admin.register(DiaDiemYeuThich)
class DiaDiemYeuThichAdmin(admin.ModelAdmin):
    """Admin for DiaDiemYeuThich."""
    list_display = ['maNguoiDung', 'maDiaDiem', 'ngayThem']
    search_fields = ['maNguoiDung__username', 'maDiaDiem__tenDiaDiem']

