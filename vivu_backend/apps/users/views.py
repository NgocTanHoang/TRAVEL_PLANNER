from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, TemplateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import PasswordChangeView
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from apps.places.models import DiaDiem
from apps.itineraries.models import LichTrinh
from apps.users.models import LichSuTimKiem


User = get_user_model()


class SignupForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'placeholder': 'Email'
        })
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'placeholder': 'Tên đăng nhập'
        })
        self.fields['password1'].widget.attrs.update({
            'placeholder': 'Mật khẩu'
        })
        self.fields['password2'].widget.attrs.update({
            'placeholder': 'Xác nhận mật khẩu'
        })

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")


class SignupView(CreateView):
    form_class = SignupForm
    template_name = "registration/signup.html"
    success_url = reverse_lazy("login")


class ProfileEditForm(forms.ModelForm):
    """Form for editing user profile."""
    
    class Meta:
        model = User
        fields = ['username', 'email', 'hoTen', 'soDienThoai', 'ngaySinh', 
                  'gioiTinh', 'diaChi', 'anhDaiDien']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-input'}),
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
            'hoTen': forms.TextInput(attrs={'class': 'form-input'}),
            'soDienThoai': forms.TextInput(attrs={'class': 'form-input'}),
            'ngaySinh': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-input'
            }),
            'gioiTinh': forms.Select(attrs={'class': 'form-input'}),
            'diaChi': forms.Textarea(attrs={
                'class': 'form-input',
                'rows': 3
            }),
            'anhDaiDien': forms.TextInput(attrs={'class': 'form-input'}),
        }
        labels = {
            'username': 'Tên đăng nhập',
            'email': 'Email',
            'hoTen': 'Họ tên',
            'soDienThoai': 'Số điện thoại',
            'ngaySinh': 'Ngày sinh',
            'gioiTinh': 'Giới tính',
            'diaChi': 'Địa chỉ',
            'anhDaiDien': 'Ảnh đại diện (URL)',
        }


class ProfileView(LoginRequiredMixin, UpdateView):
    """View for viewing and editing user profile."""
    model = User
    form_class = ProfileEditForm
    template_name = 'users/profile.html'
    success_url = reverse_lazy('profile')
    
    def get_object(self):
        return self.request.user
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        
        # Get user's itineraries
        context['itineraries'] = LichTrinh.objects.filter(
            maNguoiDung=user
        ).order_by('-ngayTao')[:10]
        
        # Get searched places (from recent itinerary places)
        recent_places = DiaDiem.objects.filter(
            lich_trinhs__maNguoiDung=user
        ).distinct().order_by('-lich_trinhs__ngayTao')[:10]
        
        context['recent_places'] = recent_places
        
        return context


class CustomPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    """Custom password change view."""
    template_name = 'users/change_password.html'
    form_class = PasswordChangeForm
    success_url = reverse_lazy('profile')


class SearchHistoryView(LoginRequiredMixin, ListView):
    """View for displaying user's search history."""
    template_name = 'users/search_history.html'
    context_object_name = 'search_history'
    paginate_by = 20
    
    def get_queryset(self):
        """Get user's search history."""
        user = self.request.user
        return LichSuTimKiem.objects.filter(
            maNguoiDung=user
        ).select_related('maDiaDiem', 'maDiaDiem__maTinhThanh').order_by('-ngayTim')


class PlaceSearchView(TemplateView):
    """View for place search page."""
    template_name = 'places/search.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['initial_query'] = self.request.GET.get('q', '')
        return context


class UserItinerariesView(LoginRequiredMixin, ListView):
    """View for displaying user's itineraries."""
    template_name = 'users/itineraries.html'
    context_object_name = 'itineraries'
    paginate_by = 20
    
    def get_queryset(self):
        """Get user's itineraries."""
        user = self.request.user
        return LichTrinh.objects.filter(
            maNguoiDung=user
        ).order_by('-ngayTao')


class PlaceDetailView(TemplateView):
    """View for place detail page."""
    template_name = 'places/detail.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        place_id = kwargs.get('id') or kwargs.get('pk')
        
        try:
            place = DiaDiem.objects.select_related('maTinhThanh').prefetch_related('hinh_anhs', 'danh_gias__maNguoiDung').get(
                maDiaDiem=place_id,
                trangThai='active'
            )
            
            # Tăng số lượt xem
            place.soLuotXem += 1
            place.save(update_fields=['soLuotXem'])
            
            context['place'] = place
            context['main_image'] = place.hinh_anhs.filter(laChinh=True).first() or place.hinh_anhs.first()
            context['other_images'] = place.hinh_anhs.exclude(laChinh=True)[:10] if context['main_image'] else place.hinh_anhs[:10]
            context['reviews'] = place.danh_gias.filter(trangThai='active')[:10]
            
            # Parse JSON fields
            import json
            try:
                context['dac_diem'] = json.loads(place.dacDiem) if place.dacDiem else []
            except:
                context['dac_diem'] = []
            
            try:
                context['tien_nghi'] = json.loads(place.tienNghi) if place.tienNghi else []
            except:
                context['tien_nghi'] = []
                
        except DiaDiem.DoesNotExist:
            context['place'] = None
            
        return context


