"""
Data Standardization Utilities
Chuẩn hóa định dạng dữ liệu: date, currency, address, category
"""
import re
import logging
from typing import Dict, Any, Optional, Union
from datetime import datetime
from decimal import Decimal, InvalidOperation

logger = logging.getLogger(__name__)


class DateStandardizer:
    """Chuẩn hóa định dạng ngày tháng"""
    
    # Các format phổ biến
    DATE_FORMATS = [
        '%Y-%m-%d',           # 2024-01-15
        '%d/%m/%Y',           # 15/01/2024
        '%d-%m-%Y',           # 15-01-2024
        '%Y/%m/%d',           # 2024/01/15
        '%d.%m.%Y',           # 15.01.2024
        '%m/%d/%Y',           # 01/15/2024 (US format)
    ]
    
    @staticmethod
    def standardize(date_str: Optional[str], output_format: str = '%Y-%m-%d') -> Optional[str]:
        """
        Chuẩn hóa date string về format chuẩn.
        
        Args:
            date_str: Date string (various formats)
            output_format: Format mong muốn (default: ISO '%Y-%m-%d')
        
        Returns:
            Date string trong format chuẩn hoặc None nếu invalid
        """
        if not date_str:
            return None
        
        if isinstance(date_str, datetime):
            return date_str.strftime(output_format)
        
        date_str = str(date_str).strip()
        
        # Thử parse với các format
        for fmt in DateStandardizer.DATE_FORMATS:
            try:
                dt = datetime.strptime(date_str, fmt)
                return dt.strftime(output_format)
            except (ValueError, TypeError):
                continue
        
        # Thử parse tự động
        try:
            dt = datetime.fromisoformat(date_str.replace('/', '-').replace('.', '-'))
            return dt.strftime(output_format)
        except (ValueError, TypeError):
            pass
        
        logger.warning(f"Could not standardize date: {date_str}")
        return None
    
    @staticmethod
    def is_valid(date_str: Optional[str]) -> bool:
        """Check if date string is valid"""
        return DateStandardizer.standardize(date_str) is not None


class CurrencyStandardizer:
    """Chuẩn hóa định dạng tiền tệ"""
    
    # Currency codes
    VND = 'VND'
    USD = 'USD'
    EUR = 'EUR'
    
    # Exchange rates (có thể lấy từ API trong tương lai)
    EXCHANGE_RATES = {
        'USD': 24000.0,  # VND per USD
        'EUR': 26000.0,  # VND per EUR
    }
    
    @staticmethod
    def standardize(
        price: Union[str, int, float, Decimal],
        source_currency: str = 'VND',
        target_currency: str = 'VND'
    ) -> Optional[Dict[str, Any]]:
        """
        Chuẩn hóa giá tiền về format chuẩn.
        
        Args:
            price: Giá tiền (có thể có currency symbol hoặc text)
            source_currency: Currency của input (default: VND)
            target_currency: Currency mong muốn (default: VND)
        
        Returns:
            Dict với 'amount' (float), 'currency' (str), 'original' (str)
            hoặc None nếu invalid
        """
        if price is None:
            return None
        
        # Convert sang string để parse
        price_str = str(price).strip()
        
        # Remove currency symbols và text
        # VND: "đ", "vnđ", "dong", "VND"
        # USD: "$", "usd", "dollar"
        currency_patterns = {
            'VND': [r'đ', r'vnđ', r'dong', r'vnd', r'₫'],
            'USD': [r'\$', r'usd', r'dollar'],
            'EUR': [r'€', r'eur', r'euro']
        }
        
        detected_currency = source_currency
        
        # Detect currency từ symbols
        for curr, patterns in currency_patterns.items():
            for pattern in patterns:
                if re.search(pattern, price_str, re.IGNORECASE):
                    detected_currency = curr
                    break
        
        # Extract số từ string
        # Remove tất cả non-digit characters trừ dấu chấm và phẩy
        numbers = re.sub(r'[^\d.,]', '', price_str)
        # Replace comma with dot (nếu có)
        numbers = numbers.replace(',', '.')
        
        try:
            # Parse số
            if '.' in numbers:
                amount = float(numbers)
            else:
                amount = float(numbers)
            
            # Convert sang target currency nếu cần
            if detected_currency != target_currency:
                if detected_currency in CurrencyStandardizer.EXCHANGE_RATES:
                    # Convert to VND first
                    if detected_currency != 'VND':
                        amount_vnd = amount * CurrencyStandardizer.EXCHANGE_RATES[detected_currency]
                    else:
                        amount_vnd = amount
                    
                    # Convert to target
                    if target_currency != 'VND':
                        amount = amount_vnd / CurrencyStandardizer.EXCHANGE_RATES[target_currency]
                    else:
                        amount = amount_vnd
                else:
                    logger.warning(f"Unknown source currency: {detected_currency}")
            
            # Round to 2 decimal places
            amount = round(float(amount), 2)
            
            return {
                'amount': amount,
                'currency': target_currency,
                'original': price_str,
                'source_currency': detected_currency
            }
            
        except (ValueError, InvalidOperation) as e:
            logger.warning(f"Could not parse price: {price_str}, error: {e}")
            return None
    
    @staticmethod
    def format_vnd(amount: float) -> str:
        """Format VND với dấu phẩy ngăn cách"""
        return f"{amount:,.0f} VND"
    
    @staticmethod
    def format_usd(amount: float) -> str:
        """Format USD với 2 decimal places"""
        return f"${amount:,.2f}"


