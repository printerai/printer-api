import datetime
from typing import Literal, Optional
from fastapi import Depends, Query
from pydantic import BaseModel, Field

from src.entities.spread import Pair

def get_pair(
    base: Optional[str] = Query(
        None, description="Base currency of the pair, e.g., BTC"
    ),
    quote: Optional[str] = Query(
        None, description="Quote currency of the pair, e.g., USDT"
    ),
) -> Optional[Pair]:
    if base and quote:
        return Pair(base=base, quote=quote)
    return None

def get_filter_query(
    limit: int = Query(100, gt=0, le=100, description="Number of records per page"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    network: Optional[str] = Query(None, description="Filter by network, e.g., SOLANA"),
    exchanges: Optional[str] = Query(None, description="Filter by exchanges"),
    from_spread: Optional[float] = Query(
        None, description="Filter by minimum spread percentage"
    ),
    to_spread: Optional[float] = Query(
        None, description="Filter by maximum spread percentage"
    ),
    from_liquidity: Optional[float] = Query(
        None, description="Filter by minimum spread liquidity"
    ),
    to_liquidity: Optional[float] = Query(
        None, description="Filter by maximum spread liquidity"
    ),
    from_fdv: Optional[float] = Query(None, description="Filter by minimum FDV"),
    to_fdv: Optional[float] = Query(None, description="Filter by maximum FDV"),
    sort_by: Literal["topSpread", "liquidity", "sortFdv", "sortDays"] = Query(
        "topSpread", description="Sort by field"
    ),
    order_by: Literal["asc", "desc"] = Query("asc", description="Sort order"),
) -> "FilterParams":
    return FilterParams(
        limit=limit,
        offset=offset,
        network=network,
        exchanges=exchanges,
        from_spread=from_spread,
        to_spread=to_spread,
        from_liquidity=from_liquidity,
        to_liquidity=to_liquidity,
        from_fdv=from_fdv,
        to_fdv=to_fdv,
        sort_by=sort_by,
        order_by=order_by,
    )

class FilterParams(BaseModel):
    limit: int = Field(100, gt=0, le=100)
    offset: int = Field(0, ge=0)
    network: Optional[str] = Field(None)
    exchanges: Optional[str] = Field(None)
    from_spread: Optional[float] = Field(None)
    to_spread: Optional[float] = Field(None)
    from_liquidity: Optional[float] = Field(None)
    to_liquidity: Optional[float] = Field(None)
    from_fdv: Optional[float] = Field(None)
    to_fdv: Optional[float] = Field(None)
    sort_by: Literal["topSpread", "liquidity", "sortFdv", "sortDays"] = Field(
        default="topSpread"
    )
    order_by: Literal["asc", "desc"] = Field(default="asc")
