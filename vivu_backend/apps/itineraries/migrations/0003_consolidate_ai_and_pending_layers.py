from __future__ import annotations

from datetime import date

from django.db import migrations, models, transaction


LEGACY_CONTRIBUTION_TYPE_MAP = {
    "them_dia_diem": "THEM_MOI_POI",
    "sua_thong_tin": "SUA_DOI_POI",
    "bao_cao_loi": "BAO_CAO_LOI",
    "khac": "KHAC",
}


def _merge_ai_into_primary_tables(apps, schema_editor):
    db_alias = schema_editor.connection.alias
    existing_tables = set(schema_editor.connection.introspection.table_names())
    LichTrinh = apps.get_model("itineraries", "LichTrinh")
    LichTrinhDiaDiem = apps.get_model("itineraries", "LichTrinhDiaDiem")
    LichTrinhAI = apps.get_model("itineraries", "LichTrinhAI")
    LichTrinhAIDiaDiem = apps.get_model("itineraries", "LichTrinhAIDiaDiem")
    DongGop = apps.get_model("itineraries", "DongGop")
    PendingPlace = apps.get_model("places", "PendingPlace")
    PendingPlaceImage = apps.get_model("places", "PendingPlaceImage")

    with transaction.atomic(using=db_alias):
        for contribution in DongGop.objects.using(db_alias).all().iterator():
            normalized_type = LEGACY_CONTRIBUTION_TYPE_MAP.get(contribution.loaiDongGop, contribution.loaiDongGop)
            if contribution.loaiDongGop != normalized_type:
                contribution.loaiDongGop = normalized_type
                contribution.save(update_fields=["loaiDongGop"])

        if "PENDING_PLACES" in existing_tables:
            for pending_place in PendingPlace.objects.using(db_alias).all().iterator():
                images_payload = []
                if "PENDING_PLACE_IMAGES" in existing_tables:
                    for image in PendingPlaceImage.objects.using(db_alias).filter(pending_place_id=pending_place.pk):
                        image_name = getattr(image.image, "name", "")
                        image_url = image_name or ""
                        images_payload.append(
                            {
                                "file_name": image_name,
                                "image_path": image_url,
                                "mo_ta": image.moTa,
                                "la_chinh": image.laChinh,
                            }
                        )

                DongGop.objects.using(db_alias).create(
                    maNguoiDung=pending_place.nguoiTao,
                    maDiaDiem=None,
                    loaiDongGop="THEM_MOI_POI",
                    noiDung=f"Đề xuất địa điểm mới: {pending_place.tenDiaDiem} - {pending_place.diaChi}",
                    duLieuBoSung={
                        "legacy_pending_place_id": pending_place.pk,
                        "ten_dia_diem": pending_place.tenDiaDiem,
                        "ma_tinh_thanh": pending_place.maTinhThanh_id,
                        "ten_tinh_thanh": pending_place.maTinhThanh.tenTinhThanh,
                        "dia_chi": pending_place.diaChi,
                        "mo_ta": pending_place.moTa,
                        "so_dien_thoai": pending_place.soDienThoai,
                        "website": pending_place.website,
                        "toa_do": {
                            "vi_do": pending_place.viDo,
                            "kinh_do": pending_place.kinhDo,
                        },
                        "de_xuat_hinh_anh": images_payload,
                        "ly_do_tu_choi_cu": pending_place.lyDoTuChoi,
                    },
                    trangThai=pending_place.trangThai,
                    phanHoi=pending_place.lyDoTuChoi or "",
                )

        if "LICHTRINHAI" not in existing_tables:
            return

        for ai_itinerary in LichTrinhAI.objects.using(db_alias).select_related("maLichTrinh", "maTinhThanh", "maNguoiDung"):
            target_itinerary = ai_itinerary.maLichTrinh
            first_visit = None
            if "LICHTRINHAI_DIADIEM" in existing_tables:
                first_visit = (
                    LichTrinhAIDiaDiem.objects.using(db_alias)
                    .filter(maLichTrinhAI=ai_itinerary, ngayThamQuan__isnull=False)
                    .order_by("ngayThamQuan")
                    .values_list("ngayThamQuan", flat=True)
                    .first()
                )
            start_date = ai_itinerary.ngayBatDau or ai_itinerary.ngayKetThuc or first_visit or date.today()
            end_date = ai_itinerary.ngayKetThuc or ai_itinerary.ngayBatDau or first_visit or start_date

            if target_itinerary is None:
                target_itinerary = LichTrinh.objects.using(db_alias).create(
                    maNguoiDung=ai_itinerary.maNguoiDung,
                    maTinhThanh=ai_itinerary.maTinhThanh,
                    tieuDe=ai_itinerary.tieuDe,
                    moTa=ai_itinerary.moTa or "",
                    ngayBatDau=start_date,
                    ngayKetThuc=end_date,
                    soNgay=ai_itinerary.soNgay,
                    soNguoi=ai_itinerary.soNguoi or 1,
                    nganSach=ai_itinerary.nganSach,
                    chiPhiUocTinh=None,
                    trangThai="draft" if ai_itinerary.trangThai == "generated" else "published",
                    laCongKhai=False,
                    is_ai_generated=True,
                    chiTiet=ai_itinerary.chiTiet or "",
                )
            else:
                update_fields = []
                if not target_itinerary.is_ai_generated:
                    target_itinerary.is_ai_generated = True
                    update_fields.append("is_ai_generated")
                if not (target_itinerary.chiTiet or "").strip() and (ai_itinerary.chiTiet or "").strip():
                    target_itinerary.chiTiet = ai_itinerary.chiTiet
                    update_fields.append("chiTiet")
                if not (target_itinerary.moTa or "").strip() and (ai_itinerary.moTa or "").strip():
                    target_itinerary.moTa = ai_itinerary.moTa
                    update_fields.append("moTa")
                if target_itinerary.maTinhThanh_id is None and ai_itinerary.maTinhThanh_id is not None:
                    target_itinerary.maTinhThanh = ai_itinerary.maTinhThanh
                    update_fields.append("maTinhThanh")
                if update_fields:
                    target_itinerary.save(update_fields=update_fields)

            if "LICHTRINHAI_DIADIEM" not in existing_tables:
                continue

            for ai_row in LichTrinhAIDiaDiem.objects.using(db_alias).filter(maLichTrinhAI=ai_itinerary):
                visit_date = ai_row.ngayThamQuan or target_itinerary.ngayBatDau or start_date
                if visit_date is None:
                    continue

                LichTrinhDiaDiem.objects.using(db_alias).update_or_create(
                    maLichTrinh=target_itinerary,
                    maDiaDiem=ai_row.maDiaDiem,
                    ngayThamQuan=visit_date,
                    defaults={
                        "thoiGianThamQuan": ai_row.thoiGianThamQuan or "",
                        "thuTu": ai_row.thuTu,
                        "ghiChu": ai_row.ghiChu or "",
                        "chiPhiUocTinh": ai_row.chiPhiUocTinh,
                    },
                )


