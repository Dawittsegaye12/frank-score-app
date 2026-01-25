"""
FrankScore Scoring Engine
Implements the three-body model from the PDF guidelines:
- Content-based trait scores from question answers
- Behavior-based trait scores from 15 metadata features
- Combined formula: Trait_final = 0.6 × Trait_behaviour + 0.4 × Trait_content
"""

import json
import math
import os
import time
from typing import Any, Dict, List, Optional


def sigmoid(x: float) -> float:
    """Stable sigmoid for demo ranges."""
    if x >= 0:
        z = math.exp(-x)
        return 1.0 / (1.0 + z)
    z = math.exp(x)
    return z / (1.0 + z)


def _safe_float(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return default


def _safe_int(x: Any, default: int = 0) -> int:
    try:
        return int(x)
    except Exception:
        return default


def _clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    """Clamp value to [lo, hi] range."""
    return max(lo, min(hi, x))


# ============================================================================
# METADATA COMPUTATION (15 Features)
# ============================================================================

def compute_metadata(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregates 15 metadata features from stored events.
    The client-side MetadataTracker computes most of these and sends them
    in a 'metadata_summary' event. This function also computes server-side
    aggregations as fallback.
    """
    # #region agent log
    import json as json_module
    log_data = {"location": "scoring.py:47", "message": "compute_metadata entry", "data": {"eventsCount": len(events), "eventNames": [e.get("event_name") for e in events[:5]]}, "timestamp": int(time.time() * 1000), "sessionId": "debug-session", "runId": "run1", "hypothesisId": "F"}
    try:
        with open(r"c:\Users\dawit\frank-score-app\.cursor\debug.log", "a", encoding="utf-8") as f:
            f.write(json_module.dumps(log_data) + "\n")
    except: pass
    # #endregion
    parsed = []
    metadata_summary = {}
    
    for e in events:
        payload = {}
        try:
            payload = json.loads(e.get("payload_json") or "{}")
        except Exception:
            payload = {}
        
        event_name = e.get("event_name")
        
        # Look for metadata_summary event from client
        if event_name == "metadata_summary":
            metadata_summary = payload
            # #region agent log
            log_data = {"location": "scoring.py:76", "message": "metadata_summary found", "data": {"payloadKeys": len(payload), "completion_status": payload.get("completion_status"), "abandonment_flag": payload.get("abandonment_flag"), "client_ts_ms": _safe_int(e.get("client_ts_ms"), 0)}, "timestamp": int(time.time() * 1000), "sessionId": "debug-session", "runId": "run1", "hypothesisId": "F"}
            try:
                with open(r"c:\Users\dawit\frank-score-app\.cursor\debug.log", "a", encoding="utf-8") as f:
                    f.write(json_module.dumps(log_data) + "\n")
            except: pass
            # #endregion
        
        parsed.append({
            "event_name": event_name,
            "client_ts_ms": _safe_int(e.get("client_ts_ms"), 0),
            "item_id": e.get("item_id"),
            "payload": payload,
        })

    # If client sent metadata_summary, use it as base
    if metadata_summary:
        # #region agent log
        log_data = {"location": "scoring.py:78", "message": "using metadata_summary", "data": {"metadataKeys": len(metadata_summary)}, "timestamp": int(time.time() * 1000), "sessionId": "debug-session", "runId": "run1", "hypothesisId": "F"}
        try:
            with open(r"c:\Users\dawit\frank-score-app\.cursor\debug.log", "a", encoding="utf-8") as f:
                f.write(json_module.dumps(log_data) + "\n")
        except: pass
        # #endregion
        return _normalize_metadata(metadata_summary)
    
    # Otherwise compute server-side (fallback)
    # #region agent log
    log_data = {"location": "scoring.py:82", "message": "using fallback server-side computation", "data": {}, "timestamp": int(time.time() * 1000), "sessionId": "debug-session", "runId": "run1", "hypothesisId": "F"}
    try:
        with open(r"c:\Users\dawit\frank-score-app\.cursor\debug.log", "a", encoding="utf-8") as f:
            f.write(json_module.dumps(log_data) + "\n")
    except: pass
    # #endregion
    return _compute_metadata_from_events(parsed)


def _normalize_metadata(md: Dict[str, Any]) -> Dict[str, Any]:
    """Ensure all 15 metadata fields are present with proper types."""
    return {
        # Session & Completion (2) - Removed: sessions_count, partial_attempts_count, return_after_disconnection, abandonment_flag
        "completion_status": _safe_float(md.get("completion_status"), 0),
        "completion_time_sec": _safe_float(md.get("completion_time_sec")),
        
        # Response Timing (6) - Removed: idle_time_total_sec, idle_time_ratio
        "avg_response_time_sec": _safe_float(md.get("avg_response_time_sec")),
        "response_time_std_sec": _safe_float(md.get("response_time_std_sec")),
        "median_response_time_sec": _safe_float(md.get("median_response_time_sec")),
        "min_response_time_sec": _safe_float(md.get("min_response_time_sec")),
        "max_response_time_sec": _safe_float(md.get("max_response_time_sec")),
        
        # Click & Hesitation (2) - Removed: rapid_click_events, rapid_click_rate
        "hesitation_time_avg": _safe_float(md.get("hesitation_time_avg")),
        "hesitation_time_financial_items": _safe_float(md.get("hesitation_time_financial_items")),
        
        # Answer Behavior (1) - Removed: skip_rate, answer_change_rate, answer_change_rate_financial_items, inconsistency_score
        "extreme_option_rate": _safe_float(md.get("extreme_option_rate"), 0),
        
        # Scroll & Navigation (4) - Removed: back_nav_count
        "scroll_events_count": _safe_int(md.get("scroll_events_count"), 0),
        "scroll_depth_avg": _safe_float(md.get("scroll_depth_avg"), 0),
        "scroll_depth_max": _safe_float(md.get("scroll_depth_max"), 0),
        "scroll_zigzag_score": _safe_float(md.get("scroll_zigzag_score"), 0),
        
        # Reading & Compliance (1) - Removed: terms_scroll_depth, instruction_compliance_flags
        "terms_screen_time": _safe_float(md.get("terms_screen_time"), 0),
    }


def _compute_metadata_from_events(parsed: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Fallback: compute metadata from raw events (server-side)."""
    
    def ts_first(name: str) -> Optional[int]:
        t = [p["client_ts_ms"] for p in parsed if p["event_name"] == name and p["client_ts_ms"] > 0]
        return min(t) if t else None

    def ts_last(name: str) -> Optional[int]:
        t = [p["client_ts_ms"] for p in parsed if p["event_name"] == name and p["client_ts_ms"] > 0]
        return max(t) if t else None

    start = ts_first("assessment_start")
    end = ts_last("assessment_end")
    completion_time = None
    if start and end and end >= start:
        completion_time = (end - start) / 1000.0

    # Response times
    q_view = {}
    rt_list = []
    for p in parsed:
        if p["event_name"] == "question_view" and p["item_id"]:
            q_view[p["item_id"]] = p["client_ts_ms"]
        if p["event_name"] == "answer_submit" and p["item_id"]:
            t0 = q_view.get(p["item_id"])
            if t0 and p["client_ts_ms"] >= t0:
                rt_list.append((p["client_ts_ms"] - t0) / 1000.0)
    
    avg_rt = sum(rt_list) / len(rt_list) if rt_list else None
    sorted_rt = sorted(rt_list)
    median_rt = sorted_rt[len(sorted_rt) // 2] if sorted_rt else None
    min_rt = sorted_rt[0] if sorted_rt else None
    max_rt = sorted_rt[-1] if sorted_rt else None
    
    # Answer changes
    change_ct = sum(1 for p in parsed if p["event_name"] == "answer_change")
    items_answered = {p["item_id"] for p in parsed if p["event_name"] == "answer_submit" and p["item_id"]}
    answer_change_rate = (change_ct / max(len(items_answered), 1)) if items_answered else 0

    # Idle ratio
    idle_total_ms = 0
    idle_start_ms = None
    for p in parsed:
        if p["event_name"] == "idle_start":
            idle_start_ms = p["client_ts_ms"]
        elif p["event_name"] == "idle_end":
            if idle_start_ms and p["client_ts_ms"] >= idle_start_ms:
                idle_total_ms += p["client_ts_ms"] - idle_start_ms
            idle_start_ms = None
    idle_ratio = (idle_total_ms / 1000.0) / completion_time if completion_time and completion_time > 0 else 0

    # Scroll
    depths = []
    for p in parsed:
        if p["event_name"] == "scroll_summary":
            depths.append(_safe_float((p["payload"] or {}).get("max_depth"), 0.0))
    scroll_depth_max = max(depths) if depths else 0

    # Back nav
    back_nav = sum(1 for p in parsed if p["event_name"] == "page_nav" and (p["payload"] or {}).get("direction") == "back")

    # Rapid clicks
    click_ts = [p["client_ts_ms"] for p in parsed if p["event_name"] == "answer_select" and p["client_ts_ms"] > 0]
    click_ts.sort()
    rapid_ct = sum(1 for i in range(1, len(click_ts)) if (click_ts[i] - click_ts[i - 1]) < 250)
    rapid_rate = (rapid_ct / (len(click_ts) - 1)) if len(click_ts) > 1 else 0

    return {
        # Session & Completion (2)
        "completion_status": 1 if end else 0,
        "completion_time_sec": completion_time,
        
        # Response Timing (6)
        "avg_response_time_sec": avg_rt,
        "response_time_std_sec": None,
        "median_response_time_sec": median_rt,
        "min_response_time_sec": min_rt,
        "max_response_time_sec": max_rt,
        
        # Click & Hesitation (2)
        "hesitation_time_avg": None,
        "hesitation_time_financial_items": None,
        
        # Answer Behavior (1)
        "extreme_option_rate": 0,
        
        # Scroll & Navigation (4)
        "scroll_events_count": len(depths),
        "scroll_depth_avg": sum(depths) / len(depths) if depths else 0,
        "scroll_depth_max": scroll_depth_max,
        "scroll_zigzag_score": 0,
        
        # Reading & Compliance (1)
        "terms_screen_time": 0,
    }


# ============================================================================
# TRAIT NAMES
# ============================================================================

DEFAULT_TRAIT_NAMES = [
    "conscientiousness",
    "impulsivity",
    "financial_self_confidence",
    "planning_horizon",
    "self_control",
    "locus_of_control",
    "honesty",
    "integrity_rule_following",
    "obligation_to_repay",
    "grit_perseverance",
    "present_bias_time_preference",
    "risk_attitude",
    "financial_decision_quality",
    "spending_vs_saving",
    "commitment_follow_through",
]


def get_trait_names() -> List[str]:
    """Return default trait names matching the PDF specification."""
    return DEFAULT_TRAIT_NAMES


# ============================================================================
# CONTENT-BASED SCORING (from question answers)
# ============================================================================

def compute_content_traits(
    answers_by_item: Dict[str, str],
    score_map: Dict[str, Dict[str, int]],
    trait_names: List[str],
) -> Dict[str, float]:
    """
    Compute content-based trait scores from question answers.
    Formula: trait_content = mean(item_scores) / 3.0  →  normalized to [0,1]
    """
    trait_item_scores: Dict[int, List[int]] = {}
    
    for item_id, selected_option in answers_by_item.items():
        parts = item_id.split(".")
        if len(parts) < 2:
            continue
        try:
            trait_id = int(parts[0])
        except ValueError:
            continue
        
        item_score_map = score_map.get(item_id, {})
        score = item_score_map.get(selected_option)
        if score is None:
            continue
        
        if trait_id not in trait_item_scores:
            trait_item_scores[trait_id] = []
        trait_item_scores[trait_id].append(score)
    
    traits: Dict[str, float] = {}
    for i, trait_name in enumerate(trait_names, start=1):
        item_scores = trait_item_scores.get(i, [])
        if item_scores:
            trait_raw = sum(item_scores) / len(item_scores)
            trait_final = trait_raw / 3.0
        else:
            raise ValueError(f"No answers provided for trait {trait_name} (trait_id={i})")
        traits[trait_name] = _clamp(trait_final)
    
    return traits


# ============================================================================
# BEHAVIOR-BASED SCORING (from metadata)
# ============================================================================

def compute_behaviour_traits(
    metadata: Dict[str, Any],
    trait_names: List[str],
) -> Dict[str, float]:
    """
    Compute behavior-based trait scores from 15 metadata features.
    Each trait uses a subset of transformed features as per PDF methodology.
    
    Transforms:
    - completion_good = completion_status
    - response_good = normalized response time (moderate is best)
    - hesitation_good = normalized hesitation (some is good)
    - scroll_good = scroll depth
    - etc.
    """
    # Transform metadata to "good" versions (higher = better for credit)
    completion_good = _safe_float(metadata.get("completion_status"), 0)
    
    # Response time: normalize to [0,1] where moderate times (~5-15s) are best
    avg_rt = _safe_float(metadata.get("avg_response_time_sec"), 5)
    if avg_rt < 1:
        response_good = 0.3  # Too fast = suspicious
    elif avg_rt > 60:
        response_good = 0.4  # Too slow = disengaged
    else:
        response_good = min(1.0, avg_rt / 10.0)  # Moderate = good
    
    # Response time statistics (use median as additional signal)
    median_rt = _safe_float(metadata.get("median_response_time_sec"), 5)
    if median_rt < 1:
        median_response_good = 0.3
    elif median_rt > 60:
        median_response_good = 0.4
    else:
        median_response_good = min(1.0, median_rt / 10.0)
    
    # Response time consistency (lower std = more consistent = better)
    rt_std = _safe_float(metadata.get("response_time_std_sec"), 0)
    consistency_good = 1.0 - _clamp(rt_std / 10.0)  # Normalize std to [0,1]
    
    # Hesitation: some hesitation is good (thoughtful), too much is bad
    hesitation = _safe_float(metadata.get("hesitation_time_avg"), 2)
    if hesitation <= 10:
        hesitation_good = _clamp(hesitation / 5.0)
    else:
        # Very high hesitation = penalty, use inverse relationship
        hesitation_good = _clamp(1.0 - (hesitation - 10) / 20.0)
    
    # Financial hesitation
    fin_hesitation = _safe_float(metadata.get("hesitation_time_financial_items"), 2)
    if fin_hesitation <= 10:
        fin_hesitation_good = _clamp(fin_hesitation / 5.0)
    else:
        fin_hesitation_good = _clamp(1.0 - (fin_hesitation - 10) / 20.0)
    
    # Scroll engagement
    scroll_good = _clamp(_safe_float(metadata.get("scroll_depth_avg"), 0))
    scroll_max_good = _clamp(_safe_float(metadata.get("scroll_depth_max"), 0))
    scroll_events = _safe_int(metadata.get("scroll_events_count"), 0)
    scroll_engagement_good = _clamp(min(1.0, scroll_events / 100.0))  # Normalize event count
    
    # Scroll zigzag (lower = more focused = better)
    zigzag = _safe_float(metadata.get("scroll_zigzag_score"), 0)
    zigzag_good = 1.0 - _clamp(zigzag)
    
    # Terms reading
    terms_time = _safe_float(metadata.get("terms_screen_time"), 0)
    terms_good = _clamp(min(terms_time, 30) / 30.0)  # Up to 30s is good
    
    # Extreme options (too many extremes = less nuanced)
    extreme_rate = _safe_float(metadata.get("extreme_option_rate"), 0)
    extreme_good = 1.0 - _clamp(extreme_rate / 0.6)
    
    # Now map transformed features to traits per PDF methodology
    traits: Dict[str, float] = {}
    
    for trait_name in trait_names:
        if trait_name == "conscientiousness":
            # Conscientiousness = (completion + response + consistency + scroll) / 4
            score = (completion_good + response_good + consistency_good + scroll_good) / 4.0
        
        elif trait_name == "impulsivity":
            # Lower impulsivity is better → use hesitation and consistency
            score = (hesitation_good + consistency_good + response_good) / 3.0
        
        elif trait_name == "financial_self_confidence":
            # Good hesitation on financial items, engagement, response time
            score = (fin_hesitation_good + response_good + completion_good) / 3.0
        
        elif trait_name == "planning_horizon":
            # Terms reading, scroll engagement, response time
            score = (terms_good + scroll_good + response_good + scroll_engagement_good) / 4.0
        
        elif trait_name == "self_control":
            # Consistency, hesitation, scroll focus (low zigzag)
            score = (consistency_good + hesitation_good + zigzag_good) / 3.0
        
        elif trait_name == "locus_of_control":
            # Completion, response consistency, scroll engagement
            score = (completion_good + consistency_good + scroll_engagement_good) / 3.0
        
        elif trait_name == "honesty":
            # Extreme options, consistency, scroll focus
            score = (extreme_good + consistency_good + zigzag_good) / 3.0
        
        elif trait_name == "integrity_rule_following":
            # Terms reading, scroll focus, completion
            score = (terms_good + zigzag_good + completion_good) / 3.0
        
        elif trait_name == "obligation_to_repay":
            # Completion, engagement, terms reading
            score = (completion_good + scroll_good + terms_good) / 3.0
        
        elif trait_name == "grit_perseverance":
            # Completion, response engagement, scroll engagement
            score = (completion_good + response_good + scroll_engagement_good) / 3.0
        
        elif trait_name == "present_bias_time_preference":
            # Lower present bias = better. Use hesitation (thoughtful = less impulsive)
            score = (hesitation_good + consistency_good + response_good) / 3.0
        
        elif trait_name == "risk_attitude":
            # Moderate risk = balanced. Use extreme options as proxy
            score = extreme_good
        
        elif trait_name == "financial_decision_quality":
            # Response time, financial hesitation, scroll engagement
            score = (response_good + fin_hesitation_good + scroll_good) / 3.0
        
        elif trait_name == "spending_vs_saving" or trait_name == "spending_vs_saving_orientation":
            # Higher = saving orientation. Use terms (careful reader), hesitation
            score = (terms_good + hesitation_good + scroll_good) / 3.0
        
        elif trait_name == "commitment_follow_through":
            # Completion, scroll engagement, terms reading
            score = (completion_good + scroll_engagement_good + terms_good) / 3.0
        
        else:
            raise ValueError(f"Trait '{trait_name}' not recognized in compute_behaviour_traits")
        
        traits[trait_name] = _clamp(score)
    
    return traits


# ============================================================================
# COMBINED SCORING (Content + Behavior)
# ============================================================================

def compute_combined_traits(
    content_traits: Dict[str, float],
    behaviour_traits: Dict[str, float],
    trait_names: List[str],
    alpha: float = 0.6,
) -> Dict[str, float]:
    """
    Combine content and behavior traits using the PDF formula:
    Trait_final = α × Trait_behaviour + (1 - α) × Trait_content
    
    Default α = 0.6 (behavior weighted 60%, content 40%)
    """
    combined: Dict[str, float] = {}
    
    for trait_name in trait_names:
        if trait_name not in content_traits:
            raise ValueError(f"Content trait '{trait_name}' is missing")
        if trait_name not in behaviour_traits:
            raise ValueError(f"Behaviour trait '{trait_name}' is missing")
        
        content_score = content_traits[trait_name]
        behaviour_score = behaviour_traits[trait_name]
        
        final_score = alpha * behaviour_score + (1 - alpha) * content_score
        combined[trait_name] = _clamp(final_score)
    
    return combined


def compute_traits(
    answers_by_item: Dict[str, str],
    metadata: Dict[str, Any],
    score_map: Dict[str, Dict[str, int]],
    trait_names: List[str],
) -> Dict[str, float]:
    """
    Main entry point: compute final combined traits.
    Uses the three-body model:
    1. Content traits from answers
    2. Behaviour traits from metadata
    3. Combined: 0.6 × behaviour + 0.4 × content
    """
    content_traits = compute_content_traits(answers_by_item, score_map, trait_names)
    behaviour_traits = compute_behaviour_traits(metadata, trait_names)
    combined_traits = compute_combined_traits(content_traits, behaviour_traits, trait_names, alpha=0.6)
    
    return combined_traits


# ============================================================================
# REMOTE HF API CLIENT (OPTIONAL)
# ============================================================================

import requests as _requests

# Set this environment variable to use the Hugging Face Spaces API
# Example: HF_API_URL=https://dawittsegaye12-frankscore.hf.space
_HF_API_URL = os.environ.get("HF_API_URL", "").rstrip("/")

def _call_hf_psych_api(assessment_id: str, traits: Dict[str, float]) -> Optional[float]:
    """Call remote Hugging Face API for psychometric prediction."""
    if not _HF_API_URL:
        return None
    
    try:
        url = f"{_HF_API_URL}/predict/psych"
        payload = {
            "assessment_id": assessment_id,
            "features": traits
        }
        resp = _requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        pd_val = data.get("prediction_pd")
        if pd_val is not None:
            print(f"Info: Got psych PD {pd_val} from HF API")
            return _clamp(float(pd_val))
        return None
    except Exception as e:
        print(f"Warning: HF psych API call failed: {e}")
        return None


def _call_hf_kenya_api(assessment_id: str, features: Dict[str, Any]) -> Optional[float]:
    """Call remote Hugging Face API for Kenya (financial) prediction."""
    if not _HF_API_URL:
        return None
    
    try:
        url = f"{_HF_API_URL}/predict/kenya"
        payload = {
            "assessment_id": assessment_id,
            "features": features
        }
        resp = _requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        pd_val = data.get("prediction_pd")
        if pd_val is not None:
            print(f"Info: Got kenya PD {pd_val} from HF API")
            return _clamp(float(pd_val))
        return None
    except Exception as e:
        print(f"Warning: HF kenya API call failed: {e}")
        return None


# ============================================================================
# XGBoost MODEL
# ============================================================================

_XGB_MODEL = None
_XGB_FEATURE_COLUMNS = None


def load_xgb_model() -> None:
    """Load XGBoost model from models/xgb_model.joblib at startup."""
    global _XGB_MODEL, _XGB_FEATURE_COLUMNS
    model_path = "models/xgb_model.joblib"
    if not os.path.exists(model_path):
        print(f"Info: XGBoost model not found at {model_path}, will use fallback scoring")
        return
    try:
        import joblib
        model_data = joblib.load(model_path)
        
        if isinstance(model_data, dict):
            _XGB_MODEL = model_data.get("model")
            _XGB_FEATURE_COLUMNS = model_data.get("feature_columns")
            if _XGB_MODEL is None:
                print(f"Warning: Model dict found but 'model' key is missing")
                return
            print(f"Info: XGBoost model loaded with {len(_XGB_FEATURE_COLUMNS) if _XGB_FEATURE_COLUMNS else 'unknown'} feature columns")
        else:
            _XGB_MODEL = model_data
            _XGB_FEATURE_COLUMNS = None
            print(f"Info: XGBoost model loaded (direct format, no feature column info)")
    except Exception as e:
        print(f"Warning: Could not load XGBoost model from {model_path}: {e}")
        _XGB_MODEL = None
        _XGB_FEATURE_COLUMNS = None


def _normalize_trait_name(name: str) -> str:
    """Normalize trait name for matching."""
    import re
    return re.sub(r"[_/ -]+", "_", name.lower()).strip("_")


def _map_trait_to_feature_column(trait_name: str, feature_columns: List[str]) -> Optional[str]:
    """Map a trait name to a feature column name using fuzzy matching."""
    trait_norm = _normalize_trait_name(trait_name)
    
    # Explicit mappings for known mismatches
    explicit_map = {
        "impulsivity": "impulsivity_control",
        "impulsivity_control": "impulsivity_control",
        "present_bias_time_preference": "present_bias_control",
        "present_bias_timepreference": "present_bias_control",
        "present_bias": "present_bias_control",
        "risk_attitude": "risk_management",
        "risk": "risk_management",
        "spending_vs_saving_orientation": "saving_orientation",
        "spending_vs_saving": "saving_orientation",
        "commitment_follow_through": "follow_through",
        "commitment_followthrough": "follow_through",
        "follow_through": "follow_through",
    }
    
    if trait_norm in explicit_map and explicit_map[trait_norm] in feature_columns:
        return explicit_map[trait_norm]
    
    # Direct match
    for col in feature_columns:
        if _normalize_trait_name(col) == trait_norm:
            return col
    
    # Partial match
    for col in feature_columns:
        col_norm = _normalize_trait_name(col)
        if trait_norm in col_norm or col_norm in trait_norm:
            return col
    
    return None


def psychometric_pd(traits: Dict[str, float], trait_names: List[str], assessment_id: str = "unknown") -> float:
    """
    Predict psychometric PD using:
    1. Remote HF API (if HF_API_URL is set)
    2. Local XGBoost model (fallback)
    """
    # Try remote HF API first
    hf_result = _call_hf_psych_api(assessment_id, traits)
    if hf_result is not None:
        return hf_result
    
    # Fallback to local model
    if _XGB_MODEL is not None:
        try:
            import numpy as np
            
            if _XGB_FEATURE_COLUMNS is not None:
                feature_values = []
                for col in _XGB_FEATURE_COLUMNS:
                    matched_trait = None
                    for t in trait_names:
                        mapped_col = _map_trait_to_feature_column(t, [col])
                        if mapped_col == col:
                            matched_trait = t
                            break
                    
                    if matched_trait and matched_trait in traits:
                        feature_values.append(traits[matched_trait])
                    else:
                        raise ValueError(f"Could not map model feature column '{col}' to any trait. Available traits: {list(traits.keys())}")
                
                if len(feature_values) != len(_XGB_FEATURE_COLUMNS):
                    raise ValueError(f"Feature vector length mismatch")
            else:
                feature_values = []
                for t in trait_names:
                    if t not in traits:
                        raise ValueError(f"Trait '{t}' is missing from traits dictionary")
                    feature_values.append(traits[t])
            
            features = np.array([feature_values], dtype=np.float32)
            proba = _XGB_MODEL.predict_proba(features)[0]
            
            if len(proba) >= 2:
                pd_prob = float(proba[1])
            else:
                pd_prob = float(proba[0])
            
            return _clamp(pd_prob)
        except Exception as e:
            print(f"Warning: XGBoost prediction failed: {e}")
            return None
    
    # No model available
    print("Warning: No XGBoost model available for psychometric PD prediction")
    return None


# ============================================================================
# FINANCIAL PD
# ============================================================================

# ============================================================================
# RANDOM FOREST MODEL FOR FINANCIAL PD
# ============================================================================

_RF_MODEL = None
_RF_FEATURE_COLUMNS = None


def load_rf_model() -> None:
    """Load Random Forest model from models/random_forest.joblib at startup."""
    global _RF_MODEL, _RF_FEATURE_COLUMNS
    model_path = "models/random_forest.joblib"
    if not os.path.exists(model_path):
        print(f"Info: Random Forest model not found at {model_path}, will use fallback scoring")
        return
    try:
        import joblib
        _RF_MODEL = joblib.load(model_path)
        
        # Extract feature names from the model pipeline
        if hasattr(_RF_MODEL, 'feature_names_in_'):
            _RF_FEATURE_COLUMNS = _RF_MODEL.feature_names_in_.tolist()
        elif hasattr(_RF_MODEL, 'steps'):
            # Try to get feature names from the pipeline
            try:
                # For sklearn pipelines, we need to check the transformer
                transformer = _RF_MODEL.steps[0][1] if len(_RF_MODEL.steps) > 0 else None
                if hasattr(transformer, 'feature_names_in_'):
                    _RF_FEATURE_COLUMNS = transformer.feature_names_in_.tolist()
            except:
                pass
        
        if _RF_FEATURE_COLUMNS:
            print(f"Info: Random Forest model loaded with {len(_RF_FEATURE_COLUMNS)} feature columns")
        else:
            print(f"Info: Random Forest model loaded (feature columns not detected)")
    except Exception as e:
        print(f"Warning: Could not load Random Forest model from {model_path}: {e}")
        _RF_MODEL = None
        _RF_FEATURE_COLUMNS = None


def financial_pd_from_model(financial_data: Dict[str, Any], assessment_id: str = "unknown") -> Optional[float]:
    """
    Calculate financial PD using:
    1. Remote HF API (if HF_API_URL is set)
    2. Local Random Forest model (fallback)
    Returns None if both are unavailable.
    """
    # Try remote HF API first
    hf_result = _call_hf_kenya_api(assessment_id, financial_data)
    if hf_result is not None:
        return hf_result
    
    # Fallback to local model
    if _RF_MODEL is None:
        return None
    
    if _RF_FEATURE_COLUMNS is None:
        print("Warning: Feature columns not available for Random Forest model")
        return None
    
    try:
        import pandas as pd
        import numpy as np
        
        # Prepare feature vector
        features = {}
        for col in _RF_FEATURE_COLUMNS:
            value = financial_data.get(col)
            # Handle NaN/None values - use 0 for numeric, empty string for categorical
            if value is None or (isinstance(value, float) and np.isnan(value)):
                # Use default values based on column type
                if col in ["amount_bucket"]:
                    features[col] = "q2"  # Default bucket
                else:
                    features[col] = 0.0
            else:
                features[col] = value
        
        # Create DataFrame with single row
        df = pd.DataFrame([features])
        
        # Ensure columns are in the correct order
        df = df[_RF_FEATURE_COLUMNS]
        
        # Predict probability of default (class 1)
        # The model predicts probabilities for classes [0, 1]
        probabilities = _RF_MODEL.predict_proba(df)
        
        if probabilities.shape[1] >= 2:
            # Probability of default (class 1)
            pd_value = float(probabilities[0][1])
        else:
            # Fallback if only one class
            pd_value = float(probabilities[0][0])
        
        return _clamp(pd_value)
    
    except Exception as e:
        error_msg = str(e)
        print(f"Error predicting financial PD: {error_msg}")
        
        # Check if it's a version incompatibility issue
        if "_fill_dtype" in error_msg or "AttributeError" in error_msg:
            print("Warning: Model version incompatibility detected.")
            print("The model was trained with scikit-learn 1.4.2, but current version is different.")
            print("Please retrain the model with the current scikit-learn version, or downgrade scikit-learn.")
        
        import traceback
        traceback.print_exc()
        return None


def financial_pd(
    *,
    monthly_income: float,
    monthly_expenses: float,
    total_debt: float,
    missed_payments_3m: int,
) -> float:
    """
    Calculate financial PD based on income, expenses, debt, and missed payments.
    This is the fallback method when model is not available.
    """
    inc = max(float(monthly_income), 1.0)
    dti = float(total_debt) / inc
    savings = float(monthly_income) - float(monthly_expenses)
    savings_norm = savings / inc

    a0 = -1.00
    a1 = +1.20  # dti
    a2 = +0.60  # missed payments
    a3 = +1.00  # savings_norm (subtracted)

    z = a0 + a1 * dti + a2 * float(missed_payments_3m) - a3 * savings_norm
    return _clamp(sigmoid(z))


def combine_pd(pd_psych_hat: Optional[float], pd_fin_hat: Optional[float]) -> Optional[float]:
    """Combine psychometric and financial PD: 60% financial + 40% psychometric."""
    if pd_psych_hat is None and pd_fin_hat is None:
        return None
    if pd_psych_hat is None:
        return float(pd_fin_hat)
    if pd_fin_hat is None:
        return float(pd_psych_hat)
    return 0.6 * float(pd_fin_hat) + 0.4 * float(pd_psych_hat)
