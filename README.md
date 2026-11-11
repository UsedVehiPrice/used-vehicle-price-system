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

## API endpoints

- `GET /vehicles?brand=&model=&fuel=&min_year=&max_year=&max_km=&max_price=&sort=price&limit=50`
- `GET /compare?model=City&year=2018` : price per source website
- `GET /stats` : average price by brand / model / year

## Team workflow

See [TEAM_GUIDE.md](TEAM_GUIDE.md).
