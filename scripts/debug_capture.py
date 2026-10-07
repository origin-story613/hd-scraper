#!/usr/bin/env python3
"""Round 4: same as round 3 (real search box + ZIP modal), but with
playwright-stealth applied, to see if that's enough to get past the 403
"Error Page" block confirmed in round 3.

Usage: python scripts/debug_capture.py
"""

import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bs4 import BeautifulSoup  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402
from playwright_stealth import stealth_sync  # noqa: E402

from app.scraper.browser import USER_AGENT  # noqa: E402

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
        if re.search(r"product|price|pod|clearance|badge|brand", tid, re.I):
            testids[tid] += 1
    print(f"relevant data-testid values (up to 25): {testids.most_common(25)}")

    if product_links:
        a = product_links[0]
        parent = a.parent
        chain = []
        for _ in range(6):
            if parent is None:
                break
            chain.append(f"<{parent.name} class={parent.get('class')} data-testid={parent.get('data-testid')}>")
            parent = parent.parent
        print("  ancestor chain for first /p/ link: " + " > ".join(chain))
    print()


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent=USER_AGENT, viewport={"width": 1400, "height": 1000})
        page = context.new_page()
        stealth_sync(page)

        print("=== Loading homepage (stealth) ===")
        page.goto("https://www.homedepot.com/", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(2000)
        print(f"title: {page.title()!r}")

        print("=== Using the real on-page search box (stealth) ===")
        box = page.locator('[data-testid="typeahead-search-field-input"]').first
        box.click(timeout=10000)
        box.fill("clearance")
        page.wait_for_timeout(500)
        box.press("Enter")
        page.wait_for_timeout(4000)

        print(f"status after search: final url: {page.url}  title: {page.title()!r}")
        summarize_html("search-box-result-stealth", page.content())

        context.close()
        browser.close()


if __name__ == "__main__":
    main()
