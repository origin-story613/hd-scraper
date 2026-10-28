#!/usr/bin/env python3
"""Round 8: the key isolating test. The user manually browsing to
/c/Savings_Center?NCNI-5 on this same residential IP/machine sees real
products with lazy-loaded infinite scroll. Round 6 (GitHub Actions,
datacenter IP) got the generic "Oops" error page on that exact URL.
This tests the same URL, direct navigation (no search box), from the
residential IP with our stealth patches -- isolates whether the block is
IP-reputation (should work now) or automation/CDP detection (would still
fail even from a "good" IP).

Usage (from the repo root, venv activated):
    python scripts/debug_capture.py
"""

import re
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bs4 import BeautifulSoup  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

from app.scraper.browser import USER_AGENT, _STEALTH_INIT_SCRIPT  # noqa: E402

URL = "https://www.homedepot.com/c/Savings_Center?NCNI-5"

BLOCK_PHRASES = [
    "pardon our interruption", "access denied", "are you a robot",
    "press and hold", "verify you are a human", "captcha",
    "unusual traffic", "blocked", "oops",
]


def summarize_html(label: str, html: str):
    print(f"--- {label}: {len(html)} chars ---")
    soup = BeautifulSoup(html, "html.parser")
    lower = html.lower()
    hits = [p for p in BLOCK_PHRASES if p in lower]
    print(f"bot-block / error phrases found: {hits or 'none'}")

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

        tile = a
        for _ in range(3):
            if tile.parent is not None:
                tile = tile.parent
        snippet = str(tile)[:3000]
        print(f"\n  --- raw HTML snippet (3 ancestors up from first /p/ link, truncated to 3000 chars) ---\n{snippet}\n")
    else:
        body = soup.find("body")
        print("  No /p/ product links found -- first 2000 chars of <body>:")
        print(str(body)[:2000] if body else "(no <body> found)")
    print()


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        context = browser.new_context(user_agent=USER_AGENT, viewport={"width": 1400, "height": 1000})
        context.add_init_script(_STEALTH_INIT_SCRIPT)
        page = context.new_page()

        print("=== Loading homepage first (establish session like a real visit) ===")
        page.goto("https://www.homedepot.com/", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(2000)
        print(f"title: {page.title()!r}")

        print(f"\n=== Navigating directly to {URL} ===")
        resp = page.goto(URL, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(3000)
        print(f"status: {resp.status if resp else 'n/a'}  final url: {page.url}  title: {page.title()!r}")

        # Scroll a bit in case content lazy-loads, like the user observed manually.
        for _ in range(3):
            page.mouse.wheel(0, 2000)
            page.wait_for_timeout(1500)

        summarize_html("savings-center-direct", page.content())

        context.close()
        browser.close()


if __name__ == "__main__":
    main()
