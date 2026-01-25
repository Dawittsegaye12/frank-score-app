# Vercel Deployment Status & URLs

## 📍 Your Deployment URLs

Based on your Vercel project name "frank-score-app", your URLs should be:

### Production URL (Main):
```
https://frank-score-app.vercel.app
```

### Deployment-Specific URLs:
Based on your deployment ID `CxqdubSzcqq23jPMVSSSL9yocVC4`:
```
https://frank-score-app-CxqdubSzcqq23jPMVSSSL9yocVC4.vercel.app
```

### Alternative URLs (if project name differs):
- `https://frankscoreapp.vercel.app`
- `https://frankscore.vercel.app`

## 🔍 How to Find Your Exact URL

1. **Go to Vercel Dashboard:**
   - https://vercel.com/dashboard
   - Select your project: "frank-score-app"

2. **Check Deployment:**
   - Go to "Deployments" tab
   - Click on the latest deployment
   - Look for "Domains" section
   - You'll see the exact URL(s)

3. **Or Check Project Settings:**
   - Project → Settings → Domains
   - Shows all assigned domains

## ✅ What's Deployed

### Files Included:
- ✅ `app.py` - Main FastAPI application
- ✅ `api/index.py` - Vercel serverless function entry point
- ✅ `db.py` - Database operations
- ✅ `scoring.py` - Scoring engine (without ML models)
- ✅ `templates/` - HTML templates
- ✅ `static/` - CSS, JS files
- ✅ `questiondb/` - Question bank JSON files
- ✅ `vercel.json` - Deployment configuration
- ✅ `requirements.txt` - Python dependencies (Vercel-compatible)
- ✅ `pyproject.toml` - Python 3.10 specification

### Files Excluded (by .vercelignore):
- ❌ `models/*.joblib` - ML models (too large, use Render)
- ❌ `*.db` - Database files
- ❌ `__pycache__/` - Python cache
- ❌ `.venv/` - Virtual environment

## ⚠️ Important Notes

### ML Models:
- **Not deployed on Vercel** (too large for 50MB limit)
- **Use Render for ML predictions**: `https://frank-score-app.onrender.com`
- Vercel handles frontend and lightweight APIs
- Heavy ML operations should proxy to Render

### Database:
- SQLite is **ephemeral** on Vercel (resets on deploy)
- Consider using Render database or external PostgreSQL

## 🧪 Test Your Deployment

### 1. Health Check:
```bash
curl https://frank-score-app.vercel.app/health
```
Should return: `{"ok": true, "db": "ok"}`

### 2. Home Page:
```bash
curl https://frank-score-app.vercel.app/
```
Should return HTML (login page)

### 3. API Endpoints:
```bash
# Questions API
curl https://frank-score-app.vercel.app/api/questions

# Health check
curl https://frank-score-app.vercel.app/health
```

## 📊 Deployment Status

Check in Vercel Dashboard:
- **Status**: Should be "Ready" (green) or "Building" (yellow)
- **Logs**: Check for any errors
- **Functions**: Should show `api/index.py` as a serverless function

## 🔗 Quick Access

**Vercel Dashboard:**
- Project: https://vercel.com/abeladiss123-1756s-projects/frank-score-app
- Deployments: Check latest deployment status
- Logs: View runtime logs

**Your App:**
- Production: `https://frank-score-app.vercel.app`
- (Check Vercel dashboard for exact URL)

