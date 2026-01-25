# Deploying FrankScore App on Vercel

## ⚠️ Important Considerations

Vercel is designed for serverless functions and has some limitations for FastAPI apps with ML models:

### Limitations:
- ⚠️ **Function timeout**: 60 seconds max (Pro plan) / 10 seconds (Free)
- ⚠️ **Package size**: 50MB limit (ML models may exceed this)
- ⚠️ **SQLite**: Ephemeral storage (resets on each deploy)
- ⚠️ **Cold starts**: First request can be slow
- ⚠️ **Memory**: Limited to 3GB (Pro plan)

### Recommended Approach:
**Hybrid Deployment**: Use Vercel for frontend/lightweight API, proxy heavy operations to Render.

---

## 🚀 Quick Deployment

### Step 1: Install Vercel CLI

```bash
npm install -g vercel
```

Or use the Vercel Desktop app.

### Step 2: Login to Vercel

```bash
vercel login
```

### Step 3: Deploy

```bash
# From your project directory
vercel
```

Follow the prompts:
- Set up and deploy? **Yes**
- Which scope? **Your account**
- Link to existing project? **No** (first time)
- Project name? **frank-score-app** (or your choice)
- Directory? **./** (current directory)
- Override settings? **No**

### Step 4: Production Deploy

```bash
vercel --prod
```

---

## 📋 Configuration Files

### `vercel.json`

Already configured! This file tells Vercel:
- How to build your app
- Route all requests to `api/index.py`
- Set function timeout and memory limits

### `api/index.py`

Serverless function entry point that:
- Imports your FastAPI app
- Wraps it with Mangum (ASGI adapter)
- Handles all requests

### `vercel-requirements.txt`

Python dependencies for Vercel. **Note**: Some large packages (XGBoost, scikit-learn) may need to be removed or use external API.

---

## 🔧 Setup Options

### Option 1: Full Deployment (All on Vercel)

**Pros:**
- ✅ Single platform
- ✅ Fast global CDN
- ✅ Automatic SSL

**Cons:**
- ⚠️ ML models may be too large
- ⚠️ SQLite resets on deploy
- ⚠️ Function timeout limits

**Steps:**
1. Ensure all dependencies fit in `vercel-requirements.txt`
2. Deploy: `vercel --prod`
3. Set environment variables in Vercel dashboard

### Option 2: Hybrid (Recommended) ✅

**Pros:**
- ✅ Best of both worlds
- ✅ Vercel for frontend/static
- ✅ Render for heavy ML operations
- ✅ No size/timeout limits for ML

**Cons:**
- ⚠️ Two services to manage

**Steps:**
1. Keep app on Render (for ML predictions)
2. Deploy frontend to Vercel
3. Proxy API calls to Render
4. Use Vercel for static files

### Option 3: Vercel + External Services

**Pros:**
- ✅ Scalable
- ✅ Persistent database
- ✅ No size limits

**Cons:**
- ⚠️ More complex setup
- ⚠️ Additional costs

**Steps:**
1. Use external database (PostgreSQL, MongoDB)
2. Use external ML API (Render, AWS Lambda)
3. Deploy frontend to Vercel

---

## 🔐 Environment Variables

Set these in Vercel Dashboard → Settings → Environment Variables:

### Required:
```
PYTHON_VERSION=3.10
```

### Optional (if using external services):
```
RENDER_API_URL=https://frank-score-app.onrender.com
SCORING_API_URL=https://frankscore-backend.onrender.com
TENANT_CLIENT_ID=your_client_id
TENANT_CLIENT_SECRET=your_secret
TENANT_HMAC_SECRET=your_hmac_secret
ADMIN_MODE=true
```

### Database (if using external):
```
DATABASE_URL=postgresql://user:pass@host:5432/dbname
```

---

## 📦 Package Size Optimization

### Check Package Size

```bash
# Install dependencies locally
pip install -r vercel-requirements.txt

# Check size
du -sh .venv/lib/python3.10/site-packages/
```

### If Too Large:

1. **Remove ML packages** (use external API):
   ```txt
   # Comment out in vercel-requirements.txt:
   # xgboost>=2.0.0
   # scikit-learn>=1.0.0
   # shap>=0.41.0
   ```

2. **Proxy ML operations to Render**:
   - Keep Render deployment for `/api/complete`
   - Vercel handles frontend and lightweight APIs

3. **Use smaller alternatives**:
   - Lightweight ML libraries
   - Pre-computed models
   - External ML services

---

## 🗄️ Database Considerations

### SQLite on Vercel

**Problem**: SQLite file is ephemeral (resets on deploy)

**Solutions**:

1. **Use External Database** (Recommended):
   - PostgreSQL (Vercel Postgres, Supabase, Neon)
   - MongoDB Atlas
   - PlanetScale (MySQL)

2. **Use Vercel KV** (Redis):
   - For session storage
   - Not for full database

3. **Proxy to Render**:
   - Keep database on Render
   - Vercel proxies API calls

### Example: Using Vercel Postgres

```python
# In db.py, add PostgreSQL support
import os
import psycopg2

DATABASE_URL = os.getenv("DATABASE_URL")

def get_conn():
    return psycopg2.connect(DATABASE_URL)
```

---

## 🚀 Deployment Steps

### Method 1: Vercel CLI

```bash
# 1. Install Vercel CLI
npm install -g vercel

# 2. Login
vercel login

# 3. Deploy
vercel

# 4. Production deploy
vercel --prod
```

### Method 2: GitHub Integration

1. **Connect GitHub**:
   - Go to https://vercel.com
   - Click "New Project"
   - Import from GitHub
   - Select your repository

2. **Configure**:
   - Framework Preset: **Other**
   - Root Directory: **./**
   - Build Command: (leave empty, Vercel auto-detects)
   - Output Directory: (leave empty)

3. **Environment Variables**:
   - Add all required variables
   - Set for Production, Preview, Development

4. **Deploy**:
   - Click "Deploy"
   - Vercel builds and deploys automatically

### Method 3: Vercel Desktop App

1. Download Vercel Desktop
2. Login
3. Add project from Git
4. Deploy

---

## 🔍 Testing Deployment

### 1. Check Health Endpoint

```bash
curl https://your-app.vercel.app/health
```

Should return:
```json
{"ok": true, "db": "ok"}
```

### 2. Test API Endpoints

```bash
# Test questions API
curl https://your-app.vercel.app/api/questions

# Test start endpoint
curl -X POST https://your-app.vercel.app/api/start \
  -H "Content-Type: application/json" \
  -d '{"user_id": "1"}'
```

### 3. Check Logs

Vercel Dashboard → Your Project → Deployments → Click deployment → Functions → View logs

---

## 🐛 Troubleshooting

### Issue: "Module not found"

**Solution:**
- Check `vercel-requirements.txt` includes all dependencies
- Ensure package names are correct
- Rebuild: `vercel --prod --force`

### Issue: "Function timeout"

**Solution:**
- Increase timeout in `vercel.json` (max 60s on Pro)
- Move heavy operations to external API
- Optimize code

### Issue: "Package too large"

**Solution:**
- Remove large packages (XGBoost, scikit-learn)
- Use external ML API
- Split into multiple functions

### Issue: "Database errors"

**Solution:**
- Use external database (PostgreSQL)
- Or proxy database operations to Render
- Check connection strings

### Issue: "Static files not loading"

**Solution:**
- Check `vercel.json` routes
- Ensure files are in `static/` directory
- Check file paths in templates

---

## 📊 Vercel vs Render Comparison

| Feature | Vercel | Render |
|---------|--------|--------|
| **Python Support** | ✅ Serverless | ✅ Full |
| **ML Models** | ⚠️ Size limits | ✅ No limits |
| **Database** | ⚠️ Ephemeral | ⚠️ Ephemeral (SQLite) |
| **Cold Starts** | ⚠️ Yes | ⚠️ Yes (free tier) |
| **Function Timeout** | ⚠️ 60s max | ✅ No limit |
| **Global CDN** | ✅ Yes | ⚠️ Limited |
| **Free Tier** | ✅ Generous | ✅ Available |
| **Best For** | Frontend/API | Full-stack apps |

---

## 🎯 Recommended Setup

### For Your App:

**Best Approach: Hybrid**

1. **Vercel**: Frontend, static files, lightweight APIs
2. **Render**: ML predictions, database, heavy operations
3. **Proxy**: Vercel proxies `/api/complete` to Render

**Benefits:**
- ✅ Fast frontend delivery (Vercel CDN)
- ✅ No ML model size limits (Render)
- ✅ Persistent database (Render)
- ✅ Best performance

---

## 📝 Next Steps

1. ✅ **Choose deployment option** (Hybrid recommended)
2. ✅ **Set up environment variables**
3. ✅ **Deploy to Vercel**
4. ✅ **Test all endpoints**
5. ✅ **Monitor logs**
6. ✅ **Set up custom domain** (optional)

---

## 🔗 Resources

- [Vercel Python Docs](https://vercel.com/docs/concepts/functions/serverless-functions/runtimes/python)
- [Vercel CLI Docs](https://vercel.com/docs/cli)
- [Mangum (ASGI Adapter)](https://mangum.io/)

---

## 🚀 Quick Start Command

```bash
# Install, login, and deploy in one go
npm install -g vercel && vercel login && vercel --prod
```

Good luck with your deployment! 🎉
