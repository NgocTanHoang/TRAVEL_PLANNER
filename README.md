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

### 🌐 Web Search Integration
- **DuckDuckGo**: Tìm kiếm miễn phí, không cần API key
- **Wikipedia**: Lấy thông tin từ Wikipedia tiếng Việt
- **SerpAPI**: Google Search results (có free tier)
- **Tavily**: Web search và data enrichment (optional)

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
│      │                                                       │
│      ├─► Flight Agent (conditional)                          │
│      │                                                       │
│      ├─► Accommodation Agent                                 │
│      │                                                       │
│      ├─► Activities Agent                                    │
│      │                                                       │
│      ├─► Budget Agent                                        │
│      │                                                       │
│      └─► Planning Agent                                      │
│                                                              │
│  All agents integrated with:                                 │
│  • LangChain LLM (GPT-4)                                     │
│  • LangSmith Tracing & Monitoring                            │
│  • Retry Logic & Error Handling                              │
└────────────────────────────┬─────────────────────────────────┘
                             │
┌────────────────────────────▼───────────────────────────────┐
│                     RAG ENGINE                             │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │  Embeddings  │──│ Vector Store │──│  LLM (GPT-4)    │   │
│  │  (OpenAI)    │  │  (ChromaDB)  │  │                 │   │
│  └──────────────┘  └──────────────┘  └─────────────────┘   │
└────────────────────────────────────────────────────────────┘
```

---

## 🚀 Hướng dẫn cài đặt

### Yêu cầu hệ thống

- **Python**: 3.10+ (khuyến nghị 3.11 hoặc 3.12)
- **Database**: SQLite (mặc định) hoặc PostgreSQL (production)
- **API Keys**: OpenAI, LangSmith (xem phần Environment Variables)

### Bước 1: Tạo và kích hoạt Virtual Environment

**Quan trọng**: Virtual environment phải được tạo tại thư mục gốc của project.

```bash
# Di chuyển đến thư mục project
cd "D:\KLTN\MAS (1)\MAS\TRAVEL_PLANNER"

# Tạo virtual environment
python -m venv venv

# Kích hoạt virtual environment
# Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# Windows (Command Prompt)
venv\Scripts\activate.bat

# Linux/Mac
source venv/bin/activate
```

Sau khi kích hoạt, bạn sẽ thấy `(venv)` ở đầu dòng command prompt.

### Bước 2: Cài đặt Dependencies

```bash
# Đảm bảo đang ở thư mục gốc TRAVEL_PLANNER
# và virtual environment đã được kích hoạt

# Cài đặt tất cả dependencies từ requirements.txt
pip install -r requirements.txt
```

**Lưu ý**: Quá trình cài đặt có thể mất vài phút tùy thuộc vào tốc độ internet.

### Bước 3: Cấu hình Environment Variables

Tạo file `.env` trong thư mục gốc `TRAVEL_PLANNER`:

```bash
# Tạo file .env (Windows PowerShell)
New-Item -Path .env -ItemType File

# Hoặc tạo thủ công bằng text editor
```

Thêm các biến môi trường sau vào file `.env`:

```env
# Django
DJANGO_SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# OpenAI (Bắt buộc)
OPENAI_API_KEY=sk-...

# LangSmith (Bắt buộc cho tracing)
LANGCHAIN_API_KEY=lsv2_pt_...
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=vi-vu-travel-planner

# Tavily (Tùy chọn - cho web search)
TAVILY_API_KEY=tvly-...

# SerpAPI (Tùy chọn - cho Google search)
SERPAPI_API_KEY=...

# OpenRouteService (Tùy chọn - cho routing)
OPENROUTE_API_KEY=...

# VietMap (Tùy chọn - cho geocoding Việt Nam)
VIETMAP_API_KEY=...
```

### Bước 4: Setup Database

**Quan trọng**: Phải di chuyển vào thư mục `vivu_backend` trước khi chạy các lệnh Django.

```bash
# Di chuyển vào thư mục vivu_backend
cd vivu_backend

# Chạy migrations để tạo database
python manage.py migrate

# Tạo superuser (admin account)
python manage.py createsuperuser
```

Khi tạo superuser, bạn sẽ được yêu cầu nhập:
- Username
- Email (tùy chọn)
- Password (sẽ không hiển thị khi gõ)

### Bước 5: Chạy Development Server

**Quan trọng**: Server chỉ có thể chạy từ thư mục `vivu_backend`.

```bash
# Đảm bảo đang ở trong thư mục vivu_backend
cd "D:\KLTN\MAS (1)\MAS\TRAVEL_PLANNER\vivu_backend"

