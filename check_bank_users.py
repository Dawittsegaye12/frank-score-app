import db
db.init_db()
with db.get_conn() as conn:
    rows = conn.execute("SELECT id, username, role FROM users WHERE role='bank'").fetchall()
    for r in rows:
        print(dict(r))
    if not rows:
        print("No bank users found!")
