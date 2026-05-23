"""
Utility functions to format itinerary data for LLM description generation
"""
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from apps.itineraries.models import LichTrinh, LichTrinhDiaDiem
from apps.places.models import DiaDiem

logger = logging.getLogger(__name__)


def format_itinerary_to_json(
    lich_trinh: LichTrinh,
    include_places: bool = True
) -> Dict[str, Any]:
    """
    Format LichTrinh object thành JSON structure như yêu cầu
    
    Args:
        lich_trinh: LichTrinh object
        include_places: Có bao gồm thông tin địa điểm không
        
    Returns:
        Dict với keys: LICHTRINH, DIADIEM, LICHTRINH_DIADIEM
    """
    result = {
        "LICHTRINH": [],
        "DIADIEM": [],
        "LICHTRINH_DIADIEM": []
    }
    
    # Format LICHTRINH
    lich_trinh_data = {
        "maLichTrinh": lich_trinh.maLichTrinh,
        "tenLichTrinh": lich_trinh.tieuDe,
        "soNgay": lich_trinh.soNgay or 0,
        "soNguoi": lich_trinh.soNguoi or 1,
        "phongCach": _extract_travel_style(lich_trinh.tieuDe),
        "diemXuatPhat": _extract_origin(lich_trinh.tieuDe),
        "diemDen": lich_trinh.maTinhThanh.tenTinhThanh if lich_trinh.maTinhThanh else "",
        "ngayBatDau": lich_trinh.ngayBatDau.isoformat() if lich_trinh.ngayBatDau else None,
        "ngayKetThuc": lich_trinh.ngayKetThuc.isoformat() if lich_trinh.ngayKetThuc else None,
        "tongChiPhiDuKien": int(lich_trinh.chiPhiUocTinh or lich_trinh.nganSach or 0),
        "trangThai": lich_trinh.trangThai
    }
    result["LICHTRINH"].append(lich_trinh_data)
    
    if not include_places:
        return result
    
    # Get all places in this itinerary
    lich_trinh_dia_diems = LichTrinhDiaDiem.objects.filter(
        maLichTrinh=lich_trinh
    ).select_related('maDiaDiem', 'maDiaDiem__maTinhThanh').order_by('ngayThamQuan', 'thuTu')
    
    # Track unique places
    places_dict = {}
    place_id_mapping = {}  # Map database ID to sequential ID
    
    for ltdd in lich_trinh_dia_diems:
        dia_diem = ltdd.maDiaDiem
        
        # Add place to DIADIEM if not already added
        if dia_diem.maDiaDiem not in places_dict:
            # Assign sequential ID starting from 1
            new_id = len(places_dict) + 1
            place_id_mapping[dia_diem.maDiaDiem] = new_id
            
            # Format DIADIEM
            dia_diem_data = {
                "maDiaDiem": new_id,
                "tenDiaDiem": dia_diem.tenDiaDiem,
                "moTa": dia_diem.moTa or "",
                "diaChi": dia_diem.diaChi or "",
                "maTinhThanh": dia_diem.maTinhThanh.maTinhThanh if dia_diem.maTinhThanh else None,
                "loaiDiaDiem": dia_diem.loaiDiaDiem,
                "viDo": float(dia_diem.viDo) if dia_diem.viDo else None,
                "kinhDo": float(dia_diem.kinhDo) if dia_diem.kinhDo else None,
                "giaVe": int(dia_diem.giaVe) if dia_diem.giaVe else 0,
                "gioMoCua": dia_diem.gioMoCua or "00:00",
                "gioDongCua": dia_diem.gioDongCua or "23:59",
                "dienThoai": dia_diem.dienThoai or None,
                "website": dia_diem.website or None,
                "danhGiaTrungBinh": float(dia_diem.danhGiaTrungBinh) if dia_diem.danhGiaTrungBinh else 0.0,
                "soLuotDanhGia": dia_diem.soLuotDanhGia or 0,
                "soLuotXem": dia_diem.soLuotXem or 0,
                "maNguoiTao": dia_diem.maNguoiTao_id if dia_diem.maNguoiTao else None,
                "ngayTao": dia_diem.ngayTao.isoformat() if dia_diem.ngayTao else None,
                "lanCapNhatCuoi": dia_diem.lanCapNhatCuoi.isoformat() if dia_diem.lanCapNhatCuoi else None,
                "trangThai": dia_diem.trangThai,
                "dacDiem": dia_diem.dacDiem or None,
                "tienNghi": dia_diem.tienNghi or None
            }
            result["DIADIEM"].append(dia_diem_data)
            places_dict[dia_diem.maDiaDiem] = new_id
        
        # Calculate ngayThu (day number, starting from 1)
        if lich_trinh.ngayBatDau and ltdd.ngayThamQuan:
            delta = (ltdd.ngayThamQuan - lich_trinh.ngayBatDau).days + 1
            ngay_thu = max(1, delta)
        else:
            # Fallback: use order in query
            ngay_thu = 1
        
        # Format LICHTRINH_DIADIEM
        lich_trinh_dia_diem_data = {
            "maLichTrinh": lich_trinh.maLichTrinh,
            "maDiaDiem": place_id_mapping[dia_diem.maDiaDiem],
            "ngayThu": ngay_thu,
            "thuTu": ltdd.thuTu or 1
        }
        result["LICHTRINH_DIADIEM"].append(lich_trinh_dia_diem_data)
    
    return result


