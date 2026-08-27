import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.scraper.parser import parse_search_page  # noqa: E402

FIXTURE = Path(__file__).parent / "fixtures" / "sample_search_page.html"


def test_parse_search_page_keeps_only_discounted_in_stock_items():
    html = FIXTURE.read_text()
    deals = parse_search_page(html, category="Tools", store_id=None, zip_code="10001")

    # The full-price widget (no "was" price) and the sold-out item's
    # discount is still real, so it should show but flagged out of stock.
    assert len(deals) == 2

    drill = next(d for d in deals if d["item_id"] == "312345678")
    assert drill["title"] == "20V MAX Cordless Drill/Driver Kit"
    assert drill["brand"] == "RYOBI"
    assert drill["current_price"] == 49.0
    assert drill["original_price"] == 99.0
    assert drill["discount_percent"] == 50.5
    assert drill["in_stock"] is True
    assert drill["category"] == "Tools"
    assert drill["zip_code"] == "10001"

    sold_out = next(d for d in deals if d["item_id"] == "555555")
    assert sold_out["in_stock"] is False

    assert all(d["item_id"] != "999999" for d in deals)


if __name__ == "__main__":
    test_parse_search_page_keeps_only_discounted_in_stock_items()
    print("ok")
