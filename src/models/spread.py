import datetime
import uuid
from typing import List, Optional

from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.dialects.sqlite import REAL
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base

class PairModel(Base):
    """Model for cryptocurrency pairs in the database"""

    __tablename__ = "pairs"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    base: Mapped[str] = mapped_column(String, nullable=False, index=True)
    quote: Mapped[str] = mapped_column(String, nullable=False, index=True)

    
    spreads: Mapped[List["SpreadModel"]] = relationship(
        back_populates="pair_rel", cascade="all, delete-orphan"
    )

class SpotExchangeDataModel(Base):
    """Model for spot exchange data for a specific spread"""

    __tablename__ = "spot_exchange_data"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    spread_id: Mapped[str] = mapped_column(
        ForeignKey("spreads.id"), nullable=False, index=True
    )
    exchange_name: Mapped[str] = mapped_column(String, nullable=False)
    exchange_kind: Mapped[str] = mapped_column(String, nullable=False, index=True)
    difference_percent: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    profit: Mapped[Optional[float]] = mapped_column(REAL, nullable=True)
    average_price: Mapped[Optional[float]] = mapped_column(REAL, nullable=True)
    volume: Mapped[Optional[float]] = mapped_column(REAL, nullable=True)
    deposit_status: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    withdrawal_status: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    link: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    spread_rel: Mapped["SpreadModel"] = relationship(foreign_keys=[spread_id])

class SpreadModel(Base):
    """Model for spreads in the database"""

    __tablename__ = "spreads"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4())
    )
    pair_id: Mapped[str] = mapped_column(
        ForeignKey("pairs.id"), nullable=False, index=True
    )

    
    contract: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    network: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    
    spread_percent: Mapped[float] = mapped_column(REAL, nullable=False, index=True)
    price_1: Mapped[Optional[float]] = mapped_column(REAL, nullable=True)
    price_2: Mapped[Optional[float]] = mapped_column(REAL, nullable=True)
    price_for: Mapped[Optional[float]] = mapped_column(REAL, nullable=True)
    dex: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    direction_from: Mapped[Optional[str]] = mapped_column(
        String, nullable=True
    )  
    direction_to: Mapped[Optional[str]] = mapped_column(
        String, nullable=True
    )  
    
    timestamp: Mapped[datetime.datetime] = mapped_column(
        DateTime,
        nullable=False,
        index=True,
        default=lambda: datetime.datetime.now(datetime.UTC),
    )
    liquidity: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    fdv: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    days_on_market: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    average_price: Mapped[Optional[float]] = mapped_column(REAL, nullable=True)
    
    pair_rel: Mapped[PairModel] = relationship(back_populates="spreads")
    spot_exchanges: Mapped[List["SpotExchangeDataModel"]] = relationship(
        "SpotExchangeDataModel",
        primaryjoin="and_(SpreadModel.id == SpotExchangeDataModel.spread_id, SpotExchangeDataModel.exchange_kind == 'spot')",
        back_populates="spread_rel",
        cascade="all, delete-orphan",
    )
    futures_exchanges: Mapped[List["SpotExchangeDataModel"]] = relationship(
        "SpotExchangeDataModel",
        primaryjoin="and_(SpreadModel.id == SpotExchangeDataModel.spread_id, SpotExchangeDataModel.exchange_kind == 'futures')",
        back_populates="spread_rel",
        cascade="all, delete-orphan",
        overlaps="spot_exchanges",
    )
