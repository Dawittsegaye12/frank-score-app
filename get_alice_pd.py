"""
Get Alice's financial probability of default.
"""
import db
import scoring

# Load models
scoring.load_rf_model()

# Get Alice's user_id (username: alice)
alice_user = db.get_user_by_username("alice")
if not alice_user:
    print("ERROR: Alice user not found. Run seed_personas.py first.")
    exit(1)

user_id = alice_user["id"]
print(f"Alice's user_id: {user_id}")
print("=" * 60)

# Get financial data
financial_data = db.get_financial_data(user_id)
if not financial_data:
    print("ERROR: No financial data found for Alice.")
    exit(1)

print("\nAlice's Financial Data (sample):")
for key in ["customer_id", "num_previous_loans", "Total_Amount", "daily_burden", 
            "amount_ratio", "burden_ratio", "borrower_history_strength"]:
    print(f"  {key}: {financial_data.get(key)}")

print("\n" + "=" * 60)
print("\nCalculating Financial PD...")

# Try model prediction
pd_fin_hat = scoring.financial_pd_from_model(financial_data)

if pd_fin_hat is not None:
    print(f"\n[OK] Model Prediction: {pd_fin_hat:.4f}")
    print(f"  (Using Random Forest model)")
else:
    print("\n[WARN] Model prediction failed (version incompatibility)")
    print("  Using fallback calculation...")
    
    # Fallback calculation
    total_amount = financial_data.get("Total_Amount", 0) or 0
    daily_burden = financial_data.get("daily_burden", 0) or 0
    num_loans = financial_data.get("num_previous_loans", 0) or 0
    
    if total_amount > 0 and daily_burden > 0:
        burden_ratio = daily_burden / (total_amount / 30) if total_amount > 0 else 0
        pd_fin_hat = min(1.0, max(0.0, burden_ratio * 0.3 + (1 - min(1.0, num_loans / 10)) * 0.2))
        print(f"\n[OK] Fallback Calculation: {pd_fin_hat:.4f}")
        print(f"  (Using heuristic: burden_ratio={burden_ratio:.4f}, num_loans={num_loans})")
    else:
        print("\n[ERROR] Cannot calculate: missing financial data")

print("\n" + "=" * 60)
if pd_fin_hat is not None:
    print(f"\nAlice's Financial Probability of Default: {pd_fin_hat:.4f}")
    print(f"\nInterpretation:")
    if pd_fin_hat < 0.3:
        print("  - LOW RISK (PD < 0.3)")
    elif pd_fin_hat < 0.6:
        print("  - MEDIUM RISK (0.3 <= PD < 0.6)")
    else:
        print("  - HIGH RISK (PD >= 0.6)")
else:
    print("\nAlice's Financial Probability of Default: N/A (calculation failed)")

