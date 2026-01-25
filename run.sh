#!/bin/bash

# FrankScore Version 2 - Startup Script
# This script sets up and runs the entire FrankScore application

# Note: We don't use 'set -e' to allow graceful error handling

echo "=========================================="
echo "FrankScore Version 2 - Startup Script"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Python is installed
echo -e "${YELLOW}Checking Python installation...${NC}"

# Determine Python command (try py launcher first for Windows, then python3, then python)
PYTHON_CMD=""
PIP_CMD=""

# Try py launcher (Windows) - test directly since command -v might not work in Git Bash
if py --version >/dev/null 2>&1; then
    PYTHON_VERSION=$(py --version 2>&1)
    if echo "$PYTHON_VERSION" | grep -qi "Python"; then
        PYTHON_CMD="py"
        PIP_CMD="py -m pip"
        echo -e "${GREEN}Found Python (via launcher): $PYTHON_VERSION${NC}"
    fi
# Try python3
elif command -v python3 >/dev/null 2>&1; then
    PYTHON_CMD=python3
    PIP_CMD=pip3
    echo -e "${GREEN}Found Python: $(python3 --version 2>&1)${NC}"
# Try python
elif command -v python >/dev/null 2>&1; then
    PYTHON_VERSION=$(python --version 2>&1)
    if echo "$PYTHON_VERSION" | grep -qi "Python"; then
        PYTHON_CMD=python
        PIP_CMD=pip
        echo -e "${GREEN}Found Python: $PYTHON_VERSION${NC}"
    fi
fi

if [ -z "$PYTHON_CMD" ]; then
    echo -e "${RED}Error: Python is not installed or not in PATH.${NC}"
    echo -e "${YELLOW}Please install Python 3.8+ from https://www.python.org/downloads/${NC}"
    echo -e "${YELLOW}On Windows, make sure Python Launcher (py.exe) is available.${NC}"
    echo -e "${YELLOW}You can test by running: py --version${NC}"
    exit 1
fi

echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    if [ "$PYTHON_CMD" = "py" ]; then
        py -m venv .venv
    else
        $PYTHON_CMD -m venv .venv
    fi
    echo -e "${GREEN}Virtual environment created.${NC}"
else
    echo -e "${GREEN}Virtual environment already exists.${NC}"
fi

echo ""

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
elif [ -f ".venv/Scripts/activate" ]; then
    source .venv/Scripts/activate
else
    echo -e "${RED}Error: Could not find virtual environment activation script.${NC}"
    exit 1
fi

echo -e "${GREEN}Virtual environment activated.${NC}"
echo ""

# Install/upgrade dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
if [ "$PYTHON_CMD" = "py" ]; then
    py -m pip install --upgrade pip
    py -m pip install -r requirements.txt
else
    $PIP_CMD install --upgrade pip
    $PIP_CMD install -r requirements.txt
fi
echo -e "${GREEN}Dependencies installed.${NC}"
echo ""

# Initialize database
echo -e "${YELLOW}Initializing database...${NC}"
if [ "$PYTHON_CMD" = "py" ]; then
    py -c "import db; db.init_db(); print('Database initialized.')"
else
    $PYTHON_CMD -c "import db; db.init_db(); print('Database initialized.')"
fi
echo -e "${GREEN}Database ready.${NC}"
echo ""

# Check if personas need to be seeded
echo -e "${YELLOW}Checking personas...${NC}"
if [ "$PYTHON_CMD" = "py" ]; then
    PERSONA_COUNT=$(py -c "import db; db.init_db(); conn = db.get_conn().__enter__(); cursor = conn.execute('SELECT COUNT(*) FROM users'); print(cursor.fetchone()[0]); conn.__exit__(None, None, None)" 2>/dev/null || echo "0")
else
    PERSONA_COUNT=$($PYTHON_CMD -c "import db; db.init_db(); conn = db.get_conn().__enter__(); cursor = conn.execute('SELECT COUNT(*) FROM users'); print(cursor.fetchone()[0]); conn.__exit__(None, None, None)" 2>/dev/null || echo "0")
fi

if [ "$PERSONA_COUNT" -eq "0" ]; then
    echo -e "${YELLOW}No personas found. Seeding personas...${NC}"
    if [ "$PYTHON_CMD" = "py" ]; then
        py seed_personas.py
    else
        $PYTHON_CMD seed_personas.py
    fi
    echo -e "${GREEN}Personas seeded.${NC}"
else
    echo -e "${GREEN}Personas already exist ($PERSONA_COUNT users).${NC}"
    read -p "Do you want to re-seed personas? This will create duplicates. (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Re-seeding personas...${NC}"
        if [ "$PYTHON_CMD" = "py" ]; then
            py seed_personas.py
        else
            $PYTHON_CMD seed_personas.py
        fi
        echo -e "${GREEN}Personas re-seeded.${NC}"
    fi
fi

echo ""

# Check if model files exist
echo -e "${YELLOW}Checking model files...${NC}"
if [ ! -f "models/random_forest.joblib" ]; then
    echo -e "${RED}Warning: Random Forest model not found at models/random_forest.joblib${NC}"
    echo -e "${YELLOW}The application will use fallback financial PD calculation.${NC}"
else
    echo -e "${GREEN}Random Forest model found.${NC}"
fi

if [ ! -f "models/xgb_model.joblib" ]; then
    echo -e "${YELLOW}Info: XGBoost model not found (optional).${NC}"
else
    echo -e "${GREEN}XGBoost model found.${NC}"
fi

echo ""

# Enable admin dashboard
export ADMIN_MODE=true
echo -e "${GREEN}Admin dashboard enabled (ADMIN_MODE=true)${NC}"

# Configure Hugging Face Spaces API for remote model inference
export HF_API_URL="https://dawittre-frankscore-model-api.hf.space"
echo -e "${GREEN}HF API URL set: $HF_API_URL${NC}"
echo ""

# Start the server
echo "=========================================="
echo -e "${GREEN}Starting FrankScore server...${NC}"
echo "=========================================="
echo ""
echo "Server will be available at:"
echo "  - Main: http://127.0.0.1:8000"
echo "  - Login: http://127.0.0.1:8000/login"
echo "  - Health: http://127.0.0.1:8000/health"
echo "  - Admin Dashboard: http://127.0.0.1:8000/admin"
echo ""
echo "Test credentials (all use 'password123'):"
echo "  - alice, bob, charlie (low risk)"
echo "  - diana, eve, frank (medium risk)"
echo "  - grace, henry, ivy (high risk)"
echo "  - john, jane (new users)"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo ""

# Start uvicorn
uvicorn app:app --reload --port 8000 --host 127.0.0.1

