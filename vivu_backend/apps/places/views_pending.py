from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.http import JsonResponse
from django.views.decorators.http import require_POST, require_http_methods
from django.core.exceptions import PermissionDenied

from django.apps import apps
from .forms import PendingPlaceForm, PendingPlaceImageForm

# Get models using string references to avoid circular imports
PendingPlace = apps.get_model('places', 'PendingPlace')
PendingPlaceImage = apps.get_model('places', 'PendingPlaceImage')
TinhThanh = apps.get_model('places', 'TinhThanh')
DiaDiem = apps.get_model('places', 'DiaDiem')

# Helper function to check if user is admin
def is_admin(user):
    return user.is_authenticated and user.is_staff

@login_required
def submit_place(request):
    if request.method == 'POST':
        place_form = PendingPlaceForm(request.POST)
        image_form = PendingPlaceImageForm(request.POST, request.FILES)
        
        if place_form.is_valid() and image_form.is_valid():
            # Save pending place
            pending_place = place_form.save(commit=False)
            pending_place.nguoiDang = request.user
            pending_place.save()
            
            # Save images
            images = request.FILES.getlist('image')
            for i, image in enumerate(images):
                PendingPlaceImage.objects.create(
                    diaDiem=pending_place,
                    image=image,
                    laChinh=(i == 0)  # First image is main
                )
            
            messages.success(request, _('Đã gửi địa điểm chờ phê duyệt thành công!'))
            return redirect('submit_success', pk=pending_place.pk)
    else:
        place_form = PendingPlaceForm()
        image_form = PendingPlaceImageForm()
    
    return render(request, 'places/submit_place.html', {
        'place_form': place_form,
        'image_form': image_form,
        'title': _('Gửi địa điểm mới')
    })

def submit_success(request, pk):
    """Success page after place submission."""
    pending_place = get_object_or_404(PendingPlace, pk=pk)
    return render(request, 'places/submit_success.html', {
        'place': pending_place,
        'title': _('Gửi địa điểm thành công')
    })

@login_required
@user_passes_test(is_admin)
def pending_place_list(request):
    """Admin view to see all pending places."""
    pending_places = PendingPlace.objects.filter(trangThai='pending').order_by('-ngayTao')
    return render(request, 'admin/pending_place_list.html', {
        'pending_places': pending_places,
        'title': _('Danh sách địa điểm chờ duyệt')
    })

@login_required
@user_passes_test(is_admin)
def review_pending_place(request, pk):
    pending_place = get_object_or_404(PendingPlace, pk=pk)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'approve':
            # Create new DiaDiem from pending place
            place = DiaDiem.objects.create(
                tenDiaDiem=pending_place.tenDiaDiem,
                maTinhThanh=pending_place.maTinhThanh,
                diaChi=pending_place.diaChi,
                moTa=pending_place.moTa,
                viDo=pending_place.viDo,
                kinhDo=pending_place.kinhDo,
                nguoiTao=pending_place.nguoiDang
            )
            
            # Update status
            pending_place.trangThai = 'approved'
            pending_place.save()
            
            messages.success(request, _('Đã phê duyệt địa điểm thành công!'))
            return redirect('admin_pending_places')
            
        elif action == 'reject':
            reason = request.POST.get('reason', '')
            pending_place.trangThai = 'rejected'
            pending_place.lyDoTuChoi = reason
            pending_place.save()
            
            messages.success(request, _('Đã từ chối địa điểm.'))
            return redirect('admin_pending_places')
    
    return render(request, 'admin/review_pending_place.html', {
        'place': pending_place,
        'title': _('Xem xét địa điểm')
    })

@login_required
def my_pending_places(request):
    """View for users to see their submitted places."""
    pending_places = PendingPlace.objects.filter(nguoiDang=request.user).order_by('-ngayTao')
    return render(request, 'places/my_pending_places.html', {
        'pending_places': pending_places,
        'title': _('Địa điểm đã gửi của tôi')
    })
