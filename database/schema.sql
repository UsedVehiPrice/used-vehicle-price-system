CREATE TABLE IF NOT EXISTS vehicles (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    source      TEXT,
    brand       TEXT NOT NULL,
    model       TEXT NOT NULL,
    year        INTEGER NOT NULL,
    fuel_type   TEXT,
    km_driven   INTEGER,
    price       INTEGER NOT NULL,
    location    TEXT,
    seller_type TEXT,
    url         TEXT UNIQUE,
    scraped_on  TEXT
);

CREATE INDEX IF NOT EXISTS idx_vehicles_model ON vehicles(brand, model);
CREATE INDEX IF NOT EXISTS idx_vehicles_year  ON vehicles(year);
CREATE INDEX IF NOT EXISTS idx_vehicles_price ON vehicles(price);
