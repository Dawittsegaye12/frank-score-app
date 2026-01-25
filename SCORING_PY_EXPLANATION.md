# Scoring.py Structure and Function Guide

## Overview

`scoring.py` implements the **three-body model** for computing psychometric traits and probability of default (PD):
1. **Content-based traits** from question answers
2. **Behavior-based traits** from 30 metadata features
3. **Combined traits**: 60% behavior + 40% content
4. **PD prediction** using XGBoost model

---

## File Structure (by Section)

```
scoring.py
├── Utility Functions
├── METADATA COMPUTATION (30 Features)
├── TRAIT NAMES
├── CONTENT-BASED SCORING
├── BEHAVIOR-BASED SCORING
├── COMBINED SCORING
├── XGBoost MODEL
└── FINANCIAL PD
```

---

## 1. Utility Functions

### `sigmoid(x: float) -> float`
**Purpose**: Computes stable sigmoid function for probability conversion
- Used to convert raw scores to probabilities (0-1 range)
- Handles both positive and negative inputs to avoid overflow
- Used in financial PD calculation

### `_safe_float(x: Any, default: float = 0.0) -> float`
**Purpose**: Safely converts any value to float with fallback
- Prevents crashes from invalid data types
- Returns default value if conversion fails
- Used throughout for metadata normalization

### `_safe_int(x: Any, default: int = 0) -> int`
**Purpose**: Safely converts any value to integer with fallback
- Similar to `_safe_float` but for integers
- Used for count-based metadata fields

### `_clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float`
**Purpose**: Clamps values to a specified range [lo, hi]
- Ensures all trait scores stay within [0, 1] range
- Prevents invalid values from propagating

---

## 2. METADATA COMPUTATION (30 Features)

### `compute_metadata(events: List[Dict]) -> Dict[str, Any]`
**Purpose**: Main entry point for metadata aggregation
- **Input**: List of telemetry events from database
- **Output**: Dictionary with 30 normalized metadata features
- **Logic**:
  1. Parses events and looks for `metadata_summary` event (from client)
  2. If found: uses client-computed metadata (preferred)
  3. If not found: falls back to server-side computation
- **Returns**: Normalized metadata dictionary with all 30 fields

### `_normalize_metadata(md: Dict) -> Dict[str, Any]`
**Purpose**: Ensures all 30 metadata fields are present with correct types
- **Input**: Raw metadata dictionary (may be incomplete)
- **Output**: Complete dictionary with all 30 fields
- **Fields grouped by category**:
  - Session & Completion (6): completion_status, completion_time_sec, sessions_count, etc.
  - Response Timing (7): avg_response_time_sec, median_response_time_sec, idle_time_ratio, etc.
  - Click & Hesitation (4): rapid_click_events, hesitation_time_avg, etc.
  - Answer Behavior (5): skip_rate, answer_change_rate, extreme_option_rate, etc.
  - Scroll & Navigation (5): scroll_depth_avg, back_nav_count, etc.
  - Reading & Compliance (3): terms_screen_time, terms_scroll_depth, etc.

### `_compute_metadata_from_events(parsed: List[Dict]) -> Dict[str, Any]`
**Purpose**: Fallback server-side metadata computation from raw events
- **When used**: When client doesn't send `metadata_summary` event
- **Computes**:
  - Completion time from `assessment_start` and `assessment_end`
  - Response times from `question_view` and `answer_submit` events
  - Answer change rate from `answer_change` events
  - Idle ratio from `idle_start` and `idle_end` events
  - Scroll depth from `scroll_summary` events
  - Back navigation from `page_nav` events
  - Rapid clicks from `answer_select` events
- **Returns**: Subset of 30 metadata fields (some may be None/0)

---

## 3. TRAIT NAMES

### `DEFAULT_TRAIT_NAMES` (constant)
**Purpose**: List of 15 trait names in order
- Defines the 15 psychometric traits used in the system
- Order matters (trait_id 1 = first trait, etc.)

