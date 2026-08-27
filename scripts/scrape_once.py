#!/usr/bin/env python3
"""Run a single scrape pass and print a summary. Meant for manual runs and cron."""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings  # noqa: E402
from app.scraper.run import run_scan  # noqa: E402

if __name__ == "__main__":
    logging.basicConfig(level=settings.log_level, format="%(asctime)s %(levelname)s %(message)s")
    result = run_scan()
    print(f"Deals found/updated: {result['deals_found']}")
    print(f"Deals marked stale: {result['marked_stale']}")
