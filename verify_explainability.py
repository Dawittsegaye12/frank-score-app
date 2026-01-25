"""
Verification script for Explainability Module (SHAP + LIME)
"""
import urllib.request
import urllib.error
import json

BASE_URL = "http://127.0.0.1:8000"

def log(msg, status="INFO"):
    print(f"[{status}] {msg}")

def request(method, url):
    try:
        req = urllib.request.Request(url, method=method)
        res = urllib.request.urlopen(req)
        return res.status, res.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8')
    except Exception as e:
        return 0, str(e)

def test_explainability():
    # First get a valid assessment_id
    log("Getting borrower list...")
    status, body = request("GET", f"{BASE_URL}/bank/api/borrowers")
    if status != 200:
        log(f"Failed to get borrowers: {status}", "FAIL")
        return
    
    data = json.loads(body)
    if not data.get("items"):
        log("No borrowers found", "FAIL")
        return
    
    assessment_id = data["items"][0]["assessment_id"]
    log(f"Using assessment: {assessment_id}")
    
    # Test SHAP endpoint
    log("Testing SHAP (psychometric)...")
    status, body = request("GET", f"{BASE_URL}/api/explain/psychometric/{assessment_id}?method=shap")
    if status == 200:
        result = json.loads(body)
        if "top_positive" in result and "top_negative" in result:
            log(f"SHAP OK - Prediction: {result.get('prediction')}", "PASS")
        else:
            log(f"SHAP returned unexpected format: {body[:200]}", "WARN")
    else:
        log(f"SHAP failed: {status} {body[:200]}", "FAIL")
    
    # Test LIME endpoint
    log("Testing LIME (psychometric)...")
    status, body = request("GET", f"{BASE_URL}/api/explain/psychometric/{assessment_id}?method=lime")
    if status == 200:
        result = json.loads(body)
        if "top_positive" in result or "top_negative" in result:
            log(f"LIME OK - Prediction: {result.get('prediction')}", "PASS")
        else:
            log(f"LIME returned unexpected format: {body[:200]}", "WARN")
    else:
        log(f"LIME failed: {status} {body[:200]}", "FAIL")
    
    log("Explainability verification complete.")

if __name__ == "__main__":
    test_explainability()
