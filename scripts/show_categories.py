import pandas as pd

df = pd.read_csv('data/vietnam_all_places.csv')

print("\n" + "="*80)
print("📊 DANH SÁCH CÁC LOẠI ĐỊA ĐIỂM TRONG DATABASE")
print("="*80)
print(f"\nTổng số categories: {df['category'].nunique()}")
print(f"Tổng số địa điểm: {len(df)}\n")

print("TOP 50 LOẠI ĐỊA ĐIỂM PHỔ BIẾN NHẤT:\n")

cats = df['category'].value_counts().head(50)
for i, (cat, count) in enumerate(cats.items(), 1):
    print(f"{i:2}. {cat:30s} - {count:5,} địa điểm")

print("\n" + "="*80)

