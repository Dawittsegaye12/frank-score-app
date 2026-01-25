import os
import time
import uuid
import hmac
import hashlib
import json
import requests
from typing import Optional, Dict, Any, Tuple

# Configuration
# Ideally these should be environment variables, but falling back to defaults for MVP
BASE_URL = os.getenv("SCORING_API_URL", "https://frankscore-backend.onrender.com")
CLIENT_ID = os.getenv("TENANT_CLIENT_ID", "acme-bank-463edc0a")
CLIENT_SECRET = os.getenv("TENANT_CLIENT_SECRET", "yPqsrtBizHgDvnK-NpkgVXMXw3WbV_s_JGK-c2pWr3U")
HMAC_SECRET = os.getenv("TENANT_HMAC_SECRET", "OSSBJgx2QToeQhGtQgzwS_8Kf1QvTraq6M67uNrBKEo")


# Token Cache
_JWT_TOKEN: Optional[str] = None
_TOKEN_EXPIRY: float = 0

def _get_token() -> str:
    """Get a valid JWT token, refreshing if necessary."""
    global _JWT_TOKEN, _TOKEN_EXPIRY
    
    # Return cached token if still valid (with 60s buffer)
    if _JWT_TOKEN and time.time() < (_TOKEN_EXPIRY - 60):
        print(f"[ScoringAPI] Using cached token. Expiry: {_TOKEN_EXPIRY}", flush=True)
        return _JWT_TOKEN
        
    # Login to get new token
    print(f"[ScoringAPI] Logging in to {BASE_URL}...", flush=True)
    try:
        resp = requests.post(
            f"{BASE_URL}/auth/login",
            json={
                "clientId": CLIENT_ID,
                "clientSecret": CLIENT_SECRET
            },
            timeout=30 # Increased timeout
        )
        if resp.status_code != 200:
            print(f"[ScoringAPI] Login failed with status {resp.status_code}: {resp.text}", flush=True)
            resp.raise_for_status()
            
        data = resp.json()
        
        _JWT_TOKEN = data["accessToken"] if "accessToken" in data else data.get("access_token")
        
        # Default expiry 600s if not provided
        expires_in = data.get("expiresIn", 600)
        _TOKEN_EXPIRY = time.time() + expires_in
        
        print(f"[ScoringAPI] Login successful. Token expires in {expires_in}s", flush=True)
        return _JWT_TOKEN
        
    except Exception as e:
        print(f"[ScoringAPI] Login EXCEPTION: {e}", flush=True)
        raise

def predict_explain(
    input_id: str,
    payload: Dict[str, Any],
    end_user_id: str
) -> Dict[str, Any]:
    """
    Call the /v1/predict_explain endpoint.
    
    Args:
        input_id: Unique identifier for this prediction request (e.g. assessment_id)
        payload: Dictionary of features (financial data, etc.)
        end_user_id: Unique identifier for the end user
        
    Returns:
        Dictionary containing prediction results (score, probability, etc.)
    """
    try:
        token = _get_token()
        
        timestamp = str(int(time.time()))
        request_id = str(uuid.uuid4())
        
        # Compute HMAC Signature
        signing_string = f"{end_user_id}|{timestamp}|{request_id}"
        signature = hmac.new(
            HMAC_SECRET.encode('utf-8'),
            signing_string.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "X-End-User-Id": end_user_id,
            "X-End-User-Timestamp": timestamp,
            "X-Request-Id": request_id,
            "X-End-User-Signature": signature
        }
        
        body = {
            "inputId": input_id,
            "payload": payload
        }
        
        print(f"[ScoringAPI] Requesting prediction for {input_id}...", flush=True)
        resp = requests.post(
            f"{BASE_URL}/v1/predict_explain",
            headers=headers,
            json=body,
            timeout=30
        )
        
        if resp.status_code != 200:
            print(f"[ScoringAPI] Request failed: {resp.status_code} {resp.text}", flush=True)
            # Try to refresh token once if 401
            if resp.status_code == 401:
                print("[ScoringAPI] Token might be expired, retrying...", flush=True)
                global _JWT_TOKEN
                _JWT_TOKEN = None # Force refresh
                token = _get_token()
                headers["Authorization"] = f"Bearer {token}"
                resp = requests.post(
                    f"{BASE_URL}/v1/predict_explain",
                    headers=headers,
                    json=body,
                    timeout=30
                )
                if resp.status_code != 200:
                    resp.raise_for_status()
            else:
                resp.raise_for_status()
                
        result = resp.json()
        print(f"[ScoringAPI] Prediction successful. Score: {result.get('score')}", flush=True)
        return result
        
    except Exception as e:
        print(f"[ScoringAPI] Error during prediction: {str(e)}", flush=True)
        # Return simplified error structure or raise
        # For robustness, we might want to return None so the app can fallback
        return None
