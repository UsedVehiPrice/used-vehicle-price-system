"""
scraper/site_carwale.py - CarWale used-car scraper for UsedVehiPrice.

Output CSV columns match the API fields in the project README:
  source, brand, model, year, fuel_type, km_driven, price, location,
  seller_type, url, scraped_on, image_url, image_alt
(`url` is the listing page on carwale.com; `price` is in INR.)

Setup:   pip install playwright pandas && playwright install chromium

Optional: put your contact e-mail in the User-Agent (good scraping manners) by setting it in YOUR terminal,
never in the code or in Git:
  Windows (cmd):   set SCRAPER_CONTACT=you@example.com
  Mac / Linux:     export SCRAPER_CONTACT=you@example.com

Usage:
  python scraper/site_carwale.py --probe            # 1 page, prints diagnostics, saves debug files
  python scraper/site_carwale.py --max-pages 2      # small test run
  python scraper/site_carwale.py                    # all pages -> data/raw/carwale.csv
  python scraper/site_carwale.py --url https://www.carwale.com/used/hyundai-creta/ --out data/raw/carwale_creta.csv

Rules (same as the project README): robots.txt is checked, >= 2 s between
pages, no personal data (seller names / phone numbers) is collected.
"""
import argparse
import os
import random
import re
import time
import urllib.error
import urllib.request
import urllib.robotparser
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

import pandas as pd
from playwright.sync_api import sync_playwright

DEFAULT_URL = "https://www.carwale.com/used/toyota-urban-cruiser-hyryder/"
CONTACT = os.environ.get("SCRAPER_CONTACT", "").strip()      # optional, see the note at the top
USER_AGENT = "Mozilla/5.0 (UsedVehiPrice student project" + (f"; contact: {CONTACT}" if CONTACT else "") + ")"
SOURCE = "carwale"
DEBUG_DIR = Path("data/debug")

COLUMNS = ["source", "brand", "model", "year", "fuel_type", "km_driven", "price",
           "location", "seller_type", "url", "scraped_on", "image_url", "image_alt"]

# CarWale card text, as seen on the live site (2026-11):
#   "2019 Maruti Suzuki Swift VXi AMT\n39,000 km  |  Petrol  |  Andheri-Kurla Road, Mumbai"
# The PRICE is not in that title text; it sits elsewhere on the same card, so it is searched in the whole
# card text (EXTRACT_JS returns it as "card"). The older layout "... | Makarba, Ahmedabad Rs. 17.75 Lakh"
# (price right after the location) is still understood.
LISTING_RE = re.compile(
    r"(?P<year>(?:19|20)\d{2})\s+(?P<name>.+?)\s+(?P<km>[\d,]+)\s*km\s*\|\s*(?P<fuel>[^|]+?)\s*\|\s*"
    r"(?P<location>.+)",
    re.I | re.S,
)
_PRICE_ANY = re.compile(r"(?:Rs\.?|₹)\s*[\d.,]+")
# "Rs. 4.50 Lakh" / "₹ 1.2 Crore". A card can also show a struck-through old price, so take the lowest.
PRICE_RE = re.compile(r"(?:Rs\.?|₹)\s*([\d.,]+)\s*(Lakh|Lac|Crore|Cr)\b", re.I)
# plain rupees like "₹ 85,000", but not EMI figures such as "₹ 9,500/month"
_PRICE_PLAIN = re.compile(r"(?:Rs\.?|₹)\s*(\d{1,3}(?:,\d{2,3})+)(?!\s*(?:/|per\b|p\.?m\b|EMI|month))", re.I)


def find_price(text):
    """Lowest price found in `text` as whole rupees, or None."""
    text = " ".join(str(text or "").split())
    values = []
    for number, unit in PRICE_RE.findall(text):
        try:
            values.append(float(number.replace(",", "")) * (1e7 if unit.lower().startswith("cr") else 1e5))
        except ValueError:
            pass
    if not values:
        values = [float(n.replace(",", "")) for n in _PRICE_PLAIN.findall(text)]
        values = [v for v in values if 30_000 <= v <= 50_000_000]
    return int(round(min(values))) if values else None


MULTI_WORD_BRANDS = ["Maruti Suzuki", "Mercedes-Benz", "Land Rover", "Rolls-Royce",
                     "Aston Martin", "Force Motors", "Mini Cooper"]

