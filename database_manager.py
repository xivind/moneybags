"""
Database manager for Moneybags application.

All database CRUD operations are performed here using PeeWee ORM.
This module contains PURE CRUD functions - no validation, no logic.
All data preparation and validation happens in business_logic.py.

See DATABASE_DESIGN.md for complete documentation.
"""

import logging
import time
from peewee import MySQLDatabase, IntegrityError, DoesNotExist, OperationalError
from playhouse.pool import PooledMySQLDatabase
from datetime import date, datetime
from database_model import (
    database,
    ALL_MODELS,
    Category,
    Payee,
    BudgetTemplate,
    BudgetEntry,
    Transaction,
    Configuration
)

logger = logging.getLogger(__name__)

# Connection retry configuration
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds

# Query performance tracking
ENABLE_QUERY_METRICS = True  # Set to False in production for performance
SLOW_QUERY_THRESHOLD = 1.0  # Log queries taking longer than 1 second


# ==================== INITIALIZATION ====================

def initialize_connection(host: str = "localhost", port: int = 3306,
                         database_name: str = "moneybags",
                         user: str = "moneybags_user",
                         password: str = "moneybags_pass",
                         pool_size: int = 10,
                         pool_recycle: int = 3600) -> None:
    """
    Initialize database connection with connection pooling.

    Connection pooling improves performance for htmx-driven interactions by
    reusing connections instead of creating new ones for each request.

    Args:
        host: Database host
        port: Database port
        database_name: Database name
        user: Database user
        password: Database password
        pool_size: Maximum number of connections in pool (default: 10)
        pool_recycle: Recycle connections after this many seconds (default: 3600)
    """
    try:
        # Initialize the PooledMySQLDatabase instance with connection parameters
        database.init(
            database_name,
            host=host,
            port=port,
            user=user,
            password=password,
            charset='utf8mb4',
            max_connections=pool_size,
            stale_timeout=pool_recycle,
            timeout=10  # Connection timeout
        )

        # Explicitly connect to initialize the connection pool
        # This is required for PooledMySQLDatabase to work correctly
        if database.is_closed():
            database.connect()

        logger.info(f"Database connection pool initialized: {host}:{port}/{database_name} "
                   f"(pool_size={pool_size}, recycle={pool_recycle}s)")
    except Exception as e:
        logger.error(f"Failed to initialize database connection: {e}")
        raise


def check_connection() -> bool:
    """
    Check if database connection is healthy.

    Returns True if connection is alive, False otherwise.
    """
    try:
        database.execute_sql('SELECT 1')
        return True
    except Exception as e:
        logger.warning(f"Database connection check failed: {e}")
        return False


def reconnect() -> bool:
    """
    Attempt to reconnect to database.

    Returns True if reconnection successful, False otherwise.
    """
    try:
        if not database.is_closed():
            database.close()
        database.connect()
        logger.info("Database reconnection successful")
        return True
    except Exception as e:
        logger.error(f"Database reconnection failed: {e}")
        return False


def execute_with_retry(operation, *args, **kwargs):
    """
    Execute database operation with retry logic for transient failures.

    Args:
        operation: Function to execute
        *args, **kwargs: Arguments to pass to operation

    Returns:
        Result of operation

    Raises:
        Exception: If all retries exhausted
    """
    last_exception = None

    for attempt in range(MAX_RETRIES):
        try:
            # Check connection health before operation
            if attempt > 0 and not check_connection():
                logger.info("Connection unhealthy, attempting reconnect...")
                reconnect()

            return operation(*args, **kwargs)

        except OperationalError as e:
            last_exception = e
            logger.warning(f"Database operation failed (attempt {attempt + 1}/{MAX_RETRIES}): {e}")

            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
                reconnect()
            else:
                logger.error(f"Database operation failed after {MAX_RETRIES} attempts")
                raise last_exception

        except Exception as e:
            # Non-retryable error, raise immediately
            logger.error(f"Non-retryable database error: {e}")
            raise

    raise last_exception


def test_connection(host: str, port: int, database_name: str,
                   user: str, password: str) -> bool:
    """
    Test database connection with provided parameters.

    Returns True if connection successful, False otherwise.
    """
    try:
        test_db = MySQLDatabase(
            database_name,
            host=host,
            port=port,
            user=user,
            password=password
        )
        test_db.connect()
        test_db.close()
        logger.info(f"Test connection successful: {host}:{port}/{database_name}")
        return True
    except Exception as e:
        logger.error(f"Test connection failed: {e}")
        return False


