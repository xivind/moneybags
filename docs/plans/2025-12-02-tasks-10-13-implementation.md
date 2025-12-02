# Tasks 10-13 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement these tasks.

**Goal:** Complete the htmx-powered interactive features for budget management, actual entry tracking, analysis, and configuration.

**Architecture:** Continue the layered structure with FastAPI API routes, business logic calculations, and htmx partial template responses for smooth UX.

**Tech Stack:** Python, FastAPI, htmx, Bootstrap, Chart.js, TomSelect

---

## Task 10: API Endpoints for Budget Updates (htmx)

**Files:**
- Modify: `app/main.py` (add POST `/api/budget/update` route)
- Create: `app/templates/partials/_budget_input.html`
- Create: `tests/test_api_budget.py` (optional - API testing)

**Step 1: Create the budget update API route in main.py**

Add new route after the `/budget` route:

```python
from fastapi import Form
from app.database_manager import create_budget_entry, update_budget_entry, get_budget_entries

@app.post("/api/budget/update")
async def update_budget(
    post_id: str = Form(...),
    year: int = Form(...),
    month: int = Form(...),
    amount: float = Form(...)
):
    """Update or create a budget entry via htmx."""
    from app.utils import generate_uuid

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
        "request": None,
        "budget_amount": entry.amount,
        "post_id": post_id,
        "year": year,
        "month": month
    })
```

**Step 2: Create the budget input partial template**

Create `app/templates/partials/_budget_input.html`:

```html
<input
    type="number"
    class="form-control budget-input"
    value="{{ "%.2f"|format(budget_amount) }}"
    hx-post="/api/budget/update"
    hx-trigger="change delay:500ms"
    hx-vals='{"post_id": "{{ post_id }}", "year": {{ year }}, "month": {{ month }}}'
    step="0.01"
>
```

**Step 3: Update _post_row.html to use the new partial**

Modify the budget input loop in `_post_row.html` to include the partial:

```html
{% for month in range(1, 13) %}
<div class="col-1">
    <label class="form-label small">{{ ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'][month-1] }}</label>
    {% set budget = (item.budgets | selectattr('month', '==', month) | list | first) if (item.budgets | selectattr('month', '==', month) | list) else None %}
    {% include "partials/_budget_input.html" with context %}
</div>
{% endfor %}
```

**Step 4: Test manually**

Run: `uvicorn app.main:app --reload`
- Navigate to `/budget`
- Change a budget value
- Verify it saves (check database or refresh page)

**Step 5: Commit**

```bash
git add app/main.py app/templates/partials/_budget_input.html app/templates/partials/_post_row.html
git commit -m "feat: add htmx budget update API endpoint"
```

---

## Task 11: API Endpoints for Actual Entries (htmx)

**Files:**
- Modify: `app/main.py` (add POST `/api/actual/create`, GET `/api/actual/create-form`)
- Create: `app/templates/partials/_actual_entry_form.html`
- Create: `app/templates/partials/_actual_entry_row.html`
- Create: `app/templates/partials/_actual_entries_list.html`

**Step 1: Create the actual entry creation form endpoint**

Add to `app/main.py`:

```python
@app.get("/api/actual/create-form")
async def actual_entry_form(request: Request, post_id: str):
    """Return the form for creating a new actual entry (htmx modal)."""
    from app.database_manager import get_post

    post = get_post(post_id)
    return templates.TemplateResponse("partials/_actual_entry_form.html", {
        "request": request,
        "post": post
    })
```

**Step 2: Create the actual entry form partial**

Create `app/templates/partials/_actual_entry_form.html`:

```html
<div class="modal fade show" style="display: block;" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Add Actual Entry - {{ post.name }}</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <form hx-post="/api/actual/create" hx-target="#actual-entries-{{ post.id }}">
                <div class="modal-body">
                    <input type="hidden" name="post_id" value="{{ post.id }}">

                    <div class="mb-3">
                        <label class="form-label">Date</label>
                        <input type="date" name="date" class="form-control datepicker" required>
                    </div>

                    <div class="mb-3">
                        <label class="form-label">Amount</label>
                        <input type="number" name="amount" class="form-control" step="0.01" required>
                    </div>

                    <div class="mb-3">
                        <label class="form-label">Comment (optional)</label>
                        <textarea name="comment" class="form-control" rows="2"></textarea>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button type="submit" class="btn btn-primary">Save Entry</button>
                </div>
            </form>
        </div>
    </div>
</div>
```

**Step 3: Create the actual entry creation endpoint**

Add to `app/main.py`:

```python
from datetime import datetime

@app.post("/api/actual/create")
async def create_actual(
    post_id: str = Form(...),
    date: str = Form(...),
    amount: float = Form(...),
    comment: str = Form("")
):
    """Create a new actual entry via htmx."""
    from app.utils import generate_uuid
    from app.database_manager import create_actual_entry, get_actual_entries
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
        "request": None,
        "post_id": post_id,
        "entries": entries
    })
```

**Step 4: Create the actual entries list partial**

Create `app/templates/partials/_actual_entries_list.html`:

