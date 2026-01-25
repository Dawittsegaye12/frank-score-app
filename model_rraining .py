DATA_PATH = r"synthetic_traits_12k_userid_FS.csv"

import os, json
from datetime import datetime

import numpy as np
import pandas as pd

from sklearn.model_selection import train_test_split
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
    }

    print(f"\n=== {split_name} (probability-only) ===")
    print(
        f"ROC-AUC: {metrics['roc_auc']:.4f} | "
        f"PR-AUC: {metrics['pr_auc']:.4f} | "
        f"Brier: {metrics['brier']:.4f}"
    )

    return metrics, pd_hat


# ----------------------------
# 1) Load data
# ----------------------------
df = pd.read_csv(DATA_PATH)

# Target label (still needed for training + evaluation)
y = df["defaulted"].astype(int)

# Features: DROP score_0_100 and defaulted (and also drop pd & user_id)
drop_cols = ["user_id", "pd", "score_0_100", "defaulted"]

# ----------------------------
# 2) Train/Valid/Test split (70/15/15) stratified
# ----------------------------
train_df, temp_df = train_test_split(
    df, test_size=0.30, random_state=42, stratify=df["defaulted"]
)
valid_df, test_df = train_test_split(
    temp_df, test_size=0.50, random_state=42, stratify=temp_df["defaulted"]
)

# Build X/y from each split (dropping the same columns from FEATURES)
X_train = train_df.drop(columns=drop_cols)
y_train = train_df["defaulted"].astype(int)

X_valid = valid_df.drop(columns=drop_cols)
y_valid = valid_df["defaulted"].astype(int)

X_test  = test_df.drop(columns=drop_cols)
y_test  = test_df["defaulted"].astype(int)

feature_cols = list(X_train.columns)

# class imbalance weight
pos = int((y_train == 1).sum())
neg = int((y_train == 0).sum())
scale_pos_weight = neg / max(pos, 1)

print("Split sizes:", len(X_train), len(X_valid), len(X_test))
print(f"Train positive rate: {pos/len(y_train):.4f} | scale_pos_weight: {scale_pos_weight:.3f}")
print(f"Using {len(feature_cols)} features:", feature_cols)

# ----------------------------
# 3) Train XGBoost (early stopping on VALID)
# ----------------------------
model = XGBClassifier(
    n_estimators=2000,
    learning_rate=0.03,
    max_depth=4,
    min_child_weight=3,
    subsample=0.9,
    colsample_bytree=0.9,
    reg_lambda=1.0,
    objective="binary:logistic",   # outputs probability via predict_proba
    eval_metric="aucpr",
    scale_pos_weight=scale_pos_weight,
    tree_method="hist",
    random_state=42,
)

fit_kwargs = dict(
    eval_set=[(X_valid, y_valid)],
    verbose=200,
)

# Handle XGBoost version differences:
try:
    model.fit(X_train, y_train, **fit_kwargs, early_stopping_rounds=100)
except TypeError:
    try:
        from xgboost.callback import EarlyStopping
        model.fit(
            X_train,
            y_train,
            **fit_kwargs,
            callbacks=[EarlyStopping(rounds=100, save_best=True)],
        )
    except Exception:
        print(
            "Warning: early stopping is not supported in this XGBoost version/build. "
            "Training without early stopping."
        )
        model.fit(X_train, y_train, **fit_kwargs)

# ----------------------------
# 4) Log probability-only metrics + save PD outputs
# ----------------------------
run_dir = make_run_dir(os.path.join("models", "runs"))
print(f"\nLogging to: {run_dir}")

all_metrics = []

# VALID
m_valid, pd_valid = evaluate_prob_only(model, X_valid, y_valid, split_name="valid")
all_metrics.append(m_valid)

valid_pred_df = pd.DataFrame({
    "user_id": valid_df["user_id"].values,
    "pd_hat": pd_valid,
    "y_true": y_valid.values,   # keep for analysis (remove if you don't want)
})
valid_pred_df.to_csv(os.path.join(run_dir, "pd_predictions_valid.csv"), index=False)

# TEST
m_test, pd_test = evaluate_prob_only(model, X_test, y_test, split_name="test")
all_metrics.append(m_test)

test_pred_df = pd.DataFrame({
    "user_id": test_df["user_id"].values,
    "pd_hat": pd_test,
    "y_true": y_test.values,    # keep for analysis (remove if you don't want)
})
test_pred_df.to_csv(os.path.join(run_dir, "pd_predictions_test.csv"), index=False)

# Save metrics
pd.DataFrame(all_metrics).to_csv(os.path.join(run_dir, "metrics.csv"), index=False)
save_json(all_metrics, os.path.join(run_dir, "metrics.json"))

# Feature importance
fi = pd.Series(model.feature_importances_, index=feature_cols).sort_values(ascending=False)
fi.to_csv(os.path.join(run_dir, "feature_importance.csv"), header=["importance"])

# Save model bundle (NO threshold; model outputs probabilities)
joblib.dump(
    {"model": model, "feature_columns": feature_cols},
    os.path.join(run_dir, "xgb_model.joblib")
)

print("\nSaved outputs:")
print(f"- {os.path.join(run_dir, 'metrics.csv')}")
print(f"- {os.path.join(run_dir, 'metrics.json')}")
print(f"- {os.path.join(run_dir, 'pd_predictions_valid.csv')}")
print(f"- {os.path.join(run_dir, 'pd_predictions_test.csv')}")
print(f"- {os.path.join(run_dir, 'feature_importance.csv')}")
print(f"- {os.path.join(run_dir, 'xgb_model.joblib')}")
print(f"\nAll saved in: {run_dir}")
