#!/usr/bin/env python3
"""One-off diagnostic: load homedepot.com + one search page, dump the
rendered HTML and a screenshot so we can see what Home Depot's real DOM
looks like (this can only be run somewhere with access to homedepot.com,
e.g. via the debug-capture GitHub Actions workflow).

Usage: python scripts/debug_capture.py
Writes to debug_capture/ in the repo root (gitignored).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from playwright.sync_api import sync_playwright  # noqa: E402

from app.scraper.browser import USER_AGENT  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "debug_capture"
OUT.mkdir(exist_ok=True)

PAGES = {
    "home": "https://www.homedepot.com/",
    "clearance_search": "https://www.homedepot.com/s/clearance?NCNI-5",
}


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent=USER_AGENT, viewport={"width": 1400, "height": 1000})
        page = context.new_page()

        for name, url in PAGES.items():
            print(f"Loading {name}: {url}")
            try:
                resp = page.goto(url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(5000)  # let JS render
                print(f"  status: {resp.status if resp else 'n/a'}  title: {page.title()!r}")
                (OUT / f"{name}.html").write_text(page.content())
                page.screenshot(path=str(OUT / f"{name}.png"), full_page=True)
            except Exception as e:
                print(f"  FAILED: {e}")

        context.close()
        browser.close()

    print(f"Wrote captures to {OUT}")


if __name__ == "__main__":
    main()
