"""
Seed the database with imaginary personas and their financial data.
This script creates users with pre-populated financial data matching the CSV structure.
"""
import random
import time
import hashlib
import db

# Feature columns needed by the Random Forest model
FEATURE_COLUMNS = [
    "num_previous_loans", "avg_time_bw_loans", "avg_past_amount",
    "avg_past_daily_burden", "std_past_amount", "std_past_daily_burden",
    "trend_in_amount", "trend_in_burden", "Total_Amount", "daily_burden",
    "amount_ratio", "burden_ratio", "amount_bucket", "burden_percentile",
    "borrower_history_strength", "month", "quarter", "week_of_year",
    "days_to_salary_day", "days_to_local_festival", "account_age_days",
    "loan_frequency_per_year", "latest_amount_ma3"
]


def generate_password_hash(password: str) -> str:
    """Simple password hashing (for demo purposes). In production, use bcrypt or similar."""
    return hashlib.sha256(password.encode()).hexdigest()


def generate_persona_data(persona_type: str) -> dict:
    """
    Generate financial data for different persona types.
    Returns a dictionary with all required features.
    """
    base_data = {
        "customer_id": f"PERSONA_{random.randint(100000, 999999)}",
        "month": random.randint(1, 12),
        "quarter": random.randint(1, 4),
        "week_of_year": random.randint(1, 52),
        "days_to_salary_day": random.randint(0, 30),
        "days_to_local_festival": random.randint(0, 90),
        "account_age_days": random.randint(30, 3650),  # 1 month to 10 years
    }
    
    if persona_type == "low_risk":
        # Low risk: good history, low burden, consistent payments
        base_data.update({
            "num_previous_loans": random.randint(3, 10),
            "avg_time_bw_loans": random.uniform(60, 180),  # 2-6 months
            "avg_past_amount": random.uniform(10000, 50000),
            "avg_past_daily_burden": random.uniform(500, 2000),
            "std_past_amount": random.uniform(1000, 5000),
            "std_past_daily_burden": random.uniform(50, 200),
            "trend_in_amount": random.uniform(-5000, 5000),  # Stable
            "trend_in_burden": random.uniform(-200, 200),
            "Total_Amount": random.uniform(15000, 60000),
            "daily_burden": random.uniform(600, 2500),
            "amount_ratio": random.uniform(0.8, 1.5),
            "burden_ratio": random.uniform(0.8, 1.5),
            "amount_bucket": random.choice(["q2", "q3"]),
            "burden_percentile": random.uniform(0.2, 0.6),
            "borrower_history_strength": random.uniform(0.6, 1.0),
            "loan_frequency_per_year": random.uniform(2, 6),
            "latest_amount_ma3": random.uniform(12000, 55000),
        })
    
    elif persona_type == "medium_risk":
        # Medium risk: moderate history, some variability
        base_data.update({
            "num_previous_loans": random.randint(1, 5),
            "avg_time_bw_loans": random.uniform(30, 120),
            "avg_past_amount": random.uniform(20000, 80000),
            "avg_past_daily_burden": random.uniform(1500, 4000),
            "std_past_amount": random.uniform(5000, 15000),
            "std_past_daily_burden": random.uniform(200, 600),
            "trend_in_amount": random.uniform(-10000, 10000),
            "trend_in_burden": random.uniform(-500, 500),
            "Total_Amount": random.uniform(25000, 90000),
            "daily_burden": random.uniform(2000, 5000),
            "amount_ratio": random.uniform(0.5, 2.0),
            "burden_ratio": random.uniform(0.5, 2.0),
            "amount_bucket": random.choice(["q2", "q3", "q4"]),
            "burden_percentile": random.uniform(0.4, 0.8),
            "borrower_history_strength": random.uniform(0.3, 0.7),
            "loan_frequency_per_year": random.uniform(3, 8),
            "latest_amount_ma3": random.uniform(20000, 85000),
        })
    
    elif persona_type == "high_risk":
        # High risk: poor history, high burden, inconsistent
        base_data.update({
            "num_previous_loans": random.randint(0, 3),
            "avg_time_bw_loans": random.uniform(10, 60) if random.random() > 0.3 else None,
            "avg_past_amount": random.uniform(5000, 30000) if random.random() > 0.2 else None,
            "avg_past_daily_burden": random.uniform(2000, 6000) if random.random() > 0.2 else None,
            "std_past_amount": random.uniform(3000, 20000) if random.random() > 0.3 else None,
            "std_past_daily_burden": random.uniform(300, 1000) if random.random() > 0.3 else None,
            "trend_in_amount": random.uniform(-20000, 5000),
            "trend_in_burden": random.uniform(-1000, 200),
            "Total_Amount": random.uniform(10000, 50000),
            "daily_burden": random.uniform(3000, 8000),
            "amount_ratio": random.uniform(1.5, 4.0),
            "burden_ratio": random.uniform(1.5, 4.0),
            "amount_bucket": random.choice(["q3", "q4"]),
            "burden_percentile": random.uniform(0.7, 1.0),
            "borrower_history_strength": random.uniform(0.0, 0.4),
            "loan_frequency_per_year": random.uniform(4, 12),
            "latest_amount_ma3": random.uniform(8000, 45000) if random.random() > 0.2 else None,
        })
    
    else:  # new_user
        # New user: no history
        base_data.update({
            "num_previous_loans": 0,
            "avg_time_bw_loans": None,
            "avg_past_amount": None,
            "avg_past_daily_burden": None,
            "std_past_amount": None,
            "std_past_daily_burden": None,
            "trend_in_amount": None,
            "trend_in_burden": None,
            "Total_Amount": random.uniform(10000, 50000),
            "daily_burden": random.uniform(1000, 4000),
            "amount_ratio": 1.0,
            "burden_ratio": 1.0,
            "amount_bucket": random.choice(["q2", "q3"]),
            "burden_percentile": random.uniform(0.3, 0.7),
            "borrower_history_strength": 0.0,
            "loan_frequency_per_year": 0.0,
            "latest_amount_ma3": None,
        })
    
    return base_data


