import pandas as pd
import pytest

pytest.importorskip("playwright")        # the scraper needs playwright; skip these tests where it is not installed

from scraper import run_carwale_all as runner  # noqa: E402


def test_read_models_accepts_slugs_urls_comments_and_duplicates(tmp_path):
    f = tmp_path / "m.txt"
    f.write_text("# comment\n\nhyundai-creta\nHyundai-Creta  # again\nhttps://www.carwale.com/used/tata-nexon\n")
    assert runner.read_models(f) == [
        ("hyundai-creta", "https://www.carwale.com/used/hyundai-creta/"),
        ("tata-nexon", "https://www.carwale.com/used/tata-nexon/"),
    ]


def test_shipped_model_list_is_valid():
    models = runner.read_models()
    assert len(models) >= 20 and all(u.startswith("https://www.carwale.com/used/") for _, u in models)


def _fake_scrape(rows_by_slug):
    def fake(url, max_pages, out, probe, with_variant, headless):
        slug = url.rstrip("/").rsplit("/", 1)[-1]
        if slug not in rows_by_slug:
            raise SystemExit("No rows parsed.")
        if slug == "boom":
            raise RuntimeError("timeout")
        from pathlib import Path
        Path(out).parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(rows_by_slug[slug]).to_csv(out, index=False)
    return fake


def test_run_merges_dedupes_and_reports_skipped(tmp_path, monkeypatch):
    row = lambda u: {"source": "carwale", "brand": "Tata", "model": "Nexon", "year": 2021, "price": 1, "url": u}
    monkeypatch.setattr(runner.site_carwale, "scrape", _fake_scrape({"a": [row("u1"), row("u2")], "b": [row("u2"), row("u3")]}))
    monkeypatch.setattr(runner.time, "sleep", lambda s: None)
    models = [("a", runner.BASE + "a/"), ("b", runner.BASE + "b/"), ("missing", runner.BASE + "missing/")]
    merged, skipped = runner.run(models, str(tmp_path / "all.csv"), 1)
    assert sorted(merged["url"]) == ["u1", "u2", "u3"]            # u2 appeared on two model pages
    assert list(skipped) == ["missing"]
    assert (tmp_path / "carwale" / "a.csv").exists()


def test_main_writes_the_merged_csv(tmp_path, monkeypatch, capsys):
    row = {"source": "carwale", "brand": "Tata", "model": "Nexon", "year": 2021, "price": 1, "url": "u1"}
    monkeypatch.setattr(runner.site_carwale, "scrape", _fake_scrape({"tata-nexon": [row]}))
    monkeypatch.setattr(runner.time, "sleep", lambda s: None)
    out = tmp_path / "all.csv"
    assert runner.main(["--only", "tata-nexon", "--out", str(out)]) == 0
    assert len(pd.read_csv(out)) == 1
    assert "import_dataset.py" in capsys.readouterr().out


def test_with_cities_expands_model_pages_to_city_pages():
    models = [("tata-nexon", runner.BASE + "tata-nexon/"), ("x", runner.BASE + "pune/x/")]
    assert runner.with_cities(models, []) == models
    assert runner.with_cities(models, ["chennai", "coimbatore"]) == [
        ("chennai-tata-nexon", runner.BASE + "chennai/tata-nexon/"),
        ("coimbatore-tata-nexon", runner.BASE + "coimbatore/tata-nexon/"),
        ("x", runner.BASE + "pune/x/"),                # already a city URL: unchanged
    ]


def test_main_with_cities_and_resume(tmp_path, monkeypatch):
    row = {"source": "carwale", "brand": "Tata", "model": "Nexon", "year": 2021, "price": 1, "url": "u1"}
    calls = []
    fake = _fake_scrape({"tata-nexon": [row]})
    monkeypatch.setattr(runner.site_carwale, "scrape", lambda url, *a, **k: (calls.append(url), fake(url, *a, **k))[1])
    monkeypatch.setattr(runner.time, "sleep", lambda s: None)
    out = tmp_path / "all.csv"
    assert runner.main(["--only", "tata-nexon", "--cities", "Chennai", "--out", str(out)]) == 0
    assert calls == [runner.BASE + "chennai/tata-nexon/"]
    assert runner.main(["--only", "tata-nexon", "--cities", "chennai", "--out", str(out), "--resume"]) == 0
    assert len(calls) == 1                              # second run reused the saved file


def test_ctrl_c_keeps_what_was_collected(tmp_path, monkeypatch):
    row = lambda u: {"source": "carwale", "brand": "Tata", "model": "Nexon", "year": 2021, "price": 1, "url": u}
    ok = _fake_scrape({"a": [row("u1")], "b": [row("u2")]})

    def scrape(url, *args, **kw):
        if url.endswith("/b/"):
            raise KeyboardInterrupt
        return ok(url, *args, **kw)
    monkeypatch.setattr(runner.site_carwale, "scrape", scrape)
    monkeypatch.setattr(runner.time, "sleep", lambda s: None)
    merged, skipped = runner.run([("a", runner.BASE + "a/"), ("b", runner.BASE + "b/")], str(tmp_path / "all.csv"), 1)
    assert list(merged["url"]) == ["u1"] and skipped == {}
