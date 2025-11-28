# 🎫 Vi Vu - AI-Powered Travel Planner

> **Plan in Minutes, Vibe for Months.**

Vi Vu là nền tảng lập kế hoạch du lịch thế hệ mới được hỗ trợ bởi **Multi-Agent Systems (MAS)**, **LangChain**, **LangGraph**, và **LangSmith**. Được xây dựng cho du lịch Việt Nam, sử dụng AI để tạo lịch trình cá nhân hóa, tối ưu chỉ trong vài phút.

**Inspired by [TripAppia](https://www.tripappia.com/)** với thiết kế UI/UX hiện đại và quy tắc màu sắc 60:30:10.

---

## ✨ Tính năng chính

### 🤖 Multi-Agent System với 7 Specialized Agents

Hệ thống sử dụng **7 agents chuyên biệt** hoạt động theo workflow có điều phối:

1. **Orchestrator Agent** - Điều phối toàn bộ workflow, quản lý state và điều hướng giữa các agents
2. **Transport Agent** - Tính toán khoảng cách, thời gian di chuyển và đề xuất phương tiện (máy bay, tàu, xe khách, xe máy)
3. **Flight Agent** - Tìm kiếm chuyến bay với tích hợp sân bay gần nhất, so sánh giá vé từ nhiều nguồn
4. **Accommodation Agent** - Tìm khách sạn, resort phù hợp với ngân sách và phong cách du lịch
5. **Activities Agent** - Gợi ý địa điểm tham quan và nhà hàng, ưu tiên database, sau đó tools, cuối cùng vector DB
6. **Budget Agent** - Tính toán và tối ưu ngân sách theo từng hạng mục (vận chuyển, lưu trú, hoạt động, ăn uống)
7. **Planning Agent** - Tạo lịch trình chi tiết theo ngày với timeline, phân bổ hoạt động hợp lý

### 🔄 Workflow Execution Flow

```
User Input (Origin, Destination, Dates, Travelers, Style)
         │
         ▼
┌─────────────────────────────────────────┐
│   Orchestrator Agent                    │
│   - Khởi tạo state                      │
│   - Điều phối workflow                  │
└──────────────┬──────────────────────────┘
               │
               ├─► Step 1: Transport Agent
               │   - Tính khoảng cách
               │   - Đề xuất phương tiện
               │
               ├─► Step 2: Flight Agent (conditional)
               │   - Nếu cần máy bay
               │   - Tìm sân bay gần nhất
               │   - So sánh giá vé
               │
               ├─► Step 3: Accommodation Agent
               │   - Tìm khách sạn
               │   - Tính chi phí lưu trú
               │
               ├─► Step 4: Activities Agent
               │   - Tìm địa điểm tham quan
               │   - Tìm nhà hàng
               │   - Tính chi phí hoạt động & ăn uống
               │
               ├─► Step 5: Budget Agent
               │   - Tổng hợp chi phí
               │   - Tính toán ngân sách
               │
               └─► Step 6: Planning Agent
                   - Tạo lịch trình chi tiết
                   - Phân bổ hoạt động theo ngày
                   - Tạo timeline với thời gian cụ thể
                   - Generate mô tả bằng LLM
```

### 🧠 RAG-Powered Recommendations
- **Vector Database**: ChromaDB với embeddings từ OpenAI
- **Intelligent Search**: Tìm kiếm địa điểm dựa trên semantic similarity
- **50K+ Địa điểm Việt Nam**: Database phong phú với thông tin chi tiết
- **Priority-based Search**: Database → Tools → Vector DB (fallback)

### 📊 Smart Analytics
- Phân tích chi phí theo từng hạng mục
- Tối ưu hoạt động theo thời gian và ngân sách
- Dự đoán giá vé và chi phí
- So sánh các phương án di chuyển

### 💬 AI Chat Assistant
- Chat với AI để nhận tư vấn du lịch
- Hỏi đáp về địa điểm, lịch trình, ngân sách
- RAG-powered với vector database

### 🗺️ Auto-Generated Itineraries
- Tạo lịch trình tự động theo ngày với timeline chi tiết
- Tối ưu route và thời gian di chuyển
- Bao gồm cả thông tin chi tiết về từng địa điểm
- **LLM-Generated Descriptions**: Tự động tạo mô tả lịch trình bằng ngôn ngữ tự nhiên với Groq/OpenAI
- Phân bổ hoạt động hợp lý (sáng, chiều, tối)
- Tính toán thời gian di chuyển giữa các địa điểm

### 🌐 Web Search Integration
- **DuckDuckGo**: Tìm kiếm miễn phí, không cần API key
- **Wikipedia**: Lấy thông tin từ Wikipedia tiếng Việt
- **SerpAPI**: Google Search results (có free tier)
- **Tavily**: Web search và data enrichment (optional)

### 🗺️ Geocoding & Routing
- **VietMap**: Geocoding và routing cho Việt Nam (khuyến nghị)
- **OpenRouteService**: Routing fallback
- **OSRM**: Open Source Routing Machine (fallback)
- **Haversine**: Tính khoảng cách nhanh (free)
- **Smart Caching**: Cache routes để giảm API calls

---

## 🏗️ Kiến trúc hệ thống

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (Django Templates)              │
│   Landing Page | Places Search | Travel Plan | User Portal  │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/REST API
┌────────────────────────▼────────────────────────────────────┐
│                   DJANGO BACKEND                            │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐     │
│  │  REST API   │  │  Multi-Agent │  │  Data Models    │     │
│  │  Endpoints  │──│  Orchestrator │──│  (SQLite)      │     │
│  └─────────────┘  └──────┬───────┘  └─────────────────┘     │
└────────────────────────────┼────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────┐
│              ORCHESTRATOR AGENT (7 Agents)                  │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  1. Transport Agent                                  │   │
│  │     - Tính khoảng cách & thời gian                   │   │
│  │     - Đề xuất phương tiện                            │   │
│  └──────────────────────────────────────────────────────┘   │
│                          │                                  │
│  ┌───────────────────────▼──────────────────────────────┐   │
│  │  2. Flight Agent (conditional)                       │   │
│  │     - Tìm sân bay gần nhất                           │   │
│  │     - So sánh giá vé                                 │   │
│  └──────────────────────────────────────────────────────┘   │
│                          │                                  │
│  ┌───────────────────────▼──────────────────────────────┐   │
│  │  3. Accommodation Agent                              │   │
│  │     - Tìm khách sạn                                  │   │
│  │     - Tính chi phí lưu trú                           │   │
│  └──────────────────────────────────────────────────────┘   │
│                          │                                  │
│  ┌───────────────────────▼──────────────────────────────┐   │
│  │  4. Activities Agent                                 │   │
│  │     - Tìm địa điểm tham quan (DB → Tools → Vector)   │   │
│  │     - Tìm nhà hàng                                   │   │
│  │     - Tính chi phí hoạt động & ăn uống               │   │
│  └──────────────────────────────────────────────────────┘   │
│                          │                                  │
│  ┌───────────────────────▼──────────────────────────────┐   │
│  │  5. Budget Agent                                     │   │
│  │     - Tổng hợp chi phí                               │   │
│  │     - Tính toán ngân sách                            │   │
│  └──────────────────────────────────────────────────────┘   │
│                          │                                  │
│  ┌───────────────────────▼──────────────────────────────┐   │
│  │  6. Planning Agent                                   │   │
│  │     - Tạo lịch trình chi tiết                        │   │
│  │     - Phân bổ hoạt động theo ngày                    │   │
│  │     - Generate mô tả bằng LLM                        │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                             │
│  All agents integrated with:                                │
│  • LangChain LLM (GPT-4, Groq)                              │
│  • LangSmith Tracing & Monitoring                           │
│  • Retry Logic & Error Handling                             │
│  • State Management (TravelPlanningState)                   │
└────────────────────────────┬────────────────────────────────┘
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
- **Redis** (tùy chọn): Cho caching

### Bước 1: Clone Repository

```bash
git clone <repository-url>
cd TRAVEL_PLANNER
```

### Bước 2: Tạo và kích hoạt Virtual Environment

**Quan trọng**: Virtual environment phải được tạo tại thư mục gốc của project.

```bash
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

### Bước 3: Cài đặt Dependencies

```bash
# Đảm bảo đang ở thư mục gốc TRAVEL_PLANNER
# và virtual environment đã được kích hoạt

# Cài đặt tất cả dependencies từ requirements.txt
pip install -r requirements.txt
```

**Lưu ý**: Quá trình cài đặt có thể mất vài phút tùy thuộc vào tốc độ internet.

### Bước 4: Cấu hình Environment Variables

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

# Groq (Tùy chọn - cho LLM nhanh, ưu tiên cho itinerary descriptions)
GROQ_API_KEY=gsk-...
GROQ_MODEL=llama-3.3-70b-versatile  # Hoặc openai/gpt-oss-120b

# LLM Fallback Configuration
FALLBACK_MODEL=openai/gpt-oss-120b  # Model dự phòng
OPENAI_BASE_URL=  # Để trống hoặc URL custom cho OpenRouter

# Tavily (Tùy chọn - cho web search)
TAVILY_API_KEY=tvly-...

# SerpAPI (Tùy chọn - cho Google search)
SERPAPI_API_KEY=...

# OpenRouteService (Tùy chọn - cho routing)
OPENROUTE_API_KEY=...

# VietMap (Khuyến nghị - cho geocoding Việt Nam)
VIETMAP_API_KEY=...

# Amadeus (Tùy chọn - cho flight search)
AMADEUS_API_KEY=...
AMADEUS_API_SECRET=...

# FlightAPI (Tùy chọn - cho flight search)
FLIGHTAPI_API_KEY=...

# Redis (Tùy chọn - cho caching)
REDIS_URL=redis://localhost:6379/0
```

### Bước 5: Setup Database

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

### Bước 6: Chạy Development Server

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
│   │       ├── travel_plan_step_views.py  # 4-step workflow views
│   │       └── urls.py             # API routing
│   │
│   ├── agents/                     # Multi-Agent System
│   │   ├── base_agent.py           # Base agent class
│   │   ├── state.py                # Shared state definition
│   │   ├── langgraph_workflow.py   # LangGraph workflow
│   │   └── travel_agents/          # 7 specialized agents
│   │       ├── orchestrator_agent.py   # Main orchestrator
│   │       ├── transport_agent.py      # Transport planning
│   │       ├── flight_agent.py         # Flight search
│   │       ├── accommodation_agent.py   # Hotel search
│   │       ├── activities_agent.py     # Activities & dining
│   │       ├── budget_agent.py         # Budget calculation
│   │       ├── planning_agent.py       # Itinerary planning
│   │       ├── rag.py                  # RAG implementation
│   │       └── vector_db.py            # Vector DB connector
│   │
│   ├── tools/                      # Agent tools
│   │   ├── geo_tools.py            # Geocoding & location
│   │   ├── flight_tools.py         # Flight search
│   │   ├── accommodation_tools.py   # Hotel search
│   │   ├── activities_tools.py     # Place search
│   │   ├── transport_tools.py      # Transport planning
│   │   ├── budget_tools.py         # Budget calculation
│   │   ├── planning_tools.py       # Itinerary tools
│   │   ├── serpapi_tools.py        # SerpAPI integration
│   │   ├── vietmap_tools.py        # VietMap geocoding
│   │   └── travel_styles.py        # Travel style profiles
│   │
│   ├── utils/                      # Utilities
│   │   ├── cache.py                # Caching utilities
│   │   ├── error_handling.py       # Error classification
│   │   ├── retry.py                # Retry decorators
│   │   ├── itinerary_formatter.py  # Itinerary JSON formatting & LLM description
│   │   └── semantic_place_classifier.py  # Place classification
│   │
│   ├── templates/                  # HTML templates
│   │   ├── index.html              # Landing page
│   │   ├── travel_plan.html        # Travel plan page (4-step workflow)
│   │   └── places/                 # Place templates
│   │
│   ├── static/                     # Static files
│   │   ├── css/
│   │   │   ├── index.css           # Main styles
│   │   │   └── global.css          # Global styles
│   │   └── js/
│   │       ├── index.js            # Main JavaScript
│   │       └── travel_plan_workflow.js  # 4-step workflow JS
│   │
│   └── vector_db/                  # ChromaDB vector store
│       └── chroma.sqlite3          # ChromaDB database
│
├── scripts/                        # Utility scripts
│   ├── test_create_itinerary.py   # Test itinerary creation
│   ├── find_provinces_without_places.py  # Analyze data coverage
│   └── ...
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
- **Redis** - Caching (optional)

### AI/ML & Multi-Agent
- **LangChain 1.x** - LLM framework
- **LangGraph 1.x** - Stateful agent workflows
- **LangSmith** - Agent monitoring & tracing
- **OpenAI GPT-4/GPT-4o-mini** - Primary LLM & embeddings
- **Groq** - Fast LLM inference (GPT-OSS-120B, Llama models)
- **ChromaDB** - Vector database for RAG

### External APIs
- **DuckDuckGo** - Free web search (no API key needed)
- **Wikipedia** - Free information source
- **Tavily** - Web search and enrichment (optional)
- **SerpAPI** - Google search results (optional, free tier available)
- **VietMap** - Vietnam geocoding (primary, recommended)
- **OpenRouteService** - Route planning (fallback, based on OSM)
- **OSRM** - Open Source Routing Machine (fallback routing)
- **Amadeus** - Flight search (optional)
- **FlightAPI** - Flight search (optional)

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
- **Total**: 50K+ places

**LICHTRINH** (Itineraries)
- User travel plans
- Linked to user accounts
- Stores full itinerary JSON

**LICHTRINHDIADIEM** (Itinerary Places)
- Links itineraries to places
- Includes visit dates and times

---

## 🔌 API Endpoints

### Travel Planning (4-Step Workflow)

```
POST   /api/v1/travel-plans/step1/        # Step 1: Location selection
POST   /api/v1/travel-plans/step2/        # Step 2: Transport options
POST   /api/v1/travel-plans/step3/        # Step 3: Budget & Hotels
POST   /api/v1/travel-plans/step4/        # Step 4: Confirm & Create plan
POST   /api/v1/travel-plans/step4/save/   # Save itinerary to database
```

### Places
```
GET    /api/v1/places/                    # List places (paginated)
GET    /api/v1/places/{id}/               # Place details
GET    /api/v1/places/search/?q=...       # Search places
```

### Itineraries (Authenticated)
```
GET    /api/v1/itineraries/               # User's itineraries
GET    /api/v1/itineraries/recent/        # Recent itineraries
POST   /api/v1/itineraries/               # Create itinerary
GET    /api/v1/itineraries/{id}/          # Get itinerary
```

### Travel Styles
```
GET    /api/v1/travel-styles/             # List all travel styles
GET    /api/v1/travel-styles/{style}/     # Get style details
```

---

## 🔧 Development Commands

### Chạy Development Server

```bash
# Di chuyển vào thư mục vivu_backend
cd vivu_backend

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

### Test Itinerary Creation

```bash
cd vivu_backend
python scripts/test_create_itinerary.py
```

### Analyze Data Coverage

```bash
cd vivu_backend
python scripts/find_provinces_without_places.py
```

---

## 🆕 Tính năng mới (2025)

### Multi-Agent System Improvements
- ✅ **7 Specialized Agents**: Orchestrator, Transport, Flight, Accommodation, Activities, Budget, Planning
- ✅ **State Management**: Centralized state với TravelPlanningState
- ✅ **Error Handling**: Retry logic và error classification
- ✅ **LangSmith Integration**: Full tracing và monitoring

### Data Quality Improvements
- ✅ **Location Normalization**: Xử lý các biến thể tên địa điểm
- ✅ **Activity Filtering**: Loại bỏ activities có tên giống destination
- ✅ **Priority-based Search**: Database → Tools → Vector DB
- ✅ **Cost Calculation**: Fallback estimates khi không có giá

### Geocoding & Routing
- ✅ **Multi-Provider Routing**: VietMap → OpenRouteService → OSRM → Haversine
- ✅ **Smart Caching**: Cache routes để giảm API calls
- ✅ **Coordinate Normalization**: Đảm bảo cache consistency

### Itinerary Generation
- ✅ **Daily Timeline**: Timeline chi tiết với thời gian cụ thể
- ✅ **Activity Distribution**: Phân bổ hoạt động hợp lý
- ✅ **Travel Time Calculation**: Tính thời gian di chuyển giữa các địa điểm
- ✅ **LLM-Generated Descriptions**: Mô tả lịch trình bằng ngôn ngữ tự nhiên

### Frontend Improvements
- ✅ **4-Step Workflow**: Step-by-step travel plan creation
- ✅ **Transport Selection**: User chọn phương tiện trước khi tiếp tục
- ✅ **Hotel Selection**: User chọn khách sạn
- ✅ **Itinerary Display**: Hiển thị lịch trình chi tiết với timeline

---

## 📈 Roadmap

- [x] Django REST API backend
- [x] Multi-Agent System với 7 specialized agents
- [x] 4-step travel planning workflow
- [x] RAG với ChromaDB
- [x] LangSmith tracing & monitoring
- [x] Web search integration
- [x] Travel styles expansion (14+ styles)
- [x] Database schema với 50K+ places
- [x] Comprehensive documentation
- [x] Groq API integration
- [x] LLM-generated itinerary descriptions
- [x] Multi-provider routing
- [x] Location name normalization
- [x] Activity filtering & cost calculation
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
