import json
import os
import sqlite3
import time
from contextlib import contextmanager
from typing import Any, Dict, Iterable, List, Optional, Tuple

# Use /tmp on Vercel (writable), current directory locally
# Check multiple indicators that we're on Vercel
is_vercel = (
    os.environ.get("VERCEL") == "1" or
    os.environ.get("VERCEL_ENV") is not None or
    (os.path.exists("/tmp") and os.access("/tmp", os.W_OK))
)

if is_vercel:
    # On Vercel, use /tmp directory (writable)
    DB_PATH = "/tmp/frankscore_demo.db"
else:
    # Local development
    DB_PATH = "frankscore_demo.db"


def _connect() -> sqlite3.Connection:
    # Ensure directory exists (for /tmp, it always exists, but be safe)
    db_dir = os.path.dirname(DB_PATH)
    if db_dir and not os.path.exists(db_dir):
        os.makedirs(db_dir, exist_ok=True)
    
    # Log database path for debugging
    try:
        log_path = ".cursor/debug.log"
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "location": "db.py:_connect",
                "message": "Connecting to database",
                "data": {"db_path": DB_PATH, "vercel": os.environ.get("VERCEL"), "tmp_exists": os.path.exists("/tmp")},
                "timestamp": int(time.time() * 1000),
                "sessionId": "debug-session",
                "runId": "run1",
                "hypothesisId": "H11"
            }) + "\n")
    except Exception:
        pass  # Fail silently if logging fails
    
    try:
        conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn
    except Exception as e:
        # Log connection error
        try:
            log_path = ".cursor/debug.log"
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            with open(log_path, "a", encoding="utf-8") as f:
                f.write(json.dumps({
                    "location": "db.py:_connect",
                    "message": "Database connection failed",
                    "error": str(e),
                    "data": {"db_path": DB_PATH, "cwd": os.getcwd()},
                    "timestamp": int(time.time() * 1000),
                    "sessionId": "debug-session",
                    "runId": "run1",
                    "hypothesisId": "H11"
                }) + "\n")
        except Exception:
            pass
        raise


