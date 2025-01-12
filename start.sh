#!/bin/sh

# Wait until Postgres is ready
POSTGRES_PORT=5432
PG_ADDR=$POSTGRES_ADDRESS

while ! nc -z "$PG_ADDR" "$POSTGRES_PORT"; do sleep 1; done

# Run migrations
alembic upgrade head

# Check if initial data collection has been done
INIT_FLAG="/app/.init_data_collected"
if [ ! -f "$INIT_FLAG" ]; then
    echo "Running psychological tests creation..."

    # Add psychological tests to database
    python3 psycho_tests_creation/add_tests_to_db.py
    python3 psycho_tests_creation/add_test_thomas_kilmann.py
    python3 psycho_tests_creation/add_test_critical_thinking.py

    # Create the flag file to indicate initial collection is done
    touch "$INIT_FLAG"
else
    echo "Initial data already collected. Skipping..."
fi

# Run the app
# exec python3 run_main.py  
exec python3 main.py