# Why pd_psych_hat is Always 0.9177

## Summary
Despite varying trait values (0.3219 to 0.8633), `pd_psych_hat` always returns **0.9177**. This is **NOT a code issue** - the code is working correctly. The problem is with the **trained model itself**.

## What's Working Correctly ✅

### 1. Traits Are Varying
From assessment FS000012:
- `obligation_to_repay`: 0.3219 (lowest)
- `financial_decision_quality`: 0.8633 (highest)
- Range: 0.3219 to 0.8633 (variation of 0.5414)

### 2. Feature Vector Construction
The feature vector is correctly built with varying values:
```
[0.6407, 0.4644, 0.5355, 0.8390, 0.7333, 0.3600, 0.6222, 0.7887, 
 0.3219, 0.7176, 0.3279, 0.6667, 0.8633, 0.3865, 0.3600]
```
- Min: 0.3219
- Max: 0.8633
- Mean: 0.5752

### 3. Trait-to-Feature Mapping
All 15 traits correctly map to model features:
- `impulsivity` → `impulsivity_control` ✓
- `present_bias_time_preference` → `present_bias_control` ✓
- `risk_attitude` → `risk_management` ✓
- `spending_vs_saving_orientation` → `saving_orientation` ✓
- `commitment_follow_through` → `follow_through` ✓
- 10 others match directly ✓

### 4. Model Receives Correct Input
The model receives a properly formatted feature vector with varying values in the correct order.

## The Problem ❌

### Model Always Outputs Same Value
Testing shows the model **does not respond to input changes**:

| Input | pd_psych_hat |
|-------|--------------|
| All features = 0.3 (low) | 0.9177 |
| All features = 0.8 (high) | 0.9177 |
| Actual varying values (0.32-0.86) | 0.9177 |

**Conclusion**: The model is **degenerate** - it always predicts the same probability regardless of input.

## Why This Happens

Possible causes:
1. **Model trained on imbalanced data** - Always predicts majority class
2. **Model not properly trained** - May have converged to a constant
3. **Model configuration issue** - `base_score` or other hyperparameters set incorrectly
4. **Model file corruption** - Model artifact may be damaged
5. **Training data issue** - All training examples had similar outcomes

## Evidence

From the debug output:
```
Raw proba output: [0.0823344 0.9176656]
```

The model outputs:
- Class 0 probability: 0.0823 (8.23%)
- Class 1 probability: 0.9177 (91.77%)

This suggests the model was trained on data where ~91.77% of examples were class 1 (default), and it learned to always predict this regardless of features.

## Solution

### Option 1: Retrain the Model (Recommended)
1. Check training data balance
2. Adjust class weights (`scale_pos_weight`)
3. Verify model training completed successfully
4. Test model on validation set to ensure it varies predictions

### Option 2: Use Deterministic Fallback
If model is unavailable, the code already has a fallback mechanism (currently returns `None`). You could implement a deterministic formula based on traits.

### Option 3: Check Model Training Script
Review `model_rraining .py` to ensure:
- Model is being trained correctly
- Validation metrics show model is learning
- Model is saved correctly

## Code Status

**The code in `scoring.py` is correct:**
- ✅ Traits are computed correctly
- ✅ Feature vector is constructed correctly
- ✅ Model is loaded correctly
- ✅ Predictions are made correctly

**The issue is with the model artifact (`models/xgb_model.joblib`):**
- ❌ Model always outputs same prediction
- ❌ Model does not respond to input variations

## Next Steps

1. **Verify model training**: Check if the model was trained correctly
2. **Retrain model**: Train a new model with proper validation
3. **Test new model**: Ensure new model produces varying predictions
4. **Replace model file**: Copy new model to `models/xgb_model.joblib`

## Current Behavior

- **Traits**: ✅ Varying correctly (0.32-0.86)
- **Feature vector**: ✅ Correctly constructed
- **Model input**: ✅ Correct format and values
- **Model output**: ❌ Always 0.9177 (broken model)

The code is working as designed. The model needs to be retrained.

