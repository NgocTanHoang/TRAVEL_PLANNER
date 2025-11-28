"""
Itinerary models for Vi Vu.
Maps to LICHTRINH, LICHTRINH_DIADIEM, DONGGOP tables.
"""
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator


class LichTrinh(models.Model):
    """Itinerary model - maps to LICHTRINH table."""
    
    class Meta:
        db_table = 'LICHTRINH'
        verbose_name = _('Lịch trình')
        verbose_name_plural = _('Lịch trình')
        ordering = ['-ngayTao']
        indexes = [
            models.Index(fields=['maNguoiDung', '-ngayTao']),
            models.Index(fields=['ngayBatDau', 'ngayKetThuc']),
            models.Index(fields=['trangThai']),
        ]
    
    TRANG_THAI_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]
    
    maLichTrinh = models.AutoField(primary_key=True, db_column='maLichTrinh')
    maNguoiDung = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lich_trinhs',
        db_column='maNguoiDung',
        verbose_name=_('người dùng')
    )
    maTinhThanh = models.ForeignKey(
        'places.TinhThanh',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='lich_trinhs',
        db_column='maTinhThanh',
        verbose_name=_('tỉnh thành')
    )
    tieuDe = models.CharField(
        _('tiêu đề'),
        max_length=255,
        db_column='tieuDe'
    )
    moTa = models.TextField(_('mô tả'), blank=True, db_column='moTa')
    ngayBatDau = models.DateField(_('ngày bắt đầu'), db_column='ngayBatDau')
    ngayKetThuc = models.DateField(_('ngày kết thúc'), db_column='ngayKetThuc')
    soNgay = models.IntegerField(
        _('số ngày'),
        null=True,
        blank=True,
        db_column='soNgay'
    )
    soNguoi = models.IntegerField(
        _('số người'),
        default=1,
        validators=[MinValueValidator(1)],
        db_column='soNguoi'
    )
    nganSach = models.FloatField(
        _('ngân sách'),
        null=True,
        blank=True,
        db_column='nganSach'
    )
    chiPhiUocTinh = models.FloatField(
        _('chi phí ước tính'),
        null=True,
        blank=True,
        db_column='chiPhiUocTinh'
    )
    trangThai = models.CharField(
        _('trạng thái'),
        max_length=20,
        choices=TRANG_THAI_CHOICES,
        default='draft',
        db_column='trangThai'
    )
    laCongKhai = models.BooleanField(
        _('là công khai'),
        default=False,
        db_column='laCongKhai'
    )
    soLuotXem = models.IntegerField(
        _('số lượt xem'),
        default=0,
        db_column='soLuotXem'
    )
    soLuotThich = models.IntegerField(
        _('số lượt thích'),
        default=0,
        db_column='soLuotThich'
    )
    ngayTao = models.DateTimeField(
        _('ngày tạo'),
        auto_now_add=True,
        db_column='ngayTao'
    )
    lanCapNhatCuoi = models.DateTimeField(
        _('lần cập nhật cuối'),
        auto_now=True,
        db_column='lanCapNhatCuoi'
    )
    chiTiet = models.TextField(
        _('chi tiết (JSON)'),
        blank=True,
        help_text='JSON string for day-by-day details',
        db_column='chiTiet'
    )
    
    # Many-to-many with DiaDiem through LichTrinhDiaDiem
    dia_diems = models.ManyToManyField(
        'places.DiaDiem',
        through='LichTrinhDiaDiem',
        related_name='lich_trinhs'
    )
    
    def __str__(self) -> str:
        return f"{self.tieuDe} ({self.maNguoiDung.tenDangNhap})"
    
    def save(self, *args, **kwargs):
        """Calculate soNgay if not provided."""
        if not self.soNgay and self.ngayBatDau and self.ngayKetThuc:
            delta = self.ngayKetThuc - self.ngayBatDau
            self.soNgay = delta.days + 1
        super().save(*args, **kwargs)


