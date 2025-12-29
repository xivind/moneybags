"""
Business logic for Moneybags application.

All validation, business rules, and data preparation happens here.
This module prepares complete data dicts with UUIDs, timestamps, and NULL conversion
before passing to database_manager.py for pure CRUD operations.

DO NOT call database methods directly - always use database_manager module.

See BACKEND_IMPLEMENTATION.md for complete documentation.
"""

import logging
import os
import json
from datetime import datetime
from typing import Optional
from utils import generate_uid, empty_to_none, validate_date_format, validate_month, validate_year
import database_manager as db

logger = logging.getLogger(__name__)

# Configuration cache for performance
# Avoids repeated database queries for config values
_config_cache = {}
_cache_timestamp = None
CACHE_TIMEOUT = 300  # 5 minutes

# Database configuration state
DATABASE_CONFIGURED = False

# Try multiple paths for database config file (Docker vs local development)
DB_CONFIG_PATHS = [
    "/app/data/moneybags_db_config.json",  # Docker container path
    "./moneybags_db_config.json",           # Local development (project root)
    "./data/moneybags_db_config.json"       # Local development (data subdirectory)
]


# ==================== HELPER FUNCTIONS ====================

def _extract_amounts_from_formula(cell_value, row_num: int, col_name: str) -> list[int]:
    """
    Extract individual amounts from Excel formula or value.

    Strict validation - only simple addition formulas allowed.

    Args:
        cell_value: Cell value (formula string or number)
        row_num: Row number for error messages
        col_name: Column name for error messages

    Returns:
        List of integer amounts extracted from formula

    Raises:
        ValueError: On invalid formula format or negative values

    Examples:
        "=575+2182" → [575, 2182]
        "=104571" → [104571]
        "55615.0" → [55615]
        "0" → [0]
        "" → []
    """
    # Handle None or empty
    if cell_value is None or cell_value == "":
        return []

    # Convert to string
    formula_str = str(cell_value).strip()

    # Empty after strip
    if not formula_str:
        return []

    # Remove "=" prefix if present
    if formula_str.startswith("="):
        formula_str = formula_str[1:]

    # Check for forbidden operations/functions
    forbidden = ["IF", "SUM", "AVERAGE", "COUNT", "MIN", "MAX", "*", "/", "-", "(", ")"]
    for forbidden_item in forbidden:
        if forbidden_item in formula_str:
            if forbidden_item in ["IF", "SUM", "AVERAGE", "COUNT", "MIN", "MAX"]:
                raise ValueError(f"Row {row_num}, Column {col_name}: Complex formula not supported ({forbidden_item})")
            elif forbidden_item == "-":
                # Allow negative check after splitting
                pass
            else:
                raise ValueError(f"Row {row_num}, Column {col_name}: Only addition (+) supported")

    # Split by "+"
    parts = formula_str.split("+")

    # Convert to integers
    amounts = []
    for part in parts:
        part = part.strip()
        if not part:
            continue

        try:
            # Convert to float first (handles decimals), then to int
            value = int(float(part))

            # Reject negative values
            if value < 0:
                raise ValueError(f"Row {row_num}, Column {col_name}: Negative value not allowed ({value})")

            amounts.append(value)
        except ValueError as e:
            if "Negative value not allowed" in str(e):
                raise
            raise ValueError(f"Row {row_num}, Column {col_name}: Invalid number format: {part}")

    return amounts


# ==================== INITIALIZATION ====================

def _get_config_file_path() -> str:
    """
    Get the path to the database configuration file.

    Tries multiple paths in order:
    1. /app/data/moneybags_db_config.json (Docker container)
    2. ./moneybags_db_config.json (local dev - project root)
    3. ./data/moneybags_db_config.json (local dev - data subdirectory)

    Returns:
        str: Path to the config file (may not exist yet)
    """
    for path in DB_CONFIG_PATHS:
        if os.path.exists(path):
            return path

    # If none exist, return the first writable path
    # In Docker: /app/data/moneybags_db_config.json
    # Local dev: ./moneybags_db_config.json
    if os.path.exists("/app/data"):
        return DB_CONFIG_PATHS[0]  # Docker
    else:
        return DB_CONFIG_PATHS[1]  # Local dev


def load_database_config() -> dict:
    """
    Load database configuration from moneybags_db_config.json file.

    Returns:
        dict: Database configuration with keys: db_host, db_port, db_name, db_user, db_password, db_pool_size
        None if file doesn't exist
    """
    config_file = _get_config_file_path()

    if not os.path.exists(config_file):
        return None

    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
            logger.info(f"Database configuration loaded from {config_file}")
            return config
    except Exception as e:
        logger.error(f"Failed to read {config_file}: {e}")
        return None


def save_database_config(config: dict) -> None:
    """
    Save database configuration to moneybags_db_config.json file.

    Args:
        config: Dictionary with keys: db_host, db_port, db_name, db_user, db_password, db_pool_size
    """
    config_file = _get_config_file_path()

    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        logger.info(f"Database configuration saved to {config_file}")
    except Exception as e:
        logger.error(f"Failed to write {config_file}: {e}")
        raise ValueError(f"Failed to save database configuration: {e}")


