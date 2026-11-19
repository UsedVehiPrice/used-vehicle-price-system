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
from scraper.images import extract_primary_image, normalize_image_url


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

            # Listing photo (optional). Two ways, use whichever the site supports:
            #  a) the <img> on the card:
            img = card.select_one("img")
            image_url = normalize_image_url(
                (img.get("src") or img.get("data-src")) if img else None,
                base_url=self.base_url,
            )
            image_alt = img.get("alt") if img else None
            #  b) the listing's own page (og:image / JSON-LD), one extra request:
            #       detail = self.fetch(listing_url)
            #       image_url, image_alt = extract_primary_image(detail, listing_url) if detail else (None, None)
            # Never use a generic stock photo; None is fine.

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
                "image_url": image_url,
                "image_alt": image_alt,
            })
        return rows