def format_state_to_json(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format state từ orchestrator thành JSON structure
    
    Args:
        state: State dictionary từ orchestrator
        
    Returns:
        Dict với keys: LICHTRINH, DIADIEM, LICHTRINH_DIADIEM, PHUONGTIEN_GIAOTHONG, HOATDONG
    """
    result = {
        "LICHTRINH": [],
        "DIADIEM": [],
        "LICHTRINH_DIADIEM": [],
        "PHUONGTIEN_GIAOTHONG": [],
        "HOATDONG": []
    }
    
    # Extract info from state
    origin = state.get('origin', '')
    destination = state.get('destination', '')
    days = state.get('days', 1)
    travelers = state.get('travelers', 2)
    travel_style = state.get('travel_style', 'standard')
    start_date = state.get('start_date', '')
    total_cost = state.get('total_cost', state.get('max_budget', 0))
    
    # Format travel style
    if isinstance(travel_style, list):
        travel_style_str = '_'.join(travel_style)
    else:
        travel_style_str = str(travel_style)
    
    # Create title
    if origin and destination:
        title = f"{origin} – {destination} {days} ngày ({travel_style_str})"
    elif destination:
        title = f"{destination} {days} ngày ({travel_style_str})"
    else:
        title = f"Lịch trình {days} ngày"
    
    # Format LICHTRINH - chỉ lấy thông tin cơ bản, không bổ sung chi tiết
    lich_trinh_data = {
        "maLichTrinh": 1,  # Temporary ID
        "tenLichTrinh": title,
        "soNgay": days,
        "soNguoi": travelers,
        "phongCach": travel_style_str,
        "diemXuatPhat": origin,
        "diemDen": destination,
        "ngayBatDau": start_date if start_date else None,
        "ngayKetThuc": _calculate_end_date(start_date, days) if start_date else None,
        "tongChiPhiDuKien": int(total_cost),
        "trangThai": "active"
    }
    result["LICHTRINH"].append(lich_trinh_data)
    
    # Extract activities from itinerary
    itinerary = state.get('itinerary', {})
    itinerary_days = []
    
    if isinstance(itinerary, dict):
        # Check for 'itinerary' key (from create_full_itinerary)
        if 'itinerary' in itinerary:
            itinerary_days = itinerary['itinerary']
        # Check if it's a daily schedule structure
        elif 'schedule' in itinerary:
            itinerary_days = itinerary['schedule']
        # Check if keys are day numbers
        elif any(str(k).isdigit() for k in itinerary.keys()):
            # Sort by day number
            sorted_keys = sorted([k for k in itinerary.keys() if str(k).isdigit()], key=int)
            itinerary_days = [itinerary[k] for k in sorted_keys]
    elif isinstance(itinerary, list):
        itinerary_days = itinerary
    
    # Track unique places
    places_dict = {}
    place_id_counter = 1
    
    # Process each day
    for day_idx, day_plan in enumerate(itinerary_days, start=1):
        if not isinstance(day_plan, dict):
            continue
        
        # Get activities from day_plan
        # Activities can be in 'activities' key (list of activity dicts)
        # or in 'timeline' key (list of timeline items with activity_details)
        activities = day_plan.get('activities', [])
        timeline = day_plan.get('timeline', [])
        transportation = day_plan.get('transportation', [])  # Thông tin phương tiện di chuyển
        
        # If no activities, try to extract from timeline
        if not activities and timeline:
            for timeline_item in timeline:
                if timeline_item.get('type') == 'activity' and timeline_item.get('activity_details'):
                    activities.append({
                        'activity': timeline_item['activity_details'],
                        'time_slot': timeline_item.get('time', ''),
                        'description': timeline_item.get('description', '')
                    })
                # Extract transportation from timeline
                elif timeline_item.get('type') == 'transport' or timeline_item.get('transportation'):
                    transport_info = timeline_item.get('transportation') or timeline_item
                    if transport_info:
                        transportation.append(transport_info)
        
        if not activities:
            continue
        
        # Process each activity
        for activity_idx, activity in enumerate(activities, start=1):
            if not isinstance(activity, dict):
                continue
            
            # Get activity details - handle different structures
            activity_obj = {}
            if 'activity' in activity and isinstance(activity['activity'], dict):
                activity_obj = activity['activity']
            elif 'activity_details' in activity and isinstance(activity['activity_details'], dict):
                activity_obj = activity['activity_details']
            else:
                activity_obj = activity
            
            activity_name = activity_obj.get('name', '')
            if not activity_name:
                continue
            
            # Check if place already added
            place_key = activity_name.lower().strip()
            if place_key not in places_dict:
                # Extract coordinates
                lat = activity_obj.get('latitude') or activity_obj.get('lat') or activity_obj.get('viDo')
                lon = activity_obj.get('longitude') or activity_obj.get('lon') or activity_obj.get('kinhDo') or activity_obj.get('lng')
                
                # Extract opening hours
                opening_hours = activity_obj.get('opening_hours', {})
                if isinstance(opening_hours, dict):
                    gio_mo_cua = opening_hours.get('open', '00:00')
                    gio_dong_cua = opening_hours.get('close', '23:59')
                elif isinstance(opening_hours, str):
                    # Try to parse "HH:MM-HH:MM" format
                    parts = opening_hours.split('-')
                    gio_mo_cua = parts[0].strip() if len(parts) > 0 else '00:00'
                    gio_dong_cua = parts[1].strip() if len(parts) > 1 else '23:59'
                else:
                    gio_mo_cua = '00:00'
                    gio_dong_cua = '23:59'
                
                # Extract features and amenities
                dac_diem = activity_obj.get('features', {})
                if isinstance(dac_diem, str):
                    try:
                        dac_diem = json.loads(dac_diem)
                    except:
                        dac_diem = {}
                
                tien_nghi = activity_obj.get('amenities', {})
                if isinstance(tien_nghi, str):
                    try:
                        tien_nghi = json.loads(tien_nghi)
                    except:
                        tien_nghi = {}
                
                # Add to DIADIEM - đảm bảo có đầy đủ thông tin
                dia_diem_data = {
                    "maDiaDiem": place_id_counter,
                    "tenDiaDiem": activity_name,
                    "moTa": activity_obj.get('description', activity.get('description', '')),
                    "diaChi": activity_obj.get('address', activity_obj.get('diaChi', activity_obj.get('location', ''))),
                    "maTinhThanh": None,  # Will be filled if available
                    "loaiDiaDiem": activity_obj.get('type', activity_obj.get('loaiDiaDiem', activity_obj.get('category', 'giai_tri'))),
                    "viDo": float(lat) if lat is not None else None,
                    "kinhDo": float(lon) if lon is not None else None,
                    "giaVe": int(activity_obj.get('cost_vnd', activity_obj.get('giaVe', activity_obj.get('price', activity_obj.get('price_per_person', 0))))),
                    "gioMoCua": gio_mo_cua,
                    "gioDongCua": gio_dong_cua,
                    "dienThoai": activity_obj.get('phone', activity_obj.get('dienThoai', activity_obj.get('contact', ''))),
                    "website": activity_obj.get('website', activity_obj.get('url', '')),
                    "danhGiaTrungBinh": float(activity_obj.get('rating', activity_obj.get('danhGiaTrungBinh', activity_obj.get('score', 0)))),
                    "soLuotDanhGia": activity_obj.get('reviews', activity_obj.get('soLuotDanhGia', activity_obj.get('review_count', 0))),
                    "soLuotXem": activity_obj.get('views', activity_obj.get('soLuotXem', 0)),
                    "maNguoiTao": None,
                    "ngayTao": None,
                    "lanCapNhatCuoi": None,
                    "trangThai": "active",
                    "dacDiem": json.dumps(dac_diem) if dac_diem else None,
                    "tienNghi": json.dumps(tien_nghi) if tien_nghi else None,
                    # Thêm các thông tin bổ sung
                    "thoiGianThamQuan": activity_obj.get('duration_hours', activity_obj.get('duration', 2.0)),
                    "thoiGianTotNhat": activity_obj.get('best_time', activity_obj.get('best_visit_time', '')),
                    "ghiChu": activity_obj.get('notes', activity_obj.get('tips', ''))
                }
                result["DIADIEM"].append(dia_diem_data)
                places_dict[place_key] = place_id_counter
                place_id_counter += 1
            
            # Extract thời gian từ timeline hoặc activity
            thoi_gian_bat_dau = None
            thoi_gian_ket_thuc = None
            thoi_gian_tham_quan = None
            
            # Tìm thời gian từ timeline
            if timeline:
                for timeline_item in timeline:
                    if timeline_item.get('type') == 'activity':
                        activity_details = timeline_item.get('activity_details') or timeline_item.get('activity')
                        if isinstance(activity_details, dict) and activity_details.get('name') == activity_name:
                            time_str = timeline_item.get('time', '')
                            if time_str:
                                thoi_gian_bat_dau = time_str
                                # Tính thời gian kết thúc dựa trên duration
                                duration = activity_obj.get('duration_hours', activity_obj.get('duration', 2.0))
                                if isinstance(duration, (int, float)):
                                    try:
                                        # Parse time string (HH:MM)
                                        if ':' in time_str:
                                            hour, minute = map(int, time_str.split(':'))
                                            end_minutes = hour * 60 + minute + int(duration * 60)
                                            end_hour = end_minutes // 60
                                            end_min = end_minutes % 60
                                            thoi_gian_ket_thuc = f"{end_hour:02d}:{end_min:02d}"
                                    except:
                                        pass
            
            # Nếu không tìm thấy từ timeline, thử từ activity
            if not thoi_gian_bat_dau:
                thoi_gian_bat_dau = activity.get('time_slot') or activity.get('time')
            
            # Format thời gian tham quan (HH:MM - HH:MM)
            if thoi_gian_bat_dau and thoi_gian_ket_thuc:
                thoi_gian_tham_quan = f"{thoi_gian_bat_dau} - {thoi_gian_ket_thuc}"
            elif thoi_gian_bat_dau:
                # Chỉ có thời gian bắt đầu, ước tính kết thúc
                duration = activity_obj.get('duration_hours', activity_obj.get('duration', 2.0))
                if isinstance(duration, (int, float)) and ':' in str(thoi_gian_bat_dau):
                    try:
                        hour, minute = map(int, str(thoi_gian_bat_dau).split(':'))
                        end_minutes = hour * 60 + minute + int(duration * 60)
                        end_hour = end_minutes // 60
                        end_min = end_minutes % 60
                        thoi_gian_ket_thuc = f"{end_hour:02d}:{end_min:02d}"
                        thoi_gian_tham_quan = f"{thoi_gian_bat_dau} - {thoi_gian_ket_thuc}"
                    except:
                        pass
            
            # Add to LICHTRINH_DIADIEM với thông tin thời gian đầy đủ
            lich_trinh_dia_diem_data = {
                "maLichTrinh": 1,
                "maDiaDiem": places_dict[place_key],
                "ngayThu": day_idx,
                "thuTu": activity_idx,
                "thoiGianBatDau": thoi_gian_bat_dau,
                "thoiGianKetThuc": thoi_gian_ket_thuc,
                "thoiGianThamQuan": thoi_gian_tham_quan,  # Format: "HH:MM - HH:MM"
                "loaiHoatDong": activity_obj.get('type', activity_obj.get('category', 'sightseeing')),
                "ghiChu": activity.get('description', activity_obj.get('notes', ''))
            }
            result["LICHTRINH_DIADIEM"].append(lich_trinh_dia_diem_data)
    
    # Thêm thông tin phương tiện giao thông vào JSON nếu có
    transport_info = state.get('transport', {})
    transport_breakdown = state.get('transport_breakdown', {})
    flight_info = state.get('flight', {})
    
    if transport_info or transport_breakdown or flight_info:
        # Thông tin di chuyển chính (từ origin đến destination)
        if transport_info:
            transport_data = {
                "loaiPhuongTien": transport_info.get('suggested_method', ''),
                "diemXuatPhat": state.get('origin', ''),
                "diemDen": state.get('destination', ''),
                "khoangCach": float(transport_info.get('distance_km', 0)),
                "thoiGian": float(transport_info.get('duration_minutes', 0)),
                "chiPhi": int(transport_info.get('estimated_cost_vnd', 0)),
                "chiTiet": transport_breakdown
            }
            result['PHUONGTIEN_GIAOTHONG'].append(transport_data)
        
        # Thông tin chuyến bay nếu có
        if flight_info:
            flight_data = {
                "loaiPhuongTien": "may_bay",
                "diemXuatPhat": flight_info.get('origin_airport', ''),
                "diemDen": flight_info.get('destination_airport', ''),
                "hangHangKhong": flight_info.get('airline', ''),
                "soHieuChuyenBay": flight_info.get('flight_number', ''),
                "gioKhoiHanh": flight_info.get('departure_time', ''),
                "gioDen": flight_info.get('arrival_time', ''),
                "chiPhi": int(flight_info.get('price_vnd', 0)),
                "chiTiet": flight_info
            }
            result['PHUONGTIEN_GIAOTHONG'].append(flight_data)
    
    # Thêm danh sách hoạt động (activities) vào JSON
    activities_list = state.get('activities', [])
    if activities_list:
        for idx, activity in enumerate(activities_list, start=1):
            activity_data = {
                "maHoatDong": idx,
                "tenHoatDong": activity.get('name', ''),
                "moTa": activity.get('description', ''),
                "loaiHoatDong": activity.get('type', activity.get('category', '')),
                "diaChi": activity.get('address', ''),
                "viDo": float(activity.get('latitude', activity.get('lat', 0))) if activity.get('latitude') or activity.get('lat') else None,
                "kinhDo": float(activity.get('longitude', activity.get('lon', activity.get('lng', 0)))) if activity.get('longitude') or activity.get('lon') or activity.get('lng') else None,
                "giaVe": int(activity.get('price_per_person', activity.get('price', activity.get('cost_vnd', 0)))),
                "thoiGianThamQuan": activity.get('duration_hours', 2.0),
                "gioMoCua": activity.get('opening_hours', {}).get('open', '00:00') if isinstance(activity.get('opening_hours'), dict) else '00:00',
                "gioDongCua": activity.get('opening_hours', {}).get('close', '23:59') if isinstance(activity.get('opening_hours'), dict) else '23:59',
                "danhGia": float(activity.get('rating', 0)),
                "soLuotDanhGia": activity.get('reviews', 0),
                "dacDiem": activity.get('features', {}),
                "tienNghi": activity.get('amenities', {})
            }
            result['HOATDONG'].append(activity_data)
    
    return result


def _extract_travel_style(title: str) -> str:
    """Extract travel style from title"""
    title_lower = title.lower()
    styles = ['shopping_giai_tri', 'van_hoa', 'thien_nhien', 'am_thuc', 'budget', 'luxury', 'standard']
    for style in styles:
        if style in title_lower:
            return style
    return 'standard'


def _extract_origin(title: str) -> str:
    """Extract origin from title (format: "Origin – Destination ...")"""
    if '–' in title:
        parts = title.split('–', 1)
        return parts[0].strip()
    return ""


def _calculate_end_date(start_date: str, days: int) -> Optional[str]:
    """Calculate end date from start date and days"""
    try:
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = start + timedelta(days=days - 1)
        return end.strftime('%Y-%m-%d')
    except (ValueError, TypeError):
        return None


def generate_itinerary_description(
    json_data: Dict[str, Any],
    llm=None,
    force_llm: bool = True
) -> str:
    """
    Sử dụng LLM để tạo mô tả lịch trình từ JSON data
    
    Args:
        json_data: Dict với keys LICHTRINH, DIADIEM, LICHTRINH_DIADIEM
        llm: LLM instance (optional, sẽ tự lấy nếu None)
        force_llm: Nếu True, sẽ force enable LLM để generate description (mặc định: True)
        
    Returns:
        Văn bản mô tả lịch trình
    """
    if llm is None:
        # Luôn force enable LLM cho description generation
        if force_llm:
            from tools.planning_tools import get_llm_candidates

            candidates = get_llm_candidates()
        else:
            from tools.planning_tools import get_llm
            llm = get_llm()
            candidates = []
    else:
        if force_llm:
            from tools.planning_tools import get_llm_candidates
            candidates = get_llm_candidates()
        else:
            candidates = []
    
    if llm is None:
        logger.warning("LLM not available, returning basic description")
        return _generate_basic_description(json_data)
    
    # Format JSON data as string
    lichtrinh_json = json.dumps(json_data.get("LICHTRINH", []), ensure_ascii=False, indent=2)
    diadiem_json = json.dumps(json_data.get("DIADIEM", []), ensure_ascii=False, indent=2)
    lichtrinh_diadiem_json = json.dumps(json_data.get("LICHTRINH_DIADIEM", []), ensure_ascii=False, indent=2)
    phuongtien_json = json.dumps(json_data.get("PHUONGTIEN_GIAOTHONG", []), ensure_ascii=False, indent=2)
    hoatdong_json = json.dumps(json_data.get("HOATDONG", []), ensure_ascii=False, indent=2)
    
    # Create prompt với yêu cầu chi tiết về thời gian và thông tin địa điểm
    prompt = f"""Nhiệm vụ:

Hãy chuyển đổi dữ liệu lịch trình du lịch được cung cấp trong các bảng JSON (LICHTRINH, DIADIEM, LICHTRINH_DIADIEM, PHUONGTIEN_GIAOTHONG, HOATDONG) thành một bản mô tả lịch trình hoàn chỉnh dưới dạng văn bản tự nhiên. Văn phong hướng tới người dùng cuối, rõ ràng, mạch lạc, dễ hình dung. Không được trả về cấu trúc JSON, chỉ mô tả thuần văn.

YÊU CẦU BẮT BUỘC:

1. CHIA THEO TỪNG NGÀY:
   - Viết theo trình tự: Ngày 1 → Ngày 2 → ... → Ngày N
   - Mỗi ngày phải có tiêu đề rõ ràng: "NGÀY [SỐ]: [Ngày cụ thể] - [Chủ đề nếu có]"
   - Ghi rõ thời gian bắt đầu và kết thúc của ngày (nếu có trong dữ liệu)

2. CHIA THEO THỜI GIAN TRONG MỖI NGÀY:
   - Sắp xếp các hoạt động theo thứ tự thời gian (từ sáng đến tối)
   - Mỗi hoạt động PHẢI có khung giờ cụ thể: "[HH:MM - HH:MM] Tên hoạt động"
   - Sử dụng thông tin từ LICHTRINH_DIADIEM (thoiGianThamQuan) để xác định thời gian
   - Nếu không có thời gian cụ thể, ước tính dựa trên thứ tự (thuTu) và thời gian tham quan (thoiGianThamQuan)

3. THÔNG TIN CHI TIẾT CHO MỖI ĐỊA ĐIỂM TRONG KHUNG GIỜ:
   Với mỗi địa điểm trong khung giờ, cần bao gồm ĐẦY ĐỦ các thông tin sau:
   - **Tên địa điểm**: Từ DIADIEM.tenDiaDiem
   - **Địa chỉ**: Từ DIADIEM.diaChi (nếu có)
   - **Mô tả**: Từ DIADIEM.moTa (mô tả chi tiết về địa điểm)
   - **Giờ mở cửa/đóng cửa**: Từ DIADIEM.gioMoCua và DIADIEM.gioDongCua (nếu có)
   - **Giá vé**: Từ DIADIEM.giaVe (nếu có, ghi rõ "Miễn phí" nếu giá = 0)
   - **Thời gian tham quan đề xuất**: Từ DIADIEM.thoiGianThamQuan (ghi rõ số giờ)
   - **Thời gian tốt nhất để ghé thăm**: Từ DIADIEM.thoiGianTotNhat (nếu có)
   - **Đánh giá**: Từ DIADIEM.danhGiaTrungBinh (nếu có, ghi dạng "X.X/5 sao")
   - **Số lượt đánh giá**: Từ DIADIEM.soLuotDanhGia (nếu có)
   - **Lý do nên ghé thăm**: Dựa trên mô tả và đặc điểm của địa điểm
   - **Lưu ý**: Từ DIADIEM.ghiChu (nếu có) hoặc các lưu ý quan trọng khác

4. THÔNG TIN PHƯƠNG TIỆN DI CHUYỂN:
   - Sử dụng thông tin từ PHUONGTIEN_GIAOTHONG
   - Ghi rõ phương tiện di chuyển giữa các điểm
   - Thời gian di chuyển (nếu có)
   - Chi phí di chuyển (nếu có)

5. HOẠT ĐỘNG TỰ CHỌN:
   - Nếu có "Thời gian tự do" hoặc "Hoạt động cá nhân", ghi rõ khung giờ
   - Gợi ý các hoạt động phù hợp với phong cách du lịch

6. CUỐI BÀI:
   - Nhận xét tổng quan về lịch trình
   - Tổng hợp chi phí (từ LICHTRINH.tongChiPhiDuKien)
   - Gợi ý phương tiện di chuyển tổng thể
   - Các lưu ý quan trọng (thời tiết, trang phục, đồ dùng, v.v.)

Văn phong mềm mại, gợi hình, tự nhiên như một bài hướng dẫn du lịch chi tiết.

Dữ liệu đầu vào:

LICHTRINH:
{lichtrinh_json}

DIADIEM:
{diadiem_json}

LICHTRINH_DIADIEM:
{lichtrinh_diadiem_json}

PHUONGTIEN_GIAOTHONG:
{phuongtien_json}

HOATDONG:
{hoatdong_json}

Đầu ra mong muốn:

Một bản lịch trình hoàn chỉnh, CHIA THEO NGÀY VÀ THỜI GIAN, chỉ gồm văn xuôi mô tả.

Format mẫu cho mỗi ngày:
NGÀY 1: [Ngày cụ thể] - [Chủ đề]
Thời gian: [HH:MM] - [HH:MM]

[HH:MM - HH:MM] [Tên hoạt động]
📍 **Địa điểm**: [Tên địa điểm]
- **Địa chỉ**: [Địa chỉ]
- **Mô tả**: [Mô tả chi tiết]
- **Giờ mở cửa**: [Giờ mở cửa] - [Giờ đóng cửa]
- **Giá vé**: [Giá vé] VNĐ (hoặc "Miễn phí")
- **Thời gian tham quan đề xuất**: [X] giờ
- **Thời gian tốt nhất**: [Thời gian tốt nhất]
- **Đánh giá**: [X.X]/5 sao ([X] lượt đánh giá)
- **Lý do nên ghé thăm**: [Lý do]
- **Lưu ý**: [Lưu ý]

[Di chuyển: Phương tiện, thời gian, chi phí]

[HH:MM - HH:MM] [Hoạt động tiếp theo]
...

Không viết thêm JSON.
Không được bịa dữ liệu ngoài những gì đã cung cấp (ngoại trừ câu chuyển ý, lời mô tả tự nhiên).

Bắt đầu tạo hướng dẫn lịch trình chi tiết."""
    
    try_candidates: List[Dict[str, Any]] = []
    if llm is not None:
        try_candidates.append({"name": "provided", "type": "langchain", "client": llm})
    try_candidates.extend(candidates)

    deduped_candidates: List[Dict[str, Any]] = []
    seen_signatures = set()
    for candidate in try_candidates:
        signature = (
            candidate.get("name"),
            candidate.get("type"),
            candidate.get("model"),
        )
        if signature in seen_signatures:
            continue
        seen_signatures.add(signature)
        deduped_candidates.append(candidate)
    try_candidates = deduped_candidates

    if not try_candidates:
        logger.warning("LLM not available, returning basic description")
        return _generate_basic_description(json_data)

    from tools.planning_tools import invoke_candidate_text

    errors: List[str] = []
    for candidate in try_candidates:
        candidate_name = candidate.get("name", "unknown")
        try:
            description = invoke_candidate_text(candidate, prompt, temperature=0.7)
            logger.info("Generated itinerary description using provider: %s", candidate_name)
            return description
        except Exception as e:
            logger.warning("Description generation failed with provider %s: %s", candidate_name, e)
            errors.append(f"{candidate_name}: {e}")

    logger.error("All itinerary description providers failed: %s", " | ".join(errors))
    return _generate_basic_description(json_data)


def _generate_basic_description(json_data: Dict[str, Any]) -> str:
    """Generate basic description without LLM"""
    lichtrinh = json_data.get("LICHTRINH", [{}])[0]
    diadiem_list = json_data.get("DIADIEM", [])
    lichtrinh_diadiem = json_data.get("LICHTRINH_DIADIEM", [])
    
    title = lichtrinh.get("tenLichTrinh", "Lịch trình du lịch")
    days = lichtrinh.get("soNgay", 1)
    destination = lichtrinh.get("diemDen", "")
    
    description = f"# {title}\n\n"
    description += f"Lịch trình du lịch {days} ngày đến {destination}.\n\n"
    
    # Group by day
    by_day = {}
    for item in lichtrinh_diadiem:
        day = item.get("ngayThu", 1)
        if day not in by_day:
            by_day[day] = []
        by_day[day].append(item)
    
    # Sort days
    for day in sorted(by_day.keys()):
        description += f"## Ngày {day}\n\n"
        items = sorted(by_day[day], key=lambda x: x.get("thuTu", 0))
        
        for item in items:
            place_id = item.get("maDiaDiem")
            place = next((p for p in diadiem_list if p.get("maDiaDiem") == place_id), None)
            if place:
                description += f"### {place.get('tenDiaDiem', '')}\n"
                if place.get('moTa'):
                    description += f"{place['moTa']}\n\n"
                if place.get('giaVe', 0) > 0:
                    description += f"Giá vé: {place['giaVe']:,} VNĐ\n\n"
    
    return description

