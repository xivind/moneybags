# Budget Progress Widget - Design Document

**Date:** 2025-12-30
**Status:** Approved for implementation

## Purpose

Help users quickly see how their spending compares to budget for all expense categories, both for the current month and year-to-date.

## Overview

A new dashboard widget showing budget vs actual spending with visual progress bars. Users can switch between "This Month" and "This Year" views using tabs.

## Widget Structure

- **Location:** Dashboard page, new widget alongside existing three widgets
- **Title:** "Budget Progress" with icon (`bi-speedometer` or `bi-graph-up`)
- **Layout:** Two-tab interface
  - Tab 1: "This Month" (default)
  - Tab 2: "This Year"
- **Content:** Scrollable list of progress bars (max-height with overflow-y-auto)
- **Scope:** All expense categories with budget entries (no income categories)

## Visual Design

### Each Category Row Displays

- Category name (left-aligned)
- Bootstrap progress bar (fills most of row width)
- Percentage text (right-aligned, e.g., "60%" or "105%")

### Progress Bar Behavior

- Fixed height (Bootstrap default `progress` class)
- Bar width capped at 100% (uniform length, never overflows)
- **Under budget:** Green bar (`bg-success`)
- **At/over budget:** Red bar (`bg-danger`)
- When over budget: Add text below bar "Over by kr 200" in small red/muted text

### Tooltip on Hover

- Shows on mouseover for entire row
- Bootstrap tooltip component
- Content format: `"Budget: kr 1,000 | Actual: kr 800"`
- Simple pipe-separated format

### Responsive Behavior

- Mobile: Full-width card, stacks naturally
- Progress bars adapt to screen width
- Tooltips work on touch devices (tap to show)

## Data Flow

### Data Sources

- Current month/year: From JavaScript state (`currentMonth`, `currentYear`)
- Categories: Filter from `allCategories` array where `category_type = 'expense'`
- Budget entries: From `/api/budget/{year}` endpoint
- Transactions: From `/api/budget/{year}` endpoint

### API Endpoints

- **Existing only:** `GET /api/budget/{year}`
- No new backend endpoints needed

### Calculation Logic

**For "This Month" tab:**
- Sum transactions where `month === currentMonth`
- Compare to budget entry for current month
- Calculate: `percentage = (actual / budget) * 100`
- Calculate: `difference = actual - budget`

**For "This Year" tab:**
- Sum all transactions for year (January through December)
- Sum all budget entries for year (12 months)
- Calculate percentage and difference same as above

**Color logic:**
- Green if `percentage < 100%`
- Red if `percentage >= 100%`

**"Over by" text:**
- Only show when `percentage >= 100%`
- Format: "Over by {formatted amount}"

### Loading Strategy

- Load on dashboard page initialization
- Call existing `/api/budget/{currentYear}` endpoint
- Process data in JavaScript
- Populate both tabs at once
- Initialize Bootstrap tooltips after rendering

## Implementation Details

### HTML (dashboard.html)

**Structure:**
```html
<div class="col-lg-3">
  <div class="card h-100">
    <div class="card-body">
      <h5 class="card-title">
        <i class="bi bi-speedometer me-2"></i>Budget Progress
      </h5>

      <!-- Nav tabs -->
      <ul class="nav nav-tabs mb-3">
        <li class="nav-item">
          <a class="nav-link active" data-bs-toggle="tab" href="#month-progress">This Month</a>
        </li>
        <li class="nav-item">
          <a class="nav-link" data-bs-toggle="tab" href="#year-progress">This Year</a>
        </li>
      </ul>

      <!-- Tab content -->
      <div class="tab-content">
        <div class="tab-pane fade show active" id="month-progress">
          <div class="budget-progress-list">
            <!-- Dynamically generated progress bars -->
          </div>
        </div>
        <div class="tab-pane fade" id="year-progress">
          <div class="budget-progress-list">
            <!-- Dynamically generated progress bars -->
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
```

**Constraints:**
- NO inline styles
- NO inline scripts
- NO onclick handlers
- Structure and Jinja2 logic only

### JavaScript (static/js/app.js)

**New function:** `loadBudgetProgress()`

**Responsibilities:**
- Fetch data from `/api/budget/{currentYear}`
- Filter expense categories only
- Calculate monthly totals (current month transactions)
- Calculate yearly totals (all transactions)
- Generate HTML for both tabs
- Initialize Bootstrap tooltips

**Integration:**
- Call from dashboard page initialization
- Use existing `apiCall()` wrapper
- Use existing state: `currentYear`, `currentMonth`, `allCategories`, `currentCurrencyFormat`
- Use existing currency formatting function

**Tab switching:**
- Handled by Bootstrap's built-in tab functionality
- No custom JavaScript needed

### CSS (static/css/custom.css)

**New classes:**
- `.budget-progress-list` - Scrollable container (max-height: 400px, overflow-y: auto)
- `.progress-row` - Spacing between rows (margin-bottom)
- `.over-budget-text` - Styling for "Over by X" text (small font, red/muted color)

**Constraints:**
- ALL styling in this file
- No inline styles in HTML

### Currency Formatting

- Use existing `currentCurrencyFormat` from config API
- Format: Symbol before amount with space (e.g., "kr 1 234")
- Thousand separator: space
- No decimals (amounts stored as integers)
- Use existing formatting helper or create one following same pattern

## Backend Changes

**None required.**

All data available from existing `/api/budget/{year}` endpoint.

## Architectural Compliance

✅ **Template:** Structure only, no inline styles/scripts
✅ **JavaScript:** All code in `static/js/app.js`
✅ **CSS:** All styles in `static/css/custom.css`
✅ **Backend:** No changes (uses existing API)
✅ **Currency:** Follows existing format pattern
✅ **Clean architecture:** Frontend only changes

## Success Criteria

- Widget displays on dashboard alongside existing three widgets
- Tabs switch between "This Month" and "This Year" views
- Progress bars show accurate budget vs actual comparison
- Green bars for under budget, red for over budget
- "Over by X" text appears when over budget
- Tooltips show budget and actual amounts on hover
- Scrollable list handles many categories gracefully
- Mobile responsive
- No inline styles or scripts
- Follows all architectural constraints in CLAUDE.md

## Future Enhancements (Not in Scope)

- Click category to drill down to transactions
- Filter by category type or tags
- Show income categories separately
- Export budget progress report
- Historical comparison (vs last month/year)