# Chạy development server
python manage.py runserver
```

Server sẽ chạy tại: **http://127.0.0.1:8000**

Mở trình duyệt và truy cập:
- **Trang chủ**: http://127.0.0.1:8000
- **Admin panel**: http://127.0.0.1:8000/admin
- **API Documentation**: http://127.0.0.1:8000/api/docs/

---

## 📁 Cấu trúc Project

```
TRAVEL_PLANNER/
│
├── venv/                           # Virtual environment (tạo tại đây)
│
├── vivu_backend/                   # Django Backend (chạy server từ đây)
│   ├── manage.py                   # Django management
│   ├── db.sqlite3                  # SQLite database
│   ├── vivu_core/                  # Django settings
│   │   ├── settings.py             # Main configuration
│   │   ├── urls.py                 # URL routing
│   │   └── wsgi.py                 # WSGI config
│   │
│   ├── apps/                       # Django apps
│   │   ├── places/                 # Places management
│   │   │   ├── models.py           # DiaDiem, TinhThanh models
│   │   │   └── migrations/         # Database migrations
│   │   ├── users/                  # User management
│   │   ├── itineraries/            # Travel itineraries
│   │   ├── analytics/              # Analytics & insights
│   │   └── api/                    # REST API endpoints
│   │       ├── views.py            # API views
│   │       ├── serializers.py      # DRF serializers
│   │       ├── urls.py             # API routing
│   │       └── place_info_searcher.py  # Web search integration
│   │
│   ├── templates/                  # HTML templates
│   │   ├── index.html              # Landing page
│   │   ├── travel_plan.html        # Travel plan page
│   │   └── places/                 # Place templates
│   │
│   └── static/                     # Static files
│       ├── css/
│       │   ├── index.css           # Main styles
│       │   ├── vivu-colors.css     # Color system
│       │   └── vivu-design-system.css
│       └── js/
│           ├── index.js            # Main JavaScript
│           └── travel_plan_workflow.js
│
├── agents/                         # Multi-Agent System
│   ├── base_agent.py               # Base agent class
│   ├── state.py                    # Shared state definition
│   ├── langgraph_workflow.py       # LangGraph workflow
│   ├── interactive_workflow.py     # Interactive workflow
│   ├── orchestrator.py             # High-level orchestrator
│   │
│   └── travel_agents/              # 7 specialized agents
│       ├── orchestrator_agent.py   # Main orchestrator
│       ├── transport_agent.py      # Transport planning
│       ├── flight_agent.py         # Flight search
│       ├── accommodation_agent.py   # Hotel search
│       ├── activities_agent.py     # Activities & dining
│       ├── budget_agent.py          # Budget calculation
│       ├── planning_agent.py       # Itinerary planning
│       ├── rag.py                  # RAG implementation
│       └── vector_db.py            # Vector DB connector
│
├── tools/                          # Agent tools
│   ├── geo_tools.py                # Geocoding & location
│   ├── flight_tools.py             # Flight search
│   ├── accommodation_tools.py      # Hotel search
│   ├── activities_tools.py         # Place search
│   ├── transport_tools.py          # Transport planning
│   ├── budget_tools.py             # Budget calculation
│   ├── planning_tools.py           # Itinerary tools
│   ├── serpapi_tools.py            # SerpAPI integration
│   ├── vietmap_tools.py            # VietMap geocoding
│   └── travel_styles.py            # Travel style profiles
│
├── config/                         # Configuration
│   └── langsmith_config.py         # LangSmith centralized config
│
├── utils/                          # Utilities
│   ├── cache.py                    # Caching utilities
│   ├── error_handling.py           # Error classification
│   ├── retry.py                    # Retry decorators
│   └── standardization.py          # Data standardization
│
├── vector_db/                      # ChromaDB vector store
│   ├── connectors/                 # Vector DB connectors
│   └── chroma.sqlite3              # ChromaDB database
│
├── data/                           # Data files
│   ├── exports/                    # Data exports
│   └── tourism_qa_dataset.json     # Tourism Q&A dataset
│
├── scripts/                        # Utility scripts
│   ├── add_*.py                    # Image management scripts
│   ├── export_diadiem.py          # Data export
│   └── fix_and_enrich_places.py    # Data enrichment
│
├── requirements.txt                # Python dependencies
├── .env                            # Environment variables (tạo file này)
├── .gitignore
└── README.md                       # This file
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
- **DuckDuckGo** - Free web search (no API key needed)
- **Wikipedia** - Free information source
- **Tavily** - Web search and enrichment (optional)
- **SerpAPI** - Google search results (optional, free tier available)
- **VietMap** - Vietnam geocoding (optional)
- **OpenRouteService** - Route planning (optional)
- **OpenSky Network** - Flight data (optional)

