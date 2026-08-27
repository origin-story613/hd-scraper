"""Scan every configured target/ZIP combination for deals.

`collect_deals()` is the shared core: it just returns a flat list of deal
dicts and has no opinion about where they end up. Two things build on it:

- `run_scan()` upserts them into the SQLite DB (used by the self-hosted
  FastAPI app / scripts/scrape_once.py).
- `scripts/build_static_site.py` writes them straight to a static
  deals.json for the GitHub Pages deployment — no DB involved there, since
  every GitHub Actions run starts fresh and does a full scan anyway.
"""

import datetime
import logging

from sqlalchemy.orm import Session

from app.config import settings
from app.db import SessionLocal, init_db
from app.models import Deal
from app.scraper.browser import fetch_rendered_html
from app.scraper.parser import parse_search_page
from app.scraper.targets import TARGETS

logger = logging.getLogger(__name__)


def collect_deals(zip_codes: list[str] | None = None, min_discount_percent: float | None = None) -> list[dict]:
    """Scan every target for every ZIP and return deduped deal dicts."""
    zip_codes = zip_codes if zip_codes is not None else settings.zip_code_list
    min_discount = settings.min_discount_percent if min_discount_percent is None else min_discount_percent

    by_id: dict[str, dict] = {}
    for zip_code in zip_codes:
        for target in TARGETS:
            logger.info("Scanning %s for ZIP %s", target.name, zip_code)
            try:
                html = fetch_rendered_html(target.url, zip_code=zip_code)
            except Exception:
                logger.exception("Failed to load %s for ZIP %s", target.url, zip_code)
                continue

            deals = parse_search_page(html, category=target.category, store_id=None, zip_code=zip_code)
            deals = [d for d in deals if (d["discount_percent"] or 0) >= min_discount]

            for d in deals:
                by_id[d["id"]] = d  # last store/ZIP scanned for a given item wins

    return list(by_id.values())


def upsert_deals(db: Session, deals: list[dict]) -> int:
    now = datetime.datetime.utcnow()
    count = 0
    for d in deals:
        existing = db.get(Deal, d["id"])
        if existing:
            for key, value in d.items():
                setattr(existing, key, value)
            existing.last_seen = now
            existing.is_active = True
        else:
            db.add(Deal(**d, first_seen=now, last_seen=now, is_active=True))
        count += 1
    return count


def mark_stale_inactive(db: Session, seen_ids: set[str], cutoff_hours: int = 48) -> int:
    """Deals not seen in the most recent full scan get flagged inactive
    (rather than deleted) so history/analytics stay intact."""
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(hours=cutoff_hours)
    query = db.query(Deal).filter(Deal.is_active.is_(True), Deal.last_seen < cutoff)
    if seen_ids:
        query = query.filter(~Deal.id.in_(seen_ids))
    stale = query.all()
    for deal in stale:
        deal.is_active = False
    return len(stale)


def run_scan() -> dict:
    """Scan and upsert into the SQLite DB (self-hosted FastAPI app path)."""
    init_db()
    deals = collect_deals()

    db = SessionLocal()
    try:
        upsert_deals(db, deals)
        db.commit()
        stale_count = mark_stale_inactive(db, {d["id"] for d in deals})
        db.commit()
    finally:
        db.close()

    logger.info("Scan complete: %s deals kept, %s marked stale", len(deals), stale_count)
    return {"deals_found": len(deals), "marked_stale": stale_count}


if __name__ == "__main__":
    logging.basicConfig(level=settings.log_level)
    run_scan()
