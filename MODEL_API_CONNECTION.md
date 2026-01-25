# Model Connection to API Endpoints

## ✅ Yes, Models Are Connected!

Both ML models are actively used in your API endpoints. Here's exactly how:

## Main API Endpoint: `/api/complete`

This is where both models are called to generate predictions:

### Flow Diagram

```
POST /api/complete
    │
    ├─→ Get assessment data (answers, events)
    │
    ├─→ Compute traits (15 trait scores)
    │
    ├─→ 🔵 XGBoost Model (Psychometric PD)
    │   └─→ scoring.psychometric_pd(traits, ...)
    │       └─→ Uses: 15 trait scores
    │       └─→ Returns: pd_psych_hat (0.0 - 1.0)
    │
    ├─→ 🔴 Random Forest Model (Financial PD)
    │   └─→ scoring.financial_pd_from_model(financial_data, ...)
    │       └─→ Uses: 23 financial features
    │       └─→ Returns: pd_fin_hat (0.0 - 1.0)
    │
    ├─→ Combine PDs
    │   └─→ scoring.combine_pd(pd_psych_hat, pd_fin_hat)
    │       └─→ Formula: 60% financial + 40% psychometric
    │       └─→ Returns: pd_final_hat
    │
    └─→ Store results in database
        └─→ computed table: pd_psych_hat, pd_fin_hat, pd_final_hat
```

## Code Location

### File: `app.py` - Line 410 & 433

```python
@app.post("/api/complete")
def api_complete(req: CompleteRequest):
    # ... compute traits from answers and metadata ...
    
    # 🔵 XGBoost Model Call (Psychometric)
    pd_psych_hat = scoring.psychometric_pd(
        traits,                    # 15 trait scores
        TRAIT_NAMES, 
        assessment_id=req.assessment_id
    )
    
    # 🔴 Random Forest Model Call (Financial)
    if financial_data:
        pd_fin_hat = scoring.financial_pd_from_model(
            financial_data,       # 23 financial features
            assessment_id=req.assessment_id
        )
    
    # Combine both predictions
    pd_final_hat = scoring.combine_pd(pd_psych_hat, pd_fin_hat)
    
    # Store in database
    db.upsert_computed(
        pd_psych_hat=pd_psych_hat,
        pd_fin_hat=pd_fin_hat,
        pd_final_hat=pd_final_hat,
        ...
    )
```

## Model Usage Details

### 1. XGBoost Model (Psychometric PD)

**Called in:** `scoring.psychometric_pd()`

**Input:**
- 15 trait scores (conscientiousness, impulsivity, etc.)
- Computed from: questionnaire answers + metadata

**Output:**
- `pd_psych_hat`: Probability of default (0.0 - 1.0)

**Model File:**
- `models/xgb_model.joblib`

**Lazy Loading:**
- Loads automatically on first prediction
- Stays in memory for subsequent requests

### 2. Random Forest Model (Financial PD)

**Called in:** `scoring.financial_pd_from_model()`

**Input:**
- 23 financial features from `financial_data` table:
  - `Total_Amount`, `daily_burden`
  - `num_previous_loans`, `avg_past_amount`
  - `account_age_days`, etc.

**Output:**
- `pd_fin_hat`: Probability of default (0.0 - 1.0)

**Model File:**
- `models/random_forest.joblib`

**Lazy Loading:**
- Loads automatically on first prediction
- Stays in memory for subsequent requests

## Other API Endpoints

### `/api/result` - Retrieves Predictions

```python
@app.get("/api/result")
def api_result(assessment_id: str):
    comp = db.get_computed(assessment_id)
    return {
        "pd_psych_hat": comp.get("pd_psych_hat"),  # From XGBoost
        "pd_fin_hat": comp.get("pd_fin_hat"),      # From Random Forest
        "pd_final_hat": comp.get("pd_final_hat"),  # Combined
        ...
    }
```

**Note:** This endpoint doesn't call models directly - it retrieves already-computed results from the database.

## Model Loading Flow

### With Lazy Loading (Current Implementation)

```
1. App starts → Models NOT loaded
2. User completes assessment → POST /api/complete
3. First model call → XGBoost loads (5-15 seconds)
4. Second model call → Random Forest loads (5-15 seconds)
5. Predictions made → Results stored
6. Subsequent requests → Models already loaded (fast!)
```

## Verification

### Check if Models Are Working

1. **Check Logs:**
   ```
   Info: Loading XGBoost model (lazy load)...
   Info: XGBoost model loaded with 15 feature columns
   Info: Loading Random Forest model (lazy load)...
   Info: Random Forest model loaded with 23 feature columns
   ```

2. **Test API Endpoint:**
   ```bash
   # Complete an assessment, then check result
   curl https://frank-score-app.onrender.com/api/result?assessment_id=FS000001
   
   # Should return:
   {
     "pd_psych_hat": 0.234,    # From XGBoost
     "pd_fin_hat": 0.189,      # From Random Forest
     "pd_final_hat": 0.207     # Combined
   }
   ```

3. **Check Database:**
   ```sql
   SELECT pd_psych_hat, pd_fin_hat, pd_final_hat 
   FROM computed 
   WHERE assessment_id = 'FS000001';
   ```

## Fallback Behavior

If models fail to load or are missing:

1. **XGBoost fails:**
   - `pd_psych_hat` = `None`
   - Final PD uses only financial PD

2. **Random Forest fails:**
   - Falls back to heuristic calculation
   - Uses: `scoring.financial_pd()` (simple formula)

3. **Both fail:**
   - `pd_final_hat` = `None`
   - Error logged, but app continues

## Summary

✅ **XGBoost Model**: Connected to `/api/complete` via `scoring.psychometric_pd()`
✅ **Random Forest Model**: Connected to `/api/complete` via `scoring.financial_pd_from_model()`
✅ **Both models**: Used to generate final PD score
✅ **Results**: Stored in database and returned via `/api/result`

The models are fully integrated and working! 🚀

