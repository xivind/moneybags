"""FastAPI application router for Moneybags."""
import os
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

from app.database_model import initialize_database
from app.business_logic import get_dashboard_data, get_posts_by_type
from app.database_manager import (
    get_budget_entries,
    create_budget_entry,
    update_budget_entry
)
from app.utils import generate_uuid

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


@app.post("/api/budget/update")
async def update_budget(
    request: Request,
    post_id: str = Form(...),
    year: int = Form(...),
    month: int = Form(...),
    amount: float = Form(...)
):
    """Update or create a budget entry via htmx."""
    # Check if budget entry exists
    existing_entries = get_budget_entries(post_id, year)
    existing = next((e for e in existing_entries if e.month == month), None)

    if existing:
        # Update existing
        entry = update_budget_entry(existing.id, amount=amount)
    else:
        # Create new
        entry_id = generate_uuid()
        entry = create_budget_entry(entry_id, post_id, year, month, amount)

    # Return updated input HTML (partial)
    return templates.TemplateResponse("partials/_budget_input.html", {
        "request": request,
        "budget_amount": entry.amount,
        "post_id": post_id,
        "year": year,
        "month": month
    })


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
