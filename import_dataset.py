"""Load CSV files into the database: a DOWNLOADED dataset or the output of one of our scrapers.

    python import_dataset.py data/raw/carwale.csv                      # scraper output (keeps listing URL + photo)
    python import_dataset.py data/raw/carwale.csv data/raw/carwale_creta.csv   # several files at once
    python import_dataset.py data/raw/Data_Train.csv --cities Chennai,Coimbatore,Kochi   # Kaggle dataset
    python import_dataset.py <file> --dry-run                          # check only, no database changes

The file type is detected from its header. Keep CSVs in data/raw/ (not committed to Git).
For a downloaded dataset, check its licence first and say in the report that it was downloaded, not scraped.
Safe to run twice: rows already in the database are skipped.
"""
import argparse
import sys

from analysis.clean import clean_dataframe
from database.db import insert_vehicles
from scraper.datasets import (DEFAULT_SOURCE, detect_format, load_scraped_csv,
                              load_used_cars_price_csv, restore_case, validate_source_name)


def import_one(path, args):
    """Load, clean and (unless --dry-run) store one file. Returns the number of new rows."""
    kind = detect_format(path)
    if kind == "scraped":
        raw = load_scraped_csv(path, source=args.source)
    else:
        raw = load_used_cars_price_csv(path, source=args.source or DEFAULT_SOURCE)
    for src in raw["source"].dropna().unique():
        validate_source_name(str(src))
    if args.cities:
        wanted = {c.strip().lower() for c in args.cities.split(",") if c.strip()}
        available = sorted(raw["location"].dropna().unique())
        raw = raw[raw["location"].fillna("").str.lower().isin(wanted)]
        if raw.empty:
            raise ValueError(f"No rows for cities {sorted(wanted)}. Cities in the file: {', '.join(available)}")
    clean = restore_case(clean_dataframe(raw), raw)
    if clean.empty:
        raise ValueError("No usable rows left after cleaning.")
    kind_label = "scraped listings" if kind == "scraped" else "downloaded dataset"
    print(f"{path} ({kind_label}): rows read {len(raw)} | kept after cleaning {len(clean)} | dropped {len(raw) - len(clean)}")
    print(f"  years {clean['year'].min()}-{clean['year'].max()} | "
          f"price Rs {int(clean['price'].min()):,} to Rs {int(clean['price'].max()):,} | "
          f"{clean['brand'].nunique()} brands, {clean['model'].nunique()} models | "
          f"with listing photo: {int(clean['image_url'].notna().sum())}")
    if args.dry_run:
        return 0
    inserted = insert_vehicles(clean)
    print(f"  New rows added to the database: {inserted}" + ("  (already imported earlier)" if inserted == 0 else ""))
    return inserted


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv_paths", nargs="+", help="one or more CSV files (Kaggle Data_Train.csv or a scraper CSV)")
    ap.add_argument("--source", help="name shown as the data source (default: the file's own 'source' column, "
                                     f"or {DEFAULT_SOURCE} for Data_Train.csv)")
    ap.add_argument("--cities", help="only import these cities, comma separated, e.g. Chennai,Coimbatore,Kochi")
    ap.add_argument("--dry-run", action="store_true", help="clean and report, but do not write to the database")
    args = ap.parse_args(argv)

    if args.source:
        try:
            validate_source_name(args.source)
        except ValueError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
    total, failed = 0, False
    for path in args.csv_paths:
        try:
            total += import_one(path, args)
        except (ValueError, OSError) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            failed = True
    if args.dry_run:
        print("Dry run: database not changed.")
    elif len(args.csv_paths) > 1:
        print(f"Total new rows added: {total}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
