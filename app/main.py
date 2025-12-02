"""FastAPI application router for Moneybags."""
import os
import csv
from io import StringIO
from pathlib import Path
from datetime import datetime
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
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
    get_monthly_chart_data,
    get_yoy_comparison_data,
    get_tag_analysis_data,
    get_time_series_data
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
    try:
        current_year = datetime.now().year
        current_month = datetime.now().month

        data = get_dashboard_data(current_year, current_month)
        chart_data = get_monthly_chart_data(current_year)

        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            **data,
            "chart_data": chart_data
        })
    except Exception as e:
        return templates.TemplateResponse("partials/_error_message.html", {
            "request": request,
            "error_message": f"Failed to load dashboard: {str(e)}"
        }, status_code=500)


@app.get("/budget", response_class=HTMLResponse)
async def budget_page(request: Request):
    """Budget and actuals page."""
    try:
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
    except Exception as e:
        return templates.TemplateResponse("partials/_error_message.html", {
            "request": request,
            "error_message": f"Failed to load budget page: {str(e)}"
        }, status_code=500)


@app.post("/api/budget/update")
async def update_budget(
    request: Request,
    post_id: str = Form(...),
    year: int = Form(...),
    month: int = Form(...),
    amount: float = Form(...)
):
    """Update or create a budget entry via htmx."""
    try:
        # Validate amount (>= 0)
        if amount < 0:
            raise HTTPException(status_code=400, detail="Budget amount must be greater than or equal to 0.")

        # Validate month (1-12)
        if month < 1 or month > 12:
            raise HTTPException(status_code=400, detail="Month must be between 1 and 12.")

        # Validate year (reasonable range)
        current_year = datetime.now().year
        if year < 2000 or year > current_year + 10:
            raise HTTPException(status_code=400, detail=f"Year must be between 2000 and {current_year + 10}.")

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
    except HTTPException:
        raise
    except Exception as e:
        return templates.TemplateResponse("partials/_error_message.html", {
            "request": request,
            "error_message": f"Failed to update budget: {str(e)}"
        }, status_code=500)


@app.get("/api/post/create-form")
async def post_create_form(request: Request, post_type: str):
    """Return form for creating a new post (income or expense)."""
    try:
        tags = get_all_tags()
        return templates.TemplateResponse("partials/_post_create_form.html", {
            "request": request,
            "post_type": post_type,
            "tags": tags
        })
    except Exception as e:
        return templates.TemplateResponse("partials/_error_message.html", {
            "request": request,
            "error_message": f"Failed to load post form: {str(e)}"
        }, status_code=500)


@app.get("/api/actual/create-form")
async def actual_entry_form(request: Request, post_id: str):
    """Return the form for creating a new actual entry (htmx modal)."""
    try:
        post = get_post(post_id)
        today = datetime.now().date().isoformat()
        return templates.TemplateResponse("partials/_actual_entry_form.html", {
            "request": request,
            "post": post,
            "today": today
        })
    except Exception as e:
        return templates.TemplateResponse("partials/_error_message.html", {
            "request": request,
            "error_message": f"Failed to load actual entry form: {str(e)}"
        }, status_code=500)


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
    name_stripped = name.strip()
    if not name_stripped:
        raise HTTPException(status_code=400, detail="Post name cannot be empty.")

    # Validate name length (max 100 characters)
    if len(name_stripped) > 100:
        raise HTTPException(status_code=400, detail="Post name cannot exceed 100 characters.")

    # Check for uniqueness - post names must be unique
    from app.database_manager import get_all_posts
    existing_posts = get_all_posts()
    if any(p.name.lower() == name_stripped.lower() for p in existing_posts):
        raise HTTPException(status_code=400, detail=f"A post with the name '{name_stripped}' already exists.")

    try:
        post = create_post_with_tags(name_stripped, post_type, tag_ids)
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
    try:
        from datetime import date as date_cls

        # Validate amount (>= 0)
        if amount < 0:
            raise HTTPException(status_code=400, detail="Amount must be greater than or equal to 0.")

        # Parse and validate date
        try:
            entry_date = datetime.strptime(date, "%Y-%m-%d").date()
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Expected YYYY-MM-DD.")

        # Validate date is not in the future
        today = datetime.now().date()
        if entry_date > today:
            raise HTTPException(status_code=400, detail="Date cannot be in the future.")

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
    except HTTPException:
        raise
    except Exception as e:
        return templates.TemplateResponse("partials/_error_message.html", {
            "request": request,
            "error_message": f"Failed to create actual entry: {str(e)}"
        }, status_code=500)


@app.delete("/api/actual/{entry_id}")
async def delete_actual_entry_endpoint(entry_id: str):
    """Delete an actual entry."""
    try:
        from app.database_manager import delete_actual_entry as db_delete

        db_delete(entry_id)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete actual entry: {str(e)}")


@app.get("/analysis", response_class=HTMLResponse)
async def analysis_page(request: Request):
    """Analysis page with multiple analysis modes."""
    try:
        current_year = datetime.now().year

        # Get budget vs actual analysis
        budget_analysis = get_budget_vs_actual_analysis(current_year)

        # Get year-over-year comparison data (last 3 years)
        years_to_compare = [current_year - 2, current_year - 1, current_year]
        yoy_data = get_yoy_comparison_data(years_to_compare)

        # Get tag analysis data
        tag_analysis = get_tag_analysis_data()

        # Get time series data for current year
        time_series = get_time_series_data(current_year)

        return templates.TemplateResponse("analysis.html", {
            "request": request,
            "year": current_year,
            "budget_analysis": budget_analysis,
            "yoy_data": yoy_data,
            "tag_analysis": tag_analysis,
            "time_series": time_series
        })
    except Exception as e:
        return templates.TemplateResponse("partials/_error_message.html", {
            "request": request,
            "error_message": f"Failed to load analysis page: {str(e)}"
        }, status_code=500)


