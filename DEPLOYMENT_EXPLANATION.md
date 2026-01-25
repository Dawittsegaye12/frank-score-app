# How Your App is Deployed on Render

## Overview

Your FrankScore app is deployed on **Render** using a configuration file (`render.yaml`) that tells Render how to build and run your application. Here's the complete deployment process:

## 📋 Deployment Configuration

### File: `render.yaml`

This is the main configuration file that Render reads:

```yaml
services:
  - type: web                    # Web service (not a background worker)
    name: frankscore-app         # Name of your service
    env: python                  # Python environment
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHON_VERSION
        value: 3.10.0
      - key: SCORING_API_URL
        value: https://frankscore-backend.onrender.com
      # ... other environment variables
```

## 🔄 Complete Deployment Process

### Step 1: Connect Repository to Render

1. **Push code to Git** (GitHub, GitLab, or Bitbucket)
2. **Connect to Render:**
   - Go to Render Dashboard
   - Click "New" → "Web Service"
   - Connect your Git repository
   - Render detects `render.yaml` automatically

### Step 2: Build Phase

When you push code or trigger a deploy, Render:

```
1. Clones your Git repository
   └─→ Gets all files from your repo

2. Sets up Python environment
   └─→ Uses Python 3.10.0 (from render.yaml)
   └─→ Creates virtual environment

3. Installs dependencies
   └─→ Runs: pip install -r requirements.txt
   └─→ Installs all packages:
       - fastapi==0.115.6
       - uvicorn[standard]==0.30.6
       - xgboost>=2.0.0
       - scikit-learn>=1.0.0
       - ... and 10+ more packages

4. Build completes
   └─→ All dependencies installed
   └─→ Ready to start application
```

**Build Logs Show:**
```
Collecting fastapi==0.115.6
Collecting uvicorn[standard]==0.30.6
...
Successfully installed fastapi-0.115.6 uvicorn-0.30.6 ...
```

### Step 3: Runtime Phase

After build, Render starts your application:

```
1. Runs start command
   └─→ uvicorn app:app --host 0.0.0.0 --port $PORT
   
2. Application startup sequence:
   └─→ FastAPI app loads (app.py)
   └─→ Startup event triggers (@app.on_event("startup"))
   └─→ Database initializes (db.init_db())
   └─→ Question banks load (load_question_banks())
   └─→ Models ready (lazy loading - load on first use)
   
3. Server starts listening
   └─→ On port $PORT (Render assigns automatically)
   └─→ On host 0.0.0.0 (accepts all connections)
   
4. Application is LIVE! 🚀
   └─→ Available at: https://frank-score-app.onrender.com
```

**Runtime Logs Show:**
```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:PORT (Press CTRL+C to quit)
```

## 📁 What Gets Deployed

### Files Included

Render deploys **everything** in your Git repository:

```
frank-score-app/
├── app.py                          ✅ Main application
├── db.py                           ✅ Database operations
├── scoring.py                      ✅ Scoring engine
├── admin_data_dual_models.py       ✅ Admin dashboard
├── requirements.txt                ✅ Dependencies list
├── render.yaml                     ✅ Deployment config
├── models/
│   ├── xgb_model.joblib           ✅ XGBoost model
│   └── random_forest.joblib        ✅ Random Forest model
├── questiondb/
│   ├── psychometric_question_bank_v2_public.json
│   └── psychometric_question_bank_v2_admin.json
├── templates/                      ✅ HTML templates
├── static/                         ✅ CSS, JS files
├── services/
│   └── scoring_api.py              ✅ External API client
└── explainability/                 ✅ SHAP/LIME services
```

### Files NOT Included (Git ignored)

- `.venv/` - Virtual environment (created fresh on Render)
- `__pycache__/` - Python cache (recreated)
- `*.db` - SQLite database (created fresh on Render)
- `.cursor/` - Editor files

## 🔧 How Render Runs Your App

### Start Command Breakdown

```bash
uvicorn app:app --host 0.0.0.0 --port $PORT
```

**What this means:**
- `uvicorn` - ASGI server (runs FastAPI)
- `app:app` - Module `app.py`, variable `app` (your FastAPI instance)
- `--host 0.0.0.0` - Listen on all network interfaces
- `--port $PORT` - Use port from Render environment variable

### Application Startup Flow

```python
# 1. Render runs: uvicorn app:app ...

# 2. Python loads app.py
from fastapi import FastAPI
app = FastAPI(title="frankscore_demo")

# 3. Startup event fires
@app.on_event("startup")
def _startup():
    db.init_db()              # Creates SQLite database
    load_question_banks()     # Loads question JSON files
    # Models load lazily (on first use)

# 4. Server starts listening
# Ready to accept HTTP requests!
```

## 🌐 How Requests Work

### Request Flow

```
User Browser
    ↓
HTTPS Request: https://frank-score-app.onrender.com/api/start
    ↓
Render Load Balancer
    ↓
Your Application Container
    ↓
FastAPI Router (app.py)
    ↓
@app.post("/api/start")
    ↓
Handler Function
    ↓
Response: {"assessment_id": "FS000001", "session_id": "..."}
    ↓
Back to User Browser
```

### Example Request

```bash
# User makes request
POST https://frank-score-app.onrender.com/api/start
Content-Type: application/json
{"user_id": "1"}

# Render routes to your app
# FastAPI handles it
@app.post("/api/start")
def api_start(req: StartRequest):
    # ... process request ...
    return {"assessment_id": "FS000001", "session_id": "abc123"}

# Response sent back
HTTP 200 OK
{"assessment_id": "FS000001", "session_id": "abc123"}
```

