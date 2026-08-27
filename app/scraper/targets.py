"""
Search targets the scraper works through on every run.

Home Depot doesn't have one single "clearance" feed you can hit — clearance
and other markdowns are scattered across search/category results and are
store-specific. The practical approach (same one most HD deal-tracking
projects use) is to repeatedly search/browse a handful of clearance-heavy
entry points and keep whatever comes back with a real discount attached.

Add/remove entries here to change what gets scanned. `url` can be either a
search results URL or a category browse URL — the parser doesn't care which,
it just looks for product tiles on the page.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class Target:
    name: str
    url: str
    category: str | None = None


TARGETS: list[Target] = [
    Target(
        name="Clearance search",
        url="https://www.homedepot.com/s/clearance?NCNI-5",
        category="Clearance",
    ),
    Target(
        name="Special Buy of the Day",
        url="https://www.homedepot.com/s/special%2520buy?NCNI-5",
        category="Special Buy",
    ),
    Target(
        name="Appliances clearance",
        url="https://www.homedepot.com/s/appliances%2520clearance?NCNI-5",
        category="Appliances",
    ),
    Target(
        name="Tools clearance",
        url="https://www.homedepot.com/s/tools%2520clearance?NCNI-5",
        category="Tools",
    ),
    Target(
        name="Outdoor & patio clearance",
        url="https://www.homedepot.com/s/patio%2520clearance?NCNI-5",
        category="Outdoor & Patio",
    ),
]
