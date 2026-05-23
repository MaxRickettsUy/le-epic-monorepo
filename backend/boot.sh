#!/bin/bash
# this script is used to boot a Docker container
MAX_RETRIES=5
attempt=1
while true; do
    alembic -c migrations/alembic.ini upgrade head && break
    if [[ "$attempt" -ge "$MAX_RETRIES" ]]; then
        echo "Migration failed after $attempt attempts, giving up." >&2
        exit 1
    fi
    echo "Migration command failed (attempt $attempt/$MAX_RETRIES), retrying in 5 secs..."
    attempt=$((attempt + 1))
    sleep 5
done
exec uvicorn app:app --host 0.0.0.0 --port 5000
