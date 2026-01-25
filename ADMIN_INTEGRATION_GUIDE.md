# Admin Dashboard Integration Guide

## Overview

This guide explains how to integrate your real model data with the admin dashboard, replacing the mock data with actual database queries and calculations.

---

## Step 1: Understanding the Current Setup

### Current Files:
- **`admin_mock_data.py`** - Mock/hardcoded data (currently used)
- **`admin_data.py`** - Real data functions (ready to use)
- **`app.py`** - Routes that call the data functions

### Current Flow:
```
Admin Page → Route in app.py → Calls admin_mock_data function → Returns mock data → Template renders
```

### Target Flow:
```
Admin Page → Route in app.py → Calls admin_data function → Queries database → Returns real data → Template renders
```

---

## Step 2: Switch from Mock to Real Data

### Option A: Quick Switch (Recommended)

In `app.py`, replace the import:

**Before:**
```python
import admin_mock_data
```

**After:**
```python
import admin_data as admin_mock_data  # Use real data instead
```

This way, all existing code continues to work without changes!

### Option B: Explicit Switch

Update each route in `app.py`:

**Before:**
```python
status = admin_mock_data.get_overview_status()
```

**After:**
```python
import admin_data
status = admin_data.get_overview_status()
```

---

## Step 3: Understanding Real Data Functions

### 1. `get_overview_status()`

**What it does:**
- Checks recent assessment count
- Determines if there's enough data for monitoring
- Returns status: OK, WARNING, or CRITICAL

**Current implementation:**
- Checks if there are at least 10 assessments in last 7 days
- Returns WARNING if not enough data

**To improve:**
- Add actual performance threshold checks
- Implement real drift detection
- Track actual API errors

---

### 2. `get_alerts(limit=5)`

**What it does:**
- Analyzes recent data for issues
- Creates alerts based on anomalies

**Current implementation:**
- Checks average PD (if > 0.5, creates warning)
- Checks incomplete assessments count

**To improve:**
- Add drift detection alerts
- Add performance degradation alerts
- Add fairness violation alerts

---

### 3. `get_performance_metrics()`

**What it does:**
- Calculates accuracy, F1, AUC from predictions
- Creates time series data (last 14 days)
- Generates confusion matrix

**⚠️ Important Limitation:**
- **Accuracy/F1/AUC require ground truth labels** (actual default outcomes)
- Current implementation uses **simplified estimates** based on PD values
- **For real metrics, you need:**
  1. Store actual default outcomes in database
  2. Compare predictions to actual outcomes
  3. Calculate true TP, FP, TN, FN

**To get real metrics:**

1. **Add outcome tracking to database:**
```sql
ALTER TABLE computed ADD COLUMN actual_default INTEGER;  -- 0 or 1
ALTER TABLE computed ADD COLUMN outcome_date TEXT;       -- When outcome was known
```

2. **Update `get_performance_metrics()`:**
```python
# Get predictions with actual outcomes
rows = conn.execute("""
    SELECT pd_final_hat, actual_default
    FROM computed
    WHERE actual_default IS NOT NULL
""").fetchall()

# Calculate real confusion matrix
tp = sum(1 for pd, actual in rows if pd >= 0.5 and actual == 1)
fp = sum(1 for pd, actual in rows if pd >= 0.5 and actual == 0)
tn = sum(1 for pd, actual in rows if pd < 0.5 and actual == 0)
fn = sum(1 for pd, actual in rows if pd < 0.5 and actual == 1)

# Calculate real metrics
accuracy = (tp + tn) / (tp + tn + fp + fn)
precision = tp / (tp + fp) if (tp + fp) > 0 else 0
recall = tp / (tp + fn) if (tp + fn) > 0 else 0
f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
```

---

### 4. `get_drift_data()`

**What it does:**
- Compares current data distribution to training baseline
- Calculates drift scores for each feature
- Identifies features with significant drift

**Current implementation:**
- Uses hardcoded baseline means
- Compares recent data (last 30 days) to baseline
- Calculates drift as normalized difference

**To improve:**

1. **Store training baseline statistics:**
```python
# After training, save baseline statistics
baseline_stats = {
    "monthly_income": {"mean": 50000, "std": 15000},
    "total_debt": {"mean": 100000, "std": 50000},
    # ... etc
}

# Save to file or database
import json
with open("baseline_stats.json", "w") as f:
    json.dump(baseline_stats, f)
```

2. **Load baseline in `get_drift_data()`:**
```python
import json
with open("baseline_stats.json", "r") as f:
    baseline_stats = json.load(f)

# Use statistical tests (KS test, PSI, etc.)
from scipy import stats
drift_score = stats.ks_2samp(baseline_data, current_data).statistic
```

3. **Use proper drift detection libraries:**
   - **Evidently AI**: `evidently`
   - **NannyML**: `nannyml`
   - **scikit-learn**: Statistical tests

---

### 5. `get_uptime_metrics()`

**What it does:**
- Calculates uptime percentage
- Measures latency (p95)
- Tracks error rate
- Shows recent API logs

**Current implementation:**
- Uses assessment completion rate as uptime proxy
- Calculates latency from assessment duration
- Generates simplified API logs

**To improve:**

1. **Add API request logging middleware:**
```python
# In app.py
import time
from fastapi import Request

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    latency_ms = int((time.time() - start_time) * 1000)
    
    # Log to database
    db.log_api_request(
        route=request.url.path,
        method=request.method,
        status_code=response.status_code,
        latency_ms=latency_ms,
        timestamp_ms=int(time.time() * 1000)
    )
    
    return response
```

