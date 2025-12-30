"""
Tests for business_logic.py

Tests for formula parsing helper function.
"""

import pytest
import business_logic
import import_logic
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


def test_extract_amounts_from_formula_simple_addition():
    """Test extracting amounts from simple addition formula."""
    result = import_logic._extract_amounts_from_formula("=575+2182", 10, "C")
    assert result == [575, 2182]


def test_extract_amounts_from_formula_single_value():
    """Test extracting single value from formula."""
    result = import_logic._extract_amounts_from_formula("=104571", 10, "C")
    assert result == [104571]


def test_extract_amounts_from_formula_plain_number():
    """Test extracting plain number (no formula)."""
    result = import_logic._extract_amounts_from_formula("55615.0", 10, "C")
    assert result == [55615]

    result = import_logic._extract_amounts_from_formula(55615.0, 10, "C")
    assert result == [55615]


def test_extract_amounts_from_formula_zero():
    """Test that zero values are included."""
    result = import_logic._extract_amounts_from_formula("0", 10, "C")
    assert result == [0]


def test_extract_amounts_from_formula_empty():
    """Test that empty cells are skipped."""
    result = import_logic._extract_amounts_from_formula("", 10, "C")
    assert result == []

    result = import_logic._extract_amounts_from_formula(None, 10, "C")
    assert result == []


def test_extract_amounts_from_formula_rejects_complex():
    """Test that complex formulas are rejected."""
    import pytest

    with pytest.raises(ValueError, match="Complex formula not supported \\(IF\\)"):
        import_logic._extract_amounts_from_formula("=IF(A1>0,100,200)", 10, "C")

    with pytest.raises(ValueError, match="Complex formula not supported \\(SUM\\)"):
        import_logic._extract_amounts_from_formula("=SUM(A1:A5)", 10, "C")


def test_extract_amounts_from_formula_rejects_negative():
    """Test that negative values are rejected."""
    import pytest

    with pytest.raises(ValueError, match="Negative value not allowed"):
        import_logic._extract_amounts_from_formula("=-500", 10, "C")

    with pytest.raises(ValueError, match="Negative value not allowed"):
        import_logic._extract_amounts_from_formula("=100+-600", 10, "C")


def test_extract_amounts_from_formula_rejects_multiplication():
    """Test that multiplication is rejected."""
    import pytest

    with pytest.raises(ValueError, match="Only addition \\(\\+\\) supported"):
        import_logic._extract_amounts_from_formula("=43*2", 10, "C")


def test_extract_amounts_from_formula_nested_parentheses():
    """Test that nested parentheses are allowed and stripped correctly."""
    result = import_logic._extract_amounts_from_formula("=((427+275)+7292)+200", 10, "C")
    assert result == [427, 275, 7292, 200]

    # Also test single-level parentheses
    result = import_logic._extract_amounts_from_formula("=(100+200)+300", 10, "C")
    assert result == [100, 200, 300]


def test_extract_amounts_from_formula_budget_formulas():
    """Test that budget formulas are correctly parsed and can be summed."""
    # Budget cell with formula
    result = import_logic._extract_amounts_from_formula("=1000+5200", 10, "C")
    assert result == [1000, 5200]
    assert sum(result) == 6200  # Should sum to 6200 for budget total

    # Budget cell with more complex formula
    result = import_logic._extract_amounts_from_formula("=2500+3000+1500", 10, "C")
    assert result == [2500, 3000, 1500]
    assert sum(result) == 7000


def test_parse_excel_file(tmp_path):
    """Test parsing Excel file structure."""
    # Note: This test uses the real test.xlsx file
    # For unit testing, we'd use openpyxl to create a minimal test file
    # But for now, we'll test with the actual file structure

    result = import_logic.parse_excel_file("/home/xivind/code/moneybags/test.xlsx", 2024)

    assert result["year"] == 2024
    assert "sheet_categories" in result
    assert len(result["sheet_categories"]) > 0

    # Check first category structure
    first_cat = result["sheet_categories"][0]
    assert "name" in first_cat
    assert "type" in first_cat
    assert "budget" in first_cat
    assert "actuals" in first_cat

    # Budget should be dict of month: amount
    assert isinstance(first_cat["budget"], dict)

    # Actuals should be dict of month: [amounts]
    assert isinstance(first_cat["actuals"], dict)