def create_tables_if_not_exist() -> None:
    """Create all tables if they don't exist."""
    try:
        database.create_tables(ALL_MODELS, safe=True)
        logger.info("Database tables created/verified")
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        raise


def close_connection() -> None:
    """Close database connection."""
    if not database.is_closed():
        database.close()
        logger.info("Database connection closed")


def with_transaction(func):
    """
    Decorator to wrap database write operations in transactions.

    Ensures atomicity - either all changes succeed or all are rolled back.
    Pattern from DATABASE_DESIGN.md.
    """
    def wrapper(*args, **kwargs):
        try:
            with database.atomic():
                return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Transaction failed in {func.__name__}: {e}")
            raise
    return wrapper


def log_query_time(func):
    """
    Decorator to log query execution time for performance monitoring.

    Logs warning for queries exceeding SLOW_QUERY_THRESHOLD.
    """
    def wrapper(*args, **kwargs):
        if not ENABLE_QUERY_METRICS:
            return func(*args, **kwargs)

        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start_time

            if elapsed > SLOW_QUERY_THRESHOLD:
                logger.warning(f"Slow query in {func.__name__}: {elapsed:.3f}s")
            else:
                logger.debug(f"Query {func.__name__}: {elapsed:.3f}s")

            return result
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"Query failed in {func.__name__} after {elapsed:.3f}s: {e}")
            raise
    return wrapper


# ==================== CATEGORY CRUD ====================

@with_transaction
def create_category(data: dict) -> Category:
    """Create category with provided data dict."""
    category = Category(**data)
    category.save(force_insert=True)
    logger.info(f"Created category: {category.name} ({category.id})")
    return category


def get_category_by_id(category_id: str) -> Category:
    """Get category by ID."""
    try:
        return Category.get(Category.id == category_id)
    except DoesNotExist:
        return None


def get_all_categories() -> list:
    """Get all categories."""
    return list(Category.select())


def category_exists_by_name(name: str) -> bool:
    """Check if category with name exists (case-insensitive)."""
    return Category.select().where(Category.name.ilike(name)).exists()


@with_transaction
def update_category(category_id: str, data: dict) -> Category:
    """Update category fields."""
    category = Category.get(Category.id == category_id)
    for key, value in data.items():
        setattr(category, key, value)
    category.save()
    logger.info(f"Updated category: {category.name} ({category.id})")
    return category


@with_transaction
def delete_category(category_id: str) -> None:
    """Delete category by ID."""
    category = Category.get(Category.id == category_id)
    category_name = category.name
    category.delete_instance()
    logger.info(f"Deleted category: {category_name} ({category_id})")


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


# ==================== PAYEE CRUD ====================

@with_transaction
def create_payee(data: dict) -> Payee:
    """Create payee with provided data dict."""
    payee = Payee(**data)
    payee.save(force_insert=True)
    logger.info(f"Created payee: {payee.name} ({payee.id})")
    return payee


def get_payee_by_id(payee_id: str) -> Payee:
    """Get payee by ID."""
    try:
        return Payee.get(Payee.id == payee_id)
    except DoesNotExist:
        return None


def get_all_payees() -> list:
    """Get all payees."""
    return list(Payee.select())


def payee_exists_by_name(name: str) -> bool:
    """Check if payee with name exists (case-insensitive)."""
    return Payee.select().where(Payee.name.ilike(name)).exists()


@with_transaction
def update_payee(payee_id: str, data: dict) -> Payee:
    """Update payee fields."""
    payee = Payee.get(Payee.id == payee_id)
    for key, value in data.items():
        setattr(payee, key, value)
    payee.save()
    logger.info(f"Updated payee: {payee.name} ({payee.id})")
    return payee


@with_transaction
def delete_payee(payee_id: str) -> None:
    """Delete payee by ID."""
    payee = Payee.get(Payee.id == payee_id)
    payee_name = payee.name
    payee.delete_instance()
    logger.info(f"Deleted payee: {payee_name} ({payee_id})")


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


# ==================== BUDGET TEMPLATE CRUD ====================

@with_transaction
def create_budget_template(data: dict) -> BudgetTemplate:
    """Create budget template entry with provided data dict."""
    template = BudgetTemplate(**data)
    template.save(force_insert=True)
    logger.info(f"Created budget template: year={template.year}, category={template.category_id}")
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


