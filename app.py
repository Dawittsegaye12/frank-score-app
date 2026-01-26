import json
import os
import random
import time
import uuid
import traceback
from datetime import datetime
from typing import Any, Dict, List, Optional

# #region agent log
import sys
LOG_PATH = os.path.join(os.getcwd(), ".cursor", "debug.log")
def _log(hypothesis_id, location, message, data=None, error=None):
    try:
        entry = {
            "timestamp": int(datetime.now().timestamp() * 1000),
            "location": location,
            "message": message,
            "sessionId": "debug-session",
            "runId": "run1",
            "hypothesisId": hypothesis_id,
            "data": data or {},
        }
        if error:
            entry["error"] = str(error)
            entry["traceback"] = traceback.format_exc()
        log_str = json.dumps(entry)
        # Write to file (for local debugging)
        try:
            os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
            with open(LOG_PATH, "a", encoding="utf-8") as f:
                f.write(log_str + "\n")
        except Exception:
            pass
        # Also print to stderr (captured by Vercel logs)
        print(f"[DEBUG] {log_str}", file=sys.stderr, flush=True)
    except Exception:
        pass
# #endregion

try:
    # #region agent log
    _log("H1", "app.py:30", "Starting app module imports", {"cwd": os.getcwd()})
    # #endregion
    
    from fastapi import FastAPI, HTTPException, Request
    from fastapi.responses import HTMLResponse, JSONResponse
    from fastapi.staticfiles import StaticFiles
    from fastapi.templating import Jinja2Templates
    from pydantic import BaseModel, Field
    
    # #region agent log
    _log("H1", "app.py:40", "FastAPI imports successful")
    # #endregion
    
    # #region agent log
    _log("H1", "app.py:43", "About to import db module")
    # #endregion
    import db
    # #region agent log
    _log("H1", "app.py:46", "db module imported")
    # #endregion
    
    # #region agent log
    _log("H1", "app.py:48", "About to import scoring module")
    # #endregion
    import scoring
    # #region agent log
    _log("H1", "app.py:51", "scoring module imported")
    # #endregion
    
    # #region agent log
    _log("H1", "app.py:53", "About to import admin_data_dual_models")
    # #endregion
    import admin_data_dual_models as admin_mock_data
    # #region agent log
    _log("H1", "app.py:56", "admin_data_dual_models imported")
    # #endregion
    
    # #region agent log
    _log("H1", "app.py:58", "About to import services.scoring_api")
    # #endregion
    from services import scoring_api
    # #region agent log
    _log("H1", "app.py:61", "services.scoring_api imported")
    # #endregion
    
    # #region agent log
    _log("H6", "app.py:64", "Creating FastAPI app instance")
    # #endregion
    app = FastAPI(title="frankscore_demo")
    
    # #region agent log
    _log("H6", "app.py:67", "Initializing Jinja2Templates", {"templates_dir": "templates", "exists": os.path.exists("templates")})
    # #endregion
    templates = Jinja2Templates(directory="templates")
    # #region agent log
    _log("H6", "app.py:70", "Jinja2Templates initialized")
    # #endregion
    
    # #region agent log
    _log("H7", "app.py:73", "Mounting StaticFiles", {"static_dir": "static", "exists": os.path.exists("static")})
    # #endregion
    app.mount("/static", StaticFiles(directory="static"), name="static")
    # #region agent log
    _log("H7", "app.py:76", "StaticFiles mounted successfully")
    # #endregion
    
    # #region agent log
    _log("H1", "app.py:78", "App module initialization complete")
    # #endregion

except Exception as e:
    # #region agent log
    _log("H1", "app.py:81", "CRITICAL: App module import/initialization failed", error=e)
    # #endregion
    # Create minimal app to prevent complete failure
    app = FastAPI(title="frankscore_demo_error")
    raise


# Question bank data (loaded at startup)
PUBLIC_QUESTIONS: List[Dict[str, Any]] = []  # All 75 questions (for backward compatibility)
QUESTIONS_BY_TRAIT: Dict[int, List[Dict[str, Any]]] = {}  # trait_id -> list of 5 items
ADMIN_SCORING_MAP: Dict[str, Dict[str, int]] = {}  # item_id -> {option_letter: score_0_to_3}
TRAIT_NAMES: List[str] = []


