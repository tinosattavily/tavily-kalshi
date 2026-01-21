# app/domains/markets/schemas.py
"""Pydantic models for Polymarket API responses."""

from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel

# ---------- Nested helper models ----------


class Tag(BaseModel):
    id: int
    label: str
    slug: str
    forceShow: bool
    publishedAt: Optional[datetime] = None
    updatedBy: Optional[int] = None
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None
    forceHide: Optional[bool] = None


class ClobReward(BaseModel):
    id: int
    conditionId: str
    assetAddress: str
    rewardsAmount: float
    rewardsDailyRate: float
    startDate: date
    endDate: date


# ---------- Main models ----------


class Market(BaseModel):
    # Core identifiers
    id: str
    question: str
    conditionId: str
    slug: str

    # Resolution / timing
    resolutionSource: Optional[str] = None
    endDate: datetime
    startDate: datetime
    endDateIso: Optional[str] = None
    startDateIso: Optional[str] = None
    hasReviewedDates: Optional[bool] = None

    # Display
    image: Optional[str] = None
    icon: Optional[str] = None
    description: str

    # Prices & outcomes (note: JSON arrays encoded as strings)
    outcomes: str
    outcomePrices: str

    # Liquidity / volume (API sometimes sends as strings, Pydantic will coerce)
    liquidity: float
    volume: str
    volumeNum: Optional[float] = None
    liquidityNum: Optional[float] = None
    volume24hr: Optional[float] = None
    volume1wk: Optional[float] = None
    volume1mo: Optional[float] = None
    volume1yr: Optional[float] = None
    volume24hrClob: Optional[float] = None
    volume1wkClob: Optional[float] = None
    volume1moClob: Optional[float] = None
    volume1yrClob: Optional[float] = None
    volumeClob: Optional[float] = None
    liquidityClob: Optional[float] = None

    # Market status / flags
    active: bool
    closed: bool
    new: bool
    featured: bool
    archived: bool
    restricted: bool
    ready: Optional[bool] = None
    funded: Optional[bool] = None
    cyom: Optional[bool] = None
    automaticallyActive: Optional[bool] = None
    clearBookOnStart: Optional[bool] = None
    manualActivation: Optional[bool] = None
    competitive: Optional[float] = None
    pagerDutyNotificationEnabled: Optional[bool] = None
    approved: Optional[bool] = None
    pendingDeployment: Optional[bool] = None
    deploying: Optional[bool] = None

    # Trading parameters
    marketMakerAddress: str
    orderPriceMinTickSize: float
    orderMinSize: float
    customLiveness: Optional[float] = None
    acceptingOrders: bool
    acceptingOrdersTimestamp: Optional[datetime] = None
    negRisk: bool
    negRiskRequestID: str
    negRiskOther: Optional[bool] = None
    enableOrderBook: bool
    spread: Optional[float] = None
    rewardsMinSize: Optional[float] = None
    rewardsMaxSpread: Optional[float] = None
    rfqEnabled: Optional[bool] = None
    holdingRewardsEnabled: Optional[bool] = None
    feesEnabled: Optional[bool] = None

    # Participants / provenance
    submitted_by: Optional[str] = None
    resolvedBy: Optional[str] = None

    # Grouping
    groupItemTitle: Optional[str] = None
    groupItemThreshold: str
    questionID: str

    # Rewards / UMA / CLOB
    clobTokenIds: str  # JSON array as string
    umaBond: str
    umaReward: str
    clobRewards: Optional[List[ClobReward]] = None
    umaResolutionStatuses: Optional[str] = None

    # Price changes / best prices
    oneDayPriceChange: Optional[float] = None
    oneHourPriceChange: Optional[float] = None
    oneWeekPriceChange: Optional[float] = None
    oneMonthPriceChange: Optional[float] = None
    lastTradePrice: Optional[float] = None
    bestBid: Optional[float] = None
    bestAsk: Optional[float] = None

    # Timestamps
    createdAt: datetime
    updatedAt: datetime
    deployingTimestamp: Optional[datetime] = None

    # Nested events (from /markets?slug=...)
    events: Optional[List["Event"]] = None

    class Config:
        # Allow extra fields from API that we don't model
        extra = "ignore"


class Event(BaseModel):
    # Core identifiers
    id: str
    ticker: str
    slug: str
    title: str

    # Description / resolution
    description: str
    resolutionSource: Optional[str] = None

    # Timing
    startDate: datetime
    creationDate: datetime
    endDate: datetime

    # Display
    image: Optional[str] = None
    icon: Optional[str] = None

    # Status flags
    active: bool
    closed: bool
    archived: bool
    new: bool
    featured: bool
    restricted: bool
    cyom: Optional[bool] = None
    showAllOutcomes: Optional[bool] = None
    showMarketImages: Optional[bool] = None
    enableNegRisk: Optional[bool] = None
    automaticallyActive: Optional[bool] = None
    negRiskAugmented: Optional[bool] = None
    pendingDeployment: Optional[bool] = None
    deploying: Optional[bool] = None

    # Liquidity / volume
    liquidity: float
    volume: float
    openInterest: float
    liquidityClob: Optional[float] = None
    competitive: Optional[float] = None
    volume24hr: Optional[float] = None
    volume1wk: Optional[float] = None
    volume1mo: Optional[float] = None
    volume1yr: Optional[float] = None

    # Misc metrics
    enableOrderBook: Optional[bool] = None
    commentCount: Optional[int] = None
    featuredOrder: Optional[int] = None

    # Timestamps
    createdAt: datetime
    updatedAt: datetime

    # Nested relations
    markets: Optional[List[Market]] = None  # present on /events?slug=...
    tags: Optional[List[Tag]] = None  # present on /events?slug=...

    class Config:
        # Allow extra fields from API that we don't model
        extra = "ignore"


# Resolve forward references for Pydantic v2
Event.model_rebuild()
Market.model_rebuild()