@with_transaction
def delete_budget_template(year: int, category_id: str) -> None:
    """Delete budget template entry."""
    template = BudgetTemplate.get(
        (BudgetTemplate.year == year) &
        (BudgetTemplate.category_id == category_id)
    )
    template.delete_instance()
    logger.info(f"Deleted budget template: year={year}, category={category_id}")


def get_distinct_years() -> list:
    """Get all distinct years from budget_templates."""
    years = (BudgetTemplate
             .select(BudgetTemplate.year)
             .distinct()
             .order_by(BudgetTemplate.year))
    return [y.year for y in years]


# ==================== BUDGET ENTRY CRUD ====================

@with_transaction
def create_budget_entry(data: dict) -> BudgetEntry:
    """Create budget entry with provided data dict."""
    entry = BudgetEntry(**data)
    entry.save(force_insert=True)
    logger.info(f"Created budget entry: category={entry.category_id}, {entry.year}/{entry.month}")
    return entry


def get_budget_entry(category_id: str, year: int, month: int) -> BudgetEntry:
    """Get budget entry by category/year/month."""
    try:
        return BudgetEntry.get(
            (BudgetEntry.category_id == category_id) &
            (BudgetEntry.year == year) &
            (BudgetEntry.month == month)
        )
    except DoesNotExist:
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


@with_transaction
def update_budget_entry(entry_id: str, data: dict) -> BudgetEntry:
    """Update budget entry fields."""
    entry = BudgetEntry.get(BudgetEntry.id == entry_id)
    for key, value in data.items():
        setattr(entry, key, value)
    entry.save()
    logger.info(f"Updated budget entry: {entry.id}")
    return entry


def category_has_budget_entries_for_year(category_id: str, year: int) -> bool:
    """Check if category has budget entries for specific year."""
    return BudgetEntry.select().where(
        (BudgetEntry.category_id == category_id) &
        (BudgetEntry.year == year)
    ).exists()


# ==================== TRANSACTION CRUD ====================

@with_transaction
def create_transaction(data: dict) -> Transaction:
    """Create transaction with provided data dict."""
    transaction = Transaction(**data)
    transaction.save(force_insert=True)
    logger.info(f"Created transaction: {transaction.id}, amount={transaction.amount}")
    return transaction


def get_transaction_by_id(transaction_id: str) -> Transaction:
    """Get transaction by ID."""
    try:
        return Transaction.get(Transaction.id == transaction_id)
    except DoesNotExist:
        return None


def get_transactions_by_category_month(category_id: str, year: int, month: int) -> list:
    """Get transactions for category/year/month."""
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
    start_date = date(year, 1, 1)
    end_date = date(year + 1, 1, 1)

    return list(Transaction
                .select()
                .where(
                    (Transaction.date >= start_date) &
                    (Transaction.date < end_date)
                ))


@with_transaction
def update_transaction(transaction_id: str, data: dict) -> Transaction:
    """Update transaction fields."""
    transaction = Transaction.get(Transaction.id == transaction_id)
    for key, value in data.items():
        setattr(transaction, key, value)
    transaction.save()
    logger.info(f"Updated transaction: {transaction.id}")
    return transaction


@with_transaction
def delete_transaction(transaction_id: str) -> None:
    """Delete transaction by ID."""
    transaction = Transaction.get(Transaction.id == transaction_id)
    transaction.delete_instance()
    logger.info(f"Deleted transaction: {transaction_id}")


def category_has_transactions_for_year(category_id: str, year: int) -> bool:
    """Check if category has transactions for specific year."""
    start_date = date(year, 1, 1)
    end_date = date(year + 1, 1, 1)

    return Transaction.select().where(
        (Transaction.category_id == category_id) &
        (Transaction.date >= start_date) &
        (Transaction.date < end_date)
    ).exists()


# ==================== CONFIGURATION CRUD ====================

@with_transaction
def create_configuration(data: dict) -> Configuration:
    """Create configuration entry with provided data dict."""
    config = Configuration(**data)
    config.save(force_insert=True)
    logger.info(f"Created configuration: {config.key}")
    return config


def get_configuration_by_key(key: str) -> Configuration:
    """Get configuration by key."""
    try:
        return Configuration.get(Configuration.key == key)
    except DoesNotExist:
        return None


