"""
Vercel serverless function entry point for FastAPI app.
This wraps the FastAPI app to work with Vercel's serverless environment.
"""
import sys
import os

# Add parent directory to path to import app modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Import the FastAPI app
from app import app

# Import Mangum for ASGI adapter (needed for Vercel)
try:
    from mangum import Mangum
except ImportError:
    # Fallback if mangum not available
    print("Warning: mangum not installed, using basic handler")
    from fastapi import Request
    from fastapi.responses import JSONResponse
    
    async def handler(request: Request):
        """Basic handler fallback."""
        return JSONResponse({"error": "Mangum adapter required"})
else:
    # Create ASGI handler with Mangum
    handler = Mangum(app, lifespan="off")
