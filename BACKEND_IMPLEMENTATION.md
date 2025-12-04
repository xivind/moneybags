# Moneybags Backend Implementation Guide

## Overview

This document describes the complete backend implementation needed to connect the frontend prototype to the MariaDB database. It maps out all required functions in `main.py`, `business_logic.py`, `database_manager.py`, and `utils.py`.

## Architecture Recap

```
Frontend (Templates + JavaScript)
       ↓ (HTTP requests)
main.py (Routing only - NO business logic)
       ↓ (calls business_logic functions)
business_logic.py (Validation, logic, prepares complete data)
       ↓ (passes data dicts to database_manager)
database_manager.py (Pure CRUD operations with PeeWee ORM)
       ↓ (uses models)
database_model.py (Pure data structures)
       ↓
MariaDB (Data storage)
```

**Key Principles:**
- `main.py`: Routing only - parse requests, call business_logic, return responses
- `business_logic.py`: All validation, business rules, data preparation (UUIDs, timestamps, NULL conversion)
- `database_manager.py`: Pure CRUD - no validation, no logic, just database operations
- `utils.py`: Helper functions (UUID generation, empty_to_none, etc.)

---

## Frontend Analysis

### Pages and Operations

**1. Budget Page (`/budget`)**
- Display budget table for selected year
- Edit budget values (modal)
- View/add/edit/delete transactions (modals)
- Switch between years

**2. Config Page (`/config`)**
- Manage categories (list, add, edit, delete with protection)
- Manage payees (list, add, edit, delete with protection, search)
- Manage budget templates by year (which categories appear in each year)
- Configure database connection settings
- Configure currency format

**3. Dashboard (`/`)** - Future implementation
- Overview widgets
- Charts and visualizations

**4. Analysis Page (`/analysis`)** - Future implementation
- Budget vs Actual analysis
- Year-over-year comparisons
- Tag/category analysis
- Time-series analysis

---

## main.py - API Routes

All routes in `main.py` follow this pattern:
1. Parse request data
2. Call business_logic function
3. Handle exceptions
4. Return JSON response

### Page Routes (render templates)

```python
@app.get("/")
async def dashboard(request: Request):
    """Render dashboard page."""
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/budget")
async def budget_page(request: Request):
    """Render budget page."""
    return templates.TemplateResponse("budget.html", {"request": request})

@app.get("/config")
async def config_page(request: Request):
    """Render configuration page."""
    return templates.TemplateResponse("config.html", {"request": request})

@app.get("/analysis")
async def analysis_page(request: Request):
    """Render analysis page."""
    return templates.TemplateResponse("analysis.html", {"request": request})
```

### Budget API Routes

```python
@app.get("/api/budget/{year}")
async def get_budget_data(year: int):
    """
    Get complete budget data for a year.

    Returns:
    {
        "year": 2025,
        "categories": [...],  # Categories active in this year's template
        "budget_entries": {...},  # All budget entries for the year
        "transactions": {...}  # All transactions for the year
    }
    """
    try:
        data = business_logic.get_budget_data_for_year(year)
        return {"success": True, "data": data}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/budget/entry")
async def save_budget_entry(request: Request):
    """
    Create or update budget entry.

    Request body:
    {
        "category_id": "abc123",
        "year": 2025,
        "month": 1,
        "amount": 53000
    }
    """
    try:
        data = await request.json()
        result = business_logic.save_budget_entry(
            category_id=data["category_id"],
            year=data["year"],
            month=data["month"],
            amount=data["amount"]
        )
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/transactions/{category_id}/{year}/{month}")
async def get_transactions(category_id: str, year: int, month: int):
    """Get all transactions for category/year/month."""
    try:
        transactions = business_logic.get_transactions(category_id, year, month)
        return {"success": True, "data": transactions}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/transaction")
async def create_transaction(request: Request):
    """
    Create new transaction.

    Request body:
    {
        "category_id": "abc123",
        "date": "2025-01-15",
        "amount": 55920,
        "payee_id": "def456",  # optional
        "comment": "Salary January"  # optional
    }
    """
    try:
        data = await request.json()
        result = business_logic.create_transaction(
            category_id=data["category_id"],
            date=data["date"],
            amount=data["amount"],
            payee_id=data.get("payee_id"),
            comment=data.get("comment")
        )
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.put("/api/transaction/{transaction_id}")
async def update_transaction(transaction_id: str, request: Request):
    """Update existing transaction."""
    try:
        data = await request.json()
        result = business_logic.update_transaction(
            transaction_id=transaction_id,
            date=data["date"],
            amount=data["amount"],
            payee_id=data.get("payee_id"),
            comment=data.get("comment")
        )
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.delete("/api/transaction/{transaction_id}")
async def delete_transaction(transaction_id: str):
    """Delete transaction."""
    try:
        business_logic.delete_transaction(transaction_id)
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

### Category API Routes

```python
@app.get("/api/categories")
async def get_categories():
    """Get all categories."""
    try:
        categories = business_logic.get_all_categories()
        return {"success": True, "data": categories}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/category")
