"""Views for unified POI contribution flows backed by DONGGOP."""
from __future__ import annotations

from django.apps import apps
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .contribution_service import approve_contribution, is_admin_role
from .forms import PendingPlaceForm, PendingPlaceImageForm


DongGop = apps.get_model("itineraries", "DongGop")
TinhThanh = apps.get_model("places", "TinhThanh")


def _build_submission_payload(cleaned_data, uploaded_files, image_note: str, is_primary: bool):
    images = []
    for index, uploaded in enumerate(uploaded_files):
        images.append(
            {
                "file_name": uploaded.name,
                "content_type": getattr(uploaded, "content_type", ""),
                "size": getattr(uploaded, "size", 0),
                "mo_ta": image_note,
                "la_chinh": is_primary and index == 0,
            }
        )

    return {
        "ten_dia_diem": cleaned_data["tenDiaDiem"],
        "ma_tinh_thanh": cleaned_data["maTinhThanh"].pk,
        "ten_tinh_thanh": cleaned_data["maTinhThanh"].tenTinhThanh,
        "dia_chi": cleaned_data["diaChi"],
        "mo_ta": cleaned_data.get("moTa", ""),
        "so_dien_thoai": cleaned_data.get("soDienThoai", ""),
        "website": cleaned_data.get("website", ""),
        "toa_do": {
            "vi_do": cleaned_data.get("viDo"),
            "kinh_do": cleaned_data.get("kinhDo"),
        },
        "de_xuat_hinh_anh": images,
    }


@login_required
def submit_place(request):
    """Capture a guest-authenticated POI proposal into the unified DONGGOP model."""
    if request.method == "POST":
        place_form = PendingPlaceForm(request.POST)
        image_form = PendingPlaceImageForm(request.POST, request.FILES)

        if place_form.is_valid() and image_form.is_valid():
            uploaded_files = request.FILES.getlist("image")
            payload = _build_submission_payload(
                place_form.cleaned_data,
                uploaded_files,
                image_form.cleaned_data.get("moTa", ""),
                image_form.cleaned_data.get("laChinh", False),
            )

            with transaction.atomic():
                contribution = DongGop.objects.create(
                    maNguoiDung=request.user,
                    maDiaDiem=None,
                    loaiDongGop="THEM_MOI_POI",
                    noiDung=(
                        f"Đề xuất địa điểm mới: {place_form.cleaned_data['tenDiaDiem']} - "
                        f"{place_form.cleaned_data['diaChi']}"
                    ),
                    duLieuBoSung=payload,
                    trangThai="pending",
                )

            messages.success(request, _("Đã gửi đề xuất địa điểm thành công!"))
            return redirect("places:pending_place_success", pk=contribution.pk)
    else:
        place_form = PendingPlaceForm()
        image_form = PendingPlaceImageForm()

    return render(
        request,
        "places/submit_place.html",
        {
            "place_form": place_form,
            "image_form": image_form,
            "title": _("Gửi địa điểm mới"),
        },
    )


@login_required
def submit_success(request, pk):
    """Render a success page for the submitted contribution."""
    contribution = get_object_or_404(
        DongGop,
        pk=pk,
        loaiDongGop="THEM_MOI_POI",
        maNguoiDung=request.user,
    )
    return render(
        request,
        "places/submit_success.html",
        {
            "place": contribution,
            "title": _("Gửi địa điểm thành công"),
        },
    )


@login_required
@user_passes_test(is_admin_role)
def pending_place_list(request):
    """List pending POI contributions for admins."""
    pending_places = DongGop.objects.filter(
        loaiDongGop="THEM_MOI_POI",
        trangThai="pending",
    ).order_by("-ngayTao")
    return render(
        request,
        "admin/pending_place_list.html",
        {
            "pending_places": pending_places,
            "title": _("Danh sách địa điểm chờ duyệt"),
        },
    )


@login_required
@user_passes_test(is_admin_role)
def review_pending_place(request, pk):
    """Approve or reject a pending POI contribution."""
    contribution = get_object_or_404(DongGop, pk=pk, loaiDongGop="THEM_MOI_POI")
    proposal = contribution.duLieuBoSung or {}
    province = None
    province_id = proposal.get("ma_tinh_thanh")
    if province_id:
        province = TinhThanh.objects.filter(pk=province_id).first()

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "approve" and province:
            approve_contribution(contribution, approver=request.user)
            messages.success(request, _("Đã phê duyệt địa điểm thành công!"))
            return redirect("places:admin_pending_places")

        if action == "reject":
            reason = request.POST.get("reason", "")
            contribution.trangThai = "rejected"
            contribution.phanHoi = reason
            contribution.ngayXuLy = timezone.now()
            contribution.save(update_fields=["trangThai", "phanHoi", "ngayXuLy"])
            messages.success(request, _("Đã từ chối địa điểm."))
            return redirect("places:admin_pending_places")

    return render(
        request,
        "admin/review_pending_place.html",
        {
            "place": contribution,
            "proposal": proposal,
            "title": _("Xem xét địa điểm"),
        },
    )


@login_required
def my_pending_places(request):
    """Show the current user's submitted POI contributions."""
    pending_places = DongGop.objects.filter(
        maNguoiDung=request.user,
        loaiDongGop="THEM_MOI_POI",
    ).order_by("-ngayTao")
    return render(
        request,
        "places/my_pending_places.html",
        {
            "pending_places": pending_places,
            "title": _("Địa điểm đã gửi của tôi"),
        },
    )
