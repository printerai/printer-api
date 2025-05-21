import os
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class RateLimitConfig(BaseModel):
    """Route rate limit configuration"""

    default_limits: List[str] = ["200/day", "50/hour", "5/minute"]

    
    get_spreads_limit: str = "50/minute"
    get_spread_limit: str = "30/minute"
    create_spread_limit: str = "20/minute"
    update_spread_limit: str = "20/minute"
    delete_spread_limit: str = "10/minute"

    
    storage_uri: str = "memory://"  
    redis_timeout: int = 30  

    @field_validator("storage_uri")
    def validate_storage_uri(cls, v: str) -> str:
        """Validate storage URI"""
        if v.startswith("redis://"):
            return v
        if v == "memory://":
            return v
        
        return "memory://"

    @property
    def storage_options(self) -> Dict[str, Union[str, int]]:
        """Get storage parameters"""
        if self.storage_uri.startswith("redis://"):
            return {"socket_connect_timeout": self.redis_timeout}
        return {}

class Settings(BaseSettings):
    """Main application settings"""

    
    database_url: str = "sqlite+aiosqlite:////app/data/arbitrage.db"

    
    api_title: str = "Arbitrage CRUD API"
    api_description: str = "REST API for managing cryptocurrency arbitrage spread data"
    api_version: str = "0.1.0"

    
    rate_limit: RateLimitConfig = RateLimitConfig()

    
    debug: bool = False

    
    logfire_token: Optional[str] = None

    bot_token: Optional[str] = None

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )


settings = Settings()
