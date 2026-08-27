import datetime

from pydantic import BaseModel, ConfigDict


class DealOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    item_id: str
    sku: str | None
    title: str
    brand: str | None
    category: str | None
    image_url: str | None
    product_url: str
    current_price: float
    original_price: float | None
    discount_percent: float | None
    discount_amount: float | None
    badge: str | None
    store_id: str | None
    store_name: str | None
    zip_code: str | None
    in_stock: bool
    first_seen: datetime.datetime
    last_seen: datetime.datetime


class DealsPage(BaseModel):
    total: int
    limit: int
    offset: int
    items: list[DealOut]


class MetaOut(BaseModel):
    total_deals: int
    categories: list[str]
    zip_codes: list[str]
    max_discount_percent: float | None
    last_scraped: datetime.datetime | None
