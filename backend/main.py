"""FastAPI backend for the Used Vehicle Price Comparison system.

Run (from the project root, venv activated):
    uvicorn backend.main:app --reload                       # development
    uvicorn backend.main:app --host 0.0.0.0 --port 8000     # reachable from other laptops
    python -m uvicorn backend.main:app --reload             # if uvicorn.exe is blocked

Interactive docs: http://127.0.0.1:8000/docs

Endpoints (used by the React frontend):
    GET /vehicles   listings, with filters           (image_url / image_alt included)
    GET /compare    price per source for one model
    GET /stats      average price by brand / model / year
    GET /health     quick check that the API and database are up

All data access goes through database/db.py, so SQL lives in one place.

Environment variables (all optional):
    VEHICLE_DB      path to the SQLite file (default database/vehicles.db)
    CORS_ORIGINS    comma-separated browser origins allowed to call the API
                    (default: the Vite dev server on port 5173)
"""
import os
import sqlite3
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from database.db import get_compare, get_connection, get_stats, init_db, query_vehicles
from scraper.images import normalize_http_url

MAX_LIMIT = 10000   # the frontend asks for 5000 at a time


# ---------------------------------------------------------------------------
# Response shapes (what the frontend can rely on)
# ---------------------------------------------------------------------------

class Vehicle(BaseModel):
    id: int
    source: Optional[str] = None
    brand: str
    model: str
    year: int
    fuel_type: Optional[str] = None
    km_driven: Optional[int] = None
    price: int
    location: Optional[str] = None
    seller_type: Optional[str] = None
    url: Optional[str] = None
    scraped_on: Optional[str] = None
    image_url: Optional[str] = None   # absolute http(s) URL of this listing's photo, or null
    image_alt: Optional[str] = None


class SourceComparison(BaseModel):
    source: Optional[str] = None
    listings: int
    avg_price: float
    min_price: int
    max_price: int


class MarketStat(BaseModel):
    brand: str
    model: str
    year: int
    listings: int
    avg_price: float


class Health(BaseModel):
    status: str
    vehicles: int


# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app):
    init_db()   # creates the table / adds new columns if needed
    yield


app = FastAPI(
    title="Used Vehicle Price Comparison API",
    description="Search, compare and analyse used-vehicle listings collected by web scraping.",
    lifespan=lifespan,
)

_origins = [
    o.strip()
    for o in os.environ.get("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.exception_handler(sqlite3.Error)
async def database_error(request: Request, exc: sqlite3.Error):
    # Never leak SQL or file paths to the browser.
    return JSONResponse(status_code=503, content={"detail": "Database unavailable. Run the pipeline and retry."})


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

def _serialize(row: dict) -> dict:
    """Only absolute http(s) links ever leave the API (listing url and photo url).
    Dataset rows carry an internal key instead of a web address; that is returned as null."""
    row = dict(row)
    row["url"] = normalize_http_url(row.get("url"))
    row["image_url"] = normalize_http_url(row.get("image_url"))
    if not row["image_url"]:
        row["image_alt"] = None
    return row


@app.get("/vehicles", response_model=List[Vehicle])
def list_vehicles(
    brand: Optional[str] = Query(None, description="Exact brand, case-insensitive"),
    model: Optional[str] = Query(None, description="Exact model, case-insensitive"),
    fuel: Optional[str] = Query(None, description="Fuel type, e.g. Petrol, Diesel, CNG"),
    min_year: Optional[int] = Query(None, ge=1900, le=2100),
    max_year: Optional[int] = Query(None, ge=1900, le=2100),
    max_km: Optional[int] = Query(None, ge=0, description="Maximum kilometres driven"),
    max_price: Optional[int] = Query(None, ge=0, description="Maximum price in rupees"),
    sort: str = Query("price", pattern="^(price|year|km_driven)$"),
    limit: int = Query(50, ge=1, le=MAX_LIMIT),
):
    """Listings sorted ascending by `sort` (default: cheapest first)."""
    filters = {
        "brand": brand, "model": model, "fuel": fuel,
        "min_year": min_year, "max_year": max_year,
        "max_km": max_km, "max_price": max_price,
        "sort": sort, "limit": limit,
    }
    return [_serialize(r) for r in query_vehicles(filters)]


@app.get("/compare", response_model=List[SourceComparison])
def compare(
    model: str = Query(..., min_length=1, description="Model name, e.g. City"),
    year: Optional[int] = Query(None, ge=1900, le=2100),
):
    """The same model across websites: listings, average, min and max price per source."""
    return get_compare(model, year)


@app.get("/stats", response_model=List[MarketStat])
def stats():
    """Average price and listing count by brand, model and year."""
    return get_stats()


@app.get("/health", response_model=Health)
def health():
    with get_connection() as conn:
        count = conn.execute("SELECT COUNT(*) FROM vehicles").fetchone()[0]
    return {"status": "ok", "vehicles": count}