async def create_category(request: Request):
    """
    Create new category.

    Request body:
    {
        "name": "New Category",
        "type": "income"  # or "expenses"
    }
    """
    try:
        data = await request.json()
        result = business_logic.create_category(
            name=data["name"],
            type=data["type"]
        )
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.put("/api/category/{category_id}")
async def update_category(category_id: str, request: Request):
    """Update category (rename only - type cannot change if data exists)."""
    try:
        data = await request.json()
        result = business_logic.update_category(
            category_id=category_id,
            name=data["name"]
        )
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.delete("/api/category/{category_id}")
async def delete_category(category_id: str):
    """Delete category (only if not in use)."""
    try:
        business_logic.delete_category(category_id)
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

### Payee API Routes

```python
@app.get("/api/payees")
async def get_payees():
    """Get all payees."""
    try:
        payees = business_logic.get_all_payees()
        return {"success": True, "data": payees}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/payee")
async def create_payee(request: Request):
    """
    Create new payee.

    Request body:
    {
        "name": "Netflix",
        "type": "Actual"  # or "Generic"
    }
    """
    try:
        data = await request.json()
        result = business_logic.create_payee(
            name=data["name"],
            type=data.get("type", "Actual")
        )
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.put("/api/payee/{payee_id}")
async def update_payee(payee_id: str, request: Request):
    """Update payee (renames all transaction references)."""
    try:
        data = await request.json()
        result = business_logic.update_payee(
            payee_id=payee_id,
            name=data["name"],
            type=data.get("type")
        )
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.delete("/api/payee/{payee_id}")
async def delete_payee(payee_id: str):
    """Delete payee (only if not in use)."""
    try:
        business_logic.delete_payee(payee_id)
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

### Budget Template API Routes

```python
@app.get("/api/budget-template/{year}")
async def get_budget_template(year: int):
    """Get categories active in year's budget template."""
    try:
        categories = business_logic.get_budget_template(year)
        return {"success": True, "data": categories}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/budget-template")
async def add_category_to_template(request: Request):
    """
    Add category to year's budget template.

    Request body:
    {
        "year": 2025,
        "category_id": "abc123"
    }
    """
    try:
        data = await request.json()
        result = business_logic.add_category_to_template(
            year=data["year"],
            category_id=data["category_id"]
        )
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.delete("/api/budget-template/{year}/{category_id}")
async def remove_category_from_template(year: int, category_id: str):
    """Remove category from year's template (only if no data exists)."""
    try:
        business_logic.remove_category_from_template(year, category_id)
        return {"success": True}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/budget-template/copy")
async def copy_budget_template(request: Request):
    """
    Copy budget template from one year to another.

    Request body:
    {
        "from_year": 2024,
        "to_year": 2025
    }
    """
    try:
        data = await request.json()
        result = business_logic.copy_budget_template(
            from_year=data["from_year"],
            to_year=data["to_year"]
        )
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/years")
async def get_available_years():
    """Get all years that have budget templates."""
    try:
        years = business_logic.get_available_years()
        return {"success": True, "data": years}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

### Configuration API Routes

```python
@app.get("/api/config")
async def get_configuration():
    """Get all configuration settings."""
    try:
        config = business_logic.get_all_configuration()
        return {"success": True, "data": config}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.put("/api/config")
async def update_configuration(request: Request):
    """
    Update configuration settings.

    Request body:
    {
        "currency_format": "nok",
        "db_host": "mariadb",
        ...
    }
    """
    try:
        data = await request.json()
        result = business_logic.update_configuration(data)
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/config/test-db-connection")
async def test_db_connection(request: Request):
    """Test database connection with provided settings."""
    try:
        data = await request.json()
        result = business_logic.test_database_connection(
            host=data["host"],
            port=data["port"],
            database=data["database"],
            user=data["user"],
            password=data["password"]
        )
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

---

## business_logic.py - Business Logic Functions

All functions in `business_logic.py`:
1. Validate input
2. Check business rules
3. Generate UUIDs, timestamps, convert empty to NULL
4. Call database_manager with complete data
5. Return results or raise exceptions

### Initialization

```python
from datetime import datetime
from utils import generate_uid, empty_to_none
import database_manager as db

