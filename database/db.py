"""SQLite helpers: create the database, insert, and query vehicles.

Public API (for other teams):
    init_db()                      – create tables from schema.sql
    insert_vehicles(df)            – bulk-insert a cleaned DataFrame (skips duplicates)
    query_vehicles(filters)        – flexible search with filters, sort, limit
    get_compare(model, year)       – avg / min price per source for a model
    get_stats()                    – avg price by brand, model, year
"""
import os
import sqlite3
from pathlib import Path

HERE = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("VEHICLE_DB", HERE / "vehicles.db"))

# ---------------------------------------------------------------------------
# Connection
# ---------------------------------------------------------------------------

def get_connection(path=None):
    """Return a sqlite3 connection with Row factory enabled."""
    conn = sqlite3.connect(path or DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


# ---------------------------------------------------------------------------
# init_db
# ---------------------------------------------------------------------------

def init_db(path=None):
    """Create the vehicles table (and indexes) from schema.sql."""
    with get_connection(path) as conn:
        conn.executescript((HERE / "schema.sql").read_text())


# ---------------------------------------------------------------------------
# insert_vehicles
# ---------------------------------------------------------------------------

_COLS = [
    "source", "brand", "model", "year", "fuel_type", "km_driven",
    "price", "location", "seller_type", "url", "scraped_on",
]


def insert_vehicles(df, path=None):
    """Bulk-insert a cleaned DataFrame into the vehicles table.

    Uses INSERT OR IGNORE so rows whose (source, url) already exist
    are silently skipped.  Returns the number of newly inserted rows.
    """
    init_db(path)

    placeholders = ", ".join("?" for _ in _COLS)
    col_names = ", ".join(_COLS)
    sql = f"INSERT OR IGNORE INTO vehicles ({col_names}) VALUES ({placeholders})"

    records = [
        tuple(None if v is None or v != v else v for v in row)
        for row in df[_COLS].astype(object).itertuples(index=False, name=None)
    ]

    with get_connection(path) as conn:
        before = conn.total_changes
        conn.executemany(sql, records)
        return conn.total_changes - before


# ---------------------------------------------------------------------------
# query_vehicles
# ---------------------------------------------------------------------------

_ALLOWED_SORT = {"price", "year", "km_driven"}


def query_vehicles(filters: dict, path=None):
    """Search the vehicles table with optional filters.

    Supported keys in *filters*:
        brand      – exact match (case-insensitive)
        model      – exact match (case-insensitive)
        fuel       – exact match on fuel_type (case-insensitive)
        min_year   – year >= value
        max_year   – year <= value
        max_km     – km_driven <= value
        max_price  – price <= value
        sort       – column to ORDER BY (price | year | km_driven)
        limit      – max rows returned (default 50)

    Returns a list of dicts (one per vehicle row).
    """
    where, params = [], []

    if filters.get("brand"):
        where.append("LOWER(brand) = LOWER(?)")
        params.append(filters["brand"])
    if filters.get("model"):
        where.append("LOWER(model) = LOWER(?)")
        params.append(filters["model"])
    if filters.get("fuel"):
        where.append("LOWER(fuel_type) = LOWER(?)")
        params.append(filters["fuel"])
    if filters.get("min_year") is not None:
        where.append("year >= ?")
        params.append(int(filters["min_year"]))
    if filters.get("max_year") is not None:
        where.append("year <= ?")
        params.append(int(filters["max_year"]))
    if filters.get("max_km") is not None:
        where.append("km_driven <= ?")
        params.append(int(filters["max_km"]))
    if filters.get("max_price") is not None:
        where.append("price <= ?")
        params.append(int(filters["max_price"]))

    clause = "WHERE " + " AND ".join(where) if where else ""

    sort_col = filters.get("sort", "price")
    if sort_col not in _ALLOWED_SORT:
        sort_col = "price"

    limit = int(filters.get("limit", 50))

    sql = f"SELECT * FROM vehicles {clause} ORDER BY {sort_col} ASC LIMIT ?"
    params.append(limit)

    with get_connection(path) as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# get_compare
# ---------------------------------------------------------------------------

def get_compare(model, year=None, path=None):
    """Return avg and min price per source for a given model (and optional year).

    Returns a list of dicts with keys:
        source, listings, avg_price, min_price, max_price
    """
    sql = (
        "SELECT source, COUNT(*) AS listings, ROUND(AVG(price)) AS avg_price, "
        "MIN(price) AS min_price, MAX(price) AS max_price "
        "FROM vehicles WHERE LOWER(model) = LOWER(?)"
    )
    params = [model]

    if year is not None:
        sql += " AND year = ?"
        params.append(int(year))

    sql += " GROUP BY source ORDER BY avg_price"

    with get_connection(path) as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


# ---------------------------------------------------------------------------
# get_stats
# ---------------------------------------------------------------------------

def get_stats(path=None):
    """Return average price by brand, model, and year.

    Returns a list of dicts with keys:
        brand, model, year, listings, avg_price
    """
    sql = (
        "SELECT brand, model, year, COUNT(*) AS listings, "
        "ROUND(AVG(price)) AS avg_price FROM vehicles "
        "GROUP BY brand, model, year ORDER BY brand, model, year"
    )
    with get_connection(path) as conn:
        return [dict(r) for r in conn.execute(sql).fetchall()]


# ---------------------------------------------------------------------------
# Backward compat alias so old code still works during migration
# ---------------------------------------------------------------------------

def load_dataframe(df, path=None):
    """Alias for insert_vehicles (backward compatibility)."""
    return insert_vehicles(df, path)