@contextmanager
def get_conn() -> Iterable[sqlite3.Connection]:
    conn = _connect()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS attempts(
              assessment_id TEXT PRIMARY KEY,
              user_id INTEGER,
              session_id TEXT,
              status TEXT,
              started_at_ms INT,
              completed_at_ms INT,
              FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL
            )
            """
        )
        # Migrate: add session_id and user_id if they don't exist
        try:
            conn.execute("ALTER TABLE attempts ADD COLUMN session_id TEXT")
        except sqlite3.OperationalError:
            pass  # Column already exists
        try:
            conn.execute("ALTER TABLE attempts ADD COLUMN user_id INTEGER")
        except sqlite3.OperationalError:
            pass  # Column already exists
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS responses(
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              assessment_id TEXT,
              item_id TEXT,
              answer_value INT,
              selected_option TEXT,
              answered_at_ms INT
            )
            """
        )
        # Migrate: add selected_option column if it doesn't exist
        try:
            conn.execute("ALTER TABLE responses ADD COLUMN selected_option TEXT")
        except sqlite3.OperationalError:
            pass  # Column already exists
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS events(
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              assessment_id TEXT,
              session_id TEXT,
              event_name TEXT,
              client_ts_ms INT,
              perf_ts_ms REAL,
              item_id TEXT,
              seq INT,
              payload_json TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS financial(
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              assessment_id TEXT UNIQUE,
              monthly_income REAL,
              monthly_expenses REAL,
              total_debt REAL,
              missed_payments_3m INT
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS computed(
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              assessment_id TEXT UNIQUE,
              metadata_json TEXT,
              traits_json TEXT,
              pd_psych_hat REAL,
              pd_fin_hat REAL,
              pd_final_hat REAL
            )
            """
        )
        # Table to track next user ID for FSxxxxxx format
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_id_counter(
              id INTEGER PRIMARY KEY CHECK (id = 1),
              next_id INT DEFAULT 1
            )
            """
        )
        # Initialize counter if not exists
        conn.execute(
            """
            INSERT OR IGNORE INTO user_id_counter(id, next_id) VALUES (1, 1)
            """
        )
        # Users table for authentication
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users(
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              username TEXT UNIQUE NOT NULL,
              password_hash TEXT NOT NULL,
              email TEXT,
              created_at_ms INT NOT NULL,
              last_login_ms INT,
              role TEXT DEFAULT 'user'
            )
            """
        )
        # Migrate: add role column if it doesn't exist
        try:
            conn.execute("ALTER TABLE users ADD COLUMN role TEXT DEFAULT 'user'")
        except sqlite3.OperationalError:
            pass  # Column already exists

        # Notes table for bank dashboard
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS notes(
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              assessment_id TEXT,
              author_id INTEGER,
              category TEXT,
              text TEXT,
              created_at_ms INT,
              FOREIGN KEY(author_id) REFERENCES users(id) ON DELETE SET NULL
            )
            """
        )
        # Financial data table for personas (matching CSV features)
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS financial_data(
              user_id INTEGER PRIMARY KEY,
              customer_id TEXT,
              num_previous_loans REAL DEFAULT 0,
              avg_time_bw_loans REAL,
              avg_past_amount REAL,
              avg_past_daily_burden REAL,
              std_past_amount REAL,
              std_past_daily_burden REAL,
              trend_in_amount REAL,
              trend_in_burden REAL,
              Total_Amount REAL,
              daily_burden REAL,
              amount_ratio REAL,
              burden_ratio REAL,
              amount_bucket TEXT,
              burden_percentile REAL,
              borrower_history_strength REAL,
              month INT,
              quarter INT,
              week_of_year INT,
              days_to_salary_day INT,
              days_to_local_festival INT,
              account_age_days INT,
              loan_frequency_per_year REAL,
              latest_amount_ma3 REAL,
              FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """
        )


def get_next_user_id() -> int:
    """Get and increment the next user ID for FSxxxxxx format."""
    with get_conn() as conn:
        # Get current counter
        row = conn.execute("SELECT next_id FROM user_id_counter WHERE id = 1").fetchone()
        counter_val = row["next_id"] if row else 1
        
        # Check max existing ID in attempts to prevent collision
        # (in case DB was modified externally or counter is out of sync)
        max_row = conn.execute("SELECT MAX(assessment_id) as max_id FROM attempts WHERE assessment_id LIKE 'FS%'").fetchone()
        max_existing = 0
        if max_row and max_row["max_id"]:
            try:
                max_existing = int(max_row["max_id"].replace("FS", ""))
            except ValueError:
                pass
        
        # If counter is behind, jump ahead
        if max_existing >= counter_val:
            counter_val = max_existing + 1
        
        # Update counter
        conn.execute("UPDATE user_id_counter SET next_id = ? WHERE id = 1", (counter_val + 1,))
        return counter_val


def insert_attempt(
    *,
    assessment_id: str,
    user_id: Optional[int],
    session_id: str,
    status: str,
    started_at_ms: int,
) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO attempts(assessment_id, user_id, session_id, status, started_at_ms, completed_at_ms)
            VALUES (?, ?, ?, ?, ?, NULL)
            """,
            (assessment_id, user_id, session_id, status, started_at_ms),
        )


def get_attempt(assessment_id: str) -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM attempts WHERE assessment_id = ?",
            (assessment_id,),
        ).fetchone()
        return dict(row) if row else None


def mark_attempt_completed(assessment_id: str, completed_at_ms: int) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE attempts
            SET status = 'completed', completed_at_ms = ?
            WHERE assessment_id = ?
            """,
            (completed_at_ms, assessment_id),
        )


def insert_response(
    *,
    assessment_id: str,
    item_id: str,
    answer_value: Optional[int] = None,
    selected_option: Optional[str] = None,
    answered_at_ms: int,
) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO responses(assessment_id, item_id, answer_value, selected_option, answered_at_ms)
            VALUES (?, ?, ?, ?, ?)
            """,
            (assessment_id, item_id, answer_value, selected_option, answered_at_ms),
        )


