from django import forms
from django.utils.translation import gettext_lazy as _
from django.apps import apps


TinhThanh = apps.get_model('places', 'TinhThanh')


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class PendingPlaceForm(forms.Form):
    """Form gom đề xuất địa điểm vào lớp đóng góp thống nhất."""

    tenDiaDiem = forms.CharField(label=_('Tên địa điểm'), max_length=255)
    maTinhThanh = forms.ModelChoiceField(
        label=_('Tỉnh/Thành phố'),
        queryset=TinhThanh.objects.none(),
    )
    diaChi = forms.CharField(label=_('Địa chỉ'), widget=forms.TextInput())
    moTa = forms.CharField(label=_('Mô tả chi tiết'), widget=forms.Textarea(attrs={'rows': 4}), required=False)
    viDo = forms.FloatField(label=_('Vĩ độ'), required=False)
    kinhDo = forms.FloatField(label=_('Kinh độ'), required=False)
    soDienThoai = forms.CharField(label=_('Số điện thoại'), max_length=20, required=False)
    website = forms.URLField(label=_('Website'), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['maTinhThanh'].queryset = TinhThanh.objects.all().order_by('tenTinhThanh')
        self.fields['maTinhThanh'].empty_label = _('-- Chọn tỉnh/thành phố --')
        self.fields['viDo'].widget.attrs.update({'step': '0.000001'})
        self.fields['kinhDo'].widget.attrs.update({'step': '0.000001'})

        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})


class PendingPlaceImageForm(forms.Form):
    """Form nhận ảnh đề xuất để lưu vào duLieuBoSung."""

    image = forms.FileField(
        label=_('Hình ảnh'),
        required=False,
        widget=MultipleFileInput(attrs={'class': 'form-control', 'multiple': True}),
    )
    moTa = forms.CharField(
        label=_('Mô tả'),
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': _('Mô tả ngắn về hình ảnh')}),
    )
    laChinh = forms.BooleanField(label=_('Đặt làm ảnh đại diện'), required=False)
