"""
Vercel serverless function entry point for FastAPI app.
This wraps the FastAPI app to work with Vercel's serverless environment.
"""
import sys
import os
import json
import traceback
import asyncio

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

_early_log("api/index.py: Module loading started - using lazy initialization")

# Global handler - will be created on first invocation
_handler = None
_init_error = None

def _create_handler():
    """Create the handler - called lazily on first request"""
    global _handler, _init_error
    
    if _handler is not None:
        return _handler
    
    if _init_error is not None:
        # Return error handler if initialization previously failed
        def error_handler(event, context):
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({
                    "error": "Handler initialization failed",
                    "detail": str(_init_error),
                    "type": type(_init_error).__name__
                })
            }
        return error_handler
    
    try:
        _early_log("Creating handler - starting imports...")
        
        # Add parent directory to path
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sys.path.insert(0, parent_dir)
        os.chdir(parent_dir)
        
        _early_log(f"Changed to directory: {os.getcwd()}")
        _early_log(f"Templates exists: {os.path.exists('templates')}")
        _early_log(f"Static exists: {os.path.exists('static')}")
        _early_log(f"Questiondb exists: {os.path.exists('questiondb')}")
        
        # Import app
        _early_log("Importing app module...")
        from app import app
        _early_log("App imported successfully")
        
        # Import Mangum
        _early_log("Importing Mangum...")
        from mangum import Mangum
        _early_log("Mangum imported successfully")
        
        # Create handler with lifespan="off" for serverless
        _early_log("Creating Mangum handler...")
        mangum_handler = Mangum(app, lifespan="off")
        _early_log("Mangum handler created successfully")
        _early_log(f"Mangum handler type: {type(mangum_handler).__name__}")
        
        # Check if handler is callable
        if not callable(mangum_handler):
            raise TypeError(f"Mangum handler is not callable: {type(mangum_handler)}")
        
        _handler = mangum_handler
        _early_log("Handler initialization complete")
        return _handler
        
    except Exception as e:
        _early_log(f"CRITICAL: Handler creation failed: {str(e)}", e)
        _init_error = e
        
        # Return error handler
        def error_handler(event, context):
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({
                    "error": "Handler initialization failed",
                    "detail": str(e),
                    "type": type(e).__name__,
                    "traceback": traceback.format_exc()
                })
            }
        _handler = error_handler
        return _handler

# Main handler function - Vercel calls this
def handler(event, context):
    """Main handler - creates handler lazily on first call"""
    try:
        _early_log("=" * 50)
        _early_log("Handler invoked - getting handler instance...")
        _early_log(f"Event type: {type(event).__name__}")
        _early_log(f"Context type: {type(context).__name__ if context else 'None'}")
        if isinstance(event, dict):
            _early_log(f"Event keys: {list(event.keys())[:10]}")  # First 10 keys
            if "httpMethod" in event:
                _early_log(f"HTTP Method: {event.get('httpMethod')}")
            if "path" in event:
                _early_log(f"Path: {event.get('path')}")
        
        h = _create_handler()
        _early_log(f"Handler instance obtained, type: {type(h).__name__}")
        _early_log(f"Handler is callable: {callable(h)}")
        _early_log("Calling handler...")
        
        # Call the handler - Mangum handles async internally
        result = h(event, context)
        
        # Check if result is a coroutine (async function result)
        import inspect
        if inspect.iscoroutine(result):
            _early_log("Handler returned coroutine - running with asyncio...")
            # Create new event loop for this invocation
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            result = loop.run_until_complete(result)
            _early_log("Coroutine completed")
        
        _early_log(f"Handler call completed, result type: {type(result).__name__}")
        if isinstance(result, dict):
            _early_log(f"Result keys: {list(result.keys())}")
            if "statusCode" in result:
                _early_log(f"Status code: {result.get('statusCode')}")
        
        return result
    except Exception as e:
        _early_log(f"CRITICAL: Handler invocation failed: {str(e)}", e)
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "error": "Handler invocation failed",
                "detail": str(e),
                "type": type(e).__name__,
                "traceback": traceback.format_exc()
            })
        }

__all__ = ["handler"]
