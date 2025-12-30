"""
Database manager for Moneybags application.

All database CRUD operations are performed here using PeeWee ORM.
This module contains PURE CRUD functions - no validation, no logic.
All data preparation and validation happens in business_logic.py.

See DATABASE_DESIGN.md for complete documentation.
"""

import logging
import time
from peewee import MySQLDatabase, IntegrityError, DoesNotExist, OperationalError, JOIN
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
        # Create test database connection with timeout
        # Use connect_timeout in connect_params for pymysql
        test_db = MySQLDatabase(
            database_name,
            host=host,
            port=port,
            user=user,
            password=password,
            charset='utf8mb4'
        )

        # Set connection timeout via connect_params
        test_db.connect_params['connect_timeout'] = 5

        # Connect and execute test query
        test_db.connect()
        test_db.execute_sql('SELECT 1')
        test_db.close()

        logger.info(f"Test connection successful: {host}:{port}/{database_name}")
        return True
    except Exception as e:
        logger.error(f"Test connection failed: {e}")
        return False


def create_tables_if_not_exist() -> None:
    """
    Create all tables if they don't exist.

    Note: PeeWee's safe=True checks if tables exist, but may still try to
    add indexes. We catch duplicate key errors which can happen if tables
    already exist with indexes from a previous run.
    """
    try:
        database.create_tables(ALL_MODELS, safe=True)
        logger.info("Database tables created/verified")
    except OperationalError as e:
        # Ignore duplicate key/index errors (happens if tables already exist with indexes)
        if "Duplicate key name" in str(e) or "Duplicate entry" in str(e):
            logger.info("Database tables already exist with indexes - skipping creation")
        else:
            logger.error(f"Failed to create tables: {e}")
            raise
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        raise


def close_connection() -> None:
    """Close database connection."""
    if not database.is_closed():
        database.close()
        logger.info("Database connection closed")


def _execute_transaction(func, *args, **kwargs):
    """
    Inner function to execute database operation in transaction.

    This is separated out so it can be wrapped by execute_with_retry.
    """
    with database.atomic():
        return func(*args, **kwargs)


def with_transaction(func):
    """
    Decorator to wrap database write operations in transactions with retry logic.

    Ensures atomicity - either all changes succeed or all are rolled back.
    Automatically retries on transient connection failures (OperationalError).

    Pattern from DATABASE_DESIGN.md.
    """
    def wrapper(*args, **kwargs):
        try:
            return execute_with_retry(_execute_transaction, func, *args, **kwargs)
        except Exception as e:
            logger.error(f"Transaction failed in {func.__name__} after all retries: {e}")
            raise
    return wrapper


def with_retry(func):
    """
    Decorator to wrap database read operations with retry logic.

    Automatically retries on transient connection failures (OperationalError).
    Used for SELECT queries to ensure connection resilience.
    """
    def wrapper(*args, **kwargs):
        try:
            return execute_with_retry(func, *args, **kwargs)
        except Exception as e:
            logger.error(f"Failed to {func.__name__} after all retries: {e}")
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


@with_retry
def get_category_by_id(category_id: str) -> Category:
    """Get category by ID."""
    try:
        return Category.get(Category.id == category_id)
    except DoesNotExist:
        return None


@with_retry
def get_all_categories() -> list:
    """Get all categories."""
    return list(Category.select().order_by(Category.type, Category.name))


@with_retry
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


@with_retry
def category_has_budget_templates(category_id: str) -> bool:
    """Check if category is used in any budget_templates."""
    return BudgetTemplate.select().where(
        BudgetTemplate.category_id == category_id
    ).exists()


@with_retry
def category_has_budget_entries(category_id: str) -> bool:
    """Check if category has any budget_entries."""
    return BudgetEntry.select().where(
        BudgetEntry.category_id == category_id
    ).exists()


@with_retry
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


@with_retry
def get_payee_by_id(payee_id: str) -> Payee:
    """Get payee by ID."""
    try:
        return Payee.get(Payee.id == payee_id)
    except DoesNotExist:
        return None


@with_retry
def get_all_payees() -> list:
    """Get all payees."""
    return list(Payee.select().order_by(Payee.name))


@with_retry
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


@with_retry
def payee_transaction_count(payee_id: str) -> int:
    """Count transactions for payee."""
    return Transaction.select().where(
        Transaction.payee_id == payee_id
    ).count()


