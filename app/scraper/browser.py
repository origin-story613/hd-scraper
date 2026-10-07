"""Playwright wrapper: loads a Home Depot page for a given ZIP and returns
the rendered HTML for the parser to work on.

Three things make this trickier than a plain HTTP fetch:

1. Home Depot's search/category pages render their product grid with
   client-side JS, so we need a real (headless) browser, not just
   requests/httpx.
2. Clearance pricing is set per store, and Home Depot infers "your store"
   from a ZIP code you set once per browser session. `set_store_by_zip`
   below drives the real "delivery ZIP" modal (button -> type -> submit);
   if Home Depot changes that flow, fix the selectors here (see
   selectors.py's docstring for how to find the new ones).
3. Home Depot's search/category pages are behind bot-mitigation (confirmed
   via a live debug capture: even organically clicking the on-page search
   box and pressing Enter -- not a guessed URL -- got a 403 "Error Page"
   from plain headless Chromium, while the static homepage loaded fine).
   `playwright-stealth` patches the common headless-detection fingerprints
   (navigator.webdriver, missing Chrome runtime object, etc.). This may
   not be enough on its own against a determined WAF -- if deals.json
   stays empty after this, that's the next thing to dig into (see
   README's troubleshooting note).
"""

import logging
import time

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync

from app.config import settings

logger = logging.getLogger(__name__)

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

SEARCH_BOX_SELECTOR = '[data-testid="typeahead-search-field-input"]'
ZIP_BUTTON_SELECTOR = '[data-testid="delivery-zip-button"]'
ZIP_INPUT_PLACEHOLDER = "Enter ZIP Code"
ZIP_SUBMIT_TEXT = "Update Delivery ZIP Code"


def set_store_by_zip(page, zip_code: str) -> bool:
    try:
        btn = page.locator(ZIP_BUTTON_SELECTOR).first
        if btn.count() == 0:
            logger.warning("delivery-zip-button not found; scraping default location.")
            return False
        btn.click(timeout=5000)
        page.wait_for_timeout(1000)

        zip_input = page.get_by_placeholder(ZIP_INPUT_PLACEHOLDER).first
        if zip_input.count() == 0:
            logger.warning("ZIP input not found after opening localizer modal; scraping default location.")
            return False
        zip_input.click(timeout=5000)
        zip_input.fill(zip_code)
        page.wait_for_timeout(500)

        submit = page.get_by_text(ZIP_SUBMIT_TEXT, exact=False).first
        if submit.count() > 0:
            submit.click(timeout=5000)
        else:
            zip_input.press("Enter")
        page.wait_for_timeout(1500)
        return True
    except PlaywrightTimeoutError:
        logger.warning("Timed out localizing store for ZIP %s; scraping default location.", zip_code)
        return False


def search_and_fetch_html(query: str, *, zip_code: str | None = None, headless: bool | None = None) -> str:
    """Drive Home Depot's own on-page search box rather than guessing a
    search URL directly -- confirmed via debug capture to be what Home
    Depot's own frontend does, and marginally less bot-like than a cold
    deep-link navigation."""
    headless = settings.headless if headless is None else headless

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(user_agent=USER_AGENT, viewport={"width": 1400, "height": 1000})
        page = context.new_page()
        stealth_sync(page)

        try:
            page.goto("https://www.homedepot.com/", wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(1500)

            if zip_code:
                set_store_by_zip(page, zip_code)

            box = page.locator(SEARCH_BOX_SELECTOR).first
            box.click(timeout=10000)
            box.fill(query)
            page.wait_for_timeout(500)
            box.press("Enter")
            page.wait_for_timeout(3000)

            try:
                page.wait_for_selector("[data-testid='product-pod'], div.product-pod", timeout=15000)
            except PlaywrightTimeoutError:
                logger.warning("Product grid selector never appeared for query %r; parsing whatever loaded.", query)

            html = page.content()
        finally:
            context.close()
            browser.close()

    time.sleep(settings.request_delay_seconds)
    return html


def fetch_rendered_html(url: str, *, zip_code: str | None = None, headless: bool | None = None) -> str:
    """Direct URL fetch, kept for cases that aren't a search query (e.g. a
    category browse page). Prefer search_and_fetch_html when possible."""
    headless = settings.headless if headless is None else headless

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(user_agent=USER_AGENT, viewport={"width": 1400, "height": 1000})
        page = context.new_page()
        stealth_sync(page)

        try:
            page.goto("https://www.homedepot.com/", wait_until="domcontentloaded", timeout=30000)
            page.wait_for_timeout(1500)
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
