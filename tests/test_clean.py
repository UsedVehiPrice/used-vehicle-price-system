import pandas as pd
import pytest

from analysis.clean import clean_dataframe, normalize_fuel, parse_km, parse_price


@pytest.mark.parametrize("text,expected", [
    ("₹ 3.50 Lakh", 350000),
    ("Rs. 4,25,000", 425000),
    ("1.2 Cr", 12000000),
    ("450000", 450000),
    ("Call for price", None),
    (None, None),
])
def test_parse_price(text, expected):
    assert parse_price(text) == expected


@pytest.mark.parametrize("text,expected", [
    ("45,000 km", 45000),
    ("45000 KMs", 45000),
    ("45k km", 45000),
    ("n/a", None),
    (None, None),
])
def test_parse_km(text, expected):
    assert parse_km(text) == expected


def test_normalize_fuel():
    assert normalize_fuel("DIESEL") == "Diesel"
    assert normalize_fuel("petrol") == "Petrol"
    assert normalize_fuel(None) is None


def test_clean_dataframe_drops_bad_rows_and_duplicates():
    raw = pd.DataFrame([
        {"source": "a", "brand": " honda ", "model": "city", "year": 2018,
         "fuel_type": "petrol", "km_driven": "40,000 km", "price": "₹ 7 Lakh",
         "location": "kochi", "seller_type": "dealer", "url": "u1", "scraped_on": "x"},
        {"source": "a", "brand": "honda", "model": "city", "year": 2018,
         "fuel_type": "petrol", "km_driven": "40,000 km", "price": "₹ 7 Lakh",
         "location": "kochi", "seller_type": "dealer", "url": "u1", "scraped_on": "x"},  # duplicate
        {"source": "a", "brand": "honda", "model": "city", "year": 2018,
         "fuel_type": "petrol", "km_driven": "40,000 km", "price": "Call for price",
         "location": "kochi", "seller_type": "dealer", "url": "u2", "scraped_on": "x"},  # no price
    ])
    out = clean_dataframe(raw)
    assert len(out) == 1
    assert out.loc[0, "brand"] == "Honda"
    assert out.loc[0, "price"] == 700000
    assert out.loc[0, "km_driven"] == 40000
