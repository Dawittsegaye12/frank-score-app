"""
Vercel serverless function entry point for FastAPI app.
This wraps the FastAPI app to work with Vercel's serverless environment.
"""
import sys
import os
import json
import traceback
from datetime import datetime

# Early logging setup - runs before any other code
def _early_log(message, error=None):
    """Early logging that works even if other imports fail"""
    try:
        log_msg = f"[EARLY_DEBUG] {message}"
        if error:
            log_msg += f" | ERROR: {str(error)} | TRACEBACK: {traceback.format_exc()}"
        print(log_msg, file=sys.stderr, flush=True)
    except Exception:
        pass

_early_log("api/index.py: Module loading started")

# #region agent log
LOG_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".cursor", "debug.log")
def _log(hypothesis_id, location, message, data=None, error=None):
    try:
        entry = {
            "timestamp": int(datetime.now().timestamp() * 1000),
            "location": location,
            "message": message,
            "sessionId": "debug-session",
            "runId": "run1",
            "hypothesisId": hypothesis_id,
            "data": data or {},
        }
        if error:
            entry["error"] = str(error)
            entry["traceback"] = traceback.format_exc()
        log_str = json.dumps(entry)
        # Write to file (for local debugging)
        try:
            os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
            with open(LOG_PATH, "a", encoding="utf-8") as f:
                f.write(log_str + "\n")
        except Exception:
            pass
        # Also print to stderr (captured by Vercel logs)
        print(f"[DEBUG] {log_str}", file=sys.stderr, flush=True)
    except Exception:
        pass
# #endregion

try:
    # #region agent log
    _log("H1", "api/index.py:30", "Starting handler initialization", {"cwd": os.getcwd()})
    # #endregion
    
    # Add parent directory to path to import app modules
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # #region agent log
    _log("H2", "api/index.py:35", "Parent directory resolved", {"parent_dir": parent_dir, "exists": os.path.exists(parent_dir)})
    # #endregion
    
    sys.path.insert(0, parent_dir)
    
    # Change to parent directory so file paths work correctly
    os.chdir(parent_dir)
    
    # #region agent log
    _log("H2", "api/index.py:42", "Changed working directory", {"new_cwd": os.getcwd(), "templates_exists": os.path.exists("templates"), "static_exists": os.path.exists("static"), "questiondb_exists": os.path.exists("questiondb")})
    # #endregion
    
    # Import the FastAPI app
    # #region agent log
    _log("H1", "api/index.py:46", "About to import app module")
    # #endregion
    
    from app import app
    
    # #region agent log
    _log("H1", "api/index.py:50", "App module imported successfully", {"app_type": type(app).__name__})
    # #endregion
    
    # Import Mangum for ASGI adapter (required for Vercel)
    from mangum import Mangum
    
    # #region agent log
    _log("H5", "api/index.py:56", "Mangum imported, creating handler")
    # #endregion
    
    # Create ASGI handler - this is what Vercel calls
    # Use lifespan="on" to allow startup events to run
    mangum_handler = Mangum(app, lifespan="on")
    
    # #region agent log
    _log("H5", "api/index.py:62", "Handler created successfully", {"handler_type": type(mangum_handler).__name__})
    # #endregion
    
    # Wrap handler to catch invocation errors
    def wrapped_handler(event, context):
        # #region agent log
        _log("H8", "api/index.py:87", "Handler invoked", {"event_keys": list(event.keys()) if isinstance(event, dict) else "not_dict", "context_type": type(context).__name__ if context else "None"})
        # #endregion
        try:
            # #region agent log
            _log("H8", "api/index.py:91", "Calling mangum_handler")
            # #endregion
            result = mangum_handler(event, context)
            # #region agent log
            _log("H8", "api/index.py:94", "Handler call completed", {"result_type": type(result).__name__})
            # #endregion
            return result
        except Exception as e:
            # #region agent log
            _log("H8", "api/index.py:98", "CRITICAL: Handler invocation failed", error=e)
            # #endregion
            # Return error response instead of crashing
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({
                    "error": "Function invocation failed",
                    "detail": str(e),
                    "type": type(e).__name__
                })
            }
    
    handler = wrapped_handler
    
    # #region agent log
    _log("H1", "api/index.py:130", "Handler initialization complete")
    # #endregion
    
    # Vercel expects the handler to be available at module level
    __all__ = ["handler"]

except Exception as e:
    # #region agent log
    _log("H1", "api/index.py:113", "CRITICAL: Handler initialization failed", error=e)
    # #endregion
    # Create a minimal error handler to prevent complete failure
    def error_handler(event, context):
        # #region agent log
        _log("H1", "api/index.py:117", "Error handler invoked", {"init_error": str(e)})
        # #endregion
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Function initialization failed", "detail": str(e)})
        }
    handler = error_handler
    __all__ = ["handler"]
