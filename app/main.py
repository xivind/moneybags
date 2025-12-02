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
from app.business_logic import get_dashboard_data, get_posts_by_type
from app.database_manager import get_budget_entries

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


@app.get("/budget", response_class=HTMLResponse)
async def budget_page(request: Request):
    """Budget and actuals page."""
    current_year = datetime.now().year

    income_posts = get_posts_by_type('income')
    expense_posts = get_posts_by_type('expense')

    # Get budget entries for each post
    income_data = []
    for post in income_posts:
        budgets = get_budget_entries(post.id, current_year)
        income_data.append({
            'post': post,
            'budgets': budgets
        })

    expense_data = []
    for post in expense_posts:
        budgets = get_budget_entries(post.id, current_year)
        expense_data.append({
            'post': post,
            'budgets': budgets
        })

    return templates.TemplateResponse("budget.html", {
        "request": request,
        "year": current_year,
        "income_data": income_data,
        "expense_data": expense_data
    })


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
