import db
import hashlib
import time

def seed_sarah():
    db.init_db()
    
    username = "sarah_bank"
    password = "password123"
    email = "sarah@frankscore.bank"
    
    # Check if exists
    user = db.get_user_by_username(username)
    if user:
        print(f"User {username} already exists.")
    else:
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        user_id = db.create_bank_user(username, password_hash, email)
        print(f"Created bank user: {username} (ID: {user_id})")
        
    # Also ensure there's some borrower data for her to look at
    # create a completed attempt if not exists
    assessment_id = "FS_DEMO_001"
    if not db.get_attempt(assessment_id):
        print(f"Seeding demo borrower {assessment_id}...")
        db.insert_attempt(
            assessment_id=assessment_id,
            user_id=None, # Anonymous for now
            session_id="session_demo_1",
            status="completed",
            started_at_ms=int(time.time() * 1000) - 86400000 # 1 day ago
        )
        # Add some score
        db.upsert_computed(
            assessment_id=assessment_id,
            metadata={},
            traits={"trait_final": {"conscientiousness": 0.8, "impulsivity": 0.2, "honesty": 0.9}},
            pd_psych_hat=0.12,
            pd_fin_hat=0.08,
            pd_final_hat=0.10
        )
        db.mark_attempt_completed(assessment_id, int(time.time() * 1000))
        print("Demo borrower seeded.")

if __name__ == "__main__":
    seed_sarah()
