# 🎫 Vi Vu - AI-Powered Travel Planner

> **Plan in Minutes, Vibe for Months.**

Vi Vu là nền tảng lập kế hoạch du lịch thế hệ mới được hỗ trợ bởi **Multi-Agent Systems (MAS)**, **LangChain**, **LangGraph**, và **LangSmith**. Được xây dựng cho du lịch Việt Nam, sử dụng AI để tạo lịch trình cá nhân hóa, tối ưu chỉ trong vài phút.

**Inspired by [TripAppia](https://www.tripappia.com/)** với thiết kế UI/UX hiện đại và quy tắc màu sắc 60:30:10.

---

## ✨ Tính năng chính

### 🤖 Multi-Agent System
- **7 Specialized Agents** hoạt động theo workflow có điều phối:
  - **Transport Agent**: Tính toán khoảng cách và đề xuất phương tiện di chuyển
  - **Flight Agent**: Tìm kiếm chuyến bay với tích hợp sân bay gần nhất
  - **Accommodation Agent**: Tìm khách sạn, resort phù hợp với ngân sách
  - **Activities Agent**: Gợi ý địa điểm tham quan và nhà hàng
  - **Budget Agent**: Tính toán và tối ưu ngân sách
  - **Planning Agent**: Tạo lịch trình chi tiết theo ngày
  - **Orchestrator Agent**: Điều phối toàn bộ workflow

### 🧠 RAG-Powered Recommendations
- **Vector Database**: ChromaDB với embeddings từ OpenAI
- **Intelligent Search**: Tìm kiếm địa điểm dựa trên semantic similarity
- **50K+ Địa điểm Việt Nam**: Database phong phú với thông tin chi tiết

### 📊 Smart Analytics
- Phân tích chi phí theo từng hạng mục
- Tối ưu hoạt động theo thời gian và ngân sách
- Dự đoán giá vé và chi phí

### 💬 AI Chat Assistant
- Chat với AI để nhận tư vấn du lịch
- Hỏi đáp về địa điểm, lịch trình, ngân sách

### 🗺️ Auto-Generated Itineraries
- Tạo lịch trình tự động theo ngày
- Tối ưu route và thời gian
- Bao gồm cả thông tin chi tiết về từng địa điểm

---

## 🏗️ Kiến trúc hệ thống

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (Django Templates)              │
│   Landing Page | Places Search | Travel Plan | User Portal │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/REST API
┌────────────────────────▼────────────────────────────────────┐
│                   DJANGO BACKEND                            │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐ │
│  │  REST API   │  │  Multi-Agent │  │  Data Models    │ │
│  │  Endpoints  │──│  Orchestrator │──│  (SQLite)        │ │
│  └─────────────┘  └──────┬───────┘  └─────────────────┘ │
└────────────────────────────┼─────────────────────────────────┘
                             │
┌────────────────────────────▼─────────────────────────────────┐
│              LANGGRAPH WORKFLOW ORCHESTRATOR                 │
│                                                              │
│  Entry Point: Transport Agent                                │
│      │                                                        │
│      ├─► Flight Agent (conditional)                         │
│      │                                                        │
│      ├─► Accommodation Agent                                 │
│      │                                                        │
│      ├─► Activities Agent                                    │
│      │                                                        │
│      ├─► Budget Agent                                        │
│      │                                                        │
│      └─► Planning Agent                                       │
│                                                              │
│  All agents integrated with:                                │
│  • LangChain LLM (GPT-4)                                     │
│  • LangSmith Tracing & Monitoring                            │
│  • Retry Logic & Error Handling                              │
└───────────────────────────┬───────────────────────────────────┘
                            │
┌────────────────────────────▼─────────────────────────────────┐
│                     RAG ENGINE                              │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │  Embeddings  │──│ Vector Store │──│  LLM (GPT-4)    │   │
│  │  (OpenAI)    │  │  (ChromaDB)  │  │                 │   │
│  └──────────────┘  └──────────────┘  └─────────────────┘   │
└───────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Yêu cầu hệ thống

- **Python**: 3.10+
- **Database**: SQLite (mặc định) hoặc PostgreSQL (production)
- **API Keys**: OpenAI, LangSmith, Tavily (xem `.env.example`)

### Cài đặt

1. **Clone repository:**
```bash
git clone https://github.com/NgocTanHoang/TRAVEL_PLANNER.git
cd TRAVEL_PLANNER
```

2. **Tạo virtual environment:**
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/Mac
source .venv/bin/activate
```

3. **Cài đặt dependencies:**
```bash
pip install -r requirements.txt
```

4. **Cấu hình environment variables:**
```bash
# Copy file mẫu
cp .env.example .env

# Chỉnh sửa .env và thêm các API keys cần thiết:
# - OPENAI_API_KEY
# - LANGCHAIN_API_KEY (LangSmith)
# - TAVILY_API_KEY
# - SERPAPI_API_KEY (optional)
# - OPENROUTE_API_KEY (optional)
```

5. **Setup database:**
```bash
cd vivu_backend
python manage.py migrate
python manage.py createsuperuser  # Tạo admin user
```

6. **Chạy development server:**
```bash
python manage.py runserver
```

Server sẽ chạy tại: **http://127.0.0.1:8000**

---

## 📁 Cấu trúc Project

```
TRAVEL_PLANNER/
│
├── vivu_backend/                    # Django Backend
│   ├── manage.py                    # Django management
│   ├── db.sqlite3                   # SQLite database
│   ├── vivu_core/                   # Django settings
│   │   ├── settings.py              # Main configuration
│   │   ├── urls.py                  # URL routing
│   │   └── wsgi.py                  # WSGI config
│   │
│   ├── apps/                        # Django apps
│   │   ├── places/                  # Places management
│   │   │   ├── models.py            # DiaDiem, TinhThanh models
│   │   │   └── migrations/          # Database migrations
│   │   ├── users/                   # User management
│   │   ├── itineraries/             # Travel itineraries
│   │   ├── analytics/               # Analytics & insights
│   │   └── api/                     # REST API endpoints
│   │       ├── views.py             # API views
│   │       ├── serializers.py       # DRF serializers
│   │       └── urls.py               # API routing
│   │
│   ├── templates/                   # HTML templates
│   │   ├── index.html               # Landing page
│   │   ├── travel_plan.html         # Travel plan page
│   │   └── places/                  # Place templates
│   │
│   └── static/                      # Static files
│       ├── css/
│       │   ├── index.css            # Main styles
│       │   ├── vivu-colors.css      # Color system
│       │   └── vivu-design-system.css
│       └── img/                     # Images & assets
│
├── agents/                          # Multi-Agent System
│   ├── base_agent.py                # Base agent class
│   ├── state.py                     # Shared state definition
│   ├── langgraph_workflow.py       # LangGraph workflow
│   ├── interactive_workflow.py     # Interactive workflow
│   ├── orchestrator.py              # High-level orchestrator
│   │
│   └── travel_agents/               # 7 specialized agents
│       ├── orchestrator_agent.py   # Main orchestrator
│       ├── transport_agent.py      # Transport planning
│       ├── flight_agent.py          # Flight search
│       ├── accommodation_agent.py # Hotel search
│       ├── activities_agent.py     # Activities & dining
│       ├── budget_agent.py          # Budget calculation
│       ├── planning_agent.py       # Itinerary planning
│       ├── rag.py                   # RAG implementation
│       └── vector_db.py             # Vector DB connector
│
├── tools/                           # Agent tools
│   ├── geo_tools.py                 # Geocoding & location
│   ├── flight_tools.py              # Flight search
│   ├── accommodation_tools.py      # Hotel search
│   ├── activities_tools.py          # Place search
│   ├── transport_tools.py           # Transport planning
│   ├── budget_tools.py              # Budget calculation
│   ├── planning_tools.py            # Itinerary tools
│   ├── serpapi_tools.py             # SerpAPI integration
│   └── vietmap_tools.py             # VietMap geocoding
│
├── config/                          # Configuration
│   ├── langsmith_config.py          # LangSmith centralized config
│   └── __init__.py
│
├── utils/                           # Utilities
│   ├── cache.py                     # Caching utilities
│   ├── error_handling.py            # Error classification
│   ├── retry.py                     # Retry decorators
│   └── standardization.py           # Data standardization
│
├── api/                             # FastAPI orchestrator
│   └── orchestrator.py              # FastAPI endpoint
│
├── vector_db/                       # ChromaDB vector store
│   ├── connectors/                  # Vector DB connectors
│   └── chroma.sqlite3              # ChromaDB database (gitignored)
│
├── data/                            # Data files
│   ├── exports/                    # Data exports
│   └── tourism_qa_dataset.json     # Tourism Q&A dataset
│
├── scripts/                         # Utility scripts
│   ├── import_*.py                  # Data import scripts
│   └── analyze_database.py          # DB analysis
│
├── docs/                            # Documentation
│   └── OPENSKY_API.md               # API documentation
│
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment template
├── .gitignore
└── README.md                        # This file
```

---

## 🛠️ Technology Stack

### Backend
- **Django 5.0.1** - Web framework
- **Django REST Framework 3.14.0** - REST API
- **SQLite** - Development database
- **PostgreSQL** - Production-ready (optional)

### AI/ML & Multi-Agent
- **LangChain 1.x** - LLM framework
- **LangGraph 1.x** - Stateful agent workflows
- **LangSmith** - Agent monitoring & tracing
- **OpenAI GPT-4** - LLM & embeddings
- **ChromaDB** - Vector database for RAG

### External APIs
- **Tavily** - Web search
- **SerpAPI** - Google search results
- **VietMap** - Vietnam geocoding
- **OpenRouteService** - Route planning
- **OpenSky Network** - Flight data

### Frontend
- **HTML5 + CSS3** - Modern responsive design
- **Inter** - Base font family
- **Poppins** - Heading font family
- **Color System**: 60:30:10 rule
  - 60% Navy Blue (#153D68)
  - 30% Teal (#00838F)
  - 10% Gold (#DAA520)

### Data Processing
- **Pandas** - Data manipulation
- **NumPy** - Numerical computing
- **BeautifulSoup4** - Web scraping
- **Requests** - HTTP client

---

## 🎨 Design System

### Color Profile (60:30:10 Rule)

**60% Primary - Navy Blue (#153D68)**
- Main backgrounds
- Headers & footers
- Large sections

**30% Secondary - Teal (#00838F)**
- Content cards
- Navigation elements
- Icons & headings

**10% Accent - Gold (#DAA520)**
- Call-to-action buttons
- Statistics highlights
- Hover effects
- Important notifications

### Typography
- **Base Font**: Inter (400, 500, 600, 700, 800)
- **Heading Font**: Poppins (400, 500, 600, 700, 800, 900)

### Responsive Design
- Mobile-first approach
- Breakpoints: 480px, 768px, 1024px, 1280px
- Flexible grid system

---

## 📊 Database Schema

### Core Tables

**TINHTHANH** (Provinces/Cities)
- `maTinhThanh` (PK, Auto, starts from 1)
- `tenTinhThanh` (Unique)
- `viDo`, `kinhDo`
- **Total**: 63 provinces

**DIADIEM** (Places)
- `maDiaDiem` (PK, Auto)
- `tenDiaDiem`, `moTa`, `diaChi`
- `maTinhThanh` (FK → TINHTHANH)
- `loaiDiaDiem` (dia_danh, nha_hang, khach_san, giai_tri, mua_sam, khac)
- `viDo`, `kinhDo` (Coordinates)
- `giaVe` (Price)
- `gioMoCua`, `gioDongCua`
- `dienThoai`, `website`
- `danhGiaTrungBinh`, `soLuotDanhGia`, `soLuotXem`
- `dacDiem`, `tienNghi`
- **Total**: 53 places (Hà Nội, TPHCM, Đà Nẵng)

**HINHANHDIADIEM** (Place Images)
- Links images to places
- Supports multiple images per place

**LICHTRINH** (Itineraries)
- User travel plans
- Linked to user accounts

---

## 🔌 API Endpoints

### Authentication
```
POST   /api/v1/auth/register/        # User registration
POST   /api/v1/auth/login/           # User login
POST   /api/v1/auth/logout/          # User logout
```

### Places
```
GET    /api/v1/places/               # List places (paginated)
GET    /api/v1/places/{id}/          # Place details
GET    /api/v1/places/search/?q=...  # Search places
```

### Travel Planning
```
POST   /api/v1/travel-plan/          # Create travel plan (AI-powered)
GET    /api/v1/travel-plan/{id}/     # Get plan details
```

### Itineraries (Authenticated)
```
GET    /api/v1/itineraries/          # User's itineraries
POST   /api/v1/itineraries/          # Create itinerary
GET    /api/v1/itineraries/{id}/     # Get itinerary
PUT    /api/v1/itineraries/{id}/     # Update itinerary
DELETE /api/v1/itineraries/{id}/     # Delete itinerary
```

### AI Chat
```
POST   /api/v1/chat/                 # Chat with AI assistant
```

### API Documentation
- **Swagger UI**: http://127.0.0.1:8000/api/docs/
- **ReDoc**: http://127.0.0.1:8000/api/redoc/

---

## 🔧 Development

### Chạy Development Server

```bash
cd vivu_backend
python manage.py runserver
```

### Tạo Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### Tạo Superuser

```bash
python manage.py createsuperuser
```

### Test LangGraph Workflow

```bash
python test_langgraph_tracing.py
```

### Test Workflow Integration

```bash
python test_workflow_integration.py
```

### Kiểm tra LangSmith Tracing

```bash
python check_tracing.py
```

### Setup LangSmith Environment

```bash
python setup_langsmith_env.py
```

---

## 📝 Environment Variables

Tạo file `.env` trong root directory:

```env
# Django
DJANGO_SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# OpenAI
OPENAI_API_KEY=sk-...

# LangSmith
LANGCHAIN_API_KEY=lsv2_pt_...
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=vi-vu-travel-planner

# Tavily
TAVILY_API_KEY=tvly-...

# SerpAPI (optional)
SERPAPI_API_KEY=...

# OpenRouteService (optional)
OPENROUTE_API_KEY=...

# VietMap (optional)
VIETMAP_API_KEY=...
```

---

## 🧪 Testing

### Run Tests

```bash
# Django tests
cd vivu_backend
python manage.py test

# Pytest
pytest

# With coverage
pytest --cov=. --cov-report=html
```

### Test API Endpoints

```bash
python test_server.py
```

---

## 📈 Roadmap

- [x] Django REST API backend
- [x] Multi-Agent System với LangGraph
- [x] 7 specialized agents với retry logic
- [x] RAG với ChromaDB
- [x] LangSmith tracing & monitoring
- [x] Database schema fixes
- [x] Hero banner với image support
- [x] Comprehensive documentation
- [ ] Booking integration (flights, hotels)
- [ ] User reviews & trip sharing
- [ ] Mobile app (React Native)
- [ ] Real-time collaboration
- [ ] Advanced ML models
- [ ] Multi-language support

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License.

---

## 👥 Team

Developed as part of a thesis project on **Multi-Agent Systems for Intelligent Travel Planning**.

---

## 🙏 Acknowledgments

- **LangChain** team for the amazing framework
- **OpenAI** for GPT-4 and embeddings
- **Django** community
- **LangSmith** for monitoring & tracing
- All contributors and testers

---

## 🆘 Troubleshooting

### Server không chạy được

```bash
# Kiểm tra Python version
python --version  # Cần >= 3.10

# Cài lại dependencies
pip install -r requirements.txt

# Kiểm tra port 8000
netstat -ano | findstr :8000  # Windows
lsof -i :8000                  # Linux/Mac
```

### Module not found

```bash
# Đảm bảo đang ở đúng directory
cd vivu_backend

# Cài lại dependencies
pip install -r requirements.txt
```

### Database errors

```bash
cd vivu_backend
python manage.py migrate
python manage.py migrate --run-syncdb
```

### LangSmith tracing không hoạt động

```bash
# Kiểm tra environment variables
python check_tracing.py

# Setup lại LangSmith
python setup_langsmith_env.py
```

### API keys không hoạt động

```bash
# Kiểm tra file .env
cat .env  # Linux/Mac
type .env # Windows

# Verify config
python check_config.py
```

---

## 📚 Documentation

- [Architecture Analysis](ARCHITECTURE_ANALYSIS.md) - Chi tiết về cấu trúc hệ thống
- [LangSmith Integration](LANGSMITH_FIX.md) - Hướng dẫn tích hợp LangSmith
- [API Documentation](http://127.0.0.1:8000/api/docs/) - Swagger UI
- [OpenSky API](docs/OPENSKY_API.md) - Flight data API

---

**Vi Vu** - Because planning should be as fun as the trip itself! 🦢✈️🌏

*Inspired by [TripAppia](https://www.tripappia.com/) - The Future of AI Travel Planning*
