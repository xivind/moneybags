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