def test_parse_excel_file_new_format(tmp_path):
    """Test parsing Excel file with new Hovedark format."""
    result = import_logic.parse_excel_file("/home/xivind/code/moneybags/new_format.xlsx", 2023)

    assert result["year"] == 2023
    assert "sheet_categories" in result
    assert len(result["sheet_categories"]) == 12  # 10 expenses + 2 income

    # Verify Stronghold (expense)
    stronghold = next((c for c in result["sheet_categories"] if c["name"] == "Stronghold"), None)
    assert stronghold is not None
    assert stronghold["type"] == "expenses"
    assert 1 in stronghold["budget"]
    assert stronghold["budget"][1] == 18500
    assert 1 in stronghold["actuals"]
    assert stronghold["actuals"][1] == [6571, 6313, 435, 3475, 1418]  # Jan formula

    # Verify IT-systemer (expense with sparse data)
    it_systemer = next((c for c in result["sheet_categories"] if c["name"] == "IT-systemer"), None)
    assert it_systemer is not None
    assert it_systemer["type"] == "expenses"
    assert 2 in it_systemer["budget"]
    assert it_systemer["budget"][2] == 3000
    assert 3 in it_systemer["actuals"]
    assert it_systemer["actuals"][3] == [2438]

    # Verify Lønn primær arbeidsgiver (income)
    lonn = next((c for c in result["sheet_categories"] if c["name"] == "Lønn primær arbeidsgiver"), None)
    assert lonn is not None
    assert lonn["type"] == "income"
    assert 1 in lonn["budget"]
    assert lonn["budget"][1] == 51000
    assert 6 in lonn["budget"]
    assert lonn["budget"][6] == 80000  # Different amount in June
    assert 1 in lonn["actuals"]
    assert lonn["actuals"][1] == [52557]

    # Verify Diverse inntekter (income with formulas)
    diverse = next((c for c in result["sheet_categories"] if c["name"] == "Diverse inntekter og overføringer"), None)
    assert diverse is not None
    assert diverse["type"] == "income"
    assert 1 in diverse["actuals"]
    assert diverse["actuals"][1] == [1271, 883, 1947, 1288]  # Formula with multiple values


def test_ensure_import_payee(setup_test_db):
    """Test getting or creating import payee."""
    # First call should create payee
    payee_id = import_logic._ensure_import_payee()
    assert payee_id is not None

    # Verify payee exists
    payee = db.get_payee_by_name("Import - Google Sheets")
    assert payee is not None
    assert payee.id == payee_id
    assert payee.type == "Generic"

    # Second call should return same payee
    payee_id_2 = import_logic._ensure_import_payee()
    assert payee_id_2 == payee_id


def test_validate_import(setup_test_db):
    """Test import validation."""
    from datetime import datetime

    # Create test categories
    cat1_data = {
        "id": "cat1",
        "name": "Salary",
        "type": "income",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    db.create_category(cat1_data)

    # Parse data structure
    parsed_data = {
        "year": 2024,
        "sheet_categories": [
            {
                "name": "Lønn",
                "type": "income",
                "budget": {1: 50000},
                "actuals": {1: [55000]}
            }
        ]
    }

    category_mapping = {
        "Lønn": "cat1"
    }

    result = import_logic.validate_import(parsed_data, category_mapping)

    assert result["valid"] is True
    assert isinstance(result["errors"], list)
    assert isinstance(result["warnings"], list)
    assert "summary" in result
    assert result["summary"]["budget_count"] == 1
    assert result["summary"]["transaction_count"] == 1


def test_validate_import_missing_category(setup_test_db):
    """Test validation fails for missing category."""
    parsed_data = {
        "year": 2024,
        "sheet_categories": [
            {
                "name": "Lønn",
                "type": "income",
                "budget": {1: 50000},
                "actuals": {1: [55000]}
            }
        ]
    }

    category_mapping = {
        "Lønn": "nonexistent123"
    }

    result = import_logic.validate_import(parsed_data, category_mapping)

    assert result["valid"] is False
    assert len(result["errors"]) > 0
    # Check for error about category not existing (contains "does not exist" message)
    assert any("does not exist" in err.lower() for err in result["errors"])


def test_import_budget_and_transactions(setup_test_db):
    """Test full import execution."""
    from datetime import datetime

    # Create test category
    cat_data = {
        "id": "cat_import",
        "name": "Test Import Cat",
        "type": "income",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    db.create_category(cat_data)

    # Parsed data
    parsed_data = {
        "year": 2024,
        "sheet_categories": [
            {
                "name": "Test Import Cat",
                "type": "income",
                "budget": {1: 50000, 2: 52000},
                "actuals": {1: [55000, 1000], 2: [53000]}
            }
        ]
    }

    category_mapping = {
        "Test Import Cat": "cat_import"
    }

    result = import_logic.import_budget_and_transactions(parsed_data, category_mapping)

    assert result["budget_count"] == 2
    assert result["transaction_count"] == 3
    assert result["template_count"] == 1  # Should auto-create budget template entry

    # Verify budget entries created
    budget_jan = db.get_budget_entry("cat_import", 2024, 1)
    assert budget_jan is not None
    assert budget_jan.amount == 50000

    budget_feb = db.get_budget_entry("cat_import", 2024, 2)
    assert budget_feb is not None
    assert budget_feb.amount == 52000

    # Verify transactions created
    transactions = list(Transaction.select().where(
        Transaction.category_id == "cat_import"
    ))
    assert len(transactions) == 3

    # Verify payee
    import_payee = db.get_payee_by_name("Import - Google Sheets")
    assert import_payee is not None
    for tx in transactions:
        # tx.payee_id is a Payee object (PeeWee foreign key), so access .id
        assert tx.payee_id.id == import_payee.id

    # Verify budget template entry was created
    assert db.budget_template_exists(2024, "cat_import") is True
