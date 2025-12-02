"""Database models using PeeWee ORM."""
from peewee import (
    Model, SqliteDatabase, CharField, DateTimeField,
    IntegerField, DecimalField, DateField, TextField, ForeignKeyField, SQL
)


# Database instance (will be initialized later)
db = SqliteDatabase(None)


class BaseModel(Model):
    """Base model with common fields."""
    class Meta:
        database = db


class Post(BaseModel):
    """Master definition of budget line items."""
    id = CharField(primary_key=True, max_length=36)
    name = CharField(max_length=255, unique=True)
    type = CharField(max_length=10)  # 'income' or 'expense'
    created_at = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")])
    updated_at = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")])

    class Meta:
        table_name = 'posts'


class Tag(BaseModel):
    """Reusable labels for grouping posts."""
    id = CharField(primary_key=True, max_length=36)
    name = CharField(max_length=100, unique=True)

    class Meta:
        table_name = 'tags'


class PostTag(BaseModel):
    """Many-to-many relationship between Posts and Tags."""
    post = ForeignKeyField(Post)
    tag = ForeignKeyField(Tag)

    class Meta:
        table_name = 'post_tags'
        indexes = (
            (('post', 'tag'), True),  # Unique together
        )


class BudgetEntry(BaseModel):
    """Monthly budget values for posts."""
    id = CharField(primary_key=True, max_length=36)
    post = ForeignKeyField(Post)
    year = IntegerField()
    month = IntegerField()  # 1-12
    amount = DecimalField(max_digits=15, decimal_places=2)
    created_at = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")])
    updated_at = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")])

    class Meta:
        table_name = 'budget_entries'
        indexes = (
            (('post', 'year', 'month'), True),  # Unique together
        )


class ActualEntry(BaseModel):
    """Real income/expenses with specific dates."""
    id = CharField(primary_key=True, max_length=36)
    post = ForeignKeyField(Post)
    date = DateField()
    amount = DecimalField(max_digits=15, decimal_places=2)
    comment = TextField(null=True)
    created_at = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")])
    updated_at = DateTimeField(constraints=[SQL("DEFAULT CURRENT_TIMESTAMP")])

    class Meta:
        table_name = 'actual_entries'


class UserPreference(BaseModel):
    """Application configuration settings."""
    id = CharField(primary_key=True, max_length=36)
    key = CharField(max_length=100, unique=True)
    value = CharField(max_length=500)

    class Meta:
        table_name = 'user_preferences'


def initialize_database(database_path: str):
    """
    Initialize database connection and create tables.

    Args:
        database_path: Path to SQLite database file
    """
    db.init(database_path)
    db.create_tables([Post, Tag, PostTag, BudgetEntry, ActualEntry, UserPreference])
