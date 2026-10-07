#!/usr/bin/env python3
"""Round 3: use Home Depot's own search box (typeahead-search-field-input)
instead of guessing URLs directly -- round 2 showed /s/ and /b/ paths all
403 with a generic "Error Page" on cold navigation, which only showed up
on search/category paths (the homepage itself loads fine), consistent
with bot-mitigation on those routes rather than a URL format issue. Also
completes the ZIP modal flow to find the submit control.

Usage: python scripts/debug_capture.py
"""

import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bs4 import BeautifulSoup  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

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


def use_real_search_box(page):
    print("=== Using the real on-page search box ===")
    page.goto("https://www.homedepot.com/", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(3000)

    box = page.locator('[data-testid="typeahead-search-field-input"]').first
    if box.count() == 0:
        print("search box not found")
        return
    box.click(timeout=5000)
    box.fill("clearance")
    page.wait_for_timeout(1000)
    box.press("Enter")
    page.wait_for_timeout(5000)

    print(f"status after search: final url: {page.url}  title: {page.title()!r}")
    summarize_html("search-box-result", page.content())


def complete_zip_flow(page):
    print("=== Completing ZIP modal flow ===")
    page.goto("https://www.homedepot.com/", wait_until="domcontentloaded", timeout=30000)
    page.wait_for_timeout(3000)

    btn = page.locator('[data-testid="delivery-zip-button"]').first
    if btn.count() == 0:
        print("delivery-zip-button not found")
        return
    btn.click(timeout=5000)
    page.wait_for_timeout(1500)

    zip_input = page.get_by_placeholder("Enter ZIP Code").first
    if zip_input.count() == 0:
        print("zip input not found after opening modal")
        return
    zip_input.click(timeout=5000)
    zip_input.fill("10001")
    page.wait_for_timeout(1000)

    html = page.content()
    soup = BeautifulSoup(html, "html.parser")
    for el in soup.select("button"):
        text = (el.get_text(strip=True) or "")[:30]
        tid = el.get("data-testid", "")
        if text or tid:
            print(f"  button after typing zip: data-testid={tid!r} text={text!r}")
    print()


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent=USER_AGENT, viewport={"width": 1400, "height": 1000})
        page = context.new_page()

        use_real_search_box(page)
        complete_zip_flow(page)

        context.close()
        browser.close()


if __name__ == "__main__":
    main()
