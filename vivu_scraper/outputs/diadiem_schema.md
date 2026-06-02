# Schema bang DIADIEM

- Model: `DiaDiem`
- Table: `DIADIEM`
- Ordering: `['-danhGiaTrungBinh', '-soLuotDanhGia']`

| Truong | Cot DB | Kieu | Null | Blank | PK | Unique | Index | Quan he |
|---|---|---|---|---|---|---|---|---|
| maDiaDiem | maDiaDiem | AutoField | False | True | True | True | False |  |
| tenDiaDiem | tenDiaDiem | CharField | False | False | False | False | True |  |
| moTa | moTa | TextField | False | True | False | False | False |  |
| diaChi | diaChi | CharField | False | True | False | False | False |  |
| maTinhThanh | maTinhThanh | ForeignKey | False | False | False | False | True | TinhThanh |
| loaiDiaDiem | loaiDiaDiem | CharField | False | False | False | False | False |  |
| viDo | viDo | FloatField | True | True | False | False | False |  |
| kinhDo | kinhDo | FloatField | True | True | False | False | False |  |
| giaVe | giaVe | FloatField | True | True | False | False | False |  |
| gioMoCua | gioMoCua | CharField | False | True | False | False | False |  |
| gioDongCua | gioDongCua | CharField | False | True | False | False | False |  |
| dienThoai | dienThoai | CharField | False | True | False | False | False |  |
| website | website | CharField | False | True | False | False | False |  |
| danhGiaTrungBinh | danhGiaTrungBinh | FloatField | False | False | False | False | False |  |
| soLuotDanhGia | soLuotDanhGia | IntegerField | False | False | False | False | False |  |
| soLuotXem | soLuotXem | IntegerField | False | False | False | False | False |  |
| maNguoiTao | maNguoiTao | ForeignKey | True | True | False | False | True | NguoiDung |
| ngayTao | ngayTao | DateTimeField | False | True | False | False | False |  |
| lanCapNhatCuoi | lanCapNhatCuoi | DateTimeField | False | True | False | False | False |  |
| trangThai | trangThai | CharField | False | False | False | False | False |  |
| dacDiem | dacDiem | TextField | False | True | False | False | False |  |
| tienNghi | tienNghi | TextField | False | True | False | False | False |  |

## Indexes

- `DIADIEM_maTinhT_58a390_idx`: maTinhThanh, loaiDiaDiem
- `DIADIEM_danhGia_14da23_idx`: -danhGiaTrungBinh
- `DIADIEM_trangTh_290f7b_idx`: trangThai