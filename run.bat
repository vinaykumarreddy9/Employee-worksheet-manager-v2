@echo off
TITLE Employee Timesheet Manager Launcher
echo ===================================================
echo   Employee Timesheet Manager - Professional
echo ===================================================
echo.

:: Check for venv
if not exist "venv\Scripts\activate" (
    echo [ERROR] Virtual environment 'venv' not found.
    echo Please create it using: python -m venv venv
    pause
    exit /b
)

echo [1/2] Starting FastAPI Backend on http://localhost:8000...
start "Timesheet Backend" cmd /k "call venv\Scripts\activate && set PYTHONPATH=. && python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"

echo [2/2] Starting Streamlit Frontend on http://localhost:8501...
start "Timesheet Frontend" cmd /k "call venv\Scripts\activate && set PYTHONPATH=. && streamlit run frontend/app.py"

echo.
echo ===================================================
echo   System is launching in separate windows...
echo   Close those windows to stop the services.
echo ===================================================
echo.
pause
