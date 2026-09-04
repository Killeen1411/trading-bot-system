#!/bin/bash
set -e

# Start dashboard in background
uvicorn dashboard.main:app --host 0.0.0.0 --port ${PORT:-8000} &
DASH_PID=$!

# Start bot in foreground (keeps container alive)
python -m bot.main

# If bot exits, kill dashboard too
kill $DASH_PID 2>/dev/null || true
