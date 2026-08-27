# HD Deal Finder

An unofficial, personal-use website that shows Home Depot clearance and
markdown deals in a browsable grid (similar to rebelsavings.com/home-depot),
backed by a scraper that periodically checks homedepot.com.

Two independent pieces:

- **Scraper** (`app/scraper/`) — uses a headless browser (Playwright) to load
  Home Depot search/category pages, pulls out any item with a real
  "was → now" price drop, and stores it in SQLite.
- **Website** (`app/main.py` + `app/static/`) — a small FastAPI app that
  serves a JSON API over that data and a plain HTML/CSS/JS frontend (no
  build step) that renders it as a filterable, sortable deal grid.

## Important: this needs to run somewhere that can reach homedepot.com

This code was written in a sandboxed environment whose network policy
blocks outbound requests to homedepot.com entirely, so **the scraper
could not be tested against the live site**. Everything else (API, DB,
frontend, filters, sorting) was verified against seeded sample data — see
the screenshot workflow below if you want to reproduce that.

Home Depot also does not publish a stable "clearance" API, and retailers
generally make scraping harder over time (layout changes, bot detection).
So expect to need to:

1. Run this from a normal residential/cloud network Home Depot doesn't block.
2. Fix CSS selectors when Home Depot changes its page markup — everything
   scraping-related is centralized in `app/scraper/selectors.py`, which has
   step-by-step instructions in its docstring for finding the new selector
   with your browser's dev tools.
3. Watch `app/scraper/browser.py`'s ZIP-localization step, since clearance
   pricing is store-specific and Home Depot's "set your store" flow is a
   likely thing to break first.

None of this is unusual for a site like this — the reference project this
was modeled on (hd-clearance-bot) also relies on a browser fallback for the
same reason.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium   # downloads the browser Playwright drives

cp .env.example .env          # then edit ZIP codes etc. to taste
```

## Running it

**1. Populate some data.** Either run the real scraper:

```bash
python scripts/scrape_once.py
```

...or, to preview the site immediately without waiting on a scrape, seed a
few fake sample deals:

```bash
python scripts/seed_sample_data.py
```

**2. Start the website:**

```bash
uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000 — you'll see the deal grid, with search,
category/store/discount filters, and sorting.

**3. Keep it updated.** Pick one:

- Cron (simplest): `0 * * * * cd /path/to/hd-scraper && .venv/bin/python scripts/scrape_once.py`
  to rescan hourly.
- Or run the built-in scheduler as a long-lived process:
  `python scripts/schedule.py 60` (runs every 60 minutes, including once at startup).

Deals that stop showing up in a scan are marked inactive (not deleted) so
they drop off the site but stay in the database for history.

## Configuration (`.env`)

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | SQLite file, default `sqlite:///./deals.db` |
| `HD_ZIP_CODES` | Comma-separated ZIPs to check store-specific clearance pricing for |
| `MIN_DISCOUNT_PERCENT` | Drop anything discounted less than this (default 20%) |
| `REQUEST_DELAY_SECONDS` | Pause between page loads, be polite |
| `HEADLESS` | `false` to watch the browser while debugging a broken selector |

What gets scanned each run (search terms / category pages) lives in
`app/scraper/targets.py` — add or remove entries there.

## Project layout

```
app/
  main.py            FastAPI app: mounts the API + serves the frontend
  config.py           Settings loaded from .env
  db.py / models.py   SQLite via SQLAlchemy, one Deal table
  schemas.py           Pydantic response models
  api/deals.py          GET /api/deals, /api/deals/{id}, /api/meta
  scraper/
    targets.py            Which pages to scan
    browser.py             Playwright: loads a page, sets ZIP/store
    selectors.py            CSS selectors (fix here when scraping breaks)
    parser.py                 HTML -> deal dicts
    run.py                      Orchestrates targets x ZIPs -> DB upsert
  static/               index.html / styles.css / app.js (no build step)
scripts/
  scrape_once.py        Run one scan (for cron)
  schedule.py             Run scans on a repeating interval
  seed_sample_data.py      Insert fake deals for local UI preview
tests/
  test_parser.py         Unit test for HTML -> deal parsing (uses a fixture,
                          no network/browser needed)
```

## Notes on scope

This intentionally only covers Home Depot (no other retailers), matches
homedepot.com pricing/availability at scan time (not real-time), and is
built for personal/non-commercial use — be mindful of Home Depot's Terms
of Service and rate-limit yourself (`REQUEST_DELAY_SECONDS`, reasonable
scan frequency) rather than hammering their site.
