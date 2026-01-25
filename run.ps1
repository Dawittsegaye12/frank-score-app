# FrankScore Version 2 - PowerShell Startup Script
# This script sets up and runs the entire FrankScore application

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "FrankScore Version 2 - Startup Script" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
Write-Host "Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Error: Python is not installed. Please install Python 3.8+ first." -ForegroundColor Red
    exit 1
}

Write-Host ""

# Check if virtual environment exists
if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
    Write-Host "Virtual environment created." -ForegroundColor Green
} else {
    Write-Host "Virtual environment already exists." -ForegroundColor Green
}

Write-Host ""

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
if (Test-Path ".venv\Scripts\Activate.ps1") {
    & .venv\Scripts\Activate.ps1
    Write-Host "Virtual environment activated." -ForegroundColor Green
} else {
    Write-Host "Error: Could not find virtual environment activation script." -ForegroundColor Red
    exit 1
}

Write-Host ""

# Install/upgrade dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
Write-Host "Dependencies installed." -ForegroundColor Green
Write-Host ""

# Initialize database
Write-Host "Initializing database..." -ForegroundColor Yellow
python -c "import db; db.init_db(); print('Database initialized.')"
Write-Host "Database ready." -ForegroundColor Green
Write-Host ""

# Check if personas need to be seeded
Write-Host "Checking personas..." -ForegroundColor Yellow
try {
    $personaCheck = python -c "import db; db.init_db(); conn = db.get_conn().__enter__(); cursor = conn.execute('SELECT COUNT(*) FROM users'); result = cursor.fetchone()[0]; conn.__exit__(None, None, None); print(result)" 2>&1
    if ($LASTEXITCODE -eq 0 -and $personaCheck -match '^\d+$') {
        $personaCount = [int]$personaCheck
    } else {
        $personaCount = 0
    }
} catch {
    $personaCount = 0
}

if ([int]$personaCount -eq 0) {
    Write-Host "No personas found. Seeding personas..." -ForegroundColor Yellow
    python seed_personas.py
    Write-Host "Personas seeded." -ForegroundColor Green
} else {
    Write-Host "Personas already exist ($personaCount users)." -ForegroundColor Green
    $response = Read-Host "Do you want to re-seed personas? This will create duplicates. (y/N)"
    if ($response -eq "y" -or $response -eq "Y") {
        Write-Host "Re-seeding personas..." -ForegroundColor Yellow
        python seed_personas.py
        Write-Host "Personas re-seeded." -ForegroundColor Green
    }
}

Write-Host ""

# Check if model files exist
Write-Host "Checking model files..." -ForegroundColor Yellow
if (-not (Test-Path "models\random_forest.joblib")) {
    Write-Host "Warning: Random Forest model not found at models\random_forest.joblib" -ForegroundColor Red
    Write-Host "The application will use fallback financial PD calculation." -ForegroundColor Yellow
} else {
    Write-Host "Random Forest model found." -ForegroundColor Green
}

if (-not (Test-Path "models\xgb_model.joblib")) {
    Write-Host "Info: XGBoost model not found (optional)." -ForegroundColor Yellow
} else {
    Write-Host "XGBoost model found." -ForegroundColor Green
}

Write-Host ""

# Enable admin dashboard
$env:ADMIN_MODE = "true"
Write-Host "Admin dashboard enabled (ADMIN_MODE=true)" -ForegroundColor Green
Write-Host ""

# Start the server
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Starting FrankScore server..." -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Server will be available at:"
Write-Host "  - Main: http://127.0.0.1:8000"
Write-Host "  - Login: http://127.0.0.1:8000/login"
Write-Host "  - Health: http://127.0.0.1:8000/health"
Write-Host "  - Admin Dashboard: http://127.0.0.1:8000/admin"
Write-Host ""
Write-Host "Test credentials (all use 'password123'):"
Write-Host "  - alice, bob, charlie (low risk)"
Write-Host "  - diana, eve, frank (medium risk)"
Write-Host "  - grace, henry, ivy (high risk)"
Write-Host "  - john, jane (new users)"
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Start uvicorn
uvicorn app:app --reload --port 8000 --host 127.0.0.1

