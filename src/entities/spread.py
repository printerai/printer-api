import datetime
from typing import List, Optional, Any
from pydantic import BaseModel, Field

class Pair(BaseModel):
    """Pydantic schema for a cryptocurrency pair"""

    id: Optional[str] = None  
    base: str
    quote: str

    class Config:
        from_attributes = True

class SpotExchangeData(BaseModel):
    """Pydantic schema for spot exchange data"""

    id: Optional[str] = None  
    exchange_name: str = Field(..., alias="exchange")
    exchange_kind: str = Field(..., alias="exchange_kind")
    difference_percent: Optional[str] = Field(None, alias="dif")
    profit: Optional[float] = Field(None, alias="prof")
    average_price: Optional[float] = Field(None, alias="av_price")
    volume: Optional[float] = Field(None, alias="vol")
    deposit_status: Optional[str] = Field(None, alias="d")
    withdrawal_status: Optional[str] = Field(None, alias="w")
    link: Optional[str] = None

    class Config:
        from_attributes = True
        populate_by_name = True  

class Direction(BaseModel):
    """Pydantic schema for direction"""

    from_exchange: Optional[str] = Field(None, alias="from")
    to_exchange: Optional[str] = Field(None, alias="to")

    class Config:
        from_attributes = True  
        populate_by_name = True

class CEXData(BaseModel):
    """Pydantic schema for CEX data (spot and futures)"""

    spot: List[SpotExchangeData] = []
    futures: List[SpotExchangeData] = []

    class Config:
        from_attributes = True

class Spread(BaseModel):
    """Main Pydantic schema for a spread"""

    id: Optional[str] = None  
    network: Optional[str] = None
    spread_percent: float = Field(
        ..., alias="spread"
    )  
    pair: Pair
    contract: Optional[str] = Field(None, alias="contract")
    dex: Optional[str] = Field(None, alias="dex")
    price_1: Optional[float] = Field(None, alias="price_1")
    price_2: Optional[float] = Field(None, alias="price_2")
    price_for: Optional[float] = Field(None, alias="price_for")
    direction: Direction  
    timestamp: datetime.datetime
    liquidity: Optional[int] = Field(None, alias="liquidity")
    fdv: Optional[int] = Field(None, alias="fdv")
    days_on_market: Optional[int] = Field(
        None, alias="days"
    )  
    cex_data: Optional[CEXData] = Field(
        None, alias="cex"
    )  

    class Config:
        from_attributes = True  
        populate_by_name = True  





















class SpreadResponse(Spread):  
    pass

class SpreadInput(BaseModel):  
    network: str
    spread: float
    contract: Optional[str] = Field(None)
    dex: Optional[str] = Field(None)
    price_1: Optional[float] = Field(None)
    price_2: Optional[float] = Field(None)
    price_for: Optional[float] = Field(None)
    pair: Pair  
    direction: Direction
    timestamp: datetime.datetime
    liquidity: int
    fdv: int
    days: int
    cex: CEXData
    

class SpreadsResponseWithCount(BaseModel):
    spreads: List[SpreadResponse]
    total_count: int
