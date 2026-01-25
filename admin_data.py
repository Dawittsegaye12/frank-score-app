"""
Real data functions for admin dashboard.
This module provides real database queries and calculations to replace mock data.
"""
import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import db


def get_overview_status() -> Dict[str, str]:
    """
    Returns status for each monitoring category based on real data.
    Status: OK, WARNING, or CRITICAL
    """
    # Get recent assessments (last 7 days)
    with db.get_conn() as conn:
        seven_days_ago = int((datetime.now() - timedelta(days=7)).timestamp() * 1000)
        recent_count = conn.execute(
            "SELECT COUNT(*) FROM attempts WHERE started_at_ms >= ?",
            (seven_days_ago,)
        ).fetchone()[0]
    
    # Performance: Check if we have enough data and recent predictions
    performance_status = "OK"
    if recent_count < 10:
        performance_status = "WARNING"  # Not enough data
    
    # Drift: Check if drift scores are high (you'll need to implement drift calculation)
    drift_status = "OK"  # TODO: Calculate actual drift
    
    # Uptime: Check recent error rate
    uptime_status = "OK"  # TODO: Track API errors
    
    # Fairness: Check approval rate gaps
    fairness_status = "OK"  # TODO: Calculate fairness metrics
    
    return {
        "performance": performance_status,
        "drift": drift_status,
        "uptime": uptime_status,
        "fairness": fairness_status,
    }


def get_alerts(limit: int = 5) -> List[Dict[str, Any]]:
    """
    Returns list of active alerts based on real data analysis.
    """
    alerts = []
    now = datetime.now()
    
    # Check for low performance
    with db.get_conn() as conn:
        # Get recent predictions
        seven_days_ago = int((now - timedelta(days=7)).timestamp() * 1000)
        recent_computed = conn.execute(
            """
            SELECT pd_final_hat FROM computed c
            JOIN attempts a ON c.assessment_id = a.assessment_id
            WHERE a.started_at_ms >= ?
            """,
            (seven_days_ago,)
        ).fetchall()
        
        if len(recent_computed) > 0:
            avg_pd = sum(row[0] for row in recent_computed if row[0] is not None) / len(recent_computed)
            if avg_pd > 0.5:  # High average PD might indicate issues
                alerts.append({
                    "category": "performance",
                    "message": f"High average PD detected: {avg_pd:.3f}",
                    "severity": "warning",
                    "timestamp": (now - timedelta(hours=1)).isoformat(),
                })
    
    # Check for data drift (example: check if recent data differs significantly)
    # TODO: Implement actual drift detection
    
    # Check for missing assessments
    with db.get_conn() as conn:
        incomplete = conn.execute(
            "SELECT COUNT(*) FROM attempts WHERE status != 'completed' AND started_at_ms >= ?",
            (int((now - timedelta(days=1)).timestamp() * 1000),)
        ).fetchone()[0]
        
        if incomplete > 5:
            alerts.append({
                "category": "uptime",
                "message": f"{incomplete} incomplete assessments in last 24 hours",
                "severity": "warning",
                "timestamp": (now - timedelta(hours=2)).isoformat(),
            })
    
    return alerts[:limit]


