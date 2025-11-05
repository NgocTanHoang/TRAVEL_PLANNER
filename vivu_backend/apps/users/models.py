"""
User models for Vi Vu.
Maps to NGUOIDUNG table in Vietnamese schema.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.places.models import DiaDiem


class NguoiDung(AbstractUser):
    """
    Custom user model mapping to NGUOIDUNG table.
    Extends Django's AbstractUser with Vietnamese field names.
    Uses Django's built-in password field but renames username to tenDangNhap.
    """
    
    class Meta:
        db_table = 'NGUOIDUNG'
        verbose_name = _('Người dùng')
        verbose_name_plural = _('Người dùng')
        ordering = ['-date_joined']
    
    # Override primary key to match Vietnamese schema
    id = models.AutoField(primary_key=True, db_column='maNguoiDung')
    
    # Override username field with Vietnamese name
    username = models.CharField(
        _('tên đăng nhập'),
        max_length=150,
        unique=True,
        db_column='tenDangNhap',
        help_text=_('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.')
    )
    
    email = models.EmailField(
        _('email'),
        unique=True,
        db_column='email'
    )
    
    # Additional Vietnamese fields
    hoTen = models.CharField(
        _('họ tên'),
        max_length=255,
        blank=True,
        db_column='hoTen'
    )
    soDienThoai = models.CharField(
        _('số điện thoại'),
        max_length=20,
        blank=True,
        db_column='soDienThoai'
    )
    anhDaiDien = models.CharField(
        _('ảnh đại diện'),
        max_length=500,
        blank=True,
        null=True,
        db_column='anhDaiDien'
    )
    ngaySinh = models.DateField(
        _('ngày sinh'),
        blank=True,
        null=True,
        db_column='ngaySinh'
    )
    
    GIOI_TINH_CHOICES = [
        ('Nam', 'Nam'),
        ('Nữ', 'Nữ'),
        ('Khác', 'Khác'),
    ]
    gioiTinh = models.CharField(
        _('giới tính'),
        max_length=10,
        choices=GIOI_TINH_CHOICES,
        blank=True,
        db_column='gioiTinh'
    )
    diaChi = models.TextField(
        _('địa chỉ'),
        blank=True,
        db_column='diaChi'
    )
    
    VAI_TRO_CHOICES = [
        ('user', 'User'),
        ('admin', 'Admin'),
        ('contributor', 'Contributor'),
    ]
    vaiTro = models.CharField(
        _('vai trò'),
        max_length=20,
        choices=VAI_TRO_CHOICES,
        default='user',
        db_column='vaiTro'
    )
    
    TRANG_THAI_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('banned', 'Banned'),
    ]
    trangThai = models.CharField(
        _('trạng thái'),
        max_length=20,
        choices=TRANG_THAI_CHOICES,
        default='active',
        db_column='trangThai'
    )
    
    USERNAME_FIELD = 'username'  # Maps to tenDangNhap column
    REQUIRED_FIELDS = ['email']
    
    @property
    def maNguoiDung(self):
        """Alias for id to match Vietnamese naming."""
        return self.id
    
    @property
    def tenDangNhap(self):
        """Alias for username to match Vietnamese naming."""
        return self.username
    
    def __str__(self) -> str:
        return f"{self.username} ({self.hoTen or 'No name'})"


class LichSuTimKiem(models.Model):
    """Search history model for users."""
    
    class Meta:
        db_table = 'LICHSU_TIMKIEM'
        verbose_name = _('Lịch sử tìm kiếm')
        verbose_name_plural = _('Lịch sử tìm kiếm')
        ordering = ['-ngayTim']
        indexes = [
            models.Index(fields=['maNguoiDung', '-ngayTim']),
        ]
    
    maTimKiem = models.AutoField(primary_key=True, db_column='maTimKiem')
    maNguoiDung = models.ForeignKey(
        NguoiDung,
        on_delete=models.CASCADE,
        related_name='lich_su_tim_kiems',
        db_column='maNguoiDung',
        verbose_name=_('người dùng')
    )
    tuKhoa = models.CharField(
        _('từ khóa'),
        max_length=255,
        db_column='tuKhoa'
    )
    maDiaDiem = models.ForeignKey(
        DiaDiem,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='tim_kiems',
        db_column='maDiaDiem',
        verbose_name=_('địa điểm')
    )
    ngayTim = models.DateTimeField(_('ngày tìm'), auto_now_add=True, db_column='ngayTim')
    soKetQua = models.IntegerField(
        _('số kết quả'),
        default=0,
        db_column='soKetQua'
    )
    
    def __str__(self) -> str:
        return f"Search: {self.tuKhoa} by {self.maNguoiDung.username}"

