import datetime
from typing import List, Literal, Optional, TypedDict, Union

import logfire
from sqlalchemy import and_, or_, select, func, literal_column
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.entities.filter import FilterParams

from src.entities.spread import (
    Pair,
    SpreadResponse,
    SpreadInput,
    Direction,
    CEXData,
    SpotExchangeData,
    SpreadsResponseWithCount,
)

from src.models.spread import (
    PairModel,
    SpreadModel,
    SpotExchangeDataModel,
)

def _normalize_sort_parameter(
    sort_by: Optional[Literal["topSpread", "liquidity", "sortFdv", "sortDays"]],
    order_by: Optional[Literal["asc", "desc"]],
) -> tuple[str, str]:
    match sort_by:
        case "liquidity":
            sort_by = SpreadModel.liquidity
        case "sortFdv":
            sort_by = SpreadModel.fdv
        case "sortDays":
            sort_by = SpreadModel.days_on_market
        case _:
            sort_by = SpreadModel.spread_percent

    if order_by == "desc":
        sort_by = sort_by.desc()
    elif order_by == "asc":
        sort_by = sort_by.asc()
    else:
        raise ValueError(f"Invalid order_by: {order_by}")

    return sort_by

class SpreadService:
    """Service for working with spreads in the database"""

    def __init__(self, db: AsyncSession):
        """
        Service initialization

        Args:
            db: SQLAlchemy asynchronous session
        """
        self.db = db

    async def get_exchanges(self) -> List[str]:
        """
        Get a list of unique exchange names from spot exchanges, direction_from, and direction_to.
        """
        all_exchange_names: set[str] = set()

        
        spot_query = select(SpotExchangeDataModel.exchange_name).distinct()
        spot_result = await self.db.execute(spot_query)
        for name in spot_result.scalars().all():
            if name and name.strip():  
                all_exchange_names.add(name.strip())

        return sorted(
            [i.lower() for i in all_exchange_names]
        )  

    async def get_spreads(
        self, filter_params: FilterParams
    ) -> SpreadsResponseWithCount:
        """
        Get a list of spreads with filters applied and total count.

        Args:
            filter_params: Filtering parameters

        Returns:
            SpreadsResponseWithCount: Object containing list of spread objects and total count.
        """
        
        base_query = select(SpreadModel.id)

        if filter_params.exchanges:
            exchanges_list = [
                ex.strip().lower()
                for ex in filter_params.exchanges.split(",")
                if ex.strip()
            ]
            if exchanges_list:
                base_query = base_query.filter(
                    SpreadModel.spot_exchanges.any(
                        func.lower(SpotExchangeDataModel.exchange_name).in_(
                            exchanges_list
                        )
                    ),
                )

        if filter_params.network:
            base_query = base_query.filter(SpreadModel.network == filter_params.network)

        if filter_params.from_spread is not None:
            base_query = base_query.filter(
                SpreadModel.spread_percent >= filter_params.from_spread
            )

        if filter_params.to_spread is not None:
            base_query = base_query.filter(
                SpreadModel.spread_percent <= filter_params.to_spread
            )

        if filter_params.from_liquidity is not None:
            base_query = base_query.filter(
                SpreadModel.liquidity >= filter_params.from_liquidity
            )

        if filter_params.to_liquidity is not None:
            base_query = base_query.filter(
                SpreadModel.liquidity <= filter_params.to_liquidity
            )

        if filter_params.from_fdv is not None:
            base_query = base_query.filter(SpreadModel.fdv >= filter_params.from_fdv)

        if filter_params.to_fdv is not None:
            base_query = base_query.filter(SpreadModel.fdv <= filter_params.to_fdv)

        if filter_params.sort_by and filter_params.order_by:
            base_query = base_query.order_by(
                _normalize_sort_parameter(filter_params.sort_by, filter_params.order_by)
            )

        
        count_query = select(func.count()).select_from(base_query.subquery())
        total_count = (await self.db.execute(count_query)).scalar_one()

        sort_expr = _normalize_sort_parameter(
            filter_params.sort_by, filter_params.order_by
        )
        id_page = (
            base_query.order_by(sort_expr)
            .offset(filter_params.offset)
            .limit(filter_params.limit)
        )
        ids = (await self.db.execute(id_page)).scalars().all()

        if not ids:
            return SpreadsResponseWithCount(spreads=[], total_count=total_count)

        data_stmt = (
            select(SpreadModel)
            .options(
                joinedload(SpreadModel.pair_rel),
                joinedload(SpreadModel.spot_exchanges),
                joinedload(SpreadModel.futures_exchanges),
            )
            .where(SpreadModel.id.in_(tuple(ids)))
            .order_by(sort_expr)
        )

        result = await self.db.execute(data_stmt)
        db_spreads = result.scalars().unique().all()

        spread_responses = [self._map_to_entity(db_spread) for db_spread in db_spreads]

        return SpreadsResponseWithCount(
            spreads=spread_responses, total_count=total_count
        )

    async def get_spread_by_id(self, spread_id: str) -> Optional[SpreadResponse]:
        """
        Get spread by ID

        Args:
            spread_id: Spread ID

        Returns:
            Optional[SpreadResponse]: Spread object or None if not found
        """
        query = (
            select(SpreadModel)
            .options(
                joinedload(SpreadModel.pair_rel),
                joinedload(SpreadModel.spot_exchanges),
                joinedload(SpreadModel.futures_exchanges),
            )
            .filter(SpreadModel.id == spread_id)
        )
        result = await self.db.execute(query)
        db_spread = result.scalars().unique().one_or_none()  

        if db_spread:
            return self._map_to_entity(db_spread)
        return None

    async def create_spread(self, spread_input: SpreadInput) -> SpreadResponse:
        """
        Create a new spread

        Args:
            spread_input: Spread data for creation (Pydantic SpreadInput model)

        Returns:
            SpreadResponse: Created spread with an assigned ID
        """
        logfire.info("Creating spread: {spread_input}", spread_input=spread_input)

        pair_query = select(PairModel).filter(
            and_(
                PairModel.base == spread_input.pair.base,
                PairModel.quote == spread_input.pair.quote,
            )
        )
        result = await self.db.execute(pair_query)
        db_pair = result.scalar_one_or_none()

        if not db_pair:
            db_pair = PairModel(
                base=spread_input.pair.base, quote=spread_input.pair.quote
            )
            self.db.add(db_pair)
            await self.db.flush()  

        logfire.info("contract: {contract}", contract=spread_input.contract)
        logfire.info("price_1: {price_1}", price_1=spread_input.price_1)
        logfire.info("price_2: {price_2}", price_2=spread_input.price_2)
        logfire.info("price_for: {price_for}", price_for=spread_input.price_for)

        db_spread = SpreadModel(
            pair_id=db_pair.id,
            network=spread_input.network,
            spread_percent=spread_input.spread,  
            direction_from=spread_input.direction.from_exchange,  
            direction_to=spread_input.direction.to_exchange,  
            timestamp=spread_input.timestamp,
            liquidity=spread_input.liquidity,
            price_1=spread_input.price_1,
            contract=spread_input.contract,
            price_2=spread_input.price_2,
            price_for=spread_input.price_for,
            dex=spread_input.dex,
            fdv=spread_input.fdv,
            days_on_market=spread_input.days,  
        )

        if spread_input.cex:
            if spread_input.cex.spot:
                for spot_data in spread_input.cex.spot:
                    db_spread.spot_exchanges.append(
                        SpotExchangeDataModel(
                            exchange_name=spot_data.exchange_name,  
                            difference_percent=spot_data.difference_percent,
                            profit=spot_data.profit,
                            average_price=spot_data.average_price,
                            volume=spot_data.volume,
                            deposit_status=spot_data.deposit_status,
                            withdrawal_status=spot_data.withdrawal_status,
                            link=spot_data.link,
                            exchange_kind=spot_data.exchange_kind,
                        )
                    )
            if spread_input.cex.futures:
                for spot_data in spread_input.cex.futures:
                    db_spread.futures_exchanges.append(
                        SpotExchangeDataModel(
                            exchange_name=spot_data.exchange_name,  
                            difference_percent=spot_data.difference_percent,
                            profit=spot_data.profit,
                            average_price=spot_data.average_price,
                            volume=spot_data.volume,
                            deposit_status=spot_data.deposit_status,
                            withdrawal_status=spot_data.withdrawal_status,
                            link=spot_data.link,
                            exchange_kind=spot_data.exchange_kind,
                        )
                    )

        self.db.add(db_spread)
        await self.db.commit()
        
        await self.db.refresh(
            db_spread, ["pair_rel", "spot_exchanges", "futures_exchanges"]
        )

        return self._map_to_entity(db_spread)

    async def update_spread(
        self, spread_id: str, spread_input: SpreadInput
    ) -> Optional[SpreadResponse]:
        """
        Update spread

        Args:
            spread_id: ID of the spread to update
            spread_input: New spread data (Pydantic SpreadInput model)

        Returns:
            Optional[SpreadResponse]: Updated spread or None if not found
        """
        query = select(SpreadModel).filter(SpreadModel.id == spread_id)
        result = await self.db.execute(query)
        db_spread = result.scalar_one_or_none()

        if not db_spread:
            return None

        pair_query = select(PairModel).filter(
            and_(
                PairModel.base == spread_input.pair.base,
                PairModel.quote == spread_input.pair.quote,
            )
        )
        result = await self.db.execute(pair_query)
        db_pair = result.scalar_one_or_none()

        if not db_pair:
            db_pair = PairModel(
                base=spread_input.pair.base, quote=spread_input.pair.quote
            )
            self.db.add(db_pair)
            await self.db.flush()

        
        db_spread.pair_id = db_pair.id
        db_spread.network = spread_input.network
        db_spread.spread_percent = spread_input.spread
        db_spread.direction_from = spread_input.direction.from_exchange
        db_spread.direction_to = spread_input.direction.to_exchange
        db_spread.timestamp = spread_input.timestamp
        db_spread.price_1 = spread_input.price_1
        db_spread.price_2 = spread_input.price_2
        db_spread.price_for = spread_input.price_for
        db_spread.contract = spread_input.contract
        db_spread.dex = spread_input.dex
        db_spread.liquidity = spread_input.liquidity
        db_spread.fdv = spread_input.fdv
        db_spread.days_on_market = spread_input.days

        
        db_spread.spot_exchanges.clear()
        db_spread.futures_exchanges.clear()
        
        await self.db.flush()

        if spread_input.cex:
            if spread_input.cex.spot:
                for spot_data in spread_input.cex.spot:
                    db_spread.spot_exchanges.append(
                        SpotExchangeDataModel(
                            exchange_name=spot_data.exchange_name,
                            difference_percent=spot_data.difference_percent,
                            profit=spot_data.profit,
                            average_price=spot_data.average_price,
                            volume=spot_data.volume,
                            deposit_status=spot_data.deposit_status,
                            withdrawal_status=spot_data.withdrawal_status,
                            link=spot_data.link,
                        )
                    )
            if spread_input.cex.futures:
                for futures_data in spread_input.cex.futures:
                    db_spread.futures_exchanges.append(
                        SpotExchangeDataModel(
                            exchange_name=futures_data.exchange_name,
                            difference_percent=futures_data.difference_percent,
                            profit=futures_data.profit,
                            average_price=futures_data.average_price,
                            volume=futures_data.volume,
                            deposit_status=futures_data.deposit_status,
                            withdrawal_status=futures_data.withdrawal_status,
                            link=futures_data.link,
                        )
                    )

        await self.db.commit()
        await self.db.refresh(
            db_spread, ["pair_rel", "spot_exchanges", "futures_exchanges"]
        )

        return self._map_to_entity(db_spread)

    async def delete_spread(self, spread_id: str) -> bool:
        """
        Delete spread

        Args:
            spread_id: ID of the spread to delete

        Returns:
            bool: True if deletion was successful, otherwise False
        """
        query = select(SpreadModel).filter(SpreadModel.id == spread_id)
        result = await self.db.execute(query)
        db_spread = result.scalar_one_or_none()

        if not db_spread:
            return False

        await self.db.delete(db_spread)  
        await self.db.commit()

        return True

    def _map_to_entity(self, db_spread: SpreadModel) -> SpreadResponse:
        """
        Convert SQLAlchemy SpreadModel to Pydantic SpreadResponse model

        Args:
            db_spread: Spread model from DB

        Returns:
            SpreadResponse: Pydantic spread model
        """
        
        spot_exchanges_pydantic = [
            SpotExchangeData.model_validate(spot_db)
            for spot_db in db_spread.spot_exchanges
        ]

        
        futures_exchanges_pydantic = [
            SpotExchangeData.model_validate(futures_db)
            for futures_db in db_spread.futures_exchanges
        ]

        cex_data_pydantic = None
        if spot_exchanges_pydantic or futures_exchanges_pydantic:
            cex_data_pydantic = CEXData(
                spot=spot_exchanges_pydantic, futures=futures_exchanges_pydantic
            )

        return SpreadResponse(
            id=db_spread.id,
            network=db_spread.network,
            spread_percent=db_spread.spread_percent,  
            pair=Pair.model_validate(db_spread.pair_rel),
            direction=Direction(
                from_exchange=db_spread.direction_from,
                to_exchange=db_spread.direction_to,
            ),
            contract=db_spread.contract,
            price_1=db_spread.price_1,
            price_2=db_spread.price_2,
            price_for=db_spread.price_for,
            dex=db_spread.dex,
            timestamp=db_spread.timestamp,
            liquidity=db_spread.liquidity,
            fdv=db_spread.fdv,
            days_on_market=db_spread.days_on_market,  
            cex_data=cex_data_pydantic,
        )
