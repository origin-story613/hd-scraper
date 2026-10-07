#!/usr/bin/env python3
"""Round 6: test two category/browse URLs the user found by browsing
homedepot.com directly (not guessed), to see if they dodge the
bot-mitigation confirmed on /s/ search pages.

Usage: python scripts/debug_capture.py
"""

import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bs4 import BeautifulSoup  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

from app.scraper.browser import USER_AGENT, _STEALTH_INIT_SCRIPT  # noqa: E402

CANDIDATE_URLS = [
    "https://www.homedepot.com/b/Special-Values/N-5yc1vZ7",
    "https://www.homedepot.com/c/Savings_Center?NCNI-5",
]

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
        browser = p.chromium.launch(headless=True, args=["--disable-blink-features=AutomationControlled"])
        context = browser.new_context(user_agent=USER_AGENT, viewport={"width": 1400, "height": 1000})
        context.add_init_script(_STEALTH_INIT_SCRIPT)
        page = context.new_page()

        page.goto("https://www.homedepot.com/", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(2000)
        print(f"homepage title: {page.title()!r}")

        for url in CANDIDATE_URLS:
            print(f"=== Trying: {url} ===")
            try:
                resp = page.goto(url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(4000)
                print(f"status: {resp.status if resp else 'n/a'}  final url: {page.url}  title: {page.title()!r}")
                summarize_html(url, page.content())
            except Exception as e:
                print(f"FAILED: {e}\n")

        context.close()
        browser.close()


if __name__ == "__main__":
    main()
