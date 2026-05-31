"""
Utility functions to save itinerary to database
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from django.db import transaction
from apps.itineraries.models import LichTrinh, LichTrinhDiaDiem
from apps.places.models import DiaDiem, TinhThanh
from django.contrib.auth import get_user_model
from utils.security import ensure_sensitive_log_filter, sanitize_sensitive_string

User = get_user_model()
logger = logging.getLogger(__name__)
ensure_sensitive_log_filter(logger)


def normalize_destination_name(dest: str) -> str:
    """Normalize destination name for matching"""
    dest = dest.lower().strip()
    # Map common variations
    mappings = {
        'cần thơ': 'Cần Thơ',
        'can tho': 'Cần Thơ',
        'cantho': 'Cần Thơ',
    }
    return mappings.get(dest, dest.title())


def find_tinh_thanh_by_name(destination: str) -> Optional[TinhThanh]:
    """Find TinhThanh by destination name"""
    try:
        normalized = normalize_destination_name(destination)
        # Try exact match first
        tinh_thanh = TinhThanh.objects.filter(tenTinhThanh__iexact=normalized).first()
        if tinh_thanh:
            return tinh_thanh
        
        # Try contains match
        tinh_thanh = TinhThanh.objects.filter(tenTinhThanh__icontains=normalized).first()
        if tinh_thanh:
            return tinh_thanh
        
        logger.warning(f"Could not find TinhThanh for destination: {destination}")
        return None
    except Exception as e:
        logger.error(f"Error finding TinhThanh: {e}")
        return None


def find_dia_diem_by_name(name: str, tinh_thanh: Optional[TinhThanh] = None) -> Optional[DiaDiem]:
    """Find DiaDiem by name, optionally filtered by TinhThanh"""
    try:
        query = DiaDiem.objects.filter(tenDiaDiem__icontains=name, trangThai='active')
        if tinh_thanh:
            query = query.filter(maTinhThanh=tinh_thanh)
        
        # Try exact match first
        dia_diem = query.filter(tenDiaDiem__iexact=name).first()
        if dia_diem:
            return dia_diem
        
        # Try contains match
        dia_diem = query.first()
        if dia_diem:
            return dia_diem
        
        logger.debug(f"Could not find DiaDiem: {name} in {tinh_thanh.tenTinhThanh if tinh_thanh else 'any city'}")
        return None
    except Exception as e:
        logger.error(f"Error finding DiaDiem: {e}")
        return None


def save_itinerary_to_database(
    itinerary_data: Dict[str, Any],
    user: Optional[User] = None,
    destination: str = None,
    origin: str = None,
    start_date: str = None,
    days: int = None,
    travelers: int = 2,
    travel_style: str = 'standard',
    total_cost: float = 0
) -> Optional[LichTrinh]:
    """
    Save itinerary to database
    
    Args:
        itinerary_data: Itinerary data from planning agent
        user: User who created the itinerary
        destination: Destination city
        origin: Origin city
        start_date: Start date (YYYY-MM-DD)
        days: Number of days
        travelers: Number of travelers
        travel_style: Travel style
        total_cost: Total estimated cost
        
    Returns:
        LichTrinh object if successful, None otherwise
    """
    try:
        with transaction.atomic():
            # Find TinhThanh for destination
            tinh_thanh = None
            if destination:
                tinh_thanh = find_tinh_thanh_by_name(destination)
            
            # Parse start_date
            if start_date:
                try:
                    start = datetime.strptime(start_date, '%Y-%m-%d').date()
                except ValueError:
                    logger.error(f"Invalid start_date format: {start_date}")
                    start = datetime.now().date()
            else:
                start = datetime.now().date()
            
            # Calculate end_date
            if days:
                end = start + timedelta(days=days - 1)
            else:
                end = start
            
            # Create title
            if origin and destination:
                title = f"{origin} – {destination} {days} ngày ({travel_style})"
            elif destination:
                title = f"{destination} {days} ngày ({travel_style})"
            else:
                title = f"Lịch trình {days} ngày"
            
            # Create LichTrinh
            lich_trinh = LichTrinh.objects.create(
                maNguoiDung=user,
                maTinhThanh=tinh_thanh,
                tieuDe=title,
                moTa=f"Lịch trình du lịch {days} ngày đến {destination}",
                ngayBatDau=start,
                ngayKetThuc=end,
                soNgay=days,
                soNguoi=travelers,
                nganSach=total_cost,
                chiPhiUocTinh=total_cost,
                trangThai='active',
                chiTiet=str(itinerary_data)  # Store full itinerary data as JSON string
            )
            lich_trinh = LichTrinh.objects.select_for_update().get(pk=lich_trinh.pk)
            
            logger.info(f"Created LichTrinh: {lich_trinh.maLichTrinh} - {lich_trinh.tieuDe}")
            
            # Extract activities from itinerary
            itinerary = itinerary_data.get('itinerary', [])
            if not itinerary and isinstance(itinerary_data, list):
                itinerary = itinerary_data
            
            # Process each day
            for day_idx, day_plan in enumerate(itinerary, start=1):
                if not isinstance(day_plan, dict):
                    continue
                
                # Get activities for this day
                activities = day_plan.get('activities', [])
                if not activities:
                    continue
                
                # Calculate date for this day
                day_date = start + timedelta(days=day_idx - 1)
                
                # Process each activity
                for activity_idx, activity in enumerate(activities, start=1):
                    if not isinstance(activity, dict):
                        continue
                    
                    # Get activity name
                    activity_name = None
                    if 'activity' in activity and isinstance(activity['activity'], dict):
                        activity_name = activity['activity'].get('name', '')
                    elif 'name' in activity:
                        activity_name = activity['name']
                    
                    if not activity_name:
                        continue
                    
                    # Find DiaDiem
                    dia_diem = find_dia_diem_by_name(activity_name, tinh_thanh)
                    if not dia_diem:
                        logger.debug(f"Skipping activity '{activity_name}' - not found in database")
                        continue
                    
                    # Create LichTrinhDiaDiem
                    try:
                        lich_trinh_dia_diem, created = LichTrinhDiaDiem.objects.update_or_create(
                            maLichTrinh=lich_trinh,
                            maDiaDiem=dia_diem,
                            ngayThamQuan=day_date,
                            defaults={
                                'thuTu': activity_idx,
                                'thoiGianThamQuan': activity.get('time_slot', ''),
                                'ghiChu': activity.get('description', ''),
                                'chiPhiUocTinh': activity.get('price_per_person', 0) * travelers if activity.get('price_per_person') else 0
                            }
                        )
                        if created:
                            logger.debug(f"Created LichTrinhDiaDiem: {dia_diem.tenDiaDiem} on day {day_idx}")
                    except Exception as e:
                        logger.warning("Error creating LichTrinhDiaDiem: %s", sanitize_sensitive_string(str(e)))
                        continue
            
            logger.info(f"Successfully saved itinerary {lich_trinh.maLichTrinh} with {LichTrinhDiaDiem.objects.filter(maLichTrinh=lich_trinh).count()} places")
            return lich_trinh
            
    except Exception as e:
        logger.error("Error saving itinerary to database: %s", sanitize_sensitive_string(str(e)), exc_info=True)
        return None






