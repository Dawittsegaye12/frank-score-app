"""
Improved Model Training Script

Key improvements:
1. Normalizes traits to [0,1] range to match inference
2. Adds model validation checks
3. Tests model responsiveness
4. Better monitoring and diagnostics
"""

DATA_PATH = r"synthetic_traits_12k_userid_FS.csv"

import os, json
from datetime import datetime

import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import (
    roc_auc_score,
    average_precision_score,
    brier_score_loss,
)

from xgboost import XGBClassifier
import joblib


def make_run_dir(base_dir: str = "runs") -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = os.path.join(base_dir, ts)
    os.makedirs(run_dir, exist_ok=True)
    return run_dir


def save_json(obj, path: str):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)


def evaluate_prob_only(model, X, y, split_name: str):
    """
    Probability-only evaluation:
    - No thresholding
    - Metrics that assess ranking + probability quality
    """
    pd_hat = model.predict_proba(X)[:, 1]

    metrics = {
        "split": split_name,
        "n": int(len(y)),
        "positive_rate": float(np.mean(y)),
        "roc_auc": float(roc_auc_score(y, pd_hat)),
        "pr_auc": float(average_precision_score(y, pd_hat)),
        "brier": float(brier_score_loss(y, pd_hat)),
        "pred_mean": float(np.mean(pd_hat)),
        "pred_std": float(np.std(pd_hat)),
        "pred_min": float(np.min(pd_hat)),
        "pred_max": float(np.max(pd_hat)),
    }

    print(f"\n=== {split_name} (probability-only) ===")
    print(
        f"ROC-AUC: {metrics['roc_auc']:.4f} | "
        f"PR-AUC: {metrics['pr_auc']:.4f} | "
        f"Brier: {metrics['brier']:.4f}"
    )
    print(
        f"Predictions: mean={metrics['pred_mean']:.4f}, "
        f"std={metrics['pred_std']:.4f}, "
        f"range=[{metrics['pred_min']:.4f}, {metrics['pred_max']:.4f}]"
    )

    return metrics, pd_hat


def test_model_responsiveness(model, feature_cols, scaler=None):
    """Test that model responds to different inputs."""
    print("\n=== Testing Model Responsiveness ===")
    
    test_cases = [
        ("Low traits", [0.1] * len(feature_cols)),
        ("Medium traits", [0.5] * len(feature_cols)),
        ("High traits", [0.9] * len(feature_cols)),
        ("Mixed traits", [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 0.2, 0.3, 0.4, 0.5, 0.6]),
    ]
    
    predictions = []
    for name, traits in test_cases:
        # Pad or truncate to match feature count
        traits = traits[:len(feature_cols)]
        if len(traits) < len(feature_cols):
            traits = traits + [0.5] * (len(feature_cols) - len(traits))
        
        X_test = np.array([traits], dtype=np.float32)
        if scaler:
            X_test = scaler.transform(X_test)
        
        pred = model.predict_proba(X_test)[0, 1]
        predictions.append(pred)
        print(f"  {name}: {pred:.6f}")
    
    # Check if predictions vary
    pred_std = np.std(predictions)
    if pred_std < 0.001:
        print(f"\n  ⚠️  WARNING: Model predictions have very low variance (std={pred_std:.6f})")
        print("     Model may not be learning properly!")
        return False
    else:
        print(f"\n  ✓ Model predictions vary (std={pred_std:.6f})")
        return True


# ----------------------------
# 1) Load data
# ----------------------------
print("Loading data...")
df = pd.read_csv(DATA_PATH)

# Target label
y = df["defaulted"].astype(int)

# Features: DROP score_0_100 and defaulted (and also drop pd & user_id)
drop_cols = ["user_id", "pd", "score_0_100", "defaulted"]

# ----------------------------
# 2) Train/Valid/Test split (70/15/15) stratified
# ----------------------------
print("\nSplitting data...")
train_df, temp_df = train_test_split(
    df, test_size=0.30, random_state=42, stratify=df["defaulted"]
)
valid_df, test_df = train_test_split(
    temp_df, test_size=0.50, random_state=42, stratify=temp_df["defaulted"]
)

# Build X/y from each split
X_train = train_df.drop(columns=drop_cols)
y_train = train_df["defaulted"].astype(int)

X_valid = valid_df.drop(columns=drop_cols)
y_valid = valid_df["defaulted"].astype(int)

X_test  = test_df.drop(columns=drop_cols)
y_test  = test_df["defaulted"].astype(int)

feature_cols = list(X_train.columns)

print("\nData validation:")
print(f"  Train: {len(X_train)} samples, {y_train.mean():.4f} positive rate")
print(f"  Valid: {len(X_valid)} samples, {y_valid.mean():.4f} positive rate")
print(f"  Test:  {len(X_test)} samples, {y_test.mean():.4f} positive rate")
print(f"  Features: {len(feature_cols)}")

# Check feature ranges
print(f"\nFeature ranges (before normalization):")
for col in feature_cols[:5]:
    print(f"  {col}: [{X_train[col].min():.2f}, {X_train[col].max():.2f}]")

