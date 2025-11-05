# 🎫 Vi Vu - AI-Powered Travel Planner

> **Plan in Minutes, Vibe for Months.**

Vi Vu là nền tảng lập kế hoạch du lịch thế hệ mới được hỗ trợ bởi Multi-Agent Systems (MAS), LangGraph, và RAG (Retrieval-Augmented Generation). Được xây dựng cho du lịch Việt Nam, sử dụng AI để tạo lịch trình cá nhân hóa, tối ưu chỉ trong vài phút.

**Inspired by [TripAppia](https://www.tripappia.com/)** với thiết kế UI/UX hiện đại và quy tắc màu sắc 60:30:10.

## ✨ Features

- **🤖 Multi-Agent System**: 10 specialized AI agents working in coordinated layers
- **🧠 RAG-Powered Recommendations**: Intelligent place recommendations using vector embeddings
- **📊 Smart Analytics**: Cost breakdowns, activity optimization, and trip insights
- **💬 AI Chat Assistant**: Natural language travel Q&A
- **🗺️ Auto-Generated Itineraries**: Day-by-day plans with timing and routes
- **📈 ML-Powered**: Sentiment analysis, price prediction, similarity matching

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (Streamlit)                     │
│              Plan Trip | Recommendations | Chat             │
└────────────────────────┬────────────────────────────────────┘
                         │ REST API
┌────────────────────────▼────────────────────────────────────┐
│                   DJANGO BACKEND                             │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │  REST API   │  │  AI Adapter  │  │  Data Models    │   │
│  │  Endpoints  │──│  (Celery)    │──│  (PostgreSQL)   │   │
│  └─────────────┘  └──────┬───────┘  └─────────────────┘   │
└────────────────────────────┼─────────────────────────────────┘
                            │
┌────────────────────────────▼─────────────────────────────────┐
│                  LANGGRAPH ORCHESTRATOR                       │
│                                                               │
│  Layer 1: Data Collection (parallel)                         │
│  ├─ APICollectorAgent                                        │
│  └─ WebScraperAgent                                          │
│                                                               │
│  Layer 2: Data Processing                                    │
│  └─ DataProcessorAgent                                       │
│                                                               │
│  Layer 3: ML Analysis (parallel)                             │
│  ├─ RecommendationAgent                                      │
│  ├─ SentimentAnalyzerAgent                                   │
│  ├─ SimilarityEngineAgent                                    │
│  └─ PricePredictorAgent                                      │
│                                                               │
│  Layer 4: Planning (parallel)                                │
│  ├─ PlannerAgent                                             │
│  └─ ResearcherAgent                                          │
│                                                               │
│  Layer 5: Analytics                                          │
│  └─ AnalyticsEngineAgent                                     │
└───────────────────────────┬───────────────────────────────────┘
                            │
┌────────────────────────────▼─────────────────────────────────┐
│                     RAG ENGINE                                │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │  Embeddings  │──│ Vector Store │──│  LLM (GPT-4)    │   │
│  │  (OpenAI)    │  │  (ChromaDB)  │  │                 │   │
│  └──────────────┘  └──────────────┘  └─────────────────┘   │
└───────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Yêu cầu

- Python 3.10+ (đã cài sẵn trong venv310)
- SQLite (đã có sẵn)
- Windows PowerShell hoặc Command Prompt

### Chạy Interactive Server (cho tương tác người dùng)

**Copy & paste lệnh này vào PowerShell:**
```powershell
cd "D:\KLTN\MAS (1)\MAS\TRAVEL_PLANNER"; ..\travel_env\Scripts\Activate.ps1; cd vivu_backend; python manage.py runserver
```

Hoặc từng bước:

```powershell
# 1. Di chuyển vào thư mục project
cd "D:\KLTN\MAS (1)\MAS\TRAVEL_PLANNER"

# 2. Kích hoạt virtual environment
..\travel_env\Scripts\Activate.ps1

# 3. Di chuyển vào backend
cd vivu_backend

# 4. Chạy interactive server
python manage.py runserver
```

**Server sẽ chạy tại:** http://127.0.0.1:8000

### Chạy Ingestion Jobs (offline processing)

Các agent nặng (API collector, web scraper, data processor) chỉ chạy nền:

```powershell
# Chạy ingestion script để populate vector database
cd TRAVEL_PLANNER
python scripts/populate_vector_db.py
```

Hoặc tạo script tùy chỉnh:

```python
# scripts/run_ingest.py
from agents.ingestion.api_collector import APICollectorAgent
from agents.ingestion.web_scraper import WebScraperAgent
from agents.ingestion.data_processor import DataProcessorAgent

# Chạy ingestion jobs offline
```

### Truy cập ứng dụng

- **Trang chủ**: http://127.0.0.1:8000/
- **Admin Panel**: http://127.0.0.1:8000/admin/ (admin / admin123)
- **API Documentation**: http://127.0.0.1:8000/api/docs/
- **API ReDoc**: http://127.0.0.1:8000/api/redoc/
- **API Endpoints**: http://127.0.0.1:8000/api/v1/

### Test APIs

```bash
# Mở terminal mới (trong khi server đang chạy)
cd "D:\KLTN\MAS (1)\MAS\TRAVEL_PLANNER\vivu_backend"
python test_api.py
```

### Kiểm tra cấu hình

```bash
cd "D:\KLTN\MAS (1)\MAS\TRAVEL_PLANNER\vivu_backend"
python check_config.py
```

## 📚 API Documentation

- **Swagger UI**: http://127.0.0.1:8000/api/docs/ - Interactive API testing
- **ReDoc**: http://127.0.0.1:8000/api/redoc/ - Beautiful API documentation
- **API Schema**: http://127.0.0.1:8000/api/schema/ - OpenAPI 3.0 schema

### API Endpoints

**Authentication**
```
POST /api/v1/auth/register/  - Đăng ký user mới
POST /api/v1/auth/login/     - Đăng nhập
```

**Places (Địa điểm)**
```
GET  /api/v1/places/         - Danh sách địa điểm (50,334)
GET  /api/v1/places/{id}/    - Chi tiết địa điểm
GET  /api/v1/places/?q=...   - Tìm kiếm địa điểm
```

**Itineraries (Lịch trình - Cần authentication)**
```
GET  /api/v1/itineraries/       - Danh sách lịch trình của user
POST /api/v1/itineraries/       - Tạo lịch trình mới
GET  /api/v1/itineraries/{id}/  - Chi tiết lịch trình
PUT  /api/v1/itineraries/{id}/  - Cập nhật lịch trình
DELETE /api/v1/itineraries/{id}/ - Xóa lịch trình
```

**AI Features**
```
POST /api/v1/chat/      - Chat với AI assistant
POST /api/v1/plan/      - Tạo lịch trình bằng AI
GET  /api/v1/analytics/ - Phân tích dữ liệu
```

## 🧪 Testing

```bash
# Di chuyển vào thư mục backend
cd "D:\KLTN\MAS (1)\MAS\TRAVEL_PLANNER\vivu_backend"

# Test APIs (server phải đang chạy)
python test_api.py

# Kiểm tra cấu hình
python check_config.py

# Run pytest (nếu có)
pytest

# Test với coverage
pytest --cov=. --cov-report=html
```

### Database Status

```
✅ NguoiDung (Users):              17 records
✅ TinhThanh (Cities):             58 records
✅ DiaDiem (Places):           50,334 records
✅ HinhAnhDiaDiem (Images):     2,000 records
✅ DanhGia (Reviews):           1,633 records
✅ DiaDiemYeuThich (Favorites):    80 records
✅ LichTrinh (Itineraries):        16 records
✅ LichTrinhDiaDiem (Details):    180 records
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOTAL:                         54,318 records
```

## 📁 Project Structure

```
D:\KLTN\MAS (1)\MAS\TRAVEL_PLANNER/
│
├── vivu_backend/              # Django Backend
│   ├── manage.py              # Django management
│   ├── db.sqlite3             # SQLite database (52,538 records)
│   ├── test_api.py            # API test suite
│   ├── check_config.py        # Configuration checker
│   │
│   ├── vivu_core/             # Django settings
│   │   ├── settings.py        # Main settings
│   │   ├── urls.py            # URL routing
│   │   └── wsgi.py
│   │
│   ├── apps/                  # Django apps
│   │   ├── users/             # User management (17 users)
│   │   ├── places/            # Places (50,334 địa điểm)
│   │   ├── itineraries/       # Itineraries (16 lịch trình)
│   │   ├── analytics/         # Analytics
│   │   └── api/               # REST API endpoints
│   │
│   ├── templates/             # HTML templates
│   │   └── index.html         # Landing page (TripAppia-inspired)
│   │
│   └── static/                # Static files
│       ├── css/
│       │   └── vivu-colors.css  # Color system (60:30:10)
│       └── img/               # Images & logo
│
├── agents/                    # 10 AI Agents
│   ├── orchestrator.py        # LangGraph orchestrator
│   ├── state.py               # Shared state
│   ├── api_collector.py       # API collection
│   ├── web_scraper.py         # Web scraping
│   ├── data_processor.py      # Data processing
│   ├── trip_planner.py        # Trip planning (LLM)
│   ├── destination_researcher.py  # Research (RAG)
│   └── analytics.py           # Analytics
│
├── data/                      # Data files
│   ├── vietnam_locations.csv
│   ├── places_final.csv
│   └── ...
│
├── vector_db/                 # ChromaDB vector store
│
├── .env                       # Environment variables (API keys)
├── .env.example               # Template
├── .gitignore
├── requirements.txt           # Python dependencies
└── README.md                  # This file
```

## 🛠️ Technology Stack

**Backend**
- Django 5.0.1 + Django REST Framework 3.14.0
- SQLite (development)
- Django CORS Headers
- DRF Spectacular (API documentation)

**AI/ML**
- LangChain + LangGraph (Multi-Agent orchestration)
- OpenAI GPT-4 & Embeddings
- LangSmith (agent monitoring)
- ChromaDB (vector database for RAG)
- Tavily (web search)

**Frontend**
- HTML5 + CSS3 (Modern responsive design)
- Inter font family
- TripAppia-inspired UI/UX
- Color palette: 60:30:10 rule
  - 60% Navy Blue (#153D68)
  - 30% Teal (#00838F)
  - 10% Gold (#DAA520)

**Data Processing**
- Pandas, NumPy
- BeautifulSoup4
- Requests

## 🔑 API Keys (Đã cấu hình sẵn)

API keys đã được cấu hình trong file `.env`:

1. **OPENAI_API_KEY** - GPT-4 & Embeddings ✅
2. **TAVILY_API_KEY** - Web search ✅
3. **LANGSMITH_API_KEY** - Agent monitoring ✅
4. **OPENWEATHER_API_KEY** - Weather data ✅
5. **LOCATIONIQ_API_KEY** - Location services ✅
6. **GEOAPIFY_API_KEY** - Geolocation ✅

File `.env` đã được cấu hình và sẵn sàng sử dụng.

## 🎨 Design & UI

### Color Palette (60:30:10 Rule)

**60% Primary - Navy Blue (#153D68)**
- Main backgrounds
- Headers & footers
- Large sections

**30% Secondary - Teal (#00838F)**
- Content cards
- Navigation
- Icons
- Headings

**10% Accent - Gold (#DAA520)**
- Call-to-action buttons
- Statistics highlights
- Hover effects
- Important notifications

### Design Inspiration

Landing page design inspired by [TripAppia](https://www.tripappia.com/):
- Clean, modern layout
- Interactive trip planning form
- Statistics showcase
- Responsive grid system
- Smooth animations

## 📈 Roadmap

- [x] Django REST API backend
- [x] 10 AI agents with LangGraph orchestration
- [x] 50,000+ địa điểm Việt Nam
- [x] RAG với ChromaDB
- [x] Admin panel
- [x] API documentation
- [x] TripAppia-inspired UI
- [ ] Booking integration (flights, hotels)
- [ ] User reviews & trip sharing
- [ ] Mobile app
- [ ] Real-time collaboration
- [ ] Advanced ML models

## 💡 Các lệnh thường dùng

```bash
# CD vào thư mục backend (BẮT BUỘC trước khi chạy bất kỳ lệnh nào)
cd "D:\KLTN\MAS (1)\MAS\TRAVEL_PLANNER\vivu_backend"

# Chạy server
python manage.py runserver

# Tạo migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Tạo superuser
python manage.py createsuperuser

# Django shell
python manage.py shell

# Collect static files
python manage.py collectstatic

# Test API
python test_api.py

# Check config
python check_config.py
```

## 🤝 Contributing

Contributions are welcome!

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Team

Developed as part of a thesis project on Multi-Agent Systems for travel planning.

## 🙏 Acknowledgments

- LangChain team for the amazing framework
- OpenAI for GPT-4 and embeddings
- Django community
- All contributors and testers

---

## 🆘 Troubleshooting

### Server không chạy được
```bash
# Kiểm tra Python version
python --version  # Cần >= 3.11

# Cài lại dependencies
pip install -r requirements.txt

# Kiểm tra port 8000
netstat -ano | findstr :8000
```

### Module not found
```bash
# Cài lại dependencies
cd "D:\KLTN\MAS (1)\MAS\TRAVEL_PLANNER"
pip install -r requirements.txt
```

### Database errors
```bash
cd "D:\KLTN\MAS (1)\MAS\TRAVEL_PLANNER\vivu_backend"
python manage.py migrate
```

### API keys not working
```bash
# Kiểm tra file .env
python check_config.py
```

---

**Vi Vu** - Because planning should be as fun as the trip itself! 🦢✈️🌏

*Inspired by [TripAppia](https://www.tripappia.com/) - The Future of AI Travel Planning*

