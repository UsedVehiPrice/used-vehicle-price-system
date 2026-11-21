"""Adapters that turn DOWNLOADED public datasets into our shared row format
(`scraper.base.FIELDS`), so they go through the same cleaning step, database
and API as scraped listings.

Currently supported:
    load_scraped_csv()           the CSV written by a scraper in scraper/ (columns = scraper.base.FIELDS,
                                 e.g. data/raw/carwale.csv from scraper/site_carwale.py); keeps the
                                 listing URL and photo URL
    load_used_cars_price_csv()   the Kaggle "Used Cars Price Prediction" Data_Train.csv
                                 (columns Name, Location, Year, Kilometers_Driven,
                                 Fuel_Type, ..., Price in lakhs of rupees)

Honest limits of dataset rows (the frontend / report should say so):
  * they are historical (this file: cars from 1998-2019), not live listings;
  * there is no listing URL, no photo and no seller type;
  * the model is the first word(s) after the brand; variant text is dropped.
"""
import re
from collections import Counter

import pandas as pd

from scraper.base import FIELDS

LAKH = 100_000
DEFAULT_SOURCE = "dataset-kaggle-used-cars"

TWO_WORD_BRANDS = ("Land Rover", "Aston Martin", "Rolls Royce", "Alfa Romeo")
# Models that are written as two words in the data ("Wagon R", "Grand i10", ...)
TWO_WORD_MODELS = {
    "Wagon R", "Grand i10", "Elite i20", "Santa Fe", "Range Rover", "Vitara Brezza",
    "Etios Liva", "Land Cruiser", "Discovery Sport", "Santro Xing", "Corolla Altis",
    "Safari Storme", "Ssangyong Rexton",
}
REQUIRED_COLUMNS = ["Name", "Location", "Year", "Kilometers_Driven", "Fuel_Type", "Price"]


def split_name(name):
    """'Hyundai Creta 1.6 CRDi SX Option' -> ('Hyundai', 'Creta').

    Returns (brand, model); model is '' when the name has only a brand."""
    tokens = str(name).split()
    if not tokens:
        return "", ""
    brand = next((b for b in TWO_WORD_BRANDS if str(name).startswith(b + " ")), tokens[0])
    rest = tokens[len(brand.split()):]
    if brand == "Mercedes-Benz" and rest and rest[0] == "New":
        rest = rest[1:]                      # "New C-Class" -> "C-Class"
    if not rest:
        return brand, ""
    if len(rest) > 1 and rest[1] in ("Series", "Class"):
        return brand, " ".join(rest[:2])     # "3 Series", "GLA Class"
    if len(rest) > 1 and " ".join(rest[:2]) in TWO_WORD_MODELS:
        return brand, " ".join(rest[:2])
    return brand, rest[0]


def _check_is_csv_data(path):
    with open(path, "rb") as f:
        head = f.read(4000).lower()
    if b"<!doctype html" in head or b"<html" in head:
        raise ValueError(
            f"{path} is a saved web page, not a data file. On the dataset page use "
            "Kaggle's Download button (you need to be logged in) and use the file from the zip."
        )


SCRAPED_REQUIRED = ["brand", "model", "year", "price", "url"]


def detect_format(path):
    """Look at the CSV header: 'used-cars-price' (Kaggle Data_Train.csv) or 'scraped' (our scrapers)."""
    _check_is_csv_data(path)
    cols = set(pd.read_csv(path, nrows=0).columns)
    if set(REQUIRED_COLUMNS) <= cols:
        return "used-cars-price"
    if set(SCRAPED_REQUIRED) <= cols:
        return "scraped"
    raise ValueError(
        f"{path}: unknown file layout (columns: {sorted(cols)[:8]}...). Expected the Kaggle Data_Train.csv "
        f"or a scraper CSV with columns {SCRAPED_REQUIRED + ['source', 'fuel_type', 'km_driven', 'location', 'image_url']}."
    )


def load_scraped_csv(path, source=None):
    """Read a scraper's CSV into raw rows (FIELDS columns).

    Keeps `url` (the link to the listing page) and `image_url`. `source` defaults to the
    file's own `source` column (e.g. 'carwale'). A location like 'Makarba, Ahmedabad' is
    shortened to its city ('Ahmedabad') so the city filter stays usable.
    """
    _check_is_csv_data(path)
    df = pd.read_csv(path)
    missing = [c for c in SCRAPED_REQUIRED if c not in df.columns]
    if missing:
        raise ValueError(f"{path} is missing columns {missing}.")
    df = df[df["url"].notna() & (df["url"].astype(str).str.strip() != "")].copy()
    if source:
        df["source"] = source
    elif "source" not in df.columns or df["source"].isna().all():
        raise ValueError(f"{path} has no 'source' column; pass --source NAME.")
    for col in FIELDS:
        if col not in df.columns:
            df[col] = None
    df["location"] = df["location"].map(
        lambda v: str(v).split(",")[-1].strip() if isinstance(v, str) and v.strip() else None)
    for col in ("seller_type", "image_url", "image_alt"):
        df[col] = df[col].map(lambda v: v.strip() if isinstance(v, str) and v.strip() else None).astype(object)
    return df[FIELDS].reset_index(drop=True)


def load_used_cars_price_csv(path, source=DEFAULT_SOURCE):
    """Read the 'Used Cars Price Prediction' Data_Train.csv into raw rows (FIELDS columns).

    Price is converted from lakhs to rupees. Each row gets the unique key
    '<source>:row-<n>' in `url`, so importing the same file twice adds nothing new.
    """
    _check_is_csv_data(path)
    df = pd.read_csv(path)
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(
            f"{path} is missing columns {missing}. Expected Data_Train.csv with columns "
            f"{REQUIRED_COLUMNS}. (Data_Test.csv has no Price column and cannot be used.)"
        )
    names = df["Name"].map(split_name)
    out = pd.DataFrame({
        "source": source,
        "brand": [n[0] for n in names],
        "model": [n[1] for n in names],
        "year": df["Year"],
        "fuel_type": df["Fuel_Type"],
        "km_driven": df["Kilometers_Driven"],
        "price": (pd.to_numeric(df["Price"], errors="coerce") * LAKH).round(),
        "location": df["Location"],
        "seller_type": None,
        "url": [f"{source}:row-{i}" for i in range(len(df))],
        "scraped_on": None,
        "image_url": None,
        "image_alt": None,
    })
    out["model"] = out["model"].replace("", None)
    return out[FIELDS]


def restore_case(cleaned, raw):
    """The cleaning step Title-Cases text, which turns 'BMW' into 'Bmw' and 'XUV500' into 'Xuv500'.
    Put back the most common original spelling for each brand / model."""
    cleaned = cleaned.copy()
    for col in ("brand", "model"):
        spellings = {}
        for key, group in raw[col].dropna().astype(str).groupby(raw[col].dropna().astype(str).str.lower()):
            spellings[key] = Counter(group).most_common(1)[0][0]
        cleaned[col] = cleaned[col].astype(str).str.lower().map(spellings).fillna(cleaned[col])
    return cleaned


def validate_source_name(source):
    if re.match(r"^site-[a-z0-9]+$", source, re.I):
        raise ValueError("Source names like 'site-a' are reserved for the fake sample data; pick another.")
    return source
