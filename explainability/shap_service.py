"""
SHAP Service for FrankScore Explainability
Provides TreeExplainer-based explanations for XGBoost and RandomForest models.
"""
import os
import json
import time
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

# Lazy imports to avoid startup slowdown if not used
_shap = None
_joblib = None
_pd = None

def _load_deps():
    global _shap, _joblib, _pd
    if _shap is None:
        import shap
        import joblib
        import pandas as pd
        _shap = shap
        _joblib = joblib
        _pd = pd

# Cached explainers (loaded once)
_explainers: Dict[str, Any] = {}
_models: Dict[str, Any] = {}
_feature_names: Dict[str, List[str]] = {}

# Feature names for each model (from training)
KENYA_FEATURES = [
    "customer_id", "num_previous_loans", "avg_time_bw_loans", "avg_past_amount",
    "avg_past_daily_burden", "std_past_amount", "std_past_daily_burden",
    "trend_in_amount", "trend_in_burden", "Total_Amount", "daily_burden",
    "amount_ratio", "burden_ratio", "amount_bucket", "burden_percentile",
]

PSYCHOMETRIC_FEATURES = [
    "conscientiousness", "impulsivity", "financial_self_confidence",
    "planning_horizon", "self_control", "locus_of_control", "honesty",
    "integrity_rule_following", "obligation_to_repay", "grit_perseverance",
    "present_bias_time_preference", "risk_attitude", "financial_decision_quality",
    "spending_vs_saving", "commitment_follow_through",
]


def load_model(model_name: str) -> Optional[Any]:
    """Load and cache a model by name."""
    _load_deps()
    
    if model_name in _models:
        return _models[model_name]
    
    model_paths = {
        "kenya": "models/random_forest.joblib",
        "psychometric": "models/xgb_model.joblib",
        "random_forest": "models/random_forest.joblib",
        "xgb": "models/xgb_model.joblib",
    }
    
    path = model_paths.get(model_name)
    if not path or not os.path.exists(path):
        return None
    
    try:
        loaded = _joblib.load(path)
        
        # Handle case where model is saved as a dictionary (common for pipelines)
        if isinstance(loaded, dict):
            if "model" in loaded:
                model = loaded["model"]
                print(f"Extracted 'model' from dict for {model_name}")
            elif "best_estimator_" in loaded:
                model = loaded["best_estimator_"]
            else:
                # Use the dict itself (might be a custom wrapper)
                model = loaded
        else:
            model = loaded
            
        _models[model_name] = model
        
        # Set feature names
        if "kenya" in model_name or "random_forest" in model_name:
            _feature_names[model_name] = KENYA_FEATURES
        else:
            _feature_names[model_name] = PSYCHOMETRIC_FEATURES
            
        return model
    except Exception as e:
        print(f"Error loading model {model_name}: {e}")
        return None


def get_explainer(model_name: str) -> Optional[Any]:
    """Get or create a SHAP TreeExplainer for the model."""
    _load_deps()
    
    if model_name in _explainers:
        return _explainers[model_name]
    
    model = load_model(model_name)
    if model is None:
        return None
    
    try:
        # Use TreeExplainer for tree-based models (XGBoost, RandomForest)
        explainer = _shap.TreeExplainer(model)
        _explainers[model_name] = explainer
        return explainer
    except Exception as e:
        print(f"Error creating SHAP explainer for {model_name}: {e}")
        return None


def explain(
    model_name: str,
    features: Dict[str, float],
    top_n: int = 10
) -> Dict[str, Any]:
    """
    Compute SHAP values for a single prediction.
    
    Args:
        model_name: Name of the model (kenya, psychometric, xgb, random_forest)
        features: Dictionary of feature name -> value
        top_n: Number of top features to return
        
    Returns:
        Dictionary with prediction, top_positive, top_negative, meta
    """
    _load_deps()
    
    explainer = get_explainer(model_name)
    if explainer is None:
        return {
            "error": f"Could not load explainer for model '{model_name}'",
            "suggestion": "Try using LIME instead (method=lime)"
        }
    
    model = _models.get(model_name)
    feature_names = _feature_names.get(model_name, [])
    
    # Build feature array in correct order
    X = np.array([[features.get(fn, 0.0) for fn in feature_names]])
    
    try:
        # Get prediction
        if hasattr(model, "predict_proba"):
            prediction = float(model.predict_proba(X)[0, 1])
        else:
            prediction = float(model.predict(X)[0])
        
        # Get SHAP values
        shap_values = explainer.shap_values(X)
        
        # Handle different SHAP output formats
        if isinstance(shap_values, list):
            # Binary classification: use class 1
            sv = shap_values[1][0] if len(shap_values) > 1 else shap_values[0][0]
        else:
            sv = shap_values[0]
        
        # Pair feature names with SHAP values
        contributions = list(zip(feature_names, sv))
        
        # Sort by absolute value
        sorted_contribs = sorted(contributions, key=lambda x: abs(x[1]), reverse=True)
        
        # Split into positive and negative
        top_positive = []
        top_negative = []
        
        for fname, sval in sorted_contribs:
            entry = {
                "feature": fname,
                "impact": round(float(sval), 4),
                "raw_value": round(features.get(fname, 0.0), 4)
            }
            if sval > 0:
                if len(top_positive) < top_n:
                    top_positive.append(entry)
            else:
                if len(top_negative) < top_n:
                    top_negative.append(entry)
            
            if len(top_positive) >= top_n and len(top_negative) >= top_n:
                break
        
        return {
            "model": model_name,
            "method": "shap",
            "prediction": round(prediction, 4),
            "top_positive": top_positive,
            "top_negative": top_negative,
            "meta": {
                "model_version": "1.0",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "num_features": len(feature_names)
            }
        }
        
    except Exception as e:
        return {
            "error": f"SHAP computation failed: {str(e)}",
            "suggestion": "Try using LIME instead (method=lime)"
        }
