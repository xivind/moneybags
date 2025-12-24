"""
Database models for Moneybags application.

All models use PeeWee ORM and follow these principles:
- UUIDs generated in business_logic.py via utils.generate_uid()
- All currency amounts stored as integers
- Empty strings converted to NULL via utils.empty_to_none()
- NO LOGIC IN MODELS - pure data structures only
- All constraints, defaults, and business rules enforced in business_logic.py
- Timestamps set explicitly by business_logic.py (YYYY-MM-DD HH:MM:SS format)

See DATABASE_DESIGN.md for complete schema documentation.
"""

from peewee import (
    Model,
    CharField,
    IntegerField,
    SmallIntegerField,
    DateField,
    DateTimeField,
    TextField,
    ForeignKeyField,
)
from playhouse.pool import PooledMySQLDatabase


# Database connection instance (with connection pooling)
# Will be initialized in database_manager.py with connection details from configuration
database = PooledMySQLDatabase(None)


class BaseModel(Model):
    """
    Base model with common fields.

    All models inherit from this to get:
    - id field (UUID - set by business_logic.py)
    - created_at timestamp (set by business_logic.py)
    - Shared database connection

    Note: No logic in models. All field values set by business_logic.py
    before passing to database_manager.py.
    """
    id = CharField(primary_key=True, max_length=10)
    created_at = DateTimeField()

    class Meta:
        database = database


class Category(BaseModel):
    """
    Income and expense categories.

    Categories are global across all years. A category can be either 'income'
    or 'expenses' type. Category names must be globally unique.

    Business rules (enforced in business_logic.py):
    - Cannot delete if referenced by budget_templates, budget_entries, or transactions
    - Cannot change type if data exists
    - Name must be unique (case-insensitive comparison)
    """
    name = CharField(max_length=255, unique=True)
    type = CharField(max_length=10)  # 'income' or 'expenses'

    class Meta:
        table_name = 'moneybags_categories'


class Payee(BaseModel):
    """
    Payees that appear in transactions.

    Payees are global entities. Type can be 'Generic' (e.g., "Hairdresser")
    or 'Actual' (e.g., "Bad Hairday Ltd").

    Business rules (enforced in business_logic.py):
    - Cannot delete if referenced by transactions
    - Renaming updates all transaction references
    - Name must be unique (case-insensitive comparison)
    """
    name = CharField(max_length=255, unique=True)
    type = CharField(max_length=10, default='Actual')  # 'Generic' or 'Actual'

    class Meta:
        table_name = 'moneybags_payees'


class BudgetTemplate(BaseModel):
    """
    Defines which categories are active/visible for each year's budget.

    This table controls which categories appear in the budget view for a given year.
    Users can copy templates from previous years or build from scratch.

    Business rules (enforced in business_logic.py):
    - Unique constraint on (year, category_id)
    - Cannot remove category if budget_entries or transactions exist for that year
    - Deletion logic handled in business_logic.py (no cascade deletes)
    """
    year = IntegerField()
    category_id = ForeignKeyField(Category, column_name='category_id')

    class Meta:
        table_name = 'moneybags_budget_templates'
        indexes = (
            (('year', 'category_id'), False),  # Composite index for year/category lookups
        )


class BudgetEntry(BaseModel):
    """
    Budget amounts for each category, year, and month.

    Stores the budgeted amount for a specific category in a specific month/year.
    Amount is stored as integer (no decimals). Comment is optional.

    Business rules (enforced in business_logic.py):
    - Unique constraint on (category_id, year, month)
    - Month must be 1-12
    - Category must exist in budget_templates for that year
    - Deletion logic handled in business_logic.py
    - Empty comment stored as NULL (via utils.empty_to_none)
    - updated_at set by business_logic.py on create/update
    """
    category_id = ForeignKeyField(Category, column_name='category_id')
    year = IntegerField()
    month = SmallIntegerField()  # 1-12
    amount = IntegerField()
    comment = TextField(null=True)
    updated_at = DateTimeField()

    class Meta:
        table_name = 'moneybags_budget_entries'
        indexes = (
            (('category_id', 'year', 'month'), False),  # Composite index for fast lookups
        )


class Transaction(BaseModel):
    """
    Actual income and expense transactions.

    Records actual financial transactions. Amount is stored as integer (no decimals).
    Payee is optional. Comment is optional. Year/month derived from date (not denormalized).

    Business rules (enforced in business_logic.py):
    - Date must be valid
    - Empty payee_id or comment stored as NULL (via utils.empty_to_none)
    - Deletion logic handled in business_logic.py
    - Payee deletion/update logic handled in business_logic.py
    - updated_at set by business_logic.py on create/update
    """
    category_id = ForeignKeyField(Category, column_name='category_id')
    payee_id = ForeignKeyField(Payee, column_name='payee_id', null=True)
    date = DateField()
    amount = IntegerField()
    comment = TextField(null=True)
    updated_at = DateTimeField()

    class Meta:
        table_name = 'moneybags_transactions'
        indexes = (
            # Note: category_id and payee_id indexes are automatically created by ForeignKeyField
            (('date',), False),  # Index for date-based queries
        )


class Configuration(BaseModel):
    """
    Application configuration settings.

    Stores key-value pairs for application settings including:
    - currency_format: "nok", "usd", "eur"
    - database_seeded: "true" or "false" (internal flag for first-time setup)

    NOTE: Database connection settings (host, port, credentials, pool size, etc.)
    are stored in moneybags_db_config.json file, NOT in this table.

    Business rules (enforced in business_logic.py):
    - Keys must be unique
    - Validation for specific key formats
    - updated_at set by business_logic.py on create/update
    """
    key = CharField(max_length=255, unique=True)
    value = TextField()
    updated_at = DateTimeField()

    class Meta:
        table_name = 'moneybags_configuration'


# List of all models for easy reference
ALL_MODELS = [
    Category,
    Payee,
    BudgetTemplate,
    BudgetEntry,
    Transaction,
    Configuration,
]
