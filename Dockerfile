FROM python:3.12-slim

WORKDIR /app

RUN pip install --no-cache-dir uv fastapi uvicorn sqlalchemy alembic aiosqlite slowapi logfire pydantic-settings logfire[fastapi,sqlite3]

COPY . .

RUN mkdir -p /app/data && chmod 777 /app/data






COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]
