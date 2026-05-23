"""Analytics models cho Vi Vu."""
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _


class YeuCauLoTrinh(models.Model):
    """
    Ghi nhận yêu cầu lập lịch trình để phục vụ analytics và tối ưu agent.

    Model này lưu cả yêu cầu preview lẫn yêu cầu tạo kế hoạch đầy đủ.
    Các khóa ngoại đến TinhThanh được để nullable vì người dùng có thể nhập
    địa điểm chưa chuẩn hóa hoàn toàn theo dữ liệu nội bộ.
    """

    class LoaiYeuCau(models.TextChoices):
        PREVIEW = "preview", _("Preview")
        TAO_KE_HOACH = "travel_plan", _("Tạo kế hoạch")
        BUOC_4 = "step4_plan", _("Luồng 4 bước")

    class TrangThaiXuLy(models.TextChoices):
        THANH_CONG = "success", _("Thành công")
        THAT_BAI = "error", _("Thất bại")
        TU_CACHE = "cached", _("Từ cache")

    class Meta:
        db_table = "YEUCAULOTRINH"
        verbose_name = _("Yêu cầu lộ trình")
        verbose_name_plural = _("Yêu cầu lộ trình")
        ordering = ["-ngayTao"]
        indexes = [
            models.Index(fields=["loaiYeuCau", "-ngayTao"]),
            models.Index(fields=["trangThai", "-ngayTao"]),
            models.Index(fields=["maNguoiDung", "-ngayTao"]),
            models.Index(fields=["maTinhThanhDiemDen", "-ngayTao"]),
        ]

    maYeuCau = models.AutoField(primary_key=True, db_column="maYeuCau")
    maNguoiDung = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="yeu_cau_lo_trinhs",
        db_column="maNguoiDung",
        verbose_name=_("người dùng"),
    )
    maTinhThanhDiemDi = models.ForeignKey(
        "places.TinhThanh",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="yeu_cau_diem_di",
        db_column="maTinhThanhDiemDi",
        verbose_name=_("tỉnh thành điểm đi"),
    )
    maTinhThanhDiemDen = models.ForeignKey(
        "places.TinhThanh",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="yeu_cau_diem_den",
        db_column="maTinhThanhDiemDen",
        verbose_name=_("tỉnh thành điểm đến"),
    )
    diemDi = models.CharField(
        _("điểm đi gốc"),
        max_length=255,
        blank=True,
        db_column="diemDi",
        help_text=_("Chuỗi đầu vào gốc do người dùng nhập."),
    )
    diemDen = models.CharField(
        _("điểm đến gốc"),
        max_length=255,
        db_column="diemDen",
        help_text=_("Chuỗi đầu vào gốc do người dùng nhập."),
    )
    ngayKhoiHanhDuKien = models.DateField(
        _("ngày khởi hành dự kiến"),
        null=True,
        blank=True,
        db_column="ngayKhoiHanhDuKien",
    )
    soNgayDi = models.PositiveSmallIntegerField(
        _("số ngày đi"),
        validators=[MinValueValidator(1)],
        db_column="soNgayDi",
    )
    soNguoi = models.PositiveSmallIntegerField(
        _("số người"),
        default=1,
        validators=[MinValueValidator(1)],
        db_column="soNguoi",
    )
    nganSachDuKien = models.FloatField(
        _("ngân sách dự kiến"),
        null=True,
        blank=True,
        db_column="nganSachDuKien",
    )
    loaiYeuCau = models.CharField(
        _("loại yêu cầu"),
        max_length=20,
        choices=LoaiYeuCau.choices,
        db_column="loaiYeuCau",
    )
    trangThai = models.CharField(
        _("trạng thái xử lý"),
        max_length=20,
        choices=TrangThaiXuLy.choices,
        default=TrangThaiXuLy.THANH_CONG,
        db_column="trangThai",
    )
    duLieuPhanHoi = models.JSONField(
        _("dữ liệu phản hồi"),
        default=dict,
        blank=True,
        db_column="duLieuPhanHoi",
        help_text=_("Metadata tóm tắt từ multi-agent để phục vụ phân tích sau này."),
    )
    ngayTao = models.DateTimeField(_("ngày tạo"), auto_now_add=True, db_column="ngayTao")
    lanCapNhatCuoi = models.DateTimeField(
        _("lần cập nhật cuối"),
        auto_now=True,
        db_column="lanCapNhatCuoi",
    )

    def __str__(self) -> str:
        return f"{self.get_loaiYeuCau_display()} - {self.diemDi} -> {self.diemDen}"