### `get_trait_names() -> List[str]`
**Purpose**: Returns the default trait names list
- Simple getter function for consistency

---

## 4. CONTENT-BASED SCORING

### `compute_content_traits(answers_by_item, score_map, trait_names) -> Dict[str, float]`
**Purpose**: Computes trait scores from explicit question answers
- **Input**:
  - `answers_by_item`: Dict mapping item_id → selected_option (A/B/C/D)
  - `score_map`: Dict mapping item_id → {option: score_0_to_3}
  - `trait_names`: List of 15 trait names
- **Process**:
  1. Groups answers by trait_id (extracted from item_id like "1.1" → trait_id=1)
  2. Maps selected_option to score (0-3) using score_map
  3. Averages scores per trait
  4. Normalizes to [0,1] by dividing by 3.0
- **Formula**: `trait_content = mean(item_scores) / 3.0`
- **Output**: Dict mapping trait_name → score (0-1)
- **Raises**: ValueError if no answers for a trait

---

## 5. BEHAVIOR-BASED SCORING

### `compute_behaviour_traits(metadata, trait_names) -> Dict[str, float]`
**Purpose**: Computes trait scores from 30 metadata features (user behavior)
- **Input**: Normalized metadata dictionary (30 fields)
- **Process**:
  1. **Transforms metadata to "good" versions** (higher = better for credit):
     - `completion_good = completion_status`
     - `sessions_good = 1 - normalize(sessions_count)`
     - `idle_good = 1 - idle_time_ratio`
     - `response_good`: Moderate response times (5-15s) are best
     - `rapid_good = 1 - rapid_click_rate`
     - `change_good = 1 - answer_change_rate`
     - `hesitation_good`: Some hesitation is good, too much is bad
     - `scroll_good = scroll_depth_avg`
     - `nav_good = 1 - normalize(back_nav_count)`
     - `terms_good`: Based on terms screen time and scroll
     - `inconsistency_good = 1 - inconsistency_score`
     - `extreme_good = 1 - extreme_option_rate`
     - `compliance_good = 1 - normalize(compliance_flags)`
  
  2. **Maps transformed features to each trait**:
     - Each trait uses a weighted combination of "good" features
     - Example: `conscientiousness = (completion + sessions + skip + idle + response) / 5`
     - Example: `impulsivity = (rapid_good + change_good + hesitation_good) / 3`
- **Output**: Dict mapping trait_name → behavior_score (0-1)
- **Raises**: ValueError if trait not recognized

---

## 6. COMBINED SCORING

### `compute_combined_traits(content_traits, behaviour_traits, trait_names, alpha=0.6) -> Dict[str, float]`
**Purpose**: Combines content and behavior traits using weighted average
- **Input**:
  - `content_traits`: Dict from `compute_content_traits`
  - `behaviour_traits`: Dict from `compute_behaviour_traits`
  - `trait_names`: List of 15 trait names
  - `alpha`: Weight for behavior (default 0.6)
- **Formula**: `Trait_final = α × Trait_behaviour + (1 - α) × Trait_content`
  - Default: 60% behavior + 40% content
- **Output**: Dict mapping trait_name → final_score (0-1)
- **Raises**: ValueError if trait missing from either input

### `compute_traits(answers_by_item, metadata, score_map, trait_names) -> Dict[str, float]`
**Purpose**: **Main entry point** - orchestrates the three-body model
- **Input**: All raw inputs (answers, metadata, score_map, trait_names)
- **Process**:
  1. Calls `compute_content_traits` → content scores
  2. Calls `compute_behaviour_traits` → behavior scores
  3. Calls `compute_combined_traits` → final combined scores
- **Output**: Dict mapping trait_name → final_combined_score (0-1)
- **This is the function called by `app.py`**

---

## 7. XGBoost MODEL

