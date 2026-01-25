# Default 0.5 Value Locations in scoring.py

## Summary
There are **6 locations** where `0.5` is used as a default/placeholder value for traits.

---

## 1. Line 301: `compute_content_traits()` - No answers for a trait

**Function:** `compute_content_traits()`  
**Location:** `scoring.py:295-302`  
**Context:** When no item scores exist for a trait (no answers provided)

```python
for i, trait_name in enumerate(trait_names, start=1):
    item_scores = trait_item_scores.get(i, [])
    if item_scores:
        trait_raw = sum(item_scores) / len(item_scores)
        trait_final = trait_raw / 3.0
    else:
        trait_final = 0.5  # ← DEFAULT 0.5 HERE
    traits[trait_name] = _clamp(trait_final)
```

**When it's used:** If a user doesn't answer any questions for a specific trait, it defaults to 0.5.

---

## 2. Line 350: `compute_behaviour_traits()` - Hesitation too high

**Function:** `compute_behaviour_traits()`  
**Location:** `scoring.py:348-350`  
**Context:** When hesitation time is > 10 seconds

```python
# Hesitation: some hesitation is good (thoughtful), too much is bad
hesitation = _safe_float(metadata.get("hesitation_time_avg"), 2)
hesitation_good = _clamp(hesitation / 5.0) if hesitation <= 10 else 0.5  # ← DEFAULT 0.5 HERE
```

**When it's used:** If average hesitation time exceeds 10 seconds, the hesitation_good value defaults to 0.5.

---

## 3. Line 390: `compute_behaviour_traits()` - Financial hesitation too high

**Function:** `compute_behaviour_traits()`  
**Location:** `scoring.py:389-390`  
**Context:** When financial item hesitation time is > 10 seconds

```python
fin_hesitation = _safe_float(metadata.get("hesitation_time_financial_items"), 2)
fin_hesitation_good = _clamp(fin_hesitation / 5.0) if fin_hesitation <= 10 else 0.5  # ← DEFAULT 0.5 HERE
```

**When it's used:** If financial item hesitation time exceeds 10 seconds, defaults to 0.5.

---

## 4. Line 445: `compute_behaviour_traits()` - Unknown trait name

**Function:** `compute_behaviour_traits()`  
**Location:** `scoring.py:443-445`  
**Context:** When a trait name doesn't match any of the 15 known traits

```python
else:
    # Default neutral
    score = 0.5  # ← DEFAULT 0.5 HERE

traits[trait_name] = _clamp(score)
```

**When it's used:** If a trait name is not recognized in the if/elif chain, it defaults to 0.5. This shouldn't happen with the 15 standard traits, but acts as a fallback.

---

## 5. Lines 471-472: `compute_combined_traits()` - Missing trait in content/behaviour

**Function:** `compute_combined_traits()`  
**Location:** `scoring.py:470-472`  
**Context:** When a trait is missing from content_traits or behaviour_traits dictionaries

```python
for trait_name in trait_names:
    content_score = content_traits.get(trait_name, 0.5)  # ← DEFAULT 0.5 HERE
    behaviour_score = behaviour_traits.get(trait_name, 0.5)  # ← DEFAULT 0.5 HERE
    
    final_score = alpha * behaviour_score + (1 - alpha) * content_score
```

**When it's used:** If a trait is not found in the content_traits or behaviour_traits dictionaries, it uses 0.5 as the default value.

---

## 6. Lines 599 & 604: `psychometric_pd()` - Missing trait in model features

**Function:** `psychometric_pd()`  
**Location:** `scoring.py:596-604`  
**Context:** When mapping traits to model feature columns fails

```python
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
            feature_values.append(0.5)  # ← DEFAULT 0.5 HERE (line 599)
    
    if len(feature_values) != len(_XGB_FEATURE_COLUMNS):
        raise ValueError(f"Feature vector length mismatch")
else:
    feature_values = [traits.get(t, 0.5) for t in trait_names]  # ← DEFAULT 0.5 HERE (line 604)
```

**When it's used:**
- **Line 599:** If a model feature column cannot be mapped to any trait, it uses 0.5
- **Line 604:** If `_XGB_FEATURE_COLUMNS` is None and a trait is missing from the traits dictionary, it uses 0.5

---

## Summary Table

| Line | Function | Context | When Used |
|------|----------|---------|-----------|
| 301 | `compute_content_traits()` | No answers for trait | No item scores exist |
| 350 | `compute_behaviour_traits()` | Hesitation > 10s | Average hesitation too high |
| 390 | `compute_behaviour_traits()` | Financial hesitation > 10s | Financial hesitation too high |
| 445 | `compute_behaviour_traits()` | Unknown trait name | Trait not in if/elif chain |
| 471-472 | `compute_combined_traits()` | Missing trait in dict | Trait not in content/behaviour dicts |
| 599 | `psychometric_pd()` | Feature mapping fails | Model feature can't be mapped to trait |
| 604 | `psychometric_pd()` | Missing trait in dict | Trait missing when _XGB_FEATURE_COLUMNS is None |

---

## Note
Based on your screenshot showing varying trait values (0.4733 to 0.8969), **these defaults are NOT being triggered** - your traits are being computed correctly! The issue is with the model itself always predicting 0.9177 regardless of input.

