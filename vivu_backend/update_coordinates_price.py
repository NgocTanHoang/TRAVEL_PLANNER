"""
Cập nhật vĩ độ, kinh độ và giá vé cho các địa điểm trong bảng DIADIEM
"""
import sqlite3
from pathlib import Path
import re

db_path = Path(__file__).resolve().parent / 'db.sqlite3'

# Dữ liệu cần cập nhật
data = [
    {"ten": "Nhà hát Thành phố Hồ Chí Minh", "tinh": "TP.HCM", "viDo": 10.777085, "kinhDo": 106.703215, "giaVe": 0},
    {"ten": "Phố đi bộ Nguyễn Huệ", "tinh": "TP.HCM", "viDo": 10.775833, "kinhDo": 106.703889, "giaVe": 0},
    {"ten": "Bitexco Financial Tower (Saigon Skydeck)", "tinh": "TP.HCM", "viDo": 10.772590, "kinhDo": 106.704200, "giaVe": 200000},
    {"ten": "Bến Nhà Rồng (Bảo tàng Hồ Chí Minh)", "tinh": "TP.HCM", "viDo": 10.768611, "kinhDo": 106.707778, "giaVe": 0},
    {"ten": "Chùa Bà Thiên Hậu", "tinh": "TP.HCM", "viDo": 10.751690, "kinhDo": 106.666928, "giaVe": 0},
    {"ten": "Phố Tây Bùi Viện", "tinh": "TP.HCM", "viDo": 10.768056, "kinhDo": 106.694806, "giaVe": 0},
    {"ten": "Tòa nhà Landmark 81", "tinh": "TP.HCM", "viDo": 10.795556, "kinhDo": 106.720833, "giaVe": 300000},  # Lấy giá nhỏ nhất
    {"ten": "Thảo Cầm Viên Sài Gòn", "tinh": "TP.HCM", "viDo": 10.787600, "kinhDo": 106.705600, "giaVe": 50000},  # Lấy giá nhỏ nhất
    {"ten": "Bảo tàng Mỹ thuật TP.HCM", "tinh": "TP.HCM", "viDo": 10.771111, "kinhDo": 106.702500, "giaVe": 30000},
    {"ten": "Hồ Con Rùa", "tinh": "TP.HCM", "viDo": 10.782800, "kinhDo": 106.696100, "giaVe": 0},
    {"ten": "Dinh Độc Lập", "tinh": "TP.HCM", "viDo": 10.778735, "kinhDo": 106.695349, "giaVe": 40000},
    {"ten": "Nhà thờ Đức Bà Sài Gòn", "tinh": "TP.HCM", "viDo": 10.779785, "kinhDo": 106.699019, "giaVe": 0},
    {"ten": "Bưu điện Trung tâm Sài Gòn", "tinh": "TP.HCM", "viDo": 10.779956, "kinhDo": 106.700142, "giaVe": 0},
    {"ten": "Bảo tàng Chứng tích Chiến tranh", "tinh": "TP.HCM", "viDo": 10.777085, "kinhDo": 106.692298, "giaVe": 40000},
    {"ten": "Chợ Bến Thành", "tinh": "TP.HCM", "viDo": 10.772590, "kinhDo": 106.698097, "giaVe": 0},
    {"ten": "Hồ Hoàn Kiếm và Đền Ngọc Sơn", "tinh": "Hà Nội", "viDo": 21.028511, "kinhDo": 105.854167, "giaVe": 30000},
    {"ten": "Lăng Chủ tịch Hồ Chí Minh và Quảng trường Ba Đình", "tinh": "Hà Nội", "viDo": 21.036730, "kinhDo": 105.834689, "giaVe": 0},
    {"ten": "Văn Miếu - Quốc Tử Giám", "tinh": "Hà Nội", "viDo": 21.028906, "kinhDo": 105.834017, "giaVe": 30000},
    {"ten": "Phố Cổ Hà Nội", "tinh": "Hà Nội", "viDo": 21.033575, "kinhDo": 105.851944, "giaVe": 0},
    {"ten": "Nhà tù Hỏa Lò", "tinh": "Hà Nội", "viDo": 21.023223, "kinhDo": 105.845459, "giaVe": 30000},
    {"ten": "Bảo tàng Dân tộc học Việt Nam", "tinh": "Hà Nội", "viDo": 21.050470, "kinhDo": 105.798151, "giaVe": 40000},
    {"ten": "Hồ Tây và Phủ Tây Hồ", "tinh": "Hà Nội", "viDo": 21.054359, "kinhDo": 105.823908, "giaVe": 0},
    {"ten": "Nhà thờ Lớn Hà Nội", "tinh": "Hà Nội", "viDo": 21.026362, "kinhDo": 105.851083, "giaVe": 0},
    {"ten": "Hoàng thành Thăng Long", "tinh": "Hà Nội", "viDo": 21.037861, "kinhDo": 105.836066, "giaVe": 30000},
    {"ten": "Làng Gốm Bát Tràng", "tinh": "Hà Nội", "viDo": 20.975416, "kinhDo": 105.901584, "giaVe": 0},
    {"ten": "Vườn Quốc gia Ba Vì", "tinh": "Hà Nội", "viDo": 21.056073, "kinhDo": 105.321798, "giaVe": 60000},
    {"ten": "Chùa Một Cột", "tinh": "Hà Nội", "viDo": 21.036139, "kinhDo": 105.834079, "giaVe": 0},
    {"ten": "Công viên Nước Hồ Tây", "tinh": "Hà Nội", "viDo": 21.066455, "kinhDo": 105.807857, "giaVe": 170000},  # Lấy giá nhỏ nhất
    {"ten": "Grand World Hà Nội", "tinh": "Hà Nội", "viDo": 20.938889, "kinhDo": 105.975000, "giaVe": 0},
    {"ten": "Làng cổ Đường Lâm", "tinh": "Hà Nội", "viDo": 21.146914, "kinhDo": 105.421596, "giaVe": 20000},
    {"ten": "Thủy cung Vinpearl Aquarium", "tinh": "Hà Nội", "viDo": 21.002811, "kinhDo": 105.862417, "giaVe": 170000},  # Lấy giá nhỏ nhất
    {"ten": "Lotte Observation Deck", "tinh": "Hà Nội", "viDo": 21.037805, "kinhDo": 105.815049, "giaVe": 230000},  # Lấy giá nhỏ nhất
    {"ten": "Cầu Long Biên", "tinh": "Hà Nội", "viDo": 21.050519, "kinhDo": 105.864784, "giaVe": 0},
    {"ten": "Chùa Hương", "tinh": "Hà Nội", "viDo": 20.672937, "kinhDo": 105.748366, "giaVe": 80000},
    {"ten": "Hồ Quan Sơn", "tinh": "Hà Nội", "viDo": 20.730331, "kinhDo": 105.745427, "giaVe": 15000},
    {"ten": "Công viên Thống Nhất", "tinh": "Hà Nội", "viDo": 21.006935, "kinhDo": 105.845941, "giaVe": 0},
    {"ten": "Bảo tàng Phụ nữ Việt Nam", "tinh": "Hà Nội", "viDo": 21.018861, "kinhDo": 105.854298, "giaVe": 40000},
    {"ten": "Nhà Hát Lớn Hà Nội", "tinh": "Hà Nội", "viDo": 21.021021, "kinhDo": 105.856012, "giaVe": 0},
    {"ten": "Bảo tàng Mỹ thuật Việt Nam", "tinh": "Hà Nội", "viDo": 21.031572, "kinhDo": 105.839818, "giaVe": 40000},
    {"ten": "Đền Quán Thánh", "tinh": "Hà Nội", "viDo": 21.045431, "kinhDo": 105.836366, "giaVe": 10000},
    {"ten": "Công viên Thủ Lệ", "tinh": "Hà Nội", "viDo": 21.030588, "kinhDo": 105.801646, "giaVe": 30000},
    {"ten": "Thiên Đường Bảo Sơn", "tinh": "Hà Nội", "viDo": 21.000787, "kinhDo": 105.733526, "giaVe": 150000},  # Lấy giá nhỏ nhất
    {"ten": "Đồi Bù", "tinh": "Hà Nội", "viDo": 20.900450, "kinhDo": 105.513520, "giaVe": 0},
    {"ten": "Làng Văn hóa - Du lịch các dân tộc Việt Nam", "tinh": "Hà Nội", "viDo": 21.077618, "kinhDo": 105.353396, "giaVe": 30000},
    {"ten": "Phố Sách Đinh Lễ", "tinh": "Hà Nội", "viDo": 21.026402, "kinhDo": 105.855322, "giaVe": 0},
    {"ten": "Khu Bảo tồn Thiên nhiên Sóc Sơn", "tinh": "Hà Nội", "viDo": 21.282914, "kinhDo": 105.855216, "giaVe": 0},
    {"ten": "Cột cờ Hà Nội", "tinh": "Hà Nội", "viDo": 21.033611, "kinhDo": 105.842778, "giaVe": 30000},
    {"ten": "Khu di tích Thành Cổ Loa", "tinh": "Hà Nội", "viDo": 21.139000, "kinhDo": 105.879000, "giaVe": 10000},
    {"ten": "Cầu Vàng (Golden Bridge) - Sun World Bà Nà Hills", "tinh": "Đà Nẵng", "viDo": 15.996111, "kinhDo": 108.033611, "giaVe": 900000},
    {"ten": "Ngũ Hành Sơn (Non Nước)", "tinh": "Đà Nẵng", "viDo": 16.002800, "kinhDo": 108.270800, "giaVe": 40000},
    {"ten": "Bán đảo Sơn Trà (Chùa Linh Ứng Bãi Bụt)", "tinh": "Đà Nẵng", "viDo": 16.108300, "kinhDo": 108.281800, "giaVe": 0},
    {"ten": "Bãi biển Mỹ Khê", "tinh": "Đà Nẵng", "viDo": 16.059400, "kinhDo": 108.243500, "giaVe": 0},
    {"ten": "Cầu Rồng", "tinh": "Đà Nẵng", "viDo": 16.061000, "kinhDo": 108.225500, "giaVe": 0},
]

