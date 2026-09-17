# Graph Report - moneybags  (2026-09-17)

## Corpus Check
- 40 files · ~55,610 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 731 nodes · 1620 edges · 53 communities (40 shown, 13 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 106 edges (avg confidence: 0.92)
- Token cost: 308,755 input · 0 output

## Community Hubs (Navigation)
- SuperSaver Feature
- Category Deletion & Architecture Rationale
- Business Logic Core Operations
- Budget Calculation JS
- API GET Routes
- Excel Import Feature
- Frontend CRUD Actions
- Database Models
- Import Parsing Logic
- Database Manager CRUD
- API Create/Update Routes
- Database Config Management
- Frontend Data Loading
- Delete API Routes
- Recurring Payments Config
- Recurring Categories UI
- Application Overview (CLAUDE.md/README)
- API Update Routes
- Dashboard Widgets JS
- Payee Management
- SuperSaver Calendar UI
- Database Migrations
- Dashboard Widget Design & Templates
- Frontend Library Stack
- Payee Creation & Tests
- Import Validation
- Expense Totals & Date Utils
- Category Update
- Docker Deployment
- Connection Retry Logic
- Currency Settings JS
- SuperSaver Templates
- Budget Progress Widget
- Available Years API
- Expense Category Breakdown
- Recent Transactions API
- DB Connection Test
- App Startup Event
- Business Logic Test Fixture
- Database Manager Test Fixture
- Transaction Execution Wrapper
- Query Timing Logger
- Web Framework Dependencies
- ORM & DB Driver Dependencies
- Test Package Init
- Currency Format Standard
- Moneybags Package
- Templating Dependency
- Testing Framework Dependency
- Date Utility Dependency
- Multipart Upload Dependency
- Favicon Icon
- Application Logo

## God Nodes (most connected - your core abstractions)
1. `apiCall()` - 48 edges
2. `with_retry()` - 41 edges
3. `with_transaction()` - 25 edges
4. `showLoading()` - 24 edges
5. `hideLoading()` - 24 edges
6. `Transaction` - 23 edges
7. `Category` - 21 edges
8. `Payee` - 20 edges
9. `BudgetEntry` - 20 edges
10. `showSuccess()` - 19 edges

## Surprising Connections (you probably didn't know these)
- `Recurring Payments Widget Configuration Design` --semantically_similar_to--> `Configuration Caching`  [INFERRED] [semantically similar]
  docs/plans/2025-12-30-recurring-payments-configuration.md → CLAUDE.md
- `Recurring Payments Tracker Widget (Design)` --references--> `get_recurring_payment_status()`  [EXTRACTED]
  docs/plans/2025-12-29-dashboard-widgets-design.md → business_logic.py
- `Recurring Payments Widget Configuration Design` --references--> `get_recurring_payment_status()`  [EXTRACTED]
  docs/plans/2025-12-30-recurring-payments-configuration.md → business_logic.py
- `Recent Transactions Widget (Design)` --references--> `get_recent_transactions()`  [EXTRACTED]
  docs/plans/2025-12-29-dashboard-widgets-design.md → business_logic.py
- `Migration Strategy` --references--> `create_tables_if_not_exist()`  [EXTRACTED]
  migrations/README.md → database_manager.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Clean Architecture Layering (main -> business_logic -> database_manager -> models -> database)** — main, business_logic, database_manager, database_model [EXTRACTED 1.00]
- **Dashboard Widget Implementation Pattern (business_logic function -> main API route -> dashboard.html card -> app.js render)** — docs_plans_2025_12_29_dashboard_widgets_design_recurring_payments_widget, docs_plans_2025_12_29_dashboard_widgets_design_recent_transactions_widget, business_logic, main, templates_dashboard, static_js_app [INFERRED 0.85]
- **Base Template Shared Frontend Dependencies** — templates_base, lib_bootstrap, lib_tomselect, lib_tempus_dominus, lib_chartjs, static_css_custom, static_js_app [EXTRACTED 1.00]

## Communities (53 total, 13 thin omitted)

### Community 0 - "SuperSaver Feature"
Cohesion: 0.06
Nodes (56): Supersaver-specific categories (independent from budget categories). Each…, Supersaver entries (savings deposits only). Records savings deposits for…, Supersaver, SupersaverCategory, create_supersaver_category(), Create new supersaver category. Request body: { "name": "Emergency Fund" }, create_supersaver_category(), delete_supersaver_category() (+48 more)

### Community 1 - "Category Deletion & Architecture Rationale"
Cohesion: 0.07
Nodes (45): delete_category(), get_all_categories(), Get all categories with usage information. Returns list with category info +…, Delete category. Business logic: - Validate category_id exists - Check NOT in…, Clean Architecture Pattern, Connection Pooling (PooledMySQLDatabase), category_has_budget_entries(), category_has_budget_entries_for_year() (+37 more)

### Community 2 - "Business Logic Core Operations"
Cohesion: 0.09
Nodes (41): add_category_to_template(), calculate_category_trends(), copy_budget_template(), create_category(), create_transaction(), business_logic._ensure_import_payee(), business_logic._extract_amounts_from_formula(), get_budget_data_for_year() (+33 more)

### Community 3 - "Budget Calculation JS"
Cohesion: 0.07
Nodes (28): allCategories, availableYears, calculateBudgetYearTotal(), calculateMonthlyBudgetBalance(), calculateMonthlyDifference(), calculateMonthlyResult(), calculateResultYearTotal(), currentMonth (+20 more)

### Community 4 - "API GET Routes"
Cohesion: 0.08
Nodes (36): get_all_payees(), Get all payees with usage statistics. Returns list with payee info + statistics…, Standard API Response Format, get, config_page(), dashboard(), get_budget_data(), get_budget_template() (+28 more)

### Community 5 - "Excel Import Feature"
Cohesion: 0.07
Nodes (35): Excel Import Feature, Transaction Wrapping (@with_transaction), Import Data Integrity Validation, Import Edge Case Handling, Google Sheets Import Feature (Design), 5-Step Import User Workflow, Google Sheets Import TDD Implementation Plan, Import Functionality Refactoring Design (+27 more)

### Community 6 - "Frontend CRUD Actions"
Cohesion: 0.15
Nodes (35): addCategoryToYear(), addRecurringCategory(), changeYear(), createCategory(), deleteBudgetEntry(), deleteBudgetEntryApi(), deleteCategory(), deleteCategoryApi() (+27 more)

### Community 7 - "Database Models"
Cohesion: 0.14
Nodes (31): close_connection(), get_recent_transactions(), get_transactions_by_date_range(), get_transactions_by_year(), Close database connection., Get all transactions for year (with eager-loaded payees and categories to avoid…, Get most recent transactions (with eager-loaded payees and categories to avoid…, Get all transactions within date range (with eager-loaded payees and… (+23 more)

### Community 8 - "Import Parsing Logic"
Cohesion: 0.06
Nodes (32): _extract_amounts_from_formula(), parse_excel_file(), _parse_hovedark_format(), _parse_original_format(), Parse Google Sheets Excel file and extract budget/actual data. Supports two…, Parse Hovedark Excel format. Structure: - Sheet: "Hovedark" - Month columns:…, Extract individual amounts from Excel formula or value. Strict validation -…, Parse original Excel format (active sheet with columns C-N). (+24 more)

### Community 9 - "Database Manager CRUD"
Cohesion: 0.08
Nodes (31): business_logic.import_budget_and_transactions(), Remove category from year's template. Business logic: - Validate entry exists -…, remove_category_from_template(), budget_template_exists(), create_budget_entry(), create_budget_template(), create_category(), create_or_update_budget_entry() (+23 more)

### Community 10 - "API Create/Update Routes"
Cohesion: 0.09
Nodes (29): add_category_to_template(), budget_page(), copy_budget_template(), create_category(), create_payee(), create_supersaver_entry(), create_transaction(), execute_import() (+21 more)

### Community 11 - "Database Config Management"
Cohesion: 0.08
Nodes (26): _get_config_file_path(), initialize_database(), _invalidate_config_cache(), load_database_config(), Initialize database connection and create tables if needed., Invalidate configuration cache., Update list of category IDs for recurring payment monitoring. Args:…, Update configuration settings. Business logic: - For each key-value in… (+18 more)

### Community 12 - "Frontend Data Loading"
Cohesion: 0.16
Nodes (18): apiCall(), createPayee(), createTransaction(), deletePayee(), deletePayeeApi(), formatDate(), loadAllTrends(), loadCategoryTrends() (+10 more)

### Community 13 - "Delete API Routes"
Cohesion: 0.12
Nodes (17): delete_budget_entry(), delete_transaction(), Delete budget entry. Business logic: - Validate entry_id exists - Delete budget…, Delete transaction. Business logic: - Validate transaction_id exists - Delete…, delete, delete_budget_entry(), delete_category(), delete_payee() (+9 more)

### Community 14 - "Recurring Payments Config"
Cohesion: 0.12
Nodes (17): get_all_configuration(), get_configuration_value(), get_recurring_payment_categories(), get_recurring_payment_status(), _is_cache_valid(), Identify recurring payments (expenses only) and their status for current month.…, Check if configuration cache is still valid., Get all configuration as key-value dict. Uses in-memory cache for performance… (+9 more)

### Community 15 - "Recurring Categories UI"
Cohesion: 0.16
Nodes (13): Configuration Caching, Configuration Table (MariaDB key/value store), Recurring Payments Widget Configuration Design, GET /api/config/recurring-categories, PUT /api/config/recurring-categories, addRecurringCategory(), loadRecurringCategories(), removeRecurringCategory() (+5 more)

### Community 16 - "Application Overview (CLAUDE.md/README)"
Cohesion: 0.13
Nodes (15): Analysis (App Part), Budget & Actuals (App Part), Configuration (App Part), Dashboard (App Part), Graphify Knowledge Graph Integration, htmx Auto-Save UX, Moneybags Web Application, Analysis (Placeholder, README) (+7 more)

### Community 17 - "API Update Routes"
Cohesion: 0.13
Nodes (15): Update supersaver entry., Update existing transaction., Update category (rename only - type cannot change if data exists)., Update payee (renames all transaction references)., Update currency configuration settings. Request body: { "currency_format":…, Update selected category IDs for recurring payment monitoring. Request body: {…, Update supersaver category (rename only)., update_category() (+7 more)

### Community 18 - "Dashboard Widgets JS"
Cohesion: 0.19
Nodes (15): calculateCategoryTotals(), createExpensePieChart(), escapeHtml(), formatCurrency(), generateProgressBarHTML(), initializeDashboard(), loadBudgetProgress(), loadExpensePieCharts() (+7 more)

### Community 19 - "Payee Management"
Cohesion: 0.15
Nodes (13): delete_payee(), Update existing transaction. Business logic: - Validate transaction_id exists -…, Update payee (rename and/or change type). Business logic: - Validate payee_id…, Delete payee. Business logic: - Validate payee_id exists - Check NOT in use: no…, update_payee(), update_transaction(), delete_payee(), get_payee_by_id() (+5 more)

### Community 20 - "SuperSaver Calendar UI"
Cohesion: 0.29
Nodes (13): handleCalendarAddEntrySubmit(), handleCalendarDeleteEntry(), initializeDatePickers(), initSupersaver(), loadSupersaverCalendar(), loadSupersaverCategories(), openEditEntryModal(), renderSupersaverCalendar() (+5 more)

### Community 21 - "Database Migrations"
Cohesion: 0.23
Nodes (11): Database Migration Strategy, migrations/001_initial_schema.sql, get_db_config(), list_migrations(), main(), Simple database migration runner for Moneybags. Usage: python…, Get database configuration from moneybags_db_config.json., List available migration files. (+3 more)

### Community 22 - "Dashboard Widget Design & Templates"
Cohesion: 0.26
Nodes (11): Recent Transactions Widget (Design), Recurring Payments Tracker Widget (Design), 3-Column Widget Grid Layout, Budget Progress Widget Design, Budget Progress Color Logic (green/red), Budget Progress Widget Implementation Plan, GET /api/dashboard/recent-transactions, static/css/custom.css (+3 more)

### Community 23 - "Frontend Library Stack"
Cohesion: 0.20
Nodes (10): Bootstrap 5.3.0, Bootstrap Icons 1.10.0, Chart.js 4.4.0, Popper.js 2.11.8, Tempus Dominus 6.9.4 (Date Picker), Tom Select 2.3.1, Add/Edit Transaction Modal, Budget Input Modal (+2 more)

### Community 24 - "Payee Creation & Tests"
Cohesion: 0.20
Nodes (10): create_payee(), Create new payee. Business logic: - Validate name not empty - Validate type in…, create_payee(), get_payee_by_name(), Create payee with provided data dict., Get payee by exact name match. Args: name: Payee name to search for Returns:…, Test getting or creating import payee., test_ensure_import_payee() (+2 more)

### Community 25 - "Import Validation"
Cohesion: 0.24
Nodes (10): business_logic.validate_import(), get_budget_entry(), Get budget entry by category/year/month., Dry-run validation before import. Checks: - All mapped categories exist -…, validate_import(), POST /api/import/validate, Test import validation., Test validation fails for missing category. (+2 more)

### Community 26 - "Expense Totals & Date Utils"
Cohesion: 0.29
Nodes (7): get_expense_category_totals(), get_transactions_by_category_month(), Get transactions for category/year/month., Get aggregated expense totals by category for a time period. Args: year: Year…, date, get_month_date_range(), Get start and end dates for a month. Returns (start_date, end_date) as date…

### Community 27 - "Category Update"
Cohesion: 0.33
Nodes (6): Update category (rename only). Business logic: - Validate category_id exists -…, update_category(), category_exists_by_name(), Check if category with name exists (case-insensitive)., Update category fields., update_category()

### Community 28 - "Docker Deployment"
Cohesion: 0.40
Nodes (5): create-container-moneybags.sh script, Dockerfile, moneybags_db_config.json, Quick Start Guide, Database Connection Section

### Community 29 - "Connection Retry Logic"
Cohesion: 0.33
Nodes (6): check_connection(), execute_with_retry(), Attempt to reconnect to database. For PooledMySQLDatabase, we just close stale…, Execute database operation with retry logic for transient failures. Args:…, Check if database connection is healthy. Returns True if connection is alive,…, reconnect()

### Community 30 - "Currency Settings JS"
Cohesion: 0.33
Nodes (6): getCurrencySymbol(), initializeBudgetPage(), loadAvailableYears(), loadCurrencyFormat(), populateYearSelector(), updateCurrencyLabels()

### Community 31 - "SuperSaver Templates"
Cohesion: 0.33
Nodes (5): Navigation Bar, Supersaver Categories Section, Supersaver Widget, Savings Heatmap Calendar, Month Entries Modal

### Community 32 - "Budget Progress Widget"
Cohesion: 0.40
Nodes (5): GET /api/budget/{year}, calculateCategoryTotals(), generateProgressBarHTML(), initializeDashboard(), loadBudgetProgress()

### Community 33 - "Available Years API"
Cohesion: 0.50
Nodes (4): get_available_years(), Get all years that have budget templates. Business logic: - Query distinct…, get_available_years(), Get all years that have budget templates.

### Community 34 - "Expense Category Breakdown"
Cohesion: 0.50
Nodes (4): get_expense_category_breakdown(), Get expense category breakdown for dashboard pie charts. Args: period: 'month'…, get_expense_categories(), Get expense category breakdown for dashboard pie charts. Args: period: 'month'…

### Community 35 - "Recent Transactions API"
Cohesion: 0.50
Nodes (4): get_recent_transactions(), Get most recent transactions for dashboard display. Args: limit: Number of…, get_recent_transactions_api(), Get most recent transactions for dashboard display. Returns last 5 transactions…

### Community 36 - "DB Connection Test"
Cohesion: 0.50
Nodes (4): Test database connection with provided settings. Business logic: - Validate all…, test_database_connection(), Test database connection with provided parameters. Returns True if connection…, test_connection()

### Community 37 - "App Startup Event"
Cohesion: 0.67
Nodes (3): Initialize application on startup., startup_event(), on_event

### Community 38 - "Business Logic Test Fixture"
Cohesion: 0.67
Nodes (3): create_test_database(), fixture, Create test database once at session start.

### Community 39 - "Database Manager Test Fixture"
Cohesion: 0.67
Nodes (3): create_test_database(), fixture, Create test database once at session start.

## Knowledge Gaps
- **49 isolated node(s):** `create-container-moneybags.sh script`, `moneybags`, `months`, `currentMonth`, `currentYear` (+44 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 294 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **13 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Project Structure Overview` connect `Business Logic Core Operations` to `Category Deletion & Architecture Rationale`, `Budget Calculation JS`, `API GET Routes`, `Excel Import Feature`, `Database Models`, `Dashboard Widget Design & Templates`?**
  _High betweenness centrality (0.239) - this node is a cross-community bridge._
- **Why does `Import Functionality Refactoring Design` connect `Excel Import Feature` to `Business Logic Core Operations`, `Budget Calculation JS`, `API GET Routes`?**
  _High betweenness centrality (0.085) - this node is a cross-community bridge._
- **Why does `with_retry()` connect `Category Deletion & Architecture Rationale` to `SuperSaver Feature`, `Business Logic Core Operations`, `Database Models`, `Database Manager CRUD`, `Database Config Management`, `Payee Management`, `Payee Creation & Tests`, `Import Validation`, `Expense Totals & Date Utils`, `Category Update`?**
  _High betweenness centrality (0.037) - this node is a cross-community bridge._
- **What connects `create-container-moneybags.sh script`, `moneybags`, `months` to the rest of the system?**
  _49 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `SuperSaver Feature` be split into smaller, more focused modules?**
  _Cohesion score 0.05565638233514821 - nodes in this community are weakly interconnected._
- **Should `Category Deletion & Architecture Rationale` be split into smaller, more focused modules?**
  _Cohesion score 0.06666666666666667 - nodes in this community are weakly interconnected._
- **Should `Business Logic Core Operations` be split into smaller, more focused modules?**
  _Cohesion score 0.08879492600422834 - nodes in this community are weakly interconnected._