"""FastAPI application router for Moneybags."""
import os
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

from app.database_model import initialize_database
from app.business_logic import get_dashboard_data

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="Moneybags", version="1.0.0")

# Setup static files and templates
BASE_DIR = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Initialize database
DATABASE_PATH = os.getenv("DATABASE_PATH", "./moneybags.db")
initialize_database(DATABASE_PATH)


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Dashboard page."""
    current_year = datetime.now().year
    current_month = datetime.now().month

    data = get_dashboard_data(current_year, current_month)

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        **data
    })


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
