"""Listing-image helpers shared by the scrapers, the cleaning step and the API.

The frontend shows `image_url` / `image_alt` for each listing. Rules:
  * the image must be the primary photo of THAT listing (never a stock photo);
  * the URL must be absolute http(s) (no relative paths, no base64 data: URIs);
  * if there is no usable image, the value is None.

Only use these helpers on sites whose terms allow scraping.
"""
import json
from urllib.parse import urljoin, urlparse


def normalize_image_url(value, base_url=None):
    """Return an absolute http(s) URL, or None when the value is unusable."""
    if not isinstance(value, str):
        return None
    value = value.strip()
    if not value or value.lower().startswith(("data:", "javascript:")):
        return None
    absolute = urljoin(base_url, value) if base_url else value
    parts = urlparse(absolute)
    if parts.scheme not in ("http", "https") or not parts.netloc:
        return None
    return absolute


def _meta(soup, **attrs):
    tag = soup.find("meta", attrs=attrs)
    content = tag.get("content") if tag else None
    return content.strip() if isinstance(content, str) and content.strip() else None


def _first_image_in_json(node):
    """Find the first `image` value in JSON-LD data (str, list or {'url': ...})."""
    if isinstance(node, list):
        for item in node:
            found = _first_image_in_json(item)
            if found:
                return found
        return None
    if not isinstance(node, dict):
        return None
    image = node.get("image")
    if isinstance(image, str):
        return image
    if isinstance(image, list) and image:
        first = image[0]
        return first if isinstance(first, str) else (first or {}).get("url")
    if isinstance(image, dict):
        return image.get("url")
    for key in ("@graph", "mainEntity", "itemOffered"):
        found = _first_image_in_json(node.get(key))
        if found:
            return found
    return None


def extract_primary_image(soup, page_url):
    """Return (image_url, image_alt) for a listing page, or (None, None).

    Order: og:image meta tag -> twitter:image meta tag -> JSON-LD `image`.
    """
    raw = _meta(soup, property="og:image") or _meta(soup, name="twitter:image")
    alt = _meta(soup, property="og:image:alt") or _meta(soup, name="twitter:image:alt")
    if not raw:
        for script in soup.find_all("script", type="application/ld+json"):
            try:
                data = json.loads(script.string or "")
            except (ValueError, TypeError):
                continue
            raw = _first_image_in_json(data)
            if raw:
                break
    return normalize_image_url(raw, page_url), (alt if raw else None)
