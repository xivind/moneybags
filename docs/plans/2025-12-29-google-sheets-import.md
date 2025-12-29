# Google Sheets Import Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Import budget and transaction data from Google Sheets Excel exports, parsing formulas to extract individual transaction amounts.

**Architecture:** Three-layer clean architecture: main.py (router) → business_logic.py (parsing/validation) → database_manager.py (CRUD). Frontend uses htmx patterns with step-by-step validation before import.

**Tech Stack:** FastAPI, openpyxl (Excel parsing), existing PeeWee ORM, Bootstrap, vanilla JavaScript

---

## Task 1: Add Dependencies

**Files:**
- Modify: `requirements.txt`

**Step 1: Add openpyxl to requirements**

Add to end of `requirements.txt`:
```
# Excel file parsing
openpyxl==3.1.5
```

**Step 2: Install dependencies**

Run: `source /home/xivind/code/moneybags-runtime/bin/activate && pip install openpyxl`
Expected: Successfully installed openpyxl-3.1.5 et-xmlfile-2.0.0

**Step 3: Commit**

```bash
git add requirements.txt
git commit -m "feat: add openpyxl dependency for Excel import"
```

---

## Task 2: Add Database Manager Functions

**Files:**
- Modify: `database_manager.py`
- Test: `tests/test_database_manager.py`

**Step 1: Write test for get_payee_by_name**

Add to `tests/test_database_manager.py`:
```python
def test_get_payee_by_name():
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
```

**Step 2: Run test to verify it fails**

Run: `source /home/xivind/code/moneybags-runtime/bin/activate && pytest tests/test_database_manager.py::test_get_payee_by_name -v`
Expected: FAIL with "AttributeError: module 'database_manager' has no attribute 'get_payee_by_name'"

**Step 3: Implement get_payee_by_name**

Add to `database_manager.py` after existing payee functions:
```python
@with_retry
def get_payee_by_name(name: str) -> Optional[Payee]:
    """
    Get payee by exact name match.

    Args:
        name: Payee name to search for

    Returns:
        Payee object if found, None otherwise
    """
    return Payee.get_or_none(Payee.name == name)
```

**Step 4: Run test to verify it passes**

Run: `source /home/xivind/code/moneybags-runtime/bin/activate && pytest tests/test_database_manager.py::test_get_payee_by_name -v`
Expected: PASS

**Step 5: Write test for create_or_update_budget_entry**

Add to `tests/test_database_manager.py`:
```python
def test_create_or_update_budget_entry():
    """Test creating and updating budget entries."""
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
```

**Step 6: Run test to verify it fails**

Run: `source /home/xivind/code/moneybags-runtime/bin/activate && pytest tests/test_database_manager.py::test_create_or_update_budget_entry -v`
Expected: FAIL with "AttributeError: module 'database_manager' has no attribute 'create_or_update_budget_entry'"

**Step 7: Implement create_or_update_budget_entry**

Add to `database_manager.py` after budget entry functions:
```python
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
```

**Step 8: Run test to verify it passes**

Run: `source /home/xivind/code/moneybags-runtime/bin/activate && pytest tests/test_database_manager.py::test_create_or_update_budget_entry -v`
Expected: PASS

**Step 9: Commit**

```bash
git add database_manager.py tests/test_database_manager.py
git commit -m "feat: add database functions for import (get_payee_by_name, create_or_update_budget_entry)"
```

---

## Task 3: Add Formula Parsing Helper

**Files:**
- Modify: `business_logic.py`
- Test: `tests/test_business_logic.py`

**Step 1: Write tests for _extract_amounts_from_formula**

Add to `tests/test_business_logic.py`:
```python
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
```

**Step 2: Run tests to verify they fail**

Run: `source /home/xivind/code/moneybags-runtime/bin/activate && pytest tests/test_business_logic.py -k extract_amounts -v`
Expected: FAIL with "AttributeError: module 'business_logic' has no attribute '_extract_amounts_from_formula'"

**Step 3: Implement _extract_amounts_from_formula**

