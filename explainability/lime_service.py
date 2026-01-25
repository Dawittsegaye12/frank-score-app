"""
LIME Service for FrankScore Explainability
Provides perturbation-based explanations as a fallback to SHAP.
"""
import os
import time
from typing import Any, Dict, List, Optional
import numpy as np

# Lazy imports
_lime = None
_joblib = None
_pd = None

def _load_deps():
    global _lime, _joblib, _pd
    if _lime is None:
        import lime
        import lime.lime_tabular
        import joblib
        import pandas as pd
        _lime = lime.lime_tabular
        _joblib = joblib
        _pd = pd

# Cached explainers and models
_explainers: Dict[str, Any] = {}
_models: Dict[str, Any] = {}
_feature_names: Dict[str, List[str]] = {}

# Feature names (same as shap_service)
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
                print(f"LIME: Extracted 'model' from dict for {model_name}")
            elif "best_estimator_" in loaded:
                model = loaded["best_estimator_"]
            else:
                model = loaded
        else:
            model = loaded
            
        _models[model_name] = model
        
        if "kenya" in model_name or "random_forest" in model_name:
            _feature_names[model_name] = KENYA_FEATURES
        else:
            _feature_names[model_name] = PSYCHOMETRIC_FEATURES
            
        return model
    except Exception as e:
        print(f"Error loading model {model_name}: {e}")
        return None


def get_explainer(model_name: str) -> Optional[Any]:
    """Get or create a LIME TabularExplainer for the model."""
    _load_deps()
    
    if model_name in _explainers:
        return _explainers[model_name]
    
    model = load_model(model_name)
    if model is None:
        return None
    
    feature_names = _feature_names.get(model_name, [])
    
    try:
        # Create synthetic training data for LIME (using reasonable ranges)
        # In production, use actual training data sample
        n_samples = 100
        n_features = len(feature_names)
        
        # Generate background data with reasonable distributions
        np.random.seed(42)
        training_data = np.random.randn(n_samples, n_features) * 0.3 + 0.5
        training_data = np.clip(training_data, 0, 1)
        
        explainer = _lime.LimeTabularExplainer(
            training_data,
            feature_names=feature_names,
            class_names=["Low Risk", "High Risk"],
            mode="classification"
        )
        _explainers[model_name] = explainer
        return explainer
    except Exception as e:
        print(f"Error creating LIME explainer for {model_name}: {e}")
        return None


def explain(
    model_name: str,
    features: Dict[str, float],
    top_n: int = 10
) -> Dict[str, Any]:
    """
    Compute LIME explanation for a single prediction.
    
    Args:
        model_name: Name of the model
        features: Dictionary of feature name -> value
        top_n: Number of top features to return
        
    Returns:
        Dictionary with prediction, top_positive, top_negative, meta
    """
    _load_deps()
    
    explainer = get_explainer(model_name)
    if explainer is None:
        return {
            "error": f"Could not load LIME explainer for model '{model_name}'"
        }
    
    model = _models.get(model_name)
    feature_names = _feature_names.get(model_name, [])
    
    # Build feature array
    X = np.array([features.get(fn, 0.0) for fn in feature_names])
    
    try:
        # Get prediction
        if hasattr(model, "predict_proba"):
            prediction = float(model.predict_proba(X.reshape(1, -1))[0, 1])
        else:
            prediction = float(model.predict(X.reshape(1, -1))[0])
        
        # Create predict function for LIME
        def predict_fn(x):
            if hasattr(model, "predict_proba"):
                return model.predict_proba(x)
            else:
                preds = model.predict(x)
                return np.column_stack([1 - preds, preds])
        
        # Get LIME explanation
        exp = explainer.explain_instance(
            X,
            predict_fn,
            num_features=top_n * 2,
            num_samples=500
        )
        
        # Extract feature contributions
        contributions = exp.as_list()
        
        top_positive = []
        top_negative = []
        
        for feature_cond, weight in contributions:
            # Parse feature name from LIME format (e.g., "conscientiousness <= 0.47")
            # LIME uses formats like: "feature < value", "value < feature <= value", etc.
            import re
            # Extract the feature name by removing comparison operators and numbers
            # Match the feature name (word characters including underscores)
            match = re.search(r'([a-zA-Z_][a-zA-Z0-9_]*)', feature_cond)
            if match:
                feature_name = match.group(1)
            else:
                feature_name = feature_cond.split()[0] if " " in feature_cond else feature_cond
            
            entry = {
                "feature": feature_name,
                "impact": round(float(weight), 4),
                "raw_value": round(features.get(feature_name, 0.0), 4)
            }
            
            if weight > 0:
                if len(top_positive) < top_n:
                    top_positive.append(entry)
            else:
                if len(top_negative) < top_n:
                    top_negative.append(entry)
        
        return {
            "model": model_name,
            "method": "lime",
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
            "error": f"LIME computation failed: {str(e)}"
        }