def parse_gia_ve(gia_ve_str):
    """Parse giá vé từ string sang số"""
    if not gia_ve_str or "Miễn phí" in gia_ve_str or "Miễn" in gia_ve_str:
        return 0
    
    # Tìm số trong string (loại bỏ dấu chấm phân cách hàng nghìn)
    numbers = re.findall(r'\d+(?:\.\d+)?', gia_ve_str.replace('.', ''))
    if numbers:
        # Lấy số đầu tiên và chuyển thành int
        return int(float(numbers[0]))
    return 0

print("=" * 100)
print("CẬP NHẬT VĨ ĐỘ, KINH ĐỘ VÀ GIÁ VÉ CHO CÁC ĐỊA ĐIỂM")
print("=" * 100)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

updated_count = 0
not_found = []

for item in data:
    ten = item["ten"]
    vi_do = item["viDo"]
    kinh_do = item["kinhDo"]
    gia_ve = item["giaVe"]
    
    # Tìm địa điểm trong database (tìm theo tên gần đúng)
    cursor.execute("""
        SELECT maDiaDiem, tenDiaDiem FROM DIADIEM 
        WHERE tenDiaDiem LIKE ? OR tenDiaDiem LIKE ?
        LIMIT 1
    """, (f"%{ten[:20]}%", f"%{ten[-20:]}%"))
    
    result = cursor.fetchone()
    
    if result:
        ma_dd, ten_db = result
        # Cập nhật
        cursor.execute("""
            UPDATE DIADIEM 
            SET viDo = ?, kinhDo = ?, giaVe = ?
            WHERE maDiaDiem = ?
        """, (vi_do, kinh_do, gia_ve, ma_dd))
        
        updated_count += 1
        print(f"✓ [{updated_count}] {ten_db[:50]}... -> viDo={vi_do}, kinhDo={kinh_do}, giaVe={gia_ve:,}")
    else:
        not_found.append(ten)
        print(f"✗ Không tìm thấy: {ten}")

conn.commit()

print("\n" + "=" * 100)
print("KẾT QUẢ:")
print("=" * 100)
print(f"✓ Đã cập nhật: {updated_count}/{len(data)} địa điểm")

if not_found:
    print(f"\n✗ Không tìm thấy {len(not_found)} địa điểm:")
    for ten in not_found:
        print(f"  - {ten}")

# Kiểm tra lại một vài bản ghi
print("\n" + "=" * 100)
print("KIỂM TRA LẠI:")
print("=" * 100)

cursor.execute("""
    SELECT maDiaDiem, tenDiaDiem, viDo, kinhDo, giaVe 
    FROM DIADIEM 
    WHERE viDo != 0 OR kinhDo != 0 OR giaVe != 0
    ORDER BY maDiaDiem 
    LIMIT 10
""")

samples = cursor.fetchall()
print("Một vài bản ghi sau khi cập nhật:")
for ma, ten, vi, kinh, gia in samples:
    print(f"  maDiaDiem={ma}: {ten[:40]}...")
    print(f"    viDo={vi}, kinhDo={kinh}, giaVe={gia:,}")

conn.close()

print("\n✅ Hoàn tất!")