Add to `business_logic.py` after other helper functions:
```python
def _extract_amounts_from_formula(cell_value, row_num: int, col_name: str) -> list[int]:
    """
    Extract individual amounts from Excel formula or value.

    Strict validation - only simple addition formulas allowed.

    Args:
        cell_value: Cell value (formula string or number)
        row_num: Row number for error messages
        col_name: Column name for error messages

    Returns:
        List of integer amounts extracted from formula

    Raises:
        ValueError: On invalid formula format or negative values

    Examples:
        "=575+2182" → [575, 2182]
        "=104571" → [104571]
        "55615.0" → [55615]
        "0" → [0]
        "" → []
    """
    # Handle None or empty
    if cell_value is None or cell_value == "":
        return []

    # Convert to string
    formula_str = str(cell_value).strip()

    # Empty after strip
    if not formula_str:
        return []

    # Remove "=" prefix if present
    if formula_str.startswith("="):
        formula_str = formula_str[1:]

    # Check for forbidden operations/functions
    forbidden = ["IF", "SUM", "AVERAGE", "COUNT", "MIN", "MAX", "*", "/", "-", "(", ")"]
    for forbidden_item in forbidden:
        if forbidden_item in formula_str:
            if forbidden_item in ["IF", "SUM", "AVERAGE", "COUNT", "MIN", "MAX"]:
                raise ValueError(f"Row {row_num}, Column {col_name}: Complex formula not supported ({forbidden_item})")
            elif forbidden_item == "-":
                # Allow negative check after splitting
                pass
            else:
                raise ValueError(f"Row {row_num}, Column {col_name}: Only addition (+) supported")

    # Split by "+"
    parts = formula_str.split("+")

    # Convert to integers
    amounts = []
    for part in parts:
        part = part.strip()
        if not part:
            continue

        try:
            # Convert to float first (handles decimals), then to int
            value = int(float(part))

            # Reject negative values
            if value < 0:
                raise ValueError(f"Row {row_num}, Column {col_name}: Negative value not allowed ({value})")

            amounts.append(value)
        except ValueError as e:
            if "Negative value not allowed" in str(e):
                raise
            raise ValueError(f"Row {row_num}, Column {col_name}: Invalid number format: {part}")

    return amounts
```

**Step 4: Run tests to verify they pass**

Run: `source /home/xivind/code/moneybags-runtime/bin/activate && pytest tests/test_business_logic.py -k extract_amounts -v`
Expected: PASS (all tests)

**Step 5: Commit**

```bash
git add business_logic.py tests/test_business_logic.py
git commit -m "feat: add formula parsing helper for Excel import"
```

---

## Task 4: Add Excel Parsing Function

**Files:**
- Modify: `business_logic.py`
- Test: `tests/test_business_logic.py`

**Step 1: Write test for parse_excel_file**

Add to `tests/test_business_logic.py`:
```python
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
```

**Step 2: Run test to verify it fails**

Run: `source /home/xivind/code/moneybags-runtime/bin/activate && pytest tests/test_business_logic.py::test_parse_excel_file -v`
Expected: FAIL with "AttributeError: module 'business_logic' has no attribute 'parse_excel_file'"

**Step 3: Implement parse_excel_file**

