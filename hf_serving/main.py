from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Dict, Any
import os, joblib
import numpy as np
import pandas as pd
from huggingface_hub import hf_hub_download

app = FastAPI(title="FrankScore Model API", version="1.0")

# -------- Request schema --------
class PredictRequest(BaseModel):
    assessment_id: str
    features: Dict[str, Any]

# -------- Globals (loaded once) --------
kenya_model = None
psych_model = None

# -------- Constants for fallback logic --------
PSYCH_FEATURES = [
    "conscientiousness", "impulsivity", "financial_self_confidence", "planning_horizon",
    "self_control", "locus_of_control", "honesty", "integrity_rule_following",
    "obligation_to_repay", "grit_perseverance", "present_bias_time_preference",
    "risk_attitude", "financial_decision_quality", "spending_vs_saving",
    "commitment_follow_through"
]

def load_joblib_local(path: str):
    if not os.path.exists(path):
        raise RuntimeError(f"Missing artifact: {path}")
    loaded = joblib.load(path)
    # Handle dict-wrapped models (common in this project)
    if isinstance(loaded, dict):
        if "model" in loaded:
            return loaded["model"]
        if "best_estimator_" in loaded:
            return loaded["best_estimator_"]
    return loaded

def load_joblib_from_hf(repo_id: str, filename: str):
    local_path = hf_hub_download(repo_id=repo_id, filename=filename)
    return load_joblib_local(local_path)

# ✅ Fix for HF "Not Found": add a root route
@app.get("/")
def home():
    return {
        "status": "ok",
        "message": "FrankScore API is running",
        "health": "/health",
        "docs": "/docs",
        "endpoints": {
            "predict_kenya": "POST /predict/kenya",
            "predict_psych": "POST /predict/psych"
        }
    }

# Optional: if you prefer redirect instead of JSON:
# @app.get("/")
# def home():
#     return RedirectResponse(url="/docs")

@app.get("/health")
def health():
    return {
        "status": "ok",
        "kenya_ok": kenya_model is not None,
        "psych_ok": psych_model is not None
    }

@app.on_event("startup")
def startup():
    """
    Choose ONE strategy:
    Strategy A: load from local ./models (default for Docker Space with baked-in models)
    Strategy B: load from HF model repo via hf_hub_download
    """
    global kenya_model, psych_model

    STRATEGY = os.getenv("ARTIFACT_STRATEGY", "local")  # "local" or "hf"
    print(f"Loading models with strategy: {STRATEGY}")

    try:
        if STRATEGY == "local":
            if os.path.exists("models/kenya_model.joblib"):
                kenya_model = load_joblib_local("models/kenya_model.joblib")
                print("Kenya model loaded locally")
            else:
                print("Kenya model file not found at models/kenya_model.joblib")

            if os.path.exists("models/psych_model.joblib"):
                psych_model = load_joblib_local("models/psych_model.joblib")
                print("Psychometric model loaded locally")
            else:
                print("Psychometric model file not found at models/psych_model.joblib")

        elif STRATEGY == "hf":
            # Put your artifacts in a HF model repo like: "your-username/frankscore-artifacts"
            repo = os.environ["HF_MODEL_REPO_ID"]
            kenya_model = load_joblib_from_hf(repo, "kenya_model.joblib")
            psych_model = load_joblib_from_hf(repo, "psych_model.joblib")
            print("Models loaded from Hugging Face repo")

        else:
            raise RuntimeError("Unknown ARTIFACT_STRATEGY")

    except Exception as e:
        print(f"Error loading models: {e}")
        # Build won't fail, but health check will show status

def pd_to_score(pd_val: float) -> float:
    return round((1.0 - pd_val) * 100.0, 2)

def pd_to_band(pd_val: float) -> str:
    # Match dashboard thresholds: <0.05 Low, <0.15 Medium, else High
    if pd_val < 0.05:
        return "Low"
    if pd_val < 0.15:
        return "Medium"
    return "High"

@app.post("/predict/kenya")
def predict_kenya(req: PredictRequest):
    if kenya_model is None:
        raise HTTPException(503, "Kenya model not loaded")

    try:
        # Create DataFrame from features
        if hasattr(kenya_model, "feature_names_in_"):
            cols = kenya_model.feature_names_in_.tolist()
            data = {c: [req.features.get(c, 0.0)] for c in cols}
            X = pd.DataFrame(data)
        else:
            X = pd.DataFrame([req.features])

        # Predict
        if hasattr(kenya_model, "predict_proba"):
            probs = kenya_model.predict_proba(X)
            if probs.shape[1] >= 2:
                pd_val = float(probs[0][1])
            else:
                pd_val = float(probs[0][0])
        else:
            pd_val = float(kenya_model.predict(X)[0])

        return {
            "assessment_id": req.assessment_id,
            "prediction_pd": pd_val,
            "score_0_100": pd_to_score(pd_val),
            "risk_band": pd_to_band(pd_val),
            "model_name": "kenya (random_forest)",
            "model_version": os.getenv("KENYA_MODEL_VERSION", "v1.0")
        }
    except Exception as e:
        print(f"Prediction error: {e}")
        raise HTTPException(500, f"Prediction failed: {str(e)}")

@app.post("/predict/psych")
def predict_psych(req: PredictRequest):
    if psych_model is None:
        raise HTTPException(503, "Psychometric model not loaded")

    try:
        features_list = []
        # Try to find expected columns if possible, else use constant list
        if isinstance(psych_model, dict) and "feature_columns" in psych_model:
            cols = psych_model["feature_columns"]
        else:
            cols = PSYCH_FEATURES

        for c in cols:
            val = req.features.get(c)
            if val is None:
                # Try some known aliases
                if c == "impulsivity_control":
                    val = req.features.get("impulsivity")
                elif c == "present_bias_control":
                    val = req.features.get("present_bias_time_preference")
                elif c == "risk_management":
                    val = req.features.get("risk_attitude")
                elif c == "saving_orientation":
                    val = req.features.get("spending_vs_saving")
                elif c == "follow_through":
                    val = req.features.get("commitment_follow_through")
                else:
                    val = 0.0

            features_list.append(float(val) if val is not None else 0.0)

        X = np.array([features_list])

        if hasattr(psych_model, "predict_proba"):
            probs = psych_model.predict_proba(X)
            if probs.shape[1] >= 2:
                pd_val = float(probs[0][1])
            else:
                pd_val = float(probs[0][0])
        else:
            pd_val = float(psych_model.predict(X)[0])

        # Normalize/Clamp
        pd_val = max(0.0, min(1.0, pd_val))

        return {
            "assessment_id": req.assessment_id,
            "prediction_pd": pd_val,
            "score_0_100": pd_to_score(pd_val),
            "risk_band": pd_to_band(pd_val),
            "model_name": "psychometric (xgboost)",
            "model_version": os.getenv("PSYCH_MODEL_VERSION", "v1.0")
        }
    except Exception as e:
        print(f"Prediction error: {e}")
        raise HTTPException(500, f"Prediction failed: {str(e)}")
