import pandas as pd

df = pd.read_csv('data/vietnam_all_places.csv')

print("\n" + "="*80)
print("📍 PHÂN BỐ ĐỊA ĐIỂM THEO TỈNH THÀNH")
print("="*80)

total_places = len(df)
total_cities = df['city'].nunique()

print(f"\n✅ Tổng số địa điểm: {total_places:,}")
print(f"📊 Thuộc: {total_cities} tỉnh thành\n")

print("="*80)
print("DANH SÁCH TỈNH THÀNH VÀ SỐ LƯỢNG ĐỊA ĐIỂM:")
print("="*80)

city_counts = df['city'].value_counts().sort_values(ascending=False)

for i, (city, count) in enumerate(city_counts.items(), 1):
    percentage = (count / total_places) * 100
    print(f"{i:2}. {city:25s} - {count:5,} địa điểm ({percentage:5.2f}%)")

print("\n" + "="*80)
print(f"📊 Trung bình: {total_places / total_cities:.0f} địa điểm/tỉnh")
print("="*80)