Add to `business_logic.py`:
```python
def parse_excel_file(file_path: str, year: int) -> dict:
    """
    Parse Google Sheets Excel file and extract budget/actual data.

    Expected structure:
    - Row 3: Headers ("Balanse", "Januar", ..., "Desember")
    - Row 7: "Inntekter" section
    - Row 16+: "Utgifter" section
    - Category blocks every 4 rows:
      - Row N: Category name
      - Row N+1: "Budsjett" (budget values)
      - Row N+2: "Resultat" (actual formulas)
      - Row N+3: "Differanse" (skip)

    Args:
        file_path: Path to .xlsx file
        year: Year for the data

    Returns:
        {
            "year": 2024,
            "sheet_categories": [
                {
                    "name": "Lønn",
                    "type": "income",
                    "budget": {1: 52000, 2: 52000, ...},
                    "actuals": {1: [55615], 2: [55615], ...}
                }
            ]
        }

    Raises:
        ValueError: On validation errors
    """
    import openpyxl

    # Validate year
    if not validate_year(year):
        raise ValueError(f"Invalid year: {year}")

    # Load workbook
    try:
        wb = openpyxl.load_workbook(file_path, data_only=False)
    except Exception as e:
        raise ValueError(f"Failed to load Excel file: {e}")

    sheet = wb.active

    # Month column mapping (C=1, D=2, ..., N=12)
    month_columns = {
        'C': 1, 'D': 2, 'E': 3, 'F': 4, 'G': 5, 'H': 6,
        'I': 7, 'J': 8, 'K': 9, 'L': 10, 'M': 11, 'N': 12
    }

    # Find "Utgifter" row to split income vs expenses
    utgifter_row = None
    for row_idx in range(1, 100):
        cell = sheet[f'B{row_idx}']
        if cell.value and "Utgifter" in str(cell.value):
            utgifter_row = row_idx
            break

    if not utgifter_row:
        raise ValueError("Could not find 'Utgifter' section in Excel file")

    sheet_categories = []

    # Parse categories (every 4 rows, starting from row 8)
    for row_idx in range(8, 60, 4):
        category_cell = sheet[f'B{row_idx}']
        category_name = category_cell.value

        # Skip if no category name or if it's a header row
        if not category_name or category_name in ["Inntekter", "Utgifter", "Balanse"]:
            continue

        category_name = str(category_name).strip()

        # Determine type (income if before utgifter_row, expenses after)
        category_type = "income" if row_idx < utgifter_row else "expenses"

        # Extract budget values (row N+1)
        budget = {}
        budget_row = row_idx + 1
        for col, month in month_columns.items():
            cell = sheet[f'{col}{budget_row}']
            if cell.value:
                try:
                    amount = int(float(cell.value)) if cell.value else 0
                    budget[month] = amount
                except (ValueError, TypeError):
                    # Skip invalid values
                    pass

        # Extract actual values (row N+2)
        actuals = {}
        actuals_row = row_idx + 2
        for col, month in month_columns.items():
            cell = sheet[f'{col}{actuals_row}']
            if cell.value:
                try:
                    amounts = _extract_amounts_from_formula(cell.value, actuals_row, col)
                    if amounts:
                        actuals[month] = amounts
                except ValueError as e:
                    raise ValueError(f"Category '{category_name}': {e}")

        # Skip categories with no data
        if not budget and not actuals:
            continue

        sheet_categories.append({
            "name": category_name,
            "type": category_type,
            "budget": budget,
            "actuals": actuals
        })

    if not sheet_categories:
        raise ValueError("No categories found in Excel file")

    return {
        "year": year,
        "sheet_categories": sheet_categories
    }
```

**Step 4: Run test to verify it passes**

Run: `source /home/xivind/code/moneybags-runtime/bin/activate && pytest tests/test_business_logic.py::test_parse_excel_file -v`
Expected: PASS

**Step 5: Commit**

```bash
git add business_logic.py tests/test_business_logic.py
git commit -m "feat: add Excel file parsing for Google Sheets import"
```

---

## Task 5: Add Import Payee Helper

**Files:**
- Modify: `business_logic.py`
- Test: `tests/test_business_logic.py`

**Step 1: Write test for _ensure_import_payee**

Add to `tests/test_business_logic.py`:
```python
def test_ensure_import_payee():
    """Test getting or creating import payee."""
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
```

**Step 2: Run test to verify it fails**

Run: `source /home/xivind/code/moneybags-runtime/bin/activate && pytest tests/test_business_logic.py::test_ensure_import_payee -v`
Expected: FAIL with "AttributeError: module 'business_logic' has no attribute '_ensure_import_payee'"

**Step 3: Implement _ensure_import_payee**

Add to `business_logic.py`:
```python
def _ensure_import_payee() -> str:
    """
    Get or create "Import - Google Sheets" payee.

    Returns:
        str: Payee UUID
    """
    payee = db.get_payee_by_name("Import - Google Sheets")
    if payee:
        return payee.id

    # Create payee
    data = {
        "id": generate_uid(),
        "name": "Import - Google Sheets",
        "type": "Generic",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    payee = db.create_payee(data)
    return payee.id
```

**Step 4: Run test to verify it passes**

Run: `source /home/xivind/code/moneybags-runtime/bin/activate && pytest tests/test_business_logic.py::test_ensure_import_payee -v`
Expected: PASS

**Step 5: Commit**

```bash
git add business_logic.py tests/test_business_logic.py
git commit -m "feat: add import payee helper for Google Sheets import"
```

---

## Task 6: Add Import Validation Function

**Files:**
- Modify: `business_logic.py`
- Test: `tests/test_business_logic.py`

**Step 1: Write test for validate_import**

Add to `tests/test_business_logic.py`:
```python
def test_validate_import():
    """Test import validation."""
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
```

**Step 2: Run tests to verify they fail**

Run: `source /home/xivind/code/moneybags-runtime/bin/activate && pytest tests/test_business_logic.py -k validate_import -v`
Expected: FAIL with "AttributeError: module 'business_logic' has no attribute 'validate_import'"