# Runs inside the page. Returns one record per listing-link currently in the DOM.
EXTRACT_JS = r"""
() => {
  const re = /^\/used\/[a-z0-9-]+\/[a-z0-9-]+\/[a-z0-9]{5,}\/?$/i;
  const pathOf = a => { try { return new URL(a.href).pathname; } catch (e) { return ""; } };
  const out = [];
  document.querySelectorAll("a[href*='/used/']").forEach(a => {
    if (!re.test(pathOf(a))) return;
    // the widest ancestor that still contains only THIS listing = the whole card (title, price, photo)
    let card = a;
    for (let i = 0; i < 8 && card.parentElement; i++) {
      const parent = card.parentElement;
      const paths = new Set();
      parent.querySelectorAll("a[href*='/used/']").forEach(x => { const p = pathOf(x); if (re.test(p)) paths.add(p); });
      if (paths.size > 1) break;
      card = parent;
    }
    // every picture in the card (lazy-loaded, srcset, <picture>); Python picks the real car photo
    const biggest = ss => {
      let best = "", bestN = -1;
      ss.split(",").forEach(part => {
        const bits = part.trim().split(/\s+/);
        const n = parseFloat(bits[1]) || 0;
        if (bits[0] && n >= bestN) { best = bits[0]; bestN = n; }
      });
      return best;
    };
    const imgs = [];
    card.querySelectorAll("img, source").forEach(el => {
      const isImg = el.tagName === "IMG";
      // a <source> has no size of its own: use the size of the <img> next to it
      const sizeEl = isImg ? el : (el.parentElement ? el.parentElement.querySelector("img") : null);
      const w = sizeEl ? (sizeEl.naturalWidth || sizeEl.width || 0) : 0;
      const h = sizeEl ? (sizeEl.naturalHeight || sizeEl.height || 0) : 0;
      const cands = [];
      const ss = el.getAttribute("srcset") || el.getAttribute("data-srcset");
      if (ss) cands.push(biggest(ss));
      if (isImg) cands.push(el.currentSrc, el.getAttribute("data-src"), el.getAttribute("data-lazy-src"),
                            el.getAttribute("data-original"), el.src);
      // keep every candidate: Python drops placeholders / logos and keeps the real photo
      new Set(cands.filter(c => c && c.trim()).map(c => c.trim())).forEach(src =>
        imgs.push({src: src, alt: isImg ? (el.alt || "") : "", w: w, h: h}));
    });
    out.push({href: a.href.split("?")[0], text: (a.innerText || a.textContent || "").trim(),
              card: (card.innerText || card.textContent || "").trim(), imgs: imgs});
  });
  return out;
}
"""
MAX_PAGE_JS = r"""
() => Math.max(1, ...Array.from(document.querySelectorAll("a[href*='/page-']"))
   .map(a => (a.href.match(/\/page-(\d+)/) || [0, 1])[1] * 1))
"""


# ----------------------------------------------------------------- parsing
def split_brand_model(name: str, href: str):
    brand = next((b for b in MULTI_WORD_BRANDS if name.lower().startswith(b.lower())), None)
    if brand is None:
        brand = name.split()[0]
    rest_words = name[len(brand):].split()
    # URL is /used/<city>/<model-slug>/<id>/ -> the model slug is the segment before the id
    slug = urlparse(href).path.strip("/").split("/")[-2]         # e.g. toyota-urban-cruiser-hyryder
    brand_slug = brand.lower().replace(" ", "-")
    if slug.startswith(brand_slug + "-"):
        model_slug = slug[len(brand_slug) + 1:]
        n_model_words, acc = None, []
        for i, w in enumerate(rest_words):          # consume words until they spell the slug
            acc.append(re.sub(r"[^a-z0-9]+", "-", w.lower()).strip("-"))
            if "-".join(acc) == model_slug:
                n_model_words = i + 1
                break
        if n_model_words is None:                   # fallback: count slug tokens
            n_model_words = len(model_slug.split("-"))
        model = " ".join(rest_words[:n_model_words])
        variant = " ".join(rest_words[n_model_words:])
    else:
        model, variant = " ".join(rest_words[:1]), " ".join(rest_words[1:])
    return brand, model, variant


def parse_card(text: str, href: str, card_text: str = ""):
    norm = " ".join(text.split())          # also turns non-breaking spaces and newlines into single spaces
    m = LISTING_RE.search(norm)
    if not m:
        return None
    price = find_price(norm) or find_price(card_text)
    if price is None:
        return None
    name = m["name"].strip()
    # the location ends where a price starts (older layout); "Mumbai" / "Andheri (E), Mumbai"
    location = _PRICE_ANY.split(m["location"])[0].strip(" ,|")
    fuel = re.sub(r"\s*\+\s*\d+\s*$", "", m["fuel"].strip())     # "Petrol + 1" (a second fuel option) -> "Petrol"
    # Fuel is sometimes printed as "Hybrid (Electric + Petrol)" and, on older cards, hybrids
    # as plain "Petrol"; normalise using both the fuel field and the variant name.
    if re.search(r"hybrid", fuel + " " + name, re.I):
        fuel = "Hybrid"
    elif re.search(r"\bcng\b", fuel + " " + name, re.I):
        fuel = "CNG"
    elif re.fullmatch(r"electric|ev", fuel, re.I) or re.search(r"\b(ev|electric)\b", name, re.I):
        fuel = "Electric"
    else:
        fuel = fuel.title()
    brand, model, variant = split_brand_model(name, href)
    return {"year": int(m["year"]), "brand": brand, "model": model, "variant": variant,
            "fuel_type": fuel, "km_driven": int(m["km"].replace(",", "")),
            "location": location, "price": price}


