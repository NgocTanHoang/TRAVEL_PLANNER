#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script kiểm tra và validate dữ liệu địa điểm
============================================
Chức năng:
1. Kiểm tra loại địa điểm đã đúng với đặc điểm hay chưa (dùng semantic classifier)
2. Sử dụng VietMap API để kiểm tra và update vị trí, địa chỉ
3. Update địa chỉ theo địa giới hành chính mới
4. Kiểm tra và update mô tả từ Wikipedia/DuckDuckGo
"""
import os
import sys
import django
import json
import time
from typing import Dict, Any, Optional, List
from pathlib import Path

# Fix encoding for Windows
if sys.platform == 'win32':
    import io
    if hasattr(sys.stdout, 'buffer'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    if hasattr(sys.stderr, 'buffer'):
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Setup Django
BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(BACKEND_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'vivu_core.settings')
django.setup()

from django.db import transaction
from apps.places.models import DiaDiem, TinhThanh
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from vivu_backend.utils.semantic_place_classifier import (
    understand_place_semantics,
    classify_place_by_semantics
)
from vivu_backend.tools.vietmap_tools import VietMapTools
from vivu_backend.apps.api.place_info_searcher import PlaceInfoSearcher

# Import normalize_province_name - copy function để tránh circular import
def normalize_province_name(name: str) -> str:
    """Chuẩn hóa tên tỉnh thành"""
    if not name:
        return name
    
    name = str(name).strip()
    
    # Mapping các tên thường gặp sang tên chuẩn
    normalization_map = {
        'Ho Chi Minh': 'TP. Hồ Chí Minh',
        'HCM': 'TP. Hồ Chí Minh',
        'Hồ Chí Minh': 'TP. Hồ Chí Minh',
        'Thành phố Hồ Chí Minh': 'TP. Hồ Chí Minh',
        'TP.HCM': 'TP. Hồ Chí Minh',
        'TP HCM': 'TP. Hồ Chí Minh',
        'Ha Noi': 'Hà Nội',
        'Hanoi': 'Hà Nội',
        'Thành phố Hà Nội': 'Hà Nội',
        'Da Nang': 'Đà Nẵng',
        'Danang': 'Đà Nẵng',
    }
    
    return normalization_map.get(name, name)


class PlaceValidator:
    """Class để validate và update dữ liệu địa điểm"""
    
    def __init__(self):
        self.vietmap = VietMapTools()
        self.place_searcher = PlaceInfoSearcher()
        self.stats = {
            'total_checked': 0,
            'type_corrected': 0,
            'location_updated': 0,
            'address_updated': 0,
            'description_updated': 0,
            'province_updated': 0,
            'errors': []
        }
    
    def validate_place_type(self, dia_diem: DiaDiem) -> Dict[str, Any]:
        """
        Kiểm tra và sửa loại địa điểm nếu không đúng
        
        Returns:
            Dict với 'needs_update', 'old_type', 'new_type', 'confidence'
        """
        semantics = understand_place_semantics(
            name=dia_diem.tenDiaDiem,
            description=dia_diem.moTa or '',
            type_hint='',
            category=dia_diem.loaiDiaDiem
        )
        
        predicted_type = semantics['loaiDiaDiem']
        confidence = semantics['confidence']
        
        result = {
            'needs_update': False,
            'old_type': dia_diem.loaiDiaDiem,
            'new_type': predicted_type,
            'confidence': confidence
        }
        
        # Nếu loại hiện tại khác với loại dự đoán và confidence > 0.5
        if dia_diem.loaiDiaDiem != predicted_type and confidence > 0.5:
            result['needs_update'] = True
        
        return result
    
    def validate_location_with_vietmap(
        self,
        dia_diem: DiaDiem
    ) -> Dict[str, Any]:
        """
        Kiểm tra và update vị trí, địa chỉ bằng VietMap API
        
        Returns:
            Dict với thông tin cần update
        """
        result = {
            'needs_update': False,
            'updates': {}
        }
        
        if not self.vietmap.vietmap_api_key:
            return result
        
        try:
            # Nếu có tọa độ, dùng reverse geocoding để kiểm tra địa chỉ
            if dia_diem.viDo and dia_diem.kinhDo:
                reverse_result = self.vietmap.reverse_geocode(
                    float(dia_diem.viDo),
                    float(dia_diem.kinhDo)
                )
                
                if reverse_result and reverse_result.get('formatted_address'):
                    new_address = reverse_result['formatted_address']
                    # So sánh với địa chỉ hiện tại
                    if new_address and new_address != dia_diem.diaChi:
                        result['needs_update'] = True
                        result['updates']['diaChi'] = new_address
                        # Extract tỉnh thành từ địa chỉ mới
                        province_name = self._extract_province_from_address(new_address)
                        if province_name:
                            result['updates']['province_name'] = province_name
            
            # Nếu có địa chỉ, dùng geocoding để kiểm tra tọa độ
            if dia_diem.diaChi:
                geocode_result = self.vietmap.geocode(dia_diem.diaChi)
                
                if geocode_result:
                    new_lat = geocode_result.get('lat')
                    new_lon = geocode_result.get('lon')
                    
                    # Kiểm tra xem tọa độ có khác nhiều không (sai lệch > 100m)
                    if new_lat and new_lon:
                        if not dia_diem.viDo or not dia_diem.kinhDo:
                            # Chưa có tọa độ, thêm mới
                            result['needs_update'] = True
                            result['updates']['viDo'] = new_lat
                            result['updates']['kinhDo'] = new_lon
                        else:
                            # Tính khoảng cách (Haversine formula đơn giản)
                            distance = self._calculate_distance(
                                float(dia_diem.viDo), float(dia_diem.kinhDo),
                                new_lat, new_lon
                            )
                            if distance > 0.1:  # > 100m
                                result['needs_update'] = True
                                result['updates']['viDo'] = new_lat
                                result['updates']['kinhDo'] = new_lon
                                result['updates']['distance_diff'] = distance
                    
                    # Update địa chỉ nếu có formatted_address tốt hơn
                    if geocode_result.get('formatted_address'):
                        formatted_addr = geocode_result['formatted_address']
                        if len(formatted_addr) > len(dia_diem.diaChi or ''):
                            result['needs_update'] = True
                            result['updates']['diaChi'] = formatted_addr
            
            # Thử geocode bằng tên địa điểm + tỉnh thành
            if not result['needs_update'] and dia_diem.tenDiaDiem:
                query = f"{dia_diem.tenDiaDiem}, {dia_diem.maTinhThanh.tenTinhThanh}"
                geocode_result = self.vietmap.geocode(query)
                
                if geocode_result:
                    new_lat = geocode_result.get('lat')
                    new_lon = geocode_result.get('lon')
                    
                    if new_lat and new_lon:
                        if not dia_diem.viDo or not dia_diem.kinhDo:
                            result['needs_update'] = True
                            result['updates']['viDo'] = new_lat
                            result['updates']['kinhDo'] = new_lon
                        else:
                            distance = self._calculate_distance(
                                float(dia_diem.viDo), float(dia_diem.kinhDo),
                                new_lat, new_lon
                            )
                            if distance > 0.5:  # > 500m
                                result['needs_update'] = True
                                result['updates']['viDo'] = new_lat
                                result['updates']['kinhDo'] = new_lon
                                result['updates']['distance_diff'] = distance
                
        except Exception as e:
            logger.error(f"Error validating location for {dia_diem.tenDiaDiem}: {e}")
            self.stats['errors'].append({
                'place': dia_diem.tenDiaDiem,
                'error': str(e),
                'type': 'location_validation'
            })
        
        return result
    
    def validate_description(
        self,
        dia_diem: DiaDiem
    ) -> Dict[str, Any]:
        """
        Kiểm tra và update mô tả từ Wikipedia/DuckDuckGo
        
        Returns:
            Dict với thông tin cần update
        """
        result = {
            'needs_update': False,
            'new_description': None,
            'source': None
        }
        
        try:
            # Tìm kiếm thông tin từ internet
            search_result = self.place_searcher.search_place_info(
                place_name=dia_diem.tenDiaDiem,
                city=dia_diem.maTinhThanh.tenTinhThanh
            )
            
            if search_result and search_result.get('description'):
                new_desc = search_result['description']
                current_desc = dia_diem.moTa or ''
                
                # Chỉ update nếu mô tả mới dài hơn và có ý nghĩa hơn
                if len(new_desc) > len(current_desc) + 50:  # Ít nhất dài hơn 50 ký tự
                    result['needs_update'] = True
                    result['new_description'] = new_desc
                    result['source'] = search_result.get('source', 'unknown')
        
        except Exception as e:
            logger.error(f"Error validating description for {dia_diem.tenDiaDiem}: {e}")
            self.stats['errors'].append({
                'place': dia_diem.tenDiaDiem,
                'error': str(e),
                'type': 'description_validation'
            })
        
        return result
    
    def _extract_province_from_address(self, address: str) -> Optional[str]:
        """Extract tỉnh thành từ địa chỉ"""
        if not address:
            return None
        
        # Lấy phần cuối của địa chỉ (thường là tỉnh thành)
        parts = address.split(',')
        if parts:
            province_candidate = parts[-1].strip()
            # Chuẩn hóa tên tỉnh thành
            normalized = normalize_province_name(province_candidate)
            
            # Kiểm tra xem có trong database không
            try:
                TinhThanh.objects.get(tenTinhThanh=normalized)
                return normalized
            except TinhThanh.DoesNotExist:
                pass
        
        return None
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Tính khoảng cách giữa 2 điểm (km) - Haversine formula"""
        from math import radians, sin, cos, sqrt, atan2
        
        R = 6371  # Bán kính Trái Đất (km)
        
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        
        a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        
        return R * c
    
    def validate_and_update_place(
        self,
        dia_diem: DiaDiem,
        update_type: bool = True,
        update_location: bool = True,
        update_description: bool = True,
        update_address: bool = True
    ) -> Dict[str, Any]:
        """
        Validate và update một địa điểm
        
        Returns:
            Dict với thông tin các thay đổi
        """
        changes = {
            'place_id': dia_diem.maDiaDiem,
            'place_name': dia_diem.tenDiaDiem,
            'updates': {}
        }
        
        # 1. Kiểm tra loại địa điểm
        if update_type:
            type_result = self.validate_place_type(dia_diem)
            if type_result['needs_update']:
                changes['updates']['loaiDiaDiem'] = {
                    'old': type_result['old_type'],
                    'new': type_result['new_type'],
                    'confidence': type_result['confidence']
                }
        
        # 2. Kiểm tra vị trí và địa chỉ
        if update_location or update_address:
            location_result = self.validate_location_with_vietmap(dia_diem)
            if location_result['needs_update']:
                updates = location_result['updates']
                if 'viDo' in updates:
                    changes['updates']['viDo'] = updates['viDo']
                if 'kinhDo' in updates:
                    changes['updates']['kinhDo'] = updates['kinhDo']
                if 'diaChi' in updates and update_address:
                    changes['updates']['diaChi'] = updates['diaChi']
                if 'province_name' in updates and update_address:
                    changes['updates']['province_name'] = updates['province_name']
        
        # 3. Kiểm tra mô tả
        if update_description:
            desc_result = self.validate_description(dia_diem)
            if desc_result['needs_update']:
                changes['updates']['moTa'] = {
                    'new': desc_result['new_description'],
                    'source': desc_result['source']
                }
        
        return changes
    
    def update_place_from_changes(
        self,
        dia_diem: DiaDiem,
        changes: Dict[str, Any]
    ) -> bool:
        """Update địa điểm từ changes dict"""
        if not changes.get('updates'):
            return False
        
        try:
            updates = changes['updates']
            
            # Update loại địa điểm
            if 'loaiDiaDiem' in updates:
                dia_diem.loaiDiaDiem = updates['loaiDiaDiem']['new']
                self.stats['type_corrected'] += 1
            
            # Update tọa độ
            if 'viDo' in updates:
                dia_diem.viDo = updates['viDo']
                self.stats['location_updated'] += 1
            if 'kinhDo' in updates:
                dia_diem.kinhDo = updates['kinhDo']
            
            # Update địa chỉ
            if 'diaChi' in updates:
                dia_diem.diaChi = updates['diaChi']
                self.stats['address_updated'] += 1
            
            # Update tỉnh thành
            if 'province_name' in updates:
                try:
                    new_province = TinhThanh.objects.get(tenTinhThanh=updates['province_name'])
                    dia_diem.maTinhThanh = new_province
                    self.stats['province_updated'] += 1
                except TinhThanh.DoesNotExist:
                    logger.warning(f"Province not found: {updates['province_name']}")
            
            # Update mô tả
            if 'moTa' in updates:
                dia_diem.moTa = updates['moTa']['new']
                self.stats['description_updated'] += 1
            
            dia_diem.save()
            return True
        
        except Exception as e:
            logger.error(f"Error updating place {dia_diem.tenDiaDiem}: {e}")
            self.stats['errors'].append({
                'place': dia_diem.tenDiaDiem,
                'error': str(e),
                'type': 'update'
            })
            return False


