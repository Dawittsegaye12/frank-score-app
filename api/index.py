"""
Vercel serverless function entry point for FastAPI app.
This wraps the FastAPI app to work with Vercel's serverless environment.
"""
import sys
import os
import json
import traceback

# Early logging - runs before any imports
def _log(message, error=None):
    try:
        msg = f"[DEBUG] {message}"
        if error:
            msg += f" | ERROR: {str(error)}"
            msg += f" | TRACEBACK: {traceback.format_exc()}"
        print(msg, file=sys.stderr, flush=True)
    except:
        pass

_log("Module loading started")

# Set up paths before any imports
try:
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, parent_dir)
    os.chdir(parent_dir)
    _log(f"Set working directory to: {os.getcwd()}")
except Exception as e:
    _log(f"Failed to set working directory: {e}", e)

# Import and create handler - do this at module level for Vercel
try:
    _log("Importing app...")
    from app import app
    _log("App imported successfully")
    
    _log("Importing Mangum...")
    from mangum import Mangum
    _log("Mangum imported successfully")
    
    _log("Creating Mangum handler...")
    # Create handler with lifespan="off" for serverless
    mangum_handler = Mangum(app, lifespan="off")
    _log(f"Mangum handler created: {type(mangum_handler).__name__}")
    
    # Wrap in a synchronous function for Vercel
    def handler(event, context):
        """Vercel handler - must be synchronous"""
        try:
            _log("=" * 60)
            _log("Handler invoked")
            _log(f"Event type: {type(event).__name__}")
            _log(f"Context: {context}")
            
            if isinstance(event, dict):
                _log(f"Event keys: {list(event.keys())[:5]}")
            
            # Call Mangum handler - it returns a coroutine for async apps
            result = mangum_handler(event, context)
            
            # Check if result is a coroutine (async)
            import inspect
            if inspect.iscoroutine(result):
                _log("Result is coroutine - running with asyncio")
                import asyncio
                # Try to get existing loop, create new if needed
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_closed():
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                result = loop.run_until_complete(result)
                _log("Coroutine completed")
            
            _log(f"Result type: {type(result).__name__}")
            if isinstance(result, dict):
                _log(f"Result has statusCode: {'statusCode' in result}")
            
            return result
            
        except Exception as e:
            _log(f"Handler invocation failed: {e}", e)
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
    
    _log("Handler function created successfully")
    
except Exception as e:
    _log(f"CRITICAL: Failed to create handler: {e}", e)
    # Fallback error handler
    def handler(event, context):
        _log("Error handler invoked")
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

# Export handler for Vercel
__all__ = ["handler"]
