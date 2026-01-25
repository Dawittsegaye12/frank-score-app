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

# Import Mangum for ASGI adapter (required for Vercel)
from mangum import Mangum

# Create ASGI handler - this is what Vercel calls
handler = Mangum(app, lifespan="off")

# Vercel expects the handler to be available at module level
__all__ = ["handler"]
