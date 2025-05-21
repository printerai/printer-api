# printer-api

This is a REST API for managing cryptocurrency arbitrage spread data.


To run the application using Docker:

```bash

docker-compose up -d

docker-compose logs -f

docker-compose down
```

For configuration, you can create a `.env` file and specify environment variables in it (e.g., `LOGFIRE_TOKEN`).


- `GET /spreads` - Get a list of spreads with pagination and filtering (limit: 100 requests per minute)
- `GET /spreads/{spread_id}` - Get spread by ID (limit: 30 requests per minute)
- `POST /spreads` - Create a new spread (limit: 20 requests per minute)
- `PUT /spreads/{spread_id}` - Update spread (limit: 20 requests per minute)
- `GET /exchanges` - Get a list of exchanges
- `DELETE /spreads/{spread_id}` - Delete spread (limit: 10 requests per minute)


- `limit` - Number of records (max 100)
- `offset` - Offset for pagination
- `base` & `quote` - Filter by base and quote currency (e.g., `base=BTC&quote=USDT`)
- `network` - Filter by network (e.g., `network=SOLANA`)
- `from_spread` - Filter by minimum spread percentage (e.g., `from_spread=0.5`)
- `to_spread` - Filter by maximum spread percentage (e.g., `to_spread=2.0`)
- `from_liquidity` - Filter by minimum liquidity (e.g., `from_liquidity=10000.0`)
- `to_liquidity` - Filter by maximum liquidity (e.g., `to_liquidity=500000.0`)
- `from_fdv` - Filter by minimum Fully Diluted Valuation (FDV) (e.g., `from_fdv=1000000.0`)
- `to_fdv` - Filter by maximum Fully Diluted Valuation (FDV) (e.g., `to_fdv=10000000.0`)
- `exchanges` - Filter by provided exchanges separated by "," (e.g. `exchanges=bybit,binance`)
- `sort_by` - Sort by provided key `topSpread`, `liquidity`, `sortFdv`, `sortDays` (e.g. `sort_by=topSpread`)
- `order_by` - Order by `asc` or `desc` (e.g. `order_by=asc`)