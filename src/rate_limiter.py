from typing import Optional

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.config import settings

def get_client_ip(request: Request) -> str:
    """
    Gets the client IP address from the request.
    Takes into account the possibility of request proxying.

    Args:
        request (Request): FastAPI request object

    Returns:
        str: Client IP address
    """
    
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        
        return forwarded_for.split(",")[0].strip()

    
    return get_remote_address(request)


limiter = Limiter(
    key_func=get_client_ip,
    default_limits=settings.rate_limit.default_limits,
    storage_uri=settings.rate_limit.storage_uri,
    storage_options=settings.rate_limit.storage_options,
    strategy="fixed-window",  
)

def rate_limit_by_ip(
    limit_value: str,
) -> callable:
    """
    Decorator to limit requests by IP address.

    Args:
        limit_value (str): Limit string in the format "{count}/{period}"
                          Example: "5/minute", "100/hour", "1000/day"
        per_second_fallback (Optional[int]): Fallback requests per second limit,
                                            if the main limit cannot be applied

    Returns:
        callable: Limit decorator
    """

    def decorator(func):
        
        limited_route = limiter.limit(
            limit_value,
            key_func=get_client_ip,
        )(func)
        return limited_route

    return decorator
