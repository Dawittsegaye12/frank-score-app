# Quick Switch Guide: Mock Data → Real Data

## 🚀 Fastest Way to Switch

### Step 1: Update app.py (One Line Change)

Find this line in `app.py` (around line 16):
```python
import admin_mock_data
```

Change it to:
```python
import admin_data as admin_mock_data  # Use real data instead of mock
```

That's it! The dashboard will now use real data from your database.

---

## 📊 What Each Function Does

### `get_overview_status()`
- **Queries**: `attempts` table (recent assessments)
- **Returns**: Status for Performance, Drift, Uptime, Fairness
- **Real Data**: Checks if you have enough assessments (needs 10+ in last 7 days)

### `get_alerts(limit=5)`
- **Queries**: `computed` table (predictions), `attempts` table (status)
- **Returns**: List of alerts (warnings/critical issues)
- **Real Data**: Checks average PD, incomplete assessments

### `get_performance_metrics()`
- **Queries**: `computed` table (pd_final_hat, pd_psych_hat, pd_fin_hat)
- **Returns**: Accuracy, F1, AUC, time series, confusion matrix
- **⚠️ Note**: Currently uses **estimated** metrics (needs ground truth labels for real metrics)

### `get_drift_data()`
- **Queries**: `financial_data` table (recent financial features)
- **Returns**: Overall drift score, top drifted features
- **Real Data**: Compares recent data to baseline (currently uses hardcoded baseline)

### `get_uptime_metrics()`
- **Queries**: `attempts` table (completion rates, timestamps)
- **Returns**: Uptime %, latency p95, error rate, API logs
- **Real Data**: Uses assessment completion as uptime proxy

### `get_fairness_metrics()`
- **Queries**: `financial_data`, `attempts`, `computed` tables
- **Returns**: Metrics by country, approval rate gap
- **Real Data**: Groups by country (currently uses placeholder grouping)

---

## 🔧 What Needs Improvement

### 1. Performance Metrics (Accuracy, F1, AUC)
**Problem**: Needs actual default outcomes to calculate real metrics.

**Solution**: Add outcome tracking:
```sql
ALTER TABLE computed ADD COLUMN actual_default INTEGER;
```

Then update predictions with actual outcomes when you know them.

### 2. Drift Detection
**Problem**: Uses hardcoded baseline statistics.

**Solution**: Save your training data statistics:
```python
# After training
baseline = {
    "monthly_income": {"mean": 50000, "std": 15000},
    "total_debt": {"mean": 100000, "std": 50000},
}
# Save to file or database
```

### 3. API Logging
**Problem**: Uses assessment completion as uptime proxy.

**Solution**: Add API request logging middleware (see `ADMIN_INTEGRATION_GUIDE.md`).

### 4. Fairness Metrics
**Problem**: Uses placeholder country grouping.

**Solution**: Add country column to users table:
```sql
ALTER TABLE users ADD COLUMN country TEXT;
```

---

## ✅ Testing

After switching, test the dashboard:

1. **Visit**: `http://localhost:8000/admin`
2. **Check**: All pages load without errors
3. **Verify**: Data looks reasonable (not all zeros or nulls)

If you see errors, check:
- Database has data (run some assessments first)
- Database connection works
- All required tables exist

---

## 📝 Example: Adding Real Performance Metrics

Here's how to add ground truth tracking:

### 1. Add column to database:
```python
# In db.py, add to init_db():
conn.execute("""
    ALTER TABLE computed ADD COLUMN actual_default INTEGER
""")
```

### 2. Update predictions with outcomes:
```python
# When you know the actual outcome:
db.update_outcome(assessment_id="FS000001", actual_default=1)  # 1 = defaulted, 0 = paid
```

### 3. Update admin_data.py:
```python
# In get_performance_metrics(), replace estimated metrics with:
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

accuracy = (tp + tn) / (tp + tn + fp + fn)
```

---

## 🎯 Summary

**To switch to real data:**
1. Change one line in `app.py`: `import admin_data as admin_mock_data`
2. Restart server
3. Done! ✅

**To improve accuracy:**
- Add ground truth labels for performance metrics
- Store baseline statistics for drift detection
- Add API logging for uptime metrics
- Add demographic data for fairness metrics

See `ADMIN_INTEGRATION_GUIDE.md` for detailed instructions.