def get_all_configuration() -> list:
    """Get all configuration entries."""
    return list(Configuration.select())


@with_transaction
def update_configuration(key: str, data: dict) -> Configuration:
    """Update configuration entry."""
    config = Configuration.get(Configuration.key == key)
    for k, value in data.items():
        setattr(config, k, value)
    config.save()
    logger.info(f"Updated configuration: {key}")
    return config


def configuration_exists(key: str) -> bool:
    """Check if configuration key exists."""
    return Configuration.select().where(Configuration.key == key).exists()


# ==================== SEED DATA ====================

def seed_initial_data():
    """
    Seed database with initial data.

    Creates:
    - Initial categories (income and expenses)
    - Sample payees
    - Default configuration
    - Budget templates for current year
    """
    from utils import generate_uid
    from datetime import datetime

    logger.info("Seeding initial data...")
    current_year = datetime.now().year

    # Initial categories
    initial_categories = [
        {'id': generate_uid(), 'name': 'Salary', 'type': 'income', 'created_at': datetime.now()},
        {'id': generate_uid(), 'name': 'Other income', 'type': 'income', 'created_at': datetime.now()},
        {'id': generate_uid(), 'name': 'Housing & utilities', 'type': 'expenses', 'created_at': datetime.now()},
        {'id': generate_uid(), 'name': 'Repairs & maintenance', 'type': 'expenses', 'created_at': datetime.now()},
        {'id': generate_uid(), 'name': 'Digital services', 'type': 'expenses', 'created_at': datetime.now()},
        {'id': generate_uid(), 'name': 'Cars', 'type': 'expenses', 'created_at': datetime.now()},
        {'id': generate_uid(), 'name': 'Clothing & travel', 'type': 'expenses', 'created_at': datetime.now()},
        {'id': generate_uid(), 'name': 'Sports', 'type': 'expenses', 'created_at': datetime.now()},
        {'id': generate_uid(), 'name': 'Travel', 'type': 'expenses', 'created_at': datetime.now()},
        {'id': generate_uid(), 'name': 'Savings', 'type': 'expenses', 'created_at': datetime.now()},
    ]

    for cat_data in initial_categories:
        if not category_exists_by_name(cat_data['name']):
            create_category(cat_data)
            logger.info(f"Seeded category: {cat_data['name']}")

    # Initial payees
    initial_payees = [
        {'id': generate_uid(), 'name': 'Employer', 'type': 'Actual', 'created_at': datetime.now()},
        {'id': generate_uid(), 'name': 'Landlord', 'type': 'Generic', 'created_at': datetime.now()},
        {'id': generate_uid(), 'name': 'Power Company', 'type': 'Generic', 'created_at': datetime.now()},
        {'id': generate_uid(), 'name': 'Netflix', 'type': 'Actual', 'created_at': datetime.now()},
        {'id': generate_uid(), 'name': 'Spotify', 'type': 'Actual', 'created_at': datetime.now()},
    ]

    for payee_data in initial_payees:
        if not payee_exists_by_name(payee_data['name']):
            create_payee(payee_data)
            logger.info(f"Seeded payee: {payee_data['name']}")

    # Initial configuration
    initial_config = [
        {'id': generate_uid(), 'key': 'currency_format', 'value': 'nok',
         'created_at': datetime.now(), 'updated_at': datetime.now()},
        {'id': generate_uid(), 'key': 'db_host', 'value': 'localhost',
         'created_at': datetime.now(), 'updated_at': datetime.now()},
        {'id': generate_uid(), 'key': 'db_port', 'value': '3306',
         'created_at': datetime.now(), 'updated_at': datetime.now()},
        {'id': generate_uid(), 'key': 'db_name', 'value': 'moneybags',
         'created_at': datetime.now(), 'updated_at': datetime.now()},
    ]

    for config_data in initial_config:
        if not configuration_exists(config_data['key']):
            create_configuration(config_data)
            logger.info(f"Seeded configuration: {config_data['key']}")

    # Create budget templates for current year with all categories
    categories = get_all_categories()
    for category in categories:
        if not budget_template_exists(current_year, category.id):
            template_data = {
                'id': generate_uid(),
                'year': current_year,
                'category_id': category.id,
                'created_at': datetime.now()
            }
            create_budget_template(template_data)
            logger.info(f"Seeded budget template for {current_year}: {category.name}")

    logger.info("Initial data seeding complete")
