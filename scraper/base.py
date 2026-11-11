"""Base class for all website scrapers.

Every site gets its own file (e.g. scraper/site_olx.py) with a class that
inherits BaseScraper and implements `parse_listing_page`. All scrapers must
return rows with the same fields (see FIELDS) so the rest of the pipeline
(cleaning, database, API) works for every site.
"""
import time
import urllib.robotparser
from datetime import date
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

# The shared data contract. Keep in sync with database/schema.sql.
FIELDS = [
    "source", "brand", "model", "year", "fuel_type", "km_driven",
    "price", "location", "seller_type", "url", "scraped_on",
]

USER_AGENT = "UsedVehiclePriceStudentProject/1.0 (college project; contact: your-email@example.com)"


class BaseScraper:
    source = "unknown"          # name of the website
    delay_seconds = 2.0         # pause between requests (be polite)
    max_pages = 5               # keep small while developing

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT})
        self._robots = {}

    # ---- politeness helpers -------------------------------------------
    def allowed_by_robots(self, url):
        parts = urlparse(url)
        base = f"{parts.scheme}://{parts.netloc}"
        if base not in self._robots:
            rp = urllib.robotparser.RobotFileParser()
            rp.set_url(base + "/robots.txt")
            try:
                rp.read()
            except Exception:
                rp = None  # robots.txt unreachable: be conservative below
            self._robots[base] = rp
        rp = self._robots[base]
        return bool(rp and rp.can_fetch(USER_AGENT, url))

    def fetch(self, url):
        """Download a page and return a BeautifulSoup object, or None."""
        if not self.allowed_by_robots(url):
            print(f"[{self.source}] blocked by robots.txt, skipping: {url}")
            return None
        time.sleep(self.delay_seconds)
        try:
            resp = self.session.get(url, timeout=20)
            resp.raise_for_status()
        except requests.RequestException as exc:
            print(f"[{self.source}] request failed: {exc}")
            return None
        return BeautifulSoup(resp.text, "lxml")

    # ---- to be implemented per site -----------------------------------
    def page_urls(self):
        """Yield the listing-page URLs to visit."""
        raise NotImplementedError

    def parse_listing_page(self, soup):
        """Return a list of dicts (one per vehicle) using the FIELDS keys."""
        raise NotImplementedError

    # ---- main entry point ---------------------------------------------
    def run(self):
        rows = []
        for i, url in enumerate(self.page_urls()):
            if i >= self.max_pages:
                break
            soup = self.fetch(url)
            if soup is None:
                continue
            for row in self.parse_listing_page(soup):
                row.setdefault("source", self.source)
                row.setdefault("url", url)
                row["scraped_on"] = date.today().isoformat()
                rows.append({k: row.get(k) for k in FIELDS})
        return rows
