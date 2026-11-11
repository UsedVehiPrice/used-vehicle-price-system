"""Cleaning functions: turn messy scraped text into consistent values."""
import re

import pandas as pd

FUEL_MAP = {
    "petrol": "Petrol", "gasoline": "Petrol",
    "diesel": "Diesel",
    "cng": "CNG",
    "electric": "Electric", "ev": "Electric",
    "lpg": "LPG",
    "hybrid": "Hybrid",
}


def parse_price(text):
    """'₹ 3.50 Lakh' -> 350000, 'Rs. 4,25,000' -> 425000, '1.2 Cr' -> 12000000.
    Returns None when no price can be read (e.g. 'Call for price')."""
    if text is None or (isinstance(text, float) and pd.isna(text)):
        return None
    s = str(text).lower().replace(",", "").strip()
    match = re.search(r"(\d+(?:\.\d+)?)\s*(lakh|lac|l\b|crore|cr\b|k\b)?", s)
    if not match:
        return None
    value = float(match.group(1))
    unit = match.group(2)
    if unit in ("lakh", "lac", "l"):
        value *= 100_000
    elif unit in ("crore", "cr"):
        value *= 10_000_000
    elif unit == "k":
        value *= 1_000
    return int(round(value))


def parse_km(text):
    """'45,000 km' -> 45000, '45k km' -> 45000. None if unreadable."""
    if text is None or (isinstance(text, float) and pd.isna(text)):
        return None
    s = str(text).lower().replace(",", "").strip()
    match = re.search(r"(\d+(?:\.\d+)?)\s*(k\b)?", s)
    if not match:
        return None
    value = float(match.group(1))
    if match.group(2):
        value *= 1000
    return int(round(value))


def normalize_fuel(text):
    if text is None or (isinstance(text, float) and pd.isna(text)):
        return None
    return FUEL_MAP.get(str(text).strip().lower(), str(text).strip().title())


def clean_dataframe(df):
    """Return a cleaned copy of the raw listings DataFrame."""
    df = df.copy()
    df["price"] = df["price"].map(parse_price)
    df["km_driven"] = df["km_driven"].map(parse_km)
    df["fuel_type"] = df["fuel_type"].map(normalize_fuel)
    df["year"] = pd.to_numeric(df["year"], errors="coerce")
    for col in ("brand", "model", "location", "seller_type"):
        df[col] = df[col].astype("string").str.strip().str.title()

    # drop rows we cannot use, then sensible-range filters
    df = df.dropna(subset=["brand", "model", "year", "price"])
    df["year"] = df["year"].astype(int)
    df = df[(df["year"] >= 1995) & (df["year"] <= 2026)]
    df = df[(df["price"] >= 20_000) & (df["price"] <= 50_000_000)]
    df = df[df["km_driven"].isna() | (df["km_driven"] <= 600_000)]

    # remove duplicate listings
    df = df.drop_duplicates(subset=["url"]).reset_index(drop=True)
    return df
