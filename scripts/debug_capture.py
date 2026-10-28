#!/usr/bin/env python3
"""Round 7: run locally (on a residential IP, unlike the GitHub Actions
rounds 1-6) to see the REAL page structure now that the IP-reputation
block looks to be out of the way. Prints the same diagnostics as before,
plus a larger raw HTML snippet around the first product link so we can
write real selectors instead of guesses.

Usage (from the repo root, venv activated):
    python scripts/debug_capture.py
"""

import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bs4 import BeautifulSoup  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

from app.scraper.browser import USER_AGENT, _STEALTH_INIT_SCRIPT  # noqa: E402

BLOCK_PHRASES = [
    "pardon our interruption", "access denied", "are you a robot",
    "press and hold", "verify you are a human", "captcha",
    "unusual traffic", "blocked",
]


def summarize_html(label: str, html: str):
    print(f"--- {label}: {len(html)} chars ---")
    soup = BeautifulSoup(html, "html.parser")
    lower = html.lower()
    hits = [p for p in BLOCK_PHRASES if p in lower]
    print(f"bot-block phrases found: {hits or 'none'}")

    product_links = soup.select("a[href*='/p/']")
    print(f"<a href*='/p/'> count: {len(product_links)}")

    testids = Counter()
    for el in soup.select("[data-testid]"):
        tid = el.get("data-testid", "")
        if re.search(r"product|price|pod|clearance|badge|brand|result", tid, re.I):
            testids[tid] += 1
    print(f"relevant data-testid values (up to 30): {testids.most_common(30)}")

    if product_links:
        a = product_links[0]
        parent = a.parent
        chain = []
        for _ in range(8):
            if parent is None:
                break
            chain.append(f"<{parent.name} class={parent.get('class')} data-testid={parent.get('data-testid')}>")
            parent = parent.parent
        print("  ancestor chain for first /p/ link: " + " > ".join(chain))

        # Print the raw HTML of the tile 3 levels up from the link -- this
        # is the real meat we need to design selectors from.
        tile = a
        for _ in range(3):
            if tile.parent is not None:
                tile = tile.parent
        snippet = str(tile)[:3000]
        print(f"\n  --- raw HTML snippet (3 ancestors up from first /p/ link, truncated to 3000 chars) ---\n{snippet}\n")
    else:
        print("  No /p/ product links found at all -- dumping first 3000 chars of <body> for inspection:")
        body = soup.find("body")
        print(str(body)[:3000] if body else "(no <body> found)")
    print()


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        context = browser.new_context(user_agent=USER_AGENT, viewport={"width": 1400, "height": 1000})
        context.add_init_script(_STEALTH_INIT_SCRIPT)
        page = context.new_page()

        print("=== Loading homepage ===")
        page.goto("https://www.homedepot.com/", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(2000)
        print(f"title: {page.title()!r}")

        print("=== Opening ZIP localizer modal ===")
        btn = page.locator('[data-testid="delivery-zip-button"]').first
        print(f"delivery-zip-button found: {btn.count() > 0}")
        if btn.count() > 0:
            btn.click(timeout=5000)
            page.wait_for_timeout(1500)
            zip_input = page.get_by_placeholder("Enter ZIP Code").first
            print(f"zip input found after click: {zip_input.count() > 0}")
            if zip_input.count() > 0:
                zip_input.click(timeout=5000)
                zip_input.fill("44118")
                page.wait_for_timeout(800)
                submit = page.get_by_text("Update Delivery ZIP Code", exact=False).first
                print(f"submit button found: {submit.count() > 0}")
                if submit.count() > 0:
                    submit.click(timeout=5000)
                    page.wait_for_timeout(2000)
                    print("Clicked submit.")

        print("\n=== Using the real on-page search box ===")
        box = page.locator('[data-testid="typeahead-search-field-input"]').first
        box.click(timeout=10000)
        box.fill("clearance")
        page.wait_for_timeout(500)
        box.press("Enter")
        page.wait_for_timeout(5000)

        print(f"status after search: final url: {page.url}  title: {page.title()!r}")
        summarize_html("search-box-result", page.content())

        context.close()
        browser.close()


if __name__ == "__main__":
    main()
