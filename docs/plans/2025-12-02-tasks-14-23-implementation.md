# Tasks 14-23 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement these tasks.

**Goal:** Complete the remaining high and medium priority features to make Moneybags production-ready.

**Architecture:** Continue the layered structure with FastAPI routes, business logic, and htmx interactions.

**Tech Stack:** Python, FastAPI, htmx, Bootstrap, Chart.js

---

## HIGH PRIORITY TASKS

## Task 14: Post Creation Modals (Income/Expense)

**Files:**
- Modify: `app/main.py` (add GET `/api/post/create-form`, POST `/api/post/create`)
- Create: `app/templates/partials/_post_create_form.html`
- Modify: `app/templates/budget.html` (update modal-content div)

**Step 1: Add post creation form endpoint**

```python
@app.get("/api/post/create-form")
async def post_create_form(request: Request, post_type: str):
    """Return form for creating a new post (income or expense)."""
    from app.database_manager import get_all_tags

    tags = get_all_tags()
    return templates.TemplateResponse("partials/_post_create_form.html", {
        "request": request,
        "post_type": post_type,
        "tags": tags
    })
```

**Step 2: Add post creation endpoint**

```python
@app.post("/api/post/create")
async def create_new_post(
    request: Request,
    name: str = Form(...),
    post_type: str = Form(...),
    tag_ids: list = Form([])
):
    """Create a new post with tags."""
    from app.business_logic import create_post_with_tags

    post = create_post_with_tags(name, post_type, tag_ids)

    # Redirect to budget page (full page reload to show new post)
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/budget", status_code=303)
```

**Step 3: Create post creation form partial**

Create `app/templates/partials/_post_create_form.html`:

```html
<div class="modal fade show" style="display: block;" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Create New {{ post_type.title() }} Post</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <form hx-post="/api/post/create" hx-swap="none">
                <div class="modal-body">
                    <input type="hidden" name="post_type" value="{{ post_type }}">

                    <div class="mb-3">
                        <label class="form-label">Post Name</label>
                        <input type="text" name="name" class="form-control"
                               placeholder="e.g., Salary, Rent, Groceries" required>
                    </div>

                    <div class="mb-3">
                        <label class="form-label">Tags (optional)</label>
                        <select name="tag_ids" class="form-select tomselect" multiple>
                            {% for tag in tags %}
                            <option value="{{ tag.id }}">{{ tag.name }}</option>
                            {% endfor %}
                        </select>
                        <small class="text-muted">Select existing tags or leave empty</small>
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                    <button type="submit" class="btn btn-primary">Create Post</button>
                </div>
            </form>
        </div>
    </div>
</div>

<script>
// Initialize TomSelect on modal load
if (typeof TomSelect !== 'undefined') {
    document.querySelectorAll('.tomselect').forEach(function(el) {
        new TomSelect(el, {
            plugins: ['remove_button'],
            create: false
        });
    });
}
</script>
```

**Step 4: Update budget.html to include modal container**

Add before the closing `{% endblock %}`:

```html
<!-- Modal placeholder -->
<div id="modal-content"></div>
```

**Step 5: Test manually**

- Navigate to `/budget`
- Click "Add Income Post" or "Add Expense Post"
- Fill form and submit
- Verify post appears in budget page

**Step 6: Commit**

```bash
git add app/main.py app/templates/partials/_post_create_form.html app/templates/budget.html
git commit -m "feat: add post creation modals with tag selection"
```

---

## Task 15: Chart.js Data Integration

**Files:**
- Modify: `app/business_logic.py` (add get_monthly_chart_data)
- Modify: `app/main.py` (update dashboard route)
- Modify: `app/templates/dashboard.html` (populate chart with data)

**Step 1: Add chart data method to business_logic**

```python
def get_monthly_chart_data(year: int) -> Dict[str, List[float]]:
    """
    Get monthly income and expense totals for chart.

    Returns dict with 'income' and 'expenses' lists (12 values each).
    """
    posts = get_all_posts()

    income_by_month = [Decimal('0')] * 12
    expenses_by_month = [Decimal('0')] * 12

    for post in posts:
        for month in range(1, 13):
            start_date = date(year, month, 1)
            if month == 12:
                end_date = date(year, 12, 31)
            else:
                from calendar import monthrange
                last_day = monthrange(year, month)[1]
                end_date = date(year, month, last_day)

            actuals = get_actual_entries(post.id, start_date, end_date)
            total = sum(Decimal(str(a.amount)) for a in actuals)

            if post.type == 'income':
                income_by_month[month - 1] += total
            else:
                expenses_by_month[month - 1] += total

    return {
        'income': [float(v) for v in income_by_month],
        'expenses': [float(v) for v in expenses_by_month]
    }
```