def initialize_database():
    """Initialize database connection and create tables if needed."""
    db.initialize_connection()
    db.create_tables_if_not_exist()
```

### Budget Entry Functions

```python
def get_budget_data_for_year(year: int) -> dict:
    """
    Get complete budget data for a year.

    Business logic:
    - Validate year is reasonable (e.g., 1900-2100)
    - Get categories from budget_template for this year
    - Get all budget_entries for this year
    - Get all transactions for this year
    - Format data for frontend

    Returns structured dict for frontend consumption.
    """

def save_budget_entry(category_id: str, year: int, month: int, amount: int) -> dict:
    """
    Create or update budget entry.

    Business logic:
    - Validate category_id exists
    - Validate year/month (month 1-12)
    - Validate amount >= 0
    - Check category is in budget_template for this year
    - Check if entry exists (get by category/year/month)
    - If exists: update with new amount, set updated_at
    - If not exists: create new entry with all fields (id, category_id, year, month, amount, created_at, updated_at)
    - Return entry data
    """

def get_transactions(category_id: str, year: int, month: int) -> list:
    """
    Get all transactions for category/year/month.

    Business logic:
    - Validate category_id exists
    - Query transactions by category and date range
    - Include payee information (join)
    - Return list of transaction dicts
    """
```

### Transaction Functions

```python
def create_transaction(category_id: str, date: str, amount: int,
                       payee_id: str = None, comment: str = None) -> dict:
    """
    Create new transaction.

    Business logic:
    - Validate required fields (category_id, date, amount)
    - Validate category_id exists
    - Validate payee_id exists (if provided)
    - Validate date format (YYYY-MM-DD)
    - Validate amount (can be negative for corrections)
    - Convert empty payee_id to NULL (empty_to_none)
    - Convert empty comment to NULL (empty_to_none)
    - Generate UUID
    - Set created_at and updated_at timestamps
    - Prepare complete transaction_data dict
    - Call db.create_transaction(transaction_data)
    - Return transaction data
    """

def update_transaction(transaction_id: str, date: str, amount: int,
                       payee_id: str = None, comment: str = None) -> dict:
    """
    Update existing transaction.

    Business logic:
    - Validate transaction_id exists
    - Validate date and amount
    - Validate payee_id if provided
    - Convert empty strings to NULL
    - Set updated_at timestamp
    - Prepare update data dict
    - Call db.update_transaction(transaction_id, data)
    - Return updated transaction
    """

def delete_transaction(transaction_id: str) -> None:
    """
    Delete transaction.

    Business logic:
    - Validate transaction_id exists
    - Call db.delete_transaction(transaction_id)
    """
```

### Category Functions

```python
def get_all_categories() -> list:
    """
    Get all categories with usage information.

    Business logic:
    - Query all categories
    - For each category, get years used (from budget_templates)
    - For each category, check if has data (budget_entries or transactions)
    - Return list with category info + metadata
    """

def create_category(name: str, type: str) -> dict:
    """
    Create new category.

    Business logic:
    - Validate name not empty
    - Validate type in ['income', 'expenses']
    - Check uniqueness: category name doesn't exist (case-insensitive)
    - Generate UUID
    - Set created_at timestamp
    - Prepare category_data dict
    - Call db.create_category(category_data)
    - Return category data
    """

def update_category(category_id: str, name: str) -> dict:
    """
    Update category (rename only).

    Business logic:
    - Validate category_id exists
    - Validate new name not empty
    - Check new name doesn't conflict with existing (case-insensitive)
    - Update category name
    - NOTE: Type cannot be changed if category has data
    - Return updated category
    """

def delete_category(category_id: str) -> None:
    """
    Delete category.

    Business logic:
    - Validate category_id exists
    - Check NOT in use:
      - No budget_templates reference it
      - No budget_entries reference it
      - No transactions reference it
    - If in use, raise ValueError with message
    - Call db.delete_category(category_id)
    """
