"""
CSS selectors used to parse Home Depot search/category result pages.

Retailer markup changes over time (and Home Depot varies its DOM on
purpose to make scraping harder), so this is the one place to fix things
when the scraper starts coming back empty:

  1. Run a scrape with HEADLESS=false so you can watch the page load.
  2. Open the same URL in a normal browser, right-click a product tile,
     "Inspect", and find the current container/attribute names.
  3. Add the new selector to the *front* of the relevant list below rather
     than replacing what's there — old and new layouts both keep working.

Each list is tried in order; the first selector that matches anything
inside a product tile wins.
"""

PRODUCT_TILE = [
    '[data-testid="product-pod"]',
    "div.product-pod",
    "div[class*='podTemplate']",
    "div[class*='product-pod']",
]

TITLE = [
    '[data-testid="product-header"]',
    "a.product-pod__title",
    "span[class*='product-title']",
    "h3",
]

LINK = [
    'a[data-testid="product-pod-title-link"]',
    "a.product-pod__link",
    "a[href*='/p/']",
]

IMAGE = [
    'img[data-testid="product-image"]',
    "img.product-pod__image",
    "img",
]

PRICE_NOW = [
    '[data-testid="price-format__main-price"]',
    "div[class*='price-format__main-price']",
    "span.price-format__main-price",
    "*[class*='price'] *[class*='dollars']",
]

PRICE_WAS = [
    '[data-testid="price-was"]',
    "span.price-format__was-price",
    "span[class*='was-price']",
    "s, del",
]

BADGE = [
    '[data-testid="badge"]',
    "span[class*='badge']",
]

BRAND = [
    '[data-testid="attribute-brandname-above"]',
    "div[class*='brand']",
]

OUT_OF_STOCK_TEXT = ["out of stock", "currently unavailable", "sold out"]
