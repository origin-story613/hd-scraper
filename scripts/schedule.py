#!/usr/bin/env python3
"""Run the scraper on a recurring interval (default: every 60 minutes).

Usage: python scripts/schedule.py [interval_minutes]

Alternative: skip this script entirely and use a system cron job that runs
`python scripts/scrape_once.py` on whatever schedule you prefer — that's
simpler for a small deployment. This script is here for cases where cron
isn't convenient (e.g. a single long-running container).
"""

import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from apscheduler.schedulers.blocking import BlockingScheduler  # noqa: E402

from app.config import settings  # noqa: E402
from app.scraper.run import run_scan  # noqa: E402

logger = logging.getLogger(__name__)


def job():
    logger.info("Starting scheduled scrape")
    try:
        result = run_scan()
        logger.info("Scheduled scrape done: %s", result)
    except Exception:
        logger.exception("Scheduled scrape failed")


if __name__ == "__main__":
    logging.basicConfig(level=settings.log_level, format="%(asctime)s %(levelname)s %(message)s")
    interval = int(sys.argv[1]) if len(sys.argv) > 1 else 60

    scheduler = BlockingScheduler()
    scheduler.add_job(job, "interval", minutes=interval, next_run_time=None)
    job()  # run once immediately on startup
    scheduler.start()
