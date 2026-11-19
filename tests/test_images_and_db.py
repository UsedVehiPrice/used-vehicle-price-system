import sqlite3

import pandas as pd
import pytest
from bs4 import BeautifulSoup

from analysis.clean import clean_dataframe
from database import db
from scraper.images import extract_primary_image, normalize_image_url


# ---- normalize_image_url --------------------------------------------------

@pytest.mark.parametrize("value,base,expected", [
    ("https://cdn.x.com/a.jpg", None, "https://cdn.x.com/a.jpg"),
    ("http://cdn.x.com/a.jpg", None, "http://cdn.x.com/a.jpg"),
    ("/img/a.jpg", "https://site.com/cars/1", "https://site.com/img/a.jpg"),
    ("//cdn.x.com/a.jpg", "https://site.com/cars/1", "https://cdn.x.com/a.jpg"),
    ("  https://cdn.x.com/a.jpg  ", None, "https://cdn.x.com/a.jpg"),
    ("/img/a.jpg", None, None),                       # relative and no base
    ("data:image/png;base64,AAAA", None, None),
    ("javascript:alert(1)", "https://site.com", None),
    ("ftp://files.x.com/a.jpg", None, None),
    ("", None, None),
    (None, None, None),
    (float("nan"), None, None),
])
def test_normalize_image_url(value, base, expected):
    assert normalize_image_url(value, base) == expected


# ---- extract_primary_image ------------------------------------------------

def soup(html):
    return BeautifulSoup(html, "lxml")


def test_extract_og_image_relative_to_absolute():
    s = soup('<head><meta property="og:image" content="/photos/1.jpg">'
             '<meta property="og:image:alt" content="Blue Swift, front view"></head>')
    assert extract_primary_image(s, "https://site.com/listing/9") == (
        "https://site.com/photos/1.jpg", "Blue Swift, front view")


def test_extract_twitter_image_fallback():
    s = soup('<head><meta name="twitter:image" content="https://cdn.x.com/t.jpg"></head>')
    assert extract_primary_image(s, "https://site.com/l") == ("https://cdn.x.com/t.jpg", None)


@pytest.mark.parametrize("ld", [
    '{"@type":"Car","image":"https://cdn.x.com/ld.jpg"}',
    '{"@type":"Car","image":["https://cdn.x.com/ld.jpg","https://cdn.x.com/2.jpg"]}',
    '{"@type":"Car","image":{"@type":"ImageObject","url":"https://cdn.x.com/ld.jpg"}}',
    '{"@graph":[{"@type":"WebPage"},{"@type":"Car","image":"https://cdn.x.com/ld.jpg"}]}',
    '[{"@type":"Car","image":"https://cdn.x.com/ld.jpg"}]',
])
def test_extract_json_ld_image(ld):
    s = soup(f'<script type="application/ld+json">{ld}</script>')
    assert extract_primary_image(s, "https://site.com/l")[0] == "https://cdn.x.com/ld.jpg"


def test_extract_returns_none_when_no_image_or_bad_json():
    assert extract_primary_image(soup("<html></html>"), "https://site.com") == (None, None)
    broken = soup('<script type="application/ld+json">{not json</script>')
    assert extract_primary_image(broken, "https://site.com") == (None, None)
    data_uri = soup('<meta property="og:image" content="data:image/png;base64,AAAA">')
    assert extract_primary_image(data_uri, "https://site.com")[0] is None


# ---- cleaning keeps only safe image URLs ------------------------------------------

def _raw(**over):
    row = {"source": "a", "brand": "honda", "model": "city", "year": 2018, "fuel_type": "petrol",
           "km_driven": "40,000 km", "price": "₹ 7 Lakh", "location": "kochi",
           "seller_type": "dealer", "url": "u1", "scraped_on": "x"}
    row.update(over)
    return pd.DataFrame([row])


def test_clean_adds_image_columns_when_missing():
    out = clean_dataframe(_raw())
    assert out.loc[0, "image_url"] is None and out.loc[0, "image_alt"] is None


def test_clean_keeps_good_and_drops_bad_image_urls():
    good = clean_dataframe(_raw(image_url="https://cdn.x.com/a.jpg", image_alt=" Honda City "))
    assert good.loc[0, "image_url"] == "https://cdn.x.com/a.jpg"
    assert good.loc[0, "image_alt"] == "Honda City"
    bad = clean_dataframe(_raw(image_url="data:image/png;base64,AAAA"))
    assert bad.loc[0, "image_url"] is None


def test_clean_handles_empty_image_columns_from_csv(tmp_path):
    p = tmp_path / "raw.csv"
    _raw(image_url=None, image_alt=None).to_csv(p, index=False)   # all-empty columns read back as NaN
    out = clean_dataframe(pd.read_csv(p))
    assert out.loc[0, "image_url"] is None


# ---- database: image columns and upgrading an old database -------------------------

def test_insert_without_image_columns_still_works(tmp_path):
    path = tmp_path / "t.db"
    df = clean_dataframe(_raw()).drop(columns=["image_url", "image_alt"])
    assert db.insert_vehicles(df, path) == 1
    row = db.query_vehicles({}, path)[0]
    assert row["image_url"] is None


def test_missing_required_column_still_fails_loudly(tmp_path):
    df = clean_dataframe(_raw()).drop(columns=["image_url", "image_alt", "price"])
    with pytest.raises(KeyError):
        db.insert_vehicles(df, tmp_path / "t.db")


def test_init_db_upgrades_an_old_database(tmp_path):
    path = tmp_path / "old.db"
    old = sqlite3.connect(path)
    old.executescript("""
        CREATE TABLE vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT, source TEXT, brand TEXT NOT NULL,
            model TEXT NOT NULL, year INTEGER NOT NULL, fuel_type TEXT, km_driven INTEGER,
            price INTEGER NOT NULL, location TEXT, seller_type TEXT, url TEXT UNIQUE, scraped_on TEXT);
        INSERT INTO vehicles (source, brand, model, year, price, url) VALUES ('a','Honda','City',2018,700000,'u1');
    """)
    old.commit(); old.close()

    db.init_db(path)
    db.init_db(path)   # running twice must be harmless
    cols = {r["name"] for r in db.get_connection(path).execute("PRAGMA table_info(vehicles)")}
    assert {"image_url", "image_alt"} <= cols
    row = db.query_vehicles({}, path)[0]
    assert row["model"] == "City" and row["image_url"] is None   # old data kept
