#!/usr/bin/env python3
"""Insert a handful of fake deals so you can preview the site before the
real scraper has a dataset to work with. Safe to run repeatedly.

Usage: python scripts/seed_sample_data.py
"""

import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.db import SessionLocal, init_db  # noqa: E402
from app.models import Deal  # noqa: E402
from app.scraper.parser import make_deal_id  # noqa: E402

SAMPLE_DEALS = [
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
    init_db()
    db = SessionLocal()
    now = datetime.datetime.utcnow()
    try:
        for raw in SAMPLE_DEALS:
            in_stock = raw.pop("in_stock", True)
            discount_amount = round(raw["original_price"] - raw["current_price"], 2)
            discount_percent = round(discount_amount / raw["original_price"] * 100, 1)
            deal_id = make_deal_id(raw["item_id"], None)

            existing = db.get(Deal, deal_id)
            fields = dict(
                **raw,
                id=deal_id,
                sku=None,
                discount_amount=discount_amount,
                discount_percent=discount_percent,
                store_id=None,
                store_name=None,
                in_stock=in_stock,
                last_seen=now,
                is_active=True,
            )
            if existing:
                for k, v in fields.items():
                    setattr(existing, k, v)
            else:
                db.add(Deal(**fields, first_seen=now))
        db.commit()
        print(f"Seeded {len(SAMPLE_DEALS)} sample deals.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
