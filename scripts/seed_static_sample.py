#!/usr/bin/env python3
"""Write a docs/deals.json with a few fake deals, so the GitHub Pages site
has something to show before the scraper workflow has run for the first
time. The real workflow overwrites this file on its own schedule.

Usage: python scripts/seed_static_sample.py
"""

import datetime
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.scraper.parser import make_deal_id  # noqa: E402

OUTPUT_PATH = Path(__file__).resolve().parent.parent / "docs" / "deals.json"

RAW = [
    dict(
        item_id="312345678",
        title="20V MAX Cordless Drill/Driver Kit with Battery and Charger",
        brand="RYOBI",
        category="Tools",
        image_url="https://images.thdstatic.com/productImages/placeholder1.jpg",
        product_url="https://www.homedepot.com/p/RYOBI-Drill-Kit/312345678",
        current_price=49.00,
        original_price=99.00,
        badge="Clearance",
        zip_code="10001",
        in_stock=True,
    ),
    dict(
        item_id="312345679",
        title="26 cu. ft. French Door Refrigerator in Stainless Steel",
        brand="Samsung",
        category="Appliances",
        image_url="https://images.thdstatic.com/productImages/placeholder2.jpg",
        product_url="https://www.homedepot.com/p/Samsung-Fridge/312345679",
        current_price=1299.00,
        original_price=2399.00,
        badge="Clearance",
        zip_code="60601",
        in_stock=True,
    ),
    dict(
        item_id="312345680",
        title="5-Piece Steel Patio Conversation Set with Cushions",
        brand="Hampton Bay",
        category="Outdoor & Patio",
        image_url="https://images.thdstatic.com/productImages/placeholder3.jpg",
        product_url="https://www.homedepot.com/p/Hampton-Bay-Patio-Set/312345680",
        current_price=249.00,
        original_price=899.00,
        badge="Special Buy",
        zip_code="90001",
        in_stock=True,
    ),
    dict(
        item_id="312345681",
        title="2 Gal. Exterior Semi-Gloss Paint",
        brand="Behr",
        category="Paint",
        image_url="https://images.thdstatic.com/productImages/placeholder4.jpg",
        product_url="https://www.homedepot.com/p/Behr-Paint/312345681",
        current_price=19.00,
        original_price=64.00,
        badge="Clearance",
        zip_code="10001",
        in_stock=False,
    ),
]


def main():
    deals = []
    for raw in RAW:
        discount_amount = round(raw["original_price"] - raw["current_price"], 2)
        discount_percent = round(discount_amount / raw["original_price"] * 100, 1)
        deals.append(
            {
                "id": make_deal_id(raw["item_id"], None),
                "item_id": raw["item_id"],
                "sku": None,
                "title": raw["title"],
                "brand": raw["brand"],
                "category": raw["category"],
                "image_url": raw["image_url"],
                "product_url": raw["product_url"],
                "current_price": raw["current_price"],
                "original_price": raw["original_price"],
                "discount_percent": discount_percent,
                "discount_amount": discount_amount,
                "badge": raw["badge"],
                "store_id": None,
                "store_name": None,
                "zip_code": raw["zip_code"],
                "in_stock": raw["in_stock"],
            }
        )

    payload = {
        "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
        "count": len(deals),
        "deals": deals,
    }
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2))
    print(f"Wrote {len(deals)} sample deals to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
