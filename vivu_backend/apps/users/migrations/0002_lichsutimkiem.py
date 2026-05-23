import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0001_initial"),
        ("places", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="LichSuTimKiem",
            fields=[
                ("maTimKiem", models.AutoField(db_column="maTimKiem", primary_key=True, serialize=False)),
                ("tuKhoa", models.CharField(db_column="tuKhoa", max_length=255, verbose_name="từ khóa")),
                ("ngayTim", models.DateTimeField(auto_now_add=True, db_column="ngayTim", verbose_name="ngày tìm")),
                ("soKetQua", models.IntegerField(db_column="soKetQua", default=0, verbose_name="số kết quả")),
                (
                    "maDiaDiem",
                    models.ForeignKey(
                        blank=True,
                        db_column="maDiaDiem",
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="tim_kiems",
                        to="places.diadiem",
                        verbose_name="địa điểm",
                    ),
                ),
                (
                    "maNguoiDung",
                    models.ForeignKey(
                        db_column="maNguoiDung",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="lich_su_tim_kiems",
                        to="users.nguoidung",
                        verbose_name="người dùng",
                    ),
                ),
            ],
            options={
                "verbose_name": "Lịch sử tìm kiếm",
                "verbose_name_plural": "Lịch sử tìm kiếm",
                "db_table": "LICHSU_TIMKIEM",
                "ordering": ["-ngayTim"],
            },
        ),
        migrations.AddIndex(
            model_name="lichsutimkiem",
            index=models.Index(fields=["maNguoiDung", "-ngayTim"], name="LICHSUTIMK_maNguo_f5a0f9_idx"),
        ),
    ]
