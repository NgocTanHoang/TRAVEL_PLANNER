"""DRF Serializers for Vi Vu API."""
from rest_framework import serializers
from apps.users.models import NguoiDung
from apps.places.models import TinhThanh, DiaDiem, HinhAnhDiaDiem, DanhGia
from apps.itineraries.models import LichTrinh, LichTrinhDiaDiem
from django.contrib.auth.hashers import make_password


class RegisterSerializer(serializers.ModelSerializer):
    """User registration."""
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = NguoiDung
        fields = ['username', 'email', 'password', 'hoTen']
        extra_kwargs = {'password': {'write_only': True}}
    
    def create(self, validated_data):
        user = NguoiDung.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            hoTen=validated_data.get('hoTen', '')
        )
        return user


class NguoiDungSerializer(serializers.ModelSerializer):
    """User profile."""
    maNguoiDung = serializers.IntegerField(source='id', read_only=True)
    tenDangNhap = serializers.CharField(source='username', read_only=True)
    
    class Meta:
        model = NguoiDung
        fields = ['maNguoiDung', 'tenDangNhap', 'email', 'hoTen', 'soDienThoai', 'vaiTro']
        read_only_fields = ['maNguoiDung', 'tenDangNhap']


class TinhThanhSerializer(serializers.ModelSerializer):
    """City."""
    class Meta:
        model = TinhThanh
        fields = '__all__'


class HinhAnhDiaDiemSerializer(serializers.ModelSerializer):
    """Place image."""
    class Meta:
        model = HinhAnhDiaDiem
        fields = ['maHinhAnh', 'urlHinhAnh', 'moTa', 'laChinh']


class DiaDiemListSerializer(serializers.ModelSerializer):
    """Place list (summary)."""
    tenTinhThanh = serializers.CharField(source='maTinhThanh.tenTinhThanh', read_only=True)
    hinhAnhChinh = serializers.SerializerMethodField()
    
    class Meta:
        model = DiaDiem
        fields = ['maDiaDiem', 'tenDiaDiem', 'moTa', 'tenTinhThanh', 'loaiDiaDiem', 
                  'danhGiaTrungBinh', 'soLuotDanhGia', 'giaVe', 'hinhAnhChinh', 
                  'viDo', 'kinhDo', 'diaChi', 'gioMoCua', 'gioDongCua', 'dienThoai', 'website']
    
    def get_hinhAnhChinh(self, obj):
        hinh = obj.hinh_anhs.filter(laChinh=True).first()
        return hinh.urlHinhAnh if hinh else None


class DiaDiemDetailSerializer(serializers.ModelSerializer):
    """Place detail."""
    tenTinhThanh = serializers.CharField(source='maTinhThanh.tenTinhThanh', read_only=True)
    hinhAnhs = HinhAnhDiaDiemSerializer(many=True, read_only=True, source='hinh_anhs')
    
    class Meta:
        model = DiaDiem
        fields = '__all__'


class DanhGiaSerializer(serializers.ModelSerializer):
    """Review."""
    tenNguoiDung = serializers.CharField(source='maNguoiDung.hoTen', read_only=True)
    
    class Meta:
        model = DanhGia
        fields = ['maDanhGia', 'diemDanhGia', 'tieuDe', 'noiDung', 'tenNguoiDung', 'ngayTao']
        read_only_fields = ['maDanhGia', 'ngayTao']


class LichTrinhDiaDiemSerializer(serializers.ModelSerializer):
    """Itinerary place."""
    tenDiaDiem = serializers.CharField(source='maDiaDiem.tenDiaDiem', read_only=True)
    
    class Meta:
        model = LichTrinhDiaDiem
        fields = ['maDiaDiem', 'tenDiaDiem', 'ngayThamQuan', 'thoiGianThamQuan', 'thuTu']


class LichTrinhSerializer(serializers.ModelSerializer):
    """Itinerary."""
    tenNguoiDung = serializers.CharField(source='maNguoiDung.tenDangNhap', read_only=True)
    dia_diems_detail = LichTrinhDiaDiemSerializer(many=True, read_only=True, source='lich_trinh_dia_diems')
    
    class Meta:
        model = LichTrinh
        fields = ['maLichTrinh', 'tieuDe', 'moTa', 'ngayBatDau', 'ngayKetThuc', 'soNgay', 
                  'soNguoi', 'nganSach', 'trangThai', 'tenNguoiDung', 'dia_diems_detail']
        read_only_fields = ['maLichTrinh', 'soNgay']

