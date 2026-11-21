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

**The Kaggle data was downloaded, not scraped** (the CarWale rows below are scraped). It is historical (not live listings) and has no listing URL,
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
- **Row limit:** the API returns at most 10000 listings per request and the frontend asks for 5000, sorted cheapest first.
  If you import more rows than that, the most expensive cars are not shown.
- Check the dataset's licence on its Kaggle page before using it.

### Scraped listings (CarWale)
`scraper/site_carwale.py` scrapes used-car listings from carwale.com into `data/raw/carwale.csv`: brand, model,
year, fuel type, kilometres, price, city, **a link to the listing page on carwale.com** and the listing photo URL.
It checks `robots.txt`, waits between pages and collects no personal data. Setup and run:

```bash
pip install playwright pandas
playwright install chromium
python scraper/site_carwale.py --probe        # page 1 only, prints what it found
python scraper/site_carwale.py                # default: used Toyota Urban Cruiser Hyryder listings
python scraper/site_carwale.py --url https://www.carwale.com/used/hyundai-creta/ --out data/raw/carwale_creta.csv
```
To scrape many models at once, use the batch runner. It reads `scraper/carwale_models.txt` (one model page per
line; edit the list freely), scrapes each page politely, and merges everything into `data/raw/carwale_all.csv`:

```bash
python -m scraper.run_carwale_all --probe                                   # test: first model, page 1 only
python -m scraper.run_carwale_all --only hyundai-creta --cities chennai     # one model, Chennai page
python -m scraper.run_carwale_all --cities chennai,coimbatore --max-pages 5 # all models, city pages (takes 1-3 hours)
python -m scraper.run_carwale_all --cities chennai,coimbatore --max-pages 5 --resume   # continue after Ctrl+C / a crash
python import_dataset.py data/raw/carwale_all.csv                           # load into the database
```
Without `--cities` it scrapes the all-India page of each model, which has hundreds to thousands of listings per
model. Pages that do not exist are skipped and listed at the end. Ctrl+C stops early and keeps what was collected.
To show **only** the scraped data in the app, delete `database/vehicles.db` first (this removes the downloaded
dataset rows too), import the scraped CSVs, and restart the backend.
Check CarWale's terms of service before collecting more than a small sample, keep `max_pages` low, and say in the
report that the listings and prices belong to CarWale. Photos are loaded from CarWale's servers, not stored by us.

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
| `GET /vehicles?brand=&model=&fuel=&min_year=&max_year=&max_km=&max_price=&sort=price&limit=50` | Listings, cheapest first. `sort` is `price`, `year` or `km_driven`; `limit` is 1 to 10000. |
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
