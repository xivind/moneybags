"""
Tests for database_manager.py

Tests CRUD operations for the import feature.
"""

import pytest
from datetime import datetime
import pymysql
from database_model import database, Category, Payee, BudgetEntry, BudgetTemplate, Transaction, Configuration
import database_manager as db


@pytest.fixture(scope="session", autouse=True)
def create_test_database():
    """Create test database once at session start."""
    conn = pymysql.connect(
        host="sandbox",
        port=3306,
        user="root",
        password="devpassword"
    )
    try:
        with conn.cursor() as cursor:
            cursor.execute("CREATE DATABASE IF NOT EXISTS moneybags_test")
        conn.commit()
    finally:
        conn.close()


@pytest.fixture(scope="function")
def setup_test_db():
    """Setup test database before each test, teardown after."""
    # Initialize test database
    db.initialize_connection(
        host="sandbox",
        port=3306,
        database_name="moneybags_test",
        user="root",
        password="devpassword",
        pool_size=5
    )

    # Create tables
    db.create_tables_if_not_exist()

    yield

    # Cleanup - truncate all tables and close connection
    try:
        # Truncate tables instead of dropping them (faster and preserves schema)
        Transaction.delete().execute()
        BudgetEntry.delete().execute()
        BudgetTemplate.delete().execute()
        Payee.delete().execute()
        Category.delete().execute()
        Configuration.delete().execute()
    except:
        pass  # Ignore errors during cleanup
    finally:
        db.close_connection()


def test_get_payee_by_name(setup_test_db):
    """Test getting payee by exact name match."""
    # Create a test payee
    payee_data = {
        "id": "test123",
        "name": "Test Payee",
        "type": "Generic",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    db.create_payee(payee_data)

    # Get by name
    result = db.get_payee_by_name("Test Payee")
    assert result is not None
    assert result.name == "Test Payee"

    # Non-existent payee
    result = db.get_payee_by_name("Does Not Exist")
    assert result is None


def test_create_or_update_budget_entry(setup_test_db):
    """Test creating and updating budget entries."""
    # First create a category (required foreign key)
    category_data = {
        "id": "cat123",
        "name": "Test Category",
        "type": "Expense",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    db.create_category(category_data)

    category_id = "cat123"
    year = 2024
    month = 1

    # Create new entry
    data = {
        "id": "budget123",
        "category_id": category_id,
        "year": year,
        "month": month,
        "amount": 50000,
        "comment": "Initial",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    result = db.create_or_update_budget_entry(data)
    assert result.amount == 50000
    assert result.comment == "Initial"

    # Update existing entry
    data["amount"] = 60000
    data["comment"] = "Updated"
    data["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    result = db.create_or_update_budget_entry(data)
    assert result.amount == 60000
    assert result.comment == "Updated"

    # Verify only one entry exists
    entries = list(BudgetEntry.select().where(
        (BudgetEntry.category_id == category_id) &
        (BudgetEntry.year == year) &
        (BudgetEntry.month == month)
    ))
    assert len(entries) == 1
