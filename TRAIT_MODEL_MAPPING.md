# Trait to Model Feature Mapping

## Overview
This document shows how the 15 calculated traits from the assessment are mapped to the 15 feature columns expected by the XGBoost model.

## Complete Mapping Table

| # | Calculated Trait Name | Model Feature Column | Mapping Method |
|---|----------------------|---------------------|-----------------|
| 1 | `conscientiousness` | `conscientiousness` | Direct match |
| 2 | `impulsivity` | `impulsivity_control` | Explicit mapping |
| 3 | `financial_self_confidence` | `financial_self_confidence` | Direct match |
| 4 | `planning_horizon` | `planning_horizon` | Direct match |
| 5 | `self_control` | `self_control` | Direct match |
| 6 | `locus_of_control` | `locus_of_control` | Direct match |
| 7 | `honesty` | `honesty` | Direct match |
| 8 | `integrity_rule_following` | `integrity_rule_following` | Direct match |
| 9 | `obligation_to_repay` | `obligation_to_repay` | Direct match |
| 10 | `grit_perseverance` | `grit_perseverance` | Direct match |
| 11 | `present_bias_time_preference` | `present_bias_control` | Explicit mapping |
| 12 | `risk_attitude` | `risk_management` | Explicit mapping |
| 13 | `financial_decision_quality` | `financial_decision_quality` | Direct match |
| 14 | `spending_vs_saving` or `spending_vs_saving_orientation` | `saving_orientation` | Explicit mapping |
| 15 | `commitment_follow_through` | `follow_through` | Explicit mapping |

## Model Expected Features (in order)

```
1.  conscientiousness
2.  impulsivity_control          ← mapped from "impulsivity"
3.  financial_self_confidence
4.  planning_horizon
5.  self_control
6.  locus_of_control
7.  honesty
8.  integrity_rule_following
9.  obligation_to_repay
10. grit_perseverance
11. present_bias_control          ← mapped from "present_bias_time_preference"
12. risk_management               ← mapped from "risk_attitude"
13. financial_decision_quality
14. saving_orientation            ← mapped from "spending_vs_saving" or "spending_vs_saving_orientation"
15. follow_through                ← mapped from "commitment_follow_through"
```

## Explicit Mappings (in code)

The following explicit mappings are defined in `_map_trait_to_feature_column()`:

```python
explicit_map = {
    "impulsivity": "impulsivity_control",
    "present_bias_time_preference": "present_bias_control",
    "risk_attitude": "risk_management",
    "spending_vs_saving_orientation": "saving_orientation",
    "spending_vs_saving": "saving_orientation",
    "commitment_follow_through": "follow_through",
}
```

## Mapping Process

1. **Normalize trait name**: Convert to lowercase, replace spaces/slashes/hyphens with underscores
2. **Check explicit map**: If trait name is in explicit_map and target exists in feature_columns, use it
3. **Direct match**: Try normalized exact match
4. **Partial match**: Try substring matching
5. **Error if no match**: Raises ValueError (no default 0.5 anymore)

## Verification

To verify all mappings work correctly:

```python
import scoring
scoring.load_xgb_model()

calculated_traits = [
    "conscientiousness",
    "impulsivity",  # ← maps to impulsivity_control
    "financial_self_confidence",
    "planning_horizon",
    "self_control",
    "locus_of_control",
    "honesty",
    "integrity_rule_following",
    "obligation_to_repay",
    "grit_perseverance",
    "present_bias_time_preference",  # ← maps to present_bias_control
    "risk_attitude",  # ← maps to risk_management
    "financial_decision_quality",
    "spending_vs_saving_orientation",  # ← maps to saving_orientation
    "commitment_follow_through",  # ← maps to follow_through
]

# All should map successfully to model features
```

## Notes

- **10 traits** match directly (no mapping needed)
- **5 traits** require explicit mapping due to naming differences
- All 15 traits must be successfully mapped or an error is raised
- The feature vector sent to the model is in the exact order of `_XGB_FEATURE_COLUMNS`

