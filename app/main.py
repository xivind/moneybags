"""FastAPI application router for Moneybags."""
import os
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv

from app.database_model import initialize_database
from app.business_logic import (
    get_dashboard_data,
    get_posts_by_type,
    get_budget_vs_actual_analysis,
    get_year_over_year_comparison,
    create_post_with_tags,
    get_monthly_chart_data
)
from app.database_manager import (
    get_budget_entries,
    create_budget_entry,
    update_budget_entry,
    get_post,
    create_actual_entry,
    get_actual_entries,
    get_or_create_preference,
    update_preference,
    get_all_tags,
    create_tag
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
    chart_data = get_monthly_chart_data(current_year)

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        **data,
        "chart_data": chart_data
    })


@app.get("/budget", response_class=HTMLResponse)
async def budget_page(request: Request):
    """Budget and actuals page."""
    from datetime import date as date_cls

    current_year = datetime.now().year

    income_posts = get_posts_by_type('income')
    expense_posts = get_posts_by_type('expense')

    # Date range for actual entries
    start_date = date_cls(current_year, 1, 1)
    end_date = date_cls(current_year, 12, 31)

    # Get budget entries and actual entries for each post
    income_data = []
    for post in income_posts:
        budgets = get_budget_entries(post.id, current_year)
        entries = get_actual_entries(post.id, start_date, end_date)
        income_data.append({
            'post': post,
            'budgets': budgets,
            'entries': entries
        })

    expense_data = []
    for post in expense_posts:
        budgets = get_budget_entries(post.id, current_year)
        entries = get_actual_entries(post.id, start_date, end_date)
        expense_data.append({
            'post': post,
            'budgets': budgets,
            'entries': entries
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


@app.get("/api/post/create-form")
async def post_create_form(request: Request, post_type: str):
    """Return form for creating a new post (income or expense)."""
    tags = get_all_tags()
    return templates.TemplateResponse("partials/_post_create_form.html", {
        "request": request,
        "post_type": post_type,
        "tags": tags
    })


@app.get("/api/actual/create-form")
async def actual_entry_form(request: Request, post_id: str):
    """Return the form for creating a new actual entry (htmx modal)."""
    post = get_post(post_id)
    return templates.TemplateResponse("partials/_actual_entry_form.html", {
        "request": request,
        "post": post
    })


@app.post("/api/post/create")
async def create_new_post(
    request: Request,
    name: str = Form(...),
    post_type: str = Form(...),
    tag_ids: list = Form([])
):
    """Create a new post with tags."""
    # Validate post_type
    if post_type not in ["income", "expense"]:
        raise HTTPException(status_code=400, detail="Invalid post type. Must be 'income' or 'expense'.")

    # Validate name is not empty after stripping whitespace
    if not name.strip():
        raise HTTPException(status_code=400, detail="Post name cannot be empty.")

    try:
        post = create_post_with_tags(name, post_type, tag_ids)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create post: {str(e)}")

    # Redirect to budget page (full page reload to show new post)
    return RedirectResponse(url="/budget", status_code=303)


@app.post("/api/actual/create")
async def create_actual(
    request: Request,
    post_id: str = Form(...),
    date: str = Form(...),
    amount: float = Form(...),
    comment: str = Form("")
):
    """Create a new actual entry via htmx."""
    from datetime import date as date_cls

    # Parse date string
    entry_date = datetime.strptime(date, "%Y-%m-%d").date()

    # Create entry
    entry_id = generate_uuid()
    create_actual_entry(entry_id, post_id, entry_date, amount, comment)

    # Get all entries for this post (current year)
    current_year = datetime.now().year
    start_date = date_cls(current_year, 1, 1)
    end_date = date_cls(current_year, 12, 31)
    entries = get_actual_entries(post_id, start_date, end_date)

    # Return updated list
    return templates.TemplateResponse("partials/_actual_entries_list.html", {
        "request": request,
        "post_id": post_id,
        "entries": entries
    })


@app.get("/analysis", response_class=HTMLResponse)
async def analysis_page(request: Request):
    """Analysis page with multiple analysis modes."""
    current_year = datetime.now().year

    # Get budget vs actual analysis
    budget_analysis = get_budget_vs_actual_analysis(current_year)

    return templates.TemplateResponse("analysis.html", {
        "request": request,
        "year": current_year,
        "budget_analysis": budget_analysis
    })


@app.get("/config", response_class=HTMLResponse)
async def config_page(request: Request):
    """Configuration page."""
    # Get current preferences
    currency = get_or_create_preference('currency_notation', 'USD')
    date_format = get_or_create_preference('date_format', 'YYYY-MM-DD')

    # Get all tags
    tags = get_all_tags()

    return templates.TemplateResponse("config.html", {
        "request": request,
        "currency": currency,
        "date_format": date_format,
        "tags": tags
    })


@app.post("/api/config/preference")
async def update_user_preference(
    key: str = Form(...),
    value: str = Form(...)
):
    """Update user preference via htmx."""
    update_preference(key, value)
    return {"status": "success"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
