from django import forms
from django.utils.translation import gettext_lazy as _
from django.apps import apps

# Get models using string references to avoid circular imports
PendingPlace = apps.get_model('places', 'PendingPlace')
PendingPlaceImage = apps.get_model('places', 'PendingPlaceImage')
TinhThanh = apps.get_model('places', 'TinhThanh')

class PendingPlaceForm(forms.ModelForm):
    """Form for submitting new places for approval."""
    
    class Meta:
        model = PendingPlace
        fields = [
            'tenDiaDiem', 'maTinhThanh', 'diaChi', 'moTa', 
            'viDo', 'kinhDo'
        ]
        labels = {
            'tenDiaDiem': _('Tên địa điểm'),
            'maTinhThanh': _('Tỉnh/Thành phố'),
            'diaChi': _('Địa chỉ'),
            'moTa': _('Mô tả chi tiết'),
            'viDo': _('Vĩ độ'),
            'kinhDo': _('Kinh độ'),
        }
        widgets = {
            'moTa': forms.Textarea(attrs={'rows': 4}),
            'viDo': forms.NumberInput(attrs={'step': '0.000001'}),
            'kinhDo': forms.NumberInput(attrs={'step': '0.000001'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['maTinhThanh'].queryset = TinhThanh.objects.all().order_by('tenTinhThanh')
        self.fields['maTinhThanh'].empty_label = _('-- Chọn tỉnh/thành phố --')
        
        # Add Bootstrap classes to form fields
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})


class PendingPlaceImageForm(forms.ModelForm):
    """Form for uploading images for a pending place."""
    class Meta:
        model = PendingPlaceImage
        fields = ['image', 'moTa', 'laChinh']
        labels = {
            'image': _('Hình ảnh'),
            'moTa': _('Mô tả'),
            'laChinh': _('Đặt làm ảnh đại diện')
        }
        widgets = {
            'moTa': forms.TextInput(attrs={'placeholder': _('Mô tả ngắn về hình ảnh')}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['image'].widget.attrs.update({'class': 'form-control'})
        self.fields['moTa'].widget.attrs.update({'class': 'form-control'})
