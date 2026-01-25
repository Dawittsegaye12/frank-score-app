this code is implemented for test 
so you can use it may be to get clear understanding

#!/usr/bin/env python3
"""
Test script for /v1/predict endpoint.

This script demonstrates the correct request format:
- inputId: required string
- payload: object containing the feature data
"""

import hmac
import hashlib
import time
import uuid
import requests

# ============================================
# CONFIGURATION (from tenant creation)
# ============================================
CLIENT_ID = "acme-bank-463edc0a"
# CLIENT_ID = "acme-bank2-4221daf8"
CLIENT_SECRET = "yPqsrtBizHgDvnK-NpkgVXMXw3WbV_s_JGK-c2pWr3U"
# CLIENT_SECRET = "j5k48wXLoVbRFfb1oY2mDUIq7JjgqMeCvsQ6KOWX03k"
HMAC_SECRET = "OSSBJgx2QToeQhGtQgzwS_8Kf1QvTraq6M67uNrBKEo"
# HMAC_SECRET = "GVY_hCGZm927NX15PbWD2FwexNQEHaT3Bw5hXfvRpXY"

BASE_URL = "https://frankscore-backend.onrender.com"
# BASE_URL = "http://localhost:8080"

# ============================================
# STEP 1: Login as Tenant
# ============================================
print("Step 1: Logging in...")
login_response = requests.post(
    f"{BASE_URL}/auth/login",
    json={
        "clientId": CLIENT_ID,
        "clientSecret": CLIENT_SECRET
    }
)

if login_response.status_code != 200:
    print(f"❌ Login failed: {login_response.status_code}")
    print(login_response.text)
    exit(1)

login_data = login_response.json()
jwt_token = login_data["access_token"]  # Note: camelCase, not snake_case
print(f"✅ Logged in. JWT: {jwt_token[:20]}...")

# ============================================
# STEP 2: Prepare End-User Identity
# ============================================
end_user_id = "user-alice-123"  # Your customer
timestamp = str(int(time.time()))
request_id = str(uuid.uuid4())

# ============================================
# STEP 3: Compute HMAC Signature
# ============================================
signing_string = f"{end_user_id}|{timestamp}|{request_id}"
signature = hmac.new(
    HMAC_SECRET.encode('utf-8'),      # SECRET KEY (never sent!)
    signing_string.encode('utf-8'),
    hashlib.sha256
).hexdigest()

print(f"📝 Signing string: {signing_string}")
print(f"🔐 Signature: {signature[:20]}...")

# ============================================
# STEP 4: Make Prediction Request
# ============================================
print("\nStep 4: Making prediction request...")

# IMPORTANT: The request format is:
# {
#   "inputId": "string",  # REQUIRED
#   "payload": { ... }    # The features go here
# }

request_body = {
    "inputId": "loan-app-78945",  # REQUIRED - unique identifier for this request
    "payload": {
      "num_previous_loans": 9,
      "num_previous_defaults": 4,
      "past_default_rate": 0.44,
      "days_since_last_loan": 2,
      "avg_time_bw_loans": 20,
      "avg_past_amount": 26000,
      "avg_past_daily_burden": 950,
      "std_past_amount": 4000,
      "std_past_daily_burden": 180,
      "trend_in_amount": 1.3,
      "trend_in_burden": 1.35,
      "Total_Amount": 30000,
      "Total_Amount_to_Repay": 36000,
      "duration": 20,
      "daily_burden": 1500,
      "amount_ratio": 2.0,
      "burden_ratio": 1.8,
      "duration_bucket": "20",
      "amount_bucket": "high",
      "burden_percentile": 0.95,
      "borrower_history_strength": "weak",
      "month": 1,
      "quarter": 1,
      "week_of_year": 3,
      "days_to_salary_day": 28,
      "days_to_local_festival": 2,
      "lender_id": "L_high3",
      "lender_exposure_ratio": 0.4,
      "account_age_days": 150,
      "loan_frequency_per_year": 12,
      "repayment_consistency": 0.4,
      "latest_amount_ma3": 28000
    }
}

response = requests.post(
    f"{BASE_URL}/v1/predict_explain",
    headers={
        "Authorization": f"Bearer {jwt_token}",
        "Content-Type": "application/json",
        "X-End-User-Id": end_user_id,
        "X-End-User-Timestamp": timestamp,
        "X-Request-Id": request_id,
        "X-End-User-Signature": signature
    },
    json=request_body
)

print(f"\nResponse Status: {response.status_code}")

if response.status_code == 200:
    result = response.json()
    print("✅ Prediction successful!")
    print(f"   Input ID: {result.get('inputId')}")
    print(f"   Score: {result.get('score')}")
    if result.get('topFeatures'):
        print(f"   Top Features: {len(result.get('topFeatures'))} features")
    print(f"\nFull response: {result}")
else:
    print(f"❌ Prediction failed: {response.status_code}")
    print(response.text)