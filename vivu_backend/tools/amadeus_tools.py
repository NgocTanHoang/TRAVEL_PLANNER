"""
Amadeus API Tools - Công cụ sử dụng Amadeus API
================================================
Sử dụng Amadeus Self-Service API để tìm kiếm chuyến bay và khách sạn
"""
import os
import logging
from typing import Dict, List, Optional, Any
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

# Kiểm tra xem có thư viện amadeus không
try:
    from amadeus import Client, ResponseError
    AMADEUS_AVAILABLE = True
except ImportError:
    AMADEUS_AVAILABLE = False
    logger.warning("amadeus package not installed. Install with: pip install amadeus")


class AmadeusTools:
    """Công cụ sử dụng Amadeus API"""
    
    def __init__(self):
        self.api_key = os.getenv('AMADEUS_API_KEY', '')
        self.api_secret = os.getenv('AMADEUS_API_SECRET', '')
        self.environment = os.getenv('AMADEUS_ENVIRONMENT', 'test')  # 'test' or 'production'
        
        if not self.api_key or not self.api_secret:
            logger.warning("Amadeus API credentials not set. Set AMADEUS_API_KEY and AMADEUS_API_SECRET in .env")
            self.client = None
        elif not AMADEUS_AVAILABLE:
            logger.warning("amadeus package not installed. Amadeus API will be disabled.")
            self.client = None
        else:
            try:
                # Tạo client với test environment
                self.client = Client(
                    client_id=self.api_key,
                    client_secret=self.api_secret,
                    hostname='test' if self.environment == 'test' else 'production'
                )
                logger.info(f"Amadeus API client initialized (environment: {self.environment})")
            except Exception as e:
                logger.error(f"Failed to initialize Amadeus client: {e}")
                self.client = None
    
    def is_available(self) -> bool:
        """Kiểm tra xem Amadeus API có khả dụng không"""
        return self.client is not None
    
    def search_flights(
        self,
        origin: str,
        destination: str,
        departure_date: str,
        return_date: Optional[str] = None,
        adults: int = 1,
        children: int = 0,
        infants: int = 0
    ) -> Dict[str, Any]:
        """
        Tìm kiếm chuyến bay qua Amadeus API
        
        Args:
            origin: Mã sân bay đi (IATA code, e.g., 'SGN', 'HAN')
            destination: Mã sân bay đến (IATA code)
            departure_date: Ngày đi (YYYY-MM-DD)
            return_date: Ngày về (YYYY-MM-DD, optional)
            adults: Số người lớn
            children: Số trẻ em
            infants: Số em bé
            
        Returns:
            Dict với flights data hoặc error
        """
        if not self.client:
            return {
                'error': 'Amadeus API not configured',
                'flights': [],
                'status': 'error'
            }
        
        try:
            params = {
                'originLocationCode': origin.upper(),
                'destinationLocationCode': destination.upper(),
                'departureDate': departure_date,
                'adults': adults
            }
            
            if return_date:
                params['returnDate'] = return_date
            
            if children > 0:
                params['children'] = children
            
            if infants > 0:
                params['infants'] = infants
            
            logger.info(f"Searching Amadeus flights: {origin}->{destination} on {departure_date}")
            response = self.client.shopping.flight_offers_search.get(**params)
            
            # Parse response
            flights = []
            if response.data:
                for offer in response.data:
                    # Lấy giá
                    price = float(offer['price']['total'])
                    currency = offer['price']['currency']
                    
                    # Convert sang VND nếu cần
                    if currency != 'VND':
                        # Tỷ giá ước tính (có thể cải thiện bằng API tỷ giá thực)
                        if currency == 'USD':
                            price_vnd = price * 25000
                        elif currency == 'EUR':
                            price_vnd = price * 28000
                        else:
                            price_vnd = price * 25000  # Default USD rate
                    else:
                        price_vnd = price
                    
                    # Lấy thông tin chuyến bay
                    itineraries = offer.get('itineraries', [])
                    segments = []
                    if itineraries:
                        for itinerary in itineraries:
                            for segment in itinerary.get('segments', []):
                                segments.append({
                                    'departure': {
                                        'iataCode': segment['departure']['iataCode'],
                                        'at': segment['departure']['at']
                                    },
                                    'arrival': {
                                        'iataCode': segment['arrival']['iataCode'],
                                        'at': segment['arrival']['at']
                                    },
                                    'carrierCode': segment.get('carrierCode', ''),
                                    'number': segment.get('number', ''),
                                    'duration': segment.get('duration', '')
                                })
                    
                    flights.append({
                        'id': offer.get('id', ''),
                        'price': price_vnd,
                        'price_original': price,
                        'currency': currency,
                        'price_vnd': int(price_vnd),
                        'segments': segments,
                        'numberOfBookableSeats': offer.get('numberOfBookableSeats', 0),
                        'source': 'amadeus'
                    })
            
            return {
                'status': 'success',
                'flights': flights,
                'source': 'amadeus',
                'count': len(flights)
            }
            
        except ResponseError as error:
            logger.error(f"Amadeus API ResponseError: {error.description} (Code: {error.response.status_code})")
            return {
                'error': error.description,
                'status_code': error.response.status_code,
                'flights': [],
                'status': 'error'
            }
        except Exception as e:
            logger.error(f"Amadeus API error: {e}")
            return {
                'error': str(e),
                'flights': [],
                'status': 'error'
            }
    
    def search_hotels(
        self,
        city_code: str,
        check_in: str,
        check_out: str,
        adults: int = 2
    ) -> Dict[str, Any]:
        """
        Tìm kiếm khách sạn qua Amadeus API
        
        Args:
            city_code: Mã thành phố (IATA code, e.g., 'HAN', 'SGN')
            check_in: Ngày nhận phòng (YYYY-MM-DD)
            check_out: Ngày trả phòng (YYYY-MM-DD)
            adults: Số người lớn
            
        Returns:
            Dict với hotels data hoặc error
        """
        if not self.client:
            return {
                'error': 'Amadeus API not configured',
                'hotels': [],
                'status': 'error'
            }
        
        try:
            # Bước 1: Tìm hotel IDs trong thành phố
            logger.info(f"Searching Amadeus hotels in {city_code}")
            hotel_ids_response = self.client.reference_data.locations.hotels.by_city.get(
                cityCode=city_code.upper()
            )
            
            if not hotel_ids_response.data:
                return {
                    'status': 'success',
                    'hotels': [],
                    'source': 'amadeus',
                    'count': 0
                }
            
            hotel_ids = [hotel['hotelId'] for hotel in hotel_ids_response.data[:10]]  # Lấy 10 hotel đầu
            
            if not hotel_ids:
                return {
                    'status': 'success',
                    'hotels': [],
                    'source': 'amadeus',
                    'count': 0
                }
            
            # Bước 2: Tìm offers cho các hotels
            offers_response = self.client.shopping.hotel_offers_search.get(
                hotelIds=','.join(hotel_ids),
                checkInDate=check_in,
                checkOutDate=check_out,
                adults=adults
            )
            
            # Parse response
            hotels = []
            if offers_response.data:
                for hotel_data in offers_response.data:
                    hotel_info = hotel_data.get('hotel', {})
                    offers = hotel_data.get('offers', [])
                    
                    if offers:
                        # Lấy offer đầu tiên (rẻ nhất)
                        best_offer = offers[0]
                        price = float(best_offer['price']['total'])
                        currency = best_offer['price']['currency']
                        
                        # Convert sang VND
                        if currency != 'VND':
                            if currency == 'USD':
                                price_vnd = price * 25000
                            elif currency == 'EUR':
                                price_vnd = price * 28000
                            else:
                                price_vnd = price * 25000
                        else:
                            price_vnd = price
                        
                        hotels.append({
                            'hotelId': hotel_data.get('hotelId', ''),
                            'name': hotel_info.get('name', 'Unknown'),
                            'rating': hotel_info.get('rating', 0),
                            'price_per_night': int(price_vnd),
                            'price_original': price,
                            'currency': currency,
                            'address': hotel_info.get('address', {}),
                            'latitude': hotel_info.get('geoCode', {}).get('latitude'),
                            'longitude': hotel_info.get('geoCode', {}).get('longitude'),
                            'source': 'amadeus'
                        })
            
            return {
                'status': 'success',
                'hotels': hotels,
                'source': 'amadeus',
                'count': len(hotels)
            }
            
        except ResponseError as error:
            logger.error(f"Amadeus API ResponseError: {error.description} (Code: {error.response.status_code})")
            return {
                'error': error.description,
                'status_code': error.response.status_code,
                'hotels': [],
                'status': 'error'
            }
        except Exception as e:
            logger.error(f"Amadeus API error: {e}")
            return {
                'error': str(e),
                'hotels': [],
                'status': 'error'
            }


# Singleton instance
_amadeus_tools = None

def get_amadeus_tools() -> AmadeusTools:
    """Get singleton AmadeusTools instance"""
    global _amadeus_tools
    if _amadeus_tools is None:
        _amadeus_tools = AmadeusTools()
    return _amadeus_tools





