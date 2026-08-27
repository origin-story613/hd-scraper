# HD Deal Finder

An unofficial, personal-use website that shows Home Depot clearance and
markdown deals in a browsable grid (similar to rebelsavings.com/home-depot),
backed by a scraper that periodically checks homedepot.com.

There are two ways to run this — pick one:

- **GitHub Pages (free, recommended)** — a GitHub Actions workflow scrapes
  on a schedule and commits a static `docs/deals.json`; GitHub Pages serves
  the plain HTML/CSS/JS site in `docs/`, which filters/sorts everything in
  the browser. No server to pay for or maintain.
- **Self-hosted FastAPI app** — a small backend (`app/`) with a live
  `/api/deals` endpoint backed by SQLite. Needs a real server (VPS, Render,
  Railway, Fly.io, etc.) since GitHub Pages can't run it.

Both share the same scraper code (`app/scraper/`).

## Important: the scraper needs to run somewhere that can reach homedepot.com

This code was written in a sandboxed dev environment whose network policy
blocks outbound requests to homedepot.com entirely, so **the scraper itself
could not be tested against the live site**. Everything else — parsing
logic (unit-tested against a fixture), the static site, the FastAPI app —
was verified end-to-end with sample data.

GitHub Actions runners have normal internet access, so option 1 below
should work out of the box; if you self-host, just make sure wherever you
deploy isn't itself blocking outbound traffic to homedepot.com.

Home Depot also doesn't publish a stable "clearance" API and retailers
generally make scraping harder over time (layout changes, bot detection),
so expect to occasionally need to:

1. Fix CSS selectors when Home Depot changes its page markup — everything
   scraping-related is centralized in `app/scraper/selectors.py`, which has
   step-by-step instructions in its docstring for finding the new selector
   with your browser's dev tools.
2. Watch `app/scraper/browser.py`'s ZIP-localization step, since clearance
   pricing is store-specific and Home Depot's "set your store" flow is a
   likely thing to break first.

None of this is unusual for a site like this — the reference project this
was modeled on (hd-clearance-bot) also relies on a browser fallback for the
same reason.

---

## Option 1: GitHub Pages + GitHub Actions (free)

**1. Enable Pages.** In this repo: **Settings → Pages → Build and
deployment → Source: "Deploy from a branch"**, branch `main` (or whichever
is your default), folder **`/docs`**. Save. A `docs/deals.json` with a
few sample deals is already committed so the site has something to show
immediately.

**2. Make sure the workflow can push commits.** In **Settings → Actions →
General → Workflow permissions**, select **"Read and write permissions"**
(the workflow needs this to commit the refreshed `deals.json`).

**3. (Optional) Set your ZIP codes.** Clearance pricing is store-specific.
Either edit `HD_ZIP_CODES` directly in
`.github/workflows/scrape-and-deploy.yml`, or set it without touching the
file via **Settings → Secrets and variables → Actions → Variables → New
repository variable**: name `HD_ZIP_CODES`, value e.g. `10001,60601,90001`.
Same pattern for `MIN_DISCOUNT_PERCENT`.

**4. Run it.** The workflow runs automatically every 3 hours (edit the
`cron:` line in the workflow file to change that). To run it right now
instead of waiting: **Actions tab → "Scrape Home Depot deals and update
site" → Run workflow**.

**5. Visit the site.** GitHub shows the Pages URL under **Settings →
Pages** once it's deployed — typically
`https://<your-username>.github.io/<repo-name>/`.

That's it — no server, no database to manage. Each run does a full fresh
scan and overwrites `docs/deals.json`; there's no history kept between
runs in this mode (see Option 2 if you want that).

### Local preview of the static site

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium

python scripts/seed_static_sample.py   # fake data, instant
# or: python scripts/build_static_site.py   # real scrape, needs homedepot.com access

cd docs && python3 -m http.server 8000
```

Open http://localhost:8000.

---

## Option 2: Self-hosted FastAPI app

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
playwright install chromium

cp .env.example .env          # then edit ZIP codes etc. to taste
```

**1. Populate some data:**

```bash
python scripts/scrape_once.py          # real scrape
# or: python scripts/seed_sample_data.py   # fake data for an instant preview
```

**2. Start the website:**

```bash
uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000.

**3. Keep it updated** — pick one:

- Cron (simplest): `0 * * * * cd /path/to/hd-scraper && .venv/bin/python scripts/scrape_once.py`
- Or the built-in scheduler as a long-lived process: `python scripts/schedule.py 60`
  (runs every 60 minutes, including once at startup).

Deals that stop showing up in a scan are marked inactive (not deleted) so
they drop off the site but stay in the database for history — this mode
does keep history, unlike the static-site path.

### Configuration (`.env`)

| Variable | Purpose |
|---|---|
| `DATABASE_URL` | SQLite file, default `sqlite:///./deals.db` |
| `HD_ZIP_CODES` | Comma-separated ZIPs to check store-specific clearance pricing for |
| `MIN_DISCOUNT_PERCENT` | Drop anything discounted less than this (default 20%) |
| `REQUEST_DELAY_SECONDS` | Pause between page loads, be polite |
| `HEADLESS` | `false` to watch the browser while debugging a broken selector |

---

## What gets scanned

`app/scraper/targets.py` lists the search/category pages scanned on every
run — add or remove entries there. Both deployment modes share it.

## Project layout

```
app/
  scraper/
    targets.py            Which pages to scan
    browser.py             Playwright: loads a page, sets ZIP/store
    selectors.py             CSS selectors (fix here when scraping breaks)
    parser.py                  HTML -> deal dicts
    run.py                       collect_deals() + DB upsert for Option 2
  main.py / config.py / db.py / models.py / schemas.py / api/
                          FastAPI app (Option 2 only)
  static/                 FastAPI-served frontend (Option 2 only)
docs/
  index.html / styles.css / app.js   The GitHub Pages site (Option 1)
  deals.json                           Generated snapshot the site reads
.github/workflows/
  scrape-and-deploy.yml   Scheduled scraper -> docs/deals.json (Option 1)
scripts/
  build_static_site.py     Scrape -> docs/deals.json (used by the workflow)
  seed_static_sample.py      Fake docs/deals.json for local preview
  scrape_once.py             Run one scan into the DB (Option 2, cron)
  schedule.py                  Run scans on a repeating interval (Option 2)
  seed_sample_data.py            Fake DB data for local preview (Option 2)
tests/
  test_parser.py            Unit test for HTML -> deal parsing (fixture-based,
                             no network/browser needed)
```

## Notes on scope

This intentionally only covers Home Depot (no other retailers), matches
homedepot.com pricing/availability at scan time (not real-time), and is
built for personal/non-commercial use — be mindful of Home Depot's Terms
of Service and rate-limit yourself (`REQUEST_DELAY_SECONDS`, a reasonable
scan frequency) rather than hammering their site.