class AddressStandardizer:
    """Chuẩn hóa định dạng địa chỉ"""
    
    # Vietnamese address components
    STREET_PREFIXES = ['đường', 'phố', 'ngõ', 'ngách', 'hẻm', 'tổ', 'khu phố']
    WARD_TYPES = ['phường', 'xã', 'thị trấn']
    DISTRICT_TYPES = ['quận', 'huyện', 'thành phố', 'thị xã']
    CITY_TYPES = ['thành phố', 'tỉnh']
    
    @staticmethod
    def standardize(address: Optional[str]) -> Optional[Dict[str, Any]]:
        """
        Chuẩn hóa địa chỉ Việt Nam về format chuẩn.
        
        Args:
            address: Địa chỉ string
        
        Returns:
            Dict với các component: 'street', 'ward', 'district', 'city', 'formatted'
            hoặc None nếu invalid
        """
        if not address:
            return None
        
        address = str(address).strip()
        
        # Normalize Vietnamese text
        address = AddressStandardizer._normalize_text(address)
        
        # Parse components (basic parsing)
        components = {
            'street': '',
            'ward': '',
            'district': '',
            'city': '',
            'formatted': address,
            'original': address
        }
        
        # Try to extract city (thường ở cuối)
        for city_type in AddressStandardizer.CITY_TYPES:
            pattern = rf'({city_type}\s+[^,]+)'
            match = re.search(pattern, address, re.IGNORECASE)
            if match:
                components['city'] = match.group(1).strip()
                break
        
        # Try to extract district
        for district_type in AddressStandardizer.DISTRICT_TYPES:
            pattern = rf'({district_type}\s+[^,]+)'
            match = re.search(pattern, address, re.IGNORECASE)
            if match:
                components['district'] = match.group(1).strip()
                break
        
        # Try to extract ward
        for ward_type in AddressStandardizer.WARD_TYPES:
            pattern = rf'({ward_type}\s+[^,]+)'
            match = re.search(pattern, address, re.IGNORECASE)
            if match:
                components['ward'] = match.group(1).strip()
                break
        
        # Street thường ở đầu
        # Remove city, district, ward để lấy street
        temp = address
        if components['city']:
            temp = temp.replace(components['city'], '').strip()
        if components['district']:
            temp = temp.replace(components['district'], '').strip()
        if components['ward']:
            temp = temp.replace(components['ward'], '').strip()
        
        components['street'] = temp.strip().rstrip(',').strip()
        
        # Format: street, ward, district, city
        parts = [p for p in [
            components['street'],
            components['ward'],
            components['district'],
            components['city']
        ] if p]
        
        components['formatted'] = ', '.join(parts)
        
        return components
    
    @staticmethod
    def _normalize_text(text: str) -> str:
        """Normalize Vietnamese text"""
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        # Remove leading/trailing spaces
        text = text.strip()
        # Capitalize first letter of each word
        words = text.split()
        words = [w.capitalize() for w in words]
        return ' '.join(words)


