"""Playwright wrapper: loads a Home Depot page for a given ZIP and returns
the rendered HTML for the parser to work on.

Two things make this trickier than a plain HTTP fetch:

1. Home Depot's search/category pages render their product grid with
   client-side JS, so we need a real (headless) browser, not just
   requests/httpx.
2. Clearance pricing is set per store, and Home Depot infers "your store"
   from a ZIP code you set once per browser session (cookie/localStorage).
   `set_store_by_zip` below does a best-effort UI interaction to set it;
   if Home Depot changes that flow, deals will still come back but may
   reflect the wrong local store — see the module docstring in
   selectors.py for how to fix a broken selector.
"""

import logging
import time

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from app.config import settings

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

# Best-effort selectors for the "set your store" ZIP entry flow. Tried in
# order; if none match, we just skip localization and scrape with whatever
# store Home Depot defaults to.
ZIP_INPUT_SELECTORS = [
    '[data-testid="localizer-zip-input"]',
    "input[placeholder*='Zip' i]",
    "input[aria-label*='zip' i]",
]
ZIP_SUBMIT_SELECTORS = [
    '[data-testid="localizer-submit"]',
    "button[aria-label*='Update' i]",
    "button[type='submit']",
]


def set_store_by_zip(page, zip_code: str) -> bool:
    for input_sel in ZIP_INPUT_SELECTORS:
        try:
            field = page.locator(input_sel).first
            if field.count() == 0:
                continue
            field.click(timeout=3000)
            field.fill(zip_code, timeout=3000)
            for submit_sel in ZIP_SUBMIT_SELECTORS:
                submit = page.locator(submit_sel).first
                if submit.count() > 0:
                    submit.click(timeout=3000)
                    page.wait_for_timeout(1500)
                    return True
            field.press("Enter")
            page.wait_for_timeout(1500)
            return True
        except PlaywrightTimeoutError:
            continue
    logger.warning("Could not find a ZIP entry field to localize the store; scraping default location.")
    return False


def fetch_rendered_html(url: str, *, zip_code: str | None = None, headless: bool | None = None) -> str:
    headless = settings.headless if headless is None else headless

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(user_agent=USER_AGENT, viewport={"width": 1400, "height": 1000})
        page = context.new_page()

        try:
            page.goto("https://www.homedepot.com/", wait_until="domcontentloaded", timeout=30000)
            if zip_code:
                set_store_by_zip(page, zip_code)

            page.goto(url, wait_until="domcontentloaded", timeout=30000)
            try:
                page.wait_for_selector("[data-testid='product-pod'], div.product-pod", timeout=15000)
            except PlaywrightTimeoutError:
                logger.warning("Product grid selector never appeared for %s; parsing whatever loaded.", url)

            html = page.content()
        finally:
            context.close()
            browser.close()

    time.sleep(settings.request_delay_seconds)
    return html