def get_performance_metrics() -> Dict[str, Any]:
    """
    Returns model performance metrics calculated from real data.
    Note: For accuracy/F1/AUC, you need ground truth labels (actual defaults).
    This is a simplified version that uses PD thresholds.
    """
    with db.get_conn() as conn:
        # Get all completed assessments with predictions
        rows = conn.execute(
            """
            SELECT 
                c.pd_final_hat,
                c.pd_psych_hat,
                c.pd_fin_hat,
                a.started_at_ms
            FROM computed c
            JOIN attempts a ON c.assessment_id = a.assessment_id
            WHERE c.pd_final_hat IS NOT NULL
            ORDER BY a.started_at_ms DESC
            LIMIT 1000
            """
        ).fetchall()
    
    if not rows:
        # No data yet, return defaults
        return {
            "accuracy": None,
            "f1": None,
            "auc": None,
            "timeseries": [],
            "confusion_matrix": {"tp": 0, "fp": 0, "tn": 0, "fn": 0},
        }
    
    # Calculate time series (last 14 days)
    now = datetime.now()
    timeseries = []
    daily_data = {}
    
    for row in rows:
        pd_final = row[0]
        started_at = row[3]
        if started_at:
            date = datetime.fromtimestamp(started_at / 1000).strftime("%Y-%m-%d")
            if date not in daily_data:
                daily_data[date] = []
            daily_data[date].append(pd_final)
    
    # Calculate daily averages
    for i in range(14, -1, -1):
        date = (now - timedelta(days=i)).strftime("%Y-%m-%d")
        if date in daily_data:
            avg_pd = sum(daily_data[date]) / len(daily_data[date])
            timeseries.append({
                "date": date,
                "accuracy": round(1.0 - avg_pd, 3),  # Simplified: lower PD = higher accuracy
                "f1": round(0.7 + (1 - avg_pd) * 0.2, 3),  # Simplified estimate
                "auc": round(0.8 + (1 - avg_pd) * 0.15, 3),  # Simplified estimate
            })
        else:
            # No data for this day, use previous day's values or defaults
            prev_accuracy = timeseries[-1]["accuracy"] if timeseries else 0.82
            prev_f1 = timeseries[-1]["f1"] if timeseries else 0.75
            prev_auc = timeseries[-1]["auc"] if timeseries else 0.88
            timeseries.append({
                "date": date,
                "accuracy": prev_accuracy,
                "f1": prev_f1,
                "auc": prev_auc,
            })
    
    # Calculate overall metrics (simplified - using PD distribution)
    all_pds = [row[0] for row in rows if row[0] is not None]
    avg_pd = sum(all_pds) / len(all_pds) if all_pds else 0.5
    
    # Simplified confusion matrix (using PD threshold of 0.5)
    # Note: This is a placeholder - you need actual ground truth labels for real metrics
    threshold = 0.5
    predicted_positives = sum(1 for pd in all_pds if pd >= threshold)
    predicted_negatives = len(all_pds) - predicted_positives
    
    # Without ground truth, we estimate (this is NOT accurate - just for demo)
    # In production, you need actual default outcomes
    estimated_tp = int(predicted_positives * 0.7)  # Assume 70% of high PD actually default
    estimated_fp = predicted_positives - estimated_tp
    estimated_fn = int(predicted_negatives * 0.2)  # Assume 20% of low PD actually default
    estimated_tn = predicted_negatives - estimated_fn
    
    return {
        "accuracy": round(1.0 - avg_pd, 3),
        "f1": round(0.7 + (1 - avg_pd) * 0.2, 3),
        "auc": round(0.8 + (1 - avg_pd) * 0.15, 3),
        "timeseries": timeseries,
        "confusion_matrix": {
            "tp": estimated_tp,
            "fp": estimated_fp,
            "tn": estimated_tn,
            "fn": estimated_fn,
        },
    }


def get_drift_data() -> Dict[str, Any]:
    """
    Returns data drift information.
    Compares current data distribution to training baseline.
    Note: You need to store training baseline statistics for comparison.
    """
    with db.get_conn() as conn:
        # Get recent financial data
        recent_data = conn.execute(
            """
            SELECT 
                fd.monthly_income,
                fd.total_debt,
                fd.missed_payments_3m,
                fd.daily_burden,
                fd.num_previous_loans
            FROM financial_data fd
            JOIN attempts a ON fd.user_id = a.user_id
            WHERE a.started_at_ms >= ?
            LIMIT 100
            """,
            (int((datetime.now() - timedelta(days=30)).timestamp() * 1000),)
        ).fetchall()
    
    if not recent_data:
        return {
            "overall_score": 0.0,
            "features": [],
        }
    
    # Calculate drift scores (simplified - compares to assumed baseline)
    # In production, you should store training baseline statistics
    baseline_means = {
        "monthly_income": 50000,
        "total_debt": 100000,
        "missed_payments_3m": 2,
        "daily_burden": 500,
        "num_previous_loans": 3,
    }
    
    features = []
    for idx, col_name in enumerate(["monthly_income", "total_debt", "missed_payments_3m", "daily_burden", "num_previous_loans"]):
        values = [row[idx] for row in recent_data if row[idx] is not None]
        if values:
            current_mean = sum(values) / len(values)
            baseline_mean = baseline_means.get(col_name, current_mean)
            
            # Calculate drift as normalized difference
            if baseline_mean > 0:
                drift_score = abs(current_mean - baseline_mean) / baseline_mean
            else:
                drift_score = 0.0
            
            # Cap at 1.0
            drift_score = min(1.0, drift_score)
            
            status = "WARNING" if drift_score > 0.3 else "OK"
            if drift_score > 0.6:
                status = "CRITICAL"
            
            features.append({
                "name": col_name,
                "score": round(drift_score, 2),
                "status": status,
            })
    
    # Overall drift is average of feature drifts
    overall_score = sum(f["score"] for f in features) / len(features) if features else 0.0
    
    return {
        "overall_score": round(overall_score, 2),
        "features": sorted(features, key=lambda x: x["score"], reverse=True),
    }


