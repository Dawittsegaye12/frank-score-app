
import requests
import json
import sys

# REPLACE THIS WITH YOUR SPACE URL
# Example: "https://dawittsegaye12-frankscore-api.hf.space"
API_URL = "YOUR_HF_SPACE_URL_HERE"

def test_kenya():
    print(f"\nTesting Kenya Model at {API_URL}/predict/kenya...")
    payload = {
        "assessment_id": "TEST_KENYA_001",
        "features": {
            "monthly_income": 5000,
            "monthly_expenses": 2000,
            "total_debt": 500,
            "missed_payments_3m": 0,
            "amount_bucket": "q2"
        }
    }
    try:
        resp = requests.post(f"{API_URL}/predict/kenya", json=payload, timeout=10)
        resp.raise_for_status()
        print("SUCCESS:")
        print(json.dumps(resp.json(), indent=2))
    except Exception as e:
        print(f"FAILED: {e}")
        if hasattr(e, 'response') and e.response:
             print(e.response.text)

def test_psych():
    print(f"\nTesting Psychometric Model at {API_URL}/predict/psych...")
    payload = {
        "assessment_id": "TEST_PSYCH_001",
        "features": {
            "conscientiousness": 0.8,
            "impulsivity": 0.2,
            "financial_self_confidence": 0.7,
            "planning_horizon": 0.9,
            "risk_attitude": 0.5,
            "honesty": 0.9
        }
    }
    try:
        resp = requests.post(f"{API_URL}/predict/psych", json=payload, timeout=10)
        resp.raise_for_status()
        print("SUCCESS:")
        print(json.dumps(resp.json(), indent=2))
    except Exception as e:
        print(f"FAILED: {e}")
        if hasattr(e, 'response') and e.response:
             print(e.response.text)

if __name__ == "__main__":
    if "YOUR_HF_SPACE_URL" in API_URL:
        print("Please edit this script and set API_URL to your Hugging Face Space URL.")
        print("Example: https://huggingface.co/spaces/USERNAME/SPACE_NAME -> https://username-space-name.hf.space")
        
        # Try to read from args
        if len(sys.argv) > 1:
            API_URL = sys.argv[1]
            print(f"Using URL from argument: {API_URL}")
        else:
            sys.exit(1)
            
    test_kenya()
    test_psych()
