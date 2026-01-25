"""
Mock data for admin dashboard.
This module provides hardcoded mock data for all admin dashboard pages.
In production, this would be replaced with real database queries and calculations.
"""
from datetime import datetime, timedelta
from typing import Any, Dict, List


def get_overview_status() -> Dict[str, str]:
    """Returns status for each monitoring category."""
    return {
        "performance": "OK",
        "drift": "WARNING",
        "uptime": "OK",
        "fairness": "OK",
    }


def get_alerts(limit: int = 5) -> List[Dict[str, Any]]:
    """Returns list of active alerts."""
    now = datetime.now()
    return [
        {
            "category": "drift",
            "message": "Feature 'monthly_income' shows significant drift (score: 0.78)",
            "severity": "warning",
            "timestamp": (now - timedelta(hours=2)).isoformat(),
        },
        {
            "category": "performance",
            "message": "Model F1 score dropped below threshold (0.72 < 0.75)",
            "severity": "warning",
            "timestamp": (now - timedelta(hours=5)).isoformat(),
        },
        {
            "category": "uptime",
            "message": "High latency detected on /api/complete endpoint (p95: 1200ms)",
            "severity": "warning",
            "timestamp": (now - timedelta(hours=8)).isoformat(),
        },
        {
            "category": "fairness",
            "message": "Approval rate gap between groups increased to 0.15",
            "severity": "warning",
            "timestamp": (now - timedelta(days=1)).isoformat(),
        },
        {
            "category": "drift",
            "message": "Feature 'total_debt' drift score: 0.65",
            "severity": "warning",
            "timestamp": (now - timedelta(days=2)).isoformat(),
        },
    ][:limit]


def get_performance_metrics() -> Dict[str, Any]:
    """Returns model performance metrics."""
    now = datetime.now()
    timeseries = []
    for i in range(14, -1, -1):
        date = (now - timedelta(days=i)).strftime("%Y-%m-%d")
        timeseries.append({
            "date": date,
            "accuracy": round(0.82 + (i % 3) * 0.01, 3),
            "f1": round(0.74 + (i % 4) * 0.01, 3),
            "auc": round(0.88 + (i % 2) * 0.01, 3),
        })
    
    return {
        "accuracy": 0.825,
        "f1": 0.752,
        "auc": 0.891,
        "timeseries": timeseries,
        "confusion_matrix": {
            "tp": 1245,
            "fp": 312,
            "tn": 1890,
            "fn": 203,
        },
    }


def get_drift_data() -> Dict[str, Any]:
    """Returns data drift information."""
    return {
        "overall_score": 0.68,
        "features": [
            {"name": "monthly_income", "score": 0.78, "status": "WARNING"},
            {"name": "total_debt", "score": 0.65, "status": "WARNING"},
            {"name": "missed_payments_3m", "score": 0.52, "status": "OK"},
            {"name": "daily_burden", "score": 0.48, "status": "OK"},
            {"name": "num_previous_loans", "score": 0.45, "status": "OK"},
            {"name": "amount_bucket", "score": 0.42, "status": "OK"},
            {"name": "loan_duration_days", "score": 0.38, "status": "OK"},
            {"name": "age", "score": 0.35, "status": "OK"},
        ],
    }


def get_uptime_metrics() -> Dict[str, Any]:
    """Returns API uptime and health metrics."""
    now = datetime.now()
    logs = []
    routes = ["/api/start", "/api/answer", "/api/complete", "/api/result", "/api/questions"]
    status_codes = [200, 200, 200, 200, 200, 200, 200, 500, 200, 200, 200, 200, 200, 200, 200]
    latencies = [120, 85, 450, 95, 110, 200, 150, 1200, 130, 90, 180, 200, 140, 100, 160]
    
    for i in range(15, 0, -1):
        route_idx = i % len(routes)
        status_idx = i % len(status_codes)
        logs.append({
            "time": (now - timedelta(minutes=i * 5)).isoformat(),
            "route": routes[route_idx],
            "status_code": status_codes[status_idx],
            "latency_ms": latencies[status_idx],
        })
    
    return {
        "uptime_pct": 99.2,
        "latency_p95_ms": 450,
        "error_rate_pct": 0.8,
        "logs": logs,
    }


def get_fairness_metrics() -> Dict[str, Any]:
    """Returns fairness metrics by group."""
    by_country = [
        {"country": "Kenya", "approval_rate": 0.72, "default_rate": 0.18, "f1": 0.76},
        {"country": "Tanzania", "approval_rate": 0.68, "default_rate": 0.22, "f1": 0.73},
        {"country": "Uganda", "approval_rate": 0.75, "default_rate": 0.15, "f1": 0.78},
        {"country": "Rwanda", "approval_rate": 0.70, "default_rate": 0.20, "f1": 0.74},
    ]
    
    approval_rates = [g["approval_rate"] for g in by_country]
    approval_rate_gap = max(approval_rates) - min(approval_rates)
    
    return {
        "by_country": by_country,
        "approval_rate_gap": round(approval_rate_gap, 3),
    }