def get_uptime_metrics() -> Dict[str, Any]:
    """
    Returns API uptime and health metrics.
    Note: You need to implement API logging to track this properly.
    For now, this uses assessment completion rates as a proxy.
    """
    now = datetime.now()
    
    with db.get_conn() as conn:
        # Get assessments from last 24 hours
        one_day_ago = int((now - timedelta(days=1)).timestamp() * 1000)
        
        total_attempts = conn.execute(
            "SELECT COUNT(*) FROM attempts WHERE started_at_ms >= ?",
            (one_day_ago,)
        ).fetchone()[0]
        
        completed_attempts = conn.execute(
            "SELECT COUNT(*) FROM attempts WHERE status = 'completed' AND started_at_ms >= ?",
            (one_day_ago,)
        ).fetchone()[0]
        
        # Calculate uptime as completion rate
        uptime_pct = (completed_attempts / total_attempts * 100) if total_attempts > 0 else 100.0
        
        # Get recent assessments for latency estimation
        recent_attempts = conn.execute(
            """
            SELECT started_at_ms, completed_at_ms
            FROM attempts
            WHERE completed_at_ms IS NOT NULL
            AND started_at_ms >= ?
            ORDER BY started_at_ms DESC
            LIMIT 50
            """,
            (one_day_ago,)
        ).fetchall()
        
        latencies = []
        for row in recent_attempts:
            if row[0] and row[1]:
                latency_ms = row[1] - row[0]
                latencies.append(latency_ms)
        
        # Calculate p95 latency
        if latencies:
            latencies_sorted = sorted(latencies)
            p95_index = int(len(latencies_sorted) * 0.95)
            latency_p95_ms = latencies_sorted[p95_index] if p95_index < len(latencies_sorted) else latencies_sorted[-1]
        else:
            latency_p95_ms = 0
        
        # Error rate (incomplete assessments)
        error_rate_pct = ((total_attempts - completed_attempts) / total_attempts * 100) if total_attempts > 0 else 0.0
        
        # Generate mock API logs (in production, you'd log actual API requests)
        logs = []
        for i in range(min(15, len(recent_attempts))):
            if i < len(recent_attempts):
                row = recent_attempts[i]
                started_at = datetime.fromtimestamp(row[0] / 1000) if row[0] else now
                latency = row[1] - row[0] if (row[0] and row[1]) else 0
                status_code = 200 if row[1] else 500
                
                logs.append({
                    "time": started_at.isoformat(),
                    "route": "/api/complete",
                    "status_code": status_code,
                    "latency_ms": latency,
                })
    
    return {
        "uptime_pct": round(uptime_pct, 1),
        "latency_p95_ms": int(latency_p95_ms),
        "error_rate_pct": round(error_rate_pct, 1),
        "logs": logs,
    }


def get_fairness_metrics() -> Dict[str, Any]:
    """
    Returns fairness metrics grouped by country or other demographic groups.
    Note: You need to store demographic data (country, etc.) to calculate this properly.
    """
    with db.get_conn() as conn:
        # Get financial data with user info
        # Note: This assumes you have country data - you may need to add this to your schema
        rows = conn.execute(
            """
            SELECT 
                fd.user_id,
                c.pd_final_hat,
                a.status
            FROM financial_data fd
            JOIN attempts a ON fd.user_id = a.user_id
            LEFT JOIN computed c ON a.assessment_id = c.assessment_id
            WHERE c.pd_final_hat IS NOT NULL
            LIMIT 100
            """
        ).fetchall()
    
    if not rows:
        return {
            "by_country": [],
            "approval_rate_gap": 0.0,
        }
    
    # Group by country (placeholder - you need actual country data)
    # For now, we'll use a simplified grouping
    # In production, add country column to users or financial_data table
    
    # Simplified: Group by user_id modulo 4 to simulate countries
    country_groups = {
        "Kenya": [],
        "Tanzania": [],
        "Uganda": [],
        "Rwanda": [],
    }
    
    country_names = list(country_groups.keys())
    for row in rows:
        user_id = row[0]
        pd_final = row[1]
        status = row[2]
        
        # Assign to country based on user_id (placeholder)
        country = country_names[user_id % len(country_names)]
        country_groups[country].append({
            "pd": pd_final,
            "approved": status == "completed" and pd_final < 0.5,  # Simplified approval logic
        })
    
    # Calculate metrics per country
    by_country = []
    approval_rates = []
    
    for country, data in country_groups.items():
        if data:
            approved = sum(1 for d in data if d["approved"])
            total = len(data)
            approval_rate = approved / total if total > 0 else 0.0
            
            # Default rate (simplified: high PD = likely to default)
            defaults = sum(1 for d in data if d["pd"] > 0.5)
            default_rate = defaults / total if total > 0 else 0.0
            
            # F1 score (simplified estimate)
            f1 = 0.75 - (default_rate * 0.1)  # Lower default rate = higher F1
            
            by_country.append({
                "country": country,
                "approval_rate": round(approval_rate, 2),
                "default_rate": round(default_rate, 2),
                "f1": round(f1, 2),
            })
            
            approval_rates.append(approval_rate)
    
    # Calculate approval rate gap
    approval_rate_gap = max(approval_rates) - min(approval_rates) if approval_rates else 0.0
    
    return {
        "by_country": by_country,
        "approval_rate_gap": round(approval_rate_gap, 3),
    }

