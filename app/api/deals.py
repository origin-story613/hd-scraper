from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Deal
from app.schemas import DealOut, DealsPage, MetaOut

router = APIRouter(prefix="/api", tags=["deals"])

SortOption = Literal["discount_desc", "price_asc", "price_desc", "newest"]


@router.get("/deals", response_model=DealsPage)
def list_deals(
    db: Session = Depends(get_db),
    search: str | None = Query(None, description="Search in title/brand"),
    category: str | None = Query(None),
    zip_code: str | None = Query(None),
    min_discount: float | None = Query(None, ge=0, le=100),
    max_price: float | None = Query(None, ge=0),
    in_stock_only: bool = Query(False),
    sort: SortOption = Query("discount_desc"),
    limit: int = Query(48, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    stmt = select(Deal).where(Deal.is_active.is_(True))

    if search:
        like = f"%{search.strip()}%"
        stmt = stmt.where((Deal.title.ilike(like)) | (Deal.brand.ilike(like)))
    if category:
        stmt = stmt.where(Deal.category == category)
    if zip_code:
        stmt = stmt.where(Deal.zip_code == zip_code)
    if min_discount is not None:
        stmt = stmt.where(Deal.discount_percent >= min_discount)
    if max_price is not None:
        stmt = stmt.where(Deal.current_price <= max_price)
    if in_stock_only:
        stmt = stmt.where(Deal.in_stock.is_(True))

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0

    if sort == "discount_desc":
        stmt = stmt.order_by(Deal.discount_percent.desc().nullslast())
    elif sort == "price_asc":
        stmt = stmt.order_by(Deal.current_price.asc())
    elif sort == "price_desc":
        stmt = stmt.order_by(Deal.current_price.desc())
    elif sort == "newest":
        stmt = stmt.order_by(Deal.first_seen.desc())

    stmt = stmt.limit(limit).offset(offset)
    items = db.scalars(stmt).all()

    return DealsPage(total=total, limit=limit, offset=offset, items=list(items))


@router.get("/deals/{deal_id}", response_model=DealOut)
def get_deal(deal_id: str, db: Session = Depends(get_db)):
    deal = db.get(Deal, deal_id)
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    return deal


@router.get("/meta", response_model=MetaOut)
def get_meta(db: Session = Depends(get_db)):
    total = db.scalar(select(func.count()).where(Deal.is_active.is_(True))) or 0
    categories = [
        c for (c,) in db.execute(
            select(Deal.category).where(Deal.is_active.is_(True), Deal.category.is_not(None)).distinct()
        )
    ]
    zip_codes = [
        z for (z,) in db.execute(
            select(Deal.zip_code).where(Deal.is_active.is_(True), Deal.zip_code.is_not(None)).distinct()
        )
    ]
    max_discount = db.scalar(
        select(func.max(Deal.discount_percent)).where(Deal.is_active.is_(True))
    )
    last_scraped = db.scalar(select(func.max(Deal.last_seen)))

    return MetaOut(
        total_deals=total,
        categories=sorted(categories),
        zip_codes=sorted(zip_codes),
        max_discount_percent=max_discount,
        last_scraped=last_scraped,
    )