def list_responses(assessment_id: str) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT * FROM responses
            WHERE assessment_id = ?
            ORDER BY answered_at_ms ASC, id ASC
            """,
            (assessment_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def insert_events(
    *,
    assessment_id: str,
    session_id: str,
    events: List[Dict[str, Any]],
) -> None:
    with get_conn() as conn:
        conn.executemany(
            """
            INSERT INTO events(assessment_id, session_id, event_name, client_ts_ms, perf_ts_ms, item_id, seq, payload_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    assessment_id,
                    session_id,
                    e.get("event_name"),
                    e.get("client_ts_ms"),
                    e.get("perf_ts_ms"),
                    e.get("item_id"),
                    e.get("seq"),
                    json.dumps(e.get("payload") or {}),
                )
                for e in events
            ],
        )


def list_events(assessment_id: str) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT * FROM events
            WHERE assessment_id = ?
            ORDER BY seq ASC, client_ts_ms ASC, id ASC
            """,
            (assessment_id,),
        ).fetchall()
        return [dict(r) for r in rows]


def upsert_financial(
    *,
    assessment_id: str,
    monthly_income: float,
    monthly_expenses: float,
    total_debt: float,
    missed_payments_3m: int,
) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO financial(assessment_id, monthly_income, monthly_expenses, total_debt, missed_payments_3m)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(assessment_id) DO UPDATE SET
              monthly_income=excluded.monthly_income,
              monthly_expenses=excluded.monthly_expenses,
              total_debt=excluded.total_debt,
              missed_payments_3m=excluded.missed_payments_3m
            """,
            (assessment_id, monthly_income, monthly_expenses, total_debt, missed_payments_3m),
        )


def get_financial(assessment_id: str) -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM financial WHERE assessment_id = ?",
            (assessment_id,),
        ).fetchone()
        return dict(row) if row else None


def upsert_computed(
    *,
    assessment_id: str,
    metadata: Dict[str, Any],
    traits: Dict[str, Any],
    pd_psych_hat: Optional[float],
    pd_fin_hat: Optional[float],
    pd_final_hat: Optional[float],
) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO computed(assessment_id, metadata_json, traits_json, pd_psych_hat, pd_fin_hat, pd_final_hat)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(assessment_id) DO UPDATE SET
              metadata_json=excluded.metadata_json,
              traits_json=excluded.traits_json,
              pd_psych_hat=excluded.pd_psych_hat,
              pd_fin_hat=excluded.pd_fin_hat,
              pd_final_hat=excluded.pd_final_hat
            """,
            (
                assessment_id,
                json.dumps(metadata),
                json.dumps(traits),
                pd_psych_hat,
                pd_fin_hat,
                pd_final_hat,
            ),
        )


def get_computed(assessment_id: str) -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM computed WHERE assessment_id = ?",
            (assessment_id,),
        ).fetchone()
        if not row:
            return None
        d = dict(row)
        d["metadata"] = json.loads(d.get("metadata_json") or "{}")
        d["traits"] = json.loads(d.get("traits_json") or "{}")
        return d


# ============================================================================
# USER AUTHENTICATION
# ============================================================================

def create_user(username: str, password_hash: str, email: Optional[str] = None) -> int:
    """Create a new user and return user_id."""
    with get_conn() as conn:
        cursor = conn.execute(
            """
            INSERT INTO users(username, password_hash, email, created_at_ms, last_login_ms, role)
            VALUES (?, ?, ?, ?, NULL, ?)
            """,
            (username, password_hash, email, int(time.time() * 1000), "user"),
        )
        return cursor.lastrowid


def create_bank_user(username: str, password_hash: str, email: Optional[str] = None) -> int:
    """Create a new bank user and return user_id."""
    with get_conn() as conn:
        cursor = conn.execute(
            """
            INSERT INTO users(username, password_hash, email, created_at_ms, last_login_ms, role)
            VALUES (?, ?, ?, ?, NULL, ?)
            """,
            (username, password_hash, email, int(time.time() * 1000), "bank_admin"),
        )
        return cursor.lastrowid


def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """Get user by username."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ?",
            (username,),
        ).fetchone()
        return dict(row) if row else None


