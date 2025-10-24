# 🌍 HỆ THỐNG LẬP KẾ HOẠCH DU LỊCH THÔNG MINH
### Multi-Agent System for Travel Planning in Vietnam

---

## 🚀 CHẠY NHANH (2 BƯỚC)

```bash
# Bước 1: Di chuyển vào thư mục project
cd TRAVEL_PLANNER

# Bước 2: Chạy ứng dụng
python run_ui.py

# Mở browser tại: http://localhost:7861
```

**Xong! Hệ thống đã sẵn sàng!** 🎉

---

## 📋 TỔNG QUAN

Hệ thống **lập kế hoạch du lịch thông minh** sử dụng **10 AI Agents** làm việc đồng bộ với **LangGraph** để tạo ra kế hoạch du lịch hoàn hảo cho Việt Nam.

### ✨ Tính Năng Nổi Bật

- 🤖 **10 AI Agents** làm việc đồng bộ với LangGraph
- 💬 **Trợ Lý Chat AI** tư vấn 24/7 bằng GPT-4
- 📍 **50,000+ địa điểm** thực tế tại Việt Nam
- 💰 **Tối ưu ngân sách** thông minh với ML
- ⭐ **Gợi ý cá nhân hóa** theo sở thích
- 🗺️ **Lịch trình chi tiết** từng ngày
- 💾 **Cache thông minh** - tăng tốc 10x
- 🆓 **100% miễn phí** với Free APIs (540K+ requests/month)

---

## 🤖 10 AI AGENTS

### Layer 1: Data Collection
1. **API Collector** - Thu thập dữ liệu từ 5 APIs (LocationIQ, Geoapify, OpenWeather, Tavily, Nominatim)
2. **Web Scraper** - Tìm kiếm thông tin bổ sung từ web

### Layer 2: Data Processing  
3. **Data Processor** - Xử lý, làm sạch và chuẩn hóa 50,000+ địa điểm

### Layer 3: ML Analysis (Parallel Processing)
4. **Recommendation Engine** - Gợi ý ML-based (TF-IDF, Cosine Similarity, KMeans)
5. **Sentiment Analyzer** - Phân tích cảm xúc từ reviews
6. **Similarity Engine** - Tìm địa điểm tương tự
7. **Price Predictor** - Dự đoán chi phí và tối ưu ngân sách

### Layer 4: Planning
8. **Planner Agent** - Lập lịch trình chi tiết với GPT-4

### Layer 5: Research
9. **Researcher Agent** - Nghiên cứu và bổ sung thông tin địa phương

### Layer 6: Analytics
10. **Analytics Engine** - Phân tích tổng hợp và tạo báo cáo insights

### Bonus
- **Chat Assistant** - Tư vấn AI hội thoại

---

## 🏗️ KIẾN TRÚC HỆ THỐNG

### Workflow Thực Thi

```
START → API Collector → Web Scraper
  ↓
Data Processor
  ↓
    ┌───────────┼───────────┬───────────┐
    │           │           │           │
Recommend   Sentiment   Similar    Price
Engine      Analyzer    Engine   Predictor
    │           │           │           │
    └───────────┴───────────┴───────────┘
                ↓
           Planner Agent
                ↓
         Researcher Agent
                ↓
        Analytics Engine
                ↓
              END
```

### Công Nghệ Sử Dụng

- **AI/ML**: OpenAI GPT-4, TF-IDF, Cosine Similarity, KMeans Clustering
- **Frameworks**: LangGraph, LangChain, AutoGen
- **Data**: Pandas, NumPy, Scikit-learn
- **UI**: Gradio (Python web UI)
- **APIs**: LocationIQ, Geoapify, OpenWeather, Tavily, Nominatim
- **Database**: SQLite (2 files: cache.db + data.db)
- **Web Scraping**: BeautifulSoup, Requests

---

## 📁 CẤU TRÚC PROJECT