def load_question_banks() -> None:
    """Load public JSON for frontend and admin JSON for scoring."""
    global PUBLIC_QUESTIONS, QUESTIONS_BY_TRAIT, ADMIN_SCORING_MAP, TRAIT_NAMES
    
    public_path = "questiondb/psychometric_question_bank_v2_public.json"
    admin_path = "questiondb/psychometric_question_bank_v2_admin.json"
    
    # #region agent log
    _log("H2", "app.py:110", "load_question_banks called", {"cwd": os.getcwd(), "public_path": public_path, "public_exists": os.path.exists(public_path), "admin_path": admin_path, "admin_exists": os.path.exists(admin_path), "questiondb_exists": os.path.exists("questiondb")})
    # #endregion
    
    # Load public JSON (for /api/questions)
    if os.path.exists(public_path):
        with open(public_path, "r", encoding="utf-8") as f:
            public_data = json.load(f)
        PUBLIC_QUESTIONS = []
        QUESTIONS_BY_TRAIT = {}
        for trait in public_data.get("traits", []):
            trait_id = trait.get("trait_id")
            if trait_id not in QUESTIONS_BY_TRAIT:
                QUESTIONS_BY_TRAIT[trait_id] = []
            for item in trait.get("items", []):
                item_data = {
                    "item_id": item["item_id"],
                    "prompt": item["prompt"],
                    "options": item["options"],  # {"A": "...", "B": "...", "C": "...", "D": "..."}
                }
                PUBLIC_QUESTIONS.append(item_data)
                QUESTIONS_BY_TRAIT[trait_id].append(item_data)
        # Extract trait names and normalize (lowercase, spaces/slashes/hyphens to underscores)
        TRAIT_NAMES = []
        for trait in public_data.get("traits", []):
            name = trait.get("trait_name", "")
            # Normalize: lowercase, replace spaces/hyphens/slashes with underscores, collapse multiple underscores
            import re
            normalized = re.sub(r"[_/ -]+", "_", name.lower()).strip("_")
            TRAIT_NAMES.append(normalized)
        if not TRAIT_NAMES or len(TRAIT_NAMES) != 15:
            TRAIT_NAMES = scoring.get_trait_names()
    else:
        TRAIT_NAMES = scoring.get_trait_names()
    
    # Load admin JSON (for scoring)
    if os.path.exists(admin_path):
        with open(admin_path, "r", encoding="utf-8") as f:
            admin_data = json.load(f)
        ADMIN_SCORING_MAP = {}
        for trait in admin_data.get("traits", []):
            for item in trait.get("items", []):
                item_id = item["item_id"]
                score_map = item.get("score_map_0_to_3", {})
                ADMIN_SCORING_MAP[item_id] = score_map


# Initialize lazily on first request instead of startup event
# Startup events don't work reliably in serverless environments
_initialized = False

def _ensure_initialized():
    """Lazy initialization - called on first request"""
    global _initialized
    if _initialized:
        return
    # #region agent log
    _log("H4", "app.py:90", "Lazy initialization triggered")
    # #endregion
    try:
        # #region agent log
        _log("H4", "app.py:94", "Calling db.init_db()")
        # #endregion
        db.init_db()
        # #region agent log
        _log("H4", "app.py:97", "db.init_db() completed")
        # #endregion
        
        # #region agent log
        _log("H4", "app.py:100", "Calling load_question_banks()")
        # #endregion
        load_question_banks()
        # #region agent log
        _log("H4", "app.py:103", "load_question_banks() completed", {"questions_count": len(PUBLIC_QUESTIONS), "traits_count": len(TRAIT_NAMES)})
        # #endregion
        
        _initialized = True
        # #region agent log
        _log("H4", "app.py:108", "Lazy initialization completed successfully")
        # #endregion
    except Exception as e:
        # #region agent log
        _log("H4", "app.py:111", "Initialization error (non-fatal)", error=e)
        # #endregion
        # Log error but don't crash - allow app to continue
        import logging
        logging.error(f"Initialization error (non-fatal): {e}")

# Keep startup event for compatibility but make it no-op
@app.on_event("startup")
def _startup() -> None:
    # No-op in serverless - use lazy initialization instead
    pass


def now_ms() -> int:
    return int(time.time() * 1000)


class StartRequest(BaseModel):
    # Accept unknown fields (e.g. older clients still sending consent_psychometric)
    model_config = {"extra": "ignore"}
    user_id: Optional[str] = None
    consent_financial: bool = False


class StartResponse(BaseModel):
    assessment_id: str
    session_id: str


class AnswerRequest(BaseModel):
    assessment_id: str
    item_id: str
    selected_option: str = Field(pattern="^[ABCD]$")  # A, B, C, or D
    answered_at_ms: int


class EventIn(BaseModel):
    event_name: str
    client_ts_ms: int
    perf_ts_ms: Optional[float] = None
    item_id: Optional[str] = None
    seq: int
    payload: Optional[Dict[str, Any]] = None


