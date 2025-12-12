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
    try:
        if not validate_year(year):
            raise ValueError(f"Invalid year: {year}")

        # Get categories for this year
        categories = get_budget_template(year)

        # Get budget entries - organized by category and month
        budget_entries = db.get_budget_entries_by_year(year)
        budget_dict = {}
        for entry in budget_entries:
            cat_id = entry.category_id if isinstance(entry.category_id, str) else entry.category_id.id
            if cat_id not in budget_dict:
                budget_dict[cat_id] = {}
            budget_dict[cat_id][entry.month] = {
                'amount': entry.amount,
                'id': entry.id
            }

        # Get transactions - organized by category and month (nested structure)
        transactions = db.get_transactions_by_year(year)
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

        return {
            'year': year,
            'categories': categories,
            'budget_entries': budget_dict,
            'transactions': transactions_dict
        }
    except Exception as e:
        logger.error(f"Failed to get budget data for year: {e}")
        raise


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
    - If not exists: create new entry with all fields
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

        # Check if entry exists
        existing_entry = db.get_budget_entry(category_id, year, month)

        if existing_entry:
            # Update
            update_data = {
                'amount': amount,
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
            'amount': entry.amount
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
