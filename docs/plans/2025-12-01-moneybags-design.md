# Moneybags Application Design
**Date:** 2025-12-01
**Status:** Approved

## Overview
Moneybags is a single-user personal finance application for managing budgets and tracking actual income and expenses. The application provides monthly budget planning, dated actual entry tracking, comprehensive analysis across multiple dimensions, and a smooth, context-preserving user experience.

## Core Requirements

### User Model
- Single-user application (personal installation)
- No authentication required
- One person per installation

### Budget Granularity
- **Budget**: Monthly breakdown (12 budget values per year per post)
- **Actuals**: Each entry has a specific date/timestamp for pattern analysis
- Enables seasonal budget planning while tracking granular spending patterns

### Data Organization
- Posts organized as flat list with tags
- Tags enable cross-year analysis even when post names evolve
- Example: "Netflix" [Streaming] (2024) → "Netflix + Disney+" [Streaming] (2025)
- Analysis by "Streaming" tag works across both years

### Income vs Expense Separation
- Income and Expenses maintained as separate types
- Linkable for combined cash flow analysis
- Clear separation for data entry, flexible views for analysis

### Analysis Capabilities
1. Budget vs Actual (same year) - variance analysis
2. Year-over-year comparison - trends and growth
3. Tag-based grouping - category aggregation across years
4. Time-series trends - pattern identification over time

## Database Architecture

### Approach: Flexible Budget/Actual Entries
Posts are year-agnostic master definitions. Budget and Actual entries link posts to specific time periods.

**Benefits:**
- Posts defined once, used across all years
- Tags provide automatic cross-year continuity
- Clean separation of definitions from time-series data
- Simplified cross-year analysis

### Database Tables

#### 1. Post
Master definition of budget line items.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| name | String | Display name (e.g., "Rent", "Salary") |
| type | ENUM | 'income' or 'expense' |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last modification timestamp |

#### 2. Tag
Reusable labels for grouping posts.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| name | String | Tag name (e.g., "Housing", "Fixed") |

#### 3. PostTag
Many-to-many relationship between Posts and Tags.

| Field | Type | Description |
|-------|------|-------------|
| post_id | UUID | Foreign key to Post |
| tag_id | UUID | Foreign key to Tag |

#### 4. BudgetEntry
Monthly budget values for posts.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| post_id | UUID | Foreign key to Post |
| year | Integer | Budget year (e.g., 2024, 2025) |
| month | Integer | Month (1-12) |
| amount | Decimal | Budgeted amount |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last modification timestamp |

**Constraint:** Unique combination of (post_id, year, month)

#### 5. ActualEntry
Real income/expenses with specific dates.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| post_id | UUID | Foreign key to Post |
| date | Date | When transaction occurred |
| amount | Decimal | Actual amount |
| comment | Text | Optional note |
| created_at | DateTime | Creation timestamp |
| updated_at | DateTime | Last modification timestamp |

#### 6. UserPreference
Application configuration settings.

| Field | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| key | String | Setting name (e.g., "currency_notation") |
| value | String | Setting value (e.g., "NOK", "USD") |

### Database Design Principles
- SQLite is purely storage, zero logic
- No triggers, stored procedures, or computed columns
- No database-level constraints beyond basic FK relationships
- All calculations, aggregations, validations in Python (business_logic.py)
- Manual UUID generation in backend before insert
- No PeeWee backrefs (explicit relationship management)

## Application Architecture

### Layered Structure

#### 1. main.py (Router Layer)
- FastAPI route definitions only
- Receives HTTP requests (GET/POST with htmx)
- Calls business_logic.py methods
- Returns HTML templates or htmx partial responses
- **Zero business logic** - pure routing

#### 2. business_logic.py (Business Layer)
- All calculations and business rules
- Orchestrates multi-table operations
- Never directly touches database models
- Only calls database_manager.py methods

Example methods:
- `calculate_monthly_variance(post_id, year, month)` - budget vs actual difference
- `get_year_overview(year)` - aggregate all posts for dashboard
- `get_tag_analysis(tag_id, year_range)` - cross-year tag grouping
- `get_time_series_data(post_id, date_range)` - pattern analysis data

#### 3. database_manager.py (Data Access Layer)
- All CRUD operations using PeeWee ORM
- All database queries and joins
- Returns data objects/dictionaries to business_logic

Example methods:
- `create_post(name, type, tags)`
- `get_budget_entries(post_id, year)`
- `create_actual_entry(post_id, date, amount, comment)`
- `get_posts_by_tag(tag_id)`
- `get_actuals_by_date_range(post_id, start_date, end_date)`

#### 4. database_model.py (ORM Models)
- PeeWee model definitions for all 6 tables
- No backrefs (manual relationship management)
- Basic field definitions only

#### 5. utils.py (Helpers)
- UUID generation
- Date formatting helpers
- Currency formatting based on user preference
- Common utility functions

### Configuration
- uvicorn_log_config.ini - Logging configuration
- All logging (FastAPI and Python) uniform and logged to Docker container
- Support both local development and Docker deployment

## Frontend Architecture

### Tech Stack
- **Bootstrap** - Responsive CSS framework (mobile + desktop)
- **htmx** - Dynamic updates without page refreshes
- **Vanilla JS** - All JavaScript in single app.js file
- **Chart.js** - Data visualizations
- **TomSelect** - Advanced input with tags
- **Tempus Dominus** - Date/time picker

### Template Structure

#### base.html (Master Layout)
- HTML structure, navbar, footer
- Links to single CSS file (styles.css)
- Links to single JS file (app.js)
- Bootstrap CSS/JS, htmx, Chart.js libraries
- Defines content blocks for page templates