def seed_personas():
    """Seed the database with personas."""
    print("Seeding personas...")
    
    personas = [
        # Low risk personas
        ("alice", "password123", "alice@example.com", "low_risk"),
        ("bob", "password123", "bob@example.com", "low_risk"),
        ("charlie", "password123", "charlie@example.com", "low_risk"),
        
        # Medium risk personas
        ("diana", "password123", "diana@example.com", "medium_risk"),
        ("eve", "password123", "eve@example.com", "medium_risk"),
        ("frank", "password123", "frank@example.com", "medium_risk"),
        
        # High risk personas
        ("grace", "password123", "grace@example.com", "high_risk"),
        ("henry", "password123", "henry@example.com", "high_risk"),
        ("ivy", "password123", "ivy@example.com", "high_risk"),
        
        # New users
        ("john", "password123", "john@example.com", "new_user"),
        ("jane", "password123", "jane@example.com", "new_user"),
    ]
    
    created_count = 0
    for username, password, email, persona_type in personas:
        # Check if user already exists
        existing = db.get_user_by_username(username)
        if existing:
            print(f"  User '{username}' already exists, skipping...")
            continue
        
        # Create user
        password_hash = generate_password_hash(password)
        user_id = db.create_user(username, password_hash, email)
        
        # Generate and store financial data
        financial_data = generate_persona_data(persona_type)
        db.upsert_financial_data(user_id, financial_data)
        
        print(f"  Created user '{username}' (ID: {user_id}, Type: {persona_type})")
        created_count += 1
    
    print(f"\nSeeding complete! Created {created_count} personas.")
    print("\nLogin credentials (all use 'password123'):")
    for username, _, _, persona_type in personas:
        print(f"  - {username} ({persona_type})")


if __name__ == "__main__":
    db.init_db()
    seed_personas()

