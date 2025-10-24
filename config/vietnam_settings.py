# Vietnam Travel Planner Configuration
import os
from dotenv import load_dotenv

# Load environment variables
try:
    load_dotenv()
except:
    pass

# API Keys
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
TAVILY_API_KEY = os.getenv('TAVILY_API_KEY')

# Model settings
MODEL = 'gpt-4o-mini'
MAX_TURN = 7
MAX_TURN_10 = 10
TERMINATION_WORD = 'stop'

# Vietnam-specific settings
VIETNAM_DESTINATIONS = {
    "north": [
        "Hà Nội", "Hạ Long", "Sapa", "Ninh Bình", "Mai Châu", 
        "Cát Bà", "Mù Cang Chải", "Điện Biên Phủ"
    ],
    "central": [
        "Huế", "Hội An", "Đà Nẵng", "Quy Nhon", "Nha Trang", 
        "Phan Thiết", "Mũi Né", "Đà Lạt"
    ],
    "south": [
        "TP. Hồ Chí Minh", "Cần Thơ", "Cà Mau", "Phú Quốc", 
        "Côn Đảo", "Vũng Tàu", "Mỹ Tho", "Châu Đốc"
    ]
}

VIETNAM_TRANSPORTATION = {
    "domestic_flights": "Vietnam Airlines, VietJet Air, Bamboo Airways",
    "trains": "Tàu hỏa Bắc Nam, tàu Thống Nhất",
    "buses": "Xe khách liên tỉnh, xe giường nằm",
    "motorbikes": "Xe máy thuê, Grab Bike",
    "taxis": "Grab, Be, taxi truyền thống"
}

VIETNAM_CUISINE = {
    "north": ["Phở bò", "Bún chả", "Bánh cuốn", "Chả cá Lã Vọng", "Bún thang"],
    "central": ["Bún bò Huế", "Cơm hến", "Bánh xèo", "Nem lụi", "Chè Huế"],
    "south": ["Cơm tấm", "Bánh mì", "Hủ tiếu", "Bún mắm", "Chè ba màu"]
}

VIETNAM_CULTURAL_TIPS = {
    "greeting": "Chào hỏi bằng 'Xin chào' hoặc 'Chào anh/chị'",
    "respect": "Thể hiện sự tôn trọng với người lớn tuổi",
    "temples": "Mặc quần áo kín đáo khi vào chùa",
    "bargaining": "Có thể mặc cả ở chợ và một số cửa hàng",
    "currency": "Sử dụng VND, có thể đổi USD tại ngân hàng"
}
