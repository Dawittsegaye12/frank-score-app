"""
Debug script to check SHAP explainer creation
"""
import joblib
import shap
import xgboost
import sklearn
import sys

print(f"Python: {sys.version}")
print(f"XGBoost: {xgboost.__version__}")
print(f"Scikit-learn: {sklearn.__version__}")
print(f"SHAP: {shap.__version__}")

try:
    print("\nLoading psychometric model...")
    model = joblib.load("models/xgb_model.joblib")
    print(f"Model type: {type(model)}")
    
    if isinstance(model, dict):
        print(f"Model keys: {model.keys()}")
        # Try to find the actual model
        if "model" in model:
            model = model["model"]
            print("Found 'model' key, using that.")
        elif "best_estimator_" in model: # sklearn searchCV
             model = model["best_estimator_"]
             print("Found 'best_estimator_' key, using that.")
    
    print("Creating TreeExplainer...")
    explainer = shap.TreeExplainer(model)
    print("SUCCESS: TreeExplainer created")
    
except Exception as e:
    print(f"\nFAILURE: {e}")
    import traceback
    traceback.print_exc()
