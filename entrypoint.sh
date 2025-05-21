
set -e 

DB_FILE="/app/data/arbitrage.db"



echo "Running entrypoint script..."
echo "DB_FILE is ${DB_FILE}"

mkdir -p /app/data
echo "Ensured /app/data directory exists."
ls -ld /app/data 

NEEDS_INITIALIZATION=false
if [ ! -f "${DB_FILE}" ]; then
    echo "Database file ${DB_FILE} not found. Will attempt to create and initialize."
    
    echo "Attempting to touch ${DB_FILE} to check write permissions..."
    touch "${DB_FILE}"
    if [ $? -ne 0 ]; then
        echo "ERROR: Could not create touch file at ${DB_FILE}. Check permissions for /app/data (host's ./data directory)."
        echo "Listing /app contents:"
        ls -l /app
        echo "Listing /app/data contents:"
        ls -l /app/data
        exit 1
    fi
    echo "Successfully touched ${DB_FILE}."
    NEEDS_INITIALIZATION=true
else
    echo "Database file ${DB_FILE} found."
    ls -l "${DB_FILE}" 
fi

echo "Attempting to upgrade database to head using Alembic..."

cd /app 
alembic -c /app/alembic.ini upgrade head 

alembic upgrade head
if [ $? -ne 0 ]; then
    echo "ERROR: alembic upgrade head failed."
    echo "Listing /app contents:"
    ls -l /app
    echo "Listing /app/data contents:"
    ls -l /app/data
    
    if [ -f "/app/alembic.ini" ]; then
        echo "Alembic script_location:"
        grep "script_location" /app/alembic.ini
    fi
    exit 1
fi
echo "Database upgrade successful or no new migrations."






echo "Starting Uvicorn server..."
exec uvicorn src.main:app --host 0.0.0.0 --port 8000