## 🔐 Environment Variables

### Set in `render.yaml`:

```yaml
envVars:
  - key: PYTHON_VERSION
    value: 3.10.0              # Python version to use
  
  - key: SCORING_API_URL
    value: https://frankscore-backend.onrender.com
  
  - key: TENANT_CLIENT_ID
    sync: false                 # Set manually in Render dashboard
  
  - key: TENANT_CLIENT_SECRET
    sync: false                 # Set manually in Render dashboard
  
  - key: TENANT_HMAC_SECRET
    sync: false                 # Set manually in Render dashboard
```

### How to Set Manual Variables:

1. Go to Render Dashboard
2. Select your service
3. Go to "Environment" tab
4. Add variables:
   - `TENANT_CLIENT_ID` = your_client_id
   - `TENANT_CLIENT_SECRET` = your_secret
   - `TENANT_HMAC_SECRET` = your_hmac_secret
   - `ADMIN_MODE` = true (optional)

## 📊 Deployment States

### 1. **Building**
```
Status: Building
- Cloning repository
- Installing dependencies
- Preparing environment
```

### 2. **Deploying**
```
Status: Deploying
- Starting application
- Running startup sequence
- Health checks
```

### 3. **Live**
```
Status: Live
✅ Application running
✅ Accepting requests
✅ All endpoints available
```

### 4. **Sleeping** (Free Tier)
```
Status: Live (but sleeping)
⚠️ App spun down after 15 min inactivity
⏱️ Next request will wake it up (30-60 seconds)
```

## 🔄 Auto-Deployment

### How It Works:

1. **You push to Git:**
   ```bash
   git add .
   git commit -m "Update feature"
   git push
   ```

2. **Render detects change:**
   - Monitors your Git repository
   - Detects new commit
   - Triggers automatic deployment

3. **Deployment happens:**
   - Builds new version
   - Tests health endpoint
   - Switches to new version
   - Old version stops

### Manual Deployment:

You can also manually trigger:
- Render Dashboard → Your Service → "Manual Deploy"
- Choose branch/commit
- Deploy

## 🗄️ Database on Render

### SQLite Database

```python
# In db.py
DB_PATH = "frankscore_demo.db"

# On Render:
# - Database file created in container
# - Persists while container is running
# - ⚠️ RESETS on each deploy (ephemeral storage)
```

**Important:** SQLite on Render is **ephemeral** - data resets on each deploy!

**For production:** Use Render PostgreSQL (persistent database)

## 📦 Dependencies Installation

### `requirements.txt` is used:

```txt
fastapi==0.115.6
uvicorn[standard]==0.30.6
jinja2==3.1.4
pydantic==2.9.2
joblib>=1.3.0
xgboost>=2.0.0
numpy>=1.24.0
pandas>=1.5.0
scikit-learn>=1.0.0
shap>=0.41.0
lime>=0.2.0.1
requests>=2.31.0
gunicorn==22.0.0
python-multipart==0.0.9
```

**Render runs:**
```bash
pip install -r requirements.txt
```

**This installs:**
- All Python packages
- ML libraries (XGBoost, scikit-learn)
- Web framework (FastAPI, Uvicorn)
- Dependencies of dependencies

## 🚀 Complete Deployment Timeline

```
Time    | Action
--------|--------------------------------------------------
00:00   | You push code to Git
00:05   | Render detects change
00:10   | Build starts
        |   - Clone repository
        |   - Setup Python 3.10.0
        |   - Install dependencies (2-5 minutes)
00:15   | Build completes
00:16   | Deploy starts
        |   - Start uvicorn server
        |   - Run startup sequence
        |   - Health check
00:20   | ✅ LIVE!
        |   - Available at: https://frank-score-app.onrender.com
```

## 🔍 How to Check Deployment

### 1. Render Dashboard
- View build logs
- View runtime logs
- Check deployment status
- Monitor health

### 2. Health Endpoint
```bash
curl https://frank-score-app.onrender.com/health
# Should return: {"ok": true, "db": "ok"}
```

### 3. Application Logs
Render Dashboard → Logs tab shows:
- Build output
- Runtime output
- Print statements
- Errors

## 🛠️ Troubleshooting

### Build Fails
- Check `requirements.txt` for errors
- Verify Python version compatibility
- Check build logs for specific errors

### App Crashes
- Check runtime logs
- Verify all files are in Git repo
- Check for missing dependencies

### Slow Startup
- Normal for free tier (cold starts)
- Models load lazily (optimized)
- First request may be slow

## 📝 Summary

**Your deployment works like this:**

1. ✅ **Code in Git** → Render monitors repository
2. ✅ **Push code** → Render detects change
3. ✅ **Build phase** → Install dependencies from `requirements.txt`
4. ✅ **Runtime phase** → Run `uvicorn app:app` command
5. ✅ **Startup** → Initialize database, load question banks
6. ✅ **Live** → Accept HTTP requests at your Render URL
7. ✅ **Auto-deploy** → New pushes trigger automatic deployments

**Key Files:**
- `render.yaml` - Tells Render how to deploy
- `requirements.txt` - Lists all dependencies
- `app.py` - Main application entry point
- `uvicorn` - Web server that runs your app

That's how your app is deployed! 🚀

