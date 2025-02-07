#!/bin/sh

# Wait until Postgres is ready
POSTGRES_PORT=5432
PG_ADDR=$POSTGRES_ADDRESS

while ! nc -z "$PG_ADDR" "$POSTGRES_PORT"; do sleep 1; done

# Run migrations
# alembic upgrade head

# Run the bot
# exec python3 bot.py
exec python3 run_bot.py