```

### Payee Functions

```python
def get_all_payees() -> list:
    """
    Get all payees with usage statistics.

    Business logic:
    - Query all payees
    - For each payee, count transactions
    - For each payee, get last used date
    - Return list with payee info + statistics
    """

def create_payee(name: str, type: str = "Actual") -> dict:
    """
    Create new payee.

    Business logic:
    - Validate name not empty
    - Validate type in ['Generic', 'Actual']
    - Check uniqueness: payee name doesn't exist (case-insensitive)
    - Generate UUID
    - Set created_at timestamp
    - Prepare payee_data dict with type
    - Call db.create_payee(payee_data)
    - Return payee data
    """

def update_payee(payee_id: str, name: str, type: str = None) -> dict:
    """
    Update payee (rename and/or change type).

    Business logic:
    - Validate payee_id exists
    - Validate new name not empty
    - Check new name doesn't conflict with existing (case-insensitive)
    - Update payee name and type
    - Return updated payee
    """

def delete_payee(payee_id: str) -> None:
    """
    Delete payee.

    Business logic:
    - Validate payee_id exists
    - Check NOT in use: no transactions reference it
    - If in use, raise ValueError with count
    - Call db.delete_payee(payee_id)
    """
```

### Budget Template Functions

```python
def get_budget_template(year: int) -> list:
    """
    Get categories active in year's budget template.

    Business logic:
    - Query budget_templates for year
    - Join with categories to get full category info
    - Return list of categories
    """

def add_category_to_template(year: int, category_id: str) -> dict:
    """
    Add category to year's budget template.

    Business logic:
    - Validate year
    - Validate category_id exists
    - Check not already in template (year, category_id unique)
    - Generate UUID
    - Set created_at
    - Prepare template_data dict
    - Call db.create_budget_template(template_data)
    - Return template entry
    """

def remove_category_from_template(year: int, category_id: str) -> None:
    """
    Remove category from year's template.

    Business logic:
    - Validate entry exists
    - Check category has NO data for this year:
      - No budget_entries for this category/year
      - No transactions for this category/year
    - If has data, raise ValueError
    - Call db.delete_budget_template(year, category_id)
    """

def copy_budget_template(from_year: int, to_year: int) -> dict:
    """
    Copy budget template from one year to another.

    Business logic:
    - Validate both years
    - Get all categories from from_year template
    - For each category, add to to_year template (skip if exists)
    - Return count of categories copied
    """

def get_available_years() -> list:
    """
    Get all years that have budget templates.

    Business logic:
    - Query distinct years from budget_templates
    - Return sorted list
    """
```

### Configuration Functions

```python
def get_all_configuration() -> dict:
    """
    Get all configuration as key-value dict.

    Business logic:
    - Query all configuration entries
    - Convert to dict {key: value}
    - Decrypt sensitive values if needed
    - Return config dict
    """

def update_configuration(config_data: dict) -> dict:
    """
    Update configuration settings.

    Business logic:
    - For each key-value in config_data:
      - Validate key is allowed
      - Validate value format for specific keys
      - Check if config entry exists
      - If exists: update value, set updated_at
      - If not exists: create new with id, key, value, created_at, updated_at
    - Encrypt sensitive values (db_password)
    - Return updated config
    """

def test_database_connection(host: str, port: int, database: str,
                             user: str, password: str) -> dict:
    """
    Test database connection with provided settings.

    Business logic:
    - Validate all parameters provided
    - Call db.test_connection(params)
    - Return success/failure with message
    """
```

---

## database_manager.py - Pure CRUD Functions

All functions in `database_manager.py` are pure CRUD - no validation, no logic.
They receive complete data dicts from business_logic and perform database operations.

### Initialization

```python
from peewee import MySQLDatabase
from database_model import database, ALL_MODELS
from database_model import (
    Category, Payee, BudgetTemplate, BudgetEntry,
    Transaction, Configuration
)

def initialize_connection(host: str = None, port: int = 3306,
                         database_name: str = None, user: str = None,
                         password: str = None) -> None:
    """
    Initialize database connection.

    If parameters not provided, load from configuration or environment.
    Set up connection pooling.
    """

def create_tables_if_not_exist() -> None:
    """Create all tables if they don't exist."""
    database.create_tables(ALL_MODELS, safe=True)