class Migration(migrations.Migration):
    atomic = True

    dependencies = [
        ("places", "0001_initial"),
        ("itineraries", "0002_alter_lichtrinh_manguoidung_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="donggop",
            name="duLieuBoSung",
            field=models.JSONField(blank=True, db_column="duLieuBoSung", null=True, verbose_name="dữ liệu bổ sung"),
        ),
        migrations.AddField(
            model_name="lichtrinh",
            name="is_ai_generated",
            field=models.BooleanField(db_column="is_ai_generated", default=False, verbose_name="Do AI sinh ra"),
        ),
        migrations.AlterField(
            model_name="donggop",
            name="loaiDongGop",
            field=models.CharField(
                choices=[
                    ("THEM_MOI_POI", "Thêm mới địa điểm"),
                    ("SUA_DOI_POI", "Sửa đổi địa điểm"),
                    ("BAO_CAO_LOI", "Báo cáo lỗi"),
                    ("KHAC", "Khác"),
                ],
                db_column="loaiDongGop",
                max_length=50,
                verbose_name="loại đóng góp",
            ),
        ),
        migrations.RunPython(_merge_ai_into_primary_tables, migrations.RunPython.noop),
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL("DROP TABLE IF EXISTS LICHTRINHAI_DIADIEM"),
            ],
            state_operations=[
                migrations.DeleteModel(
                    name="LichTrinhAIDiaDiem",
                ),
            ],
        ),
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL("DROP TABLE IF EXISTS LICHTRINHAI"),
            ],
            state_operations=[
                migrations.DeleteModel(
                    name="LichTrinhAI",
                ),
            ],
        ),
    ]
