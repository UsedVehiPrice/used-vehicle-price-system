import pandas as pd
import pytest
from fastapi.testclient import TestClient

from database import db

ROWS = [
    {"source": "site-a", "brand": "Honda", "model": "City", "year": 2018,
     "fuel_type": "Petrol", "km_driven": 40000, "price": 700000,
     "location": "Kochi", "seller_type": "Dealer", "url": "u1", "scraped_on": "2026-11-11",
     "image_url": "https://cdn.example.org/city1.jpg", "image_alt": "White Honda City"},
    {"source": "site-b", "brand": "Honda", "model": "City", "year": 2018,
     "fuel_type": "Petrol", "km_driven": 60000, "price": 650000,
     "location": "Kochi", "seller_type": "Individual", "url": "u2", "scraped_on": "2026-11-11",
     "image_url": None, "image_alt": None},
    {"source": "site-a", "brand": "Hyundai", "model": "Creta", "year": 2020,
     "fuel_type": "Diesel", "km_driven": 30000, "price": 1200000,
     "location": "Chennai", "seller_type": "Dealer", "url": "u3", "scraped_on": "2026-11-11",
     # stored badly on purpose: the API must never return these
     "image_url": "/relative/creta.jpg", "image_alt": "should be dropped"},
    {"source": "site-b", "brand": "Tata", "model": "Nexon", "year": 2021,
     "fuel_type": "Petrol", "km_driven": None, "price": 900000,
     "location": "Coimbatore", "seller_type": "Dealer", "url": "u4", "scraped_on": "2026-11-11",
     "image_url": "data:image/png;base64,AAAA", "image_alt": None},
]


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    db.insert_vehicles(pd.DataFrame(ROWS))
    from backend.main import app
    with TestClient(app) as c:
        yield c


# ---- /vehicles ------------------------------------------------------------

def test_vehicles_filter_and_sort(client):
    data = client.get("/vehicles", params={"brand": "honda", "sort": "price"}).json()
    assert [r["price"] for r in data] == [650000, 700000]


def test_vehicles_default_is_cheapest_first(client):
    prices = [r["price"] for r in client.get("/vehicles").json()]
    assert prices == sorted(prices) and len(prices) == 4


def test_vehicles_other_filters(client):
    assert len(client.get("/vehicles", params={"max_km": 35000}).json()) == 1
    assert len(client.get("/vehicles", params={"fuel": "diesel"}).json()) == 1
    assert len(client.get("/vehicles", params={"min_year": 2020}).json()) == 2
    assert len(client.get("/vehicles", params={"max_year": 2018}).json()) == 2
    assert len(client.get("/vehicles", params={"max_price": 700000}).json()) == 2
    assert client.get("/vehicles", params={"model": "nope"}).json() == []


def test_vehicles_limit(client):
    assert len(client.get("/vehicles", params={"limit": 2}).json()) == 2
    assert len(client.get("/vehicles", params={"limit": 500}).json()) == 4   # what the frontend sends


def test_vehicles_response_has_every_field_the_frontend_reads(client):
    row = client.get("/vehicles", params={"brand": "honda", "sort": "price"}).json()[1]
    for key in ("id", "source", "brand", "model", "year", "fuel_type", "km_driven", "price",
                "location", "seller_type", "url", "image_url", "image_alt"):
        assert key in row
    assert row["image_url"] == "https://cdn.example.org/city1.jpg"
    assert row["image_alt"] == "White Honda City"


def test_missing_image_is_null_not_a_stock_photo(client):
    row = client.get("/vehicles", params={"max_price": 650000}).json()[0]
    assert row["image_url"] is None and row["image_alt"] is None


def test_unsafe_image_urls_are_never_returned(client):
    rows = {r["model"]: r for r in client.get("/vehicles").json()}
    assert rows["Creta"]["image_url"] is None and rows["Creta"]["image_alt"] is None   # relative path
    assert rows["Nexon"]["image_url"] is None                                           # base64 data URI


def test_null_km_is_allowed(client):
    rows = {r["model"]: r for r in client.get("/vehicles").json()}
    assert rows["Nexon"]["km_driven"] is None


@pytest.mark.parametrize("params", [
    {"sort": "price; DROP TABLE vehicles"},
    {"sort": "brand"},
    {"limit": 0},
    {"limit": 2001},
    {"max_km": -1},
    {"min_year": "abc"},
    {"max_price": -5},
])
def test_bad_input_is_rejected(client, params):
    assert client.get("/vehicles", params=params).status_code == 422


def test_sql_injection_in_text_filters_is_harmless(client):
    r = client.get("/vehicles", params={"brand": "x' OR '1'='1"})
    assert r.status_code == 200 and r.json() == []
    assert client.get("/health").json()["vehicles"] == 4


# ---- /compare -------------------------------------------------------------

def test_compare(client):
    data = client.get("/compare", params={"model": "city"}).json()
    assert {r["source"] for r in data} == {"site-a", "site-b"}
    a = next(r for r in data if r["source"] == "site-a")
    assert a["listings"] == 1 and a["min_price"] == a["max_price"] == 700000


def test_compare_with_year(client):
    assert client.get("/compare", params={"model": "City", "year": 2018}).json() != []
    assert client.get("/compare", params={"model": "City", "year": 2010}).json() == []


def test_compare_requires_model(client):
    assert client.get("/compare").status_code == 422
    assert client.get("/compare", params={"model": ""}).status_code == 422


# ---- /stats and /health -----------------------------------------------------

def test_stats(client):
    data = client.get("/stats").json()
    assert len(data) == 3
    city = next(r for r in data if r["model"] == "City")
    assert city["listings"] == 2 and city["avg_price"] == 675000


def test_health(client):
    assert client.get("/health").json() == {"status": "ok", "vehicles": 4}


# ---- CORS and errors ----------------------------------------------------------

def test_cors_allows_the_vite_dev_server(client):
    r = client.get("/vehicles", headers={"Origin": "http://localhost:5173"})
    assert r.headers.get("access-control-allow-origin") == "http://localhost:5173"


def test_cors_blocks_unknown_origins(client):
    r = client.get("/vehicles", headers={"Origin": "http://evil.example"})
    assert "access-control-allow-origin" not in r.headers


def test_database_failure_returns_503_without_details(client, tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "missing-folder" / "x.db")
    r = client.get("/vehicles")
    assert r.status_code == 503
    assert "missing-folder" not in r.text and "sqlite" not in r.text.lower()