@app.get("/config", response_class=HTMLResponse)
async def config_page(request: Request):
    """Configuration page."""
    try:
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
    except Exception as e:
        return templates.TemplateResponse("partials/_error_message.html", {
            "request": request,
            "error_message": f"Failed to load configuration page: {str(e)}"
        }, status_code=500)


@app.post("/api/config/preference")
async def update_user_preference(
    key: str = Form(...),
    value: str = Form(...)
):
    """Update user preference via htmx."""
    try:
        update_preference(key, value)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update preference: {str(e)}")


@app.post("/api/tag/create")
async def create_new_tag(
    request: Request,
    name: str = Form(...)
):
    """Create a new tag."""
    try:
        # Validate name is not empty after stripping whitespace
        name_stripped = name.strip()
        if not name_stripped:
            raise HTTPException(status_code=400, detail="Tag name cannot be empty.")

        # Validate name length (max 50 characters)
        if len(name_stripped) > 50:
            raise HTTPException(status_code=400, detail="Tag name cannot exceed 50 characters.")

        # Check for uniqueness - tag names must be unique (case-insensitive)
        existing_tags = get_all_tags()
        if any(t.name.lower() == name_stripped.lower() for t in existing_tags):
            raise HTTPException(status_code=400, detail=f"A tag with the name '{name_stripped}' already exists.")

        tag_id = generate_uuid()
        tag = create_tag(tag_id, name_stripped)

        # Return updated tag row
        return templates.TemplateResponse("partials/_tag_row.html", {
            "request": request,
            "tag": tag
        })
    except HTTPException:
        raise
    except Exception as e:
        return templates.TemplateResponse("partials/_error_message.html", {
            "request": request,
            "error_message": f"Failed to create tag: {str(e)}"
        }, status_code=500)


@app.delete("/api/tag/{tag_id}")
async def delete_tag_endpoint(tag_id: str):
    """Delete a tag."""
    try:
        from app.database_manager import delete_tag as db_delete_tag

        db_delete_tag(tag_id)
        return {"status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete tag: {str(e)}")


@app.get("/api/export/csv")
async def export_csv(
    export_type: str,
    start_date: str = None,
    end_date: str = None
):
    """
    Export data to CSV format.

    Args:
        export_type: Type of data to export (posts, budgets, actuals, analysis)
        start_date: Optional start date filter (YYYY-MM-DD)
        end_date: Optional end date filter (YYYY-MM-DD)
    """
    try:
        from datetime import date as date_cls

        # Parse date filters if provided
        date_filter_start = None
        date_filter_end = None
        if start_date:
            date_filter_start = datetime.strptime(start_date, "%Y-%m-%d").date()
        if end_date:
            date_filter_end = datetime.strptime(end_date, "%Y-%m-%d").date()

        # Generate CSV content based on export type
        output = StringIO()
        writer = csv.writer(output)

        if export_type == "posts":
            # Export all posts
            from app.database_manager import get_all_posts
            posts = get_all_posts()

            # CSV headers
            writer.writerow(["ID", "Name", "Type", "Created"])

            # CSV rows
            for post in posts:
                writer.writerow([
                    post.id,
                    post.name,
                    post.type,
                    post.created_at.isoformat() if hasattr(post, 'created_at') else ""
                ])

        elif export_type == "budgets":
            # Export budget entries
            from app.database_manager import get_all_posts
            posts = get_all_posts()

            # CSV headers
            writer.writerow(["Post ID", "Post Name", "Post Type", "Year", "Month", "Amount"])

            # Get budget entries for each post
            current_year = datetime.now().year
            for post in posts:
                budgets = get_budget_entries(post.id, current_year)
                for budget in budgets:
                    writer.writerow([
                        post.id,
                        post.name,
                        post.type,
                        budget.year,
                        budget.month,
                        float(budget.amount)
                    ])

        elif export_type == "actuals":
            # Export actual entries
            from app.database_manager import get_all_posts
            posts = get_all_posts()

            # CSV headers
            writer.writerow(["Post ID", "Post Name", "Post Type", "Date", "Amount", "Comment"])

            # Get actual entries for each post
            if not date_filter_start:
                date_filter_start = date_cls(datetime.now().year, 1, 1)
            if not date_filter_end:
                date_filter_end = date_cls(datetime.now().year, 12, 31)

            for post in posts:
                entries = get_actual_entries(post.id, date_filter_start, date_filter_end)
                for entry in entries:
                    writer.writerow([
                        post.id,
                        post.name,
                        post.type,
                        entry.date.isoformat(),
                        float(entry.amount),
                        entry.comment
                    ])

        elif export_type == "analysis":
            # Export budget vs actual analysis
            current_year = datetime.now().year
            analysis = get_budget_vs_actual_analysis(current_year)

            # CSV headers
            writer.writerow(["Post Name", "Post Type", "Budget", "Actual", "Variance", "Percentage"])

            # CSV rows
            for item in analysis:
                writer.writerow([
                    item['post_name'],
                    item['post_type'],
                    float(item['budget']),
                    float(item['actual']),
                    float(item['variance']),
                    float(item['percentage'])
                ])
        else:
            raise HTTPException(status_code=400, detail=f"Invalid export type: {export_type}")

        # Generate filename with timestamp and filters
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"moneybags_{export_type}_{timestamp}"
        if start_date and end_date:
            filename += f"_{start_date}_to_{end_date}"
        filename += ".csv"

        # Return CSV as downloadable file
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export CSV: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}
