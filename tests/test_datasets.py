import pandas as pd
import pytest

import import_dataset
from analysis.clean import clean_dataframe
from database import db
from scraper.datasets import (DEFAULT_SOURCE, load_used_cars_price_csv, restore_case,
                              split_name, validate_source_name)

HEADER = "Name,Location,Year,Kilometers_Driven,Fuel_Type,Transmission,Owner_Type,Mileage,Engine,Power,Seats,Price\n"
ROWS = [
    "Maruti Wagon R LXI CNG,Mumbai,2010,72000,CNG,Manual,First,26.6 km/kg,998 CC,58.16 bhp,5.0,1.75",
    "Hyundai Creta 1.6 CRDi SX Option,Chennai,2015,41000,Diesel,Manual,First,19.67 kmpl,1582 CC,126.2 bhp,5.0,12.50",
    "BMW 3 Series 320d Luxury Line,Kochi,2014,50000,Diesel,Automatic,First,18 kmpl,1995 CC,184 bhp,5.0,22.0",
    "Ford Ecosport 1.5 Titanium,Coimbatore,2016,30000,Petrol,Manual,First,17 kmpl,1498 CC,110 bhp,5.0,6.5",
    "Ford EcoSport 1.5 Trend,Coimbatore,2017,31000,Petrol,Manual,First,17 kmpl,1498 CC,110 bhp,5.0,7.0",
    "Mahindra XUV500 W8,Pune,2013,90000,Diesel,Manual,Second,15 kmpl,2179 CC,140 bhp,7.0,6.0",
    "Honda City 1.5 V,Delhi,2012,6500000,Petrol,Manual,First,17 kmpl,1497 CC,118 bhp,5.0,3.0",   # absurd km: dropped by cleaning
]


@pytest.fixture()
def csv_path(tmp_path):
    p = tmp_path / "Data_Train.csv"
    p.write_text(HEADER + "\n".join(ROWS) + "\n")
    return str(p)


# ---- name splitting ------------------------------------------------------------

@pytest.mark.parametrize("name,expected", [
    ("Hyundai Creta 1.6 CRDi SX Option", ("Hyundai", "Creta")),
    ("Maruti Wagon R LXI CNG", ("Maruti", "Wagon R")),
    ("Hyundai Grand i10 Magna", ("Hyundai", "Grand i10")),
    ("Land Rover Range Rover 2.2L Pure", ("Land Rover", "Range Rover")),
    ("BMW 3 Series 320d", ("BMW", "3 Series")),
    ("Mercedes-Benz New C-Class 200", ("Mercedes-Benz", "C-Class")),
    ("Mercedes-Benz GLA Class 200 CDI", ("Mercedes-Benz", "GLA Class")),
    ("Toyota Innova 2.5 G", ("Toyota", "Innova")),
    ("Tata", ("Tata", "")),
])
def test_split_name(name, expected):
    assert split_name(name) == expected


# ---- loading Data_Train.csv ------------------------------------------------------

def test_load_converts_lakhs_and_builds_unique_keys(csv_path):
    raw = load_used_cars_price_csv(csv_path)
    assert list(raw["price"][:2]) == [175000, 1250000]
    assert raw["url"].is_unique and raw.loc[0, "url"] == f"{DEFAULT_SOURCE}:row-0"
    assert (raw["source"] == DEFAULT_SOURCE).all()
    assert raw["seller_type"].isna().all() and raw["image_url"].isna().all()


def test_load_rejects_a_saved_web_page(tmp_path):
    p = tmp_path / "cardekho.csv"
    p.write_text(",car_name,brand\n,,\n<!DOCTYPE html>,,\n<html lang=\"en\">,,\n")
    with pytest.raises(ValueError, match="saved web page"):
        load_used_cars_price_csv(str(p))


def test_load_rejects_the_test_file_without_price(tmp_path):
    p = tmp_path / "Data_Test.csv"
    p.write_text(HEADER.replace(",Price", "") + ROWS[0].rsplit(",", 1)[0] + "\n")
    with pytest.raises(ValueError, match="Price"):
        load_used_cars_price_csv(str(p))


# ---- case restoring ----------------------------------------------------------------

def test_restore_case_keeps_acronyms_and_merges_spellings(csv_path):
    raw = load_used_cars_price_csv(csv_path)
    out = restore_case(clean_dataframe(raw), raw)
    assert "BMW" in set(out["brand"]) and "Bmw" not in set(out["brand"])
    assert "XUV500" in set(out["model"])
    assert len({m for m in out["model"] if m.lower() == "ecosport"}) == 1   # Ecosport / EcoSport -> one spelling


# ---- the command-line tool --------------------------------------------------------------

def test_import_loads_database_and_is_safe_to_repeat(csv_path, tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "t.db")
    assert import_dataset.main([csv_path]) == 0
    rows = db.query_vehicles({"limit": 100})
    assert len(rows) == 6                                  # 7 read, absurd-km row dropped
    assert {r["price"] for r in rows} >= {175000, 1250000}
    assert all(r["source"] == DEFAULT_SOURCE for r in rows)
    capsys.readouterr()
    assert import_dataset.main([csv_path]) == 0            # second run adds nothing
    assert "New rows added to the database: 0" in capsys.readouterr().out
    assert len(db.query_vehicles({"limit": 100})) == 6


def test_cities_option_limits_the_import(csv_path, tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "t.db")
    assert import_dataset.main([csv_path, "--cities", "chennai, Coimbatore"]) == 0
    assert {r["location"] for r in db.query_vehicles({"limit": 100})} == {"Chennai", "Coimbatore"}