**Step 3: Implement validate_import**

Add to `business_logic.py`:
```python
def validate_import(parsed_data: dict, category_mapping: dict) -> dict:
    """
    Dry-run validation before import.

    Checks:
    - All mapped categories exist
    - Category types match (income/expenses)
    - Check for duplicate BudgetEntries
    - Check for duplicate Transactions

    Args:
        parsed_data: Parsed Excel data structure
        category_mapping: Dict mapping sheet category names to Moneybags category IDs

    Returns:
        {
            "valid": True/False,
            "errors": ["..."],
            "warnings": ["..."],
            "summary": {"budget_count": 120, "transaction_count": 347}
        }
    """
    errors = []
    warnings = []
    budget_count = 0
    transaction_count = 0

    year = parsed_data["year"]

    # Validate all categories exist and types match
    for sheet_cat in parsed_data["sheet_categories"]:
        sheet_name = sheet_cat["name"]

        # Check category is mapped
        if sheet_name not in category_mapping:
            errors.append(f"Category '{sheet_name}' not mapped")
            continue

        category_id = category_mapping[sheet_name]

        # Check category exists
        category = db.get_category_by_id(category_id)
        if not category:
            errors.append(f"Category '{sheet_name}' mapped to '{category_id}' which does not exist")
            continue

        # Check type matches
        if category.type != sheet_cat["type"]:
            errors.append(f"Category '{sheet_name}' type mismatch: sheet has '{sheet_cat['type']}' but Moneybags has '{category.type}'")
            continue

        # Count budget entries and check for duplicates
        for month in sheet_cat["budget"].keys():
            existing = db.get_budget_entry(category_id, year, month)
            if existing:
                warnings.append(f"Budget entry for '{category.name}' {year}-{month:02d} already exists - will overwrite")
            budget_count += 1

        # Count transactions
        for month, amounts in sheet_cat["actuals"].items():
            transaction_count += len(amounts)

    # Final validation
    valid = len(errors) == 0

    return {
        "valid": valid,
        "errors": errors,
        "warnings": warnings,
        "summary": {
            "budget_count": budget_count,
            "transaction_count": transaction_count
        }
    }
```

**Step 4: Run tests to verify they pass**

Run: `source /home/xivind/code/moneybags-runtime/bin/activate && pytest tests/test_business_logic.py -k validate_import -v`
Expected: PASS (all tests)

**Step 5: Commit**

```bash
git add business_logic.py tests/test_business_logic.py
git commit -m "feat: add import validation function"
```

---

## Task 7: Add Import Execution Function

**Files:**
- Modify: `business_logic.py`
- Test: `tests/test_business_logic.py`

**Step 1: Write test for import_budget_and_transactions**

Add to `tests/test_business_logic.py`:
```python
def test_import_budget_and_transactions():
    """Test full import execution."""
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
```

**Step 2: Run test to verify it fails**

Run: `source /home/xivind/code/moneybags-runtime/bin/activate && pytest tests/test_business_logic.py::test_import_budget_and_transactions -v`
Expected: FAIL with "AttributeError: module 'business_logic' has no attribute 'import_budget_and_transactions'"

**Step 3: Implement import_budget_and_transactions**

Add to `business_logic.py`:
```python
def import_budget_and_transactions(parsed_data: dict, category_mapping: dict) -> dict:
    """
    Create BudgetEntry and Transaction records from parsed data.

    Prerequisites: validate_import() should pass before calling this

    Args:
        parsed_data: Parsed Excel data structure
        category_mapping: Dict mapping sheet category names to Moneybags category IDs

    Returns:
        {
            "budget_count": 120,
            "transaction_count": 347,
            "message": "Successfully imported data"
        }

    Raises:
        ValueError: On errors
    """
    import_payee_id = _ensure_import_payee()

    budget_count = 0
    transaction_count = 0

    year = parsed_data["year"]

    for sheet_category in parsed_data["sheet_categories"]:
        category_id = category_mapping[sheet_category["name"]]

        # Import budget entries
        for month, amount in sheet_category["budget"].items():
            data = {
                "id": generate_uid(),
                "category_id": category_id,
                "year": year,
                "month": month,
                "amount": amount,
                "comment": empty_to_none(None),
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            db.create_or_update_budget_entry(data)
            budget_count += 1

        # Import transactions
        for month, amounts in sheet_category["actuals"].items():
            for amount in amounts:
                date_str = f"{year}-{month:02d}-01"
                data = {
                    "id": generate_uid(),
                    "category_id": category_id,
                    "payee_id": import_payee_id,
                    "date": date_str,
                    "amount": amount,
                    "comment": empty_to_none(None),
                    "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                db.create_transaction(data)
                transaction_count += 1

    logger.info(f"Imported {budget_count} budget entries and {transaction_count} transactions")

    return {
        "budget_count": budget_count,
        "transaction_count": transaction_count,
        "message": "Successfully imported data"
    }
```

