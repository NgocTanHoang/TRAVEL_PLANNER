"""
Place models for Vi Vu.
Maps to TINHTHANH, DIADIEM, HINHANHDIADIEM, DANHGIA, DIADIEM_YEUTHICH tables.
"""
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator


class TinhThanh(models.Model):
    """Province/City model - maps to TINHTHANH table."""
    
    class Meta:
        db_table = 'TINHTHANH'
        verbose_name = _('Tỉnh thành')
        verbose_name_plural = _('Tỉnh thành')
        ordering = ['tenTinhThanh']
    
    maTinhThanh = models.AutoField(primary_key=True, db_column='maTinhThanh')
    tenTinhThanh = models.CharField(
        _('tên tỉnh thành'),
        max_length=255,
        unique=True,
        db_index=True,
        db_column='tenTinhThanh'
    )
    moTa = models.TextField(_('mô tả'), blank=True, db_column='moTa')
    anhDaiDien = models.CharField(
        _('ảnh đại diện'),
        max_length=500,
        blank=True,
        db_column='anhDaiDien'
    )
    viDo = models.FloatField(_('vĩ độ'), null=True, blank=True, db_column='viDo')
    kinhDo = models.FloatField(_('kinh độ'), null=True, blank=True, db_column='kinhDo')
    created_at = models.DateTimeField(_('ngày tạo'), auto_now_add=True)
    updated_at = models.DateTimeField(_('cập nhật'), auto_now=True)
    
    def __str__(self) -> str:
        return self.tenTinhThanh


class DiaDiem(models.Model):
    """Place model - maps to DIADIEM table."""
    
    class Meta:
        db_table = 'DIADIEM'
        verbose_name = _('Địa điểm')
        verbose_name_plural = _('Địa điểm')
        ordering = ['-danhGiaTrungBinh', '-soLuotDanhGia']
        indexes = [
            models.Index(fields=['maTinhThanh', 'loaiDiaDiem']),
            models.Index(fields=['-danhGiaTrungBinh']),
            models.Index(fields=['trangThai']),
        ]
    
    LOAI_DIA_DIEM_CHOICES = [
        ('dia_danh', 'Địa danh'),
        ('nha_hang', 'Nhà hàng'),
        ('khach_san', 'Khách sạn'),
        ('giai_tri', 'Giải trí'),
        ('mua_sam', 'Mua sắm'),
        ('khac', 'Khác'),
    ]
    
    TRANG_THAI_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('pending', 'Pending'),
    ]
    
    maDiaDiem = models.AutoField(primary_key=True, db_column='maDiaDiem')
    tenDiaDiem = models.CharField(
        _('tên địa điểm'),
        max_length=255,
        db_index=True,
        db_column='tenDiaDiem'
    )
    moTa = models.TextField(_('mô tả'), blank=True, db_column='moTa')
    diaChi = models.CharField(
        _('địa chỉ'),
        max_length=500,
        blank=True,
        db_column='diaChi'
    )
    maTinhThanh = models.ForeignKey(
        TinhThanh,
        on_delete=models.CASCADE,
        related_name='dia_diems',
        db_column='maTinhThanh',
        verbose_name=_('tỉnh thành')
    )
    loaiDiaDiem = models.CharField(
        _('loại địa điểm'),
        max_length=50,
        choices=LOAI_DIA_DIEM_CHOICES,
        db_column='loaiDiaDiem'
    )
    viDo = models.FloatField(_('vĩ độ'), null=True, blank=True, db_column='viDo')
    kinhDo = models.FloatField(_('kinh độ'), null=True, blank=True, db_column='kinhDo')
    giaVe = models.FloatField(_('giá vé'), null=True, blank=True, db_column='giaVe')
    gioMoCua = models.CharField(
        _('giờ mở cửa'),
        max_length=50,
        blank=True,
        db_column='gioMoCua'
    )
    gioDongCua = models.CharField(
        _('giờ đóng cửa'),
        max_length=50,
        blank=True,
        db_column='gioDongCua'
    )
    dienThoai = models.CharField(
        _('điện thoại'),
        max_length=20,
        blank=True,
        db_column='dienThoai'
    )
    website = models.URLField(_('website'), blank=True, db_column='website')
    
    danhGiaTrungBinh = models.FloatField(
        _('đánh giá trung bình'),
        default=0.0,
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)],
        db_column='danhGiaTrungBinh'
    )
    soLuotDanhGia = models.IntegerField(
        _('số lượt đánh giá'),
        default=0,
        db_column='soLuotDanhGia'
    )
    soLuotXem = models.IntegerField(
        _('số lượt xem'),
        default=0,
        db_column='soLuotXem'
    )
    
    maNguoiTao = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='dia_diems_created',
        db_column='maNguoiTao',
        verbose_name=_('người tạo')
    )
    
    ngayTao = models.DateTimeField(_('ngày tạo'), auto_now_add=True, db_column='ngayTao')
    lanCapNhatCuoi = models.DateTimeField(
        _('lần cập nhật cuối'),
        auto_now=True,
        db_column='lanCapNhatCuoi'
    )
    
    trangThai = models.CharField(
        _('trạng thái'),
        max_length=20,
        choices=TRANG_THAI_CHOICES,
        default='active',
        db_column='trangThai'
    )
    
    dacDiem = models.TextField(
        _('đặc điểm (JSON)'),
        blank=True,
        help_text='JSON string for special features',
        db_column='dacDiem'
    )
    tienNghi = models.TextField(
        _('tiện nghi (JSON)'),
        blank=True,
        help_text='JSON string for amenities',
        db_column='tienNghi'
    )
    
    def __str__(self) -> str:
        return f"{self.tenDiaDiem} - {self.maTinhThanh.tenTinhThanh}"


