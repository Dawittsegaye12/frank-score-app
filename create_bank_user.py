import db
import hashlib

db.init_db()

# Create bank admin user
username = "bankadmin"
password = "password123"
password_hash = hashlib.sha256(password.encode()).hexdigest()

with db.get_conn() as conn:
    # Check if exists
    existing = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
    if existing:
        print(f"User '{username}' already exists with id {existing['id']}")
    else:
        conn.execute(
            "INSERT INTO users (username, password_hash, email, role, created_at_ms, last_login_ms) VALUES (?, ?, ?, ?, ?, ?)",
            (username, password_hash, "bank@frankscore.com", "bank", 0, 0)
        )
        print(f"Created bank user: {username} / {password}")

# Also create sarah_bank if you prefer
username2 = "sarah_bank"
with db.get_conn() as conn:
    existing = conn.execute("SELECT id FROM users WHERE username = ?", (username2,)).fetchone()
    if existing:
        print(f"User '{username2}' already exists")
    else:
        conn.execute(
            "INSERT INTO users (username, password_hash, email, role, created_at_ms, last_login_ms) VALUES (?, ?, ?, ?, ?, ?)",
            (username2, password_hash, "sarah@frankscore.com", "bank", 0, 0)
        )
        print(f"Created bank user: {username2} / {password}")

print("\nBank users now:")
with db.get_conn() as conn:
    rows = conn.execute("SELECT id, username, role FROM users WHERE role='bank'").fetchall()
    for r in rows:
        print(f"  - {r['username']} (id: {r['id']})")
