# Admin Dashboard Documentation

## Overview

The FrankScore Admin Dashboard is a simple, internal monitoring tool for administrators to track:
- Model Performance
- Data Drift
- API Uptime/Health
- Fairness Metrics

## Features

### 1. Overview Page (`/admin`)
- **Status Cards**: Quick view of all monitoring categories (OK/WARNING/CRITICAL)
- **Active Alerts**: Top 5 alerts with category, message, severity, and timestamp

### 2. Performance Page (`/admin/performance`)
- **Metrics Cards**: Accuracy, F1 Score, AUC
- **Time Series Table**: Performance metrics over the last 14 days
- **Confusion Matrix**: 2x2 matrix showing TP, FP, FN, TN

### 3. Drift Page (`/admin/drift`)
- **Overall Drift Score**: Single number indicating overall data drift
- **Top Drifted Features**: Table showing feature names, drift scores, and status

### 4. Uptime Page (`/admin/uptime`)
- **Health Metrics**: Uptime %, Latency (p95), Error Rate %
- **API Logs Table**: Recent API requests with time, route, status code, and latency

### 5. Fairness Page (`/admin/fairness`)
- **Approval Rate Gap**: Difference between max and min approval rates
- **Metrics by Country**: Table showing approval rate, default rate, and F1 score per country

## Access Control

The admin dashboard is protected by a simple access control mechanism:

1. **Environment Variable**: Set `ADMIN_MODE=true` to enable access
2. **Default Behavior**: Access is denied by default (returns 403)

### Enabling Admin Access

**Windows PowerShell:**
```powershell
$env:ADMIN_MODE="true"
uvicorn app:app --reload
```

**Linux/Mac:**
```bash
export ADMIN_MODE=true
uvicorn app:app --reload
```

**Note**: In production, this should be replaced with proper user role-based authentication.

## Mock Data

The dashboard currently uses mock data from `admin_mock_data.py`. This allows the UI to work immediately without requiring:
- Complex database queries
- Real-time monitoring infrastructure
- Historical data collection

### Mock Data Structure

- `get_overview_status()`: Returns status for each category
- `get_alerts(limit)`: Returns list of active alerts
- `get_performance_metrics()`: Returns accuracy, F1, AUC, timeseries, confusion matrix
- `get_drift_data()`: Returns overall drift score and top drifted features
- `get_uptime_metrics()`: Returns uptime %, latency, error rate, and API logs
- `get_fairness_metrics()`: Returns metrics by country and approval rate gap

## File Structure

```
templates/admin/
├── base.html          # Base layout with sidebar navigation
├── overview.html      # Overview page
├── performance.html   # Performance page
├── drift.html         # Drift page
├── uptime.html        # Uptime page
└── fairness.html      # Fairness page

admin_mock_data.py     # Mock data module
app.py                 # Admin routes (lines 511-619)
```

## Routes

- `GET /admin` - Overview page
- `GET /admin/performance` - Performance page
- `GET /admin/drift` - Drift page
- `GET /admin/uptime` - Uptime page
- `GET /admin/fairness` - Fairness page

## UI Features

- **Sidebar Navigation**: Fixed sidebar with navigation links
- **Date Range Filter**: UI-only date range selector (From/To) - defaults to last 14 days
- **Status Indicators**: Color-coded status badges (OK=green, WARNING=orange, CRITICAL=red)
- **Responsive Design**: Clean, modern UI with proper spacing and typography

## Future Enhancements

For production, consider:
1. Replace mock data with real database queries
2. Implement proper user authentication and role-based access
3. Add real-time updates (WebSocket or polling)
4. Implement date range filtering functionality
5. Add export functionality for reports
6. Add charts/graphs using a charting library (Chart.js, Plotly, etc.)
7. Add alert management (acknowledge, resolve, etc.)




