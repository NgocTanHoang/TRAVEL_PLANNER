"""
OpenSky Network API Tools
==========================
API để theo dõi chuyến bay theo thời gian thực (flight tracking)

Tài liệu: https://openskynetwork.github.io/opensky-api/rest.html

Authentication Methods:
1. HTTP Basic Auth (Username/Password):
   - Đăng ký tại: https://opensky-network.org/
   - Sử dụng username và password
   
2. OAuth2 Client Credentials Flow (Recommended):
   - Đăng ký và tạo API client tại: https://opensky-network.org/
   - Sử dụng client_id và client_secret
   - Lấy access token từ auth endpoint
   - Sử dụng Bearer token cho API calls

Rate Limits:
- Anonymous: Rất hạn chế
- OpenSky Users: Nhiều lượt hơn (tùy plan)
"""
import logging
import requests
import os
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import time

logger = logging.getLogger(__name__)

# Import cache utility
try:
    from utils.cache import cache_get, cache_set
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False
    logger.warning("Cache utility not available, OpenSky API calls will not be cached")


class OpenSkyTools:
    """Công cụ tương tác với OpenSky Network API"""
    
    BASE_URL = "https://opensky-network.org/api"
    AUTH_URL = "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token"
    
    def __init__(self):
        # OAuth2 Credentials (Preferred)
        self.client_id = os.getenv('OPENSKY_CLIENT_ID', '')
        self.client_secret = os.getenv('OPENSKY_CLIENT_SECRET', '')
        
        # Basic Auth Credentials (Fallback)
        self.username = os.getenv('OPENSKY_USERNAME', '')
        self.password = os.getenv('OPENSKY_PASSWORD', '')
        
        # Access token cache
        self._access_token = None
        self._token_expires_at = 0
        
        # Setup authentication
        if self.client_id and self.client_secret:
            logger.info("OpenSky API: Using OAuth2 authentication")
            self.auth_type = 'oauth2'
        elif self.username and self.password:
            logger.info("OpenSky API: Using Basic Auth")
            self.auth_type = 'basic'
            self.auth = (self.username, self.password)
        else:
            logger.warning("OpenSky API: Using anonymous access (limited rate)")
            self.auth_type = 'anonymous'
            self.auth = None
    
    def _get_access_token(self) -> Optional[str]:
        """
        Lấy OAuth2 access token
        
        Returns:
            Access token hoặc None nếu lỗi
        """
        # Kiểm tra token cache
        if self._access_token and time.time() < self._token_expires_at:
            return self._access_token
        
        if not self.client_id or not self.client_secret:
            return None
        
        try:
            response = requests.post(
                self.AUTH_URL,
                data={
                    'grant_type': 'client_credentials',
                    'client_id': self.client_id,
                    'client_secret': self.client_secret
                },
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                self._access_token = data.get('access_token')
                expires_in = data.get('expires_in', 3600)  # Default 1 hour
                self._token_expires_at = time.time() + expires_in - 60  # Refresh 1 min trước khi hết hạn
                logger.info("OpenSky API: OAuth2 token obtained")
                return self._access_token
            else:
                logger.error(f"OpenSky API: Failed to get token: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"OpenSky API: Token request error: {e}")
            return None
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """
        Lấy authentication headers cho request
        
        Returns:
            Dict chứa headers
        """
        if self.auth_type == 'oauth2':
            token = self._get_access_token()
            if token:
                return {'Authorization': f'Bearer {token}'}
        elif self.auth_type == 'basic':
            return {}  # Auth sẽ được truyền qua auth parameter
        
        return {}
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None, timeout: int = 10) -> Dict[str, Any]:
        """
        Thực hiện request đến OpenSky API
        
        Args:
            endpoint: API endpoint (ví dụ: '/states/all')
            params: Query parameters
            timeout: Request timeout
            
        Returns:
            Response dict hoặc empty dict nếu lỗi
        """
        url = f"{self.BASE_URL}{endpoint}"
        headers = self._get_auth_headers()
        
        try:
            response = requests.get(
                url,
                params=params,
                headers=headers,
                auth=self.auth if self.auth_type == 'basic' else None,
                timeout=timeout
            )
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                logger.warning(f"OpenSky API: No data found for {endpoint}")
                return {}
            elif response.status_code == 429:
                logger.warning("OpenSky API: Rate limit exceeded")
                return {'error': 'rate_limit_exceeded'}
            else:
                logger.error(f"OpenSky API error {response.status_code}: {response.text[:200]}")
                return {'error': f'http_{response.status_code}'}
                
        except Exception as e:
            logger.error(f"OpenSky API request error: {e}")
            return {'error': str(e)}
    
    def get_flights_by_airport(
        self,
        airport_code: str,
        begin_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        flight_type: str = 'departure'
    ) -> Dict[str, Any]:
        """
        Lấy danh sách chuyến bay từ/sẽ đến một sân bay
        
        Args:
            airport_code: Mã ICAO của sân bay (ví dụ: 'VVNB' cho Nội Bài, 'VVTS' cho Tân Sơn Nhất)
            begin_time: Thời gian bắt đầu (Unix timestamp hoặc datetime)
            end_time: Thời gian kết thúc (Unix timestamp hoặc datetime)
            flight_type: 'departure' hoặc 'arrival'
            
        Returns:
            Dict chứa danh sách chuyến bay hoặc error
        """
        # Convert datetime to Unix timestamp nếu cần
        if isinstance(begin_time, datetime):
            begin_ts = int(begin_time.timestamp())
        elif isinstance(begin_time, (int, float)):
            begin_ts = int(begin_time)
        else:
            # Default: 2 giờ trước đến hiện tại
            end_ts = int(time.time())
            begin_ts = end_ts - 7200  # 2 giờ
        
        if isinstance(end_time, datetime):
            end_ts = int(end_time.timestamp())
        elif isinstance(end_time, (int, float)):
            end_ts = int(end_time)
        else:
            end_ts = int(time.time())
        
        # Validate time interval (không quá 2 ngày)
        if end_ts - begin_ts > 172800:  # 2 days = 172800 seconds
            logger.warning("OpenSky API: Time interval too large (max 2 days)")
            return {'error': 'time_interval_too_large'}
        
        # Create cache key
        cache_key = f"opensky:{flight_type}:{airport_code}:{begin_ts}:{end_ts}"
        
        # Check cache (TTL: 1 giờ cho historical data, 5 phút cho real-time)
        if CACHE_AVAILABLE:
            cached_result = cache_get(cache_key)
            if cached_result:
                logger.info(f"OpenSky API cache hit for {flight_type} at {airport_code}")
                return cached_result
        
        # Choose endpoint
        endpoint = '/flights/departure' if flight_type == 'departure' else '/flights/arrival'
        
        params = {
            'airport': airport_code.upper(),
            'begin': begin_ts,
            'end': end_ts
        }
        
        result = self._make_request(endpoint, params)
        
        # Cache result
        if CACHE_AVAILABLE and result and 'error' not in result:
            # Cache historical data longer than real-time
            ttl = 3600 if (time.time() - end_ts) > 3600 else 300  # 1 hour or 5 minutes
            cache_set(cache_key, result, ttl=ttl)
        
        return result
    
    def get_flights_in_interval(
        self,
        begin_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Lấy tất cả chuyến bay trong khoảng thời gian
        
        Args:
            begin_time: Thời gian bắt đầu
            end_time: Thời gian kết thúc
            
        Returns:
            Dict chứa danh sách chuyến bay
        """
        # Convert datetime to Unix timestamp
        if isinstance(begin_time, datetime):
            begin_ts = int(begin_time.timestamp())
        elif isinstance(begin_time, (int, float)):
            begin_ts = int(begin_time)
        else:
            # Default: 1 giờ trước đến hiện tại
            end_ts = int(time.time())
            begin_ts = end_ts - 3600
        
        if isinstance(end_time, datetime):
            end_ts = int(end_time.timestamp())
        elif isinstance(end_time, (int, float)):
            end_ts = int(end_time)
        else:
            end_ts = int(time.time())
        
        # Validate time interval (không quá 2 giờ)
        if end_ts - begin_ts > 7200:  # 2 hours = 7200 seconds
            logger.warning("OpenSky API: Time interval too large (max 2 hours)")
            return {'error': 'time_interval_too_large'}
        
        cache_key = f"opensky:flights_all:{begin_ts}:{end_ts}"
        
        # Check cache
        if CACHE_AVAILABLE:
            cached_result = cache_get(cache_key)
            if cached_result:
                return cached_result
        
        params = {
            'begin': begin_ts,
            'end': end_ts
        }
        
        result = self._make_request('/flights/all', params)
        
        # Cache result
        if CACHE_AVAILABLE and result and 'error' not in result:
            ttl = 3600 if (time.time() - end_ts) > 3600 else 300
            cache_set(cache_key, result, ttl=ttl)
        
        return result
    
    def get_aircraft_track(
        self,
        icao24: str,
        track_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Lấy trajectory (quỹ đạo) của một máy bay
        
        Args:
            icao24: ICAO 24-bit address của máy bay (hex string, lowercase)
            track_time: Thời gian để lấy track (0 = live track, hoặc Unix timestamp)
            
        Returns:
            Dict chứa track information
        """
        if isinstance(track_time, datetime):
            time_ts = int(track_time.timestamp())
        elif isinstance(track_time, (int, float)):
            time_ts = int(track_time)
        else:
            time_ts = 0  # Live track
        
        cache_key = f"opensky:track:{icao24}:{time_ts}"
        
        # Check cache (TTL ngắn cho live track)
        if CACHE_AVAILABLE and time_ts > 0:  # Chỉ cache historical tracks
            cached_result = cache_get(cache_key)
            if cached_result:
                return cached_result
        
        params = {
            'icao24': icao24.lower(),
            'time': time_ts
        }
        
        result = self._make_request('/tracks', params)
        
        # Cache historical tracks only
        if CACHE_AVAILABLE and result and 'error' not in result and time_ts > 0:
            cache_set(cache_key, result, ttl=3600)
        
        return result
    
    def get_state_vectors(
        self,
        icao24: Optional[str] = None,
        bbox: Optional[Dict[str, float]] = None,
        time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Lấy state vectors (thông tin máy bay theo thời gian thực)
        
        Args:
            icao24: ICAO 24-bit address (optional)
            bbox: Bounding box {lamin, lomin, lamax, lomax} (optional)
            time: Thời gian cụ thể (optional, default: current time)
            
        Returns:
            Dict chứa state vectors
        """
        params = {}
        
        if icao24:
            params['icao24'] = icao24.lower()
        
        if bbox:
            params.update({
                'lamin': bbox.get('lamin'),
                'lomin': bbox.get('lomin'),
                'lamax': bbox.get('lamax'),
                'lomax': bbox.get('lomax')
            })
        
        if isinstance(time, datetime):
            params['time'] = int(time.timestamp())
        elif isinstance(time, (int, float)):
            params['time'] = int(time)
        
        # Cache key
        cache_key = f"opensky:states:{str(params)}"
        
        # Check cache (TTL ngắn cho real-time data)
        if CACHE_AVAILABLE:
            cached_result = cache_get(cache_key)
            if cached_result:
                return cached_result
        
        result = self._make_request('/states/all', params)
        
        # Cache với TTL ngắn (30 giây cho real-time data)
        if CACHE_AVAILABLE and result and 'error' not in result:
            cache_set(cache_key, result, ttl=30)
        
        return result
    
    def search_flights_by_route(
        self,
        origin_icao: str,
        dest_icao: str,
        begin_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Tìm chuyến bay giữa hai sân bay
        
        Args:
            origin_icao: Mã ICAO sân bay đi
            dest_icao: Mã ICAO sân bay đến
            begin_time: Thời gian bắt đầu
            end_time: Thời gian kết thúc
            
        Returns:
            List các chuyến bay matching
        """
        # Lấy departures từ origin
        departures = self.get_flights_by_airport(
            origin_icao,
            begin_time,
            end_time,
            'departure'
        )
        
        # Lấy arrivals tại dest
        arrivals = self.get_flights_by_airport(
            dest_icao,
            begin_time,
            end_time,
            'arrival'
        )
        
        if not departures or not arrivals:
            return []
        
        # Tìm matches dựa trên callsign hoặc icao24
        matches = []
        
        dep_dict = {}
        for dep in departures:
            key = dep.get('callsign', '').strip() or dep.get('icao24', '')
            if key:
                dep_dict[key] = dep
        
        for arr in arrivals:
            key = arr.get('callsign', '').strip() or arr.get('icao24', '')
            if key in dep_dict:
                matches.append({
                    'departure': dep_dict[key],
                    'arrival': arr,
                    'icao24': key,
                    'callsign': arr.get('callsign', '')
                })
        
        return matches


# Singleton instance
_opensky_tools = None

def get_opensky_tools() -> OpenSkyTools:
    """Get singleton OpenSkyTools instance"""
    global _opensky_tools
    if _opensky_tools is None:
        _opensky_tools = OpenSkyTools()
    return _opensky_tools

