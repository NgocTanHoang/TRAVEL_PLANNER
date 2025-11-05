"""Admin configuration for users app."""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import NguoiDung


@admin.register(NguoiDung)
class NguoiDungAdmin(UserAdmin):
    """Admin for NguoiDung model."""
    
    list_display = ['username', 'email', 'hoTen', 'vaiTro', 'trangThai', 'date_joined']
    list_filter = ['vaiTro', 'trangThai', 'is_staff', 'is_active']
    search_fields = ['username', 'email', 'hoTen', 'soDienThoai']
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Thông tin cá nhân', {'fields': ('hoTen', 'email', 'soDienThoai', 'ngaySinh', 'gioiTinh', 'diaChi', 'anhDaiDien')}),
        ('Phân quyền', {'fields': ('vaiTro', 'trangThai', 'is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
        ('Thời gian', {'fields': ('last_login', 'date_joined')}),
    )