class LichTrinhDiaDiem(models.Model):
    """Itinerary-Place relationship - maps to LICHTRINH_DIADIEM table."""
    
    class Meta:
        db_table = 'LICHTRINH_DIADIEM'
        verbose_name = _('Lịch trình - Địa điểm')
        verbose_name_plural = _('Lịch trình - Địa điểm')
        unique_together = [['maLichTrinh', 'maDiaDiem', 'ngayThamQuan']]
        ordering = ['ngayThamQuan', 'thuTu']
    
    maLichTrinh = models.ForeignKey(
        LichTrinh,
        on_delete=models.CASCADE,
        related_name='lich_trinh_dia_diems',
        db_column='maLichTrinh',
        verbose_name=_('lịch trình')
    )
    maDiaDiem = models.ForeignKey(
        'places.DiaDiem',
        on_delete=models.CASCADE,
        related_name='lich_trinh_dia_diems',
        db_column='maDiaDiem',
        verbose_name=_('địa điểm')
    )
    ngayThamQuan = models.DateField(
        _('ngày tham quan'),
        db_column='ngayThamQuan'
    )
    thoiGianThamQuan = models.CharField(
        _('thời gian tham quan'),
        max_length=50,
        blank=True,
        help_text='e.g., "09:00-12:00"',
        db_column='thoiGianThamQuan'
    )
    thuTu = models.IntegerField(
        _('thứ tự'),
        null=True,
        blank=True,
        db_column='thuTu'
    )
    ghiChu = models.TextField(_('ghi chú'), blank=True, db_column='ghiChu')
    chiPhiUocTinh = models.FloatField(
        _('chi phí ước tính'),
        null=True,
        blank=True,
        db_column='chiPhiUocTinh'
    )
    
    def __str__(self) -> str:
        return f"{self.maLichTrinh.tieuDe} - {self.maDiaDiem.tenDiaDiem} on {self.ngayThamQuan}"


class LichTrinhAI(models.Model):
    """AI-generated itinerary model - maps to LICHTRINHAI table."""

    class Meta:
        db_table = 'LICHTRINHAI'
        verbose_name = _('Lịch trình AI')
        verbose_name_plural = _('Lịch trình AI')
        ordering = ['-ngayTao']
        indexes = [
            models.Index(fields=['maNguoiDung', '-ngayTao']),
            models.Index(fields=['maLichTrinh']),
            models.Index(fields=['maTinhThanh']),
        ]

    TRANG_THAI_CHOICES = [
        ('draft', 'Draft'),
        ('generated', 'Generated'),
        ('final', 'Final'),
        ('archived', 'Archived'),
    ]

    maLichTrinhAI = models.AutoField(primary_key=True, db_column='maLichTrinhAI')
    maLichTrinh = models.ForeignKey(
        LichTrinh,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='ban_ai',
        db_column='maLichTrinh',
        verbose_name=_('lịch trình gốc')
    )
    maTinhThanh = models.ForeignKey(
        'places.TinhThanh',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='lich_trinh_ai',
        db_column='maTinhThanh',
        verbose_name=_('tỉnh thành')
    )
    maNguoiDung = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='lich_trinh_ai',
        db_column='maNguoiDung',
        verbose_name=_('người dùng')
    )
    tieuDe = models.CharField(_('tiêu đề'), max_length=255, db_column='tieuDe')
    moTa = models.TextField(_('mô tả'), blank=True, db_column='moTa')
    ngayBatDau = models.DateField(_('ngày bắt đầu'), null=True, blank=True, db_column='ngayBatDau')
    ngayKetThuc = models.DateField(_('ngày kết thúc'), null=True, blank=True, db_column='ngayKetThuc')
    soNgay = models.IntegerField(_('số ngày'), null=True, blank=True, db_column='soNgay')
    soNguoi = models.IntegerField(_('số người'), null=True, blank=True, db_column='soNguoi')
    nganSach = models.FloatField(_('ngân sách'), null=True, blank=True, db_column='nganSach')
    trangThai = models.CharField(
        _('trạng thái'),
        max_length=20,
        choices=TRANG_THAI_CHOICES,
        default='generated',
        db_column='trangThai'
    )
    chiTiet = models.TextField(
        _('chi tiết (JSON)'),
        blank=True,
        help_text='JSON string describing the generated schedule',
        db_column='chiTiet'
    )
    ngayTao = models.DateTimeField(_('ngày tạo'), auto_now_add=True, db_column='ngayTao')
    lanCapNhatCuoi = models.DateTimeField(_('lần cập nhật cuối'), auto_now=True, db_column='lanCapNhatCuoi')

    dia_diems = models.ManyToManyField(
        'places.DiaDiem',
        through='LichTrinhAIDiaDiem',
        related_name='lich_trinh_ai'
    )

    def __str__(self) -> str:
        return f"AI {self.tieuDe} (#{self.maLichTrinhAI})"

    def save(self, *args, **kwargs):
        if not self.soNgay and self.ngayBatDau and self.ngayKetThuc:
            delta = self.ngayKetThuc - self.ngayBatDau
            self.soNgay = delta.days + 1
        super().save(*args, **kwargs)


