@echo off
REM FrankScore Version 2 - Windows Batch Startup Script
REM This script sets up and runs the entire FrankScore application

echo ==========================================
echo FrankScore Version 2 - Startup Script
echo ==========================================
echo.

REM Check if Python is installed
echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed. Please install Python 3.8+ first.
    pause
    exit /b 1
)

for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo Found Python: %PYTHON_VERSION%
echo.

REM Check if virtual environment exists
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
    echo Virtual environment created.
) else (
    echo Virtual environment already exists.
)

echo.

REM Activate virtual environment
echo Activating virtual environment...
if exist ".venv\Scripts\activate.bat" (
    call .venv\Scripts\activate.bat
    echo Virtual environment activated.
) else (
    echo Error: Could not find virtual environment activation script.
    pause
    exit /b 1
)

echo.

REM Install/upgrade dependencies
echo Installing dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
echo Dependencies installed.
echo.

REM Initialize database
echo Initializing database...
python -c "import db; db.init_db(); print('Database initialized.')"
echo Database ready.
echo.

REM Check if personas need to be seeded
echo Checking personas...
python -c "import db; db.init_db(); conn = db.get_conn().__enter__(); cursor = conn.execute('SELECT COUNT(*) FROM users'); result = cursor.fetchone()[0]; conn.__exit__(None, None, None); print(result)" > temp_persona_count.txt 2>nul
set /p PERSONA_COUNT=<temp_persona_count.txt
del temp_persona_count.txt

if "%PERSONA_COUNT%"=="0" (
    echo No personas found. Seeding personas...
    python seed_personas.py
    echo Personas seeded.
) else (
    echo Personas already exist (%PERSONA_COUNT% users).
    set /p RESEED="Do you want to re-seed personas? This will create duplicates. (y/N): "
    if /i "%RESEED%"=="y" (
        echo Re-seeding personas...
        python seed_personas.py
        echo Personas re-seeded.
    )
)

echo.

REM Check if model files exist
echo Checking model files...
if not exist "models\random_forest.joblib" (
    echo Warning: Random Forest model not found at models\random_forest.joblib
    echo The application will use fallback financial PD calculation.
) else (
    echo Random Forest model found.
)

if not exist "models\xgb_model.joblib" (
    echo Info: XGBoost model not found (optional).
) else (
    echo XGBoost model found.
)

echo.

REM Enable admin dashboard
set ADMIN_MODE=true
echo Admin dashboard enabled (ADMIN_MODE=true)
echo.

REM Start the server
echo ==========================================
echo Starting FrankScore server...
echo ==========================================
echo.
echo Server will be available at:
echo   - Main: http://127.0.0.1:8000
echo   - Login: http://127.0.0.1:8000/login
echo   - Health: http://127.0.0.1:8000/health
echo   - Admin Dashboard: http://127.0.0.1:8000/admin
echo.
echo Test credentials (all use 'password123'):
echo   - alice, bob, charlie (low risk)
echo   - diana, eve, frank (medium risk)
echo   - grace, henry, ivy (high risk)
echo   - john, jane (new users)
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start uvicorn
uvicorn app:app --reload --port 8000 --host 127.0.0.1

