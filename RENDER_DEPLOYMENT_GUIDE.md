# Render Deployment Guide

## Understanding Your Deployment Logs

When you view your deployment at the Render dashboard, here's what to look for:

### ✅ Successful Startup Sequence

Your app should show these messages in order:

```
1. Python version check
2. Installing dependencies from requirements.txt
3. Starting application...
4. Database initialization
5. Question banks loaded
6. Model loading messages
```

### Expected Log Messages

#### 1. **Dependency Installation**
```
Collecting fastapi==0.115.6
Collecting uvicorn[standard]==0.30.6
...
Successfully installed ...
```

#### 2. **Application Startup**
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:PORT
```

#### 3. **Database Initialization** (from `app.py` startup event)
```
# Should happen automatically, no error messages
```

#### 4. **Question Banks Loaded** (from `load_question_banks()`)
```
# Should load without errors
```

#### 5. **Model Loading** (from `scoring.load_xgb_model()` and `scoring.load_rf_model()`)
```
Info: XGBoost model loaded with 15 feature columns
Info: Random Forest model loaded with 23 feature columns
```

OR if models are missing:
```
Info: XGBoost model not found at models/xgb_model.joblib, will use fallback scoring
Info: Random Forest model not found at models/random_forest.joblib, will use fallback scoring
```

## 🔍 Common Issues & Solutions

### Issue 1: Build Fails During Dependency Installation

**Symptoms:**
```
ERROR: Could not find a version that satisfies the requirement...
ERROR: Failed building wheel for...
```

**Solutions:**
1. Check `requirements.txt` for version conflicts
2. Ensure Python version matches (3.10.0 in render.yaml)
3. Some packages may need system dependencies (check Render docs)

### Issue 2: Application Crashes on Startup

**Symptoms:**
```
Application failed to respond
Process exited with code 1
```

**Check for:**
1. **Missing files:**
   - `questiondb/psychometric_question_bank_v2_public.json`
   - `questiondb/psychometric_question_bank_v2_admin.json`
   - `models/xgb_model.joblib` (optional, has fallback)
   - `models/random_forest.joblib` (optional, has fallback)

2. **Import errors:**
   ```
   ModuleNotFoundError: No module named '...'
   ```
   → Add missing package to `requirements.txt`

3. **Database errors:**
   ```
   sqlite3.OperationalError: ...
   ```
   → Database should auto-initialize, check file permissions

### Issue 3: Models Not Loading

**Symptoms:**
```
Warning: Could not load XGBoost model from models/xgb_model.joblib: ...
Warning: Could not load Random Forest model from models/random_forest.joblib: ...
```

**Solutions:**
1. **Model files not in repo:**
   - Ensure `models/` directory is committed to Git
   - Check file sizes (Render has limits)
   - Use Git LFS for large files if needed

2. **Model version incompatibility:**
   ```
   AttributeError: '_fill_dtype'
   ```
   → Model was trained with different scikit-learn version
   → Retrain model or match scikit-learn version

### Issue 4: Application Starts But Returns 500 Errors

**Symptoms:**
- Health check returns `{"ok": false, "db": "error"}`
- Pages return 500 Internal Server Error

**Check logs for:**
1. Database connection errors
2. Missing environment variables
3. File path issues (relative paths may differ on Render)

### Issue 5: Static Files Not Loading

**Symptoms:**
- CSS/JS files return 404
- Pages load but look broken

**Solutions:**
1. Ensure `static/` directory is in repo
2. Check `app.mount("/static", ...)` in app.py
3. Verify file paths in templates

## 📋 Deployment Checklist

### Before Deployment
- [ ] All required files committed to Git
- [ ] `requirements.txt` is up to date
- [ ] `render.yaml` is configured correctly
- [ ] Model files are in repo (or fallback is acceptable)
- [ ] Question bank JSON files are in repo

### After Deployment
- [ ] Build completes successfully
- [ ] Application starts without errors
- [ ] Health endpoint works: `/health`
- [ ] Home page loads: `/`
- [ ] Admin dashboard accessible: `/admin`
- [ ] Questions API works: `/api/questions`
- [ ] Models loaded (check logs)

## 🔧 Debugging Steps

### 1. Check Build Logs
In Render dashboard → Your Service → Logs → Build Logs
- Look for dependency installation errors
- Check Python version
- Verify all packages installed

### 2. Check Runtime Logs
In Render dashboard → Your Service → Logs → Runtime Logs
- Look for startup messages
- Check for error traces
- Verify model loading messages

### 3. Test Endpoints
```bash
# Health check
curl https://your-app.onrender.com/health

# Should return: {"ok": true, "db": "ok"}
```

### 4. Check Environment Variables
Render Dashboard → Your Service → Environment
- Verify `ADMIN_MODE` (optional)
- Check `SCORING_API_URL` if using external API
- Verify API credentials if needed

### 5. Verify File Structure
Ensure these directories exist in your repo:
```
frank-score-app/
├── app.py
├── db.py
├── scoring.py
├── models/
│   ├── xgb_model.joblib (optional)
│   └── random_forest.joblib (optional)
├── questiondb/
│   ├── psychometric_question_bank_v2_public.json
│   └── psychometric_question_bank_v2_admin.json
├── templates/
├── static/
└── requirements.txt
```

## 🚨 Critical Errors to Watch For

### 1. Import Errors
```
ImportError: cannot import name '...'
ModuleNotFoundError: No module named '...'
```
**Fix:** Add missing package to `requirements.txt`

### 2. File Not Found
```
FileNotFoundError: [Errno 2] No such file or directory: '...'
```
**Fix:** Ensure file is committed to Git and path is correct

### 3. Database Errors
```
sqlite3.OperationalError: unable to open database file
```
**Fix:** Check file permissions, database auto-initializes on startup

### 4. Port Binding
```
Address already in use
```
**Fix:** Use `$PORT` environment variable (already in render.yaml)

## 📊 Monitoring Your Deployment

### Health Endpoint
Visit: `https://your-app.onrender.com/health`
- Should return: `{"ok": true, "db": "ok"}`
- If `db: "error"`, check database initialization

### Admin Dashboard
Visit: `https://your-app.onrender.com/admin`
- Should show overview page
- If 403, check `ADMIN_MODE` environment variable

### Application Logs
Render Dashboard → Logs tab
- Real-time logs
- Filter by level (INFO, WARNING, ERROR)
- Search for specific errors

## 🎯 Quick Fixes

### Restart Application
Render Dashboard → Manual Deploy → Clear build cache & deploy

### Rebuild from Scratch
1. Delete service in Render
2. Create new service
3. Connect to same Git repo
4. Deploy fresh

### Check Git Repository
Ensure all files are committed:
```bash
git status
git add .
git commit -m "Deploy to Render"
git push
```

## 📞 Next Steps

If deployment is successful:
1. ✅ Test full assessment flow
2. ✅ Verify model predictions work
3. ✅ Check admin dashboard metrics
4. ✅ Monitor for errors in production

If deployment fails:
1. Check the specific error in logs
2. Review this guide for solutions
3. Verify all files are in Git repo
4. Test locally first to isolate issues

