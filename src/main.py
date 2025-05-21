import datetime
from typing import Annotated, List, Optional, TypeVar
from fastapi import Depends, FastAPI, Query, HTTPException, Request, Header

from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from slowapi.middleware import SlowAPIMiddleware
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse
from contextlib import asynccontextmanager

import os
import sys

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.dirname(SCRIPT_DIR))

from src.config import settings
from src.database import get_db, engine, Base
from src.entities.filter import FilterParams, get_filter_query
from src.entities.spread import SpreadResponse, SpreadInput, SpreadsResponseWithCount
from src.rate_limiter import limiter, rate_limit_by_ip
from src.services.spread_service import SpreadService

import logfire

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle context manager"""
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


app = FastAPI(
    title=settings.api_title,
    description=settings.api_description,
    version=settings.api_version,
    debug=settings.debug,
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*"
    ],  
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

logfire.configure(token=settings.logfire_token)
logfire.instrument_fastapi(app, capture_headers=True)
logfire.instrument_sqlite3()

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

async def verify_bot_token(x_bot_token: Annotated[str | None, Header()] = None):
    """Dependency to verify the bot token from X-Bot-Token header."""
    if not settings.bot_token:
        
        
        
        raise HTTPException(
            status_code=500, detail="Bot token not configured on the server."
        )
    if not x_bot_token:
        raise HTTPException(
            status_code=401, detail="Not authenticated: X-Bot-Token header is missing."
        )
    if x_bot_token != settings.bot_token:
        raise HTTPException(status_code=403, detail="Forbidden: Invalid X-Bot-Token.")
    return x_bot_token

def get_spread_service(db: AsyncSession = Depends(get_db)) -> SpreadService:
    """
    Dependency to get the spread service

    Args:
        db: Async DB session

    Returns:
        SpreadService: Service for working with spreads
    """
    return SpreadService(db)

@app.get("/exchanges", response_model=List[str])
async def get_exchanges(
    request: Request,
    spread_service: SpreadService = Depends(get_spread_service),
) -> List[str]:
    """Get a list of exchanges"""

    return await spread_service.get_exchanges()

@app.get("/spreads", response_model=SpreadsResponseWithCount)
@rate_limit_by_ip(settings.rate_limit.get_spreads_limit)
async def get_spreads(
    request: Request,  
    filter_query: FilterParams = Depends(get_filter_query),
    spread_service: SpreadService = Depends(get_spread_service),
) -> SpreadsResponseWithCount:
    """
    Get a list of spreads with filters applied and total count.

    Args:
        request: FastAPI request
        filter_query: Filtering parameters
        spread_service: Service for working with spreads

    Returns:
        SpreadsResponseWithCount: Object containing list of spreads and total count.
    """
    return await spread_service.get_spreads(filter_query)

@app.get("/spreads/{spread_id}", response_model=SpreadResponse)
@rate_limit_by_ip(settings.rate_limit.get_spread_limit)
async def get_spread(
    spread_id: str,
    request: Request,  
    spread_service: SpreadService = Depends(get_spread_service),
) -> SpreadResponse:
    """
    Get spread by ID

    Args:
        spread_id: Spread ID
        request: FastAPI request
        spread_service: Service for working with spreads

    Returns:
        SpreadResponse: Spread object

    Raises:
        HTTPException: If spread is not found
    """
    spread = await spread_service.get_spread_by_id(spread_id)
    if not spread:
        raise HTTPException(status_code=404, detail="Spread not found")
    return spread

@app.post("/spreads", response_model=SpreadResponse, status_code=201)
@rate_limit_by_ip(settings.rate_limit.create_spread_limit)
async def create_spread(
    spread_input: SpreadInput,
    request: Request,  
    spread_service: SpreadService = Depends(get_spread_service),
    _: str = Depends(verify_bot_token),
) -> SpreadResponse:
    """
    Create a new spread

    Args:
        spread_input: New spread data
        request: FastAPI request
        spread_service: Service for working with spreads

    Returns:
        SpreadResponse: Created spread with an assigned ID
    """
    return await spread_service.create_spread(spread_input)

@app.put("/spreads/{spread_id}", response_model=SpreadResponse)
@rate_limit_by_ip(settings.rate_limit.update_spread_limit)
async def update_spread(
    spread_id: str,
    spread_input: SpreadInput,
    request: Request,  
    spread_service: SpreadService = Depends(get_spread_service),
    _: str = Depends(verify_bot_token),
) -> SpreadResponse:
    """
    Update spread

    Args:
        spread_id: ID of the spread to update
        spread_input: New spread data
        request: FastAPI request
        spread_service: Service for working with spreads

    Returns:
        SpreadResponse: Updated spread

    Raises:
        HTTPException: If spread is not found
    """
    updated_spread = await spread_service.update_spread(spread_id, spread_input)
    if not updated_spread:
        raise HTTPException(status_code=404, detail="Spread not found")
    return updated_spread

@app.delete("/spreads/{spread_id}", status_code=204)
@rate_limit_by_ip(settings.rate_limit.delete_spread_limit)
async def delete_spread(
    spread_id: str,
    request: Request,  
    spread_service: SpreadService = Depends(get_spread_service),
    _: str = Depends(verify_bot_token),
) -> None:
    """
    Delete spread

    Args:
        spread_id: ID of the spread to delete
        request: FastAPI request
        spread_service: Service for working with spreads

    Raises:
        HTTPException: If spread is not found
    """
    result = await spread_service.delete_spread(spread_id)
    if not result:
        raise HTTPException(status_code=404, detail="Spread not found")