**Step 2: Update dashboard route**

```python
from app.business_logic import get_dashboard_data, get_monthly_chart_data

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
```

**Step 3: Update dashboard.html chart script**

Replace the empty data arrays:

```html
<script>
// Basic chart initialization
const ctx = document.getElementById('monthlyChart').getContext('2d');
const monthlyChart = new Chart(ctx, {
    type: 'bar',
    data: {
        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
        datasets: [{
            label: 'Income',
            data: {{ chart_data.income | tojson }},
            backgroundColor: 'rgba(40, 167, 69, 0.5)'
        }, {
            label: 'Expenses',
            data: {{ chart_data.expenses | tojson }},
            backgroundColor: 'rgba(220, 53, 69, 0.5)'
        }]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            y: {
                beginAtZero: true
            }
        }
    }
});
</script>
```

**Step 4: Test manually**

- Add some posts and actual entries
- Navigate to dashboard
- Verify chart displays with actual data

**Step 5: Commit**

```bash
git add app/business_logic.py app/main.py app/templates/dashboard.html
git commit -m "feat: integrate Chart.js with actual monthly data"
```

---

## Task 16: Tag CRUD Operations

**Files:**
- Modify: `app/main.py` (add POST `/api/tag/create`, DELETE `/api/tag/{tag_id}`)
- Modify: `app/templates/config.html` (add forms and htmx attributes)
- Create: `app/templates/partials/_tag_row.html`

**Step 1: Add tag creation endpoint**

```python
@app.post("/api/tag/create")
async def create_new_tag(
    request: Request,
    name: str = Form(...)
):
    """Create a new tag."""
    from app.utils import generate_uuid

    tag_id = generate_uuid()
    tag = create_tag(tag_id, name)

    # Return updated tags table
    tags = get_all_tags()
    return templates.TemplateResponse("partials/_tag_row.html", {
        "request": request,
        "tag": tag
    })
```

**Step 2: Add tag delete endpoint**

```python
@app.delete("/api/tag/{tag_id}")
async def delete_tag(tag_id: str):
    """Delete a tag."""
    from app.database_manager import delete_tag as db_delete_tag

    db_delete_tag(tag_id)
    return {"status": "success"}
```

**Note:** Need to add `delete_tag()` to database_manager.py:

```python
def delete_tag(tag_id: str) -> None:
    """
    Delete a tag.

    Args:
        tag_id: Tag identifier
    """
    # Remove all post-tag relationships first
    PostTag.delete().where(PostTag.tag == tag_id).execute()

    # Then delete the tag
    tag = Tag.get_by_id(tag_id)
    tag.delete_instance()
```

**Step 3: Create tag row partial**

Create `app/templates/partials/_tag_row.html`:

```html
<tr id="tag-{{ tag.id }}">
    <td>{{ tag.name }}</td>
    <td>
        <button class="btn btn-sm btn-outline-danger"
                hx-delete="/api/tag/{{ tag.id }}"
                hx-target="#tag-{{ tag.id }}"
                hx-swap="outerHTML swap:1s"
                hx-confirm="Delete tag '{{ tag.name }}'?">
            Delete
        </button>
    </td>
</tr>
```

**Step 4: Update config.html**

Modify the tags table and add form:

```html
<table class="table" id="tags-table">
    <thead>
        <tr>
            <th>Tag Name</th>
            <th>Actions</th>
        </tr>
    </thead>
    <tbody id="tags-tbody">
        {% for tag in tags %}
            {% include "partials/_tag_row.html" with context %}
        {% endfor %}
    </tbody>
</table>

<form hx-post="/api/tag/create" hx-target="#tags-tbody" hx-swap="beforeend">
    <div class="input-group">
        <input type="text" name="name" class="form-control"
               placeholder="New tag name" required>
        <button type="submit" class="btn btn-primary">+ Add Tag</button>
    </div>
</form>
```