def test_unknown_city_lists_the_available_ones(csv_path, capsys):
    assert import_dataset.main([csv_path, "--cities", "Atlantis"]) == 1
    err = capsys.readouterr().err
    assert "Atlantis".lower() in err.lower() and "Chennai" in err


def test_dry_run_does_not_touch_the_database(csv_path, tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "t.db")
    assert import_dataset.main([csv_path, "--dry-run"]) == 0
    assert not (tmp_path / "t.db").exists()


def test_bad_files_give_a_clear_error_and_exit_code(tmp_path, capsys):
    p = tmp_path / "page.csv"
    p.write_text("<!DOCTYPE html><html></html>")
    assert import_dataset.main([str(p)]) == 1
    assert "saved web page" in capsys.readouterr().err
    assert import_dataset.main([str(tmp_path / "missing.csv")]) == 1


def test_reserved_sample_source_names_are_refused(csv_path):
    with pytest.raises(ValueError):
        validate_source_name("site-a")
    assert import_dataset.main([csv_path, "--source", "site-b", "--dry-run"]) == 1


# ---- scraper CSV (e.g. data/raw/carwale.csv) ------------------------------------------------

SCRAPED_HEADER = "source,brand,model,year,fuel_type,km_driven,price,location,seller_type,url,scraped_on,image_url,image_alt\n"
SCRAPED_ROWS = [
    "carwale,Toyota,Urban Cruiser Hyryder,2024,Hybrid,24800,1775000,\"Makarba, Ahmedabad\",,https://www.carwale.com/used/ahmedabad/toyota-urban-cruiser-hyryder/ab12cd/,2026-11-21,https://imgd.aeplcdn.com/664x374/n/a.jpg,Toyota Hyryder",
    "carwale,Maruti Suzuki,Swift,2019,Petrol,45000,520000,\"Adyar, Chennai\",,https://www.carwale.com/used/chennai/maruti-suzuki-swift/xy98zt/,2026-11-21,,",
    "carwale,Tata,Nexon,2021,Electric,12300,1210000,Chennai,,https://www.carwale.com/used/chennai/tata-nexon/q1w2e3/,2026-11-21,\"data:image/png;base64,AAAA\",",
    "carwale,Tata,Nexon,2021,Electric,12300,1210000,Chennai,,https://www.carwale.com/used/chennai/tata-nexon/q1w2e3/,2026-11-21,,",   # same listing twice
    "carwale,Honda,City,2018,Petrol,40000,,Chennai,,https://www.carwale.com/used/chennai/honda-city/no1price/,2026-11-21,,",     # no price: dropped
]


@pytest.fixture()
def scraped_path(tmp_path):
    p = tmp_path / "carwale.csv"
    p.write_text(SCRAPED_HEADER + "\n".join(SCRAPED_ROWS) + "\n")
    return str(p)


def test_format_detection(csv_path, scraped_path):
    from scraper.datasets import detect_format
    assert detect_format(csv_path) == "used-cars-price"
    assert detect_format(scraped_path) == "scraped"


def test_unknown_layout_is_rejected(tmp_path, capsys):
    p = tmp_path / "other.csv"
    p.write_text("a,b\n1,2\n")
    assert import_dataset.main([str(p)]) == 1
    assert "unknown file layout" in capsys.readouterr().err


def test_scraped_import_keeps_listing_url_and_photo(scraped_path, tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "t.db")
    assert import_dataset.main([scraped_path]) == 0
    rows = {r["model"]: r for r in db.query_vehicles({"limit": 100})}
    assert set(rows) == {"Urban Cruiser Hyryder", "Swift", "Nexon"}        # duplicate and no-price rows gone
    hy = rows["Urban Cruiser Hyryder"]
    assert hy["source"] == "carwale"
    assert hy["url"].startswith("https://www.carwale.com/used/ahmedabad/")
    assert hy["image_url"] == "https://imgd.aeplcdn.com/664x374/n/a.jpg"
    assert hy["location"] == "Ahmedabad" and hy["fuel_type"] == "Hybrid" and hy["price"] == 1775000
    assert rows["Swift"]["brand"] == "Maruti Suzuki" and rows["Swift"]["image_url"] is None
    assert rows["Nexon"]["image_url"] is None                                 # data: URIs are refused


def test_scraped_import_twice_and_several_files(scraped_path, tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "t.db")
    assert import_dataset.main([scraped_path, scraped_path]) == 0             # same file twice in one run
    assert len(db.query_vehicles({"limit": 100})) == 3
    assert "Total new rows added: 3" in capsys.readouterr().out


def test_scraped_import_does_not_mix_with_dataset_rows_by_url(csv_path, scraped_path, tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "t.db")
    assert import_dataset.main([csv_path, scraped_path]) == 0
    sources = {r["source"] for r in db.query_vehicles({"limit": 100})}
    assert sources == {DEFAULT_SOURCE, "carwale"}


def test_scraped_cities_filter_uses_the_city(scraped_path, tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "t.db")
    assert import_dataset.main([scraped_path, "--cities", "chennai"]) == 0
    assert {r["location"] for r in db.query_vehicles({"limit": 100})} == {"Chennai"}


def test_one_bad_file_does_not_stop_the_others(scraped_path, tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "t.db")
    assert import_dataset.main([str(tmp_path / "missing.csv"), scraped_path]) == 1
    assert len(db.query_vehicles({"limit": 100})) == 3
