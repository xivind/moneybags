# Graph Report - moneybags  (2026-10-27)

## Corpus Check
- 4 files · ~55,280 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 740 nodes · 1639 edges · 56 communities (51 shown, 5 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 121 edges (avg confidence: 0.92)
- Token cost: 70,413 input · 0 output

## Community Hubs (Navigation)
- Architecture & App Overview Docs
- Budget Calculation JS
- Frontend CRUD Actions
- Excel Import Feature
- Import Parsing Logic
- Business Logic Core Operations
- API GET Routes
- Database Manager CRUD
- API Create/Update Routes
- Payee & Transaction Creation
- Expense Totals & Date Utils
- Connection & Transaction Handling
- Database Delete Operations
- Frontend Data Loading
- Delete API Routes
- Database Connection Lifecycle
- Budget Template Management
- Recurring Payments Config
- Frontend Library Stack
- API Update Routes
- Dashboard Widgets JS
- Database Migrations
- SuperSaver Calendar UI
- Categories & Available Years
- Payee Management
- SuperSaver Data Access
- Dashboard Widget Design & Templates
- Payee Deletion & Listing
- Category Deletion
- Database Config File
- Import Validation
- SuperSaver Business Logic
- Configuration Cache
- Database Initialization
- Recurring Categories UI
- SuperSaver Category Deletion
- Config Page Template
- Category Create & Update
- Configuration Updates
- DB Connection Test
- Currency Settings JS
- SuperSaver Entry Deletion
- SuperSaver Category Listing
- SuperSaver Monthly Entries
- SuperSaver Category Update
- Budget Progress Widget
- Expense Category Breakdown
- Recent Transactions API
- SuperSaver Dashboard Summary
- SuperSaver Heatmap
- App Startup Event
- Docker Deployment Script
- Test Package Init
- Moneybags Package
- Favicon Icon
- Application Logo

## God Nodes (most connected - your core abstractions)
1. `apiCall()` - 48 edges
2. `with_retry()` - 41 edges
3. `with_transaction()` - 25 edges
4. `hideLoading()` - 24 edges
5. `showLoading()` - 24 edges
6. `Transaction` - 23 edges
7. `Category` - 21 edges
8. `BudgetEntry` - 20 edges
9. `Payee` - 20 edges
10. `showSuccess()` - 19 edges

## Surprising Connections (you probably didn't know these)
- `Recurring Payments Widget Configuration Design` --semantically_similar_to--> `Configuration Caching (5-minute)`  [INFERRED] [semantically similar]
  docs/plans/2025-12-30-recurring-payments-configuration.md → CLAUDE.md
- `business_logic.import_budget_and_transactions()` --calls--> `empty_to_none()`  [EXTRACTED]
  docs/plans/2025-12-29-google-sheets-import-design.md → utils.py
- `business_logic.validate_import()` --calls--> `get_category_by_id()`  [EXTRACTED]
  docs/plans/2025-12-29-google-sheets-import-design.md → database_manager.py
- `Recent Transactions Widget (Design)` --references--> `get_recent_transactions()`  [EXTRACTED]
  docs/plans/2025-12-29-dashboard-widgets-design.md → business_logic.py
- `business_logic.import_budget_and_transactions()` --calls--> `create_or_update_budget_entry()`  [EXTRACTED]
  docs/plans/2025-12-29-google-sheets-import-design.md → database_manager.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Base Template Shared Frontend Dependencies** — templates_base, lib_bootstrap, lib_tomselect, lib_tempus_dominus, lib_chartjs, static_js_app [EXTRACTED 1.00]
- **Dashboard Widget Implementation Pattern (business_logic function -> main API route -> dashboard.html card -> app.js render)** — docs_plans_2025_12_29_dashboard_widgets_design_recurring_payments_widget, docs_plans_2025_12_29_dashboard_widgets_design_recent_transactions_widget, business_logic, main, templates_dashboard, static_js_app [INFERRED 0.85]
- **Layered request flow main -> business_logic -> database_manager -> models** — claude_main_router, claude_business_logic_layer, claude_database_manager_layer, claude_database_model_layer [EXTRACTED 1.00]
- **Database resilience and performance mechanisms** — claude_pooled_mysql_database, claude_with_transaction_decorator, claude_retry_logic, claude_configuration_caching, claude_log_query_time_decorator [EXTRACTED 1.00]
- **Excel import pipeline with pluggable parsers** — claude_excel_import, claude_import_logic_module, claude_original_format, claude_hovedark_format, claude_import_parser_pattern [EXTRACTED 1.00]

## Communities (56 total, 5 thin omitted)

### Community 0 - "Architecture & App Overview Docs"
Cohesion: 0.08
Nodes (42): Analysis Page, JSON API Response Envelope, Backend-Generated UUIDs, Budget & Actuals View, Budget Templates by Year, business_logic.py Layer, Configuration Caching (5-minute), Configuration Page (+34 more)

### Community 1 - "Budget Calculation JS"
Cohesion: 0.07
Nodes (28): allCategories, availableYears, calculateBudgetYearTotal(), calculateMonthlyBudgetBalance(), calculateMonthlyDifference(), calculateMonthlyResult(), calculateResultYearTotal(), currentMonth (+20 more)

### Community 2 - "Frontend CRUD Actions"
Cohesion: 0.15
Nodes (35): addCategoryToYear(), addRecurringCategory(), changeYear(), createCategory(), deleteBudgetEntry(), deleteBudgetEntryApi(), deleteCategory(), deleteCategoryApi() (+27 more)

### Community 3 - "Excel Import Feature"
Cohesion: 0.08
Nodes (29): Import Data Integrity Validation, Import Edge Case Handling, Google Sheets Import Feature (Design), 5-Step Import User Workflow, Google Sheets Import TDD Implementation Plan, Import Functionality Refactoring Design, handleFileUpload() (app.js, pre-refactor), handleImport() (app.js, pre-refactor) (+21 more)

### Community 4 - "Import Parsing Logic"
Cohesion: 0.09
Nodes (29): business_logic._extract_amounts_from_formula(), Formula Parsing Validation Rules, _extract_amounts_from_formula(), Extract individual amounts from Excel formula or value. Strict validation -…, Tests for business_logic.py Tests for formula parsing helper function., Test that complex formulas are rejected., Test that negative values are rejected., Test that multiplication is rejected. (+21 more)

### Community 5 - "Business Logic Core Operations"
Cohesion: 0.12
Nodes (26): calculate_category_trends(), get_budget_data_for_year(), get_budget_template(), get_transactions(), business_logic.parse_excel_file(), Business logic for Moneybags application. All validation, business rules, and…, Get all transactions for category/year/month. Business logic: - Validate…, Get categories active in year's budget template. Business logic: - Query… (+18 more)

### Community 6 - "API GET Routes"
Cohesion: 0.11
Nodes (26): get, budget_page(), config_page(), dashboard(), get_budget_data(), get_budget_template(), get_budget_trends(), get_supersaver_categories() (+18 more)

### Community 7 - "Database Manager CRUD"
Cohesion: 0.13
Nodes (24): create_budget_entry(), create_category(), create_or_update_budget_entry(), get_budget_entries_by_year(), Create category with provided data dict., Create budget entry with provided data dict., Get all budget entries for year (with eager-loaded categories to avoid N+1…, Create or update budget entry. Checks if entry exists by (category_id, year,… (+16 more)

### Community 8 - "API Create/Update Routes"
Cohesion: 0.11
Nodes (25): add_category_to_template(), copy_budget_template(), create_category(), create_payee(), create_supersaver_category(), create_supersaver_entry(), create_transaction(), execute_import() (+17 more)

### Community 9 - "Payee & Transaction Creation"
Cohesion: 0.13
Nodes (24): create_payee(), create_transaction(), business_logic._ensure_import_payee(), business_logic.import_budget_and_transactions(), Create new transaction. Business logic: - Validate required fields…, Create new payee. Business logic: - Validate name not empty - Validate type in…, create_payee(), create_transaction() (+16 more)

### Community 10 - "Expense Totals & Date Utils"
Cohesion: 0.15
Nodes (19): category_has_transactions_for_year(), get_expense_category_totals(), get_recent_transactions(), get_transactions_by_category_month(), get_transactions_by_date_range(), get_transactions_by_year(), Get transactions for category/year/month., Get all transactions for year (with eager-loaded payees and categories to avoid… (+11 more)

### Community 11 - "Connection & Transaction Handling"
Cohesion: 0.12
Nodes (17): check_connection(), configuration_exists(), _execute_transaction(), execute_with_retry(), get_budget_entries_by_category_year(), log_query_time(), Database manager for Moneybags application. All database CRUD operations are…, Attempt to reconnect to database. For PooledMySQLDatabase, we just close stale… (+9 more)

### Community 12 - "Database Delete Operations"
Cohesion: 0.11
Nodes (18): delete_budget_entry(), delete_budget_template(), delete_category(), delete_transaction(), Decorator to wrap database write operations in transactions with retry logic.…, Update category fields., Delete category by ID., Delete budget template entry. (+10 more)

### Community 13 - "Frontend Data Loading"
Cohesion: 0.16
Nodes (18): apiCall(), createPayee(), createTransaction(), deletePayee(), deletePayeeApi(), formatDate(), loadAllTrends(), loadCategoryTrends() (+10 more)

### Community 14 - "Delete API Routes"
Cohesion: 0.12
Nodes (17): delete_budget_entry(), delete_transaction(), Delete budget entry. Business logic: - Validate entry_id exists - Delete budget…, Delete transaction. Business logic: - Validate transaction_id exists - Delete…, get_budget_entry_by_id(), Get budget entry by ID., delete, delete_budget_entry() (+9 more)

### Community 15 - "Database Connection Lifecycle"
Cohesion: 0.13
Nodes (17): close_connection(), create_tables_if_not_exist(), initialize_connection(), Create all tables if they don't exist. Note: PeeWee's safe=True checks if…, Close database connection., Initialize database connection with connection pooling. Connection pooling…, Migration Strategy, create_test_database() (+9 more)

### Community 16 - "Budget Template Management"
Cohesion: 0.14
Nodes (16): add_category_to_template(), copy_budget_template(), Add category to year's budget template. Business logic: - Validate year -…, Remove category from year's template. Business logic: - Validate entry exists -…, Copy budget template from one year to another. Business logic: - Validate both…, remove_category_from_template(), budget_template_exists(), create_budget_template() (+8 more)

### Community 17 - "Recurring Payments Config"
Cohesion: 0.16
Nodes (15): get_configuration_value(), get_recurring_payment_categories(), get_recurring_payment_status(), Identify recurring payments (expenses only) and their status for current month.…, Get a single configuration value by key. Args: key: Configuration key to…, Get list of category IDs for recurring payment monitoring. Returns: List of…, Configuration Table (MariaDB key/value store), Recurring Payments Tracker Widget (Design) (+7 more)

### Community 18 - "Frontend Library Stack"
Cohesion: 0.18
Nodes (12): Bootstrap 5.3.0, Bootstrap Icons 1.10.0, Popper.js 2.11.8, Tempus Dominus 6.9.4 (Date Picker), Tom Select 2.3.1, GET /import, Navigation Bar, Add/Edit Transaction Modal (+4 more)

### Community 19 - "API Update Routes"
Cohesion: 0.13
Nodes (15): Update supersaver entry., Update existing transaction., Update category (rename only - type cannot change if data exists)., Update payee (renames all transaction references)., Update currency configuration settings. Request body: { "currency_format":…, Update selected category IDs for recurring payment monitoring. Request body: {…, Update supersaver category (rename only)., update_category() (+7 more)

### Community 20 - "Dashboard Widgets JS"
Cohesion: 0.19
Nodes (15): calculateCategoryTotals(), createExpensePieChart(), escapeHtml(), formatCurrency(), generateProgressBarHTML(), initializeDashboard(), loadBudgetProgress(), loadExpensePieCharts() (+7 more)

### Community 21 - "Database Migrations"
Cohesion: 0.18
Nodes (13): json, get_db_config(), list_migrations(), main(), Simple database migration runner for Moneybags. Usage: python…, Get database configuration from moneybags_db_config.json., List available migration files., Run specified migration file. (+5 more)

### Community 22 - "SuperSaver Calendar UI"
Cohesion: 0.29
Nodes (13): handleCalendarAddEntrySubmit(), handleCalendarDeleteEntry(), initializeDatePickers(), initSupersaver(), loadSupersaverCalendar(), loadSupersaverCategories(), openEditEntryModal(), renderSupersaverCalendar() (+5 more)

### Community 23 - "Categories & Available Years"
Cohesion: 0.17
Nodes (12): get_all_categories(), get_available_years(), Get all categories with usage information. Returns list with category info +…, Get all years that have budget templates. Business logic: - Query distinct…, category_has_budget_entries_for_year(), get_all_categories(), get_distinct_years(), Get all distinct years from budget_templates. (+4 more)

### Community 24 - "Payee Management"
Cohesion: 0.17
Nodes (12): Update existing transaction. Business logic: - Validate transaction_id exists -…, Update payee (rename and/or change type). Business logic: - Validate payee_id…, update_payee(), update_transaction(), get_payee_by_id(), get_transaction_by_id(), payee_exists_by_name(), Check if payee with name exists (case-insensitive). (+4 more)

### Community 25 - "SuperSaver Data Access"
Cohesion: 0.23
Nodes (11): Supersaver entries (savings deposits only). Records savings deposits for…, Supersaver, create_supersaver_entry(), get_all_supersaver_entries_for_year(), get_supersaver_balance(), Supersaver database CRUD operations. Pure CRUD functions - no validation or…, Update supersaver entry fields., Get current balance for category (total deposits). Returns 0 if no entries… (+3 more)

### Community 26 - "Dashboard Widget Design & Templates"
Cohesion: 0.23
Nodes (11): Recent Transactions Widget (Design), 3-Column Widget Grid Layout, Budget Progress Widget Design, Budget Progress Color Logic (green/red), Budget Progress Widget Implementation Plan, Chart.js 4.4.0, GET /api/dashboard/recent-transactions, Budget Progress Widget (Implemented) (+3 more)

### Community 27 - "Payee Deletion & Listing"
Cohesion: 0.18
Nodes (11): delete_payee(), get_all_payees(), Get all payees with usage statistics. Returns list with payee info + statistics…, Delete payee. Business logic: - Validate payee_id exists - Check NOT in use: no…, delete_payee(), get_all_payees(), payee_last_used_date(), payee_transaction_count() (+3 more)

### Community 28 - "Category Deletion"
Cohesion: 0.24
Nodes (10): delete_category(), Delete category. Business logic: - Validate category_id exists - Check NOT in…, category_has_budget_entries(), category_has_budget_templates(), category_has_transactions(), Decorator to wrap database read operations with retry logic. Automatically…, Check if category is used in any budget_templates., Check if category has any budget_entries. (+2 more)

### Community 29 - "Database Config File"
Cohesion: 0.20
Nodes (10): _get_config_file_path(), load_database_config(), Get the path to the database configuration file. Tries multiple paths in order:…, Load database configuration from moneybags_db_config.json file. Returns: dict:…, Save database configuration to moneybags_db_config.json file. Args: config:…, save_database_config(), get_db_connection(), Get current database connection settings from moneybags_db_config.json. Note:… (+2 more)

### Community 30 - "Import Validation"
Cohesion: 0.24
Nodes (10): business_logic.validate_import(), get_budget_entry(), Get budget entry by category/year/month., Dry-run validation before import. Checks: - All mapped categories exist -…, validate_import(), POST /api/import/validate, Test import validation., Test validation fails for missing category. (+2 more)

### Community 31 - "SuperSaver Business Logic"
Cohesion: 0.24
Nodes (9): create_supersaver_category(), create_supersaver_entry(), Supersaver business logic. Validation, business rules, and data preparation for…, Create supersaver entry (savings deposit). Business logic: - Validate category…, Update supersaver entry., Create new supersaver category. Business logic: - Validate name not empty -…, update_supersaver_entry(), Validate date string is in YYYY-MM-DD format. Returns True if valid, False… (+1 more)

### Community 32 - "Configuration Cache"
Cohesion: 0.25
Nodes (8): get_all_configuration(), _is_cache_valid(), Check if configuration cache is still valid., Get all configuration as key-value dict. Uses in-memory cache for performance…, get_all_configuration(), Get all configuration entries., get_currency_configuration(), Get currency configuration settings. Returns currency_format and other app…

### Community 33 - "Database Initialization"
Cohesion: 0.25
Nodes (8): initialize_database(), Initialize database connection and create tables if needed., create_configuration(), get_configuration_by_key(), Create configuration entry with provided data dict., Get configuration by key., No-op function for database seeding. Previously seeded categories, payees, and…, seed_initial_data()

### Community 34 - "Recurring Categories UI"
Cohesion: 0.32
Nodes (6): GET /api/config/recurring-categories, PUT /api/config/recurring-categories, addRecurringCategory(), loadRecurringCategories(), removeRecurringCategory(), Recurring Payments Widget Config Section

### Community 35 - "SuperSaver Category Deletion"
Cohesion: 0.25
Nodes (8): delete_supersaver_category(), Delete supersaver category (only if no entries)., delete_supersaver_category(), Delete supersaver category. Business logic: - Validate category exists - Check…, delete_supersaver_category(), Delete supersaver category by ID., Check if category has any supersaver entries., supersaver_category_has_entries()

### Community 36 - "Config Page Template"
Cohesion: 0.25
Nodes (7): Budget Templates by Year Section, Categories Section, Currency Settings Section, Database Connection Section, Payees Section, Supersaver Categories Section, Month Entries Modal

### Community 37 - "Category Create & Update"
Cohesion: 0.29
Nodes (7): create_category(), Create new category. Business logic: - Validate name not empty - Validate type…, Update category (rename only). Business logic: - Validate category_id exists -…, update_category(), category_exists_by_name(), get_category_by_id(), Check if category with name exists (case-insensitive).

### Community 38 - "Configuration Updates"
Cohesion: 0.33
Nodes (6): _invalidate_config_cache(), Invalidate configuration cache., Update list of category IDs for recurring payment monitoring. Args:…, Update configuration settings. Business logic: - For each key-value in…, update_configuration(), update_recurring_payment_categories()

### Community 39 - "DB Connection Test"
Cohesion: 0.33
Nodes (6): Test database connection with provided settings. Business logic: - Validate all…, test_database_connection(), Test database connection with provided parameters. Returns True if connection…, test_connection(), Test database connection with provided settings., test_db_connection()

### Community 40 - "Currency Settings JS"
Cohesion: 0.33
Nodes (6): getCurrencySymbol(), initializeBudgetPage(), loadAvailableYears(), loadCurrencyFormat(), populateYearSelector(), updateCurrencyLabels()

### Community 41 - "SuperSaver Entry Deletion"
Cohesion: 0.33
Nodes (6): delete_supersaver_entry(), Delete supersaver entry., delete_supersaver_entry(), get_supersaver_entry_by_id(), Delete supersaver entry by ID., Get supersaver entry by ID. Returns None if not found.

### Community 42 - "SuperSaver Category Listing"
Cohesion: 0.33
Nodes (6): get_all_supersaver_categories(), Get all supersaver categories with balance and usage stats., get_all_supersaver_categories(), Count entries for supersaver category., Get all supersaver categories ordered by name., supersaver_entry_count_by_category()

### Community 43 - "SuperSaver Monthly Entries"
Cohesion: 0.33
Nodes (6): get_supersaver_entries_for_month(), Get all supersaver entries for category/year/month. Returns list organized by…, get_supersaver_category_by_id(), get_supersaver_entries_by_category_month(), Get supersaver entries for category/year/month., Get supersaver category by ID. Returns None if not found.

### Community 44 - "SuperSaver Category Update"
Cohesion: 0.33
Nodes (6): Update supersaver category (rename only). Business logic: - Validate category…, update_supersaver_category(), Check if supersaver category with name exists (case-insensitive)., Update supersaver category fields., supersaver_category_exists_by_name(), update_supersaver_category()

### Community 45 - "Budget Progress Widget"
Cohesion: 0.40
Nodes (5): GET /api/budget/{year}, calculateCategoryTotals(), generateProgressBarHTML(), initializeDashboard(), loadBudgetProgress()

### Community 46 - "Expense Category Breakdown"
Cohesion: 0.50
Nodes (4): get_expense_category_breakdown(), Get expense category breakdown for dashboard pie charts. Args: period: 'month'…, get_expense_categories(), Get expense category breakdown for dashboard pie charts. Args: period: 'month'…

### Community 47 - "Recent Transactions API"
Cohesion: 0.50
Nodes (4): get_recent_transactions(), Get most recent transactions for dashboard display. Args: limit: Number of…, get_recent_transactions_api(), Get most recent transactions for dashboard display. Returns last 5 transactions…

### Community 48 - "SuperSaver Dashboard Summary"
Cohesion: 0.50
Nodes (4): get_supersaver_dashboard_summary(), Get supersaver summary for dashboard widget (all categories, deposits only)., get_supersaver_dashboard_summary(), Get supersaver summary for dashboard widget. Returns aggregated data across all…

### Community 49 - "SuperSaver Heatmap"
Cohesion: 0.50
Nodes (4): get_supersaver_heatmap(), Get daily heatmap data for entire year (all categories, deposits only). Returns…, get_supersaver_heatmap_year(), Get daily heatmap data for entire year (all categories, deposits only). Returns…

### Community 50 - "App Startup Event"
Cohesion: 0.67
Nodes (3): Initialize application on startup., startup_event(), on_event

## Ambiguous Edges - Review These
- `database_manager.py Layer` → `import_logic.py Import Module`  [AMBIGUOUS]
  CLAUDE.md · relation: calls

## Knowledge Gaps
- **39 isolated node(s):** `create-container-moneybags.sh script`, `allCategories`, `availableYears`, `currentMonth`, `currentYear` (+34 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 289 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `database_manager.py Layer` and `import_logic.py Import Module`?**
  _Edge tagged AMBIGUOUS (relation: calls) - confidence is low._
- **Why does `Import Functionality Refactoring Design` connect `Excel Import Feature` to `Budget Calculation JS`, `Business Logic Core Operations`, `API GET Routes`?**
  _High betweenness centrality (0.262) - this node is a cross-community bridge._
- **Why does `Recurring Payments Widget Configuration Design` connect `Recurring Payments Config` to `Architecture & App Overview Docs`, `Recurring Categories UI`, `Config Page Template`?**
  _High betweenness centrality (0.119) - this node is a cross-community bridge._
- **Why does `Configuration Caching (5-minute)` connect `Architecture & App Overview Docs` to `Recurring Payments Config`?**
  _High betweenness centrality (0.104) - this node is a cross-community bridge._
- **What connects `create-container-moneybags.sh script`, `allCategories`, `availableYears` to the rest of the system?**
  _39 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Architecture & App Overview Docs` be split into smaller, more focused modules?**
  _Cohesion score 0.07665505226480836 - nodes in this community are weakly interconnected._
- **Should `Budget Calculation JS` be split into smaller, more focused modules?**
  _Cohesion score 0.06968641114982578 - nodes in this community are weakly interconnected._