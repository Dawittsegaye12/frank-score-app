import db
import hashlib

def seed():
    db.init_db()
    
    username = "bank_admin"
    password = "password123"
    email = "admin@frankscore.com"
    
    # internal hash logic from app.py/db.py
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    user = db.get_user_by_username(username)
    if user:
        print(f"User {username} already exists.")
        return

    user_id = db.create_bank_user(username, password_hash, email)
    print(f"Created bank user: {username} (ID: {user_id})")

if __name__ == "__main__":
    seed()
