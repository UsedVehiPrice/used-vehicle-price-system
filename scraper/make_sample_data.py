"""Generate realistic SAMPLE listings so everyone can build and test the
cleaning / database / API / dashboard before the real scrapers are ready.

This is fake data for development only. Do not present it as real results.

Usage:  python -m scraper.make_sample_data
"""
import random
from datetime import date
from pathlib import Path

import pandas as pd

random.seed(42)

CARS = {  # (brand, model): approx. price in rupees when new-ish (2023)
    ("Maruti Suzuki", "Swift"): 700000,
    ("Maruti Suzuki", "Baleno"): 750000,
    ("Hyundai", "i20"): 800000,
    ("Hyundai", "Creta"): 1300000,
    ("Honda", "City"): 1200000,
    ("Toyota", "Innova"): 1900000,
    ("Tata", "Nexon"): 1000000,
    ("Mahindra", "XUV500"): 1500000,
}
SOURCES = ["site-a", "site-b", "site-c"]
CITIES = ["Kochi", "Thrissur", "Bengaluru", "Chennai", "Coimbatore"]
FUELS = ["Petrol", "Diesel", "CNG", "petrol", "DIESEL"]  # messy on purpose


def price_text(value):
    style = random.choice(["lakh", "plain", "rs"])
    if style == "lakh":
        return f"₹ {value / 100000:.2f} Lakh"
    if style == "rs":
        return f"Rs. {value:,}"
    return str(value)


def km_text(km):
    return random.choice([f"{km:,} km", f"{km} KMs", f"{km / 1000:.0f}k km"])


rows = []
for _ in range(300):
    (brand, model), base = random.choice(list(CARS.items()))
    year = random.randint(2012, 2023)
    km = random.randint(5000, 150000)
    age = 2026 - year
    value = int(base * (0.88 ** age) * (1 - km / 600000) * random.uniform(0.9, 1.1))
    rows.append({
        "source": random.choice(SOURCES),
        "brand": brand,
        "model": model,
        "year": year,
        "fuel_type": random.choice(FUELS),
        "km_driven": km_text(km),
        "price": price_text(value),
        "location": random.choice(CITIES),
        "seller_type": random.choice(["Individual", "Dealer"]),
        "url": f"https://example.com/listing/{random.randint(100000, 999999)}",
        "scraped_on": date.today().isoformat(),
    })

# add a few duplicates and a broken row to exercise the cleaning code
rows.extend(rows[:5])
rows.append({**rows[0], "price": "Call for price", "url": "https://example.com/listing/1"})

out = Path("data/raw")
out.mkdir(parents=True, exist_ok=True)
path = out / "sample_listings.csv"
pd.DataFrame(rows).to_csv(path, index=False)
print(f"Wrote {len(rows)} sample rows to {path}")
