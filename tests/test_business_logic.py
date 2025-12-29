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
