"""
Debug script to check why financial PD is null.
Run this to check the database state.
"""
import db

def check_financial_pd_issue(assessment_id: str = "FS000004"):
    """Check why financial PD might be null for an assessment."""
    print(f"Checking financial PD for assessment: {assessment_id}")
    print("=" * 60)
    
    # Check attempt record
    attempt = db.get_attempt(assessment_id)
    if not attempt:
        print(f"ERROR: Assessment {assessment_id} not found!")
        return
    
    print(f"\n1. Attempt Record:")
    print(f"   assessment_id: {attempt.get('assessment_id')}")
    print(f"   user_id: {attempt.get('user_id')}")
    print(f"   status: {attempt.get('status')}")
    
    user_id = attempt.get("user_id")
    
    if user_id:
        print(f"\n2. User Financial Data:")
        financial_data = db.get_financial_data(user_id)
        if financial_data:
            print(f"   [OK] Financial data found for user_id {user_id}")
            print(f"   Sample fields:")
            for key in list(financial_data.keys())[:5]:
                print(f"     {key}: {financial_data.get(key)}")
        else:
            print(f"   [ERROR] No financial data found for user_id {user_id}")
    else:
        print(f"\n2. User Financial Data:")
        print(f"   [ERROR] No user_id in attempt record - cannot retrieve financial data")
    
    # Check old financial table
    print(f"\n3. Old Financial Table:")
    fin = db.get_financial(assessment_id)
    if fin:
        print(f"   [OK] Financial data found in old format")
        print(f"     monthly_income: {fin.get('monthly_income')}")
        print(f"     monthly_expenses: {fin.get('monthly_expenses')}")
    else:
        print(f"   [ERROR] No financial data in old format")
    
    # Check computed results
    print(f"\n4. Computed Results:")
    comp = db.get_computed(assessment_id)
    if comp:
        print(f"   pd_psych_hat: {comp.get('pd_psych_hat')}")
        print(f"   pd_fin_hat: {comp.get('pd_fin_hat')}")
        print(f"   pd_final_hat: {comp.get('pd_final_hat')}")
    else:
        print(f"   [ERROR] No computed results found")
    
    print("\n" + "=" * 60)
    print("\nDiagnosis:")
    if not user_id:
        print("  → Issue: user_id is None in attempt record")
        print("  → Solution: Make sure user logs in before starting assessment")
    elif not financial_data:
        print("  → Issue: No financial data for user_id")
        print("  → Solution: Run seed_personas.py to create personas with financial data")
    else:
        print("  → Financial data exists, but model might be failing")
        print("  → Check server logs for model prediction errors")

if __name__ == "__main__":
    import sys
    assessment_id = sys.argv[1] if len(sys.argv) > 1 else "FS000004"
    check_financial_pd_issue(assessment_id)