```html
<div id="actual-entries-{{ post_id }}">
    {% if entries %}
    <table class="table table-sm">
        <thead>
            <tr>
                <th>Date</th>
                <th>Amount</th>
                <th>Comment</th>
                <th>Actions</th>
            </tr>
        </thead>
        <tbody>
            {% for entry in entries %}
            <tr>
                <td>{{ entry.date }}</td>
                <td>{{ "%.2f"|format(entry.amount) }}</td>
                <td>{{ entry.comment or '-' }}</td>
                <td>
                    <button class="btn btn-sm btn-danger"
                            hx-delete="/api/actual/{{ entry.id }}"
                            hx-target="closest tr"
                            hx-swap="outerHTML swap:1s">
                        Delete
                    </button>
                </td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
    {% else %}
    <p class="text-muted">No entries yet</p>
    {% endif %}
</div>
```

**Step 5: Update _post_row.html to include actual entries list**

Modify the actual entries section in `_post_row.html`:

```html
<!-- Actual entries -->
<div class="mt-2">
    <h6>Actual Entries</h6>
    {% include "partials/_actual_entries_list.html" with context %}
    <button class="btn btn-sm btn-outline-primary mt-2"
            hx-get="/api/actual/create-form?post_id={{ item.post.id }}"
            hx-target="#modal-content">
        + Add Entry
    </button>
</div>
```

**Step 6: Test manually**

- Navigate to `/budget`
- Click "Add Entry" on a post
- Fill form and submit
- Verify entry appears in table

**Step 7: Commit**

```bash
git add app/main.py app/templates/partials/
git commit -m "feat: add htmx actual entry creation API endpoints"
```

---

## Task 12: Analysis Page (Basic Structure)

**Files:**
- Modify: `app/main.py` (add GET `/analysis` route)
- Modify: `app/business_logic.py` (add analysis methods)
- Create: `app/templates/analysis.html`

**Step 1: Add analysis methods to business_logic.py**

```python
def get_budget_vs_actual_analysis(year: int) -> List[Dict[str, Any]]:
    """
    Calculate budget vs actual for all posts in a year.

    Returns list of dicts with post name, budget total, actual total, variance.
    """
    posts = get_all_posts()
    results = []

    for post in posts:
        # Get all 12 months of budget
        budgets = get_budget_entries(post.id, year)
        budget_total = sum(Decimal(str(b.amount)) for b in budgets)

        # Get all actuals for the year
        from datetime import date
        actuals = get_actual_entries(post.id, date(year, 1, 1), date(year, 12, 31))
        actual_total = sum(Decimal(str(a.amount)) for a in actuals)

        variance = budget_total - actual_total
        percentage = float((actual_total / budget_total * 100)) if budget_total > 0 else 0.0

        results.append({
            'post_name': post.name,
            'post_type': post.type,
            'budget': budget_total,
            'actual': actual_total,
            'variance': variance,
            'percentage': percentage
        })

    return results


def get_year_over_year_comparison(year1: int, year2: int) -> Dict[str, Any]:
    """
    Compare two years' income and expenses.
    """
    overview1 = get_year_overview(year1)
    overview2 = get_year_overview(year2)

    income_change = overview2['total_income'] - overview1['total_income']
    expense_change = overview2['total_expenses'] - overview1['total_expenses']

    return {
        'year1': year1,
        'year2': year2,
        'year1_data': overview1,
        'year2_data': overview2,
        'income_change': income_change,
        'expense_change': expense_change
    }
```

**Step 2: Add analysis route to main.py**

```python
from app.business_logic import get_budget_vs_actual_analysis, get_year_over_year_comparison

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
```

**Step 3: Create analysis.html template**

Create `app/templates/analysis.html`:

```html
{% extends "base.html" %}

{% block title %}Analysis - Moneybags{% endblock %}

{% block content %}
<div class="row mb-3">
    <div class="col-12">
        <h1>Analysis</h1>
        <p class="text-muted">Deep dive into your financial data</p>
    </div>
</div>

<!-- Analysis Mode Tabs -->
<ul class="nav nav-tabs mb-4" role="tablist">
    <li class="nav-item">
        <a class="nav-link active" data-bs-toggle="tab" href="#budget-vs-actual">Budget vs Actual</a>
    </li>
    <li class="nav-item">
        <a class="nav-link" data-bs-toggle="tab" href="#year-over-year">Year-over-Year</a>
    </li>
    <li class="nav-item">
        <a class="nav-link" data-bs-toggle="tab" href="#tag-analysis">By Tags</a>
    </li>
    <li class="nav-item">
        <a class="nav-link" data-bs-toggle="tab" href="#time-series">Time Series</a>
    </li>
</ul>

<!-- Tab Content -->
<div class="tab-content">
    <!-- Budget vs Actual Tab -->
    <div class="tab-pane fade show active" id="budget-vs-actual">
        <h3>Budget vs Actual - {{ year }}</h3>
        <table class="table">
            <thead>
                <tr>
                    <th>Post</th>
                    <th>Type</th>
                    <th>Budget</th>
                    <th>Actual</th>
                    <th>Variance</th>
                    <th>%</th>
                </tr>
            </thead>
            <tbody>
                {% for item in budget_analysis %}
                <tr>
                    <td>{{ item.post_name }}</td>
                    <td>{{ item.post_type }}</td>
                    <td>{{ "%.2f"|format(item.budget) }}</td>
                    <td>{{ "%.2f"|format(item.actual) }}</td>
                    <td class="{{ 'variance-positive' if item.variance > 0 else 'variance-negative' }}">
                        {{ "%.2f"|format(item.variance) }}
                    </td>
                    <td>{{ "%.1f"|format(item.percentage) }}%</td>
                </tr>
                {% endfor %}
            </tbody>
        </table>

        <!-- Chart placeholder -->
        <div class="chart-container">
            <canvas id="budgetVsActualChart"></canvas>
        </div>
    </div>

    <!-- Other tabs (placeholders for now) -->
    <div class="tab-pane fade" id="year-over-year">
        <h3>Year-over-Year Comparison</h3>
        <p>Coming soon...</p>
    </div>

    <div class="tab-pane fade" id="tag-analysis">
        <h3>Tag-based Analysis</h3>
        <p>Coming soon...</p>
    </div>

    <div class="tab-pane fade" id="time-series">
        <h3>Time Series Trends</h3>
        <p>Coming soon...</p>
    </div>
</div>
{% endblock %}
```

**Step 4: Test manually**

- Navigate to `/analysis`
- Verify budget vs actual table renders
- Check tab switching works

**Step 5: Commit**

```bash
git add app/main.py app/business_logic.py app/templates/analysis.html
git commit -m "feat: add analysis page with budget vs actual mode"
```

---

## Task 13: Configuration Page

**Files:**
- Modify: `app/main.py` (add GET `/config`, POST `/api/config/preference`)
- Create: `app/templates/config.html`

**Step 1: Add configuration route to main.py**

```python
from app.database_manager import get_or_create_preference, update_preference, get_all_tags, create_tag

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
```

**Step 2: Create config.html template**

Create `app/templates/config.html`:

```html
{% extends "base.html" %}

{% block title %}Configuration - Moneybags{% endblock %}

{% block content %}
<div class="row mb-3">
    <div class="col-12">
        <h1>Configuration</h1>
        <p class="text-muted">Manage your preferences and settings</p>
    </div>
</div>

<!-- Preferences Section -->
<div class="row mb-4">
    <div class="col-md-6">
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">Preferences</h5>

                <div class="mb-3">
                    <label class="form-label">Currency Notation</label>
                    <select class="form-select"
                            hx-post="/api/config/preference"
                            hx-trigger="change"
                            hx-vals='{"key": "currency_notation"}'
                            name="value">
                        <option value="USD" {{ 'selected' if currency.value == 'USD' else '' }}>USD</option>
                        <option value="EUR" {{ 'selected' if currency.value == 'EUR' else '' }}>EUR</option>
                        <option value="NOK" {{ 'selected' if currency.value == 'NOK' else '' }}>NOK</option>
                        <option value="GBP" {{ 'selected' if currency.value == 'GBP' else '' }}>GBP</option>
                    </select>
                </div>

                <div class="mb-3">
                    <label class="form-label">Date Format</label>
                    <select class="form-select"
                            hx-post="/api/config/preference"
                            hx-trigger="change"
                            hx-vals='{"key": "date_format"}'
                            name="value">
                        <option value="YYYY-MM-DD" {{ 'selected' if date_format.value == 'YYYY-MM-DD' else '' }}>YYYY-MM-DD</option>
                        <option value="DD/MM/YYYY" {{ 'selected' if date_format.value == 'DD/MM/YYYY' else '' }}>DD/MM/YYYY</option>
                        <option value="MM/DD/YYYY" {{ 'selected' if date_format.value == 'MM/DD/YYYY' else '' }}>MM/DD/YYYY</option>
                    </select>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Tags Management Section -->
<div class="row">
    <div class="col-md-8">
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">Tags</h5>

                <table class="table">
                    <thead>
                        <tr>
                            <th>Tag Name</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for tag in tags %}
                        <tr>
                            <td>{{ tag.name }}</td>
                            <td>
                                <button class="btn btn-sm btn-outline-danger">Delete</button>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>

                <button class="btn btn-primary mt-2">+ Add Tag</button>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

**Step 3: Test manually**

- Navigate to `/config`
- Change currency preference
- Verify it saves (reload page to check)

**Step 4: Commit**

```bash
git add app/main.py app/templates/config.html
git commit -m "feat: add configuration page with preferences"
```

---

## Execution Notes

These tasks build on the foundation from Tasks 1-9:
- Use htmx for all dynamic interactions
- Return partial templates from API endpoints
- Follow the established layered architecture
- Test manually (integration tests can come later)
- Commit frequently with descriptive messages

**Note:** Tasks 14-16 (Docker, Testing, Documentation) are infrastructure tasks and should be planned separately after core functionality is complete.