```
TRAVEL_PLANNER/
├── app.py                      # 🚀 Main Gradio application
├── run_ui.py                   # Quick launcher
├── README.md                   # File này
│
├── agents/                     # 10 AI Agents
│   ├── api_collector_agent.py
│   ├── web_scraper_agent.py
│   ├── data_processor_agent.py
│   ├── recommendation_agent.py
│   ├── sentiment_analyzer_agent.py
│   ├── similarity_engine_agent.py
│   ├── price_predictor_agent.py
│   ├── planner.py
│   ├── researcher.py
│   ├── analytics_engine_agent.py
│   └── chat_assistant_agent.py
│
├── data/                       # 50,000+ địa điểm Việt Nam
│   ├── vietnam_all_places.csv
│   ├── hotels.csv / hotels_large.csv
│   ├── restaurants.csv / restaurants_large.csv
│   ├── attractions.csv / attractions_large.csv
│   ├── entertainment.csv
│   ├── family.csv
│   ├── foodandbeverage.csv
│   └── wellness.csv
│
├── data_collection/            # Data collection & scraping
│   ├── api_collector.py
│   ├── web_scraper.py
│   ├── data_processor.py
│   ├── real_data_provider.py
│   └── train_scraper.py
│
├── ml_models/                  # ML models
│   ├── recommendation_engine.py
│   ├── sentiment_analyzer.py
│   ├── similarity_engine.py
│   └── price_predictor.py
│
├── multi_agent_system/         # LangGraph workflow
│   └── langgraph_workflow.py
│
├── database/                   # Database management
│   ├── dual_db_manager.py      # ✅ Main database manager
│   ├── migrate_to_dual_db.py   # Migration script
│   ├── cache.db                # Cache database (temporary)
│   └── data.db                 # Data database (persistent)
│
├── config/                     # Configuration
│   ├── settings.py
│   └── api_keys.py
│
├── visualization/              # Analytics & visualization
│   ├── analytics_engine.py
│   ├── chart_generator.py
│   ├── dashboard_builder.py
│   └── report_generator.py
│
└── models/                     # Trained ML models
    ├── price_prediction_model.pkl
    ├── rating_prediction_model.pkl
    ├── recommendation_model.pkl
    └── sentiment_analysis_model.pkl
```

---

## 💾 DATABASE SYSTEM (2 FILES)

Hệ thống sử dụng **2 database files** để quản lý hiệu quả:

### **1. cache.db** - Temporary Data (Có thể xóa)
```sql
cache.db
├── api_cache          (Cache từ APIs)
├── web_cache          (Cache từ web scraping)
└── cache_stats        (Statistics)
```
- ⚡ Tăng tốc 10x cho requests đã cache
- 🔄 Auto expire sau 24 giờ
- 🗑️ Có thể xóa bất cứ lúc nào (sẽ regenerate)

### **2. data.db** - Persistent Data (Quan trọng!)
```sql
data.db
├── vietnam_places      (50,000+ địa điểm)
├── travel_plans        (Kế hoạch du lịch)
├── analytics_results   (Kết quả phân tích)
├── processed_places    (ML features)
└── user_history        (Lịch sử user)
```
- 💾 Lưu trữ lâu dài
- 🔒 Phải backup thường xuyên
- 📈 Data quan trọng

### Sử dụng Database

```python
from database.dual_db_manager import db_manager

# Cache operations
db_manager.set_api_cache(...)
cached = db_manager.get_api_cache(...)

# Data operations
db_manager.save_travel_plan(...)
places = db_manager.get_places_by_city('Hanoi')

# Maintenance
db_manager.clear_expired_cache()
db_manager.vacuum_databases()
```

---

## 🔑 CẤU HÌNH API KEYS

Cấu hình trong file `config/settings.py`:

```python
OPENAI_API_KEY = 'REDACTED_OPENAI_API_KEY'  # Please set this as an environment variable in your local .env or CI
MODEL = 'gpt-4o-mini'
```

### API Keys (Tất cả FREE hoặc Free Tier)

| API | Quota FREE | Chi phí | Mục đích |
|-----|------------|---------|----------|
| OpenAI | Credits | ~$5/month | AI Agents, GPT-4 |
| LocationIQ | 150K/month | $0 | Places, Geocoding |
| Geoapify | 360K/month | $0 | Places, Routing |
| OpenWeather | 30K/month | $0 | Thời tiết |
| Tavily | 1K/month | $0 | Web search |
| Nominatim | Unlimited | $0 | Geocoding backup |

**Tổng:** 540,000+ requests/month FREE | Chi phí: ~$5/month

---

## 💡 CÁCH SỬ DỤNG

### Giao Diện Web

```
┌────────────────────────────────────────────────────┐
│   🌍 HỆ THỐNG LẬP KẾ HOẠCH DU LỊCH THÔNG MINH    │
├────────────────────┬───────────────────────────────┤
│                    │                               │
│ 📝 THÔNG TIN       │ 📊 KẾ HOẠCH DU LỊCH          │
│ CHUYẾN ĐI          │                               │
│                    │ [Lịch trình chi tiết]         │
│ • Điểm đến        │ [Khách sạn gợi ý]             │
│ • Ngân sách       │ [Nhà hàng đề xuất]            │
│ • Số ngày         │ [Điểm tham quan]              │
│ • Sở thích        │ [Phân tích ngân sách]         │
│                    │                               │
│ 🚀 Tạo Kế Hoạch   │                               │
│                    │                               │
├────────────────────┴───────────────────────────────┤
│                                                    │
│ 💬 TRỢ LÝ DU LỊCH AI                             │
│ [Chat để được tư vấn và tự động điền form]        │
│                                                    │
└────────────────────────────────────────────────────┘
```

### 2 Cách Sử Dụng

**Cách 1: Điền Form Trực Tiếp**
1. Điền thông tin: Hà Nội, 10 triệu, 5 ngày, văn hóa
2. Nhấn "🚀 Tạo Kế Hoạch Du Lịch"
3. Nhận kết quả sau 10-30 giây

**Cách 2: Chat với AI (Khuyến nghị)**
1. Chat: "Tôi muốn đi Đà Nẵng 5 ngày, 15 triệu"
2. AI hiểu và hỏi thêm về sở thích
3. Nhấn "✨ Áp Dụng Vào Form"
4. Tự động điền form
5. Nhấn "🚀 Tạo Kế Hoạch"

### Kết Quả Bạn Nhận Được

```
================================================================================
KẾ HOẠCH DU LỊCH HÀ NỘI
================================================================================

📋 THÔNG TIN CHUYẾN ĐI
Điểm đến:    Hà Nội
Ngân sách:   10,000,000 VND
Số ngày:     5 ngày
...

📅 LỊCH TRÌNH CHI TIẾT
Ngày 1: Khám Phá Phố Cổ
  🌅 Sáng:   Check-in Khách sạn Sofitel Legend Metropole
  ☀️ Trưa:   Ăn trưa tại Phở Thìn Lò Đúc
  🌆 Chiều:  Tham quan Hồ Hoàn Kiếm
  🌙 Tối:    Dạo phố cổ, chợ đêm Hàng Đào

🏨 KHÁCH SẠN ĐỀ XUẤT
1. Sofitel Legend Metropole     ⭐ 4.8/5.0  💵 3,500,000 VND/đêm
2. Hanoi Pearl Hotel            ⭐ 4.5/5.0  💵 1,200,000 VND/đêm

🍜 NHÀ HÀNG GỢI Ý
1. Phở Thìn Lò Đúc             ⭐ 4.7/5.0  💵 50,000 VND/người
2. Bún Chả Hương Liên          ⭐ 4.6/5.0  💵 70,000 VND/người

💰 PHÂN BỔ NGÂN SÁCH
Khách sạn:    4,000,000 VND (40%)
Ăn uống:      3,000,000 VND (30%)
Di chuyển:    1,500,000 VND (15%)
Hoạt động:    1,500,000 VND (15%)
```

---

## ⚡ PERFORMANCE

### Tốc Độ
- **Lần đầu**: 10-30 giây (thu thập dữ liệu mới)
- **Có cache**: 2-5 giây (dùng dữ liệu đã lưu)
- **Offline**: < 1 giây (chỉ dùng local data)

### Hiệu Quả
- **Cache hit rate**: 70-80%
- **API cost**: ~$5/month
- **Savings**: 99.97% vs Google APIs
- **Free requests**: 540,000+/month

---

## 💰 CHI PHÍ SO SÁNH

### Nếu Dùng Google APIs (540K requests/month)
```
Google Places:      $9,180/month
Google Geocoding:   $2,700/month
Google Routes:      $5,400/month
────────────────────────────────
TỔNG:              $17,280/month 💸
```

### Setup Hiện Tại
```
OpenAI:             $5/month
Free APIs:          $0/month
────────────────────────────────
TỔNG:               $5/month ✅

TIẾT KIỆM: $17,275/month = $207,300/year
TIẾT KIỆM: 99.97% 🎉
```

---

## 🛠️ CÀI ĐẶT & YÊU CẦU

### Yêu Cầu Hệ Thống
- Python 3.8+
- 2GB RAM minimum
- Internet connection (cho APIs)

### Dependencies

```bash
pip install gradio langchain langchain_core langgraph openai
pip install pandas numpy scikit-learn beautifulsoup4 requests
pip install python-dotenv
```

### Hoặc Tất Cả Cùng Lúc

```bash
pip install gradio langchain langchain_core langgraph openai pandas numpy scikit-learn beautifulsoup4 requests python-dotenv
```

---

## 🔧 TROUBLESHOOTING

### Lỗi: `can't open file 'app.py'`
**Nguyên nhân**: Bạn chưa CD vào TRAVEL_PLANNER
```bash
# ✅ ĐÚNG
cd TRAVEL_PLANNER
python run_ui.py

# ❌ SAI
python run_ui.py  # Chưa vào folder
```

### Lỗi: `ModuleNotFoundError`
**Giải pháp**: Cài đặt dependencies
```bash
pip install gradio langchain langchain_core langgraph openai
```

### Lỗi: `Port already in use`
**Giải pháp**: Đổi port trong `run_ui.py`
```python
server_port=7862,  # Thay đổi thành port khác
```