**Step 5: Test manually**

- Navigate to `/config`
- Add a new tag
- Delete a tag
- Verify changes persist

**Step 6: Commit**

```bash
git add app/main.py app/database_manager.py app/templates/config.html app/templates/partials/_tag_row.html
git commit -m "feat: implement tag CRUD operations"
```

---

## Task 17: Delete Actual Entry Endpoint

**Files:**
- Modify: `app/main.py` (add DELETE `/api/actual/{entry_id}`)

**Step 1: Add delete endpoint**

```python
@app.delete("/api/actual/{entry_id}")
async def delete_actual_entry(entry_id: str):
    """Delete an actual entry."""
    from app.database_manager import delete_actual_entry as db_delete

    db_delete(entry_id)
    return {"status": "success"}
```

**Step 2: Test manually**

- Navigate to `/budget`
- Add an actual entry
- Click delete button
- Verify entry is removed

**Step 3: Commit**

```bash
git add app/main.py
git commit -m "feat: add delete endpoint for actual entries"
```

---

## Task 18: htmx Loading Indicators

**Files:**
- Modify: `app/static/css/styles.css` (enhance htmx indicator styles)
- Modify: `app/templates/partials/_budget_input.html` (add indicator)
- Modify: `app/templates/partials/_actual_entry_form.html` (add indicator)

**Step 1: Enhance CSS for loading indicators**

Add to `app/static/css/styles.css`:

```css
/* htmx loading indicators */
.htmx-indicator {
    display: none;
}

.htmx-request .htmx-indicator {
    display: inline-block;
}

.htmx-request.htmx-indicator {
    display: inline-block;
}

/* Spinner animation */
.spinner-border-sm {
    width: 1rem;
    height: 1rem;
    border-width: 0.2em;
}

/* Loading overlay for forms */
.loading-overlay {
    display: none;
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(255, 255, 255, 0.8);
    z-index: 1000;
    align-items: center;
    justify-content: center;
}

.htmx-request .loading-overlay {
    display: flex;
}
```

**Step 2: Add indicators to forms**

Update form buttons to include spinners:

```html
<button type="submit" class="btn btn-primary">
    <span class="htmx-indicator spinner-border spinner-border-sm me-2" role="status"></span>
    Save Entry
</button>
```

**Step 3: Test manually**

- Trigger htmx requests
- Verify spinners appear during requests

**Step 4: Commit**

```bash
git add app/static/css/styles.css app/templates/partials/
git commit -m "feat: add loading indicators for htmx requests"
```

---

## MEDIUM PRIORITY TASKS

## Task 19: Remaining Analysis Modes

**Files:**
- Modify: `app/business_logic.py` (add get_tag_analysis, get_time_series_data)
- Modify: `app/main.py` (update analysis route)
- Modify: `app/templates/analysis.html` (implement other tabs)

**Implementation similar to Task 12, but for the remaining 3 analysis modes.**

---

## Task 20: Form Validation

**Files:**
- Modify: `app/main.py` (add validation logic)
- Modify: templates (add client-side validation)

**Add validation for:**
- Budget amounts (>= 0)
- Dates (valid format, not future)
- Post names (not empty, unique)
- Tag names (not empty, unique)

---

## Task 21: Error Handling & User Feedback

**Files:**
- Modify: `app/main.py` (add try/except blocks)
- Create: `app/templates/partials/_error_message.html`
- Modify: `app/static/js/app.js` (add toast notifications)

**Add:**
- Try/except around database operations
- User-friendly error messages
- Toast notifications for success/error

---

## Task 22: Data Export (CSV)

**Files:**
- Modify: `app/main.py` (add GET `/api/export/csv`)
- Modify: `app/templates/analysis.html` (add export button)

**Export functionality for:**
- All posts
- Budget entries
- Actual entries
- Analysis results

---

## Task 23: Docker Configuration

**Files:**
- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Create: `.dockerignore`

**Setup for:**
- Python 3.11+ base image
- Install dependencies
- Run uvicorn
- Volume for database persistence
- Environment variable configuration

---

## Execution Strategy

Execute tasks 14-18 (High Priority) first, then 19-23 (Medium Priority).
Use subagent-driven development with code review after each task.
Test thoroughly and commit frequently.