**Step 4: Run test to verify it passes**

Run: `source /home/xivind/code/moneybags-runtime/bin/activate && pytest tests/test_business_logic.py::test_import_budget_and_transactions -v`
Expected: PASS

**Step 5: Commit**

```bash
git add business_logic.py tests/test_business_logic.py
git commit -m "feat: add import execution function"
```

---

## Task 8: Add API Routes

**Files:**
- Modify: `main.py`

**Step 1: Add import page route**

Add to `main.py` after other page routes:
```python
@app.get("/import", response_class=HTMLResponse)
def import_page(request: Request):
    """Import from Google Sheets Excel files"""
    return templates.TemplateResponse("import.html", {
        "request": request
    })
```

**Step 2: Add parse API route**

Add to `main.py` after import page route:
```python
@app.post("/api/import/parse")
async def parse_import_file(file: UploadFile = File(...), year: int = Form(...)):
    """
    Parse uploaded Excel file and extract budget/actual data.

    Returns parsed data structure with categories, budget, and actuals.
    """
    try:
        # Validate file extension
        if not file.filename.endswith('.xlsx'):
            raise ValueError("Only .xlsx files supported")

        # Save to temp file
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
            content = await file.read()
            tmp.write(content)
            tmp_path = tmp.name

        try:
            # Call business logic for parsing
            result = business_logic.parse_excel_file(tmp_path, year)
            return {"success": True, "data": result}
        finally:
            # Clean up temp file
            os.unlink(tmp_path)

    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": str(e)}
        )
    except Exception as e:
        logger.error(f"Error parsing import file: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )
```

**Step 3: Add validate API route**

Add to `main.py`:
```python
@app.post("/api/import/validate")
async def validate_import_data(request: Request):
    """
    Validate import data before execution (dry-run).

    Request body:
    {
        "parsed_data": {...},
        "category_mapping": {"Lønn": "uuid-123", ...}
    }
    """
    try:
        data = await request.json()
        result = business_logic.validate_import(
            parsed_data=data["parsed_data"],
            category_mapping=data["category_mapping"]
        )
        return {"success": True, "data": result}
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": str(e)}
        )
    except KeyError as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": f"Missing required field: {e}"}
        )
    except Exception as e:
        logger.error(f"Error validating import: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )
```

**Step 4: Add execute API route**

Add to `main.py`:
```python
@app.post("/api/import/execute")
async def execute_import(request: Request):
    """
    Execute import - create BudgetEntry and Transaction records.

    Request body: Same as /api/import/validate
    """
    try:
        data = await request.json()
        result = business_logic.import_budget_and_transactions(
            parsed_data=data["parsed_data"],
            category_mapping=data["category_mapping"]
        )
        return {"success": True, "data": result}
    except ValueError as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": str(e)}
        )
    except KeyError as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": f"Missing required field: {e}"}
        )
    except Exception as e:
        logger.error(f"Error executing import: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": str(e)}
        )
```

**Step 5: Add missing imports at top of main.py**

Add to imports section:
```python
from fastapi import FastAPI, Request, UploadFile, File, Form
```

**Step 6: Test API routes manually**

Run: `source /home/xivind/code/moneybags-runtime/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8009 --reload`
Expected: Server starts without errors

