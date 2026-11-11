"""FastAPI backend.  Run:  uvicorn backend.main:app --reload
Docs UI:  http://127.0.0.1:8000/docs
"""
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Query

from database.db import get_connection, init_db


@asynccontextmanager
async def lifespan(app):
    init_db()
    yield


app = FastAPI(title="Used Vehicle Price Comparison API", lifespan=lifespan)


@app.get("/vehicles")
def list_vehicles(
    brand: Optional[str] = None,
    model: Optional[str] = None,
    fuel: Optional[str] = None,
    min_year: Optional[int] = None,
    max_year: Optional[int] = None,
    max_km: Optional[int] = None,
    max_price: Optional[int] = None,
    sort: str = Query("price", pattern="^(price|year|km_driven)$"),
    limit: int = Query(50, ge=1, le=500),
):
    where, params = [], []
    if brand:
        where.append("LOWER(brand) = LOWER(?)"); params.append(brand)
    if model:
        where.append("LOWER(model) = LOWER(?)"); params.append(model)
    if fuel:
        where.append("LOWER(fuel_type) = LOWER(?)"); params.append(fuel)
    if min_year:
        where.append("year >= ?"); params.append(min_year)
    if max_year:
        where.append("year <= ?"); params.append(max_year)
    if max_km:
        where.append("km_driven <= ?"); params.append(max_km)
    if max_price:
        where.append("price <= ?"); params.append(max_price)
    clause = f"WHERE {' AND '.join(where)}" if where else ""
    # `sort` is validated by the regex above, so it is safe to interpolate.
    sql = f"SELECT * FROM vehicles {clause} ORDER BY {sort} ASC LIMIT ?"
    with get_connection() as conn:
        rows = conn.execute(sql, (*params, limit)).fetchall()
    return [dict(r) for r in rows]


@app.get("/compare")
def compare(model: str, year: Optional[int] = None):
    """Same model across websites: average / min / max price per source."""
    sql = (
        "SELECT source, COUNT(*) AS listings, ROUND(AVG(price)) AS avg_price, "
        "MIN(price) AS min_price, MAX(price) AS max_price "
        "FROM vehicles WHERE LOWER(model) = LOWER(?)"
    )
    params = [model]
    if year:
        sql += " AND year = ?"; params.append(year)
    sql += " GROUP BY source ORDER BY avg_price"
    with get_connection() as conn:
        return [dict(r) for r in conn.execute(sql, params).fetchall()]


@app.get("/stats")
def stats():
    """Average price by brand/model/year."""
    sql = (
        "SELECT brand, model, year, COUNT(*) AS listings, "
        "ROUND(AVG(price)) AS avg_price FROM vehicles "
        "GROUP BY brand, model, year ORDER BY brand, model, year"
    )
    with get_connection() as conn:
        return [dict(r) for r in conn.execute(sql).fetchall()]