@with_retry
def payee_last_used_date(payee_id: str) -> str:
    """Get most recent transaction date for payee."""
    result = (Transaction
              .select(Transaction.date)
              .where(Transaction.payee_id == payee_id)
              .order_by(Transaction.date.desc())
              .first())
    return result.date if result else None


@with_retry
def get_payee_by_name(name: str):
    """
    Get payee by exact name match.

    Args:
        name: Payee name to search for

    Returns:
        Payee object if found, None otherwise
    """
    return Payee.get_or_none(Payee.name == name)


# ==================== BUDGET TEMPLATE CRUD ====================

@with_transaction
def create_budget_template(data: dict) -> BudgetTemplate:
    """Create budget template entry with provided data dict."""
    template = BudgetTemplate(**data)
    template.save(force_insert=True)
    logger.info(f"Created budget template: year={template.year}, category={template.category_id}")
    return template


@with_retry
def get_budget_template_by_year(year: int) -> list:
    """Get all categories in budget template for year."""
    return list(BudgetTemplate
                .select(BudgetTemplate, Category)
                .join(Category)
                .where(BudgetTemplate.year == year)
                .order_by(Category.type, Category.name))


@with_retry
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


@with_retry
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


@with_retry
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


@with_retry
def get_budget_entry_by_id(entry_id: str) -> BudgetEntry:
    """Get budget entry by ID."""
    try:
        return BudgetEntry.get(BudgetEntry.id == entry_id)
    except DoesNotExist:
        return None


@with_retry
def get_budget_entries_by_year(year: int) -> list:
    """Get all budget entries for year (with eager-loaded categories to avoid N+1 queries)."""
    return list(BudgetEntry
                .select(BudgetEntry, Category)
                .join(Category, JOIN.LEFT_OUTER, on=(BudgetEntry.category_id == Category.id))
                .where(BudgetEntry.year == year))


@with_retry
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


@with_transaction
def delete_budget_entry(entry_id: str) -> None:
    """Delete budget entry by ID."""
    entry = BudgetEntry.get(BudgetEntry.id == entry_id)
    entry.delete_instance()
    logger.info(f"Deleted budget entry: {entry_id}")


@with_retry
def category_has_budget_entries_for_year(category_id: str, year: int) -> bool:
    """Check if category has budget entries for specific year."""
    return BudgetEntry.select().where(
        (BudgetEntry.category_id == category_id) &
        (BudgetEntry.year == year)
    ).exists()


@with_transaction
def create_or_update_budget_entry(data: dict) -> BudgetEntry:
    """
    Create or update budget entry.

    Checks if entry exists by (category_id, year, month).
    If exists: updates amount, comment, updated_at
    If not: creates new entry

    Args:
        data: Budget entry data dict with all fields

    Returns:
        BudgetEntry object (created or updated)
    """
    existing = BudgetEntry.get_or_none(
        (BudgetEntry.category_id == data["category_id"]) &
        (BudgetEntry.year == data["year"]) &
        (BudgetEntry.month == data["month"])
    )

    if existing:
        existing.amount = data["amount"]
        existing.comment = data["comment"]
        existing.updated_at = data["updated_at"]
        existing.save()
        logger.info(f"Updated budget entry: {existing.id}")
        return existing
    else:
        entry = BudgetEntry(**data)
        entry.save(force_insert=True)
        logger.info(f"Created budget entry: {entry.id}")
        return entry


# ==================== TRANSACTION CRUD ====================

@with_transaction
def create_transaction(data: dict) -> Transaction:
    """Create transaction with provided data dict."""
    transaction = Transaction(**data)
    transaction.save(force_insert=True)
    logger.info(f"Created transaction: {transaction.id}, amount={transaction.amount}")
    return transaction


@with_retry
def get_transaction_by_id(transaction_id: str) -> Transaction:
    """Get transaction by ID."""
    try:
        return Transaction.get(Transaction.id == transaction_id)
    except DoesNotExist:
        return None


@with_retry
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


@with_retry
def get_transactions_by_year(year: int) -> list:
    """Get all transactions for year (with eager-loaded payees and categories to avoid N+1 queries)."""
    start_date = date(year, 1, 1)
    end_date = date(year + 1, 1, 1)

    return list(Transaction
                .select(Transaction, Payee, Category)
                .join(Payee, JOIN.LEFT_OUTER, on=(Transaction.payee_id == Payee.id))
                .switch(Transaction)
                .join(Category, JOIN.LEFT_OUTER, on=(Transaction.category_id == Category.id))
                .where(
                    (Transaction.date >= start_date) &
                    (Transaction.date < end_date)
                )
                .order_by(Transaction.date))


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


