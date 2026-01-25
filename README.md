# frankscore_demo (minimal FastAPI + SQLite + vanilla JS demo)

Demo-ready flow:
1. Consent (`/terms`)
2. 10-question questionnaire + real-time telemetry (`/questions`)
3. Optional financial inputs (`/financial`)
4. Scoring + PD computation + results (`/result`)

## Run locally

### Quick Start (Recommended)

**On Linux/Mac/Git Bash:**
```bash
./run.sh
```

**On Windows (PowerShell):**
```powershell
.\run.ps1
```

**On Windows (Command Prompt):**
```cmd
run.bat
```

The script will automatically:
1. Check Python installation
2. Create and activate virtual environment
3. Install dependencies
4. Initialize database
5. Seed personas (if needed)
6. Start the server

### Manual Setup

If you prefer manual setup:

```bash
python -m venv .venv
```

Activate (PowerShell):
```powershell
.venv\Scripts\Activate.ps1
```

Activate (Linux/Mac):
```bash
source .venv/bin/activate
```

Install deps:
```bash
pip install -r requirements.txt
```

Initialize database and seed personas:
```bash
python -c "import db; db.init_db()"
python seed_personas.py
```

Run:
```bash
uvicorn app:app --reload --port 8000
```

Open:
- `http://127.0.0.1:8000` (redirects to login)
- `http://127.0.0.1:8000/login`
- Health check: `http://127.0.0.1:8000/health`

## Admin Dashboard

The admin dashboard provides monitoring for model performance, data drift, API uptime, and fairness metrics.

### Accessing the Admin Dashboard

**Enable admin mode:**
```bash
# Windows PowerShell
$env:ADMIN_MODE="true"
uvicorn app:app --reload

# Linux/Mac
export ADMIN_MODE=true
uvicorn app:app --reload
```

Then visit:
- `http://127.0.0.1:8000/admin` - Overview
- `http://127.0.0.1:8000/admin/performance` - Model Performance
- `http://127.0.0.1:8000/admin/drift` - Data Drift
- `http://127.0.0.1:8000/admin/uptime` - API Uptime & Health
- `http://127.0.0.1:8000/admin/fairness` - Fairness Metrics

**Note:** The admin dashboard currently uses mock data. In production, this would be replaced with real database queries and calculations.

## What gets created

- **SQLite DB**: `frankscore_demo.db` in the project root (auto-created on first run).
- **Tables**: attempts, responses, events, financial, computed (see `db.py`).

## Notes

- The demo **starts without a psychometric consent checkbox** (your request). It still collects questionnaire + telemetry to compute scores.
- Telemetry events are buffered in the browser and posted to `/api/events` every ~3 seconds or 30 events, plus a best-effort flush on unload.
- Scoring is demo-but-real: metadata aggregation → 15 trait scores → psychometric PD → optional financial PD → combined PD.

## Using your own psychometric questions

Edit `data/questions.json` (format: `[{ "item_id": "Q1", "text": "..." }, ...]`). The app serves these via `GET /api/questions`.