Visit: http://localhost:8009/import
Expected: 500 error (template doesn't exist yet - expected)

**Step 7: Commit**

```bash
git add main.py
git commit -m "feat: add API routes for Google Sheets import"
```

---

## Task 9: Create Import Template

**Files:**
- Create: `templates/import.html`

**Step 1: Create import.html template**

Create `templates/import.html`:
```html
{% extends "base.html" %}

{% block content %}
<div class="container mt-4">
    <h2>Import from Google Sheets</h2>
    <p class="text-muted">Upload an Excel file (.xlsx) exported from Google Sheets to import budget and transaction data.</p>

    <!-- Step 1: Upload File -->
    <div class="card mb-4">
        <div class="card-header">
            <strong>Step 1:</strong> Upload Excel File
        </div>
        <div class="card-body">
            <form id="upload-form">
                <div class="mb-3">
                    <label for="file-input" class="form-label">Excel File (.xlsx)</label>
                    <input type="file" class="form-control" id="file-input" accept=".xlsx" required>
                    <div class="form-text">Export your Google Sheet as .xlsx (File → Download → Microsoft Excel)</div>
                </div>
                <div class="mb-3">
                    <label for="year-input" class="form-label">Year</label>
                    <input type="number" class="form-control" id="year-input"
                           min="2000" max="2100" value="{{ current_year }}" required style="max-width: 150px;">
                    <div class="form-text">The year this data belongs to</div>
                </div>
                <button type="submit" class="btn btn-primary" id="parse-btn">
                    <span class="spinner-border spinner-border-sm d-none" id="parse-spinner"></span>
                    Parse File
                </button>
            </form>
        </div>
    </div>

    <!-- Step 2: Category Mapping (hidden until file parsed) -->
    <div class="card mb-4 d-none" id="mapping-section">
        <div class="card-header">
            <strong>Step 2:</strong> Map Categories
        </div>
        <div class="card-body">
            <p class="text-muted">Map each Google Sheets category to a Moneybags category.</p>
            <div id="mapping-container"></div>
            <button type="button" class="btn btn-primary mt-3" id="validate-btn">
                <span class="spinner-border spinner-border-sm d-none" id="validate-spinner"></span>
                Validate Import
            </button>
        </div>
    </div>

    <!-- Step 3: Preview & Import (hidden until validated) -->
    <div class="card mb-4 d-none" id="preview-section">
        <div class="card-header">
            <strong>Step 3:</strong> Preview & Import
        </div>
        <div class="card-body">
            <div id="validation-results"></div>
            <button type="button" class="btn btn-success mt-3 d-none" id="import-btn">
                <span class="spinner-border spinner-border-sm d-none" id="import-spinner"></span>
                Import Data
            </button>
        </div>
    </div>
</div>

<script>
    // Set current year
    const currentYear = new Date().getFullYear();
    document.getElementById('year-input').value = currentYear;
</script>
{% endblock %}
```

**Step 2: Update import route to pass current year**

Modify `main.py` import page route:
```python
@app.get("/import", response_class=HTMLResponse)
def import_page(request: Request):
    """Import from Google Sheets Excel files"""
    from datetime import datetime
    return templates.TemplateResponse("import.html", {
        "request": request,
        "current_year": datetime.now().year
    })
```

**Step 3: Test template renders**

Run: `source /home/xivind/code/moneybags-runtime/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8009 --reload`
Visit: http://localhost:8009/import
Expected: Page renders with upload form

**Step 4: Commit**

```bash
git add templates/import.html main.py
git commit -m "feat: add import page template"
```

---

## Task 10: Add JavaScript for Import Workflow

**Files:**
- Modify: `static/js/app.js`

**Step 1: Add import page JavaScript**

Add to `static/js/app.js` at the end:
```javascript
// ==================== IMPORT PAGE ====================

// Global state for import workflow
let parsedData = null;
let categoryMapping = {};
let existingCategories = [];

// Initialize import page
async function initImportPage() {
    if (!document.getElementById('upload-form')) return;

    // Load existing categories for mapping dropdowns
    try {
        const response = await fetch('/api/categories');
        const result = await response.json();
        if (result.success) {
            existingCategories = result.data;
        }
    } catch (error) {
        console.error('Failed to load categories:', error);
    }

    // Attach event handlers
    document.getElementById('upload-form').addEventListener('submit', handleFileUpload);

    const validateBtn = document.getElementById('validate-btn');
    if (validateBtn) {
        validateBtn.addEventListener('click', handleValidate);
    }

    const importBtn = document.getElementById('import-btn');
    if (importBtn) {
        importBtn.addEventListener('click', handleImport);
    }
}

async function handleFileUpload(e) {
    e.preventDefault();

    const fileInput = document.getElementById('file-input');
    const yearInput = document.getElementById('year-input');
    const parseBtn = document.getElementById('parse-btn');
    const spinner = document.getElementById('parse-spinner');

    if (!fileInput.files[0]) {
        showToast('Please select a file', 'danger');
        return;
    }

    // Show loading
    parseBtn.disabled = true;
    spinner.classList.remove('d-none');

    try {
        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        formData.append('year', yearInput.value);

        const response = await fetch('/api/import/parse', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (result.success) {
            parsedData = result.data;
            showCategoryMapping(result.data.sheet_categories);
        } else {
            showToast(result.error, 'danger');
        }
    } catch (error) {
        showToast('Error parsing file: ' + error.message, 'danger');
    } finally {
        parseBtn.disabled = false;
        spinner.classList.add('d-none');
    }
}

function showCategoryMapping(sheetCategories) {
    const container = document.getElementById('mapping-container');
    container.innerHTML = '';

    sheetCategories.forEach(cat => {
        const row = document.createElement('div');
        row.className = 'row mb-2 align-items-center';
        row.innerHTML = `
            <div class="col-md-4">
                <strong>${cat.name}</strong>
                <span class="badge bg-${cat.type === 'income' ? 'success' : 'warning'}">${cat.type}</span>
            </div>
            <div class="col-md-1 text-center">→</div>
            <div class="col-md-7">
                <select class="form-select category-mapping" data-sheet-category="${cat.name}" data-type="${cat.type}">
                    <option value="">-- Select Moneybags Category --</option>
                    ${existingCategories
                        .filter(c => c.type === cat.type)
                        .map(c => `<option value="${c.id}">${c.name}</option>`)
                        .join('')}
                </select>
            </div>
        `;
        container.appendChild(row);
    });

    document.getElementById('mapping-section').classList.remove('d-none');
}

async function handleValidate() {
    // Collect category mapping
    categoryMapping = {};
    const selects = document.querySelectorAll('.category-mapping');
    let allMapped = true;

    selects.forEach(select => {
        const sheetCategory = select.dataset.sheetCategory;
        const moneybagsId = select.value;
        if (!moneybagsId) {
            allMapped = false;
        } else {
            categoryMapping[sheetCategory] = moneybagsId;
        }
    });

    if (!allMapped) {
        showToast('Please map all categories', 'danger');
        return;
    }

    // Show loading
    const validateBtn = document.getElementById('validate-btn');
    const spinner = document.getElementById('validate-spinner');
    validateBtn.disabled = true;
    spinner.classList.remove('d-none');

    try {
        const response = await fetch('/api/import/validate', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                parsed_data: parsedData,
                category_mapping: categoryMapping
            })
        });

        const result = await response.json();

        if (result.success) {
            showValidationResults(result.data);
        } else {
            showToast(result.error, 'danger');
        }
    } catch (error) {
        showToast('Error validating import: ' + error.message, 'danger');
    } finally {
        validateBtn.disabled = false;
        spinner.classList.add('d-none');
    }
}

function showValidationResults(validationData) {
    const container = document.getElementById('validation-results');
    const importBtn = document.getElementById('import-btn');

    let html = '';

    // Show errors
    if (validationData.errors && validationData.errors.length > 0) {
        html += '<div class="alert alert-danger"><strong>❌ Errors (must fix):</strong><ul class="mb-0">';
        validationData.errors.forEach(error => {
            html += `<li>${error}</li>`;
        });
        html += '</ul></div>';
    }

    // Show warnings
    if (validationData.warnings && validationData.warnings.length > 0) {
        html += '<div class="alert alert-warning"><strong>⚠️ Warnings:</strong><ul class="mb-0">';
        validationData.warnings.forEach(warning => {
            html += `<li>${warning}</li>`;
        });
        html += '</ul></div>';
    }

    // Show summary
    if (validationData.valid) {
        html += `
            <div class="alert alert-success">
                <strong>✅ Validation Passed</strong>
                <p class="mb-0 mt-2">Ready to import:</p>
                <ul class="mb-0">
                    <li>${validationData.summary.budget_count} budget entries</li>
                    <li>${validationData.summary.transaction_count} transactions</li>
                </ul>
            </div>
        `;
        importBtn.classList.remove('d-none');
    } else {
        html += '<p class="text-danger mt-2">Fix errors before importing.</p>';
        importBtn.classList.add('d-none');
    }

    container.innerHTML = html;
    document.getElementById('preview-section').classList.remove('d-none');
}

async function handleImport() {
    const importBtn = document.getElementById('import-btn');
    const spinner = document.getElementById('import-spinner');

    if (!confirm('Are you sure you want to import this data? This will create budget entries and transactions.')) {
        return;
    }

    importBtn.disabled = true;
    spinner.classList.remove('d-none');

    try {
        const response = await fetch('/api/import/execute', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                parsed_data: parsedData,
                category_mapping: categoryMapping
            })
        });

        const result = await response.json();

        if (result.success) {
            showToast(`Successfully imported ${result.data.budget_count} budget entries and ${result.data.transaction_count} transactions!`, 'success');

            // Reset form after 2 seconds
            setTimeout(() => {
                location.reload();
            }, 2000);
        } else {
            showToast(result.error, 'danger');
            importBtn.disabled = false;
        }
    } catch (error) {
        showToast('Error executing import: ' + error.message, 'danger');
        importBtn.disabled = false;
    } finally {
        spinner.classList.add('d-none');
    }
}

// Call init on page load
document.addEventListener('DOMContentLoaded', function() {
    // ... existing init code ...
    initImportPage();
});
```

**Step 2: Test JavaScript workflow**

Run: `source /home/xivind/code/moneybags-runtime/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8009 --reload`
Visit: http://localhost:8009/import
Test: Upload test.xlsx file, verify parsing works
Expected: Category mapping section appears

**Step 3: Commit**

```bash
git add static/js/app.js
git commit -m "feat: add JavaScript for import workflow"
```

---

## Task 11: Add Navigation Link

**Files:**
- Modify: `templates/base.html`

**Step 1: Add import link to navigation**

Find the navbar in `templates/base.html` and add after the "Config" link:
```html
<li class="nav-item">
    <a class="nav-link" href="/import">Import</a>
</li>
```

**Step 2: Test navigation**

Visit: http://localhost:8009
Expected: "Import" link appears in navigation
Click: Import link
Expected: Import page loads

**Step 3: Commit**

```bash
git add templates/base.html
git commit -m "feat: add import link to navigation"
```

---

## Task 12: Run All Tests

**Files:**
- None (testing only)

**Step 1: Run all unit tests**

Run: `source /home/xivind/code/moneybags-runtime/bin/activate && pytest tests/ -v`
Expected: All tests pass

**Step 2: Fix any failing tests**

If tests fail, debug and fix issues.

**Step 3: Commit if fixes were needed**

```bash
git add <fixed-files>
git commit -m "fix: resolve test failures"
```

---

## Task 13: Manual Integration Testing

**Files:**
- None (testing only)

**Step 1: Start application**

Run: `source /home/xivind/code/moneybags-runtime/bin/activate && uvicorn main:app --host 0.0.0.0 --port 8009 --reload`

**Step 2: Test full import workflow**

1. Visit http://localhost:8009/import
2. Upload `/home/xivind/code/moneybags/test.xlsx`
3. Set year to 2024
4. Click "Parse File"
5. Verify categories appear
6. Map all categories to existing Moneybags categories
7. Click "Validate Import"
8. Verify validation passes with counts
9. Click "Import Data"
10. Verify success toast appears
11. Navigate to Budget page
12. Verify budget entries imported
13. Verify transactions imported with "Import - Google Sheets" payee

**Step 3: Test error cases**

1. Upload non-.xlsx file → Should show error
2. Upload .xlsx but don't map all categories → Should show validation error
3. Map category to wrong type → Should show type mismatch error

**Step 4: Document any issues**

Create GitHub issue or fix immediately if critical.

---

## Task 14: Final Cleanup and Documentation

**Files:**
- Modify: `CLAUDE.md`

**Step 1: Update CLAUDE.md with import feature**

Add to "What's implemented" section in CLAUDE.md:
```markdown
- ✅ Google Sheets import (Excel .xlsx parsing with formula extraction)
```

**Step 2: Remove test.xlsx from repo**

Run: `git rm test.xlsx`

Note: test.xlsx should be in .gitignore to prevent accidental commits of user data.

**Step 3: Final commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md with import feature"
```

---

## Completion Checklist

✅ Dependencies added (openpyxl)
✅ Database functions (get_payee_by_name, create_or_update_budget_entry)
✅ Formula parsing helper (_extract_amounts_from_formula)
✅ Excel parsing (parse_excel_file)
✅ Import payee helper (_ensure_import_payee)
✅ Validation function (validate_import)
✅ Import execution (import_budget_and_transactions)
✅ API routes (parse, validate, execute)
✅ Import template (import.html)
✅ JavaScript workflow (app.js)
✅ Navigation link
✅ All tests passing
✅ Manual integration testing complete
✅ Documentation updated

**Ready for production! 🎉**
