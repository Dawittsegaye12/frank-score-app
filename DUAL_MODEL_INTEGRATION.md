# Dual Model Admin Dashboard Integration Guide

## Overview

Your FrankScore app uses **two separate ML models**:

1. **XGBoost Model** (`models/xgb_model.joblib`)
   - Purpose: Predicts **Psychometric PD** (`pd_psych_hat`)
   - Input: 15 trait scores (from questionnaire + metadata)
   - Output: Probability of default based on psychometric traits

2. **Random Forest Model** (`models/random_forest.joblib`)
   - Purpose: Predicts **Financial PD** (`pd_fin_hat`)
   - Input: Financial features (income, debt, payments, etc.)
   - Output: Probability of default based on financial profile

3. **Combined Prediction** (`pd_final_hat`)
   - Combines both model predictions
   - Used for final decision making

---

## What's New in the Dual Model Dashboard

The updated admin dashboard (`admin_data_dual_models.py`) now tracks **both models separately**:

### 1. **Overview Page**
- Shows status for both models individually
- Alerts specific to each model
- Combined system status

### 2. **Performance Page**
- **Combined metrics**: Overall accuracy, F1, AUC
- **XGBoost metrics**: Psychometric model performance
- **Random Forest metrics**: Financial model performance
- **Time series**: Shows all three metrics over time
- **Prediction counts**: How many predictions each model made

### 3. **Drift Page**
- **XGBoost drift**: Tracks drift in trait distributions
- **Random Forest drift**: Tracks drift in financial features
- **Overall drift**: Combined view

### 4. **Uptime Page**
- **XGBoost success rate**: % of assessments with psychometric predictions
- **Random Forest success rate**: % of assessments with financial predictions
- **Overall uptime**: System-wide metrics

### 5. **Fairness Page**
- **Combined fairness**: Overall metrics by country
- **XGBoost fairness**: Psychometric model fairness per country
- **Random Forest fairness**: Financial model fairness per country

---

## How to Switch to Dual Model Tracking

### Step 1: Update app.py

Change the import from:
```python
import admin_mock_data
```

To:
```python
import admin_data_dual_models as admin_mock_data
```

Or explicitly:
```python
import admin_data_dual_models

# Then update each route:
status = admin_data_dual_models.get_overview_status()
metrics = admin_data_dual_models.get_performance_metrics()
# etc.
```

### Step 2: Restart Server

The dashboard will now show separate metrics for both models!

---

## Understanding the Data Structure

### Performance Metrics Structure

```python
{
    "combined": {
        "accuracy": 0.825,
        "f1": 0.752,
        "auc": 0.891
    },
    "xgb_model": {
        "accuracy": 0.830,
        "f1": 0.760,
        "auc": 0.895,
        "avg_pd": 0.245,  # Average psychometric PD
        "prediction_count": 1250  # Number of predictions made
    },
    "rf_model": {
        "accuracy": 0.820,
        "f1": 0.748,
        "auc": 0.888,
        "avg_pd": 0.280,  # Average financial PD
        "prediction_count": 1180  # Number of predictions made
    },
    "timeseries": [...],
    "confusion_matrix": {...}
}
```

### Drift Data Structure

```python
{
    "overall_score": 0.68,
    "features": [...],  # All features combined
    "xgb_features": [  # XGBoost-specific (traits)
        {"name": "trait_impulsivity", "score": 0.45, "status": "OK"},
        ...
    ],
    "rf_features": [  # Random Forest-specific (financial)
        {"name": "monthly_income", "score": 0.78, "status": "WARNING"},
        ...
    ]
}
```

### Uptime Metrics Structure

```python
{
    "uptime_pct": 99.2,
    "latency_p95_ms": 450,
    "error_rate_pct": 0.8,
    "xgb_success_rate": 98.5,  # % of assessments with XGBoost predictions
    "rf_success_rate": 97.2,   # % of assessments with RF predictions
    "logs": [...]
}
```

---

## What Each Model Tracks

### XGBoost Model (Psychometric)

**Input Features** (from `computed.traits_json`):
- 15 trait scores (impulsivity, risk_attitude, saving_orientation, etc.)
- Computed from: questionnaire answers + metadata

**What to Monitor**:
- Average PD values (should be reasonable, not too high/low)
- Prediction success rate (should be close to 100%)
- Trait distribution drift (are traits changing over time?)

**Alerts**:
- High average PD (> 0.6) - model may be too conservative
- Low average PD (< 0.1) - model may be too lenient
- Missing predictions - model may be failing

### Random Forest Model (Financial)

**Input Features** (from `financial_data` table):
- monthly_income
- total_debt
- missed_payments_3m
- daily_burden
- num_previous_loans
- amount_bucket
- loan_duration_days
- age
- etc.

**What to Monitor**:
- Average PD values
- Prediction success rate
- Financial feature drift (are financial profiles changing?)

**Alerts**:
- High average PD (> 0.6)
- Low average PD (< 0.1)
- Missing predictions
- Feature drift (e.g., income distribution changing)

---

## Key Metrics to Watch

### 1. Model Health
- **XGBoost success rate**: Should be > 95%
- **RF success rate**: Should be > 95%
- **Missing predictions**: Should be < 5%

### 2. Model Performance
- **Average PD**: Should be between 0.2-0.4 (reasonable default rate)
- **PD distribution**: Should be balanced (not all high or all low)
- **Prediction consistency**: Both models should agree on most cases

### 3. Data Drift
- **Trait drift**: Are psychometric traits changing? (XGBoost)
- **Financial drift**: Are financial profiles changing? (RF)
- **Drift threshold**: > 0.3 = WARNING, > 0.6 = CRITICAL

### 4. Model Agreement
- **Disagreement rate**: How often do models disagree?
- **High disagreement**: May indicate data quality issues

---

## Troubleshooting

### Issue: One model shows 0 predictions

**Possible causes**:
1. Model file not loaded (check startup logs)
2. Missing input data (traits or financial data)
3. Model prediction failed (check error logs)

**Solution**:
- Check `app.py` startup: Are both models loaded?
- Check database: Do assessments have required data?
- Check logs: Are there prediction errors?

### Issue: High drift scores

**Possible causes**:
1. Data distribution actually changed (new user demographics)
2. Baseline statistics are outdated
3. Data quality issues

**Solution**:
- Verify if change is expected (e.g., new market entry)
- Update baseline statistics if needed
- Check data quality (missing values, outliers)

### Issue: Models disagree frequently

**Possible causes**:
1. Different feature sets (one model sees different data)
2. Model calibration issues
3. Data inconsistencies

**Solution**:
- Check if both models receive complete data
- Recalibrate models if needed
- Investigate data inconsistencies

---

## Next Steps

1. **Switch to dual model tracking**: Update import in `app.py`
2. **Monitor both models**: Watch for alerts specific to each model
3. **Compare performance**: See which model performs better
4. **Track drift separately**: Monitor trait drift vs financial drift
5. **Add ground truth**: For real accuracy metrics (see `ADMIN_INTEGRATION_GUIDE.md`)

---

## Summary

The dual model dashboard gives you:
- ✅ Separate monitoring for each model
- ✅ Combined metrics for overall system
- ✅ Model-specific alerts and drift detection
- ✅ Better visibility into which model might be having issues
- ✅ Comparison between psychometric and financial predictions

Switch the import and you're ready to monitor both models! 🚀