#### Page Templates (extend base.html)
1. **dashboard.html** - Overview page
2. **budget.html** - Budget and actuals entry
3. **analysis.html** - Deep dive analytics
4. **config.html** - User preferences

#### Partial Templates (for htmx swaps)
- `_post_row.html` - Single post with budget/actual fields
- `_monthly_chart.html` - Chart component
- `_variance_table.html` - Budget vs actual table
- `_actual_entry_row.html` - Individual actual entry
- Return HTML fragments, not full pages

### htmx Interaction Pattern
- User edits budget value → htmx POST → server saves → returns updated partial
- User adds actual entry → htmx POST → server saves → returns updated post row with totals
- Chart data updates → htmx fetches JSON → Chart.js re-renders
- **No page refresh, no scroll-to-top, context maintained**

### Form Elements
- **TomSelect**: Post selection with tag filtering
- **Tempus Dominus**: Date picking for actual entries
- **Bootstrap inputs**: Amounts, comments, configuration
- Auto-save with htmx debounce on budget fields

## Application Sections

### 1. Dashboard (dashboard.html)

**Purpose:** At-a-glance financial overview

**Content:**
- Current month overview: Budget vs Actual summary
- Year-to-date totals: Income, Expenses, Net savings
- Visual highlights using Chart.js:
  - Monthly variance chart (budget vs actual across 12 months)
  - Income vs Expense trend line
  - Top spending categories by tag (pie chart)
- Recent actual entries list (last 10 transactions)

**Interactions:**
- All data updates via htmx
- Charts re-render smoothly without page refresh
- Click chart elements to drill into details

### 2. Budget & Actuals (budget.html)

**Purpose:** Primary data entry interface

**Layout:** Horizontal split
- **Top Section - Income** (compact, always visible)
  - 1-2 income posts (Salary, Bonus, etc.)
  - 12 monthly budget fields + actual entries per post
  - Minimal vertical space

- **Bottom Section - Expenses** (scrollable, main focus)
  - Many expense posts (Rent, Groceries, Insurance, etc.)
  - 12 monthly budget fields + actual entries per post
  - Uses full screen width effectively

**Features per Post:**
- 12 monthly budget input fields (Jan-Dec)
- List of actual entries with date, amount, comment
- Running total: sum of actuals vs monthly budget
- Color coding: green (under budget), red (over budget)

**Interactions:**
- Add new actual entry form (htmx POST, partial update)
- Create new post button (modal with TomSelect for tags)
- Monthly totals auto-update as you type (htmx debounce)
- Delete/edit actual entries inline

### 3. Analysis (analysis.html)

**Purpose:** Deep dive into financial data

**Filter Controls:**
- Year range selector
- Tag filter (multi-select)
- Post filter (multi-select)
- Income/Expense/Both toggle

**Four Analysis Modes** (tabs):

1. **Budget vs Actual**
   - Variance table (budgeted, actual, difference, %)
   - Bar chart comparing budget and actual
   - Drill-down to see specific actual entries

2. **Year-over-year**
   - Compare selected years (e.g., 2024 vs 2025)
   - Line chart showing trends
   - Percentage change calculations
   - Identify growth patterns

3. **Tag-based Grouping**
   - Aggregate all posts by tag
   - Pie chart showing category distribution
   - Table with tag totals
   - Works across all years automatically

4. **Time-series Trends**
   - Plot actual entries over time
   - Spot patterns (e.g., "groceries spike before holidays")
   - Moving averages
   - Seasonal analysis

**Export:**
- CSV download of filtered/analyzed data
- Include date range, filters applied in filename

### 4. Configuration (config.html)

**Purpose:** User preferences and system settings

**Settings:**
- Currency notation (USD, EUR, NOK, etc.)
- Date format preference (YYYY-MM-DD, DD/MM/YYYY, etc.)
- Dashboard default year
- First day of week (for date pickers)

**Tag Management:**
- List all tags
- Create new tags
- Rename existing tags
- Delete unused tags (with warning if in use)
- Merge tags functionality

**Data Management:**
- Export all data (backup)
- Import data (restore)

**Interactions:**
- Simple form layout
- htmx autosave on change
- Confirmation dialogs for destructive actions

## User Experience Principles

### Smooth Interactions
- No full page reloads
- Context preservation (scroll position, form state)
- Optimistic UI updates with rollback on error
- Loading indicators for async operations
- Debounced inputs to reduce server requests

### Responsive Design
- Mobile-first Bootstrap layout
- Touch-friendly tap targets on mobile
- Collapsible sections for small screens
- Horizontal scrolling for wide tables on mobile
- Chart.js responsive mode

### Data Integrity
- Client-side validation before htmx submission
- Server-side validation in business_logic.py
- Clear error messages inline (no page-level alerts)
- Confirmation for destructive actions (delete post, delete actual entry)

### Performance
- Lazy load actual entries (paginated lists)
- Cache frequently accessed data in business_logic
- Minimize database queries through smart aggregation
- Progressive chart rendering for large datasets

## Success Criteria

1. **Data Integrity**: Cross-year analysis works seamlessly via tags
2. **Smooth UX**: No context loss, instant feedback, maintained scroll position
3. **Responsive**: Works perfectly on mobile and desktop
4. **Analytical Power**: All four analysis modes provide actionable insights
5. **Performance**: Sub-second response times for all interactions
6. **Maintainability**: Clear separation of concerns across layers

## Next Steps

1. Set up git worktree for isolated development
2. Create detailed implementation plan with task breakdown
3. Begin implementation following test-driven development practices
