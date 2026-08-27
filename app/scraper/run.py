"""Scan every configured target/ZIP combination and upsert results into the DB."""

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
    init_db()
    db = SessionLocal()
    seen_ids: set[str] = set()
    total_found = 0

    try:
        for zip_code in settings.zip_code_list:
            for target in TARGETS:
                logger.info("Scanning %s for ZIP %s", target.name, zip_code)
                try:
                    html = fetch_rendered_html(target.url, zip_code=zip_code)
                except Exception:
                    logger.exception("Failed to load %s for ZIP %s", target.url, zip_code)
                    continue

                deals = parse_search_page(
                    html, category=target.category, store_id=None, zip_code=zip_code
                )
                deals = [d for d in deals if (d["discount_percent"] or 0) >= settings.min_discount_percent]

                upsert_deals(db, deals)
                seen_ids.update(d["id"] for d in deals)
                total_found += len(deals)
                db.commit()

        stale_count = mark_stale_inactive(db, seen_ids)
        db.commit()
    finally:
        db.close()

    logger.info("Scan complete: %s deals kept, %s marked stale", total_found, stale_count)
    return {"deals_found": total_found, "marked_stale": stale_count}


if __name__ == "__main__":
    logging.basicConfig(level=settings.log_level)
    run_scan()