# words in an image path that mean "not the car photo": placeholders, logos, icons, badges
_NOT_A_CAR_PHOTO = re.compile(r"(grey|gray|placeholder|blank|spacer|loader|sprite|logo|icon|badge|noimage|no-image|default)", re.I)


def clean_image_url(src):
    """An absolute http(s) URL of a normal photo, or None (data: URIs, svg/gif, placeholders, logos)."""
    src = str(src or "").strip()
    if src.startswith("//"):
        src = "https:" + src
    if not re.match(r"https?://", src, re.I):
        return None
    path = urlparse(src).path.lower()
    if path.endswith((".svg", ".gif")) or _NOT_A_CAR_PHOTO.search(path):
        return None
    return src


def choose_image(pictures):
    """Pick the car photo from every picture found on a card: the largest real photo.
    `pictures` = [{"src", "alt", "w", "h"}]. Returns (image_url, image_alt), each None if there is none."""
    best, best_area = (None, None), 0
    for pic in pictures:
        url = clean_image_url(pic.get("src"))
        if not url:
            continue
        w, h = int(pic.get("w") or 0), int(pic.get("h") or 0)
        if w and h and (w < 100 or h < 60):        # too small to be the car photo (icon, badge)
            continue
        area = w * h if (w and h) else 1           # size unknown: still usable, but loses to a known big one
        if area > best_area:
            best, best_area = (url, (pic.get("alt") or "").strip() or None), area
    return best


def records_to_rows(bucket: dict):
    """bucket: href -> list of raw anchor records. Returns (rows, unparsed_texts)."""
    rows, unparsed = [], []
    today = date.today().isoformat()
    for href, recs in bucket.items():
        parsed = None
        card = max((r.get("card") or "" for r in recs), key=len, default="")
        for r in recs:                      # a card has several anchors; one holds the full text
            parsed = parse_card(r["text"], href, card)
            if parsed:
                break
        if not parsed:
            title = max((r["text"] for r in recs), key=len, default="")
            unparsed.append((href, f"TITLE: {title!r} || CARD: {card[:500]!r}"))
            continue
        pictures = [i for r in recs for i in (r.get("imgs") or [])]
        pictures += [{"src": r["img"], "alt": r.get("alt", "")} for r in recs if r.get("img")]   # older record shape
        img, alt = choose_image(pictures)
        rows.append({"source": SOURCE, **parsed, "seller_type": "", "url": href,
                     "scraped_on": today, "image_url": img, "image_alt": alt})
    return rows, unparsed


# ---------------------------------------------------------------- browsing
def allowed_by_robots(url: str) -> bool:
    p = urlparse(url)
    robots_url = f"{p.scheme}://{p.netloc}/robots.txt"
    # urllib's default user agent is often answered with 403, which RobotFileParser.read()
    # treats as "disallow everything". Fetch with our own identifying UA and parse manually.
    try:
        req = urllib.request.Request(robots_url, headers={"User-Agent": USER_AGENT})
        with urllib.request.urlopen(req, timeout=15) as resp:
            lines = resp.read().decode("utf-8", "replace").splitlines()
    except urllib.error.HTTPError as e:
        if e.code == 404:                      # no robots.txt = no restrictions
            return True
        print(f"  could not read robots.txt (HTTP {e.code})")
        return False
    except Exception as e:
        print(f"  could not read robots.txt ({e})")
        return False
    rp = urllib.robotparser.RobotFileParser()
    rp.parse(lines)
    return rp.can_fetch("*", url)


def harvest(page, bucket: dict):
    for r in page.evaluate(EXTRACT_JS):
        bucket.setdefault(r["href"], []).append(r)


def load_whole_page(page, bucket: dict, slow: bool = False, max_steps: int = 150):
    """Scroll in small steps and harvest at EVERY step (works even if the site removes
    off-screen cards), clicking any 'load more' button. Stops once nothing new appears."""
    wait_ms = 900 if slow else 350
    stale = 0
    for _ in range(max_steps):
        before = len(bucket)
        harvest(page, bucket)
        try:
            btn = page.get_by_role("button", name=re.compile(r"(load|show|view) more", re.I))
            if btn.count() and btn.first.is_visible():
                btn.first.click(timeout=2000)
                page.wait_for_timeout(1200)
        except Exception:
            pass
        page.evaluate("window.scrollBy(0, Math.round(window.innerHeight * 0.7))")
        page.wait_for_timeout(wait_ms)
        harvest(page, bucket)
        at_bottom = page.evaluate(
            "window.scrollY + window.innerHeight >= document.documentElement.scrollHeight - 5")
        stale = stale + 1 if len(bucket) == before else 0
        if at_bottom and stale >= 4:
            break
    # belt and braces: return to the top and harvest once more (catches cards a
    # virtualised list dropped or that rendered late)
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(wait_ms + 300)
    harvest(page, bucket)


