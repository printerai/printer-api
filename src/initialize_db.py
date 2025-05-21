import asyncio
import datetime
from typing import List

import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from src.entities.spread import Pair, SpreadInput, Direction, CEXData, SpotExchangeData
from src.services.spread_service import SpreadService
from src.database import get_db, engine, Base

async def create_initial_data() -> None:
    """
    Creates initial data in the database
    """
    
    initial_spreads: List[SpreadInput] = [
        SpreadInput(
            pair=Pair(base="ETH", quote="USDT"),
            network="ETH",
            spread=1.03,
            direction=Direction(from_exchange="CEX", to_exchange="DEX"),
            timestamp=datetime.datetime.now(datetime.timezone.utc),
            liquidity=1234567,
            fdv=100000000,
            days=30,
            cex=CEXData(
                spot=[
                    SpotExchangeData(
                        exchange_name="binance",
                        average_price="2971.50",
                        volume="1000",
                        profit="1.05$",
                        difference_percent="0.5%",
                        deposit_status="🟠",
                        withdrawal_status="🟠",
                        link="http://binance.com/eth_usdt",
                    ),
                    SpotExchangeData(
                        exchange_name="bybit",
                        average_price="2971.50",
                        volume="1000",
                        profit="1.05$",
                        difference_percent="0.5%",
                        deposit_status="🟠",
                        withdrawal_status="🟠",
                        link="http://binance.com/eth_usdt",
                    ),
                ],
                futures=[],  
            ),
        ),
        SpreadInput(
            pair=Pair(base="BTC", quote="USDT"),
            network="BTC",
            spread=0.24,
            direction=Direction(from_exchange="CEX", to_exchange="DEX"),
            timestamp=datetime.datetime.now(datetime.timezone.utc),
            liquidity=500000,
            fdv=900000000,
            days=180,
            cex=CEXData(
                spot=[
                    SpotExchangeData(
                        exchange_name="coinbase",
                        average_price="42000.00",
                        volume="1000",
                        profit="1.05$",
                        difference_percent="0.5%",
                        deposit_status="🟠",
                        withdrawal_status="🟠",
                        link="http://coinbase.com/btc_usdt",
                    ),
                    SpotExchangeData(
                        exchange_name="kraken",
                        average_price="42100.00",
                        volume="1000",
                        profit="1.05$",
                        difference_percent="0.5%",
                        deposit_status="🟠",
                        withdrawal_status="🟠",
                        link="http://kraken.com/btc_usdt",
                    ),
                ]
            ),
        ),
        SpreadInput(
            pair=Pair(base="SOL", quote="USDT"),
            network="SOLANA",
            spread=1.55,
            direction=Direction(from_exchange="CEX", to_exchange="DEX"),
            timestamp=datetime.datetime.now(datetime.timezone.utc),
            liquidity=250000,
            fdv=50000000,
            days=90,
            cex=CEXData(
                spot=[
                    SpotExchangeData(
                        exchange_name="kraken",
                        average_price="42100.00",
                        volume="1000",
                        profit="1.05$",
                        difference_percent="0.5%",
                        deposit_status="🟢",
                        withdrawal_status="🟢",
                        link="http://kraken.com/btc_usdt",
                    )
                ]
            ),
        ),
    ]

    
    async with engine.begin() as conn:
        await conn.run_sync(
            Base.metadata.drop_all
        )  
        await conn.run_sync(Base.metadata.create_all)

    
    async for db in get_db():
        service = SpreadService(db)
        for spread_data in initial_spreads:  
            await service.create_spread(spread_data)
        break  

async def main() -> None:
    """
    Main function to run initialization
    """
    await create_initial_data()
    print("Database initialized successfully with new sample data.")

if __name__ == "__main__":
    asyncio.run(main())
