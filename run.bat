@echo off
REM Activate virtual environment and run the tool

if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat
    python meter_aggregator.py
) else (
    echo Virtual environment not found. Please run: python -m venv .venv
    exit /b 1
)
