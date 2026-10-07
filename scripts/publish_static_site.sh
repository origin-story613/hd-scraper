#!/usr/bin/env bash
# Scrape Home Depot from THIS machine and push the result to the repo so
# the GitHub Pages site picks it up. Meant to run via cron from a
# residential network -- GitHub Actions' shared IPs are blocked by Home
# Depot's bot protection on every content page (confirmed via debug
# capture), so the scrape itself has to happen somewhere else. Pages
# hosting is unaffected; only where the scrape runs changes.
#
# Setup (one-time):
#   1. Clone this repo somewhere on the machine that will run the cron job:
#        git clone git@github.com:<you>/<repo>.git
#      (SSH, so cron can push without a password prompt -- set up a
#      deploy key or your normal SSH key with push access.)
#   2. cd into it, create the venv, install deps:
#        python3 -m venv .venv && source .venv/bin/activate
#        pip install -r requirements.txt
#        playwright install chromium
#   3. cp .env.example .env and set HD_ZIP_CODES etc. to taste.
#   4. Add a cron entry (crontab -e), e.g. every 3 hours:
#        0 */3 * * * /path/to/hd-scraper/scripts/publish_static_site.sh >> /path/to/hd-scraper/scrape.log 2>&1
#
# Safe to run manually too: ./scripts/publish_static_site.sh

set -euo pipefail
cd "$(dirname "$0")/.."

source .venv/bin/activate
python scripts/build_static_site.py

git fetch origin
git rebase origin/HEAD

if git diff --quiet -- docs/deals.json; then
  echo "No deal changes, skipping commit."
else
  git add docs/deals.json
  git commit -m "Update deals.json ($(date -u +'%Y-%m-%d %H:%M UTC'))"
  git push
fi