### Frontend
- **HTML5 + CSS3** - Modern responsive design
- **JavaScript (Vanilla)** - Interactive features
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
- `dacDiem`, `tienNghi` (JSON fields)
- **Total**: 50+ places

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
GET    /api/v1/places/{id}/enriched/ # Place details with web search
GET    /api/v1/places/search/?q=...  # Search places
```

### Travel Planning
```
POST   /api/v1/travel-plans/         # Create travel plan (AI-powered)
POST   /api/v1/travel-plans/preview/ # Preview travel plan
GET    /api/v1/travel-plans/{id}/    # Get plan details
```

### Travel Styles
```
GET    /api/v1/travel-styles/        # List all travel styles
GET    /api/v1/travel-styles/{style}/ # Get style details
POST   /api/v1/travel-styles/combine/ # Combine multiple styles
```

### Itineraries (Authenticated)
```
GET    /api/v1/itineraries/          # User's itineraries
POST   /api/v1/itineraries/          # Create itinerary
GET    /api/v1/itineraries/{id}/     # Get itinerary
PUT    /api/v1/itineraries/{id}/     # Update itinerary
DELETE /api/v1/itineraries/{id}/     # Delete itinerary
```

### API Documentation
- **Swagger UI**: http://127.0.0.1:8000/api/docs/
- **ReDoc**: http://127.0.0.1:8000/api/redoc/

---

## 🔧 Development Commands

### Chạy Development Server

```bash
# Di chuyển vào thư mục vivu_backend
cd "D:\KLTN\MAS (1)\MAS\TRAVEL_PLANNER\vivu_backend"

# Chạy server
python manage.py runserver

# Chạy trên port khác
python manage.py runserver 8080
```

### Tạo Migrations

```bash
cd vivu_backend
python manage.py makemigrations
python manage.py migrate
```

### Tạo Superuser

```bash
cd vivu_backend
python manage.py createsuperuser
```

### Collect Static Files

```bash
cd vivu_backend
python manage.py collectstatic
```

### Shell (Django Shell)

```bash
cd vivu_backend
python manage.py shell
```

---

## 📝 Environment Variables

Tạo file `.env` trong thư mục gốc `TRAVEL_PLANNER`:

```env
# Django
DJANGO_SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# OpenAI (Bắt buộc)
OPENAI_API_KEY=sk-...

# LangSmith (Bắt buộc cho tracing)
LANGCHAIN_API_KEY=lsv2_pt_...
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=vi-vu-travel-planner

# Tavily (Tùy chọn - cho web search)
TAVILY_API_KEY=tvly-...

# SerpAPI (Tùy chọn - cho Google search)
SERPAPI_API_KEY=...

# OpenRouteService (Tùy chọn - cho routing)
OPENROUTE_API_KEY=...

# VietMap (Tùy chọn - cho geocoding Việt Nam)
VIETMAP_API_KEY=...
```

**Lưu ý**: 
- DuckDuckGo và Wikipedia không cần API key (hoàn toàn miễn phí)
- Chỉ cần `OPENAI_API_KEY` và `LANGCHAIN_API_KEY` để chạy cơ bản
- Các API khác là tùy chọn để có thêm tính năng

---

## 🆘 Troubleshooting

### Server không chạy được

```bash
# Kiểm tra Python version
python --version  # Cần >= 3.10

# Kiểm tra virtual environment đã được kích hoạt chưa
# Bạn sẽ thấy (venv) ở đầu dòng command prompt

# Kiểm tra đang ở đúng thư mục
# Phải ở trong: D:\KLTN\MAS (1)\MAS\TRAVEL_PLANNER\vivu_backend

# Cài lại dependencies
pip install -r requirements.txt

# Kiểm tra port 8000
netstat -ano | findstr :8000  # Windows
```

### Module not found

```bash
# Đảm bảo virtual environment đã được kích hoạt
# Đảm bảo đang ở đúng directory
cd "D:\KLTN\MAS (1)\MAS\TRAVEL_PLANNER\vivu_backend"

# Cài lại dependencies
pip install -r requirements.txt
```

### Database errors

```bash
cd vivu_backend
python manage.py migrate
python manage.py migrate --run-syncdb
```

### Import errors khi chạy từ thư mục sai

**Quan trọng**: 
- Tạo venv tại: `D:\KLTN\MAS (1)\MAS\TRAVEL_PLANNER`
- Chạy server từ: `D:\KLTN\MAS (1)\MAS\TRAVEL_PLANNER\vivu_backend`

Nếu gặp lỗi import, đảm bảo:
1. Virtual environment đã được kích hoạt
2. Đang ở đúng thư mục khi chạy lệnh
3. Đã cài đặt đầy đủ requirements.txt

### API keys không hoạt động

```bash
# Kiểm tra file .env
type .env  # Windows
cat .env   # Linux/Mac

# Đảm bảo file .env ở thư mục gốc TRAVEL_PLANNER
# Không phải trong vivu_backend
```

---

## 📈 Roadmap

- [x] Django REST API backend
- [x] Multi-Agent System với LangGraph
- [x] 7 specialized agents với retry logic
- [x] RAG với ChromaDB
- [x] LangSmith tracing & monitoring
- [x] Web search integration (DuckDuckGo, Wikipedia)
- [x] Travel styles expansion (14+ styles)
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

**Vi Vu** - Because planning should be as fun as the trip itself! 🦢✈️🌏