def initialize_database():
    """Initialize database connection and create tables if needed."""
    global DATABASE_CONFIGURED

    try:
        # Load connection settings from moneybags_db_config.json
        config = load_database_config()

        if config is None:
            logger.warning("Database not configured - moneybags_db_config.json not found")
            DATABASE_CONFIGURED = False
            return

        # Extract connection parameters
        host = config.get('db_host', 'localhost')
        port = int(config.get('db_port', 3306))
        database = config.get('db_name', 'moneybags')
        user = config.get('db_user', 'moneybags_user')
        password = config.get('db_password', 'moneybags_pass')
        pool_size = int(config.get('db_pool_size', 10))

        logger.info(f"Connecting to database: {host}:{port}/{database}")

        db.initialize_connection(
            host=host,
            port=port,
            database_name=database,
            user=user,
            password=password,
            pool_size=pool_size
        )
        db.create_tables_if_not_exist()
        logger.info("Database initialized successfully")
        DATABASE_CONFIGURED = True

        # Seed initial data if not already seeded
        try:
            seeded_config = db.get_configuration_by_key('database_seeded')
            is_seeded = seeded_config.value == 'true'
        except Exception:
            # Configuration doesn't exist yet
            is_seeded = False

        if not is_seeded:
            db.seed_initial_data()
            # Mark database as seeded
            seeded_config = {
                'id': generate_uid(),
                'key': 'database_seeded',
                'value': 'true',
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
            db.create_configuration(seeded_config)
            logger.info("Database seeded with initial data")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        DATABASE_CONFIGURED = False
        # Don't raise - allow app to start so user can fix configuration


# ==================== CATEGORY BUSINESS LOGIC ====================

def get_all_categories() -> list:
    """
    Get all categories with usage information.

    Returns list with category info + metadata about years used and whether
    category has data.
    """
    try:
        categories = db.get_all_categories()
        result = []

        for cat in categories:
            # Get years this category is used in budget templates
            templates = db.get_budget_template_by_year(2020)  # Need to check all years
            years_used = []
            for year in db.get_distinct_years():
                if db.budget_template_exists(year, cat.id):
                    # Check if has actual data
                    has_data = (db.category_has_budget_entries_for_year(cat.id, year) or
                              db.category_has_transactions_for_year(cat.id, year))
                    if has_data:
                        years_used.append(year)

            result.append({
                'id': cat.id,
                'name': cat.name,
                'type': cat.type,
                'years_used': years_used,
                'has_data': len(years_used) > 0
            })

        return result
    except Exception as e:
        logger.error(f"Failed to get categories: {e}")
        raise


def create_category(name: str, type: str) -> dict:
    """
    Create new category.

    Business logic:
    - Validate name not empty
    - Validate type in ['income', 'expenses']
    - Check uniqueness: category name doesn't exist (case-insensitive)
    - Generate UUID and timestamp
    - Create category
    """
    try:
        # Validation
        if not name or not name.strip():
            raise ValueError("Category name is required")

        name = name.strip()

        if type not in ['income', 'expenses']:
            raise ValueError("Category type must be 'income' or 'expenses'")

        # Check uniqueness
        if db.category_exists_by_name(name):
            raise ValueError(f"Category '{name}' already exists")

        # Prepare complete record
        category_data = {
            'id': generate_uid(),
            'name': name,
            'type': type,
            'created_at': datetime.now()
        }

        # Create
        category = db.create_category(category_data)
        logger.info(f"Business logic: Created category {name}")

        return {
            'id': category.id,
            'name': category.name,
            'type': category.type
        }
    except Exception as e:
        logger.error(f"Failed to create category: {e}")
        raise


def update_category(category_id: str, name: str) -> dict:
    """
    Update category (rename only).

    Business logic:
    - Validate category_id exists
    - Validate new name not empty
    - Check new name doesn't conflict with existing (case-insensitive)
    - Update category name
    - Note: Type cannot be changed if category has data
    """
    try:
        # Validate category exists
        category = db.get_category_by_id(category_id)
        if not category:
            raise ValueError(f"Category {category_id} not found")

        # Validate name
        if not name or not name.strip():
            raise ValueError("Category name is required")

        name = name.strip()

        # Check uniqueness (skip if name hasn't changed)
        if name.lower() != category.name.lower():
            if db.category_exists_by_name(name):
                raise ValueError(f"Category '{name}' already exists")

        # Update
        updated_category = db.update_category(category_id, {'name': name})
        logger.info(f"Business logic: Updated category {category_id}")

        return {
            'id': updated_category.id,
            'name': updated_category.name,
            'type': updated_category.type
        }
    except Exception as e:
        logger.error(f"Failed to update category: {e}")
        raise


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
    """
    try:
        # Validate category exists
        category = db.get_category_by_id(category_id)
        if not category:
            raise ValueError(f"Category {category_id} not found")

        # Check usage
        if db.category_has_budget_templates(category_id):
            raise ValueError(f"Cannot delete category '{category.name}' - it is used in budget templates")

        if db.category_has_budget_entries(category_id):
            raise ValueError(f"Cannot delete category '{category.name}' - it has budget entries")

        if db.category_has_transactions(category_id):
            raise ValueError(f"Cannot delete category '{category.name}' - it has transactions")

        # Delete
        db.delete_category(category_id)
        logger.info(f"Business logic: Deleted category {category_id}")
    except Exception as e:
        logger.error(f"Failed to delete category: {e}")
        raise


# ==================== PAYEE BUSINESS LOGIC ====================

def get_all_payees() -> list:
    """
    Get all payees with usage statistics.

    Returns list with payee info + statistics (transaction count, last used).
    """
    try:
        payees = db.get_all_payees()
        result = []

        for payee in payees:
            count = db.payee_transaction_count(payee.id)
            last_used = db.payee_last_used_date(payee.id)

            result.append({
                'id': payee.id,
                'name': payee.name,
                'type': payee.type,
                'transaction_count': count,
                'last_used': str(last_used) if last_used else None
            })

        return result
    except Exception as e:
        logger.error(f"Failed to get payees: {e}")
        raise


def create_payee(name: str, type: str = "Actual") -> dict:
    """
    Create new payee.

    Business logic:
    - Validate name not empty
    - Validate type in ['Generic', 'Actual']
    - Check uniqueness: payee name doesn't exist (case-insensitive)
    - Generate UUID and timestamp
    - Create payee
    """
    try:
        # Validation
        if not name or not name.strip():
            raise ValueError("Payee name is required")

        name = name.strip()

        if type not in ['Generic', 'Actual']:
            raise ValueError("Payee type must be 'Generic' or 'Actual'")

        # Check uniqueness
        if db.payee_exists_by_name(name):
            raise ValueError(f"Payee '{name}' already exists")

        # Prepare complete record
        payee_data = {
            'id': generate_uid(),
            'name': name,
            'type': type,
            'created_at': datetime.now()
        }

        # Create
        payee = db.create_payee(payee_data)
        logger.info(f"Business logic: Created payee {name}")

        return {
            'id': payee.id,
            'name': payee.name,
            'type': payee.type
        }
    except Exception as e:
        logger.error(f"Failed to create payee: {e}")
        raise


def update_payee(payee_id: str, name: str, type: Optional[str] = None) -> dict:
    """
    Update payee (rename and/or change type).

    Business logic:
    - Validate payee_id exists
    - Validate new name not empty
    - Check new name doesn't conflict with existing (case-insensitive)
    - Update payee
    """
    try:
        # Validate payee exists
        payee = db.get_payee_by_id(payee_id)
        if not payee:
            raise ValueError(f"Payee {payee_id} not found")

        # Validate name
        if not name or not name.strip():
            raise ValueError("Payee name is required")

        name = name.strip()

        # Check uniqueness (skip if name hasn't changed)
        if name.lower() != payee.name.lower():
            if db.payee_exists_by_name(name):
                raise ValueError(f"Payee '{name}' already exists")

        # Prepare update data
        update_data = {'name': name}
        if type:
            if type not in ['Generic', 'Actual']:
                raise ValueError("Payee type must be 'Generic' or 'Actual'")
            update_data['type'] = type

        # Update
        updated_payee = db.update_payee(payee_id, update_data)
        logger.info(f"Business logic: Updated payee {payee_id}")

        return {
            'id': updated_payee.id,
            'name': updated_payee.name,
            'type': updated_payee.type
        }
    except Exception as e:
        logger.error(f"Failed to update payee: {e}")
        raise


def delete_payee(payee_id: str) -> None:
    """
    Delete payee.

    Business logic:
    - Validate payee_id exists
    - Check NOT in use: no transactions reference it
    - If in use, raise ValueError with count
    """
    try:
        # Validate payee exists
        payee = db.get_payee_by_id(payee_id)
        if not payee:
            raise ValueError(f"Payee {payee_id} not found")

        # Check usage
        count = db.payee_transaction_count(payee_id)
        if count > 0:
            raise ValueError(f"Cannot delete payee '{payee.name}' - it is used in {count} transactions")

        # Delete
        db.delete_payee(payee_id)
        logger.info(f"Business logic: Deleted payee {payee_id}")
    except Exception as e:
        logger.error(f"Failed to delete payee: {e}")
        raise


# ==================== BUDGET TEMPLATE BUSINESS LOGIC ====================

def get_budget_template(year: int) -> list:
    """
    Get categories active in year's budget template.

    Business logic:
    - Query budget_templates for year
    - Join with categories to get full category info
    - Return list of categories
    """
    try:
        if not validate_year(year):
            raise ValueError(f"Invalid year: {year}")

        templates = db.get_budget_template_by_year(year)

        result = []
        for template in templates:
            result.append({
                'id': template.category_id.id,
                'name': template.category_id.name,
                'type': template.category_id.type
            })

        return result
    except Exception as e:
        logger.error(f"Failed to get budget template: {e}")
        raise


def add_category_to_template(year: int, category_id: str) -> dict:
    """
    Add category to year's budget template.

    Business logic:
    - Validate year
    - Validate category_id exists
    - Check not already in template (year, category_id unique)
    - Generate UUID and timestamp
    - Create budget template entry
    """
    try:
        if not validate_year(year):
            raise ValueError(f"Invalid year: {year}")

        # Validate category exists
        category = db.get_category_by_id(category_id)
        if not category:
            raise ValueError(f"Category {category_id} not found")

        # Check not already in template
        if db.budget_template_exists(year, category_id):
            raise ValueError(f"Category '{category.name}' is already in budget template for {year}")

        # Prepare complete record
        template_data = {
            'id': generate_uid(),
            'year': year,
            'category_id': category_id,
            'created_at': datetime.now()
        }

        # Create
        template = db.create_budget_template(template_data)
        logger.info(f"Business logic: Added category {category_id} to template for {year}")

        return {
            'year': template.year,
            'category_id': template.category_id
        }
    except Exception as e:
        logger.error(f"Failed to add category to template: {e}")
        raise


def remove_category_from_template(year: int, category_id: str) -> None:
    """
    Remove category from year's template.

    Business logic:
    - Validate entry exists
    - Check category has NO data for this year:
      - No budget_entries for this category/year
      - No transactions for this category/year
    - If has data, raise ValueError
    """
    try:
        if not validate_year(year):
            raise ValueError(f"Invalid year: {year}")

        # Validate template exists
        if not db.budget_template_exists(year, category_id):
            raise ValueError(f"Category {category_id} not found in budget template for {year}")

        # Check for data
        if db.category_has_budget_entries_for_year(category_id, year):
            raise ValueError(f"Cannot remove category - it has budget entries for {year}")

        if db.category_has_transactions_for_year(category_id, year):
            raise ValueError(f"Cannot remove category - it has transactions for {year}")

        # Delete
        db.delete_budget_template(year, category_id)
        logger.info(f"Business logic: Removed category {category_id} from template for {year}")
    except Exception as e:
        logger.error(f"Failed to remove category from template: {e}")
        raise


def copy_budget_template(from_year: int, to_year: int) -> dict:
    """
    Copy budget template from one year to another.

    Business logic:
    - Validate both years
    - Get all categories from from_year template
    - For each category, add to to_year template (skip if exists)
    - Return count of categories copied
    """
    try:
        if not validate_year(from_year):
            raise ValueError(f"Invalid from_year: {from_year}")
        if not validate_year(to_year):
            raise ValueError(f"Invalid to_year: {to_year}")

        # Get source template
        source_templates = db.get_budget_template_by_year(from_year)

        copied_count = 0
        for template in source_templates:
            try:
                add_category_to_template(to_year, template.category_id.id)
                copied_count += 1
            except ValueError:
                # Category already exists in target year, skip
                pass

        logger.info(f"Business logic: Copied {copied_count} categories from {from_year} to {to_year}")

        return {
            'from_year': from_year,
            'to_year': to_year,
            'copied_count': copied_count
        }
    except Exception as e:
        logger.error(f"Failed to copy budget template: {e}")
        raise


def get_available_years() -> list:
    """
    Get all years that have budget templates.

    Business logic:
    - Query distinct years from budget_templates
    - Return sorted list
    """
    try:
        years = db.get_distinct_years()
        return sorted(years)
    except Exception as e:
        logger.error(f"Failed to get available years: {e}")
        raise


# ==================== BUDGET ENTRY BUSINESS LOGIC ====================

def get_budget_data_for_year(year: int) -> dict:
    """
    Get complete budget data for a year.

    Business logic:
    - Validate year
    - Get categories from budget_template for this year
    - Get all budget_entries for this year
    - Get all transactions for this year
    - Format data for frontend consumption
    """
    import time
    start_time = time.time()
    logger.debug(f"[BUDGET_DATA] Starting get_budget_data_for_year({year})")

    try:
        if not validate_year(year):
            raise ValueError(f"Invalid year: {year}")

        # Get categories for this year
        t1 = time.time()
        categories = get_budget_template(year)
        logger.debug(f"[BUDGET_DATA] Get categories took {(time.time()-t1)*1000:.2f}ms")

        # Get budget entries - organized by category and month
        t2 = time.time()
        budget_entries = db.get_budget_entries_by_year(year)
        logger.debug(f"[BUDGET_DATA] Get budget entries took {(time.time()-t2)*1000:.2f}ms")
        budget_dict = {}
        for entry in budget_entries:
            cat_id = entry.category_id if isinstance(entry.category_id, str) else entry.category_id.id
            if cat_id not in budget_dict:
                budget_dict[cat_id] = {}
            budget_dict[cat_id][entry.month] = {
                'amount': entry.amount,
                'id': entry.id,
                'comment': entry.comment
            }

        # Get transactions - organized by category and month (nested structure)
        t3 = time.time()
        transactions = db.get_transactions_by_year(year)
        logger.debug(f"[BUDGET_DATA] Get transactions took {(time.time()-t3)*1000:.2f}ms")
        transactions_dict = {}
        for t in transactions:
            month = t.date.month
            cat_id = t.category_id if isinstance(t.category_id, str) else t.category_id.id
            if cat_id not in transactions_dict:
                transactions_dict[cat_id] = {}
            if month not in transactions_dict[cat_id]:
                transactions_dict[cat_id][month] = []
            transactions_dict[cat_id][month].append({
                'id': t.id,
                'category_id': cat_id,
                'payee_id': t.payee_id.id if t.payee_id else None,
                'payee_name': t.payee_id.name if t.payee_id else None,
                'date': str(t.date),
                'amount': t.amount,
                'comment': t.comment
            })

        total_time = (time.time() - start_time) * 1000
        logger.debug(f"[BUDGET_DATA] Total get_budget_data_for_year({year}) took {total_time:.2f}ms")

        return {
            'year': year,
            'categories': categories,
            'budget_entries': budget_dict,
            'transactions': transactions_dict
        }
    except Exception as e:
        logger.error(f"Failed to get budget data for year: {e}")
        raise


def calculate_category_trends(year: int, category_id: str) -> dict:
    """
    Calculate year-over-year trends for a category.

    Compares current year to previous year for budget and actuals.
    Returns arrow direction and color based on category type.

    Business logic:
    - Compare year to year-1
    - For each month (1-12) + total:
      - Budget: compare budget amounts
      - Actual: compare transaction totals
    - Income: increase = green up, decrease = red down
    - Expense: increase = red up, decrease = green down
    - Same value = grey right
    - No comparison data = None (no arrow)

    Returns:
    {
        "months": {
            "1": {"budget": {"arrow": "up", "color": "success"}, "actual": {"arrow": "down", "color": "danger"}},
            ...
        },
        "total": {"budget": {"arrow": "right", "color": "secondary"}, "actual": None}
    }
    """
    import time
    start_time = time.time()
    logger.debug(f"[TRENDS] Starting trend calculation for category {category_id}, year {year}")

    try:
        if not validate_year(year):
            raise ValueError(f"Invalid year: {year}")

        # Get category to determine type (income/expense)
        t1 = time.time()
        category = db.get_category_by_id(category_id)
        logger.debug(f"[TRENDS] Get category took {(time.time()-t1)*1000:.2f}ms")
        if not category:
            raise ValueError(f"Category not found: {category_id}")

        # Get current year and previous year data
        t2 = time.time()
        current_year_data = get_budget_data_for_year(year)
        logger.debug(f"[TRENDS] Get current year data took {(time.time()-t2)*1000:.2f}ms")

        try:
            t3 = time.time()
            previous_year_data = get_budget_data_for_year(year - 1)
            logger.debug(f"[TRENDS] Get previous year data took {(time.time()-t3)*1000:.2f}ms")
        except:
            # Previous year doesn't exist - return None for all trends
            logger.debug(f"[TRENDS] Previous year {year-1} doesn't exist, returning None trends")
            return {
                "months": {str(m): {"budget": None, "actual": None} for m in range(1, 13)},
                "total": {"budget": None, "actual": None}
            }

        # Check if category exists in both years
        current_budget = current_year_data['budget_entries'].get(category_id, {})
        previous_budget = previous_year_data['budget_entries'].get(category_id, {})
        current_transactions = current_year_data['transactions'].get(category_id, {})
        previous_transactions = previous_year_data['transactions'].get(category_id, {})

        def calculate_trend(current_value, previous_value, category_type):
            """
            Helper to calculate trend arrow and color.

            Note: 0 is a valid value (user entered zero), None means no data entered.

            Arrow types based on percentage change:
            - ≤ 5%: right arrow (grey) - minimal change (inflation/noise)
            - > 5% and ≤ 25%: diagonal arrow (colored) - moderate change
            - > 25%: straight arrow (colored) - significant change
            """
            # No arrow if current year has no data entered (None/NULL, not 0)
            if current_value is None:
                return None

            # No arrow if previous year has no data to compare against (None/NULL, not 0)
            if previous_value is None:
                return None

            # Calculate percentage change
            # Handle division by zero (previous_value could be 0)
            if previous_value == 0:
                # If previous was 0 and current is not 0, that's infinite change
                # Treat as significant change (>25%)
                if current_value == 0:
                    return {"arrow": "right", "color": "secondary"}
                else:
                    percentage_change = 100  # Force significant change threshold
            else:
                percentage_change = abs((current_value - previous_value) / previous_value * 100)

            # Determine direction
            is_increase = current_value > previous_value

            # Determine arrow type based on percentage change
            if percentage_change <= 5:
                # Minimal change - grey right arrow (inflation/noise)
                return {"arrow": "right", "color": "secondary"}
            elif percentage_change <= 25:
                # Moderate change - diagonal arrow with color
                if is_increase:
                    arrow = "up-right"
                else:
                    arrow = "down-right"
            else:
                # Significant change (>25%) - straight arrow with color
                if is_increase:
                    arrow = "up"
                else:
                    arrow = "down"

            # Determine color based on category type and direction
            if category_type == 'income':
                # Income: increase is good, decrease is bad
                color = "success" if is_increase else "danger"
            else:  # expenses
                # Expense: decrease is good, increase is bad
                color = "success" if not is_increase else "danger"

            return {"arrow": arrow, "color": color}

        # Calculate trends for each month
        months_trends = {}
        current_budget_total = 0
        previous_budget_total = 0
        current_actual_total = 0
        previous_actual_total = 0
        has_current_budget = False
        has_previous_budget = False
        has_current_actual = False
        has_previous_actual = False

        for month in range(1, 13):
            # Budget trend
            current_budget_amount = current_budget.get(month, {}).get('amount', 0)
            previous_budget_amount = previous_budget.get(month, {}).get('amount', 0)
            budget_trend = calculate_trend(current_budget_amount, previous_budget_amount, category.type)

            # Track if we have any budget entries
            if month in current_budget:
                has_current_budget = True
                current_budget_total += current_budget_amount
            if month in previous_budget:
                has_previous_budget = True
                previous_budget_total += previous_budget_amount

            # Actual trend (pass None if no transactions, not 0)
            current_month_transactions = current_transactions.get(month, [])
            previous_month_transactions = previous_transactions.get(month, [])

            current_actual_amount = sum(t['amount'] for t in current_month_transactions) if len(current_month_transactions) > 0 else None
            previous_actual_amount = sum(t['amount'] for t in previous_month_transactions) if len(previous_month_transactions) > 0 else None

            actual_trend = calculate_trend(current_actual_amount, previous_actual_amount, category.type)

            # Track if we have any transactions
            if month in current_transactions and len(current_transactions[month]) > 0:
                has_current_actual = True
                current_actual_total += current_actual_amount
            if month in previous_transactions and len(previous_transactions[month]) > 0:
                has_previous_actual = True
                previous_actual_total += previous_actual_amount

            months_trends[str(month)] = {
                "budget": budget_trend,
                "actual": actual_trend
            }

        # Calculate total trends (pass None if no data, not 0)
        budget_total_trend = calculate_trend(
            current_budget_total if has_current_budget else None,
            previous_budget_total if has_previous_budget else None,
            category.type
        )
        actual_total_trend = calculate_trend(
            current_actual_total if has_current_actual else None,
            previous_actual_total if has_previous_actual else None,
            category.type
        )

        total_time = (time.time() - start_time) * 1000
        logger.debug(f"[TRENDS] Total trend calculation took {total_time:.2f}ms for category {category_id}")

        return {
            "months": months_trends,
            "total": {
                "budget": budget_total_trend,
                "actual": actual_total_trend
            }
        }
    except Exception as e:
        logger.error(f"Failed to calculate trends: {e}")
        raise


def save_budget_entry(category_id: str, year: int, month: int, amount: int, comment: str = None) -> dict:
    """
    Create or update budget entry.

    Business logic:
    - Validate category_id exists
    - Validate year/month (month 1-12)
    - Validate amount >= 0
    - Check category is in budget_template for this year
    - Check if entry exists (get by category/year/month)
    - If exists: update with new amount and comment, set updated_at
    - If not exists: create new entry with all fields
    - Empty comment stored as NULL (via utils.empty_to_none)
    """
    try:
        # Validate
        category = db.get_category_by_id(category_id)
        if not category:
            raise ValueError(f"Category {category_id} not found")

        if not validate_year(year):
            raise ValueError(f"Invalid year: {year}")

        if not validate_month(month):
            raise ValueError(f"Invalid month: {month}. Must be 1-12")

        if not isinstance(amount, int) or amount < 0:
            raise ValueError("Amount must be a non-negative integer")

        # Check category in template
        if not db.budget_template_exists(year, category_id):
            raise ValueError(f"Category not in budget template for {year}")

        # Convert empty comment to NULL
        comment = empty_to_none(comment)

        # Check if entry exists
        existing_entry = db.get_budget_entry(category_id, year, month)

        if existing_entry:
            # Update
            update_data = {
                'amount': amount,
                'comment': comment,
                'updated_at': datetime.now()
            }
            entry = db.update_budget_entry(existing_entry.id, update_data)
            logger.info(f"Business logic: Updated budget entry {existing_entry.id}")
        else:
            # Create
            entry_data = {
                'id': generate_uid(),
                'category_id': category_id,
                'year': year,
                'month': month,
                'amount': amount,
                'comment': comment,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            }
            entry = db.create_budget_entry(entry_data)
            logger.info(f"Business logic: Created budget entry")

        return {
            'id': entry.id,
            'category_id': entry.category_id,
            'year': entry.year,
            'month': entry.month,
            'amount': entry.amount,
            'comment': entry.comment
        }
    except Exception as e:
        logger.error(f"Failed to save budget entry: {e}")
        raise


def delete_budget_entry(entry_id: str) -> None:
    """
    Delete budget entry.

    Business logic:
    - Validate entry_id exists
    - Delete budget entry
    """
    try:
        # Validate entry exists
        entry = db.get_budget_entry_by_id(entry_id)
        if not entry:
            raise ValueError(f"Budget entry {entry_id} not found")

        # Delete
        db.delete_budget_entry(entry_id)
        logger.info(f"Business logic: Deleted budget entry {entry_id}")
    except Exception as e:
        logger.error(f"Failed to delete budget entry: {e}")
        raise


# ==================== TRANSACTION BUSINESS LOGIC ====================

def get_transactions(category_id: str, year: int, month: int) -> list:
    """
    Get all transactions for category/year/month.

    Business logic:
    - Validate category_id exists
    - Query transactions by category and date range
    - Include payee information (join)
    - Return list of transaction dicts
    """
    try:
        # Validate category
        category = db.get_category_by_id(category_id)
        if not category:
            raise ValueError(f"Category {category_id} not found")

        if not validate_year(year):
            raise ValueError(f"Invalid year: {year}")

        if not validate_month(month):
            raise ValueError(f"Invalid month: {month}")

        # Get transactions
        transactions = db.get_transactions_by_category_month(category_id, year, month)

        result = []
        for t in transactions:
            result.append({
                'id': t.id,
                'category_id': t.category_id,
                'payee_id': t.payee_id if t.payee_id else None,
                'payee_name': t.payee_id.name if t.payee_id else None,
                'date': str(t.date),
                'amount': t.amount,
                'comment': t.comment
            })

        return result
    except Exception as e:
        logger.error(f"Failed to get transactions: {e}")
        raise


def create_transaction(category_id: str, date: str, amount: int,
                      payee_id: Optional[str] = None, comment: Optional[str] = None) -> dict:
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
    """
    try:
        # Validate required fields
        if not category_id:
            raise ValueError("Category ID is required")

        if not date:
            raise ValueError("Date is required")

        if amount is None:
            raise ValueError("Amount is required")

        # Validate category
        category = db.get_category_by_id(category_id)
        if not category:
            raise ValueError(f"Category {category_id} not found")

        # Validate payee if provided
        payee_id = empty_to_none(payee_id)
        if payee_id:
            payee = db.get_payee_by_id(payee_id)
            if not payee:
                raise ValueError(f"Payee {payee_id} not found")

        # Validate date format
        if not validate_date_format(date):
            raise ValueError("Date must be in YYYY-MM-DD format")

        # Validate amount is integer
        if not isinstance(amount, int):
            raise ValueError("Amount must be an integer")

        # Convert empty comment to NULL
        comment = empty_to_none(comment)

        # Prepare complete record
        transaction_data = {
            'id': generate_uid(),
            'category_id': category_id,
            'payee_id': payee_id,
            'date': date,
            'amount': amount,
            'comment': comment,
            'created_at': datetime.now(),
            'updated_at': datetime.now()
        }

        # Create
        transaction = db.create_transaction(transaction_data)
        logger.info(f"Business logic: Created transaction {transaction.id}")

        return {
            'id': transaction.id,
            'category_id': transaction.category_id,
            'payee_id': transaction.payee_id if transaction.payee_id else None,
            'date': str(transaction.date),
            'amount': transaction.amount,
            'comment': transaction.comment
        }
    except Exception as e:
        logger.error(f"Failed to create transaction: {e}")
        raise


def update_transaction(transaction_id: str, date: str, amount: int,
                      payee_id: Optional[str] = None, comment: Optional[str] = None) -> dict:
    """
    Update existing transaction.

    Business logic:
    - Validate transaction_id exists
    - Validate date and amount
    - Validate payee_id if provided
    - Convert empty strings to NULL
    - Set updated_at timestamp
    """
    try:
        # Validate transaction exists
        transaction = db.get_transaction_by_id(transaction_id)
        if not transaction:
            raise ValueError(f"Transaction {transaction_id} not found")

        # Validate date
        if not validate_date_format(date):
            raise ValueError("Date must be in YYYY-MM-DD format")

        # Validate amount
        if not isinstance(amount, int):
            raise ValueError("Amount must be an integer")

        # Validate payee if provided
        payee_id = empty_to_none(payee_id)
        if payee_id:
            payee = db.get_payee_by_id(payee_id)
            if not payee:
                raise ValueError(f"Payee {payee_id} not found")

        # Convert empty comment to NULL
        comment = empty_to_none(comment)

        # Prepare update data
        update_data = {
            'date': date,
            'amount': amount,
            'payee_id': payee_id,
            'comment': comment,
            'updated_at': datetime.now()
        }

        # Update
        updated_transaction = db.update_transaction(transaction_id, update_data)
        logger.info(f"Business logic: Updated transaction {transaction_id}")

        return {
            'id': updated_transaction.id,
            'category_id': updated_transaction.category_id,
            'payee_id': updated_transaction.payee_id if updated_transaction.payee_id else None,
            'date': str(updated_transaction.date),
            'amount': updated_transaction.amount,
            'comment': updated_transaction.comment
        }
    except Exception as e:
        logger.error(f"Failed to update transaction: {e}")
        raise


def delete_transaction(transaction_id: str) -> None:
    """
    Delete transaction.

    Business logic:
    - Validate transaction_id exists
    - Delete transaction
    """
    try:
        # Validate transaction exists
        transaction = db.get_transaction_by_id(transaction_id)
        if not transaction:
            raise ValueError(f"Transaction {transaction_id} not found")

        # Delete
        db.delete_transaction(transaction_id)
        logger.info(f"Business logic: Deleted transaction {transaction_id}")
    except Exception as e:
        logger.error(f"Failed to delete transaction: {e}")
        raise


# ==================== DASHBOARD BUSINESS LOGIC ====================

def get_recurring_payment_status() -> list:
    """
    Identify recurring payments (expenses only) and their status for current month.

    Logic:
    - Find expense payees that appear in BOTH of the previous 2 months
    - Income transactions are excluded (only expenses tracked)
    - Check if each payee has a transaction in current month
    - Return list with payee name, status, and last payment details

    Returns:
        list: [
            {
                'payee_id': str,
                'payee_name': str,
                'status': 'paid' | 'pending',
                'last_payment_date': str,  # YYYY-MM-DD
                'last_amount': int  # Most recent transaction amount
            }
        ]
    """
    try:
        from datetime import date
        from dateutil.relativedelta import relativedelta

        # Get current date and calculate month boundaries
        today = date.today()
        current_month_start = date(today.year, today.month, 1)

        # Previous month (month - 1)
        prev_month_start = current_month_start - relativedelta(months=1)
        prev_month_end = current_month_start - relativedelta(days=1)

        # Two months ago (month - 2)
        two_months_ago_start = current_month_start - relativedelta(months=2)
        two_months_ago_end = prev_month_start - relativedelta(days=1)

        # Get transactions for the last 3 months
        three_months_ago_start = current_month_start - relativedelta(months=2)
        transactions = db.get_transactions_by_date_range(three_months_ago_start, today)

        # Group transactions by payee and month
        payee_months = {}  # {payee_id: {month_key: [transactions]}}

        for t in transactions:
            if not t.payee_id:
                continue  # Skip transactions without payee

            # Only include expense transactions (skip income)
            if t.category_id and t.category_id.type == 'income':
                continue

            payee_id = t.payee_id.id if hasattr(t.payee_id, 'id') else str(t.payee_id)
            month_key = f"{t.date.year}-{t.date.month:02d}"

            if payee_id not in payee_months:
                payee_months[payee_id] = {}
            if month_key not in payee_months[payee_id]:
                payee_months[payee_id][month_key] = []

            payee_months[payee_id][month_key].append(t)

        # Calculate month keys
        current_month_key = f"{today.year}-{today.month:02d}"
        prev_month_key = f"{prev_month_start.year}-{prev_month_start.month:02d}"
        two_months_ago_key = f"{two_months_ago_start.year}-{two_months_ago_start.month:02d}"

        # Find payees that appear in BOTH previous months
        recurring_payees = []

        for payee_id, months in payee_months.items():
            # Must have transactions in BOTH month-1 AND month-2
            if prev_month_key in months and two_months_ago_key in months:
                # Get payee details
                payee = db.get_payee_by_id(payee_id)
                if not payee:
                    continue

                # Check if paid in current month
                paid_this_month = current_month_key in months

                # Get most recent transaction details
                all_transactions = []
                for month_transactions in months.values():
                    all_transactions.extend(month_transactions)

                # Sort by date descending to get most recent
                all_transactions.sort(key=lambda t: t.date, reverse=True)
                last_transaction = all_transactions[0]

                recurring_payees.append({
                    'payee_id': payee_id,
                    'payee_name': payee.name,
                    'status': 'paid' if paid_this_month else 'pending',
                    'last_payment_date': str(last_transaction.date),
                    'last_amount': last_transaction.amount
                })

        # Sort: pending first, then paid (alphabetically within each group)
        recurring_payees.sort(key=lambda p: (p['status'] == 'paid', p['payee_name']))

        logger.info(f"Business logic: Found {len(recurring_payees)} recurring payments")
        return recurring_payees

    except Exception as e:
        logger.error(f"Failed to get recurring payment status: {e}")
        raise


def get_recent_transactions(limit: int = 5) -> list:
    """
    Get most recent transactions for dashboard display.

    Args:
        limit: Number of transactions to return (default 5)

    Returns:
        list: [
            {
                'transaction_id': str,
                'transaction_date': str,   # YYYY-MM-DD
                'payee_name': str,
                'category_name': str,
                'amount': int,
                'category_type': str       # 'income' | 'expense'
            }
        ]
    """
    try:
        transactions = db.get_recent_transactions(limit)

        result = []
        for t in transactions:
            result.append({
                'transaction_id': t.id,
                'transaction_date': str(t.date),
                'payee_name': t.payee_id.name if t.payee_id else 'Unknown',
                'category_name': t.category_id.name if t.category_id else 'Unknown',
                'amount': t.amount,
                'category_type': t.category_id.type if t.category_id else 'expense'
            })

        logger.info(f"Business logic: Retrieved {len(result)} recent transactions")
        return result

    except Exception as e:
        logger.error(f"Failed to get recent transactions: {e}")
        raise


# ==================== CONFIGURATION BUSINESS LOGIC ====================

def _invalidate_config_cache():
    """Invalidate configuration cache."""
    global _config_cache, _cache_timestamp
    _config_cache = {}
    _cache_timestamp = None
    logger.debug("Configuration cache invalidated")


def _is_cache_valid() -> bool:
    """Check if configuration cache is still valid."""
    global _cache_timestamp
    if _cache_timestamp is None:
        return False

    elapsed = (datetime.now() - _cache_timestamp).total_seconds()
    return elapsed < CACHE_TIMEOUT


def get_all_configuration() -> dict:
    """
    Get all configuration as key-value dict.

    Uses in-memory cache for performance (5 minute timeout).

    Business logic:
    - Query all configuration entries
    - Convert to dict {key: value}
    - Return config dict
    """
    global _config_cache, _cache_timestamp

    try:
        # Check cache first
        if _is_cache_valid() and _config_cache:
            logger.debug("Returning cached configuration")
            return _config_cache.copy()

        # Cache miss or expired - load from database
        configs = db.get_all_configuration()
        result = {}
        for config in configs:
            result[config.key] = config.value

        # Update cache
        _config_cache = result.copy()
        _cache_timestamp = datetime.now()

        logger.info(f"Retrieved {len(result)} configuration settings (cache updated)")
        return result
    except Exception as e:
        logger.error(f"Failed to get configuration: {e}")
        raise


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
    """
    try:
        result = {}

        for key, value in config_data.items():
            # Check if exists
            existing_config = db.get_configuration_by_key(key)

            if existing_config:
                # Update
                update_data = {
                    'value': value,
                    'updated_at': datetime.now()
                }
                config = db.update_configuration(key, update_data)
                logger.info(f"Business logic: Updated configuration {key}")
            else:
                # Create
                new_config_data = {
                    'id': generate_uid(),
                    'key': key,
                    'value': value,
                    'created_at': datetime.now(),
                    'updated_at': datetime.now()
                }
                config = db.create_configuration(new_config_data)
                logger.info(f"Business logic: Created configuration {key}")

            result[config.key] = config.value

        # Invalidate cache after update
        _invalidate_config_cache()

        return result
    except Exception as e:
        logger.error(f"Failed to update configuration: {e}")
        raise


def test_database_connection(host: str, port: int, database: str,
                            user: str, password: str) -> dict:
    """
    Test database connection with provided settings.

    Business logic:
    - Validate all parameters provided
    - Test connection
    - Return success/failure with message in standard API format
    """
    try:
        if not all([host, port, database, user, password]):
            raise ValueError("All database connection parameters are required")

        success = db.test_connection(host, port, database, user, password)

        if success:
            return {
                'success': True,
                'data': {
                    'message': f'Successfully connected to {host}:{port}/{database}'
                }
            }
        else:
            return {
                'success': False,
                'error': 'Failed to connect to database'
            }
    except Exception as e:
        logger.error(f"Failed to test database connection: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def _ensure_import_payee() -> str:
    """
    Get or create "Import - Google Sheets" payee.

    Returns:
        str: Payee UUID
    """
    payee = db.get_payee_by_name("Import - Google Sheets")
    if payee:
        return payee.id

    # Create payee
    data = {
        "id": generate_uid(),
        "name": "Import - Google Sheets",
        "type": "Generic",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    payee = db.create_payee(data)
    return payee.id


def parse_excel_file(file_path: str, year: int) -> dict:
    """
    Parse Google Sheets Excel file and extract budget/actual data.

    Expected structure:
    - Row 3: Headers ("Balanse", "Januar", ..., "Desember")
    - Row 7: "Inntekter" section
    - Row 16+: "Utgifter" section
    - Category blocks every 4 rows:
      - Row N: Category name
      - Row N+1: "Budsjett" (budget values)
      - Row N+2: "Resultat" (actual formulas)
      - Row N+3: "Differanse" (skip)

    Args:
        file_path: Path to .xlsx file
        year: Year for the data

    Returns:
        {
            "year": 2024,
            "sheet_categories": [
                {
                    "name": "Lønn",
                    "type": "income",
                    "budget": {1: 52000, 2: 52000, ...},
                    "actuals": {1: [55615], 2: [55615], ...}
                }
            ]
        }

    Raises:
        ValueError: On validation errors
    """
    import openpyxl

    # Validate year
    if not validate_year(year):
        raise ValueError(f"Invalid year: {year}")

    # Load workbook
    try:
        wb = openpyxl.load_workbook(file_path, data_only=False)
    except Exception as e:
        raise ValueError(f"Failed to load Excel file: {e}")

    sheet = wb.active

    # Month column mapping (C=1, D=2, ..., N=12)
    month_columns = {
        'C': 1, 'D': 2, 'E': 3, 'F': 4, 'G': 5, 'H': 6,
        'I': 7, 'J': 8, 'K': 9, 'L': 10, 'M': 11, 'N': 12
    }

    # Find "Utgifter" row to split income vs expenses
    utgifter_row = None
    for row_idx in range(1, 100):
        cell = sheet[f'B{row_idx}']
        if cell.value and "Utgifter" in str(cell.value):
            utgifter_row = row_idx
            break

    if not utgifter_row:
        raise ValueError("Could not find 'Utgifter' section in Excel file")

    sheet_categories = []

    # Parse categories (every 4 rows, starting from row 8)
    for row_idx in range(8, 60, 4):
        category_cell = sheet[f'B{row_idx}']
        category_name = category_cell.value

        # Skip if no category name or if it's a header row
        if not category_name or category_name in ["Inntekter", "Utgifter", "Balanse"]:
            continue

        category_name = str(category_name).strip()

        # Determine type (income if before utgifter_row, expenses after)
        category_type = "income" if row_idx < utgifter_row else "expenses"

        # Extract budget values (row N+1)
        budget = {}
        budget_row = row_idx + 1
        for col, month in month_columns.items():
            cell = sheet[f'{col}{budget_row}']
            if cell.value:
                try:
                    amount = int(float(cell.value)) if cell.value else 0
                    budget[month] = amount
                except (ValueError, TypeError):
                    # Skip invalid values
                    pass

        # Extract actual values (row N+2)
        actuals = {}
        actuals_row = row_idx + 2
        for col, month in month_columns.items():
            cell = sheet[f'{col}{actuals_row}']
            if cell.value:
                try:
                    amounts = _extract_amounts_from_formula(cell.value, actuals_row, col)
                    if amounts:
                        actuals[month] = amounts
                except ValueError as e:
                    raise ValueError(f"Category '{category_name}': {e}")

        # Skip categories with no data
        if not budget and not actuals:
            continue

        sheet_categories.append({
            "name": category_name,
            "type": category_type,
            "budget": budget,
            "actuals": actuals
        })

    if not sheet_categories:
        raise ValueError("No categories found in Excel file")

    return {
        "year": year,
        "sheet_categories": sheet_categories
    }


def validate_import(parsed_data: dict, category_mapping: dict) -> dict:
    """
    Dry-run validation before import.

    Checks:
    - All mapped categories exist
    - Category types match (income/expenses)
    - Check for duplicate BudgetEntries
    - Check for duplicate Transactions

    Args:
        parsed_data: Parsed Excel data structure
        category_mapping: Dict mapping sheet category names to Moneybags category IDs

    Returns:
        {
            "valid": True/False,
            "errors": ["..."],
            "warnings": ["..."],
            "summary": {"budget_count": 120, "transaction_count": 347}
        }
    """
    errors = []
    warnings = []
    budget_count = 0
    transaction_count = 0

    year = parsed_data["year"]

    # Validate all categories exist and types match
    for sheet_cat in parsed_data["sheet_categories"]:
        sheet_name = sheet_cat["name"]

        # Check category is mapped
        if sheet_name not in category_mapping:
            errors.append(f"Category '{sheet_name}' not mapped")
            continue

        category_id = category_mapping[sheet_name]

        # Check category exists
        category = db.get_category_by_id(category_id)
        if not category:
            errors.append(f"Category '{sheet_name}' mapped to '{category_id}' which does not exist")
            continue

        # Check type matches
        if category.type != sheet_cat["type"]:
            errors.append(f"Category '{sheet_name}' type mismatch: sheet has '{sheet_cat['type']}' but Moneybags has '{category.type}'")
            continue

        # Count budget entries and check for duplicates
        for month in sheet_cat["budget"].keys():
            existing = db.get_budget_entry(category_id, year, month)
            if existing:
                warnings.append(f"Budget entry for '{category.name}' {year}-{month:02d} already exists - will overwrite")
            budget_count += 1

        # Count transactions
        for month, amounts in sheet_cat["actuals"].items():
            transaction_count += len(amounts)

    # Final validation
    valid = len(errors) == 0

    return {
        "valid": valid,
        "errors": errors,
        "warnings": warnings,
        "summary": {
            "budget_count": budget_count,
            "transaction_count": transaction_count
        }
    }


def import_budget_and_transactions(parsed_data: dict, category_mapping: dict) -> dict:
    """
    Create BudgetEntry and Transaction records from parsed data.

    Prerequisites: validate_import() should pass before calling this

    Args:
        parsed_data: Parsed Excel data structure
        category_mapping: Dict mapping sheet category names to Moneybags category IDs

    Returns:
        {
            "budget_count": 120,
            "transaction_count": 347,
            "message": "Successfully imported data"
        }

    Raises:
        ValueError: On errors
    """
    import_payee_id = _ensure_import_payee()

    budget_count = 0
    transaction_count = 0

    year = parsed_data["year"]

    for sheet_category in parsed_data["sheet_categories"]:
        category_id = category_mapping[sheet_category["name"]]

        # Import budget entries
        for month, amount in sheet_category["budget"].items():
            data = {
                "id": generate_uid(),
                "category_id": category_id,
                "year": year,
                "month": month,
                "amount": amount,
                "comment": empty_to_none(None),
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            db.create_or_update_budget_entry(data)
            budget_count += 1

        # Import transactions
        for month, amounts in sheet_category["actuals"].items():
            for amount in amounts:
                date_str = f"{year}-{month:02d}-01"
                data = {
                    "id": generate_uid(),
                    "category_id": category_id,
                    "payee_id": import_payee_id,
                    "date": date_str,
                    "amount": amount,
                    "comment": empty_to_none(None),
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                db.create_transaction(data)
                transaction_count += 1

    logger.info(f"Imported {budget_count} budget entries and {transaction_count} transactions")

    return {
        "budget_count": budget_count,
        "transaction_count": transaction_count,
        "message": "Successfully imported data"
    }
