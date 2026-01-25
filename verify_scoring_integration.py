import db
import app
import time
import json
import uuid

def verify_integration():
    print("Setting up test data...")
    db.init_db()
    
    # 1. Create a User with Financial Data
    username = f"test_user_{uuid.uuid4().hex[:6]}"
    user_id = db.create_user(username, "hash", "email@test.com")
    print(f"Created user: {username} (ID: {user_id})")
    
    # Insert Financial Data (matching ddd.py payload)
    fin_data = {
        "customer_id": f"cust_{user_id}",
        "num_previous_loans": 9,
        "Total_Amount": 30000,
        "daily_burden": 1500,
        "account_age_days": 150,
        # Add a few others to be safe
        "month": 1,
        "quarter": 1
    }
    db.upsert_financial_data(user_id, fin_data)
    print("Inserted financial data.")
    
    # 2. Create an Attempt
    assessment_id = f"FS_TEST_{uuid.uuid4().hex[:6]}"
    session_id = uuid.uuid4().hex
    db.insert_attempt(
        assessment_id=assessment_id,
        user_id=user_id,
        session_id=session_id,
        status="in_progress",
        started_at_ms=int(time.time() * 1000)
    )
    print(f"Created attempt: {assessment_id}")
    
    # 3. Insert some responses (mocking usage)
    # Just insert one response so compute_traits doesn't crash
    db.insert_response(
        assessment_id=assessment_id,
        item_id="Q1",
        selected_option="A",
        answered_at_ms=int(time.time() * 1000)
    )
    
    # 4. Call api_complete
    print("Calling api_complete...")
    req = app.CompleteRequest(assessment_id=assessment_id)
    try:
        app.api_complete(req)
        print("api_complete returned successfully.")
    except Exception as e:
        print(f"api_complete FAILED: {e}")
        import traceback
        traceback.print_exc()
        return

    # 5. Verify Computed Results
    print("Verifying results in DB...")
    comp = db.get_computed(assessment_id)
    if not comp:
        print("ERROR: No computed record found!")
        return
        
    metadata = comp.get("metadata", {})
    print(f"Metadata keys: {metadata.keys()}")
    
    if "remote_score" in metadata:
        print(f"SUCCESS! Found remote_score: {metadata['remote_score']}")
    else:
        print("FAILURE: remote_score NOT found in metadata.")
        
    if "remote_explainability" in metadata:
        print(f"SUCCESS! Found remote_explainability (count: {len(metadata['remote_explainability'])})")
    else:
        print("FAILURE: remote_explainability NOT found in metadata.")

if __name__ == "__main__":
    verify_integration()