def validate_places_batch(
    limit: int = 100,
    offset: int = 0,
    update_type: bool = True,
    update_location: bool = True,
    update_description: bool = True,
    update_address: bool = True,
    dry_run: bool = False
):
    """
    Validate và update một batch địa điểm
    
    Args:
        limit: Số địa điểm cần kiểm tra
        offset: Offset để bắt đầu
        update_type: Có update loại địa điểm không
        update_location: Có update vị trí không
        update_description: Có update mô tả không
        update_address: Có update địa chỉ không
        dry_run: Chỉ kiểm tra, không update
    """
    validator = PlaceValidator()
    
    print("="*80)
    print("VALIDATE VÀ UPDATE ĐỊA ĐIỂM")
    print("="*80)
    print(f"Limit: {limit}, Offset: {offset}")
    print(f"Update type: {update_type}")
    print(f"Update location: {update_location}")
    print(f"Update description: {update_description}")
    print(f"Update address: {update_address}")
    print(f"Dry run: {dry_run}")
    print("="*80)
    
    # Lấy danh sách địa điểm
    places = DiaDiem.objects.filter(trangThai='active')[offset:offset+limit]
    total = places.count()
    
    print(f"\nĐang kiểm tra {total} địa điểm...\n")
    
    updated_count = 0
    with transaction.atomic():
        for i, place in enumerate(places, 1):
            validator.stats['total_checked'] += 1
            
            if i % 10 == 0:
                print(f"Đã kiểm tra {i}/{total} địa điểm...")
            
            # Validate
            changes = validator.validate_and_update_place(
                place,
                update_type=update_type,
                update_location=update_location,
                update_description=update_description,
                update_address=update_address
            )
            
            # Update nếu có thay đổi
            if changes.get('updates') and not dry_run:
                if validator.update_place_from_changes(place, changes):
                    updated_count += 1
                    print(f"✓ Updated: {place.tenDiaDiem[:50]}")
                    if 'loaiDiaDiem' in changes['updates']:
                        print(f"  - Type: {changes['updates']['loaiDiaDiem']['old']} → {changes['updates']['loaiDiaDiem']['new']}")
                    if 'diaChi' in changes['updates']:
                        print(f"  - Address updated")
                    if 'viDo' in changes['updates']:
                        print(f"  - Location updated")
                    if 'moTa' in changes['updates']:
                        print(f"  - Description updated from {changes['updates']['moTa']['source']}")
            elif changes.get('updates') and dry_run:
                print(f"[DRY RUN] Would update: {place.tenDiaDiem[:50]}")
                for key, value in changes['updates'].items():
                    print(f"  - {key}: {value}")
            
            # Delay để tránh rate limit
            time.sleep(0.5)
        
        if dry_run:
            transaction.set_rollback(True)
    
    # In thống kê
    print("\n" + "="*80)
    print("THỐNG KÊ")
    print("="*80)
    print(f"Tổng số địa điểm đã kiểm tra: {validator.stats['total_checked']}")
    print(f"Số địa điểm đã update: {updated_count}")
    print(f"Loại địa điểm đã sửa: {validator.stats['type_corrected']}")
    print(f"Vị trí đã update: {validator.stats['location_updated']}")
    print(f"Địa chỉ đã update: {validator.stats['address_updated']}")
    print(f"Mô tả đã update: {validator.stats['description_updated']}")
    print(f"Tỉnh thành đã update: {validator.stats['province_updated']}")
    print(f"Số lỗi: {len(validator.stats['errors'])}")
    
    if validator.stats['errors']:
        print("\nCác lỗi gặp phải:")
        for error in validator.stats['errors'][:10]:
            print(f"  - {error['place']}: {error['error']}")
        if len(validator.stats['errors']) > 10:
            print(f"  ... và {len(validator.stats['errors']) - 10} lỗi khác")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate và update địa điểm')
    parser.add_argument('--limit', type=int, default=100, help='Số địa điểm cần kiểm tra')
    parser.add_argument('--offset', type=int, default=0, help='Offset để bắt đầu')
    parser.add_argument('--no-type', action='store_true', help='Không update loại địa điểm')
    parser.add_argument('--no-location', action='store_true', help='Không update vị trí')
    parser.add_argument('--no-description', action='store_true', help='Không update mô tả')
    parser.add_argument('--no-address', action='store_true', help='Không update địa chỉ')
    parser.add_argument('--dry-run', action='store_true', help='Chỉ kiểm tra, không update')
    
    args = parser.parse_args()
    
    validate_places_batch(
        limit=args.limit,
        offset=args.offset,
        update_type=not args.no_type,
        update_location=not args.no_location,
        update_description=not args.no_description,
        update_address=not args.no_address,
        dry_run=args.dry_run
    )

