#!/bin/sh

# Set default port if PORT is not set
PORT=${PORT:-8000}

# Start the Uvicorn server
exec uvicorn lab_api:app --host 0.0.0.0 --port "$PORT"