# ----------------------------
# 2.5) NORMALIZE FEATURES TO [0,1] RANGE
# ----------------------------
print("\nNormalizing features to [0,1] range...")
scaler = MinMaxScaler(feature_range=(0, 1))

X_train_scaled = pd.DataFrame(
    scaler.fit_transform(X_train),
    columns=feature_cols,
    index=X_train.index
)
X_valid_scaled = pd.DataFrame(
    scaler.transform(X_valid),
    columns=feature_cols,
    index=X_valid.index
)
X_test_scaled = pd.DataFrame(
    scaler.transform(X_test),
    columns=feature_cols,
    index=X_test.index
)

print(f"\nFeature ranges (after normalization):")
for col in feature_cols[:5]:
    print(f"  {col}: [{X_train_scaled[col].min():.2f}, {X_train_scaled[col].max():.2f}]")

# class imbalance weight
pos = int((y_train == 1).sum())
neg = int((y_train == 0).sum())
scale_pos_weight = neg / max(pos, 1)

print(f"\nClass imbalance:")
print(f"  Positive: {pos}, Negative: {neg}")
print(f"  scale_pos_weight: {scale_pos_weight:.3f}")

# ----------------------------
# 3) Train XGBoost (early stopping on VALID)
# ----------------------------
print("\n" + "="*70)
print("Training XGBoost model...")
print("="*70)

model = XGBClassifier(
    n_estimators=2000,
    learning_rate=0.01,  # Lower learning rate for more stable training
    max_depth=4,
    min_child_weight=3,
    subsample=0.9,
    colsample_bytree=0.9,
    reg_lambda=1.0,
    objective="binary:logistic",
    eval_metric="aucpr",
    scale_pos_weight=scale_pos_weight,
    tree_method="hist",
    random_state=42,
)

fit_kwargs = dict(
    eval_set=[(X_valid_scaled, y_valid)],
    verbose=100,  # More frequent updates
)

# Handle XGBoost version differences:
try:
    model.fit(X_train_scaled, y_train, **fit_kwargs, early_stopping_rounds=100)
except TypeError:
    try:
        from xgboost.callback import EarlyStopping
        model.fit(
            X_train_scaled,
            y_train,
            **fit_kwargs,
            callbacks=[EarlyStopping(rounds=100, save_best=True)],
        )
    except Exception:
        print(
            "Warning: early stopping is not supported in this XGBoost version/build. "
            "Training without early stopping."
        )
        model.fit(X_train_scaled, y_train, **fit_kwargs)

# ----------------------------
# 4) Test model responsiveness BEFORE evaluation
# ----------------------------
print("\n" + "="*70)
test_model_responsiveness(model, feature_cols, scaler)

# ----------------------------
# 5) Evaluate and save
# ----------------------------
run_dir = make_run_dir(os.path.join("models", "runs"))
print(f"\nSaving outputs to: {run_dir}")

all_metrics = []

# VALID
m_valid, pd_valid = evaluate_prob_only(model, X_valid_scaled, y_valid, split_name="valid")
all_metrics.append(m_valid)

valid_pred_df = pd.DataFrame({
    "user_id": valid_df["user_id"].values,
    "pd_hat": pd_valid,
    "y_true": y_valid.values,
})
valid_pred_df.to_csv(os.path.join(run_dir, "pd_predictions_valid.csv"), index=False)

# TEST
m_test, pd_test = evaluate_prob_only(model, X_test_scaled, y_test, split_name="test")
all_metrics.append(m_test)

test_pred_df = pd.DataFrame({
    "user_id": test_df["user_id"].values,
    "pd_hat": pd_test,
    "y_true": y_test.values,
})
test_pred_df.to_csv(os.path.join(run_dir, "pd_predictions_test.csv"), index=False)

# Save metrics
pd.DataFrame(all_metrics).to_csv(os.path.join(run_dir, "metrics.csv"), index=False)
save_json(all_metrics, os.path.join(run_dir, "metrics.json"))

# Feature importance
fi = pd.Series(model.feature_importances_, index=feature_cols).sort_values(ascending=False)
fi.to_csv(os.path.join(run_dir, "feature_importance.csv"), header=["importance"])

# Save model bundle WITH scaler
joblib.dump(
    {
        "model": model,
        "feature_columns": feature_cols,
        "scaler": scaler,  # IMPORTANT: Save scaler for inference
    },
    os.path.join(run_dir, "xgb_model.joblib")
)

print("\n" + "="*70)
print("Saved outputs:")
print(f"- {os.path.join(run_dir, 'metrics.csv')}")
print(f"- {os.path.join(run_dir, 'metrics.json')}")
print(f"- {os.path.join(run_dir, 'pd_predictions_valid.csv')}")
print(f"- {os.path.join(run_dir, 'pd_predictions_test.csv')}")
print(f"- {os.path.join(run_dir, 'feature_importance.csv')}")
print(f"- {os.path.join(run_dir, 'xgb_model.joblib')}")
print("="*70)

