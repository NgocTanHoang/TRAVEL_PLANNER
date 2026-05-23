from django.conf import settings
from django.db import migrations, models
import django.core.validators
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("users", "0001_initial"),
        ("places", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="YeuCauLoTrinh",
            fields=[
                ("maYeuCau", models.AutoField(db_column="maYeuCau", primary_key=True, serialize=False)),
                ("diemDi", models.CharField(blank=True, db_column="diemDi", help_text="Chuỗi đầu vào gốc do người dùng nhập.", max_length=255, verbose_name="điểm đi gốc")),
                ("diemDen", models.CharField(db_column="diemDen", help_text="Chuỗi đầu vào gốc do người dùng nhập.", max_length=255, verbose_name="điểm đến gốc")),
                ("ngayKhoiHanhDuKien", models.DateField(blank=True, db_column="ngayKhoiHanhDuKien", null=True, verbose_name="ngày khởi hành dự kiến")),
                ("soNgayDi", models.PositiveSmallIntegerField(db_column="soNgayDi", validators=[django.core.validators.MinValueValidator(1)], verbose_name="số ngày đi")),
                ("soNguoi", models.PositiveSmallIntegerField(db_column="soNguoi", default=1, validators=[django.core.validators.MinValueValidator(1)], verbose_name="số người")),
                ("nganSachDuKien", models.FloatField(blank=True, db_column="nganSachDuKien", null=True, verbose_name="ngân sách dự kiến")),
                ("loaiYeuCau", models.CharField(choices=[("preview", "Preview"), ("travel_plan", "Tạo kế hoạch"), ("step4_plan", "Luồng 4 bước")], db_column="loaiYeuCau", max_length=20, verbose_name="loại yêu cầu")),
                ("trangThai", models.CharField(choices=[("success", "Thành công"), ("error", "Thất bại"), ("cached", "Từ cache")], db_column="trangThai", default="success", max_length=20, verbose_name="trạng thái xử lý")),
                ("duLieuPhanHoi", models.JSONField(blank=True, db_column="duLieuPhanHoi", default=dict, help_text="Metadata tóm tắt từ multi-agent để phục vụ phân tích sau này.", verbose_name="dữ liệu phản hồi")),
                ("ngayTao", models.DateTimeField(auto_now_add=True, db_column="ngayTao", verbose_name="ngày tạo")),
                ("lanCapNhatCuoi", models.DateTimeField(auto_now=True, db_column="lanCapNhatCuoi", verbose_name="lần cập nhật cuối")),
                ("maNguoiDung", models.ForeignKey(blank=True, db_column="maNguoiDung", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="yeu_cau_lo_trinhs", to=settings.AUTH_USER_MODEL, verbose_name="người dùng")),
                ("maTinhThanhDiemDen", models.ForeignKey(blank=True, db_column="maTinhThanhDiemDen", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="yeu_cau_diem_den", to="places.tinhthanh", verbose_name="tỉnh thành điểm đến")),
                ("maTinhThanhDiemDi", models.ForeignKey(blank=True, db_column="maTinhThanhDiemDi", null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="yeu_cau_diem_di", to="places.tinhthanh", verbose_name="tỉnh thành điểm đi")),
            ],
            options={
                "verbose_name": "Yêu cầu lộ trình",
                "verbose_name_plural": "Yêu cầu lộ trình",
                "db_table": "YEUCAULOTRINH",
                "ordering": ["-ngayTao"],
            },
        ),
        migrations.AddIndex(
            model_name="yeucaulotrinh",
            index=models.Index(fields=["loaiYeuCau", "-ngayTao"], name="YEUCAULOTR_loaiYe_33eef0_idx"),
        ),
        migrations.AddIndex(
            model_name="yeucaulotrinh",
            index=models.Index(fields=["trangThai", "-ngayTao"], name="YEUCAULOTR_trangT_7a530e_idx"),
        ),
        migrations.AddIndex(
            model_name="yeucaulotrinh",
            index=models.Index(fields=["maNguoiDung", "-ngayTao"], name="YEUCAULOTR_maNguo_c1b4b9_idx"),
        ),
        migrations.AddIndex(
            model_name="yeucaulotrinh",
            index=models.Index(fields=["maTinhThanhDiemDen", "-ngayTao"], name="YEUCAULOTR_maTinh_b9f541_idx"),
        ),
    ]
