"""Run the whole pipeline:  raw data -> cleaning -> database.

    python run_pipeline.py --sample     # build + load fake sample data (for development)
    python run_pipeline.py --scrape     # run the real scrapers listed in SCRAPERS below
"""
import argparse
from pathlib import Path

import pandas as pd

from analysis.clean import clean_dataframe
from database.db import insert_vehicles

RAW_DIR = Path("data/raw")

# Add each finished scraper class here, e.g.:
#   from scraper.site_olx import OlxScraper
#   SCRAPERS = [OlxScraper(), ...]
SCRAPERS = []


def run_scrapers():
    rows = []
    for scraper in SCRAPERS:
        print(f"Scraping {scraper.source} ...")
        rows.extend(scraper.run())
    if not rows:
        raise SystemExit("No rows scraped. Add your scrapers to SCRAPERS in run_pipeline.py.")
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    path = RAW_DIR / "scraped_listings.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def main():
    ap = argparse.ArgumentParser()
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--sample", action="store_true", help="use generated sample data")
    mode.add_argument("--scrape", action="store_true", help="run the real scrapers")
    args = ap.parse_args()

    if args.sample:
        from scraper import make_sample_data  # noqa: F401  (runs on import)
        raw_path = RAW_DIR / "sample_listings.csv"
    else:
        raw_path = run_scrapers()

    raw = pd.read_csv(raw_path)
    clean = clean_dataframe(raw)
    inserted = insert_vehicles(clean)
    print(f"Raw rows: {len(raw)} | after cleaning: {len(clean)} | new rows in DB: {inserted}")


if __name__ == "__main__":
    main()