@with_retry
def category_has_transactions_for_year(category_id: str, year: int) -> bool:
    """Check if category has transactions for specific year."""
    start_date = date(year, 1, 1)
    end_date = date(year + 1, 1, 1)

    return Transaction.select().where(
        (Transaction.category_id == category_id) &
        (Transaction.date >= start_date) &
        (Transaction.date < end_date)
    ).exists()


@with_retry
def get_recent_transactions(limit: int = 5) -> list:
    """Get most recent transactions (with eager-loaded payees and categories to avoid N+1 queries)."""
    return list(Transaction
                .select(Transaction, Payee, Category)
                .join(Payee, JOIN.LEFT_OUTER, on=(Transaction.payee_id == Payee.id))
                .switch(Transaction)
                .join(Category, JOIN.LEFT_OUTER, on=(Transaction.category_id == Category.id))
                .order_by(Transaction.date.desc())
                .limit(limit))


@with_retry
def get_transactions_by_date_range(start_date: date, end_date: date) -> list:
    """Get all transactions within date range (with eager-loaded payees and categories)."""
    return list(Transaction
                .select(Transaction, Payee, Category)
                .join(Payee, JOIN.LEFT_OUTER, on=(Transaction.payee_id == Payee.id))
                .switch(Transaction)
                .join(Category, JOIN.LEFT_OUTER, on=(Transaction.category_id == Category.id))
                .where(
                    (Transaction.date >= start_date) &
                    (Transaction.date <= end_date)
                )
                .order_by(Transaction.date.desc()))


@with_retry
def get_expense_category_totals(year: int, month: int = None) -> list:
    """
    Get aggregated expense totals by category for a time period.

    Args:
        year: Year to filter transactions
        month: Optional month (1-12) to filter transactions

    Returns:
        List of dicts: [
            {
                'category_id': str,
                'category_name': str,
                'total_amount': int,
                'transaction_count': int
            }
        ]
        Only includes expense categories with transactions > 0.
    """
    from peewee import fn

    # Build date range
    if month:
        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1)
        else:
            end_date = date(year, month + 1, 1)
    else:
        start_date = date(year, 1, 1)
        end_date = date(year + 1, 1, 1)

    # Query with aggregation - use .dicts() to get results as dictionaries
    # Convert to list immediately to release the database connection
    results = list((Transaction
                    .select(
                        Category.id.alias('category_id'),
                        Category.name.alias('category_name'),
                        fn.SUM(Transaction.amount).alias('total_amount'),
                        fn.COUNT(Transaction.id).alias('transaction_count')
                    )
                    .join(Category)
                    .where(
                        (Transaction.date >= start_date) &
                        (Transaction.date < end_date) &
                        (Category.type == 'expenses')
                    )
                    .group_by(Category.id, Category.name)
                    .order_by(fn.SUM(Transaction.amount).desc())
                    .dicts()))

    # Convert to list of dicts with proper types
    result_list = []
    for row in results:
        result_list.append({
            'category_id': row['category_id'],
            'category_name': row['category_name'],
            'total_amount': int(row['total_amount']),
            'transaction_count': int(row['transaction_count'])
        })

    return result_list


# ==================== CONFIGURATION CRUD ====================

@with_transaction
def create_configuration(data: dict) -> Configuration:
    """Create configuration entry with provided data dict."""
    config = Configuration(**data)
    config.save(force_insert=True)
    logger.info(f"Created configuration: {config.key}")
    return config


@with_retry
def get_configuration_by_key(key: str) -> Configuration:
    """Get configuration by key."""
    try:
        return Configuration.get(Configuration.key == key)
    except DoesNotExist:
        return None


@with_retry
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


@with_retry
def configuration_exists(key: str) -> bool:
    """Check if configuration key exists."""
    return Configuration.select().where(Configuration.key == key).exists()


# ==================== SEED DATA ====================

def seed_initial_data():
    """
    No-op function for database seeding.

    Previously seeded categories, payees, and configuration.
    Now users create everything themselves for a clean start.

    This function is kept to maintain compatibility with existing code,
    but performs no operations.
    """
    logger.info("Database initialized - no initial data seeding (users create their own data)")