def test_connection(host: str, port: int, database_name: str,
                   user: str, password: str) -> bool:
    """Test database connection with provided parameters."""
```

### Category CRUD

```python
def create_category(data: dict) -> Category:
    """Create category with provided data dict."""
    category = Category(**data)
    category.save()
    return category

def get_category_by_id(category_id: str) -> Category:
    """Get category by ID."""
    try:
        return Category.get(Category.id == category_id)
    except Category.DoesNotExist:
        return None

def get_all_categories() -> list:
    """Get all categories."""
    return list(Category.select())

def category_exists(name: str) -> bool:
    """Check if category with name exists (case-insensitive)."""
    return Category.select().where(Category.name.ilike(name)).exists()

def update_category(category_id: str, data: dict) -> Category:
    """Update category fields."""
    category = Category.get(Category.id == category_id)
    for key, value in data.items():
        setattr(category, key, value)
    category.save()
    return category

def delete_category(category_id: str) -> None:
    """Delete category by ID."""
    category = Category.get(Category.id == category_id)
    category.delete_instance()

def category_has_budget_templates(category_id: str) -> bool:
    """Check if category is used in any budget_templates."""
    return BudgetTemplate.select().where(
        BudgetTemplate.category_id == category_id
    ).exists()

def category_has_budget_entries(category_id: str) -> bool:
    """Check if category has any budget_entries."""
    return BudgetEntry.select().where(
        BudgetEntry.category_id == category_id
    ).exists()

def category_has_transactions(category_id: str) -> bool:
    """Check if category has any transactions."""
    return Transaction.select().where(
        Transaction.category_id == category_id
    ).exists()
```

### Payee CRUD

```python
def create_payee(data: dict) -> Payee:
    """Create payee with provided data dict."""
    payee = Payee(**data)
    payee.save()
    return payee

def get_payee_by_id(payee_id: str) -> Payee:
    """Get payee by ID."""
    try:
        return Payee.get(Payee.id == payee_id)
    except Payee.DoesNotExist:
        return None

def get_all_payees() -> list:
    """Get all payees."""
    return list(Payee.select())

def payee_exists(name: str) -> bool:
    """Check if payee with name exists (case-insensitive)."""
    return Payee.select().where(Payee.name.ilike(name)).exists()

def update_payee(payee_id: str, data: dict) -> Payee:
    """Update payee fields."""
    payee = Payee.get(Payee.id == payee_id)
    for key, value in data.items():
        setattr(payee, key, value)
    payee.save()
    return payee

def delete_payee(payee_id: str) -> None:
    """Delete payee by ID."""
    payee = Payee.get(Payee.id == payee_id)
    payee.delete_instance()

def payee_transaction_count(payee_id: str) -> int:
    """Count transactions for payee."""
    return Transaction.select().where(
        Transaction.payee_id == payee_id
    ).count()

def payee_last_used_date(payee_id: str) -> str:
    """Get most recent transaction date for payee."""
    result = (Transaction
              .select(Transaction.date)
              .where(Transaction.payee_id == payee_id)
              .order_by(Transaction.date.desc())
              .first())
    return result.date if result else None
```

### Budget Template CRUD

```python
def create_budget_template(data: dict) -> BudgetTemplate:
    """Create budget template entry with provided data dict."""
    template = BudgetTemplate(**data)
    template.save()
    return template

def get_budget_template_by_year(year: int) -> list:
    """Get all categories in budget template for year."""
    return list(BudgetTemplate
                .select(BudgetTemplate, Category)
                .join(Category)
                .where(BudgetTemplate.year == year))

def budget_template_exists(year: int, category_id: str) -> bool:
    """Check if category is in year's template."""
    return BudgetTemplate.select().where(
        (BudgetTemplate.year == year) &
        (BudgetTemplate.category_id == category_id)
    ).exists()

def delete_budget_template(year: int, category_id: str) -> None:
    """Delete budget template entry."""
    template = BudgetTemplate.get(
        (BudgetTemplate.year == year) &
        (BudgetTemplate.category_id == category_id)
    )
    template.delete_instance()

def get_distinct_years() -> list:
    """Get all distinct years from budget_templates."""
    years = (BudgetTemplate
             .select(BudgetTemplate.year)
             .distinct()
             .order_by(BudgetTemplate.year))
    return [y.year for y in years]
