#!/usr/bin/env python3
"""Scan Home Depot and write docs/deals.json for the GitHub Pages site.

This is what the scheduled GitHub Actions workflow runs. Unlike the
self-hosted FastAPI path, there's no persistent DB here — every run does a
full scan and writes a fresh snapshot, since each GitHub Actions run starts
from a clean checkout anyway.

Usage: python scripts/build_static_site.py
"""

import datetime
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings  # noqa: E402
from app.scraper.run import collect_deals  # noqa: E402

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "docs" / "deals.json"

FIELDS = [
    "id", "item_id", "sku", "title", "brand", "category", "image_url",
    "product_url", "current_price", "original_price", "discount_percent",
    "discount_amount", "badge", "store_id", "store_name", "zip_code", "in_stock",
]


def main():
    logging.basicConfig(level=settings.log_level, format="%(asctime)s %(levelname)s %(message)s")
    deals = collect_deals()

    payload = {
        "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
        "count": len(deals),
        "deals": [{k: d.get(k) for k in FIELDS} for d in deals],
    }

    OUTPUT_PATH.write_text(json.dumps(payload, indent=2))
    print(f"Wrote {len(deals)} deals to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
