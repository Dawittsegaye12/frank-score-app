# Render Performance Optimization Guide

## Why Your App is Slow

### 1. **Render Free Tier Cold Starts** ❄️
- Apps spin down after **15 minutes of inactivity**
- First request after spin-down takes **30-60 seconds** to wake up
- This is normal for free tier - Render needs to:
  - Start the container
  - Install dependencies (if needed)
  - Load your application
  - Initialize everything

### 2. **Heavy Startup Operations** 🐌
Your app loads ML models at startup (in `app.py`):
```python
@app.on_event("startup")
def _startup() -> None:
    db.init_db()                    # Fast
    load_question_banks()            # Fast
    scoring.load_xgb_model()        # SLOW (if model is large)
    scoring.load_rf_model()         # SLOW (if model is large)
```

**Model loading can take 5-15 seconds** per model if files are large!

## Solutions

### Solution 1: Lazy Load Models (Recommended) ⚡

Load models only when needed, not at startup:

```python
# In app.py, remove model loading from startup:
@app.on_event("startup")
def _startup() -> None:
    db.init_db()
    load_question_banks()
    # Don't load models here - load them lazily
```

Models will load on first prediction request (still slow first time, but faster startup).

### Solution 2: Use Render Paid Tier 💰
- **Starter Plan ($7/month)**: Keeps app always running
- No cold starts
- Faster response times
- Better for production

### Solution 3: Keep App Warm 🔥
Use a service like:
- **UptimeRobot** (free): Pings your app every 5 minutes
- **Cron-job.org** (free): Scheduled pings
- **Pingdom** (free tier available)

Set up a cron job to ping: `https://frank-score-app.onrender.com/health` every 5 minutes

### Solution 4: Optimize Model Loading 🚀

Make model loading faster:

1. **Compress models** (if possible)
2. **Use smaller models** for production
3. **Load models in background** after startup

### Solution 5: Add Startup Optimization

Add a lightweight health check that doesn't wait for models:

```python
@app.get("/health")
def health() -> Dict[str, Any]:
    # Fast health check - don't wait for models
    try:
        with db.get_conn() as conn:
            conn.execute("SELECT 1").fetchone()
        return {"ok": True, "db": "ok", "models": "loading"}
    except Exception as e:
        return {"ok": False, "db": "error", "error": str(e)}
```

## Quick Fix: Lazy Model Loading

Here's how to implement lazy loading:

