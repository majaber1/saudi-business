"""
Business Auctions API (LISTING + interest only).

  GET  /auctions/                 -> public list of published auctions
  GET  /auctions/{id}             -> public detail (with bids/interests)
  POST /auctions/                 -> authenticated user creates a listing
  POST /auctions/{id}/bids        -> authenticated user records interest/bid

IMPORTANT: this module intentionally has NO payment processing, escrow, or
legally binding settlement. Bids are non-binding expressions of interest.
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.db import DB_ENABLED, SessionLocal
from app.api.auth import UserOut, get_current_user

router = APIRouter(prefix="/auctions", tags=["auctions"])

DISCLAIMER = (
    "Listing and connection only. No payment processing, escrow, or binding "
    "settlement. Bids are non-binding expressions of interest."
)


def _db():
    if not DB_ENABLED:
        raise HTTPException(status_code=503, detail="Auctions require persistence.")
    return SessionLocal()


class AuctionIn(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    category: str = Field(..., min_length=1, max_length=80)
    description: Optional[str] = None
    asking_price: Optional[float] = None


class BidIn(BaseModel):
    amount: Optional[float] = None
    kind: str = Field(default="expression_of_interest", max_length=30)
    message: Optional[str] = None


class BidOut(BaseModel):
    id: int
    auction_id: int
    amount: Optional[float]
    kind: str
    message: Optional[str]
    model_config = {"from_attributes": True}


class AuctionOut(BaseModel):
    id: int
    title: str
    category: str
    description: Optional[str]
    asking_price: Optional[float]
    status: str
    disclaimer: str = DISCLAIMER
    model_config = {"from_attributes": True}


@router.get("/", response_model=List[AuctionOut])
def list_auctions():
    if not DB_ENABLED:
        return []
    from app import models
    db = SessionLocal()
    try:
        rows = (db.query(models.Auction)
                .filter(models.Auction.status.in_(["published", "open"]))
                .order_by(models.Auction.id.desc()).limit(200).all())
        return [AuctionOut.model_validate(r) for r in rows]
    finally:
        db.close()


@router.get("/{auction_id}", response_model=AuctionOut)
def get_auction(auction_id: int):
    if not DB_ENABLED:
        raise HTTPException(status_code=404, detail="Not found")
    from app import models
    db = SessionLocal()
    try:
        obj = db.get(models.Auction, auction_id)
        if obj is None:
            raise HTTPException(status_code=404, detail="Not found")
        return AuctionOut.model_validate(obj)
    finally:
        db.close()


@router.post("/", response_model=AuctionOut, status_code=201)
def create_auction(data: AuctionIn, user: UserOut = Depends(get_current_user)):
    from app import models
    db = _db()
    try:
        obj = models.Auction(status="published", seller_id=user.id, **data.model_dump())
        db.add(obj)
        db.add(models.AuditLog(actor_id=user.id, action="auction.create", entity="auction",
                               entity_id=None, meta={}))
        db.commit()
        db.refresh(obj)
        return AuctionOut.model_validate(obj)
    finally:
        db.close()


@router.post("/{auction_id}/bids", response_model=BidOut, status_code=201)
def place_bid(auction_id: int, data: BidIn, user: UserOut = Depends(get_current_user)):
    from app import models
    db = _db()
    try:
        auction = db.get(models.Auction, auction_id)
        if auction is None:
            raise HTTPException(status_code=404, detail="Auction not found")
        bid = models.AuctionBid(auction_id=auction_id, bidder_id=user.id,
                                amount=data.amount, kind=data.kind, message=data.message)
        db.add(bid)
        db.add(models.AuditLog(actor_id=user.id, action="auction.bid", entity="auction",
                               entity_id=auction_id, meta={}))
        db.commit()
        db.refresh(bid)
        return BidOut.model_validate(bid)
    finally:
        db.close()
