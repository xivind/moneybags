# Graph Report - moneybags  (2026-11-14)

## Corpus Check
- 30 files · ~49,040 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 8 file(s) not represented in the graph (top: (none) 5, .css 1, .lock 1)

## Summary
- 740 nodes · 1642 edges · 40 communities (32 shown, 8 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 121 edges (avg confidence: 0.92)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `b89aeef2`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Architecture & App Overview Docs
- Budget Calculation JS
- Frontend CRUD Actions
- Excel Import Feature
- Import Parsing Logic
- Business Logic Core Operations
- API GET Routes
- BudgetEntry
- API Create/Update Routes
- Payee & Transaction Creation
- Expense Totals & Date Utils
- database_manager.py
- with_transaction
- Frontend Data Loading
- Delete API Routes
- setup_test_db
- Budget Template Management
- Recurring Payments Config
- templates/base.html
- API Update Routes
- Dashboard Widgets JS
- execute_with_retry
- SuperSaver Calendar UI
- with_retry
- get_recurring_payment_status
- supersaver_database_manager.py
- budget_page
- _get_config_file_path
- Import Validation
- SuperSaver Business Logic
- Category Create & Update
- Configuration Updates
- DB Connection Test
- Currency Settings JS
- get_all_supersaver_entries_for_year
- Docker Deployment Script
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
8. `Payee` - 20 edges
9. `BudgetEntry` - 20 edges
10. `showSuccess()` - 19 edges

## Surprising Connections (you probably didn't know these)
- `Recurring Payments Widget Configuration Design` --semantically_similar_to--> `Configuration Caching (5-minute)`  [INFERRED] [semantically similar]
  docs/plans/2025-12-30-recurring-payments-configuration.md → CLAUDE.md
- `Migration Strategy` --references--> `create_tables_if_not_exist()`  [EXTRACTED]
  migrations/README.md → database_manager.py
- `Recurring Payments Tracker Widget (Design)` --references--> `get_recurring_payment_status()`  [EXTRACTED]
  docs/plans/2025-12-29-dashboard-widgets-design.md → business_logic.py
- `Recurring Payments Widget Configuration Design` --references--> `get_recurring_payment_status()`  [EXTRACTED]
  docs/plans/2025-12-30-recurring-payments-configuration.md → business_logic.py
- `GET /api/dashboard/recurring-payments` --calls--> `get_recurring_payment_status()`  [EXTRACTED]
  docs/plans/2025-12-29-dashboard-widgets-design.md → business_logic.py

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Base Template Shared Frontend Dependencies** — templates_base, lib_bootstrap, lib_tomselect, lib_tempus_dominus, lib_chartjs, static_js_app [EXTRACTED 1.00]
- **Database resilience and performance mechanisms** — claude_pooled_mysql_database, claude_with_transaction_decorator, claude_retry_logic, claude_configuration_caching, claude_log_query_time_decorator [EXTRACTED 1.00]
- **Excel import pipeline with pluggable parsers** — claude_excel_import, claude_import_logic_module, claude_original_format, claude_hovedark_format, claude_import_parser_pattern [EXTRACTED 1.00]
- **Layered request flow main -> business_logic -> database_manager -> models** — claude_main_router, claude_business_logic_layer, claude_database_manager_layer, claude_database_model_layer [EXTRACTED 1.00]
- **Dashboard Widget Implementation Pattern (business_logic function -> main API route -> dashboard.html card -> app.js render)** — docs_plans_2025_12_29_dashboard_widgets_design_recurring_payments_widget, docs_plans_2025_12_29_dashboard_widgets_design_recent_transactions_widget, business_logic, main, templates_dashboard, static_js_app [INFERRED 0.85]

## Communities (40 total, 8 thin omitted)

### Community 0 - "Architecture & App Overview Docs"
Cohesion: 0.08
Nodes (34): Analysis Page, JSON API Response Envelope, Budget & Actuals View, Budget Templates by Year, business_logic.py Layer, Configuration Caching (5-minute), Configuration Page, Dynamic Currency Format (NOK/USD/EUR) (+26 more)

### Community 1 - "Budget Calculation JS"
Cohesion: 0.07
Nodes (28): allCategories, availableYears, calculateBudgetYearTotal(), calculateMonthlyBudgetBalance(), calculateMonthlyDifference(), calculateMonthlyResult(), calculateResultYearTotal(), currentMonth (+20 more)

### Community 2 - "Frontend CRUD Actions"
Cohesion: 0.15
Nodes (35): addCategoryToYear(), addRecurringCategory(), changeYear(), createCategory(), deleteBudgetEntry(), deleteBudgetEntryApi(), deleteCategory(), deleteCategoryApi() (+27 more)

### Community 3 - "Excel Import Feature"
Cohesion: 0.08
Nodes (28): Import Data Integrity Validation, Import Edge Case Handling, Google Sheets Import Feature (Design), 5-Step Import User Workflow, Google Sheets Import TDD Implementation Plan, handleFileUpload() (app.js, pre-refactor), handleImport() (app.js, pre-refactor), handleValidate() (app.js, pre-refactor) (+20 more)

### Community 4 - "Import Parsing Logic"
Cohesion: 0.08
Nodes (16): business_logic._extract_amounts_from_formula(), _extract_amounts_from_formula(), _parse_hovedark_format(), _parse_original_format(), test_extract_amounts_from_formula_budget_formulas(), test_extract_amounts_from_formula_empty(), test_extract_amounts_from_formula_nested_parentheses(), test_extract_amounts_from_formula_plain_number() (+8 more)

### Community 5 - "Business Logic Core Operations"
Cohesion: 0.13
Nodes (13): calculate_category_trends(), create_transaction(), get_budget_data_for_year(), get_budget_template(), get_transactions(), business_logic.parse_excel_file(), save_budget_entry(), get_category_by_id() (+5 more)

### Community 6 - "API GET Routes"
Cohesion: 0.08
Nodes (17): config_page(), dashboard(), get_available_years(), get_budget_data(), get_budget_template(), get_budget_trends(), get_db_connection(), get_expense_categories() (+9 more)

### Community 7 - "BudgetEntry"
Cohesion: 0.15
Nodes (8): delete_budget_entry(), create_or_update_budget_entry(), delete_budget_entry(), get_budget_entries_by_year(), get_budget_entry_by_id(), BudgetEntry, delete_budget_entry(), test_create_or_update_budget_entry()

### Community 8 - "API Create/Update Routes"
Cohesion: 0.10
Nodes (13): add_category_to_template(), copy_budget_template(), create_category(), create_payee(), create_supersaver_category(), create_supersaver_entry(), create_transaction(), execute_import() (+5 more)

### Community 9 - "Payee & Transaction Creation"
Cohesion: 0.11
Nodes (14): create_category(), create_payee(), business_logic._ensure_import_payee(), business_logic.import_budget_and_transactions(), create_payee(), create_transaction(), get_payee_by_name(), _ensure_import_payee() (+6 more)

### Community 10 - "Expense Totals & Date Utils"
Cohesion: 0.12
Nodes (13): get_expense_category_breakdown(), get_expense_category_totals(), get_recent_transactions(), get_transactions_by_category_month(), get_transactions_by_date_range(), get_transactions_by_year(), BaseModel, Category (+5 more)

### Community 11 - "database_manager.py"
Cohesion: 0.09
Nodes (13): delete_category(), category_has_budget_entries(), category_has_budget_templates(), category_has_transactions(), configuration_exists(), create_configuration(), delete_category(), _execute_transaction() (+5 more)

### Community 12 - "with_transaction"
Cohesion: 0.10
Nodes (11): delete_transaction(), update_transaction(), create_budget_entry(), delete_budget_template(), delete_transaction(), get_transaction_by_id(), update_budget_entry(), update_transaction() (+3 more)

### Community 13 - "Frontend Data Loading"
Cohesion: 0.16
Nodes (18): apiCall(), createPayee(), createTransaction(), deletePayee(), deletePayeeApi(), formatDate(), loadAllTrends(), loadCategoryTrends() (+10 more)

### Community 14 - "Delete API Routes"
Cohesion: 0.18
Nodes (5): delete_category(), delete_payee(), delete_supersaver_category(), delete_supersaver_entry(), remove_category_from_template()

### Community 15 - "setup_test_db"
Cohesion: 0.06
Nodes (16): initialize_database(), load_database_config(), close_connection(), create_tables_if_not_exist(), initialize_connection(), seed_initial_data(), startup_event(), get_db_config() (+8 more)

### Community 16 - "Budget Template Management"
Cohesion: 0.16
Nodes (7): add_category_to_template(), copy_budget_template(), remove_category_from_template(), budget_template_exists(), create_budget_template(), get_budget_template_by_year(), BudgetTemplate

### Community 17 - "Recurring Payments Config"
Cohesion: 0.13
Nodes (8): get_all_configuration(), get_configuration_value(), get_recurring_payment_categories(), _is_cache_valid(), GET /api/dashboard/recurring-payments, get_currency_configuration(), get_recurring_categories(), get_recurring_payments()

### Community 18 - "templates/base.html"
Cohesion: 0.05
Nodes (43): get_recent_transactions(), Configuration Table (MariaDB key/value store), Recent Transactions Widget (Design), Recurring Payments Tracker Widget (Design), Budget Progress Widget Design, Budget Progress Widget Implementation Plan, Bootstrap 5.3.0, Bootstrap Icons 1.10.0 (+35 more)

### Community 19 - "API Update Routes"
Cohesion: 0.13
Nodes (7): update_category(), update_currency_configuration(), update_payee(), update_recurring_categories(), update_supersaver_category(), update_supersaver_entry(), update_transaction()

### Community 20 - "Dashboard Widgets JS"
Cohesion: 0.19
Nodes (15): calculateCategoryTotals(), createExpensePieChart(), escapeHtml(), formatCurrency(), generateProgressBarHTML(), initializeDashboard(), loadBudgetProgress(), loadExpensePieCharts() (+7 more)

### Community 21 - "execute_with_retry"
Cohesion: 0.33
Nodes (3): check_connection(), execute_with_retry(), reconnect()

### Community 22 - "SuperSaver Calendar UI"
Cohesion: 0.29
Nodes (13): handleCalendarAddEntrySubmit(), handleCalendarDeleteEntry(), initializeDatePickers(), initSupersaver(), loadSupersaverCalendar(), loadSupersaverCategories(), openEditEntryModal(), renderSupersaverCalendar() (+5 more)

### Community 23 - "with_retry"
Cohesion: 0.11
Nodes (13): get_all_categories(), get_all_payees(), get_available_years(), category_has_budget_entries_for_year(), category_has_transactions_for_year(), get_all_categories(), get_all_payees(), get_budget_entries_by_category_year() (+5 more)

### Community 24 - "get_recurring_payment_status"
Cohesion: 0.15
Nodes (8): delete_payee(), get_recurring_payment_status(), update_payee(), delete_payee(), get_payee_by_id(), payee_exists_by_name(), payee_transaction_count(), update_payee()

### Community 25 - "supersaver_database_manager.py"
Cohesion: 0.07
Nodes (19): Supersaver, delete_supersaver_category(), delete_supersaver_entry(), get_all_supersaver_categories(), get_supersaver_entries_for_month(), update_supersaver_category(), create_supersaver_entry(), delete_supersaver_category() (+11 more)

### Community 30 - "Import Validation"
Cohesion: 0.20
Nodes (7): business_logic.validate_import(), create_category(), get_budget_entry(), validate_import(), POST /api/import/validate, test_validate_import(), test_validate_import_missing_category()

### Community 31 - "SuperSaver Business Logic"
Cohesion: 0.24
Nodes (4): create_supersaver_category(), create_supersaver_entry(), update_supersaver_entry(), validate_date_format()

### Community 37 - "Category Create & Update"
Cohesion: 0.33
Nodes (3): update_category(), category_exists_by_name(), update_category()

### Community 38 - "Configuration Updates"
Cohesion: 0.33
Nodes (3): _invalidate_config_cache(), update_configuration(), update_recurring_payment_categories()

### Community 40 - "Currency Settings JS"
Cohesion: 0.33
Nodes (6): getCurrencySymbol(), initializeBudgetPage(), loadAvailableYears(), loadCurrencyFormat(), populateYearSelector(), updateCurrencyLabels()

### Community 48 - "get_all_supersaver_entries_for_year"
Cohesion: 0.33
Nodes (3): get_supersaver_dashboard_summary(), get_supersaver_heatmap_year(), get_all_supersaver_entries_for_year()

## Ambiguous Edges - Review These
- `database_manager.py Layer` → `import_logic.py Import Module`  [AMBIGUOUS]
  CLAUDE.md · relation: calls

## Knowledge Gaps
- **27 isolated node(s):** `moneybags`, `Bootstrap 5.3.0`, `Bootstrap Icons 1.10.0`, `Tom Select 2.3.1`, `Budget Input Modal` (+22 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 287 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **8 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Import Functionality Refactoring Design` connect `Excel Import Feature` to `Budget Calculation JS`, `Business Logic Core Operations`, `API GET Routes`?**
  _High betweenness centrality (0.262) - this node is a cross-community bridge._
- **What connects `moneybags`, `Bootstrap 5.3.0`, `Bootstrap Icons 1.10.0` to the rest of the system?**
  _27 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Architecture & App Overview Docs` be split into smaller, more focused modules?**
  _Cohesion score 0.07665505226480836 - nodes in this community are weakly interconnected._
- **Why does `Recurring Payments Widget Configuration Design` connect `templates/base.html` to `get_recurring_payment_status`, `Architecture & App Overview Docs`?**
  _High betweenness centrality (0.119) - this node is a cross-community bridge._
- **Should `Budget Calculation JS` be split into smaller, more focused modules?**
  _Cohesion score 0.06968641114982578 - nodes in this community are weakly interconnected._
- **Why does `Configuration Caching (5-minute)` connect `Architecture & App Overview Docs` to `templates/base.html`?**
  _High betweenness centrality (0.104) - this node is a cross-community bridge._

### Low-confidence Hints
_AMBIGUOUS edges — the extractor was unsure. Verify before acting on these._

- **What is the exact relationship between `database_manager.py Layer` and `import_logic.py Import Module`?**
  _Edge tagged AMBIGUOUS (relation: calls) - confidence is low._