class CategoryStandardizer:
    """Chuẩn hóa category/label"""
    
    # Category mappings
    CATEGORY_MAPPINGS = {
        # Accommodation
        'khách sạn': 'khach_san',
        'hotel': 'khach_san',
        'resort': 'khach_san',
        'homestay': 'khach_san',
        'nhà nghỉ': 'khach_san',
        
        # Restaurant
        'nhà hàng': 'nha_hang',
        'restaurant': 'nha_hang',
        'quán ăn': 'nha_hang',
        'café': 'nha_hang',
        'cafe': 'nha_hang',
        'quán cà phê': 'nha_hang',
        
        # Attraction
        'địa danh': 'dia_danh',
        'attraction': 'dia_danh',
        'di tích': 'dia_danh',
        'cảnh đẹp': 'dia_danh',
        'viewpoint': 'dia_danh',
        
        # Entertainment
        'giải trí': 'giai_tri',
        'entertainment': 'giai_tri',
        'khu vui chơi': 'giai_tri',
        'amusement': 'giai_tri',
        
        # Shopping
        'mua sắm': 'mua_sam',
        'shopping': 'mua_sam',
        'chợ': 'mua_sam',
        'market': 'mua_sam',
        
        # Other
        'khác': 'khac',
        'other': 'khac',
        'others': 'khac',
    }
    
    @staticmethod
    def standardize(category: Optional[str]) -> Optional[str]:
        """
        Chuẩn hóa category về format chuẩn.
        
        Args:
            category: Category string (various formats)
        
        Returns:
            Standardized category code hoặc None
        """
        if not category:
            return None
        
        category_lower = str(category).strip().lower()
        
        # Check direct mapping
        if category_lower in CategoryStandardizer.CATEGORY_MAPPINGS:
            return CategoryStandardizer.CATEGORY_MAPPINGS[category_lower]
        
        # Check partial match
        for key, value in CategoryStandardizer.CATEGORY_MAPPINGS.items():
            if key in category_lower or category_lower in key:
                return value
        
        # If already in standard format, return as is
        valid_categories = ['khach_san', 'nha_hang', 'dia_danh', 'giai_tri', 'mua_sam', 'khac']
        if category_lower in valid_categories:
            return category_lower
        
        # Default to 'khac'
        logger.warning(f"Unknown category: {category}, defaulting to 'khac'")
        return 'khac'


class DataStandardizer:
    """Main class để chuẩn hóa dữ liệu"""
    
    @staticmethod
    def standardize_place_data(place_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Chuẩn hóa toàn bộ place data.
        
        Args:
            place_data: Dict chứa place information
        
        Returns:
            Dict đã được chuẩn hóa
        """
        standardized = place_data.copy()
        
        # Standardize date fields
        date_fields = ['ngayTao', 'ngayCapNhat', 'ngayMoCua', 'ngayDongCua']
        for field in date_fields:
            if field in standardized:
                standardized[field] = DateStandardizer.standardize(standardized[field])
        
        # Standardize price
        price_fields = ['giaVe', 'giaThamKhao', 'giaTrungBinh']
        for field in price_fields:
            if field in standardized:
                price_result = CurrencyStandardizer.standardize(standardized[field])
                if price_result:
                    standardized[field] = price_result['amount']
                    standardized[f'{field}_currency'] = price_result['currency']
        
        # Standardize address
        if 'diaChi' in standardized:
            addr_result = AddressStandardizer.standardize(standardized['diaChi'])
            if addr_result:
                standardized['diaChi'] = addr_result['formatted']
                standardized['diaChi_street'] = addr_result.get('street', '')
                standardized['diaChi_ward'] = addr_result.get('ward', '')
                standardized['diaChi_district'] = addr_result.get('district', '')
                standardized['diaChi_city'] = addr_result.get('city', '')
        
        # Standardize category
        if 'loaiDiaDiem' in standardized:
            standardized['loaiDiaDiem'] = CategoryStandardizer.standardize(
                standardized['loaiDiaDiem']
            )
        
        return standardized

