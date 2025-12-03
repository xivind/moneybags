"""
Main application file for Moneybags.
All routes consolidated here - no separate router files.
"""

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import logging

# Setup logging
logger = logging.getLogger(__name__)

# Initialize app
app = FastAPI(title="Moneybags")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.on_event("startup")
def startup_event():
    """Initialize application on startup."""
    logger.info("Starting Moneybags application...")
    # TODO: Initialize database when ready
    logger.info("Moneybags application started")

# ==================== HTML VIEWS ====================

@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    """Dashboard showing financial overview"""
    # TODO: Add real data when backend is ready
    return templates.TemplateResponse("dashboard.html", {
        "request": request
    })

@app.get("/budget", response_class=HTMLResponse)
def budget_page(request: Request):
    """Budget and actuals page"""
    return templates.TemplateResponse("budget.html", {
        "request": request
    })

@app.get("/analysis", response_class=HTMLResponse)
def analysis_page(request: Request):
    """Analysis page with charts and deep dives"""
    return templates.TemplateResponse("analysis.html", {
        "request": request
    })

@app.get("/config", response_class=HTMLResponse)
def config_page(request: Request):
    """Configuration page for user preferences"""
    return templates.TemplateResponse("config.html", {
        "request": request
    })

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_config="uvicorn_log_config.ini"
    )
