"""
Search queries the scraper works through on every run.

Home Depot doesn't have one single "clearance" feed you can hit — clearance
and other markdowns are scattered across search results and are
store-specific. The practical approach (same one most HD deal-tracking
projects use) is to repeatedly search a handful of clearance-heavy terms
and keep whatever comes back with a real discount attached.

`query` is typed into Home Depot's own search box (see browser.py) rather
than a hand-built URL — a live debug capture confirmed Home Depot's own
frontend lands on /s/<query>?NCNI-5 for a plain search, but builds that URL
itself, so there's no guessing involved this way.

Add/remove entries here to change what gets scanned.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Target:
    name: str
    query: str
    category: str | None = None


TARGETS: list[Target] = [
    Target(name="Clearance search", query="clearance", category="Clearance"),
    Target(name="Special Buy of the Day", query="special buy", category="Special Buy"),
    Target(name="Appliances clearance", query="appliances clearance", category="Appliances"),
    Target(name="Tools clearance", query="tools clearance", category="Tools"),
    Target(name="Outdoor & patio clearance", query="patio clearance", category="Outdoor & Patio"),
]
