import pandas as pd
import pytest
from fastapi.testclient import TestClient

from database import db


@pytest.fixture()
def client(tmp_path, monkeypatch):
    test_db = tmp_path / "test.db"
    monkeypatch.setattr(db, "DB_PATH", test_db)
    df = pd.DataFrame([
        {"source": "site-a", "brand": "Honda", "model": "City", "year": 2018,
         "fuel_type": "Petrol", "km_driven": 40000, "price": 700000,
         "location": "Kochi", "seller_type": "Dealer", "url": "u1", "scraped_on": "2026-11-11"},
        {"source": "site-b", "brand": "Honda", "model": "City", "year": 2018,
         "fuel_type": "Petrol", "km_driven": 60000, "price": 650000,
         "location": "Kochi", "seller_type": "Individual", "url": "u2", "scraped_on": "2026-11-11"},
        {"source": "site-a", "brand": "Hyundai", "model": "Creta", "year": 2020,
         "fuel_type": "Diesel", "km_driven": 30000, "price": 1200000,
         "location": "Chennai", "seller_type": "Dealer", "url": "u3", "scraped_on": "2026-11-11"},
    ])
    db.load_dataframe(df)
    from backend.main import app
    with TestClient(app) as c:
        yield c


def test_vehicles_filter_and_sort(client):
    data = client.get("/vehicles", params={"brand": "honda", "sort": "price"}).json()
    assert [r["price"] for r in data] == [650000, 700000]


def test_vehicles_max_km(client):
    data = client.get("/vehicles", params={"max_km": 35000}).json()
    assert len(data) == 1 and data[0]["model"] == "Creta"


def test_invalid_sort_rejected(client):
    assert client.get("/vehicles", params={"sort": "price; DROP TABLE vehicles"}).status_code == 422


def test_compare(client):
    data = client.get("/compare", params={"model": "city"}).json()
    assert {r["source"] for r in data} == {"site-a", "site-b"}


def test_stats(client):
    data = client.get("/stats").json()
    assert len(data) == 2
