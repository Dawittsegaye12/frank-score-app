# Model Version Compatibility Issue

## Problem

The financial PD prediction is showing as `null` (dashed) because of a scikit-learn version incompatibility.

**Error:**
```
AttributeError: 'SimpleImputer' object has no attribute '_fill_dtype'
```

**Root Cause:**
- The Random Forest model (`models/random_forest.joblib`) was trained with **scikit-learn 1.4.2**
- Current environment has **scikit-learn 1.8.0**
- The model pipeline uses `SimpleImputer` which has API changes between versions

## Current Status

The application now includes a **fallback calculation** that uses financial data heuristics when the model fails. However, for accurate predictions, the model should be retrained.

## Solutions

### Option 1: Retrain the Model (Recommended)

Retrain the Random Forest model with the current scikit-learn version:

```bash
# Make sure you have the training data
# Then retrain using model_training_improved.py or your training script
python model_training_improved.py
```

### Option 2: Downgrade scikit-learn

Match the training environment version:

```bash
pip install scikit-learn==1.4.2
```

**Warning:** This may cause compatibility issues with other packages.

### Option 3: Use Fallback (Current Implementation)

The application now automatically falls back to a simple heuristic-based calculation when the model fails. This provides a basic PD estimate but is less accurate than the trained model.

## Fallback Calculation

When the model fails, the system uses:
- `Total_Amount`: Total loan amount
- `daily_burden`: Daily payment burden
- `num_previous_loans`: Number of previous loans

Formula:
```
burden_ratio = daily_burden / (Total_Amount / 30)
pd_fin_hat = min(1.0, max(0.0, burden_ratio * 0.3 + (1 - min(1.0, num_loans / 10)) * 0.2))
```

## Verification

To check if the model is working:

```python
import scoring
import db

scoring.load_rf_model()
financial_data = db.get_financial_data(1)  # user_id 1
result = scoring.financial_pd_from_model(financial_data)
print(f"Model prediction: {result}")
```

If it returns `None`, the model is failing and the fallback will be used.

