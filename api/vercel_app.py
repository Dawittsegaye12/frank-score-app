"""
Vercel-optimized FastAPI app.
This version is designed for serverless deployment with external services.
"""
import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import requests
from typing import Any, Dict, Optional

# Create FastAPI app
app = FastAPI(title="frankscore_demo_vercel")

# Templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# External API URL (your Render deployment)
RENDER_API_URL = os.getenv("RENDER_API_URL", "https://frank-score-app.onrender.com")


@app.get("/health")
def health() -> Dict[str, Any]:
    """Health check endpoint."""
    return {
        "ok": True,
        "platform": "vercel",
        "render_api": RENDER_API_URL
    }


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> Any:
    """Redirect to login page."""
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request) -> Any:
    """Login page."""
    return templates.TemplateResponse("login.html", {"request": request})


@app.get("/terms", response_class=HTMLResponse)
def terms(request: Request) -> Any:
    """Terms page."""
    return templates.TemplateResponse("terms.html", {"request": request})


@app.get("/questions", response_class=HTMLResponse)
def questions_page(request: Request, assessment_id: str) -> Any:
    """Questions page."""
    return templates.TemplateResponse(
        "questions.html",
        {"request": request, "assessment_id": assessment_id},
    )


@app.get("/result", response_class=HTMLResponse)
def result_page(request: Request, assessment_id: str) -> Any:
    """Result page."""
    return templates.TemplateResponse(
        "result.html",
        {"request": request, "assessment_id": assessment_id},
    )


# API Routes - Proxy to Render for heavy operations
@app.post("/api/start")
async def api_start(request: Request) -> Any:
    """Start assessment - proxy to Render."""
    try:
        body = await request.json()
        response = requests.post(
            f"{RENDER_API_URL}/api/start",
            json=body,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/questions")
async def api_questions(assessment_id: Optional[str] = None) -> Any:
    """Get questions - can serve from Vercel or proxy."""
    try:
        # Option 1: Serve from Vercel (if question bank is small)
        # Option 2: Proxy to Render
        response = requests.get(
            f"{RENDER_API_URL}/api/questions",
            params={"assessment_id": assessment_id},
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/complete")
async def api_complete(request: Request) -> Any:
    """Complete assessment - proxy to Render for ML predictions."""
    try:
        body = await request.json()
        response = requests.post(
            f"{RENDER_API_URL}/api/complete",
            json=body,
            timeout=30  # ML predictions may take longer
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/result")
async def api_result(assessment_id: str) -> Any:
    """Get results - proxy to Render."""
    try:
        response = requests.get(
            f"{RENDER_API_URL}/api/result",
            params={"assessment_id": assessment_id},
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Export for Vercel
def handler(request):
    """Vercel serverless function handler."""
    from mangum import Mangum
    asgi_handler = Mangum(app, lifespan="off")
    return asgi_handler(request.environ, lambda status, headers: None)

