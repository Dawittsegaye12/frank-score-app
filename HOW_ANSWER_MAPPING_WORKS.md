# How Answer Mapping Works in the Website

## Overview
This document explains how user-selected answers (A, B, C, D) are mapped to numeric scores (0-3) in the FrankScore system.

---

## Step-by-Step Process

### Step 1: Loading the Scoring Map (Server Startup)

When the FastAPI server starts, it loads the scoring map from the admin JSON file:

**File:** `app.py` (lines 70-77)

```python
def load_question_banks():
    # ... loads public JSON for frontend ...
    
    # Load admin JSON for scoring
    with open("questiondb/psychometric_question_bank_v2_admin.json", "r") as f:
        admin_data = json.load(f)
    
    ADMIN_SCORING_MAP = {}
    for trait in admin_data.get("traits", []):
        for item in trait.get("items", []):
            item_id = item["item_id"]  # e.g., "1.1", "2.1", etc.
            score_map = item.get("score_map_0_to_3", {})  # e.g., {"A": 2, "B": 3, "C": 0, "D": 1}
            ADMIN_SCORING_MAP[item_id] = score_map
```

**Result:** `ADMIN_SCORING_MAP` is a dictionary like:
```python
{
    "1.1": {"B": 3, "A": 2, "D": 1, "C": 0},
    "2.1": {"B": 3, "D": 2, "A": 1, "C": 0},
    "3.1": {"C": 3, "B": 2, "D": 1, "A": 0},
    # ... etc for all 15 questions
}
```

---

### Step 2: User Selects an Answer (Frontend)

When a user selects an option on the questionnaire page:

**File:** `static/questions.js`

The frontend sends the selected option (A, B, C, or D) to the backend:

```javascript
// User clicks option A, B, C, or D
const selectedOption = "B";  // example

// Send to backend
await fetch("/api/answer", {
    method: "POST",
    body: JSON.stringify({
        assessment_id: "...",
        item_id: "1.1",
        selected_option: "B",  // ← This is what gets stored
        answered_at_ms: Date.now()
    })
});
```

**Database:** The answer is stored in the `responses` table with:
- `item_id`: "1.1"
- `selected_option`: "B" (stored as text, not numeric)

---

### Step 3: Retrieving Answers (When Computing Traits)

When the assessment is completed, the system retrieves all answers:

**File:** `app.py` (lines 300-311)

```python
@app.post("/api/complete")
def api_complete(req: CompleteRequest):
    # Get all responses from database
    responses = db.list_responses(req.assessment_id)
    
    # Build dictionary: item_id -> selected_option
    answers_by_item: Dict[str, str] = {}
    for r in responses:
        item_id = r["item_id"]  # e.g., "1.1"
        selected = r.get("selected_option")  # e.g., "B"
        if selected:
            answers_by_item[item_id] = selected
    
    # Now answers_by_item looks like:
    # {"1.1": "B", "2.1": "D", "3.1": "C", ...}
    
    # Compute traits using the scoring map
    traits = scoring.compute_traits(
        answers_by_item,      # {"1.1": "B", "2.1": "D", ...}
        metadata,
        ADMIN_SCORING_MAP,    # {"1.1": {"B": 3, "A": 2, ...}, ...}
        TRAIT_NAMES
    )
```

---

### Step 4: Mapping to Numeric Scores (Scoring Engine)

The scoring engine maps each selected option to its numeric value:

**File:** `scoring.py` (lines 276-315)