2. **Create API logs table:**
```sql
CREATE TABLE IF NOT EXISTS api_logs(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    route TEXT,
    method TEXT,
    status_code INTEGER,
    latency_ms INTEGER,
    timestamp_ms INTEGER
);
```

3. **Query real logs in `get_uptime_metrics()`:**
```python
logs = conn.execute("""
    SELECT route, status_code, latency_ms, timestamp_ms
    FROM api_logs
    ORDER BY timestamp_ms DESC
    LIMIT 100
""").fetchall()
```

---

### 6. `get_fairness_metrics()`

**What it does:**
- Groups metrics by demographic (country, gender, etc.)
- Calculates approval rates per group
- Calculates approval rate gap

**Current implementation:**
- Uses placeholder country grouping (user_id % 4)
- Simplified approval logic (PD < 0.5 = approved)

**To improve:**

1. **Add demographic data to database:**
```sql
ALTER TABLE users ADD COLUMN country TEXT;
ALTER TABLE users ADD COLUMN gender TEXT;
ALTER TABLE users ADD COLUMN age_group TEXT;
```

2. **Update `get_fairness_metrics()`:**
```python
rows = conn.execute("""
    SELECT 
        u.country,
        c.pd_final_hat,
        a.status
    FROM users u
    JOIN attempts a ON u.id = a.user_id
    LEFT JOIN computed c ON a.assessment_id = c.assessment_id
    WHERE c.pd_final_hat IS NOT NULL
    AND u.country IS NOT NULL
""").fetchall()

# Group by actual country
country_groups = {}
for row in rows:
    country = row[0]
    if country not in country_groups:
        country_groups[country] = []
    country_groups[country].append(row[1])
```

---

## Step 4: Adding Ground Truth Labels (Critical for Performance Metrics)

To get **real** accuracy, F1, and AUC, you need to track actual default outcomes:

### 1. Add Outcome Tracking

```python
# In db.py
def add_outcome(assessment_id: str, actual_default: int, outcome_date: Optional[str] = None):
    """Record actual default outcome for an assessment."""
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE computed
            SET actual_default = ?, outcome_date = ?
            WHERE assessment_id = ?
            """,
            (actual_default, outcome_date or datetime.now().isoformat(), assessment_id)
        )
```

### 2. Update Performance Metrics

```python
# In admin_data.py, update get_performance_metrics()
def get_performance_metrics() -> Dict[str, Any]:
    with db.get_conn() as conn:
        rows = conn.execute("""
            SELECT pd_final_hat, actual_default
            FROM computed
            WHERE actual_default IS NOT NULL
        """).fetchall()
    
    # Calculate real confusion matrix
    threshold = 0.5
    tp = sum(1 for pd, actual in rows if pd >= threshold and actual == 1)
    fp = sum(1 for pd, actual in rows if pd >= threshold and actual == 0)
    tn = sum(1 for pd, actual in rows if pd < threshold and actual == 0)
    fn = sum(1 for pd, actual in rows if pd < threshold and actual == 1)
    
    # Calculate real metrics
    accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) > 0 else 0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    # Calculate AUC using sklearn
    from sklearn.metrics import roc_auc_score
    y_true = [row[1] for row in rows]
    y_pred = [row[0] for row in rows]
    auc = roc_auc_score(y_true, y_pred) if len(set(y_true)) > 1 else 0.5
    
    return {
        "accuracy": round(accuracy, 3),
        "f1": round(f1, 3),
        "auc": round(auc, 3),
        # ... rest
    }
```

---

## Step 5: Testing the Integration

### 1. Test with Real Data

```python
# Test script: test_admin_data.py
import admin_data

# Test each function
print("Overview Status:", admin_data.get_overview_status())
print("Alerts:", len(admin_data.get_alerts()))
print("Performance:", admin_data.get_performance_metrics())
print("Drift:", admin_data.get_drift_data())
print("Uptime:", admin_data.get_uptime_metrics())
print("Fairness:", admin_data.get_fairness_metrics())
```

### 2. Compare Mock vs Real

```python
import admin_mock_data
import admin_data

# Compare outputs
mock_status = admin_mock_data.get_overview_status()
real_status = admin_data.get_overview_status()
print("Mock:", mock_status)
print("Real:", real_status)
```

---

## Step 6: Production Considerations

### 1. Caching

Add caching for expensive calculations:

```python
from functools import lru_cache
from datetime import datetime, timedelta

@lru_cache(maxsize=1)
def get_performance_metrics_cached():
    """Cached version - refreshes every 5 minutes."""
    return get_performance_metrics()

# Clear cache every 5 minutes
# (In production, use Redis or similar)
```

### 2. Error Handling

```python
def get_performance_metrics() -> Dict[str, Any]:
    try:
        # ... database queries
    except Exception as e:
        # Log error
        print(f"Error calculating performance metrics: {e}")
        # Return safe defaults
        return {
            "accuracy": None,
            "f1": None,
            "auc": None,
            "timeseries": [],
            "confusion_matrix": {"tp": 0, "fp": 0, "tn": 0, "fn": 0},
        }
```

### 3. Performance Optimization

- Add database indexes on frequently queried columns
- Use materialized views for complex aggregations
- Batch queries where possible
- Consider background jobs for expensive calculations

---

## Summary

1. **Switch imports** in `app.py` from `admin_mock_data` to `admin_data`
2. **Add ground truth tracking** for real performance metrics
3. **Implement API logging** for real uptime metrics
4. **Store baseline statistics** for real drift detection
5. **Add demographic data** for real fairness metrics
6. **Test thoroughly** before deploying to production

The `admin_data.py` file is ready to use - just switch the import and it will start using real data from your database!




