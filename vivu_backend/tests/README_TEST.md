# Test Suite Documentation

## Test Case TC_ITIN_001_romantic_dalat

### Mô tả
Test case kiểm tra luồng đầy đủ của hệ thống Vi Vu cho chuyến đi 4 ngày từ Quận 1, TP.HCM → Đà Lạt, phong cách `romantic + wellness`.

### Cách chạy test

1. **Cài đặt dependencies:**
```bash
pip install pytest pytest-django pytest-asyncio
```

2. **Chạy test:**
```bash
cd TRAVEL_PLANNER
pytest vivu_backend/tests/test_travel_plan_preview.py -v
```

3. **Chạy với output chi tiết:**
```bash
pytest vivu_backend/tests/test_travel_plan_preview.py -v -s --tb=short
```

### Expected Output

Test sẽ kiểm tra:
- ✅ HTTP 200 OK
- ✅ Complete itinerary_preview với 4 daily_schedules
- ✅ Cost breakdown trong expected ranges
- ✅ Geocoding resolved
- ✅ At least one wellness/spa activity
- ✅ Total cost consistency

### Edge Cases

Test suite cũng bao gồm:
- Missing parameters
- Invalid days (>14)
- Geocoding resolution
- Cost range validation

