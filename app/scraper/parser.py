"""Turn raw HTML from a Home Depot search/category page into deal dicts."""

import hashlib
import re

from bs4 import BeautifulSoup, Tag

from app.scraper import selectors

PRICE_RE = re.compile(r"[\d,]+\.\d{2}|[\d,]+")


def _first(scope: Tag, selector_list: list[str]) -> Tag | None:
    for sel in selector_list:
        found = scope.select_one(sel)
        if found is not None:
            return found
    return None


def _parse_price(text: str | None) -> float | None:
    if not text:
        return None
    match = PRICE_RE.search(text.replace(",", ""))
    if not match:
        return None
    try:
        return float(match.group())
    except ValueError:
        return None


def _item_id_from_url(url: str) -> str | None:
    match = re.search(r"/p/(?:.*?/)?(\d+)", url)
    return match.group(1) if match else None


def make_deal_id(item_id: str, store_id: str | None) -> str:
    raw = f"{item_id}:{store_id or 'online'}"
    return hashlib.sha1(raw.encode()).hexdigest()[:20]


def parse_search_page(html: str, *, category: str | None, store_id: str | None, zip_code: str | None) -> list[dict]:
    """Extract deal dicts from one rendered search/category page's HTML.

    Only items with a real, present discount (a "was" price higher than the
    current price) are returned — this scraper is about deals, not full
    catalog scraping.
    """
    soup = BeautifulSoup(html, "html.parser")
    tiles: list[Tag] = []
    for sel in selectors.PRODUCT_TILE:
        tiles = soup.select(sel)
        if tiles:
            break

    deals = []
    for tile in tiles:
        deal = _parse_tile(tile, category=category, store_id=store_id, zip_code=zip_code)
        if deal is not None:
            deals.append(deal)
    return deals


def _parse_tile(tile: Tag, *, category: str | None, store_id: str | None, zip_code: str | None) -> dict | None:
    link_el = _first(tile, selectors.LINK)
    href = link_el.get("href") if link_el else None
    if not href:
        return None
    if href.startswith("/"):
        href = f"https://www.homedepot.com{href}"

    item_id = _item_id_from_url(href)
    if not item_id:
        return None

    title_el = _first(tile, selectors.TITLE)
    title = title_el.get_text(strip=True) if title_el else None
    if not title:
        return None

    price_now = _parse_price(_first(tile, selectors.PRICE_NOW).get_text(strip=True) if _first(tile, selectors.PRICE_NOW) else None)
    price_was = _parse_price(_first(tile, selectors.PRICE_WAS).get_text(strip=True) if _first(tile, selectors.PRICE_WAS) else None)
    if price_now is None:
        return None

    # Only keep it if there's an actual discount to show.
    if price_was is None or price_was <= price_now:
        return None

    discount_amount = round(price_was - price_now, 2)
    discount_percent = round((discount_amount / price_was) * 100, 1)

    image_el = _first(tile, selectors.IMAGE)
    image_url = image_el.get("src") or image_el.get("data-src") if image_el else None

    badge_el = _first(tile, selectors.BADGE)
    badge = badge_el.get_text(strip=True) if badge_el else None

    brand_el = _first(tile, selectors.BRAND)
    brand = brand_el.get_text(strip=True) if brand_el else None

    tile_text = tile.get_text(" ", strip=True).lower()
    in_stock = not any(phrase in tile_text for phrase in selectors.OUT_OF_STOCK_TEXT)

    return {
        "id": make_deal_id(item_id, store_id),
        "item_id": item_id,
        "sku": None,
        "title": title,
        "brand": brand,
        "category": category,
        "image_url": image_url,
        "product_url": href,
        "current_price": price_now,
        "original_price": price_was,
        "discount_percent": discount_percent,
        "discount_amount": discount_amount,
        "badge": badge,
        "store_id": store_id,
        "store_name": None,
        "zip_code": zip_code,
        "in_stock": in_stock,
    }
