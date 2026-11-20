# Used Vehicle Price Comparison and Analysis System Using Python Web Scraping

Collects used-vehicle listings from several websites with Python web scraping,
cleans and stores them in a database, and lets users compare prices by model,
year, fuel type and kilometres driven.

## Pipeline

```
scraper/  ->  data/raw/*.csv  ->  analysis/clean.py  ->  database (SQLite)  ->  backend (FastAPI)  ->  frontend (React + Vite)
```

| Folder | Purpose |
|---|---|
| `scraper/` | One scraper per website (`base.py` has shared, polite scraping code; `site_template.py` is the template to copy) |
| `analysis/` | `clean.py` (cleaning), `analyze.py` (averages, good-deal detection) |
| `database/` | `schema.sql`, `db.py` (SQLite) |
| `backend/` | `main.py` REST API |
| `frontend/` | React + Vite web app (`src/`, `package.json`) |
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

## Run with real data

The project database currently holds **1,778 real used-car listings** from the Kaggle dataset
"Used Cars Price Prediction" (`Data_Train.csv`), restricted to **Chennai, Coimbatore and Kochi**:
27 brands, 175 models, manufacturing years 2001-2019, prices Rs 65,000 to Rs 97 lakh.
Kaggle page: <ADD THE DATASET URL AND LICENCE HERE>.

**This data was downloaded, not scraped.** It is historical (not live listings) and has no listing URL,
photo or seller type. Say so in the report and the demo. Load it with:

```bash
# put Data_Train.csv in data/raw/ (not committed to Git), then:
python import_dataset.py data/raw/Data_Train.csv --dry-run                         # check only
python import_dataset.py data/raw/Data_Train.csv --cities Chennai,Coimbatore,Kochi # import
```
It goes through the same cleaning and database as scraped data, and is safe to run twice.

- **Only `Data_Train.csv` works.** `Data_Test.csv` has no price column. A file saved from a Kaggle web page
  (instead of the Download button) is rejected with a message.
- **Model names are approximate:** the model is the first word(s) after the brand ("Creta", "Wagon R");
  variant text is dropped. A few prices in the source file are wrong (for example one 2019 Porsche Cayenne at
  2.02 lakh); spot-check before quoting numbers.
- **Row limit:** the API returns at most 2000 listings per request and the frontend asks for 500, so importing
  all 6015 rows would hide the expensive cars. Use `--cities`, or ask the frontend team to request
  `limit=2000` / filter on the server.
- Check the dataset's licence on its Kaggle page before using it.

### Live scraping (not done yet)
No website scraper is finished yet. To add one: copy `scraper/site_template.py` to `scraper/site_<name>.py`,
fill in the real URL and CSS selectors, add it to the `SCRAPERS` list in `run_pipeline.py`, then run
`python run_pipeline.py --scrape`. Scraped rows will be stored under their own source name, next to the dataset.

## Quick demo mode (sample data, for testing only)

```bash
python run_pipeline.py --sample        # generates FAKE placeholder rows (sources site-a, site-b ...)
python -m pytest                       # tests
```
Use this only to test the code without real data. Never present it as results. It writes into the same
database, so for the real data delete `database/vehicles.db` and import the dataset again.

## Run the whole app

Backend (API) and frontend (React + Vite) run in two terminals:

```bash
python -m uvicorn backend.main:app --reload --host 127.0.0.1 --port 9000   # API, docs at http://127.0.0.1:9000/docs
cd frontend
npm install
npm run dev                                                                 # http://localhost:5173
```
`frontend/.env.local` must contain `VITE_API_PROXY_TARGET=http://127.0.0.1:9000` if the API is not on port 8000.
Needs Node 20.19+ or 22.12+.

### Scraping rules
- Read each site's `robots.txt` and terms of service first. Only scrape what is allowed.
- Keep a delay between requests (`delay_seconds >= 2`) and a small `max_pages` while testing.
- Do not collect personal data such as phone numbers.
- Set a real contact e-mail in `USER_AGENT` in `scraper/base.py`.

## Backend API (FastAPI)

```bash
uvicorn backend.main:app --reload                      # http://127.0.0.1:8000/docs (use --port 9000 if 8000 is blocked)
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
To start completely fresh, delete `database/vehicles.db` and import the dataset again (see "Run with real data").

## Team workflow

See [TEAM_GUIDE.md](TEAM_GUIDE.md).
