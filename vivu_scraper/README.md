# Vi Vu Scraper

Subproject thu thập du lieu cong khai cho `Vi Vu`, duoc thiet ke de chay tren ha tang Docker hien tai cua repo.

## Muc tieu

- Scaffold mot workspace rieng cho pipeline crawl/normalize/import.
- Tai su dung cac script public-source da co trong `vivu_backend/scripts`.
- Xuat schema thuc te cua bang `DIADIEM` tu Django model de mapper du lieu chuan xac.
- Ho tro muc tieu `20k+` dia diem ma khong phu thuoc vao API tra phi.

## Nguon du lieu an toan / public

- `csdl.vietnamtourism.gov.vn`: nguon public du lich Viet Nam, da co script import/upsert.
- OpenStreetMap / Overpass / Nominatim / Wikipedia: nguon public cho harvest POI quy mo lon.

## Khong nam trong pham vi

- Bypass anti-bot.
- Quet nguon tra phi hoac nguon yeu cau truy cap khong duoc phep.
- Reverse private API / co che tranh chi phi cua ben thu ba.

## Cau truc

```text
vivu_scraper/
├── README.md
├── outputs/
│   └── .gitkeep
└── scripts/
    ├── export_diadiem_schema.py
    └── run_public_pipeline.py
```

## Lenh nhanh

### 1. Xuat schema DIADIEM

```powershell
docker compose run --rm scraper python vivu_scraper/scripts/run_public_pipeline.py schema
```

### 2. Dry-run crawler du lich cong khai

```powershell
docker compose run --rm scraper python vivu_scraper/scripts/run_public_pipeline.py tourism-db --dry-run --categories cslt,dest --max-pages-per-category 1 --max-items-per-category 10
```

### 3. Harvest OSM quy mo lon vao SQLite rieng

```powershell
docker compose run --rm scraper python vivu_scraper/scripts/run_public_pipeline.py osm --limit 20000
```

## Ghi chu ve muc tieu 20k

- Chi rieng script `scrape_vietnam_tourism_db.py` da ghi nhan `14k+` co so luu tru tu mot danh muc public.
- Script `poi_harvest.py` da huong den `50k+` POI tu OSM.
- Vi vay, muc tieu `20k` la kha thi, nhung nen chia batch, luu output trung gian va kiem soat chat luong mapping tinh/thanh.
