"""TEMPLATE scraper: copy this file for each website (site_olx.py, ...).

The CSS selectors below are PLACEHOLDERS. Open the real website in your
browser, right-click a listing -> Inspect, and replace the selectors with the
ones that match that site's HTML.

Before scraping any site:
  1. Read its robots.txt (https://<site>/robots.txt) and terms of service.
  2. Only scrape what is allowed. Do not collect personal data (phone numbers).
  3. Keep delay_seconds >= 2 and max_pages small.
"""
from scraper.base import BaseScraper


class TemplateSiteScraper(BaseScraper):
    source = "example-site"
    base_url = "https://example.com/used-cars?page={page}"   # TODO: real URL

    def page_urls(self):
        for page in range(1, self.max_pages + 1):
            yield self.base_url.format(page=page)

    def parse_listing_page(self, soup):
        rows = []
        # TODO: replace ".listing-card" and the selectors inside it.
        for card in soup.select(".listing-card"):
            title = card.select_one(".title")
            price = card.select_one(".price")
            details = card.select_one(".details")
            link = card.select_one("a")
            if not (title and price):
                continue  # skip incomplete listings
            rows.append({
                "brand": None,            # fill from the title or a field
                "model": title.get_text(strip=True),
                "year": None,             # e.g. parse from details text
                "fuel_type": None,
                "km_driven": details.get_text(strip=True) if details else None,
                "price": price.get_text(strip=True),   # raw text, cleaned later
                "location": None,
                "seller_type": None,
                "url": link["href"] if link and link.has_attr("href") else None,
            })
        return rows
