"""
Vercel serverless function entry point for FastAPI app.
Minimal version to test basic functionality first.
"""
import sys
import os
import json
import traceback

# Simple logging
def log(msg, error=None):
    try:
        print(f"[DEBUG] {msg}", file=sys.stderr, flush=True)
        if error:
            print(f"[ERROR] {error}", file=sys.stderr, flush=True)
            print(f"[TRACEBACK] {traceback.format_exc()}", file=sys.stderr, flush=True)
    except:
        pass

log("Module loading - starting minimal handler setup")

# Try to create handler at module level
try:
    # Set up paths
    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, parent_dir)
    os.chdir(parent_dir)
    log(f"Working directory: {os.getcwd()}")
    
    # Import app
    log("Importing app...")
    from app import app
    log("App imported")
    
    # Import Mangum
    log("Importing Mangum...")
    from mangum import Mangum
    log("Mangum imported")
    
    # Create handler
    log("Creating Mangum handler...")
    mangum_handler = Mangum(app, lifespan="off")
    log(f"Mangum handler created: {type(mangum_handler)}")
    
    # Wrap in synchronous function for Vercel
    def handler(event, context):
        log("=" * 50)
        log("Handler called")
        log(f"Event type: {type(event)}")
        
        try:
            # Call Mangum - it handles async internally
            result = mangum_handler(event, context)
            
            # Handle async result if needed
            import inspect
            if inspect.iscoroutine(result):
                log("Result is coroutine - running async")
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                result = loop.run_until_complete(result)
                log("Async completed")
            
            log(f"Result: {type(result)}")
            return result
            
        except Exception as e:
            log("Handler error", e)
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({
                    "error": str(e),
                    "type": type(e).__name__,
                    "traceback": traceback.format_exc()
                })
            }
    
    log("Handler function created successfully")
    
except Exception as e:
    log("CRITICAL: Failed to create handler", e)
    
    # Fallback minimal handler
    def handler(event, context):
        log("Fallback handler called")
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

# Export for Vercel
__all__ = ["handler"]
