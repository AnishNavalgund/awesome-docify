#!/bin/bash

if [ -f /.dockerenv ]; then
    echo "Running in Docker"
    uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
else
    echo "Running locally with uv"
    uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
fi