```

### Budget Entry CRUD

```python
def create_budget_entry(data: dict) -> BudgetEntry:
    """Create budget entry with provided data dict."""
    entry = BudgetEntry(**data)
    entry.save()
    return entry

def get_budget_entry(category_id: str, year: int, month: int) -> BudgetEntry:
    """Get budget entry by category/year/month."""
    try:
        return BudgetEntry.get(
            (BudgetEntry.category_id == category_id) &
            (BudgetEntry.year == year) &
            (BudgetEntry.month == month)
        )
    except BudgetEntry.DoesNotExist:
        return None

def get_budget_entries_by_year(year: int) -> list:
    """Get all budget entries for year."""
    return list(BudgetEntry
                .select()
                .where(BudgetEntry.year == year))

def get_budget_entries_by_category_year(category_id: str, year: int) -> list:
    """Get all budget entries for category/year."""
    return list(BudgetEntry
                .select()
                .where(
                    (BudgetEntry.category_id == category_id) &
                    (BudgetEntry.year == year)
                ))

def update_budget_entry(entry_id: str, data: dict) -> BudgetEntry:
    """Update budget entry fields."""
    entry = BudgetEntry.get(BudgetEntry.id == entry_id)
    for key, value in data.items():
        setattr(entry, key, value)
    entry.save()
    return entry

def category_has_budget_entries_for_year(category_id: str, year: int) -> bool:
    """Check if category has budget entries for specific year."""
    return BudgetEntry.select().where(
        (BudgetEntry.category_id == category_id) &
        (BudgetEntry.year == year)
    ).exists()
```

### Transaction CRUD

```python
def create_transaction(data: dict) -> Transaction:
    """Create transaction with provided data dict."""
    transaction = Transaction(**data)
    transaction.save()
    return transaction

def get_transaction_by_id(transaction_id: str) -> Transaction:
    """Get transaction by ID."""
    try:
        return Transaction.get(Transaction.id == transaction_id)
    except Transaction.DoesNotExist:
        return None

def get_transactions_by_category_month(category_id: str, year: int, month: int) -> list:
    """Get transactions for category/year/month."""
    from datetime import date
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)

    return list(Transaction
                .select(Transaction, Payee)
                .join(Payee, join_type='LEFT OUTER')
                .where(
                    (Transaction.category_id == category_id) &
                    (Transaction.date >= start_date) &
                    (Transaction.date < end_date)
                )
                .order_by(Transaction.date))

def get_transactions_by_year(year: int) -> list:
    """Get all transactions for year."""
    from datetime import date
    start_date = date(year, 1, 1)
    end_date = date(year + 1, 1, 1)

    return list(Transaction
                .select()
                .where(
                    (Transaction.date >= start_date) &
                    (Transaction.date < end_date)
                ))

def update_transaction(transaction_id: str, data: dict) -> Transaction:
    """Update transaction fields."""
    transaction = Transaction.get(Transaction.id == transaction_id)
    for key, value in data.items():
        setattr(transaction, key, value)
    transaction.save()
    return transaction

def delete_transaction(transaction_id: str) -> None:
    """Delete transaction by ID."""
    transaction = Transaction.get(Transaction.id == transaction_id)
    transaction.delete_instance()

def category_has_transactions_for_year(category_id: str, year: int) -> bool:
    """Check if category has transactions for specific year."""
    from datetime import date
    start_date = date(year, 1, 1)
    end_date = date(year + 1, 1, 1)

    return Transaction.select().where(
        (Transaction.category_id == category_id) &
        (Transaction.date >= start_date) &
        (Transaction.date < end_date)
    ).exists()
```

### Configuration CRUD

```python
def create_configuration(data: dict) -> Configuration:
    """Create configuration entry with provided data dict."""
    config = Configuration(**data)
    config.save()
    return config

def get_configuration_by_key(key: str) -> Configuration:
    """Get configuration by key."""
    try:
        return Configuration.get(Configuration.key == key)
    except Configuration.DoesNotExist:
        return None

def get_all_configuration() -> list:
    """Get all configuration entries."""
    return list(Configuration.select())

def update_configuration(key: str, data: dict) -> Configuration:
    """Update configuration entry."""
    config = Configuration.get(Configuration.key == key)
    for k, value in data.items():
        setattr(config, k, value)
    config.save()
    return config
```

---

## utils.py - Helper Functions

Additional helper functions that may be needed.

### Existing Functions

```python
def generate_uid() -> str:
    """Generate unique record ID using UUID + timestamp."""
    # Already implemented

