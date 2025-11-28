# 📚 Tài Liệu Chi Tiết Dự Án Vi Vu - AI-Powered Travel Planner

## 📋 Mục Lục

1. [Tổng Quan Dự Án](#tổng-quan-dự-án)
2. [Kiến Trúc Hệ Thống](#kiến-trúc-hệ-thống)
3. [Multi-Agent System](#multi-agent-system)
4. [Luồng Dữ Liệu và Sự Kiện](#luồng-dữ-liệu-và-sự-kiện)
5. [Vai Trò của LangGraph và LLM](#vai-trò-của-langgraph-và-llm)
6. [Tools và Dependencies](#tools-và-dependencies)
7. [Tính Năng Chính](#tính-năng-chính)
8. [Cấu Trúc Cơ Sở Dữ Liệu](#cấu-trúc-cơ-sở-dữ-liệu)
9. [API Endpoints](#api-endpoints)

---

## 🎯 Tổng Quan Dự Án

**Vi Vu** là một nền tảng lập kế hoạch du lịch thông minh được xây dựng bằng **Multi-Agent Systems (MAS)**, sử dụng **LangChain**, **LangGraph**, và **LangSmith** để tạo lịch trình du lịch cá nhân hóa tự động.

### Mục Tiêu
- Tạo lịch trình du lịch hoàn chỉnh trong vài phút
- Tối ưu hóa chi phí, thời gian và trải nghiệm
- Hỗ trợ 63 tỉnh thành Việt Nam
- Tích hợp AI để đưa ra gợi ý thông minh

### Công Nghệ Core
- **Backend**: Django 5.0.1 + Django REST Framework
- **AI Framework**: LangChain 1.x + LangGraph 1.x
- **LLM**: OpenAI GPT-4/GPT-4o-mini, Groq (GPT-OSS-120B, Llama)
- **Vector DB**: ChromaDB (RAG)
- **Monitoring**: LangSmith
- **Database**: SQLite (dev) / PostgreSQL (production)

---

## 🏗️ Kiến Trúc Hệ Thống

### State Configuration

**TravelPlanningState được cấu hình tại**: `agents/state.py`

- **Type**: `TypedDict` với `total=False` (tất cả fields đều optional)
- **Purpose**: Shared state giữa các agents trong LangGraph workflow
- **Structure**: 
  - User Input fields (origin, destination, days, etc.)
  - Agent Output fields (transport, flight, hotels, etc.)
  - Workflow Metadata (status, current_step, completed_steps)
  - Error fields (transport_error, flight_error, etc.)

**LangGraph StateGraph Configuration**: `agents/langgraph_workflow.py`

```python
# Tạo StateGraph với TravelPlanningState
workflow = StateGraph(TravelPlanningState)

# LangGraph sử dụng default reducer: dict.update()
# Không có reducer function tùy chỉnh
self.app = self.graph.compile(checkpointer=memory)
```

### Kiến Trúc Tổng Thể

```
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND LAYER                           │
│   Django Templates (HTML/CSS/JS)                            │
│   - Landing Page                                            │
│   - Travel Plan Workflow (4 Steps)                          │
│   - Places Search                                           │
│   - AI Chat Interface                                       │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/REST API
┌────────────────────────▼────────────────────────────────────┐
│                   DJANGO BACKEND                            │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │  REST API   │  │  Multi-Agent │  │  Data Models    │   │
│  │  Endpoints  │──│  Orchestrator │──│  (SQLite/PostgreSQL)│
│  └─────────────┘  └──────┬───────┘  └─────────────────┘   │
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
│  • LangChain LLM (GPT-4/GPT-4o-mini/Groq)                   │
│  • LangSmith Tracing & Monitoring                            │
│  • Retry Logic & Error Handling                              │
│  • State Management (TravelPlanningState)                    │
└────────────────────────────┬─────────────────────────────────┘
                             │
┌────────────────────────────▼───────────────────────────────┐
│                     RAG ENGINE                             │
│  ┌──────────────┐  ┌──────────────┐  ┌─────────────────┐   │
│  │  Embeddings  │──│ Vector Store │──│  LLM (GPT-4)    │   │
│  │  (OpenAI)    │  │  (ChromaDB)  │  │                 │   │
│  └──────────────┘  └──────────────┘  └─────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Luồng Xử Lý Request

1. **User Input** → Frontend (Django Templates)
2. **API Request** → Django REST API Endpoints
3. **Orchestration** → TravelPlannerOrchestrator
4. **Workflow Execution** → LangGraph Workflow
5. **Agent Execution** → 7 Specialized Agents
6. **Tool Execution** → External APIs & Database
7. **Response** → JSON Response → Frontend Display

---

## 🤖 Multi-Agent System

### 1. Orchestrator Agent
**Vai trò**: Điều phối toàn bộ workflow, quản lý thứ tự thực thi các agents

**Chức năng**:
- Nhận yêu cầu từ người dùng
- Phân tích và giao nhiệm vụ cho các agents
- Quản lý state giữa các agents
- Tổng hợp kết quả từ tất cả agents
- Xử lý lỗi và retry logic

**Tools sử dụng**:
- Không có tools riêng, chỉ điều phối các agents khác

**Luồng thực thi**:
```
OrchestratorAgent.execute()
  ├─► TransportAgent.execute()
  ├─► FlightAgent.execute() (conditional)
  ├─► AccommodationAgent.execute()
  ├─► ActivitiesAgent.execute()
  ├─► BudgetAgent.execute()
  └─► PlanningAgent.execute()
```

---

### 2. Transport Agent
**Vai trò**: Tính toán khoảng cách, thời gian di chuyển và đề xuất phương tiện phù hợp

**Chức năng**:
- Geocode địa điểm (origin, destination)
- Tính khoảng cách và thời gian di chuyển
- Đề xuất phương tiện (flight, bus, train, car, motorcycle)
- Tính chi phí vận chuyển

**Tools sử dụng**:
- `geo_tools.py`: Geocoding và routing
  - VietMap API (ưu tiên)
  - OpenRouteService (fallback)
  - OSRM (fallback)
  - Haversine distance (fallback cuối)
- `transport_tools.py`: Tính toán chi phí vận chuyển
  - `_calculate_ground_transport_cost()`: Tính chi phí xe buýt, taxi, xe máy
  - `_estimate_flight_cost()`: Ước tính chi phí máy bay
  - `suggest_transport_method()`: Đề xuất phương tiện dựa trên khoảng cách

**Input State**:
```python
{
    'origin': str,  # Điểm xuất phát
    'destination': str,  # Điểm đến
    'travelers': int,  # Số người
    'travel_style': str  # Phong cách du lịch
}
```

**Output State**:
```python
{
    'transport': {
        'distance_km': float,
        'duration_minutes': float,
        'suggested_method': str,  # 'flight', 'bus', 'train', 'car', 'motorcycle'
        'estimated_cost_vnd': float
    },
    'transport_cost': float
}
```

**Logic đề xuất phương tiện**:
- **Flight**: Khoảng cách > 500km hoặc thời gian > 8h
- **Train**: Khoảng cách 200-500km, có tuyến đường sắt
- **Bus**: Khoảng cách 100-500km
- **Car/Motorcycle**: Khoảng cách < 300km, travel_style = 'adventure'
- **Taxi/Grab**: Khoảng cách < 100km, travel_style = 'luxury'

---

### 3. Flight Agent
**Vai trò**: Tìm kiếm và so sánh giá vé máy bay

**Chức năng**:
- Tìm sân bay gần nhất cho origin và destination
- Tính chi phí di chuyển từ origin → sân bay đi
- Tìm kiếm giá vé máy bay
- Tính chi phí di chuyển từ sân bay đến → destination
- Tổng hợp chi phí vận chuyển đầy đủ

**Tools sử dụng**:
- `flight_tools.py`: Tìm kiếm vé máy bay
  - FlightAPI.io (ưu tiên)
  - Amadeus API (nếu có key)
  - SerpAPI (fallback)
  - Travelpayouts API (fallback)
- `airport_utils.py`: Quản lý sân bay
  - `get_nearest_airport()`: Tìm sân bay gần nhất
  - `calculate_airport_transport_cost()`: Tính chi phí di chuyển đến/đi sân bay
- `geo_tools.py`: Tính khoảng cách đến sân bay

**Input State**:
```python
{
    'origin': str,  # IATA code hoặc tên thành phố
    'destination': str,  # IATA code hoặc tên thành phố
    'departure_date': str,  # YYYY-MM-DD
    'return_date': str,  # YYYY-MM-DD (optional)
    'passengers': int,  # Số người
    'cabin_class': str  # 'economy', 'business', 'first'
}
```

**Output State**:
```python
{
    'flight': {
        'airline': str,
        'flight_number': str,
        'departure_time': str,
        'arrival_time': str,
        'departure_airport': str,
        'arrival_airport': str,
        'price_vnd': float,
        'currency': str
    },
    'transport_breakdown': {
        'origin_to_airport': {...},
        'flight': {...},
        'airport_to_dest': {...},
        'total_vnd': float
    }
}
```

**Priority của Flight APIs**:
1. Amadeus API (nếu có key)
2. FlightAPI.io
3. SerpAPI
4. Travelpayouts API

---

### 4. Accommodation Agent
**Vai trò**: Tìm kiếm và đề xuất khách sạn/resort phù hợp

**Chức năng**:
- Tìm kiếm khách sạn tại destination
- Lọc theo travel_style (budget, standard, luxury)
- Tính chi phí lưu trú
- Đề xuất khách sạn phù hợp nhất

**Tools sử dụng**:
- `accommodation_tools.py`: Tìm kiếm khách sạn
  - SerpAPI (Google Hotels)
  - Database fallback (DiaDiem với loaiDiaDiem='khach_san')
  - `calculate_total_accommodation_cost()`: Tính tổng chi phí
- `travel_styles.py`: Định nghĩa travel styles và multipliers

**Input State**:
```python
{
    'destination': str,
    'check_in': str,  # YYYY-MM-DD
    'check_out': str,  # YYYY-MM-DD
    'nights': int,  # Số đêm
    'travelers': int,
    'rooms': int,
    'travel_style': str
}
```

**Output State**:
```python
{
    'hotels': [
        {
            'name': str,
            'address': str,
            'price_per_night': float,
            'rating': float,
            'amenities': list,
            'images': list
        }
    ],
    'selected_hotel': {...},  # Khách sạn được chọn
    'accommodation_cost': float
}
```

**Logic lọc khách sạn**:
- **Budget**: Giá < 500,000 VNĐ/đêm
- **Standard**: Giá 500,000 - 2,000,000 VNĐ/đêm
- **Luxury**: Giá > 2,000,000 VNĐ/đêm

---

### 5. Activities Agent
**Vai trò**: Tìm kiếm địa điểm tham quan và nhà hàng

**Chức năng**:
- Tìm địa điểm tham quan tại destination
- Tìm nhà hàng phù hợp
- Tính chi phí hoạt động và ăn uống
- Lọc theo travel_style và interests

**Tools sử dụng**:
- `activities_tools.py`: Tìm kiếm địa điểm
  - Vector DB (ChromaDB) - RAG search
  - Database (DiaDiem) - Fallback
  - SerpAPI (Google Places) - Enrichment
- `serpapi_tools.py`: Tìm kiếm nhà hàng
  - `search_restaurants()`: Tìm nhà hàng với SerpAPI
- `vector_db.py`: Semantic search trong ChromaDB
- `semantic_place_classifier.py`: Phân loại địa điểm bằng LLM

**Input State**:
```python
{
    'destination': str,
    'travel_style': str,
    'interests': list,  # ['beach', 'culture', 'food', ...]
    'days': int,
    'travelers': int
}
```

**Output State**:
```python
{
    'activities': [
        {
            'name': str,
            'type': str,  # 'dia_danh', 'giai_tri', 'mua_sam'
            'address': str,
            'price': float,
            'rating': float,
            'description': str,
            'opening_hours': str,
            'best_time_to_visit': str
        }
    ],
    'restaurants': [
        {
            'name': str,
            'address': str,
            'price_level': str,  # 'budget', 'moderate', 'expensive'
            'price': float,  # VNĐ
            'rating': float,
            'cuisine': str
        }
    ],
    'activities_cost': float,
    'dining_cost': float,
    'dining_breakdown': {
        'breakfast': float,
        'lunch': float,
        'dinner': float,
        'snacks': float
    }
}
```

**Logic tìm kiếm**:
1. **RAG Search**: Tìm trong ChromaDB bằng semantic similarity
2. **Database Fallback**: Query DiaDiem với filters
3. **SerpAPI Enrichment**: Làm giàu thông tin từ Google Places
4. **LLM Classification**: Phân loại địa điểm bằng LLM nếu cần

**Lọc địa điểm**:
- Loại bỏ: `loaiDiaDiem` = 'nha_hang', 'khach_san', 'co_so_luu_tru'
- Loại bỏ: Tên chứa "nhà nghỉ", "khách sạn", "hotel", "resort", "homestay"

---

### 6. Budget Agent
**Vai trò**: Tính toán và phân tích ngân sách tổng thể

**Chức năng**:
- Tổng hợp chi phí từ tất cả agents
- Phân tích phân bổ ngân sách
- So sánh với max_budget (nếu có)
- Đề xuất tối ưu hóa chi phí

**Tools sử dụng**:
- `budget_tools.py`: Tính toán ngân sách
  - `calculate_total_budget()`: Tổng hợp tất cả chi phí
  - `calculate_budget_allocation()`: Phân bổ theo hạng mục
  - `optimize_budget()`: Tối ưu hóa chi phí
- `travel_styles.py`: Áp dụng multipliers theo travel_style

**Input State**:
```python
{
    'transport_cost': float,
    'accommodation_cost': float,
    'activities_cost': float,
    'dining_cost': float,
    'travelers': int,
    'days': int,
    'travel_style': str,
    'max_budget': float  # Optional
}
```

**Output State**:
```python
{
    'budget': {
        'total_cost': float,
        'cost_per_person': float,
        'cost_per_day': float,
        'breakdown': {
            'transport': float,
            'accommodation': float,
            'activities': float,
            'dining': float
        },
        'allocation_percentage': {
            'transport': float,  # %
            'accommodation': float,
            'activities': float,
            'dining': float
        }
    },
    'budget_allocation': {...},
    'within_budget': bool,  # So với max_budget
    'optimization_suggestions': list
}
```

**Logic tính toán**:
- Tổng chi phí = Transport + Accommodation + Activities + Dining
- Chi phí/người = Tổng chi phí / Số người
- Chi phí/ngày = Tổng chi phí / Số ngày
- Phân bổ % = (Chi phí hạng mục / Tổng chi phí) * 100

**Travel Style Multipliers**:
- **Budget**: 0.8x (giảm 20%)
- **Standard**: 1.0x (không đổi)
- **Luxury**: 1.5x (tăng 50%)

**Lưu ý**: Multiplier chỉ áp dụng cho ước tính, không áp dụng cho giá thực tế từ API.

---

### 7. Planning Agent
**Vai trò**: Tạo lịch trình chi tiết theo ngày và thời gian

**Chức năng**:
- Tạo timeline chi tiết cho từng ngày
- Phân bổ hoạt động theo thời gian
- Tối ưu thứ tự tham quan
- Tạo mô tả lịch trình bằng LLM
- Format output thành JSON chuẩn

**Tools sử dụng**:
- `planning_tools.py`: Tạo lịch trình
  - `_create_timeline()`: Tạo timeline cho từng ngày
  - `_score_activities()`: Đánh giá và sắp xếp hoạt động
  - `_optimize_route()`: Tối ưu thứ tự tham quan
  - `get_llm()`: Lấy LLM instance (Groq → GPT-OSS-120B → OpenAI)
- `itinerary_formatter.py`: Format output
  - `format_state_to_json()`: Chuyển state sang JSON (LICHTRINH, DIADIEM, LICHTRINH_DIADIEM)
  - `generate_itinerary_description()`: Tạo mô tả bằng LLM

**Input State**:
```python
{
    'origin': str,
    'destination': str,
    'start_date': str,
    'days': int,
    'travelers': int,
    'travel_style': str,
    'activities': list,
    'restaurants': list,
    'selected_hotel': dict,
    'transport': dict
}
```

**Output State**:
```python
{
    'itinerary': {
        'days': [
            {
                'day': int,
                'date': str,  # YYYY-MM-DD
                'start_time': str,  # HH:MM
                'end_time': str,  # HH:MM
                'activities': [
                    {
                        'time': str,  # HH:MM
                        'activity': str,
                        'place': dict,
                        'duration_minutes': int,
                        'type': str  # 'activity', 'meal', 'transport', 'personal', 'user_selected'
                    }
                ]
            }
        ]
    },
    'itinerary_json': {
        'LICHTRINH': [...],
        'DIADIEM': [...],
        'LICHTRINH_DIADIEM': [...]
    },
    'itinerary_description': str  # LLM-generated natural language description
}
```

**Logic tạo timeline**:
1. **Phân bổ thời gian**: Mỗi ngày từ 8:00 - 22:00
2. **Sắp xếp hoạt động**: Theo thứ tự ưu tiên và vị trí địa lý
3. **Thêm bữa ăn**: Breakfast (8:00), Lunch (12:00), Dinner (18:00)
4. **Thêm personal time**: Khoảng trống cho hoạt động cá nhân
5. **Tối ưu route**: Sắp xếp theo khoảng cách giữa các địa điểm

**LLM Description Generation**:
- Sử dụng Groq (ưu tiên) hoặc OpenAI
- Prompt: Chuyển đổi JSON thành mô tả tự nhiên
- Bao gồm: Thời gian, lịch trình, phương tiện, lưu ý

---

## 🔄 Luồng Dữ Liệu và Sự Kiện

### Luồng Dữ Liệu Tổng Thể

```
User Input (Frontend)
    │
    ▼
API Endpoint (Django REST)
    │
    ▼
TravelPlannerOrchestrator
    │
    ▼
LangGraph Workflow
    │
    ├─► Transport Agent
    │   ├─► geo_tools.geocode()
    │   ├─► geo_tools.calculate_distance_time()
    │   └─► transport_tools.suggest_transport_method()
    │
    ├─► Flight Agent (conditional)
    │   ├─► airport_utils.get_nearest_airport()
    │   ├─► flight_tools.search_flight_prices()
    │   └─► geo_tools.calculate_distance_time()
    │
    ├─► Accommodation Agent
    │   ├─► accommodation_tools.search_hotels()
    │   └─► accommodation_tools.calculate_total_accommodation_cost()
    │
    ├─► Activities Agent
    │   ├─► vector_db.search_places() (RAG)
    │   ├─► activities_tools.search_activities()
    │   ├─► serpapi_tools.search_restaurants()
    │   └─► semantic_place_classifier.classify()
    │
    ├─► Budget Agent
    │   └─► budget_tools.calculate_total_budget()
    │
    └─► Planning Agent
        ├─► planning_tools._create_timeline()
        ├─► itinerary_formatter.format_state_to_json()
        └─► itinerary_formatter.generate_itinerary_description()
            │
            └─► LLM (Groq/OpenAI)
    │
    ▼
Final State (JSON Response)
    │
    ▼
Frontend Display
```

### State Management

**TravelPlanningState** (TypedDict) được truyền giữa các agents:

**Định nghĩa State**: `agents/state.py`

```python
class TravelPlanningState(TypedDict, total=False):
    # User Input
    origin: Optional[str]
    destination: Optional[str]
    start_date: Optional[str]
    days: Optional[int]
    travelers: Optional[int]
    travel_style: Optional[str]
    
    # Agent Outputs
    transport: Optional[Dict[str, Any]]
    transport_cost: Optional[float]
    flight: Optional[Dict[str, Any]]
    hotels: Optional[List[Dict[str, Any]]]
    selected_hotel: Optional[Dict[str, Any]]
    accommodation_cost: Optional[float]
    activities: Optional[List[Dict[str, Any]]]
    restaurants: Optional[List[Dict[str, Any]]]
    activities_cost: Optional[float]
    dining_cost: Optional[float]
    budget: Optional[Dict[str, Any]]
    itinerary: Optional[Dict[str, Any]]
    itinerary_json: Optional[Dict[str, Any]]
    itinerary_description: Optional[str]
    
    # Workflow Metadata
    status: Optional[str]  # 'success', 'error', 'in_progress'
    current_step: Optional[str]
    completed_steps: Optional[List[str]]
```

**Cách Agents Xử Lý State**:

1. **Mỗi agent nhận toàn bộ TravelPlanningState**:
   ```python
   async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
       # Agent nhận toàn bộ state
       origin = state.get('origin')  # Chỉ đọc field cần thiết
       destination = state.get('destination')
   ```

2. **Agent chỉ đọc các fields cần thiết**:
   - TransportAgent: Đọc `origin`, `destination`
   - FlightAgent: Đọc `origin`, `destination`, `start_date`, `travelers`
   - AccommodationAgent: Đọc `destination`, `check_in`, `check_out`, `travelers`
   - ActivitiesAgent: Đọc `destination`, `travel_style`, `interests`
   - BudgetAgent: Đọc tất cả cost fields
   - PlanningAgent: Đọc tất cả data để tạo itinerary

3. **Agent trả về state đã được cập nhật**:
   ```python
   # TransportAgent chỉ update các fields của mình
   state['transport'] = {...}
   state['transport_cost'] = 1000000
   state['transport_error'] = None
   return state  # Trả về toàn bộ state, nhưng chỉ update fields của agent
   ```

4. **LangGraph tự động merge state**:
   - LangGraph sử dụng **default reducer**: `dict.update()`
   - Khi node trả về state, LangGraph sẽ merge bằng cách **ghi đè** các keys có trong return value
   - **KHÔNG** sử dụng `PartialStateUpdate` (agents trả về toàn bộ state dictionary)
   - **KHÔNG** có reducer function tùy chỉnh

**Ví dụ State Flow**:

```python
# Initial state
state = {
    'origin': 'Hà Nội',
    'destination': 'Hồ Chí Minh',
    'days': 3,
    'travelers': 2
}

# TransportAgent execute
result = await transport_agent.execute(state)
# result = {
#     'origin': 'Hà Nội',  # Giữ nguyên
#     'destination': 'Hồ Chí Minh',  # Giữ nguyên
#     'days': 3,  # Giữ nguyên
#     'travelers': 2,  # Giữ nguyên
#     'transport': {...},  # MỚI - TransportAgent thêm vào
#     'transport_cost': 2000000  # MỚI - TransportAgent thêm vào
# }

# LangGraph merge: state.update(result)
# State sau merge = result (vì dict.update() ghi đè các keys)
```

**Lưu ý**:
- Agents **KHÔNG** sử dụng `PartialStateUpdate` từ LangGraph
- Agents trả về toàn bộ state dictionary (nhưng chỉ update các fields của mình)
- LangGraph tự động merge bằng `dict.update()` - ghi đè các keys có trong return value
- Các fields không được update sẽ giữ nguyên giá trị cũ

### Event Flow trong LangGraph

1. **Entry Point**: `transport` node
2. **Conditional Edge**: `transport` → `flight` (nếu suggested_method == 'flight') hoặc `accommodation`
3. **Sequential Edges**:
   - `flight` → `accommodation`
   - `accommodation` → `activities`
   - `activities` → `budget`
   - `budget` → `planning`
   - `planning` → `END`

### Error Handling và Retry

- Mỗi node có `@retry_with_backoff` decorator
- Retry config: `max_retries=2`, `initial_delay=1.0`
- Error classification: `RETRYABLE`, `PERMANENT`, `NETWORK`
- Errors được lưu trong state: `transport_error`, `flight_error`, etc.
- Workflow tiếp tục ngay cả khi một agent fail (graceful degradation)

---

## 🧠 Vai Trò của LangGraph và LLM

### LangGraph

**Vai trò**:
1. **State Management**: Quản lý state giữa các agents
2. **Workflow Orchestration**: Điều phối thứ tự thực thi agents
3. **Conditional Logic**: Quyết định routing dựa trên state
4. **Checkpointing**: Lưu trữ state để có thể resume
5. **Tracing**: Tích hợp với LangSmith để monitor

**Cấu trúc Graph**:
```python
workflow = StateGraph(TravelPlanningState)

# Add nodes
workflow.add_node("transport", _transport_node)
workflow.add_node("flight", _flight_node)
workflow.add_node("accommodation", _accommodation_node)
workflow.add_node("activities", _activities_node)
workflow.add_node("budget", _budget_node)
workflow.add_node("planning", _planning_node)

# Define edges
workflow.set_entry_point("transport")
workflow.add_conditional_edges("transport", _should_use_flight, {...})
workflow.add_edge("flight", "accommodation")
workflow.add_edge("accommodation", "activities")
workflow.add_edge("activities", "budget")
workflow.add_edge("budget", "planning")
workflow.add_edge("planning", END)
```

**Checkpointing**:
- Sử dụng `MemorySaver` (có thể nâng cấp lên `PostgresSaver`)
- Lưu state sau mỗi node execution
- Cho phép resume workflow nếu bị gián đoạn

### LLM (Large Language Models)

**Vai trò trong hệ thống**:

1. **Itinerary Description Generation** (Planning Agent):
   - Input: JSON structured data (LICHTRINH, DIADIEM, LICHTRINH_DIADIEM)
   - Output: Natural language description
   - Model: Groq (GPT-OSS-120B) → OpenAI (GPT-4o-mini)
   - Prompt: Chuyển đổi JSON thành mô tả tự nhiên, bao gồm thời gian, lịch trình, phương tiện, lưu ý

2. **Semantic Place Classification** (Activities Agent):
   - Input: Place information
   - Output: Classified place type
   - Model: OpenAI GPT-4o-mini
   - Purpose: Phân loại địa điểm khi không rõ ràng

3. **RAG (Retrieval-Augmented Generation)** (RAG Agent):
   - Vector search trong ChromaDB
   - LLM để generate answers từ retrieved context
   - Model: OpenAI GPT-4o-mini
   - Purpose: Chatbot tư vấn du lịch

**LLM Fallback Chain**:
1. **Groq** (nếu có `GROQ_API_KEY`):
   - Model: `openai/gpt-oss-120b` hoặc `llama-3.3-70b-versatile`
   - Ưu điểm: Nhanh, miễn phí (có giới hạn)
2. **GPT-OSS-120B** (nếu có `OPENAI_BASE_URL`):
   - Qua OpenRouter hoặc custom endpoint
3. **OpenAI GPT-4o-mini** (fallback cuối):
   - Model: `gpt-4o-mini`
   - Ưu điểm: Ổn định, chất lượng tốt

**LLM Configuration**:
```python
def get_llm():
    # Priority 1: Groq
    if GROQ_API_KEY:
        return ChatGroq(model=GROQ_MODEL, temperature=0.7)
    
    # Priority 2: GPT-OSS-120B (OpenRouter)
    if OPENAI_BASE_URL or model_name.startswith('openai/'):
        return ChatOpenAI(base_url=OPENAI_BASE_URL, model=model_name)
    
    # Priority 3: OpenAI
    return ChatOpenAI(model='gpt-4o-mini', temperature=0.7)
```

---

## 🛠️ Tools và Dependencies

### Tools theo Agent

#### Transport Agent
- **geo_tools.py**:
  - `geocode()`: Chuyển đổi địa chỉ → tọa độ
  - `calculate_distance_time()`: Tính khoảng cách và thời gian
  - Providers: VietMap → OpenRouteService → OSRM → Haversine
- **transport_tools.py**:
  - `suggest_transport_method()`: Đề xuất phương tiện
  - `_calculate_ground_transport_cost()`: Tính chi phí
  - `_estimate_flight_cost()`: Ước tính chi phí máy bay

#### Flight Agent
- **flight_tools.py**:
  - `search_flight_prices()`: Tìm kiếm vé máy bay
  - APIs: FlightAPI.io → Amadeus → SerpAPI → Travelpayouts
- **airport_utils.py**:
  - `get_nearest_airport()`: Tìm sân bay gần nhất
  - `calculate_airport_transport_cost()`: Tính chi phí đến/đi sân bay

#### Accommodation Agent
- **accommodation_tools.py**:
  - `search_hotels()`: Tìm kiếm khách sạn
  - `calculate_total_accommodation_cost()`: Tính tổng chi phí
  - APIs: SerpAPI (Google Hotels) + Database fallback

#### Activities Agent
- **activities_tools.py**:
  - `search_activities()`: Tìm địa điểm tham quan
  - `_query_fallback_activities_from_db()`: Query database
- **vector_db.py**:
  - `search_places()`: Semantic search trong ChromaDB
- **serpapi_tools.py**:
  - `search_restaurants()`: Tìm nhà hàng
- **semantic_place_classifier.py**:
  - `classify_place()`: Phân loại địa điểm bằng LLM

#### Budget Agent
- **budget_tools.py**:
  - `calculate_total_budget()`: Tổng hợp chi phí
  - `calculate_budget_allocation()`: Phân bổ ngân sách
  - `optimize_budget()`: Tối ưu hóa

#### Planning Agent
- **planning_tools.py**:
  - `_create_timeline()`: Tạo timeline
  - `_score_activities()`: Đánh giá hoạt động
  - `_optimize_route()`: Tối ưu route
  - `get_llm()`: Lấy LLM instance
- **itinerary_formatter.py**:
  - `format_state_to_json()`: Format JSON
  - `generate_itinerary_description()`: Tạo mô tả bằng LLM

### External APIs

1. **VietMap**:
   - Geocoding, Routing, Search Places
   - API v3: `/search/v3`, `/place/v3`, `/route/v3`, `/migrate-address/v3`

2. **OpenRouteService**:
   - Routing (fallback)
   - Based on OpenStreetMap

3. **OSRM**:
   - Open Source Routing Machine
   - Routing (fallback)

4. **FlightAPI.io**:
   - Flight price search
   - Priority: 2 (sau Amadeus)

5. **SerpAPI**:
   - Google Search, Google Hotels, Google Places
   - Flight search (fallback)
   - Restaurant search

6. **Amadeus**:
   - Flight search (nếu có key)
   - Priority: 1

7. **OpenAI**:
   - GPT-4o-mini, Embeddings
   - LLM cho descriptions và RAG

8. **Groq**:
   - GPT-OSS-120B, Llama models
   - Fast LLM inference

9. **ChromaDB**:
   - Vector database
   - RAG search

---

## ✨ Tính Năng Chính

### 1. Travel Plan Generation (4 Steps)

**Step 1: Location Selection**
- Chọn điểm đi và điểm đến
- Autocomplete với VietMap
- Tính khoảng cách và thời gian
- Đề xuất phương tiện

**Step 2: Travel Details**
- Số ngày, số người
- Ngày bắt đầu
- Phong cách du lịch (budget, standard, luxury)
- Sở thích (optional)

**Step 3: Accommodation & Activities**
- Tìm kiếm khách sạn
- Tìm địa điểm tham quan
- Tìm nhà hàng
- Hiển thị chi phí ước tính

**Step 4: Confirm & Plan**
- Tổng hợp ngân sách
- Lịch trình chi tiết theo ngày
- LLM-generated description
- JSON export

### 2. RAG-Powered Recommendations

- **Vector Database**: ChromaDB với 50K+ địa điểm
- **Semantic Search**: Tìm kiếm dựa trên ý nghĩa, không chỉ keyword
- **LLM Enhancement**: Làm giàu thông tin bằng LLM

### 3. AI Chat Assistant

- **RAG Agent**: Kết hợp vector search và web search
- **Context-Aware**: Hiểu ngữ cảnh câu hỏi
- **Multi-Source**: Từ database, vector DB, và web

### 4. Smart Budget Calculation

- Tổng hợp chi phí từ tất cả hạng mục
- Phân tích phân bổ ngân sách
- So sánh với ngân sách tối đa
- Đề xuất tối ưu hóa

### 5. LLM-Generated Itinerary Descriptions

- Tự động tạo mô tả lịch trình bằng ngôn ngữ tự nhiên
- Bao gồm: Thời gian, lịch trình, phương tiện, lưu ý
- Format: Văn xuôi, dễ đọc, hướng tới người dùng

### 6. Multi-Provider Fallback

- **Geocoding**: VietMap → OpenRouteService → OSRM → Haversine
- **Routing**: VietMap → OpenRouteService → OSRM → Haversine
- **Flight Search**: Amadeus → FlightAPI → SerpAPI → Travelpayouts
- **LLM**: Groq → GPT-OSS-120B → OpenAI

---

## 🗄️ Cấu Trúc Cơ Sở Dữ Liệu

### Core Tables

#### 1. TINHTHANH (Provinces/Cities)
```sql
CREATE TABLE TINHTHANH (
    maTinhThanh INTEGER PRIMARY KEY AUTOINCREMENT,
    tenTinhThanh VARCHAR(255) UNIQUE NOT NULL,
    moTa TEXT,
    anhDaiDien VARCHAR(500),
    viDo FLOAT,
    kinhDo FLOAT,
    created_at DATETIME,
    updated_at DATETIME
);
```
- **Total**: 63 tỉnh thành
- **Indexes**: `tenTinhThanh`

#### 2. DIADIEM (Places)
```sql
CREATE TABLE DIADIEM (
    maDiaDiem INTEGER PRIMARY KEY AUTOINCREMENT,
    tenDiaDiem VARCHAR(255) NOT NULL,
    moTa TEXT,
    diaChi VARCHAR(500),
    maTinhThanh INTEGER NOT NULL,
    loaiDiaDiem VARCHAR(50) NOT NULL,
    viDo FLOAT,
    kinhDo FLOAT,
    giaVe FLOAT,
    gioMoCua VARCHAR(50),
    gioDongCua VARCHAR(50),
    dienThoai VARCHAR(20),
    website VARCHAR(500),
    danhGiaTrungBinh FLOAT DEFAULT 0.0,
    soLuotDanhGia INTEGER DEFAULT 0,
    soLuotXem INTEGER DEFAULT 0,
    trangThai VARCHAR(20) DEFAULT 'active',
    thoiGianTotNhat TEXT,
    ghiChu TEXT,
    FOREIGN KEY (maTinhThanh) REFERENCES TINHTHANH(maTinhThanh)
);
```
- **Total**: 50K+ địa điểm
- **Indexes**: 
  - `(maTinhThanh, loaiDiaDiem)`
  - `danhGiaTrungBinh`
  - `trangThai`
- **loaiDiaDiem**: 'dia_danh', 'nha_hang', 'khach_san', 'giai_tri', 'mua_sam', 'khac'

#### 3. HINHANHDIADIEM (Place Images)
```sql
CREATE TABLE HINHANHDIADIEM (
    maHinhAnh INTEGER PRIMARY KEY AUTOINCREMENT,
    maDiaDiem INTEGER NOT NULL,
    urlHinhAnh VARCHAR(500) NOT NULL,
    moTa TEXT,
    thuTu INTEGER DEFAULT 0,
    FOREIGN KEY (maDiaDiem) REFERENCES DIADIEM(maDiaDiem)
);
```

#### 4. LICHTRINH (Itineraries)
```sql
CREATE TABLE LICHTRINH (
    maLichTrinh INTEGER PRIMARY KEY AUTOINCREMENT,
    tenLichTrinh VARCHAR(255),
    maNguoiDung INTEGER,
    diemXuatPhat VARCHAR(255),
    diemDen VARCHAR(255),
    ngayBatDau DATE,
    ngayKetThuc DATE,
    soNguoi INTEGER,
    phongCach VARCHAR(50),
    trangThai VARCHAR(20),
    created_at DATETIME,
    updated_at DATETIME
);
```

#### 5. LICHTRINH_DIADIEM (Itinerary Places)
```sql
CREATE TABLE LICHTRINH_DIADIEM (
    maLichTrinhDiaDiem INTEGER PRIMARY KEY AUTOINCREMENT,
    maLichTrinh INTEGER NOT NULL,
    maDiaDiem INTEGER NOT NULL,
    ngay INTEGER,
    thuTu INTEGER,
    thoiGian TIME,
    FOREIGN KEY (maLichTrinh) REFERENCES LICHTRINH(maLichTrinh),
    FOREIGN KEY (maDiaDiem) REFERENCES DIADIEM(maDiaDiem)
);
```

### Vector Database (ChromaDB)

- **Collection**: `places`
- **Embeddings**: OpenAI `text-embedding-3-small`
- **Metadata**: 
  - `maDiaDiem`, `tenDiaDiem`, `loaiDiaDiem`, `maTinhThanh`
  - `danhGiaTrungBinh`, `giaVe`, `diaChi`
- **Total Documents**: 50K+ places
- **Purpose**: Semantic search cho RAG

---

## 🔌 API Endpoints

### Travel Planning Workflow

**POST** `/api/v1/travel-plans/step1/`
- Location selection
- Input: `origin`, `destination`
- Output: Distance, time, suggested transport

**POST** `/api/v1/travel-plans/step2/`
- Travel details
- Input: `days`, `travelers`, `start_date`, `travel_style`
- Output: Confirmation

**POST** `/api/v1/travel-plans/step3/`
- Accommodation & activities
- Input: State from step 2
- Output: Hotels, activities, restaurants, costs

**POST** `/api/v1/travel-plans/step4/`
- Confirm & generate plan
- Input: State from step 3
- Output: Complete itinerary, budget, JSON, description

### Places

**GET** `/api/v1/places/`
- List places (paginated)

**GET** `/api/v1/places/{id}/`
- Place details

**GET** `/api/v1/places/search/?q=...`
- Search places

### Chat

**POST** `/api/v1/chat/`
- AI chat assistant
- Input: `message`, `context`
- Output: `response`, `sources`

---

## 📊 Performance & Optimization

### Caching
- **Redis**: Cache API responses (geocoding, routing, flight search)
- **TTL**: 7 days cho geocoding, 1 day cho flight search

### Retry Logic
- **Max Retries**: 2
- **Backoff**: Exponential (1s, 2s)
- **Error Classification**: RETRYABLE, PERMANENT, NETWORK

### Async Execution
- **LangGraph**: Async workflow execution
- **Agents**: Async `execute()` methods
- **Concurrent API calls**: Khi có thể

---

## 🔐 Security & Error Handling

### Error Handling
- **Graceful Degradation**: Workflow tiếp tục ngay cả khi một agent fail
- **Error Classification**: Phân loại lỗi để quyết định retry
- **Error Logging**: LangSmith tracing + Django logging

### Security
- **API Keys**: Lưu trong `.env`, không commit vào git
- **Input Validation**: Django serializers
- **SQL Injection**: Django ORM protection
- **XSS**: Django template auto-escaping

---

## 📈 Monitoring & Tracing

### LangSmith Integration
- **Tracing**: Tất cả agent executions
- **Metadata**: Agent name, step, input/output
- **Tags**: `travel-planner`, `langgraph-node`, agent-specific tags
- **Project**: `vi-vu-travel-planner`

### Logging
- **Structured Logging**: Python logging module
- **Log Levels**: INFO, WARNING, ERROR
- **Context**: Agent name, state, errors

---

## 🚀 Deployment Considerations

### Development
- **Database**: SQLite
- **Cache**: Redis (localhost)
- **Server**: Django development server

### Production (Recommended)
- **Database**: PostgreSQL
- **Cache**: Redis (cloud)
- **Server**: Gunicorn + Nginx
- **Static Files**: CDN hoặc S3
- **Monitoring**: LangSmith + Sentry

---

## 📝 Kết Luận

Vi Vu là một hệ thống lập kế hoạch du lịch thông minh sử dụng Multi-Agent Systems với LangGraph để điều phối 7 agents chuyên biệt. Hệ thống tích hợp nhiều external APIs, LLM, và vector database để tạo ra lịch trình du lịch cá nhân hóa, tối ưu và chi tiết.

**Điểm mạnh**:
- Kiến trúc modular, dễ mở rộng
- Fallback mechanisms đảm bảo reliability
- LLM integration cho natural language generation
- RAG-powered recommendations
- Comprehensive error handling

**Hướng phát triển**:
- Booking integration
- Real-time collaboration
- Mobile app
- Advanced ML models
- Multi-language support

---

**Tài liệu này được tạo tự động dựa trên codebase hiện tại.**
**Cập nhật lần cuối**: 2025-11-28

