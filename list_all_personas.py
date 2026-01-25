"""
List all personas with their financial data and PD calculations.
"""
import db
import scoring

# Load models
scoring.load_rf_model()

print("=" * 80)
print("ALL PERSONAS - Financial Data and PD")
print("=" * 80)

# Get all users
with db.get_conn() as conn:
    users = conn.execute("SELECT id, username, email FROM users ORDER BY id").fetchall()

if not users:
    print("\nNo personas found. Run seed_personas.py first.")
    exit(0)

print(f"\nTotal personas: {len(users)}\n")

for user in users:
    user_id, username, email = user
    print("-" * 80)
    print(f"Persona: {username} (ID: {user_id})")
    if email:
        print(f"Email: {email}")
    
    # Get financial data
    financial_data = db.get_financial_data(user_id)
    if not financial_data:
        print("[ERROR] No financial data found")
        print()
        continue
    
    # Key financial metrics
    print("\nFinancial Profile:")
    print(f"  Customer ID: {financial_data.get('customer_id', 'N/A')}")
    print(f"  Previous Loans: {financial_data.get('num_previous_loans', 0) or 0}")
    print(f"  Total Amount: {financial_data.get('Total_Amount', 0) or 0:,.2f}")
    print(f"  Daily Burden: {financial_data.get('daily_burden', 0) or 0:,.2f}")
    print(f"  Amount Ratio: {financial_data.get('amount_ratio', 0) or 0:.4f}")
    print(f"  Burden Ratio: {financial_data.get('burden_ratio', 0) or 0:.4f}")
    print(f"  Burden Percentile: {financial_data.get('burden_percentile', 0) or 0:.4f}")
    print(f"  Borrower History Strength: {financial_data.get('borrower_history_strength', 0) or 0:.4f}")
    print(f"  Account Age (days): {financial_data.get('account_age_days', 0) or 0}")
    
    # Calculate PD
    print("\nProbability of Default:")
    pd_fin_hat = scoring.financial_pd_from_model(financial_data)
    
    if pd_fin_hat is not None:
        print(f"  Model Prediction: {pd_fin_hat:.4f} ({pd_fin_hat*100:.2f}%)")
        if pd_fin_hat < 0.3:
            risk_level = "LOW RISK"
        elif pd_fin_hat < 0.6:
            risk_level = "MEDIUM RISK"
        else:
            risk_level = "HIGH RISK"
        print(f"  Risk Level: {risk_level}")
    else:
        # Fallback calculation
        total_amount = financial_data.get("Total_Amount", 0) or 0
        daily_burden = financial_data.get("daily_burden", 0) or 0
        num_loans = financial_data.get("num_previous_loans", 0) or 0
        
        if total_amount > 0 and daily_burden > 0:
            burden_ratio = daily_burden / (total_amount / 30) if total_amount > 0 else 0
            pd_fin_hat = min(1.0, max(0.0, burden_ratio * 0.3 + (1 - min(1.0, num_loans / 10)) * 0.2))
            print(f"  Fallback Calculation: {pd_fin_hat:.4f} ({pd_fin_hat*100:.2f}%)")
            if pd_fin_hat < 0.3:
                risk_level = "LOW RISK"
            elif pd_fin_hat < 0.6:
                risk_level = "MEDIUM RISK"
            else:
                risk_level = "HIGH RISK"
            print(f"  Risk Level: {risk_level} (using fallback)")
        else:
            print("  [ERROR] Cannot calculate PD - missing data")
    
    print()

print("=" * 80)
print("\nSummary by Risk Category:")
print("-" * 80)

# Categorize personas
low_risk = []
medium_risk = []
high_risk = []

for user in users:
    user_id = user[0]
    username = user[1]
    financial_data = db.get_financial_data(user_id)
    
    if not financial_data:
        continue
    
    # Calculate PD
    pd_fin_hat = scoring.financial_pd_from_model(financial_data)
    
    if pd_fin_hat is None:
        # Fallback
        total_amount = financial_data.get("Total_Amount", 0) or 0
        daily_burden = financial_data.get("daily_burden", 0) or 0
        num_loans = financial_data.get("num_previous_loans", 0) or 0
        
        if total_amount > 0 and daily_burden > 0:
            burden_ratio = daily_burden / (total_amount / 30) if total_amount > 0 else 0
            pd_fin_hat = min(1.0, max(0.0, burden_ratio * 0.3 + (1 - min(1.0, num_loans / 10)) * 0.2))
        else:
            continue
    
    if pd_fin_hat < 0.3:
        low_risk.append((username, pd_fin_hat))
    elif pd_fin_hat < 0.6:
        medium_risk.append((username, pd_fin_hat))
    else:
        high_risk.append((username, pd_fin_hat))

print(f"\nLOW RISK (PD < 0.3): {len(low_risk)} personas")
for username, pd in sorted(low_risk, key=lambda x: x[1]):
    print(f"  - {username}: {pd:.4f} ({pd*100:.2f}%)")

print(f"\nMEDIUM RISK (0.3 <= PD < 0.6): {len(medium_risk)} personas")
for username, pd in sorted(medium_risk, key=lambda x: x[1]):
    print(f"  - {username}: {pd:.4f} ({pd*100:.2f}%)")

print(f"\nHIGH RISK (PD >= 0.6): {len(high_risk)} personas")
for username, pd in sorted(high_risk, key=lambda x: x[1]):
    print(f"  - {username}: {pd:.4f} ({pd*100:.2f}%)")

print("\n" + "=" * 80)
print("\nLogin Credentials:")
print("  All personas use password: password123")
print("=" * 80)




