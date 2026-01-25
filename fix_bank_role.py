import db
db.init_db()
with db.get_conn() as conn:
    conn.execute("UPDATE users SET role='bank_admin' WHERE username IN ('bankadmin', 'sarah_bank')")
    print("Updated roles to bank_admin")
    
    # Verify
    rows = conn.execute("SELECT id, username, role FROM users WHERE username IN ('bankadmin', 'sarah_bank')").fetchall()
    for r in rows:
        print(f"  {r['username']}: role={r['role']}")
