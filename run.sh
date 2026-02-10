#!/bin/bash
# Activate virtual environment and run the tool

if [ -d ".venv" ]; then
    source .venv/bin/activate
else
    echo "Virtual environment not found. Please run: python3 -m venv .venv"
    exit 1
fi

python meter_aggregator.py
