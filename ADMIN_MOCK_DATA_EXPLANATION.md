# Explanation of admin_mock_data.py

## Overview

`admin_mock_data.py` is a Python module that provides **hardcoded mock data** for the admin dashboard. It contains 5 functions that return sample data for each dashboard page, allowing the UI to work immediately without needing real database queries or calculations.

---

## Why Mock Data?

- **Quick Development**: UI can be built and tested without waiting for backend infrastructure
- **No Dependencies**: Works without database queries, monitoring systems, or historical data
- **Consistent Testing**: Provides predictable data for testing the dashboard UI
- **Easy Replacement**: Can be swapped out with real data functions later

---

## Functions Explained

### 1. `get_overview_status()`

**Purpose**: Returns the overall status for each monitoring category.

**Returns**:
```python
{
    "performance": "OK",      # Model performance status
    "drift": "WARNING",       # Data drift status
    "uptime": "OK",           # API health status
    "fairness": "OK"          # Fairness metrics status
}
```

**Used by**: Overview page to show the 4 status cards.

**Status Values**: `"OK"`, `"WARNING"`, or `"CRITICAL"` (displayed with color coding)

---

### 2. `get_alerts(limit: int = 5)`

**Purpose**: Returns a list of active alerts/notifications.

**Parameters**:
- `limit`: Maximum number of alerts to return (default: 5)

**Returns**: List of alert dictionaries, each containing:
```python
{
    "category": "drift",           # Category: performance/drift/uptime/fairness
    "message": "Feature 'monthly_income' shows significant drift (score: 0.78)",
    "severity": "warning",         # "warning" or "critical"
    "timestamp": "2026-01-09T13:00:00"  # ISO format timestamp
}
```

**How it works**:
- Creates 5 sample alerts with different categories
- Uses `datetime.now()` to generate current timestamps
- Subtracts hours/days to create realistic relative times
- Returns only the first `limit` items

**Used by**: Overview page to display the "Active Alerts" list.

---

### 3. `get_performance_metrics()`

**Purpose**: Returns model performance metrics including accuracy, F1, AUC, time series, and confusion matrix.

**Returns**:
```python
{
    "accuracy": 0.825,        # Overall accuracy (0-1)
    "f1": 0.752,             # F1 score (0-1)
    "auc": 0.891,            # Area Under Curve (0-1)
    "timeseries": [           # 14 days of historical data
        {
            "date": "2026-01-01",
            "accuracy": 0.820,
            "f1": 0.740,
            "auc": 0.880
        },
        # ... 13 more days
    ],
    "confusion_matrix": {
        "tp": 1245,  # True Positives
        "fp": 312,   # False Positives
        "tn": 1890,  # True Negatives
        "fn": 203    # False Negatives
    }
}
```

**How it works**:
- Generates 15 days of time series data (last 14 days + today)
- Uses modulo operations (`i % 3`, `i % 4`) to create slight variations in metrics
- Provides a 2x2 confusion matrix with sample counts

**Used by**: Performance page to show metrics cards, time series table, and confusion matrix.

---

### 4. `get_drift_data()`

**Purpose**: Returns data drift information showing how much the current data differs from the training baseline.

**Returns**:
```python
{
    "overall_score": 0.68,    # Overall drift score (0-1, higher = more drift)
    "features": [
        {
            "name": "monthly_income",
            "score": 0.78,           # Drift score for this feature
            "status": "WARNING"       # OK/WARNING/CRITICAL
        },
        # ... more features
    ]
}
```

**How it works**:
- Provides an overall drift score (0.68 = moderate drift)
- Lists 8 features with their individual drift scores
- Higher scores indicate more drift from training data
- Status is determined by score thresholds (WARNING if > 0.6, OK if < 0.6)

**Used by**: Drift page to show overall score and top drifted features table.

---

### 5. `get_uptime_metrics()`

**Purpose**: Returns API health metrics including uptime percentage, latency, error rate, and recent API logs.

**Returns**:
```python
{
    "uptime_pct": 99.2,              # Uptime percentage
    "latency_p95_ms": 450,           # 95th percentile latency in milliseconds
    "error_rate_pct": 0.8,           # Error rate percentage
    "logs": [                        # Recent API request logs
        {
            "time": "2026-01-09T14:00:00",
            "route": "/api/start",
            "status_code": 200,
            "latency_ms": 120
        },
        # ... 14 more logs
    ]
}
```

**How it works**:
- Generates 15 recent API log entries
- Uses arrays of routes, status codes, and latencies
- Cycles through arrays using modulo to create variety
- Timestamps are generated going backwards from now (5 minutes apart)

**Used by**: Uptime page to show health metrics cards and API logs table.

---

### 6. `get_fairness_metrics()`

**Purpose**: Returns fairness metrics grouped by country, showing approval rates, default rates, and F1 scores.

**Returns**:
```python
{
    "by_country": [
        {
            "country": "Kenya",
            "approval_rate": 0.72,      # Percentage of loans approved
            "default_rate": 0.18,        # Percentage that defaulted
            "f1": 0.76                   # F1 score for this group
        },
        # ... more countries
    ],
    "approval_rate_gap": 0.07            # Max - Min approval rate
}
```

**How it works**:
- Defines 4 countries with different metrics
- Calculates the approval rate gap by finding max and min values
- Rounds the gap to 3 decimal places

**Used by**: Fairness page to show approval rate gap and metrics by country table.

---

## Data Flow

```
Admin Dashboard Page
    ↓
Calls admin route in app.py
    ↓
Route calls admin_mock_data function
    ↓
Function returns mock data dictionary
    ↓
Data passed to Jinja2 template
    ↓
Template renders HTML with data
    ↓
User sees dashboard with mock data
```

---

## Replacing with Real Data

To replace mock data with real data, you would:

1. **Keep the function signatures** (same return types)
2. **Replace the function bodies** with:
   - Database queries (SQLite, PostgreSQL, etc.)
   - Real-time calculations
   - API calls to monitoring services
   - Historical data aggregation

**Example** (for `get_performance_metrics`):
```python
def get_performance_metrics() -> Dict[str, Any]:
    # Real implementation
    with db.get_conn() as conn:
        # Query actual metrics from database
        accuracy = conn.execute("SELECT AVG(accuracy) FROM model_metrics WHERE date >= ?", ...).fetchone()[0]
        # ... more queries
    return {
        "accuracy": accuracy,
        "f1": f1_score,
        # ... rest of data
    }
```

The admin dashboard templates don't need to change - they'll automatically use the real data!

---

## Summary

- **5 functions** provide mock data for all dashboard pages
- **Simple and predictable** - easy to understand and modify
- **Ready for replacement** - swap functions when real data is available
- **No external dependencies** - works standalone
- **Realistic structure** - matches what real data would look like




