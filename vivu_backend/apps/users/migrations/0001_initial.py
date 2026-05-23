import django.contrib.auth.models
import django.contrib.auth.validators
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.CreateModel(
            name="NguoiDung",
            fields=[
                ("password", models.CharField(max_length=128, verbose_name="password")),
                ("last_login", models.DateTimeField(blank=True, null=True, verbose_name="last login")),
                ("is_superuser", models.BooleanField(default=False, help_text="Designates that this user has all permissions without explicitly assigning them.", verbose_name="superuser status")),
                ("first_name", models.CharField(blank=True, max_length=150, verbose_name="first name")),
                ("last_name", models.CharField(blank=True, max_length=150, verbose_name="last name")),
                ("is_staff", models.BooleanField(default=False, help_text="Designates whether the user can log into this admin site.", verbose_name="staff status")),
                ("is_active", models.BooleanField(default=True, help_text="Designates whether this user should be treated as active. Unselect this instead of deleting accounts.", verbose_name="active")),
                ("date_joined", models.DateTimeField(default=django.utils.timezone.now, verbose_name="date joined")),
                ("id", models.AutoField(db_column="maNguoiDung", primary_key=True, serialize=False)),
                (
                    "username",
                    models.CharField(
                        db_column="tenDangNhap",
                        help_text="Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.",
                        max_length=150,
                        unique=True,
                        validators=[django.contrib.auth.validators.UnicodeUsernameValidator()],
                        verbose_name="tên đăng nhập",
                    ),
                ),
                ("email", models.EmailField(db_column="email", max_length=254, unique=True, verbose_name="email")),
                ("hoTen", models.CharField(blank=True, db_column="hoTen", max_length=255, verbose_name="họ tên")),
                ("soDienThoai", models.CharField(blank=True, db_column="soDienThoai", max_length=20, verbose_name="số điện thoại")),
                ("anhDaiDien", models.CharField(blank=True, db_column="anhDaiDien", max_length=500, null=True, verbose_name="ảnh đại diện")),
                ("ngaySinh", models.DateField(blank=True, db_column="ngaySinh", null=True, verbose_name="ngày sinh")),
                ("gioiTinh", models.CharField(blank=True, choices=[("Nam", "Nam"), ("Nữ", "Nữ"), ("Khác", "Khác")], db_column="gioiTinh", max_length=10, verbose_name="giới tính")),
                ("diaChi", models.TextField(blank=True, db_column="diaChi", verbose_name="địa chỉ")),
                ("vaiTro", models.CharField(choices=[("user", "User"), ("admin", "Admin"), ("contributor", "Contributor")], db_column="vaiTro", default="user", max_length=20, verbose_name="vai trò")),
                ("trangThai", models.CharField(choices=[("active", "Active"), ("inactive", "Inactive"), ("banned", "Banned")], db_column="trangThai", default="active", max_length=20, verbose_name="trạng thái")),
                (
                    "groups",
                    models.ManyToManyField(
                        blank=True,
                        help_text="The groups this user belongs to. A user will get all permissions granted to each of their groups.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.group",
                        verbose_name="groups",
                    ),
                ),
                (
                    "user_permissions",
                    models.ManyToManyField(
                        blank=True,
                        help_text="Specific permissions for this user.",
                        related_name="user_set",
                        related_query_name="user",
                        to="auth.permission",
                        verbose_name="user permissions",
                    ),
                ),
            ],
            options={
                "verbose_name": "Người dùng",
                "verbose_name_plural": "Người dùng",
                "db_table": "NGUOIDUNG",
                "ordering": ["-date_joined"],
            },
            managers=[
                ("objects", django.contrib.auth.models.UserManager()),
            ],
        ),
    ]