class EventsRequest(BaseModel):
    assessment_id: str
    session_id: str
    events: List[EventIn]


class FinancialRequest(BaseModel):
    assessment_id: str
    monthly_income: float
    monthly_expenses: float
    total_debt: float
    missed_payments_3m: int = Field(ge=0, le=24)


class CompleteRequest(BaseModel):
    assessment_id: str


class SignupRequest(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6)
    email: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


@app.get("/health")
def health() -> Dict[str, Any]:
    # #region agent log
    _log("H8", "app.py:292", "Health endpoint called")
    # #endregion
    _ensure_initialized()  # Lazy initialization
    try:
        with db.get_conn() as conn:
            conn.execute("SELECT 1").fetchone()
        return {"ok": True, "db": "ok"}
    except Exception as e:
        # #region agent log
        _log("H8", "app.py:300", "Health check failed", error=e)
        # #endregion
        return {"ok": False, "db": "error", "error": str(e)}


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> Any:
    """Redirect to login page."""
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request) -> Any:
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/signup", response_class=HTMLResponse)
def signup_page(request: Request) -> Any:
    return templates.TemplateResponse("signup.html", {"request": request})


@app.get("/terms", response_class=HTMLResponse)
def terms(request: Request) -> Any:
    return templates.TemplateResponse("terms.html", {"request": request})


@app.get("/questions", response_class=HTMLResponse)
def questions_page(request: Request, assessment_id: str) -> Any:
    attempt = db.get_attempt(assessment_id)
    if not attempt:
        raise HTTPException(status_code=404, detail="assessment_id not found")
    return templates.TemplateResponse(
        "questions.html",
        {
            "request": request,
            "assessment_id": assessment_id,
        },
    )


@app.get("/financial", response_class=HTMLResponse)
def financial_page(request: Request, assessment_id: str) -> Any:
    attempt = db.get_attempt(assessment_id)
    if not attempt:
        raise HTTPException(status_code=404, detail="assessment_id not found")
    # Financial page is optional - allow access if assessment exists
    return templates.TemplateResponse(
        "financial.html",
        {"request": request, "assessment_id": assessment_id},
    )


@app.get("/result", response_class=HTMLResponse)
def result_page(request: Request, assessment_id: str) -> Any:
    attempt = db.get_attempt(assessment_id)
    if not attempt:
        raise HTTPException(status_code=404, detail="assessment_id not found")
    return templates.TemplateResponse(
        "result.html",
        {"request": request, "assessment_id": assessment_id},
    )


