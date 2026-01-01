@echo off
echo ============================================================
echo ORION OS - Starting Backend Server
echo ============================================================
echo.
echo This will start the Python Flask backend server on port 5000
echo.
echo Press Ctrl+C to stop the server
echo ============================================================
echo.

cd /d "%~dp0"

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.11 or higher
    pause
    exit /b 1
)

REM Check if required packages are installed
python -c "import flask" >nul 2>&1
if errorlevel 1 (
    echo Installing required Python packages...
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
)

REM Start the backend server (with TTS disabled by default for stability)
echo Starting backend server...
echo.
set ORION_DISABLE_TTS=1
python scripts\api_server.py

pause
