@echo off
cd /d "%~dp0"
echo ========================================
echo   AI Multi-Code Converter
echo   Starting Backend and Frontend...
echo ========================================
echo.

REM Check if .env exists
if not exist .env (
    echo [ERROR] .env file not found!
    echo Please create a .env file with your GROQ_API_KEY
    echo Example: GROQ_API_KEY=your_key_here
    echo.
    pause
    exit /b 1
)

echo [1/3] Checking Python dependencies...
python -c "import fastapi" 2>nul
if errorlevel 1 (
    echo Installing Python dependencies...
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install Python dependencies.
        echo Please check your internet connection and Python installation.
        pause
        exit /b 1
    )
) else (
    echo Dependencies already installed, skipping...
)

echo.
echo [2/3] Starting Backend Server...
start "Backend Server" cmd /k "python backend.py"
timeout /t 3 /nobreak > nul

echo.
echo [3/3] Starting Frontend Server...
cd frontend
start "Frontend Server" cmd /k "npm run dev"
cd ..

echo.
echo ========================================
echo   Servers Started Successfully!
echo ========================================
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:3000
echo ========================================
echo.
echo Opening browser...
start "" "http://localhost:3000"
echo.
echo Press any key to stop all servers...
pause > nul

echo Stopping servers...
taskkill /FI "WindowTitle eq Backend Server*" /T /F > nul 2>&1
taskkill /FI "WindowTitle eq Frontend Server*" /T /F > nul 2>&1
echo Servers stopped.
