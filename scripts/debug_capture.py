#!/usr/bin/env python3
"""One-off diagnostic: load homedepot.com + a search page and print
structural signals (title, bot-block indicators, candidate product-tile
selectors, candidate ZIP-input selectors) to stdout.

This exists because the dev environment this scraper was built in cannot
reach homedepot.com at all, so there was never a way to see the real page
structure directly -- only live GitHub Actions runners can. Output goes
to the job log (read via the Actions API) rather than an uploaded
artifact, since artifact downloads redirect to Azure Blob Storage, which
is also unreachable from that dev environment.

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

PAGES = {
    "home": "https://www.homedepot.com/",
    "clearance_search": "https://www.homedepot.com/s/clearance?NCNI-5",
}

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

    # Product links: HD product URLs look like /p/<slug>/<numeric-id>
    product_links = soup.select("a[href*='/p/']")
    print(f"<a href*='/p/'> count: {len(product_links)}")
    if product_links:
        a = product_links[0]
        print(f"  sample href: {a.get('href')}")
        print(f"  sample classes: {a.get('class')}")
        parent = a.parent
        chain = []
        for _ in range(4):
            if parent is None:
                break
            chain.append(f"<{parent.name} class={parent.get('class')} data-testid={parent.get('data-testid')}>")
            parent = parent.parent
        print("  ancestor chain (closest first): " + " > ".join(chain))

    # Any data-testid attributes mentioning product/price/pod
    testids = Counter()
    for el in soup.select("[data-testid]"):
        tid = el.get("data-testid", "")
        if re.search(r"product|price|pod|clearance|badge|brand", tid, re.I):
            testids[tid] += 1
    print(f"relevant data-testid values (up to 20): {testids.most_common(20)}")

    # Candidate ZIP/store localizer inputs
    for inp in soup.select("input"):
        attrs = " ".join(f'{k}="{v}"' for k, v in inp.attrs.items() if k in ("type", "placeholder", "aria-label", "name", "data-testid", "id"))
        if re.search(r"zip|location|store", attrs, re.I):
            print(f"  candidate zip/location input: <input {attrs}>")

    # Candidate store/localizer buttons or triggers
    for el in soup.select("[data-testid], button, a"):
        text = (el.get_text(strip=True) or "")[:40]
        tid = el.get("data-testid", "")
        if re.search(r"store|location|zip", f"{tid} {text}", re.I) and len(text) < 40:
            print(f"  candidate localizer element: <{el.name} data-testid={tid!r}> text={text!r}")

    print()


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent=USER_AGENT, viewport={"width": 1400, "height": 1000})
        page = context.new_page()

        for name, url in PAGES.items():
            print(f"=== Loading {name}: {url} ===")
            try:
                resp = page.goto(url, wait_until="domcontentloaded", timeout=30000)
                page.wait_for_timeout(5000)
                print(f"status: {resp.status if resp else 'n/a'}  final url: {page.url}  title: {page.title()!r}")
                summarize_html(name, page.content())
            except Exception as e:
                print(f"FAILED: {e}")

        context.close()
        browser.close()


if __name__ == "__main__":
    main()