class LichTrinhAIDiaDiem(models.Model):
    """AI Itinerary-Place relationship - maps to LICHTRINHAI_DIADIEM table."""

    class Meta:
        db_table = 'LICHTRINHAI_DIADIEM'
        verbose_name = _('Lịch trình AI - Địa điểm')
        verbose_name_plural = _('Lịch trình AI - Địa điểm')
        unique_together = [['maLichTrinhAI', 'maDiaDiem', 'ngayThamQuan']]
        ordering = ['ngayThamQuan', 'thuTu']

    maLichTrinhAI = models.ForeignKey(
        LichTrinhAI,
        on_delete=models.CASCADE,
        related_name='chi_tiets',
        db_column='maLichTrinhAI',
        verbose_name=_('lịch trình AI')
    )
    maDiaDiem = models.ForeignKey(
        'places.DiaDiem',
        on_delete=models.CASCADE,
        related_name='lich_trinh_ai_dia_diems',
        db_column='maDiaDiem',
        verbose_name=_('địa điểm')
    )
    ngayThamQuan = models.DateField(_('ngày tham quan'), null=True, blank=True, db_column='ngayThamQuan')
    thoiGianThamQuan = models.CharField(
        _('thời gian tham quan'),
        max_length=50,
        blank=True,
        help_text='e.g., "09:00-12:00"',
        db_column='thoiGianThamQuan'
    )
    thuTu = models.IntegerField(_('thứ tự'), null=True, blank=True, db_column='thuTu')
    ghiChu = models.TextField(_('ghi chú'), blank=True, db_column='ghiChu')
    chiPhiUocTinh = models.FloatField(_('chi phí ước tính'), null=True, blank=True, db_column='chiPhiUocTinh')

    def __str__(self) -> str:
        return f"AI#{self.maLichTrinhAI_id} - {self.maDiaDiem.tenDiaDiem}"

class DongGop(models.Model):
    """Contribution/Report model - maps to DONGGOP table."""
    
    class Meta:
        db_table = 'DONGGOP'
        verbose_name = _('Đóng góp')
        verbose_name_plural = _('Đóng góp')
        ordering = ['-ngayTao']
        indexes = [
            models.Index(fields=['maNguoiDung', '-ngayTao']),
            models.Index(fields=['trangThai']),
        ]
    
    LOAI_DONG_GOP_CHOICES = [
        ('them_dia_diem', 'Thêm địa điểm'),
        ('sua_thong_tin', 'Sửa thông tin'),
        ('bao_cao_loi', 'Báo cáo lỗi'),
        ('khac', 'Khác'),
    ]
    
    TRANG_THAI_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    maDongGop = models.AutoField(primary_key=True, db_column='maDongGop')
    maNguoiDung = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='dong_gops',
        db_column='maNguoiDung',
        verbose_name=_('người dùng')
    )
    maDiaDiem = models.ForeignKey(
        'places.DiaDiem',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='dong_gops',
        db_column='maDiaDiem',
        verbose_name=_('địa điểm')
    )
    loaiDongGop = models.CharField(
        _('loại đóng góp'),
        max_length=50,
        choices=LOAI_DONG_GOP_CHOICES,
        db_column='loaiDongGop'
    )
    noiDung = models.TextField(_('nội dung'), db_column='noiDung')
    trangThai = models.CharField(
        _('trạng thái'),
        max_length=20,
        choices=TRANG_THAI_CHOICES,
        default='pending',
        db_column='trangThai'
    )
    phanHoi = models.TextField(_('phản hồi'), blank=True, db_column='phanHoi')
    ngayTao = models.DateTimeField(_('ngày tạo'), auto_now_add=True, db_column='ngayTao')
    ngayXuLy = models.DateTimeField(
        _('ngày xử lý'),
        null=True,
        blank=True,
        db_column='ngayXuLy'
    )
    
    def __str__(self) -> str:
        return f"{self.loaiDongGop} by {self.maNguoiDung.tenDangNhap}"

