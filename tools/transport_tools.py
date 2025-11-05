"""
Transport Tools - Công cụ vận chuyển
=====================================
- Tính khoảng cách và thời gian di chuyển
- Đề xuất phương tiện phù hợp
- Tính chi phí vận chuyển nội địa (taxi, Grab, xe bus)
"""
import logging
from typing import Dict, Any, Optional, List
from .geo_tools import get_geo_tools

logger = logging.getLogger(__name__)


class TransportTools:
    """Công cụ vận chuyển cho Transport Agent"""
    
    # Bảng giá vận chuyển (VNĐ/km)
    TRANSPORT_RATES = {
        'taxi': 15000,  # 15k/km
        'grab': 12000,  # 12k/km
        'bus': 2000,    # 2k/km
        'train': 1500,  # 1.5k/km
    }
    
    # Ngưỡng khoảng cách để đề xuất phương tiện
    DISTANCE_THRESHOLDS = {
        'walking': 5,      # < 5km: đi bộ
        'taxi_grab': 50,   # < 50km: taxi/Grab
        'bus': 200,        # < 200km: xe bus
        'train': 500,      # < 500km: tàu hỏa
        'flight': 500,     # >= 500km: máy bay
    }
    
    def __init__(self):
        self.geo_tools = get_geo_tools()
    
    def suggest_transport(
        self,
        origin: str,
        destination: str,
        distance_km: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Đề xuất phương tiện vận chuyển
        
        Args:
            origin: Điểm xuất phát
            destination: Điểm đến
            distance_km: Khoảng cách (nếu đã biết, sẽ tính lại nếu None)
            
        Returns:
            Dict với 'method', 'distance_km', 'duration_minutes', 'estimated_cost'
        """
        if distance_km is None:
            route_info = self.geo_tools.calculate_distance_time(origin, destination)
            if not route_info:
                return {
                    'method': 'unknown',
                    'error': 'Cannot calculate distance'
                }
            distance_km = route_info['distance_km']
            duration_minutes = route_info['duration_minutes']
        else:
            # Ước tính thời gian (giả sử tốc độ trung bình)
            duration_minutes = distance_km * 1.5  # ~1.5 phút/km
        
        # Đề xuất phương tiện
        if distance_km < self.DISTANCE_THRESHOLDS['walking']:
            method = 'walking'
            cost = 0
        elif distance_km < self.DISTANCE_THRESHOLDS['taxi_grab']:
            method = 'taxi'  # Hoặc Grab
            cost = self._calculate_ground_transport_cost(distance_km, 'taxi')
        elif distance_km < self.DISTANCE_THRESHOLDS['bus']:
            method = 'bus'
            cost = self._calculate_ground_transport_cost(distance_km, 'bus')
        elif distance_km < self.DISTANCE_THRESHOLDS['train']:
            method = 'train'
            cost = self._calculate_ground_transport_cost(distance_km, 'train')
        else:
            method = 'flight'
            cost = None  # Để Flight Agent tính
        
        return {
            'method': method,
            'distance_km': round(distance_km, 2),
            'duration_minutes': round(duration_minutes, 1),
            'estimated_cost_vnd': cost,
            'origin': origin,
            'destination': destination
        }
    
    def _calculate_ground_transport_cost(
        self,
        distance_km: float,
        method: str
    ) -> float:
        """Tính chi phí vận chuyển nội địa"""
        rate = self.TRANSPORT_RATES.get(method, self.TRANSPORT_RATES['bus'])
        base_cost = distance_km * rate
        
        # Điều chỉnh theo phương tiện
        if method == 'taxi':
            # Taxi có phí mở cửa
            base_cost += 20000  # 20k phí mở cửa
        elif method == 'grab':
            base_cost += 15000  # 15k phí mở cửa
        
        return round(base_cost)
    
    def calculate_multi_hop_route(
        self,
        origin: str,
        destination: str,
        hubs: List[str] = None
    ) -> Dict[str, Any]:
        """
        Tính toán hành trình nhiều chặng
        
        Args:
            origin: Điểm xuất phát
            destination: Điểm đến
            hubs: Danh sách hub trung gian (nếu None, tự động đề xuất)
            
        Returns:
            Dict với thông tin từng chặng
        """
        # Hubs mặc định: Hà Nội, TP. Hồ Chí Minh, Đà Nẵng
        default_hubs = ['Hà Nội', 'TP. Hồ Chí Minh', 'Đà Nẵng']
        hubs = hubs or default_hubs
        
        route_info = self.geo_tools.calculate_distance_time(origin, destination)
        if not route_info:
            return {'error': 'Cannot calculate direct route'}
        
        direct_distance = route_info['distance_km']
        
        # Tìm hub gần nhất với điểm xuất phát và điểm đến
        # TODO: Implement logic tìm hub tốt nhất
        
        # Tạm thời return direct route
        return {
            'type': 'direct',
            'total_distance_km': direct_distance,
            'total_duration_minutes': route_info['duration_minutes'],
            'hops': [
                {
                    'from': origin,
                    'to': destination,
                    'distance_km': direct_distance,
                    'duration_minutes': route_info['duration_minutes'],
                    'method': self.suggest_transport(origin, destination, direct_distance)['method']
                }
            ]
        }


# Singleton instance
_transport_tools = None

def get_transport_tools() -> TransportTools:
    """Get singleton TransportTools instance"""
    global _transport_tools
    if _transport_tools is None:
        _transport_tools = TransportTools()
    return _transport_tools