class HinhAnhDiaDiem(models.Model):
    """Place Image model - maps to HINHANHDIADIEM table."""
    
    class Meta:
        db_table = 'HINHANHDIADIEM'
        verbose_name = _('Hình ảnh địa điểm')
        verbose_name_plural = _('Hình ảnh địa điểm')
        ordering = ['-laChinh', '-ngayTao']
        indexes = [
            models.Index(fields=['maDiaDiem']),
        ]
    
    maHinhAnh = models.AutoField(primary_key=True, db_column='maHinhAnh')
    maDiaDiem = models.ForeignKey(
        DiaDiem,
        on_delete=models.CASCADE,
        related_name='hinh_anhs',
        db_column='maDiaDiem',
        verbose_name=_('địa điểm')
    )
    urlHinhAnh = models.CharField(
        _('URL hình ảnh'),
        max_length=500,
        db_column='urlHinhAnh'
    )
    moTa = models.CharField(
        _('mô tả'),
        max_length=500,
        blank=True,
        db_column='moTa'
    )
    laChinh = models.BooleanField(
        _('là chính'),
        default=False,
        db_column='laChinh'
    )
    ngayTao = models.DateTimeField(_('ngày tạo'), auto_now_add=True, db_column='ngayTao')
    
    def __str__(self) -> str:
        return f"Image for {self.maDiaDiem.tenDiaDiem}"


class DanhGia(models.Model):
    """Review model - maps to DANHGIA table."""
    
    class Meta:
        db_table = 'DANHGIA'
        verbose_name = _('Đánh giá')
        verbose_name_plural = _('Đánh giá')
        ordering = ['-ngayTao']
        unique_together = [['maDiaDiem', 'maNguoiDung']]
        indexes = [
            models.Index(fields=['maDiaDiem', '-ngayTao']),
            models.Index(fields=['maNguoiDung']),
        ]
    
    TRANG_THAI_CHOICES = [
        ('active', 'Active'),
        ('hidden', 'Hidden'),
        ('flagged', 'Flagged'),
    ]
    
    maDanhGia = models.AutoField(primary_key=True, db_column='maDanhGia')
    maDiaDiem = models.ForeignKey(
        DiaDiem,
        on_delete=models.CASCADE,
        related_name='danh_gias',
        db_column='maDiaDiem',
        verbose_name=_('địa điểm')
    )
    maNguoiDung = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='danh_gias',
        db_column='maNguoiDung',
        verbose_name=_('người dùng')
    )
    diemDanhGia = models.IntegerField(
        _('điểm đánh giá'),
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        db_column='diemDanhGia'
    )
    tieuDe = models.CharField(
        _('tiêu đề'),
        max_length=255,
        blank=True,
        db_column='tieuDe'
    )
    noiDung = models.TextField(_('nội dung'), db_column='noiDung')
    ngayTao = models.DateTimeField(_('ngày tạo'), auto_now_add=True, db_column='ngayTao')
    lanCapNhatCuoi = models.DateTimeField(
        _('lần cập nhật cuối'),
        auto_now=True,
        db_column='lanCapNhatCuoi'
    )
    soLuotThich = models.IntegerField(
        _('số lượt thích'),
        default=0,
        db_column='soLuotThich'
    )
    trangThai = models.CharField(
        _('trạng thái'),
        max_length=20,
        choices=TRANG_THAI_CHOICES,
        default='active',
        db_column='trangThai'
    )
    
    def __str__(self) -> str:
        return f"Review by {self.maNguoiDung.tenDangNhap} for {self.maDiaDiem.tenDiaDiem}"


class DiaDiemYeuThich(models.Model):
    """Favorite Place model - maps to DIADIEM_YEUTHICH table."""
    
    class Meta:
        db_table = 'DIADIEM_YEUTHICH'
        verbose_name = _('Địa điểm yêu thích')
        verbose_name_plural = _('Địa điểm yêu thích')
        unique_together = [['maNguoiDung', 'maDiaDiem']]
        ordering = ['-ngayThem']
    
    maNguoiDung = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='dia_diems_yeu_thich',
        db_column='maNguoiDung',
        verbose_name=_('người dùng')
    )
    maDiaDiem = models.ForeignKey(
        DiaDiem,
        on_delete=models.CASCADE,
        related_name='nguoi_dungs_yeu_thich',
        db_column='maDiaDiem',
        verbose_name=_('địa điểm')
    )
    ngayThem = models.DateTimeField(_('ngày thêm'), auto_now_add=True, db_column='ngayThem')
    ghiChu = models.TextField(_('ghi chú'), blank=True, db_column='ghiChu')
    
    def __str__(self) -> str:
        return f"{self.maNguoiDung.tenDangNhap} likes {self.maDiaDiem.tenDiaDiem}"