### `load_xgb_model() -> None`
**Purpose**: Loads XGBoost model at application startup
- **Called by**: `app.py` on startup
- **Process**:
  1. Loads model from `models/xgb_model.joblib`
  2. Extracts model and feature_columns
  3. Stores in global variables `_XGB_MODEL` and `_XGB_FEATURE_COLUMNS`
- **Handles**: Missing model, dict format, direct format

### `_normalize_trait_name(name: str) -> str`
**Purpose**: Normalizes trait names for fuzzy matching
- Converts to lowercase, replaces spaces/slashes/dashes with underscores
- Example: "Integrity / Rule Following" → "integrity_rule_following"
- Used for matching trait names to model feature columns

### `_map_trait_to_feature_column(trait_name, feature_columns) -> Optional[str]`
**Purpose**: Maps trait name to model feature column name
- **Process**:
  1. Checks explicit mappings (e.g., "impulsivity" → "impulsivity_control")
  2. Tries direct match (normalized)
  3. Tries partial match (substring)
- **Returns**: Feature column name or None if not found
- **Used by**: `psychometric_pd` to align traits with model features

### `psychometric_pd(traits, trait_names) -> float`
**Purpose**: Predicts psychometric PD using trained XGBoost model
- **Input**:
  - `traits`: Dict of final combined traits (from `compute_traits`)
  - `trait_names`: List of trait names
- **Process**:
  1. Maps traits to model feature columns (using `_map_trait_to_feature_column`)
  2. Creates feature vector in correct order
  3. Calls `model.predict_proba()` to get probability
  4. Extracts probability of default (class 1)
- **Output**: PD probability (0-1) or None if model unavailable/fails
- **Returns**: Clamped value between 0 and 1

---

## 8. FINANCIAL PD

### `financial_pd(monthly_income, monthly_expenses, total_debt, missed_payments_3m) -> float`
**Purpose**: Calculates financial PD using deterministic formula
- **Input**: Financial data (income, expenses, debt, missed payments)
- **Process**:
  1. Computes DTI (debt-to-income ratio)
  2. Computes savings_norm (normalized savings)
  3. Applies logistic regression formula:
     ```
     z = a0 + a1×DTI + a2×missed_payments - a3×savings_norm
     PD = sigmoid(z)
     ```
- **Output**: Financial PD probability (0-1)

### `combine_pd(pd_psych_hat, pd_fin_hat) -> Optional[float]`
**Purpose**: Combines psychometric and financial PD scores
- **Input**: Two PD values (may be None)
- **Formula**: `PD_final = 0.6 × PD_financial + 0.4 × PD_psychometric`
- **Handles**: Missing values (if one is None, returns the other)
- **Output**: Combined PD (0-1) or None if both are None

---

## Data Flow Summary

```
1. User completes assessment
   ↓
2. Events stored in database
   ↓
3. app.py calls compute_metadata(events)
   → Returns 30 metadata features
   ↓
4. app.py calls compute_traits(answers, metadata, score_map, trait_names)
   → compute_content_traits() → content scores
   → compute_behaviour_traits() → behavior scores
   → compute_combined_traits() → final scores (60% behavior + 40% content)
   ↓
5. app.py calls psychometric_pd(traits, trait_names)
   → Maps traits to model features
   → XGBoost predicts PD
   ↓
6. app.py calls financial_pd(...) [optional]
   → Deterministic formula
   ↓
7. app.py calls combine_pd(pd_psych, pd_fin)
   → Final PD = 60% financial + 40% psychometric
```

---

## Key Design Principles

1. **Three-body model**: Content + Behavior → Combined
2. **Normalization**: All scores in [0, 1] range
3. **Fallback mechanisms**: Server-side computation if client fails
4. **Type safety**: Safe conversion functions prevent crashes
5. **Modularity**: Each function has single responsibility
6. **Error handling**: Raises ValueError for missing data (no silent failures)