def get_user_by_id(user_id: int) -> Optional[Dict[str, Any]]:
    """Get user by user_id."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        return dict(row) if row else None


def update_last_login(user_id: int) -> None:
    """Update last login timestamp."""
    with get_conn() as conn:
        conn.execute(
            "UPDATE users SET last_login_ms = ? WHERE id = ?",
            (int(time.time() * 1000), user_id),
        )


# ============================================================================
# FINANCIAL DATA (PERSONAS)
# ============================================================================

def upsert_financial_data(user_id: int, financial_data: Dict[str, Any]) -> None:
    """Insert or update financial data for a user."""
    with get_conn() as conn:
        # Get all column names except user_id
        columns = [
            "customer_id", "num_previous_loans", "avg_time_bw_loans", "avg_past_amount",
            "avg_past_daily_burden", "std_past_amount", "std_past_daily_burden",
            "trend_in_amount", "trend_in_burden", "Total_Amount", "daily_burden",
            "amount_ratio", "burden_ratio", "amount_bucket", "burden_percentile",
            "borrower_history_strength", "month", "quarter", "week_of_year",
            "days_to_salary_day", "days_to_local_festival", "account_age_days",
            "loan_frequency_per_year", "latest_amount_ma3"
        ]
        
        values = [financial_data.get(col) for col in columns]
        placeholders = ", ".join(["?"] * len(columns))
        column_names = ", ".join(columns)
        
        conn.execute(
            f"""
            INSERT INTO financial_data(user_id, {column_names})
            VALUES (?, {placeholders})
            ON CONFLICT(user_id) DO UPDATE SET
              {", ".join([f"{col}=excluded.{col}" for col in columns])}
            """,
            [user_id] + values,
        )


def get_financial_data(user_id: int) -> Optional[Dict[str, Any]]:
    """Get financial data for a user."""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT * FROM financial_data WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        return dict(row) if row else None


        return dict(row) if row else None


# ============================================================================
# BANK DASHBOARD FUNCTIONS
# ============================================================================

def get_all_borrowers(
    search: Optional[str] = None,
    model_type: Optional[str] = None,
    risk_band: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
) -> Tuple[List[Dict[str, Any]], int]:
    """
    Get list of borrowers/attempts with filters.
    Returns (list_of_attempts, total_count).
    """
    with get_conn() as conn:
        query = """
            SELECT a.*, c.pd_final_hat, c.traits_json, f.monthly_income 
            FROM attempts a
            LEFT JOIN computed c ON a.assessment_id = c.assessment_id
            LEFT JOIN financial f ON a.assessment_id = f.assessment_id
            WHERE 1=1
        """
        params = []
        
        if search:
            # Basic search implementation
            query += " AND (a.assessment_id LIKE ? OR a.session_id LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])
            
        if status:
            query += " AND a.status = ?"
            params.append(status)
            
        # Add more filters as needed for MVP
        
        query += " ORDER BY a.started_at_ms DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])
        
        rows = conn.execute(query, params).fetchall()
        
        # Get total count
        count_query = "SELECT COUNT(*) as count FROM attempts a WHERE 1=1"
        # Re-apply filters for count
        count_params = []
        if search:
            count_query += " AND (a.assessment_id LIKE ? OR a.session_id LIKE ?)"
            count_params.extend([f"%{search}%", f"%{search}%"])
        if status:
            count_query += " AND a.status = ?"
            count_params.append(status)
            
        count_row = conn.execute(count_query, count_params).fetchone()
        total = count_row["count"] if count_row else 0
        
        return [dict(r) for r in rows], total


def add_note(assessment_id: str, author_id: int, category: str, text: str) -> int:
    with get_conn() as conn:
        cursor = conn.execute(
            """
            INSERT INTO notes(assessment_id, author_id, category, text, created_at_ms)
            VALUES (?, ?, ?, ?, ?)
            """,
            (assessment_id, author_id, category, text, int(time.time() * 1000)),
        )
        return cursor.lastrowid


def get_notes(assessment_id: str) -> List[Dict[str, Any]]:
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT n.*, u.username as author_name 
            FROM notes n
            LEFT JOIN users u ON n.author_id = u.id
            WHERE n.assessment_id = ?
            ORDER BY n.created_at_ms DESC
            """,
            (assessment_id,),
        ).fetchall()
        return [dict(r) for r in rows]
