@echo off
REM Launch the Map Image Generator GUI with dependency checking

echo Starting pzmapdzi2img...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo.
    echo This application requires Python 3.8 or newer.
    echo.
    echo To fix this:
    echo 1. Download Python from https://www.python.org/downloads/
    echo 2. During installation, check "Add Python to PATH"
    echo 3. Restart your computer after installation
    echo.
    pause
    exit /b 1
)

python run_gui.py

if errorlevel 1 (
    echo.
    echo Error: Failed to start application
    pause
)
s