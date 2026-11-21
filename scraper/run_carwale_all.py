"""Scrape SEVERAL CarWale model pages in one go and merge them into one CSV.

    python -m scraper.run_carwale_all --probe                 # 1 page of the first model only, to test
    python -m scraper.run_carwale_all --only hyundai-creta    # one model from the list
    python -m scraper.run_carwale_all                         # every model in scraper/carwale_models.txt (all-India pages)
    python -m scraper.run_carwale_all --cities chennai,coimbatore --max-pages 5    # city pages (smaller, local)
    python -m scraper.run_carwale_all --cities chennai,coimbatore --resume         # continue after an interruption

Run it from the project folder. It uses scraper/site_carwale.py for each model page, so the same rules
apply: robots.txt is checked, there is a pause between pages, no personal data is collected. Between
models it waits 5-10 seconds. Press Ctrl+C to stop early: what was collected so far is still saved.
A model page that fails (wrong slug, blocked, nothing found) is skipped and
listed at the end. Each model also gets its own file in data/raw/carwale/. Afterwards:

    python import_dataset.py data/raw/carwale_all.csv
"""
import argparse
import random
import re
import time
from pathlib import Path

import pandas as pd

from scraper import site_carwale

MODELS_FILE = Path(__file__).with_name("carwale_models.txt")
BASE = "https://www.carwale.com/used/"


def read_models(path=MODELS_FILE):
    """Return [(slug, url)] from the model list (slugs or full URLs, # comments allowed)."""
    out, seen = [], set()
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        line = line.split("#", 1)[0].strip()
        if not line:
            continue
        if line.startswith("http"):
            url = line.rstrip("/") + "/"
            slug = url.rstrip("/").rsplit("/", 1)[-1]
        else:
            slug = line.strip("/").lower()
            url = f"{BASE}{slug}/"
        slug = re.sub(r"[^a-z0-9-]+", "-", slug)
        if url not in seen:
            seen.add(url)
            out.append((slug, url))
    return out


def with_cities(models, cities):
    """Turn all-India model pages into city pages: .../used/<slug>/ -> .../used/<city>/<slug>/.
    Entries that are already a full city URL are kept as they are."""
    if not cities:
        return models
    out = []
    for slug, url in models:
        if url.startswith(BASE) and url[len(BASE):].strip("/").count("/") == 0:
            out.extend((f"{c}-{slug}", f"{BASE}{c}/{slug}/") for c in cities)
        else:
            out.append((slug, url))
    return out


def run(models, out, max_pages, probe=False, with_variant=False, headless=True, pause=(5, 10), resume=False):
    """Scrape each model, return (merged DataFrame, {slug: reason} for skipped models)."""
    per_model_dir = Path(out).parent / "carwale"
    frames, skipped = [], {}
    try:
        for i, (slug, url) in enumerate(models):
            print(f"\n=== [{i + 1}/{len(models)}] {slug}  {url}")
            part = per_model_dir / f"{slug}.csv"
            if resume and part.exists() and not probe:
                frames.append(pd.read_csv(part))
                print("  already scraped, using the saved file")
                continue
            try:
                site_carwale.scrape(url, max_pages, str(part), probe, with_variant, headless)
            except SystemExit as exc:                       # robots.txt blocked / nothing parsed
                skipped[slug] = str(exc.code or "stopped")
                print(f"  skipped: {skipped[slug]}")
            except Exception as exc:                        # network error, timeout, page changed ...
                skipped[slug] = f"{type(exc).__name__}: {exc}"
                print(f"  skipped: {skipped[slug]}")
            else:
                if not probe and part.exists():
                    frames.append(pd.read_csv(part))
            if probe:
                break
            if i < len(models) - 1:
                time.sleep(random.uniform(*pause))
    except KeyboardInterrupt:
        print("\nStopped by you. Saving what was collected so far.")
    merged = pd.concat(frames, ignore_index=True).drop_duplicates("url") if frames else pd.DataFrame()
    return merged, skipped


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--models-file", default=str(MODELS_FILE))
    ap.add_argument("--only", help="scrape only this slug from the list, e.g. hyundai-creta")
    ap.add_argument("--cities", help="comma separated cities, e.g. chennai,coimbatore: scrape the city page of each model")
    ap.add_argument("--resume", action="store_true", help="reuse model files already saved in data/raw/carwale/")
    ap.add_argument("--max-pages", type=int, default=3, help="pages per model (default 3 - keep it small)")
    ap.add_argument("--out", default="data/raw/carwale_all.csv")
    ap.add_argument("--probe", action="store_true", help="test: first model, page 1 only, nothing saved")
    ap.add_argument("--with-variant", action="store_true")
    ap.add_argument("--show-browser", action="store_true")
    a = ap.parse_args(argv)

    models = read_models(a.models_file)
    if a.only:
        models = [m for m in models if m[0] == a.only] or [(a.only, f"{BASE}{a.only}/")]
    cities = [re.sub(r"[^a-z0-9]+", "-", c.strip().lower()).strip("-") for c in (a.cities or "").split(",") if c.strip()]
    models = with_cities(models, cities)
    if not models:
        raise SystemExit("No models in the list.")
    merged, skipped = run(models, a.out, a.max_pages, a.probe, a.with_variant, not a.show_browser, resume=a.resume)

    print("\n" + "=" * 60)
    if not a.probe and not merged.empty:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        merged.to_csv(a.out, index=False)
        print(f"Saved {len(merged)} listings from {len(models) - len(skipped)} model pages to {a.out}")
        print("Next:  python import_dataset.py " + a.out)
    elif not a.probe:
        print("Nothing was scraped.")
    if skipped:
        print(f"Skipped {len(skipped)} model page(s):")
        for slug, why in skipped.items():
            print(f"  {slug}: {why}")
    return 0 if (a.probe or not merged.empty) else 1


if __name__ == "__main__":
    raise SystemExit(main())