@app.post("/api/signup")
def api_signup(req: SignupRequest) -> Any:
    """Create a new user account."""
    import hashlib
    
    # Check if username already exists
    existing = db.get_user_by_username(req.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Hash password
    password_hash = hashlib.sha256(req.password.encode()).hexdigest()
    
    # Create user
    user_id = db.create_user(req.username, password_hash, req.email)
    
    return {"ok": True, "user_id": user_id, "message": "Account created successfully"}


@app.post("/api/login")
def api_login(req: LoginRequest) -> Any:
    """Login and return user_id."""
    import hashlib
    
    # Get user
    user = db.get_user_by_username(req.username)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    # Verify password
    password_hash = hashlib.sha256(req.password.encode()).hexdigest()
    if user["password_hash"] != password_hash:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    # Update last login
    db.update_last_login(user["id"])
    
    return {"ok": True, "user_id": user["id"], "username": user["username"]}


@app.post("/api/start", response_model=StartResponse)
def api_start(req: StartRequest) -> Any:
    """
    Start a new assessment.
    In v2, this requires a user_id (from login) and uses their financial data.
    """
    try:
        # user_id should be provided from the frontend after login
        user_id = req.user_id
        if user_id:
            try:
                user_id = int(user_id)
            except (ValueError, TypeError):
                user_id = None
        
        # Generate assessment_id in FSxxxxxx format (matching dataset format)
        next_id = db.get_next_user_id()
        assessment_id = f"FS{next_id:06d}"
        session_id = uuid.uuid4().hex
        db.insert_attempt(
            assessment_id=assessment_id,
            user_id=user_id,
            session_id=session_id,
            status="in_progress",
            started_at_ms=now_ms(),
        )
        return {"assessment_id": assessment_id, "session_id": session_id}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


@app.get("/api/questions")
def api_questions(assessment_id: Optional[str] = None) -> Any:
    """
    Returns 15 questions (one per trait) with rotation based on assessment_id.
    If assessment_id is provided, uses it to deterministically select which of the 5 items per trait to show.
    This ensures different users get different questions, but the same user gets the same questions.
    """
    if not QUESTIONS_BY_TRAIT:
        # Fallback to all questions if not organized by trait
        if PUBLIC_QUESTIONS:
            return PUBLIC_QUESTIONS
        return [{"item_id": "Q1", "text": "Demo question (question bank not found)"}]
    
    # Select one question per trait with rotation
    selected_questions = []
    
    # Use assessment_id to determine rotation (hash-based for deterministic selection)
    rotation_seed = 0
    if assessment_id:
        # Use hash of assessment_id as seed for rotation
        rotation_seed = hash(assessment_id) % 1000
    
    # Sort trait IDs to ensure consistent order
    trait_ids = sorted(QUESTIONS_BY_TRAIT.keys())
    
    for trait_id in trait_ids:
        items = QUESTIONS_BY_TRAIT[trait_id]
        if not items:
            continue
        
        # Select which of the 5 items to use for this trait (0-4)
        # Use rotation_seed + trait_id to vary selection per trait
        item_index = (rotation_seed + trait_id) % len(items)
        selected_questions.append(items[item_index])
    
    return selected_questions


@app.post("/api/answer")
def api_answer(req: AnswerRequest) -> Any:
    attempt = db.get_attempt(req.assessment_id)
    if not attempt:
        raise HTTPException(status_code=404, detail="assessment_id not found")
    db.insert_response(
        assessment_id=req.assessment_id,
        item_id=req.item_id,
        selected_option=req.selected_option,
        answered_at_ms=req.answered_at_ms,
    )
    return {"ok": True}


@app.post("/api/events")
def api_events(req: EventsRequest) -> Any:
    attempt = db.get_attempt(req.assessment_id)
    if not attempt:
        raise HTTPException(status_code=404, detail="assessment_id not found")
    db.insert_events(
        assessment_id=req.assessment_id,
        session_id=req.session_id,
        events=[e.model_dump() for e in req.events],
    )
    return {"ok": True}


@app.post("/api/financial")
def api_financial(req: FinancialRequest) -> Any:
    try:
        attempt = db.get_attempt(req.assessment_id)
        if not attempt:
            raise HTTPException(status_code=404, detail="assessment_id not found")
        # Financial data is optional - allow submission if assessment exists
        db.upsert_financial(
            assessment_id=req.assessment_id,
            monthly_income=req.monthly_income,
            monthly_expenses=req.monthly_expenses,
            total_debt=req.total_debt,
            missed_payments_3m=req.missed_payments_3m,
        )
        return {"ok": True}
    except Exception as e:
        import traceback
        error_msg = str(e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error saving financial data: {error_msg}")


@app.post("/api/complete")
def api_complete(req: CompleteRequest) -> Any:
    attempt = db.get_attempt(req.assessment_id)
    if not attempt:
        raise HTTPException(status_code=404, detail="assessment_id not found")

    try:
        events = db.list_events(req.assessment_id)
        responses = db.list_responses(req.assessment_id)

        # Latest answer per item (selected_option: "A"/"B"/"C"/"D").
        answers_by_item: Dict[str, str] = {}
        for r in responses:
            item_id = r["item_id"]
            selected = r.get("selected_option")
            if selected:
                answers_by_item[item_id] = selected

        metadata = scoring.compute_metadata(events)
        traits = scoring.compute_traits(answers_by_item, metadata, ADMIN_SCORING_MAP, TRAIT_NAMES)

        # #region agent log
        try:
            with open('.cursor/debug.log', 'a', encoding='utf-8') as f:
                f.write(json.dumps({"location": "app.py:311", "message": "final traits computed", "data": {"assessment_id": req.assessment_id, "traits": traits, "trait_count": len(traits)}, "timestamp": int(time.time() * 1000), "sessionId": "debug-session", "runId": "run1", "hypothesisId": "traits_output"}) + "\n")
        except Exception:
            pass
        # #endregion


        pd_psych_hat = scoring.psychometric_pd(traits, TRAIT_NAMES, assessment_id=req.assessment_id)

        pd_fin_hat: Optional[float] = None
        # In v2, get financial data from user's persona data (if available)
        attempt = db.get_attempt(req.assessment_id)
        user_id = attempt.get("user_id") if attempt else None
        
        # Data preparation for External API
        financial_data = None
        api_payload = {}
        
        # Debug logging
        print(f"[DEBUG] Financial PD calculation for assessment {req.assessment_id}:")
        print(f"  - user_id from attempt: {user_id}")
        
        if user_id:
            # Try to get financial data from user's persona
            financial_data = db.get_financial_data(user_id)
            print(f"  - financial_data retrieved: {financial_data is not None}")
            
            if financial_data:
                # Use Random Forest model for prediction (local fallback)
                print(f"  - Attempting model prediction...")
                pd_fin_hat = scoring.financial_pd_from_model(financial_data, assessment_id=req.assessment_id)
                print(f"  - Model prediction result: {pd_fin_hat}")
                
                 # Populate API payload with financial data
                # We use the raw dictionary from DB which matches the columns
                api_payload = financial_data.copy()
                # Remove internal IDs if necessary, but additionalProperties: true allows them mostly.
                if "user_id" in api_payload: del api_payload["user_id"]
                if "customer_id" in api_payload: del api_payload["customer_id"]

                
                # If model failed, use a simple fallback based on financial data
                if pd_fin_hat is None and financial_data:
                    # Simple fallback: use Total_Amount and daily_burden to estimate risk
                    total_amount = financial_data.get("Total_Amount", 0) or 0
                    daily_burden = financial_data.get("daily_burden", 0) or 0
                    num_loans = financial_data.get("num_previous_loans", 0) or 0
                    
                    # Simple heuristic: higher amount/burden ratio = higher risk
                    if total_amount > 0 and daily_burden > 0:
                        burden_ratio = daily_burden / (total_amount / 30) if total_amount > 0 else 0
                        # Normalize to 0-1 range (rough estimate)
                        pd_fin_hat = min(1.0, max(0.0, burden_ratio * 0.3 + (1 - min(1.0, num_loans / 10)) * 0.2))
                        print(f"  - Using fallback financial PD calculation: {pd_fin_hat}")
            else:
                print(f"  - Warning: No financial data found for user_id {user_id}")
        else:
            print(f"  - Warning: No user_id found in attempt record")
        
        # Fallback to old method if model prediction failed or no user data
        if pd_fin_hat is None:
            print(f"  - Falling back to old financial PD method...")
            fin = db.get_financial(req.assessment_id)
            if fin:
                pd_fin_hat = scoring.financial_pd(
                    monthly_income=float(fin["monthly_income"] or 0.0),
                    monthly_expenses=float(fin["monthly_expenses"] or 0.0),
                    total_debt=float(fin["total_debt"] or 0.0),
                    missed_payments_3m=int(fin["missed_payments_3m"] or 0),
                )
                print(f"  - Fallback PD result: {pd_fin_hat}")
            else:
                print(f"  - No financial data in old format either")
        
        print(f"  - Final pd_fin_hat: {pd_fin_hat}")
        
        # =========================================================
        # INTEGRATION: Call External Scoring API
        # =========================================================
        remote_result = None
        if api_payload:
            # Also add psychometric traits to payload if useful
            # The ddd.py didn't use them, but we can pass them labeled
            for t_name, t_val in traits.items():
                api_payload[f"trait_{t_name}"] = t_val
                
            # Use user_id as end_user_id (convert to string)
            params_user_id = f"user-{user_id}" if user_id else f"anon-{req.assessment_id}"
            
            remote_result = scoring_api.predict_explain(
                input_id=req.assessment_id,
                payload=api_payload,
                end_user_id=params_user_id
            )

        pd_final_hat = scoring.combine_pd(pd_psych_hat, pd_fin_hat)
        
        # If remote result exists, update/overwrite our local calculations
        if remote_result:
            print(f"[Core] Using remote scoring result")
            # Remote provides "score" (0-100 usually) and "probability" (PD)
            if "probability" in remote_result:
                pd_final_hat = remote_result["probability"]
            elif "score" in remote_result:
                # map 0-100 score to PD? Assuming score is good (high), PD is bad (low)
                # This is risky without knowing mapping. Trust "probability" if present.
                pass
                
            # Store explainability data in metadata
            if "groupContributions" in remote_result:
                metadata["remote_explainability"] = remote_result["groupContributions"]
            if "base_value" in remote_result:
                metadata["remote_base_value"] = remote_result["base_value"]
            
            # Store the remote score in metadata too
            metadata["remote_score"] = remote_result.get("score")

        db.upsert_computed(
            assessment_id=req.assessment_id,
            metadata=metadata,
            traits={"trait_final": traits},
            pd_psych_hat=pd_psych_hat,
            pd_fin_hat=pd_fin_hat,
            pd_final_hat=pd_final_hat,
        )

        # #region agent log
        try:
            with open('.cursor/debug.log', 'a', encoding='utf-8') as f:
                f.write(json.dumps({"location": "app.py:334", "message": "final traits stored to database", "data": {"assessment_id": req.assessment_id, "traits": traits, "pd_psych_hat": pd_psych_hat, "pd_fin_hat": pd_fin_hat, "pd_final_hat": pd_final_hat}, "timestamp": int(time.time() * 1000), "sessionId": "debug-session", "runId": "run1", "hypothesisId": "traits_output"}) + "\n")
        except Exception:
            pass
        # #endregion

        db.mark_attempt_completed(req.assessment_id, now_ms())
        return {"ok": True}
    except ValueError as e:
        import traceback
        error_msg = str(e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Scoring error: {error_msg}")
    except Exception as e:
        import traceback
        error_msg = str(e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {error_msg}")


@app.get("/api/result")
def api_result(assessment_id: str) -> Any:
    attempt = db.get_attempt(assessment_id)
    if not attempt:
        raise HTTPException(status_code=404, detail="assessment_id not found")
    comp = db.get_computed(assessment_id)
    if not comp:
        raise HTTPException(status_code=404, detail="result not computed yet")
    return {
        "assessment_id": assessment_id,
        "consent_financial": bool(int(attempt.get("consent_financial") or 0)),
        "trait_final": comp["traits"].get("trait_final") or {},
        "pd_psych_hat": comp.get("pd_psych_hat"),
        "pd_fin_hat": comp.get("pd_fin_hat"),
        "pd_final_hat": comp.get("pd_final_hat"),
        "metadata": comp.get("metadata") or {},
    }


# ============================================================================
# ADMIN DASHBOARD ROUTES
# ============================================================================

def check_admin_access(request: Request) -> bool:
    """
    Simple admin access check.
    For MVP: allows access by default (development mode).
    Set ADMIN_MODE=false to restrict access.
    In production, this should check user role from session/auth.
    """
    # Check environment variable - deny only if explicitly set to "false"
    admin_mode = os.getenv("ADMIN_MODE", "").lower()
    if admin_mode == "false":
        return False
    
    # For MVP: allow access by default (development-friendly)
    # In production, check user role from session/cookie:
    #   user = get_current_user(request)
    #   return user and user.get("role") == "admin"
    return True


@app.get("/admin", response_class=HTMLResponse)
def admin_overview(request: Request) -> Any:
    """Admin dashboard overview page."""
    if not check_admin_access(request):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    status = admin_mock_data.get_overview_status()
    alerts = admin_mock_data.get_alerts(limit=5)
    
    return templates.TemplateResponse(
        "admin/overview.html",
        {
            "request": request,
            "status": status,
            "alerts": alerts,
        },
    )


@app.get("/admin/performance", response_class=HTMLResponse)
def admin_performance(request: Request) -> Any:
    """Admin dashboard performance page."""
    if not check_admin_access(request):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    metrics = admin_mock_data.get_performance_metrics()
    
    return templates.TemplateResponse(
        "admin/performance.html",
        {
            "request": request,
            "metrics": metrics,
        },
    )


@app.get("/admin/drift", response_class=HTMLResponse)
def admin_drift(request: Request) -> Any:
    """Admin dashboard drift page."""
    if not check_admin_access(request):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    drift_data = admin_mock_data.get_drift_data()
    
    return templates.TemplateResponse(
        "admin/drift.html",
        {
            "request": request,
            "drift": drift_data,
        },
    )


@app.get("/admin/uptime", response_class=HTMLResponse)
def admin_uptime(request: Request) -> Any:
    """Admin dashboard uptime page."""
    if not check_admin_access(request):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    uptime_data = admin_mock_data.get_uptime_metrics()
    
    return templates.TemplateResponse(
        "admin/uptime.html",
        {
            "request": request,
            "uptime": uptime_data,
        },
    )


@app.get("/admin/fairness", response_class=HTMLResponse)
def admin_fairness(request: Request) -> Any:
    """Admin dashboard fairness page."""
    if not check_admin_access(request):
        raise HTTPException(status_code=403, detail="Admin access required")
    
    fairness_data = admin_mock_data.get_fairness_metrics()
    
    return templates.TemplateResponse(
        "admin/fairness.html",
        {
            "request": request,
            "fairness": fairness_data,
        },
    )



# ============================================================================
# BANK DASHBOARD MVP ROUTES
# ============================================================================

class BankLoginRequest(BaseModel):
    username: str
    password: str

class NoteRequest(BaseModel):
    category: str
    text: str

@app.get("/bank/login", response_class=HTMLResponse)
def bank_login_page(request: Request) -> Any:
    return templates.TemplateResponse("bank/login.html", {"request": request})

@app.post("/bank/api/login")
def bank_api_login(req: BankLoginRequest) -> Any:
    import hashlib
    user = db.get_user_by_username(req.username)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    password_hash = hashlib.sha256(req.password.encode()).hexdigest()
    if user["password_hash"] != password_hash:
        raise HTTPException(status_code=401, detail="Invalid credentials")
        
    if user.get("role") != "bank_admin":
        raise HTTPException(status_code=403, detail="Unauthorized access")
        
    db.update_last_login(user["id"])
    
    # Generate a simple session token (for MVP, just user_id + hash)
    # In prod, use proper JWT or secure session
    token = f"{user['id']}:{uuid.uuid4().hex}"
    
    return {"ok": True, "token": token, "user": {"id": user["id"], "username": user["username"]}}

@app.get("/bank/portfolio", response_class=HTMLResponse)
def bank_portfolio_page(request: Request) -> Any:
    return templates.TemplateResponse("bank/portfolio.html", {"request": request})

@app.get("/bank/borrowers", response_class=HTMLResponse)
def bank_borrowers_page(request: Request) -> Any:
    return templates.TemplateResponse("bank/borrowers.html", {"request": request})

@app.get("/bank/api/borrowers")
def bank_api_borrowers(
    search: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    limit: int = 50
) -> Any:
    offset = (page - 1) * limit
    items, total = db.get_all_borrowers(search=search, status=status, limit=limit, offset=offset)
    
    # Process items for display
    processed = []
    for item in items:
        # Mask borrower ref/ID if needed, keeping it simple for now
        # Format dates
        created = item.get("started_at_ms")
        processed.append({
            "assessment_id": item.get("assessment_id"),
            "status": item.get("status"),
            "score": item.get("pd_final_hat"),  # This is PD, maybe convert to score?
            "income": item.get("monthly_income"),
            "created_at": time.strftime('%Y-%m-%d %H:%M', time.localtime(created/1000)) if created else "-",
            "user_id": item.get("user_id")
        })
        
    return {
        "items": processed,
        "total": total,
        "page": page,
        "limit": limit
    }

@app.get("/bank/api/borrowers/export.csv")
def bank_export_csv(
    search: Optional[str] = None,
    status: Optional[str] = None
) -> Any:
    from fastapi.responses import StreamingResponse
    import io
    import csv
    
    # Get all items (high limit)
    items, _ = db.get_all_borrowers(search=search, status=status, limit=10000)
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Application ID", "User ID", "Status", "Score (PD)", "Risk Band", "Income", "Created At"])
    
    for item in items:
        # Calculate risk band
        pd = item.get("pd_final_hat")
        risk = "Unknown"
        if pd is not None:
            if pd < 0.05: risk = "Low"
            elif pd < 0.15: risk = "Medium"
            else: risk = "High"
            
        created = item.get("started_at_ms")
        date_str = time.strftime('%Y-%m-%d %H:%M', time.localtime(created/1000)) if created else "-"
        
        writer.writerow([
            item.get("assessment_id"),
            item.get("user_id"),
            item.get("status"),
            pd,
            risk,
            item.get("monthly_income"),
            date_str
        ])
    
    output.seek(0)
    response = StreamingResponse(io.BytesIO(output.getvalue().encode()), media_type="text/csv")
    response.headers["Content-Disposition"] = "attachment; filename=borrowers_export.csv"
    return response

@app.get("/bank/borrowers/{assessment_id}", response_class=HTMLResponse)
def bank_borrower_detail_page(request: Request, assessment_id: str) -> Any:
    return templates.TemplateResponse("bank/borrower_detail.html", {"request": request, "assessment_id": assessment_id})

@app.get("/bank/api/borrowers/{assessment_id}")
def bank_api_borrower_detail(assessment_id: str) -> Any:
    attempt = db.get_attempt(assessment_id)
    if not attempt:
        raise HTTPException(status_code=404, detail="Not found")
        
    comp = db.get_computed(assessment_id)
    fin = db.get_financial(assessment_id)
    notes = db.get_notes(assessment_id)
    
    # Calculate simple drivers
    drivers = []
    if comp and comp.get("traits"):
        traits = comp["traits"].get("trait_final", {})
        # Find top 3 positive (highest) and top 3 negative (lowest) traits
        # "Positive" driver = helps score (high conscientiousness etc)
        # "Negative" driver = hurts score (high impulsivity etc)
        
        # We need to know which traits are "good" when high. 
        # Most FrankScore traits are "higher is better" except:
        # - impulsivity (lower is better)
        # - present_bias (lower is better)
        # But score logic might have already inverted them? 
        # Looking at scoring.py, all traits seem normalized so 1.0 is "best" for the credit score? 
        # "impulsivity" score calculation: (hesitation_good + consistency_good + response_good) / 3.0
        # So YES, the stored trait values are "scores" where 1.0 is good.
        
        sorted_traits = sorted(traits.items(), key=lambda x: x[1], reverse=True)
        
        # Top strengths
        for k, v in sorted_traits[:3]:
            drivers.append({"feature": k, "value": v, "shap": 0.1, "direction": "positive"})
            
        # Top weaknesses (lowest scores)
        for k, v in sorted_traits[-3:]:
             drivers.append({"feature": k, "value": v, "shap": -0.1, "direction": "negative"})

    return {
        "assessment": attempt,
        "score": comp,
        "financial": fin,
        "drivers": drivers,
        "notes": notes
    }

@app.post("/bank/api/borrowers/{assessment_id}/notes")
def bank_api_add_note(assessment_id: str, req: NoteRequest, user_id: int = 1) -> Any: 
    # user_id should come from auth token in real app. For MVP using default admin ID if not passed
    # simpler: just use ID 1 (admin)
    note_id = db.add_note(assessment_id, 1, req.category, req.text)
    return {"ok": True, "id": note_id}



@app.get("/bank/api/portfolio")
def bank_api_portfolio() -> Any:
    # Get all borrowers (simplified for MVP - in prod use DB aggregation)
    items, _ = db.get_all_borrowers(limit=10000)
    
    risk_counts = {"Low": 0, "Medium": 0, "High": 0}
    score_dist = [0] * 10  # 10 buckets for PD 0.0-1.0
    
    for item in items:
        # Check against None explicitly
        score = item.get("pd_final_hat")
        
        # Risk Band Logic
        if score is not None:
            if score < 0.05:
                risk_counts["Low"] += 1
            elif score < 0.15:
                risk_counts["Medium"] += 1
            else:
                risk_counts["High"] += 1
            
            # Bucket Logic (0.00-0.09 -> 0, 0.90-0.99 -> 9)
            bucket = min(int(score * 10), 9)
            score_dist[bucket] += 1
            
    return {
        "risk_distribution": risk_counts,
        "score_distribution": score_dist
    }


# ============================================================================
# EXPLAINABILITY API
# ============================================================================

@app.get("/api/explain/{model_name}/{assessment_id}")
def api_explain(
    model_name: str,
    assessment_id: str,
    method: str = "shap"
) -> Any:
    """
    Get explainability results for a borrower's score.
    
    Args:
        model_name: 'kenya', 'psychometric', 'xgb', or 'random_forest'
        assessment_id: The borrower's assessment ID
        method: 'shap' or 'lime'
        
    Returns:
        JSON with prediction, top_positive, top_negative, meta
    """
    # Get borrower data
    computed = db.get_computed(assessment_id)
    if not computed:
        raise HTTPException(status_code=404, detail="Assessment not found or not scored")
    
    # Build features based on model type
    if model_name in ["kenya", "random_forest"]:
        # Get financial data for Kenya model
        fin = db.get_financial(assessment_id)
        if not fin:
            raise HTTPException(status_code=400, detail="No financial data for Kenya model")
        features = {
            "customer_id": 0,  # Anonymized
            "num_previous_loans": fin.get("num_previous_loans", 0),
            "avg_time_bw_loans": fin.get("avg_time_bw_loans", 0),
            "avg_past_amount": fin.get("avg_past_amount", 0),
            "avg_past_daily_burden": fin.get("avg_past_daily_burden", 0),
            "std_past_amount": fin.get("std_past_amount", 0),
            "std_past_daily_burden": fin.get("std_past_daily_burden", 0),
            "trend_in_amount": fin.get("trend_in_amount", 0),
            "trend_in_burden": fin.get("trend_in_burden", 0),
            "Total_Amount": fin.get("Total_Amount", 0),
            "daily_burden": fin.get("daily_burden", 0),
            "amount_ratio": fin.get("amount_ratio", 0),
            "burden_ratio": fin.get("burden_ratio", 0),
            "amount_bucket": fin.get("amount_bucket", 0),
            "burden_percentile": fin.get("burden_percentile", 0),
        }
    else:
        # Get psychometric traits for psychometric model
        traits = computed.get("traits", {}).get("trait_final", {})
        if not traits:
            raise HTTPException(status_code=400, detail="No trait data for psychometric model")
        features = traits
    
    # Call appropriate explainability service
    if method == "lime":
        from explainability import lime_service
        result = lime_service.explain(model_name, features)
    else:
        from explainability import shap_service
        result = shap_service.explain(model_name, features)
    
    if "error" in result:
        raise HTTPException(status_code=500, detail=result)
    
    return result
