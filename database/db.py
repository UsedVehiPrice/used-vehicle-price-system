"""SQLite helpers: create the database and load cleaned data."""
import os
import sqlite3
from pathlib import Path

HERE = Path(__file__).resolve().parent
DB_PATH = Path(os.environ.get("VEHICLE_DB", HERE / "vehicles.db"))


def get_connection(path=None):
    conn = sqlite3.connect(path or DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(path=None):
    with get_connection(path) as conn:
        conn.executescript((HERE / "schema.sql").read_text())


def load_dataframe(df, path=None):
    """Insert cleaned rows; listings with an existing URL are skipped."""
    init_db(path)
    cols = ["source", "brand", "model", "year", "fuel_type", "km_driven",
            "price", "location", "seller_type", "url", "scraped_on"]
    records = [
        tuple(None if v is None or v != v else v for v in row)
        for row in df[cols].astype(object).itertuples(index=False, name=None)
    ]
    with get_connection(path) as conn:
        before = conn.total_changes
        conn.executemany(
            f"INSERT OR IGNORE INTO vehicles ({', '.join(cols)}) "
            f"VALUES ({', '.join('?' * len(cols))})",
            records,
        )
        return conn.total_changes - before
