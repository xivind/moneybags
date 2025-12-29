"""
Tests for business_logic.py

Tests for formula parsing helper function.
"""

import pytest
import business_logic


def test_extract_amounts_from_formula_simple_addition():
    """Test extracting amounts from simple addition formula."""
    result = business_logic._extract_amounts_from_formula("=575+2182", 10, "C")
    assert result == [575, 2182]


def test_extract_amounts_from_formula_single_value():
    """Test extracting single value from formula."""
    result = business_logic._extract_amounts_from_formula("=104571", 10, "C")
    assert result == [104571]


def test_extract_amounts_from_formula_plain_number():
    """Test extracting plain number (no formula)."""
    result = business_logic._extract_amounts_from_formula("55615.0", 10, "C")
    assert result == [55615]

    result = business_logic._extract_amounts_from_formula(55615.0, 10, "C")
    assert result == [55615]


def test_extract_amounts_from_formula_zero():
    """Test that zero values are included."""
    result = business_logic._extract_amounts_from_formula("0", 10, "C")
    assert result == [0]


def test_extract_amounts_from_formula_empty():
    """Test that empty cells are skipped."""
    result = business_logic._extract_amounts_from_formula("", 10, "C")
    assert result == []

    result = business_logic._extract_amounts_from_formula(None, 10, "C")
    assert result == []


def test_extract_amounts_from_formula_rejects_complex():
    """Test that complex formulas are rejected."""
    import pytest

    with pytest.raises(ValueError, match="Complex formula not supported \\(IF\\)"):
        business_logic._extract_amounts_from_formula("=IF(A1>0,100,200)", 10, "C")

    with pytest.raises(ValueError, match="Complex formula not supported \\(SUM\\)"):
        business_logic._extract_amounts_from_formula("=SUM(A1:A5)", 10, "C")


def test_extract_amounts_from_formula_rejects_negative():
    """Test that negative values are rejected."""
    import pytest

    with pytest.raises(ValueError, match="Negative value not allowed"):
        business_logic._extract_amounts_from_formula("=-500", 10, "C")

    with pytest.raises(ValueError, match="Negative value not allowed"):
        business_logic._extract_amounts_from_formula("=100+-600", 10, "C")


def test_extract_amounts_from_formula_rejects_multiplication():
    """Test that multiplication is rejected."""
    import pytest

    with pytest.raises(ValueError, match="Only addition \\(\\+\\) supported"):
        business_logic._extract_amounts_from_formula("=43*2", 10, "C")


def test_parse_excel_file(tmp_path):
    """Test parsing Excel file structure."""
    # Note: This test uses the real test.xlsx file
    # For unit testing, we'd use openpyxl to create a minimal test file
    # But for now, we'll test with the actual file structure

    result = business_logic.parse_excel_file("/home/xivind/code/moneybags/test.xlsx", 2024)

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


def test_ensure_import_payee():
    """Test getting or creating import payee."""
    import database_manager as db

    # First call should create payee
    payee_id = business_logic._ensure_import_payee()
    assert payee_id is not None

    # Verify payee exists
    payee = db.get_payee_by_name("Import - Google Sheets")
    assert payee is not None
    assert payee.id == payee_id
    assert payee.type == "Generic"

    # Second call should return same payee
    payee_id_2 = business_logic._ensure_import_payee()
    assert payee_id_2 == payee_id


def test_validate_import():
    """Test import validation."""
    import database_manager as db
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

    result = business_logic.validate_import(parsed_data, category_mapping)

    assert result["valid"] is True
    assert isinstance(result["errors"], list)
    assert isinstance(result["warnings"], list)
    assert "summary" in result
    assert result["summary"]["budget_count"] == 1
    assert result["summary"]["transaction_count"] == 1


def test_validate_import_missing_category():
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

    result = business_logic.validate_import(parsed_data, category_mapping)

    assert result["valid"] is False
    assert len(result["errors"]) > 0
    assert any("not found" in err.lower() for err in result["errors"])


def test_import_budget_and_transactions():
    """Test full import execution."""
    import database_manager as db
    from datetime import datetime
    from database_model import Transaction

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

    result = business_logic.import_budget_and_transactions(parsed_data, category_mapping)

    assert result["budget_count"] == 2
    assert result["transaction_count"] == 3

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
        assert tx.payee_id == import_payee.id