def save_debug(page, tag: str, unparsed):
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    (DEBUG_DIR / f"carwale_{tag}.html").write_text(page.content(), encoding="utf-8")
    page.screenshot(path=str(DEBUG_DIR / f"carwale_{tag}.png"), full_page=True)
    if unparsed:
        with open(DEBUG_DIR / f"carwale_{tag}_unparsed.txt", "w", encoding="utf-8") as f:
            for href, text in unparsed:
                f.write(f"{href}\n{text}\n\n")


def scrape(base_url: str, max_pages: int, out: str, probe: bool, with_variant: bool, headless: bool):
    if not allowed_by_robots(base_url):
        raise SystemExit("robots.txt disallows (or could not be read for) this URL. Stopping.")

    all_rows, seen = [], set()
    expected_total, total_pages = None, None
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=headless)
        page = browser.new_context(user_agent=USER_AGENT, viewport={"width": 1366, "height": 900}).new_page()

        n = 0
        while n < (1 if probe else max_pages):
            n += 1
            url = base_url if n == 1 else f"{base_url.rstrip('/')}/page-{n}/"
            page.goto(url, wait_until="domcontentloaded", timeout=60000)
            try:   # wait for real listing cards (not just nav links) before scrolling
                page.wait_for_function(f"({EXTRACT_JS})().length > 0", timeout=20000)
            except Exception:
                print(f"  page {n}: no listing cards appeared within 20 s")
            if n == 1:
                m = re.search(r"([\d,]+)\s+Used", page.title())
                expected_total = int(m[1].replace(",", "")) if m else None
                total_pages = page.evaluate(MAX_PAGE_JS)
                print(f"site says {expected_total} listings over ~{total_pages} pages")

            bucket = {}
            load_whole_page(page, bucket)
            rows, unparsed = records_to_rows(bucket)
            if len(rows) < 15 and (total_pages is None or n < total_pages):   # suspiciously few
                print(f"  page {n}: only {len(rows)} found, retrying slower...")
                load_whole_page(page, bucket, slow=True)
                rows, unparsed = records_to_rows(bucket)

            new = [r for r in rows if r["url"] not in seen]
            seen.update(r["url"] for r in new)
            all_rows.extend(new)
            print(f"page {n}: {len(bucket)} listing links, {len(rows)} parsed, "
                  f"{len(new)} new, {len(unparsed)} unparsed (total {len(all_rows)})")
            if unparsed or probe:
                save_debug(page, f"page{n}", unparsed)
            if not new:
                break
            if total_pages and n >= total_pages:
                break
            if not probe:
                time.sleep(random.uniform(3, 6))
        browser.close()

    df = pd.DataFrame(all_rows)
    if df.empty:
        raise SystemExit("No rows parsed. Look at data/debug/*.html and *_unparsed.txt, then adjust LISTING_RE.")
    df = df.drop_duplicates("url")
    with_photo = int(df["image_url"].notna().sum())
    print(f"{with_photo} of {len(df)} listings have a photo URL")
    if with_photo < 0.8 * len(df):
        print("WARNING: many listings have no photo. Open data/debug/*.html (run with --probe) and send it to be checked.")
    cols = COLUMNS[:]
    if with_variant:
        cols.insert(cols.index("year"), "variant")
    df = df[cols]
    if not probe:
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(out, index=False)
        print(f"Saved {len(df)} rows to {out}")
    else:
        print(df.head(10).to_string())
    if expected_total and not probe and len(df) < 0.95 * expected_total:
        print(f"WARNING: got {len(df)} of {expected_total} listings. Check data/debug/ and rerun with "
              f"--show-browser to watch it scroll.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default=DEFAULT_URL)
    ap.add_argument("--max-pages", type=int, default=30)
    ap.add_argument("--out", default="data/raw/carwale.csv")
    ap.add_argument("--probe", action="store_true", help="scrape page 1 only and print diagnostics")
    ap.add_argument("--with-variant", action="store_true", help="add a 'variant' column")
    ap.add_argument("--show-browser", action="store_true")
    a = ap.parse_args()
    scrape(a.url, a.max_pages, a.out, a.probe, a.with_variant, headless=not a.show_browser)
