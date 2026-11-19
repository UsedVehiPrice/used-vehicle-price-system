# Used Vehicle Price Comparison and Analysis System Using Python Web Scraping

Collects used-vehicle listings from several websites with Python web scraping,
cleans and stores them in a database, and lets users compare prices by model,
year, fuel type and kilometres driven.

## Pipeline

```
scraper/  ->  data/raw/*.csv  ->  analysis/clean.py  ->  database (SQLite)  ->  backend (FastAPI)  ->  frontend (Streamlit)
```

| Folder | Purpose |
|---|---|
| `scraper/` | One scraper per website (`base.py` has shared, polite scraping code; `site_template.py` is the template to copy) |
| `analysis/` | `clean.py` (cleaning), `analyze.py` (averages, good-deal detection) |
| `database/` | `schema.sql`, `db.py` (SQLite) |
| `backend/` | `main.py` REST API |
| `frontend/` | `app.py` Streamlit dashboard |
| `tests/` | Automated tests (`pytest`) |
| `data/raw/` | Raw scraped CSVs (not committed to Git) |

## Setup (every team member)

```bash
git clone <repo-url>
cd used-vehicle-price-system
python -m venv venv
# Windows:  venv\Scripts\activate        Mac/Linux:  source venv/bin/activate
pip install -r requirements.txt
```

## Run with sample data (works immediately)

```bash
python run_pipeline.py --sample        # makes fake data, cleans it, loads the DB
streamlit run frontend/app.py          # dashboard
uvicorn backend.main:app --reload      # API, docs at http://127.0.0.1:8000/docs
python -m pytest                       # tests
```

The sample data is **fake and for development only**. Never present it as real results.

## Run with real data

1. Copy `scraper/site_template.py` to `scraper/site_<name>.py` and fill in the real URL and CSS selectors.
2. Add your scraper to the `SCRAPERS` list in `run_pipeline.py`.
3. `python run_pipeline.py --scrape`

### Scraping rules
- Read each site's `robots.txt` and terms of service first. Only scrape what is allowed.
- Keep a delay between requests (`delay_seconds >= 2`) and a small `max_pages` while testing.
- Do not collect personal data such as phone numbers.
- Set a real contact e-mail in `USER_AGENT` in `scraper/base.py`.

## Backend API (FastAPI)

```bash
uvicorn backend.main:app --reload                      # http://127.0.0.1:8000/docs
uvicorn backend.main:app --host 0.0.0.0 --port 8000    # reachable from other laptops
python -m uvicorn backend.main:app --reload            # if uvicorn.exe is blocked by Windows
```

| Endpoint | Purpose |
|---|---|
| `GET /vehicles?brand=&model=&fuel=&min_year=&max_year=&max_km=&max_price=&sort=price&limit=50` | Listings, cheapest first. `sort` is `price`, `year` or `km_driven`; `limit` is 1 to 2000. |
| `GET /compare?model=City&year=2018` | Listings / average / min / max price per source website (`year` optional). |
| `GET /stats` | Average price and listing count by brand, model and year. |
| `GET /health` | `{"status": "ok", "vehicles": <count>}` |

Each vehicle returned by `/vehicles` has: `id, source, brand, model, year, fuel_type, km_driven, price,
location, seller_type, url, scraped_on, image_url, image_alt`. Invalid input (for example `sort=brand` or
`limit=5000`) returns HTTP 422. If the database cannot be opened the API returns 503 with a short message.

**Listing images.** `image_url` is the photo of that exact listing as an absolute `http(s)` URL, or `null`.
`image_alt` is optional text. The API never returns relative paths or base64 data, and never a stock photo.
Scrapers fill them with `scraper/images.py` (`extract_primary_image` reads `og:image` / JSON-LD from a listing
page, `normalize_image_url` cleans a URL taken from a card). Caching copies of images on our own server is
not implemented; if a source blocks hotlinking the frontend shows its own labelled placeholder.

**Settings (optional environment variables):** `VEHICLE_DB` (path to the SQLite file) and `CORS_ORIGINS`
(comma-separated browser origins allowed to call the API; default is the Vite dev server,
`http://localhost:5173,http://127.0.0.1:5173`). The React frontend normally calls the API through its
own `/api` proxy, so CORS only matters for a deployed frontend.

**Existing databases** are upgraded automatically (`init_db()` adds the `image_url` / `image_alt` columns).
To start completely fresh, delete `database/vehicles.db` and run `python run_pipeline.py --sample`.

## Team workflow

See [TEAM_GUIDE.md](TEAM_GUIDE.md).
