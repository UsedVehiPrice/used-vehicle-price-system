"""Load a DOWNLOADED dataset file into the database (no web scraping involved).

    python import_dataset.py data/raw/Data_Train.csv
    python import_dataset.py data/raw/Data_Train.csv --dry-run          # check only, no database changes
    python import_dataset.py data/raw/Data_Train.csv --source dataset-kaggle-used-cars
    python import_dataset.py data/raw/Data_Train.csv --cities Chennai,Coimbatore,Kochi   # only these cities

Keep the CSV in data/raw/ (it is not committed to Git). Check the dataset's licence
on its Kaggle page first, and say in the report that this data was downloaded, not scraped.
Safe to run twice: rows already in the database are skipped.
"""
import argparse
import sys

from analysis.clean import clean_dataframe
from database.db import insert_vehicles
from scraper.datasets import DEFAULT_SOURCE, load_used_cars_price_csv, restore_case, validate_source_name


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv_path", help="path to Data_Train.csv (the Kaggle 'Used Cars Price Prediction' file)")
    ap.add_argument("--source", default=DEFAULT_SOURCE, help=f"name shown as the data source (default {DEFAULT_SOURCE})")
    ap.add_argument("--cities", help="only import these cities, comma separated, e.g. Chennai,Coimbatore,Kochi")
    ap.add_argument("--dry-run", action="store_true", help="clean and report, but do not write to the database")
    args = ap.parse_args(argv)

    try:
        validate_source_name(args.source)
        raw = load_used_cars_price_csv(args.csv_path, source=args.source)
        if args.cities:
            wanted = {c.strip().lower() for c in args.cities.split(",") if c.strip()}
            available = sorted(raw["location"].dropna().unique())
            raw = raw[raw["location"].str.lower().isin(wanted)]
            if raw.empty:
                raise ValueError(f"No rows for cities {sorted(wanted)}. Cities in the file: {', '.join(available)}")
    except (ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    clean = restore_case(clean_dataframe(raw), raw)
    print(f"Rows read: {len(raw)} | kept after cleaning: {len(clean)} | dropped: {len(raw) - len(clean)}")
    print(f"Years {clean['year'].min()}-{clean['year'].max()} | "
          f"price Rs {int(clean['price'].min()):,} to Rs {int(clean['price'].max()):,} | "
          f"{clean['brand'].nunique()} brands, {clean['model'].nunique()} models")
    if args.dry_run:
        print("Dry run: database not changed.")
        return 0
    inserted = insert_vehicles(clean)
    print(f"New rows added to the database: {inserted}" + ("  (already imported earlier)" if inserted == 0 else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