```python
def compute_content_traits(
    answers_by_item: Dict[str, str],      # {"1.1": "B", "2.1": "D", ...}
    score_map: Dict[str, Dict[str, int]],  # ADMIN_SCORING_MAP
    trait_names: List[str],
) -> Dict[str, float]:
    trait_item_scores: Dict[int, List[int]] = {}
    
    # For each answered question
    for item_id, selected_option in answers_by_item.items():
        # item_id = "1.1", selected_option = "B"
        
        # Get the scoring map for this question
        item_score_map = score_map.get(item_id, {})
        # item_score_map = {"B": 3, "A": 2, "D": 1, "C": 0}
        
        # Look up the numeric score for the selected option
        score = item_score_map.get(selected_option)
        # score = 3 (because selected_option = "B" maps to 3)
        
        if score is None:
            continue  # Skip if mapping not found
        
        # Extract trait_id from item_id (e.g., "1.1" -> trait_id = 1)
        trait_id = int(item_id.split(".")[0])
        
        # Store the score for this trait
        if trait_id not in trait_item_scores:
            trait_item_scores[trait_id] = []
        trait_item_scores[trait_id].append(score)
    
    # Now compute normalized trait scores
    traits: Dict[str, float] = {}
    for i, trait_name in enumerate(trait_names, start=1):
        item_scores = trait_item_scores.get(i, [])
        if item_scores:
            # Average the scores
            trait_raw = sum(item_scores) / len(item_scores)
            # Normalize to [0, 1] by dividing by 3.0
            trait_final = trait_raw / 3.0
        else:
            raise ValueError(f"No answers provided for trait {trait_name}")
        
        traits[trait_name] = _clamp(trait_final)
    
    return traits
```

---

## Example Flow

Let's trace through a complete example:

### Example: User answers Question 1.1 with option "B"

1. **User selects "B"** on the frontend
   - Frontend sends: `{"item_id": "1.1", "selected_option": "B"}`

2. **Answer stored in database**
   - `responses` table: `item_id="1.1"`, `selected_option="B"`

3. **When computing traits:**
   ```python
   answers_by_item = {"1.1": "B"}
   ADMIN_SCORING_MAP = {
       "1.1": {"B": 3, "A": 2, "D": 1, "C": 0}
   }
   ```

4. **Mapping happens:**
   ```python
   item_id = "1.1"
   selected_option = "B"
   item_score_map = ADMIN_SCORING_MAP["1.1"]  # {"B": 3, "A": 2, "D": 1, "C": 0}
   score = item_score_map["B"]  # score = 3
   ```

5. **Trait computation:**
   ```python
   trait_id = 1  # from "1.1"
   trait_item_scores[1] = [3]  # Store score for trait 1
   
   # For trait 1 (Conscientiousness):
   trait_raw = 3 / 1 = 3.0
   trait_final = 3.0 / 3.0 = 1.0  # Normalized to [0, 1]
   ```

6. **Final result:**
   - `traits["conscientiousness"] = 1.0` (maximum score for this trait)

---

## Key Points

1. **Mapping is stored in JSON**: The `score_map_0_to_3` in the admin JSON file defines the mapping
2. **Frontend only sends letters**: The frontend sends "A", "B", "C", or "D" as text
3. **Backend does the mapping**: The scoring engine looks up the numeric value using `ADMIN_SCORING_MAP`
4. **Scores are normalized**: Raw scores (0-3) are averaged and divided by 3.0 to get [0, 1] range
5. **One question per trait**: Currently, each trait has exactly one question, so the average is just that one score

---

## Files Involved

1. **`questiondb/psychometric_question_bank_v2_admin.json`**: Contains the `score_map_0_to_3` for each question
2. **`app.py`**: Loads the scoring map at startup and passes it to the scoring engine
3. **`scoring.py`**: Contains `compute_content_traits()` which performs the actual mapping
4. **`static/questions.js`**: Frontend code that sends selected options to the backend
5. **`db.py`**: Stores answers in the database with `selected_option` as text

---

## Summary

The mapping process is:
1. **Load** scoring maps from JSON at server startup
2. **Store** user selections as letters (A/B/C/D) in the database
3. **Retrieve** answers when computing traits
4. **Map** letters to numbers (0-3) using the scoring map
5. **Normalize** scores to [0, 1] range for trait computation

The actual mapping happens in `scoring.py` in the `compute_content_traits()` function, which uses the `ADMIN_SCORING_MAP` loaded from the admin JSON file.