### UI Không Mở
**Giải pháp**: Tự mở browser
```
http://localhost:7861
```

---

## 📚 VÍ DỤ SỬ DỤNG

### Ví Dụ 1: Chuyến Du Lịch Hà Nội
```
Điểm đến: Hà Nội
Ngân sách: 10,000,000 VND
Số ngày: 5
Số người: 2
Sở thích: văn hóa, ẩm thực

Kết quả:
- 5 ngày lịch trình chi tiết
- 10 khách sạn đề xuất
- 15 nhà hàng gợi ý
- 20 điểm tham quan
- Phân bổ ngân sách chi tiết
```

### Ví Dụ 2: Chuyến Du Lịch Đà Nẵng
```
Điểm đến: Đà Nẵng
Ngân sách: 15,000,000 VND
Số ngày: 7
Số người: 4
Sở thích: biển, thiên nhiên

Kết quả:
- 7 ngày bao gồm Hội An, Bà Nà Hills
- Khách sạn view biển
- Nhà hàng hải sản
- Tour Cù Lao Chàm
- Sunset Cruise
```

---

## 🎯 FEATURES ROADMAP

### Đã Hoàn Thành ✅
- [x] 10 AI Agents với LangGraph
- [x] Chat Assistant với GPT-4
- [x] 50,000+ địa điểm Việt Nam
- [x] ML-based recommendations
- [x] Weather integration
- [x] Routing & navigation
- [x] Dual database system (cache.db + data.db)
- [x] Vietnamese UI
- [x] Free APIs integration

### Kế Hoạch Tương Lai 🔮
- [ ] Mobile app (React Native)
- [ ] Voice input/output
- [ ] Multi-language support (English, Chinese, Korean)
- [ ] Social sharing
- [ ] Booking integration
- [ ] Real-time collaboration

---

## 📞 HỖ TRỢ

### Câu Hỏi Thường Gặp

**Q: Có tốn phí không?**
A: Chỉ ~$5/month cho OpenAI. Các API khác FREE (540K+ requests/month)

**Q: Cần API keys nào?**
A: Chỉ cần OPENAI_API_KEY trong `config/settings.py`. Các API khác optional.

**Q: Dữ liệu có chính xác không?**
A: Có! 50,000+ địa điểm thực tế + real-time API data + ML analysis

**Q: Làm sao để nhanh hơn?**
A: Hệ thống tự động cache. Lần 2 trở đi sẽ nhanh (2-5 giây)

**Q: Có hoạt động offline không?**
A: Có! Sử dụng 50K+ địa điểm local khi không có internet

**Q: Database .db là gì?**
A: SQLite files - cache.db (temporary) và data.db (persistent)

---

## 🗄️ DATABASE MANAGEMENT

### Clear Cache (khi cần fresh data)

```python
from database.dual_db_manager import db_manager

# Clear expired cache
db_manager.clear_expired_cache()

# Clear ALL cache (fresh start)
db_manager.clear_all_cache()
```

### Backup Data (quan trọng!)

```bash
# Backup data.db (chứa data quan trọng)
cp data.db backups/data_$(date +%Y%m%d).db

# cache.db không cần backup (sẽ regenerate)
```

### Database Statistics

```python
from database.dual_db_manager import db_manager

# Get statistics
stats = db_manager.get_all_stats()
print(f"Cache entries: {stats['cache']['api_cache_entries']}")
print(f"Total places: {stats['data']['total_places']}")
print(f"Total size: {stats['total_size_mb']} MB")
```

---

## 📝 LICENSE

MIT License - Free to use for educational and commercial purposes

---

## 🤝 ĐÓNG GÓP

Mọi đóng góp đều được hoan nghênh! 

1. Fork project
2. Tạo branch (`git checkout -b feature/AmazingFeature`)
3. Commit (`git commit -m 'Add AmazingFeature'`)
4. Push (`git push origin feature/AmazingFeature`)
5. Tạo Pull Request

---

## 🙏 CREDITS

**Công Nghệ:**
- OpenAI GPT-4
- LangGraph, LangChain, AutoGen
- Gradio
- LocationIQ, Geoapify, OpenWeather, Tavily
- Scikit-learn, Pandas, NumPy

**Dữ Liệu:**
- 50,000+ địa điểm Việt Nam
- OpenStreetMap contributors

---

## 🎉 BẮT ĐẦU NGAY!

```bash
cd TRAVEL_PLANNER
python run_ui.py
```

**Mở browser:** http://localhost:7861

**CHÚC BẠN CÓ CHUYẾN ĐI VUI VẺ!** 🌍✨

---

**Built with ❤️ by Travel Planner MAS Team**  
**Version 2.0 | October 2025**