def empty_to_none(value):
    """Convert empty string or whitespace-only string to None."""
    # Already implemented
```

### Additional Helper Functions

```python
def validate_date_format(date_str: str) -> bool:
    """
    Validate date string is in YYYY-MM-DD format.

    Returns True if valid, False otherwise.
    """
    from datetime import datetime
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False

def validate_month(month: int) -> bool:
    """Validate month is 1-12."""
    return 1 <= month <= 12

def validate_year(year: int) -> bool:
    """Validate year is reasonable (1900-2100)."""
    return 1900 <= year <= 2100

def get_month_date_range(year: int, month: int) -> tuple:
    """
    Get start and end dates for a month.

    Returns (start_date, end_date) as date objects.
    """
    from datetime import date
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1)
    else:
        end_date = date(year, month + 1, 1)
    return (start_date, end_date)

def format_currency(amount: int, currency: str = 'nok') -> str:
    """
    Format integer amount as currency string.

    Examples:
    - format_currency(53000, 'nok') -> "kr 53,000"
    - format_currency(1234, 'usd') -> "$1,234"
    - format_currency(5678, 'eur') -> "€5,678"
    """
    # Implementation based on currency format

def encrypt_value(value: str) -> str:
    """Encrypt sensitive configuration value (e.g., passwords)."""
    # Implementation for production use

def decrypt_value(encrypted: str) -> str:
    """Decrypt sensitive configuration value."""
    # Implementation for production use
```

---

## Implementation Checklist

### Phase 1: Database Setup
- [ ] Implement `database_manager.py` initialization functions
- [ ] Implement connection pooling
- [ ] Test database connection
- [ ] Create tables
- [ ] Add seed data (initial categories, config)

### Phase 2: Core CRUD (database_manager.py)
- [ ] Category CRUD functions
- [ ] Payee CRUD functions
- [ ] Budget Template CRUD functions
- [ ] Budget Entry CRUD functions
- [ ] Transaction CRUD functions
- [ ] Configuration CRUD functions

### Phase 3: Business Logic (business_logic.py)
- [ ] Category business logic with validation
- [ ] Payee business logic with validation
- [ ] Budget template business logic
- [ ] Budget entry business logic
- [ ] Transaction business logic
- [ ] Configuration business logic
- [ ] Database connection testing logic

### Phase 4: API Routes (main.py)
- [ ] Page render routes
- [ ] Budget API routes
- [ ] Category API routes
- [ ] Payee API routes
- [ ] Budget template API routes
- [ ] Configuration API routes
- [ ] Error handling and logging

### Phase 5: Frontend Integration
- [ ] Update JavaScript to call real API endpoints
- [ ] Remove mock data from app.js
- [ ] Handle loading states
- [ ] Handle error states


### Phase 6: Testing & Deployment - ASK FOR CONFIRMATION BEFORE ENTERING THIS PART
- [ ] Unit tests for business_logic functions
- [ ] Integration tests for API routes
- [ ] Test all CRUD operations end-to-end
- [ ] Database migration scripts
- [ ] Docker configuration
- [ ] Logging configuration
- [ ] Production deployment

---

## Notes

**Error Handling Pattern:**
All functions should raise appropriate exceptions with clear messages:
- `ValueError` for validation errors
- `DoesNotExist` for missing records (PeeWee exception)
- `IntegrityError` for database constraint violations (PeeWee exception)

**Transaction Management:**
All write operations in `database_manager.py` should use database transactions for atomicity.

**Performance Considerations:**
- Use JOIN queries to fetch related data in single query
- Consider caching configuration data
- Use connection pooling for htmx performance
- Add indexes as needed based on query patterns

**Security:**
- Validate and sanitize all user input in business_logic.py
- Use parameterized queries (PeeWee handles this)
- Encrypt sensitive configuration values
- Use environment variables for initial database bootstrap
- Never commit database credentials to git

---

## Summary

This document provides a complete roadmap for implementing the backend:

1. **main.py**: 30+ API routes for frontend operations
2. **business_logic.py**: 20+ business logic functions with validation
3. **database_manager.py**: 50+ pure CRUD functions
4. **utils.py**: 8+ helper functions

All functions follow the clean architecture pattern:
- Routing → Business Logic → Database Manager → Models → Database

With this implementation, the frontend prototype will connect to the real database, and the application will be fully functional.
