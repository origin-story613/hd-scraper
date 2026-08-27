import datetime

from sqlalchemy import Boolean, DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class Deal(Base):
    """A single Home Depot clearance/discounted item seen at a specific store."""

    __tablename__ = "deals"

    # Stable id: hash of (item_id, store_id) so re-scraping upserts instead of duplicating.
    id: Mapped[str] = mapped_column(String, primary_key=True)

    item_id: Mapped[str] = mapped_column(String, index=True)
    sku: Mapped[str | None] = mapped_column(String, nullable=True)
    title: Mapped[str] = mapped_column(String, index=True)
    brand: Mapped[str | None] = mapped_column(String, nullable=True)
    category: Mapped[str | None] = mapped_column(String, index=True, nullable=True)

    image_url: Mapped[str | None] = mapped_column(String, nullable=True)
    product_url: Mapped[str] = mapped_column(String)

    current_price: Mapped[float] = mapped_column(Float)
    original_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    discount_percent: Mapped[float | None] = mapped_column(Float, index=True, nullable=True)
    discount_amount: Mapped[float | None] = mapped_column(Float, nullable=True)
    badge: Mapped[str | None] = mapped_column(String, nullable=True)

    store_id: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    store_name: Mapped[str | None] = mapped_column(String, nullable=True)
    zip_code: Mapped[str | None] = mapped_column(String, index=True, nullable=True)
    in_stock: Mapped[bool] = mapped_column(Boolean, default=True)

    first_seen: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )
    last_seen: Mapped[datetime.datetime] = mapped_column(
        DateTime, default=datetime.datetime.utcnow
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
