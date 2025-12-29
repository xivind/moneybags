# Google Sheets Import Feature Design

**Date:** 2025-12-29
**Status:** Approved for Implementation

## Overview

Import budget and actual transaction data from Google Sheets Excel exports into Moneybags. Parse formulas to extract individual transaction amounts while maintaining data integrity and following Moneybags architectural constraints.

## Problem Statement

User has historical budget data in Google Sheets with:
- Categories as rows, months as columns
- Budget values in one row, actual values (as formulas) in another row
- Formulas like `=495+8289+5627` representing individual transactions
- Need to import both budget entries and individual transactions into Moneybags

## Solution Design

### Architecture

**Clean separation following CLAUDE.md constraints:**
- `main.py` - Router only (file upload, JSON responses)
- `business_logic.py` - All parsing, validation, data preparation
- `database_manager.py` - Pure CRUD operations
- `templates/import.html` - Structure only
- `static/js/app.js` - All JavaScript
- `static/css/custom.css` - All CSS

### User Workflow

1. **Upload** - Select `.xlsx` file, specify year
2. **Parse** - Extract categories, budget values, formula components
3. **Map** - User maps Google Sheet categories to Moneybags categories
4. **Validate** - Dry-run checks for errors/warnings (no DB writes)
5. **Import** - Create BudgetEntry and Transaction records atomically

### Data Flow

```
Excel File (.xlsx)
    ↓
parse_excel_file() → Extract formulas with openpyxl
    ↓
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
    ↓
validate_import() → Check categories, duplicates (READ-ONLY)
    ↓
import_budget_and_transactions() → Create records (@with_transaction)
```

## Implementation Details

### Excel File Structure

Expected Google Sheets export format:
```
Row 3:  Headers ("Balanse", "Januar", "Februar", ..., "Desember")
Row 7:  "Inntekter" section header
Row 8+: Income categories (4-row blocks)
Row 16: "Utgifter" section header
Row 17+: Expense categories (4-row blocks)

Category block (every 4 rows):
  Row N:   Category name (e.g., "Lønn")
  Row N+1: "Budsjett" with budget amounts
  Row N+2: "Resultat" with formulas (actuals)
  Row N+3: "Differanse" (skip)
```

### Formula Parsing

**Strict validation - only simple addition formulas:**

✅ Accepted:
- `=575+2182` → [575, 2182]
- `=104571` → [104571]
- `55615.0` → [55615]
- `0` → [0]
- `""` → [] (skip empty)

❌ Rejected (raise ValueError):
- `=IF(...)` → "Row 14, Column C: Complex formula not supported (IF)"
- `=SUM(...)` → "Row 14, Column C: Complex formula not supported (SUM)"
- `=-500` → "Row 14, Column C: Negative value not allowed"
- `=43*2` → "Row 14, Column C: Only addition (+) supported"

### API Endpoints

**main.py:**
```
GET  /import                - Render import page
POST /api/import/parse      - Parse Excel file, return data structure
POST /api/import/validate   - Dry-run validation (no DB writes)
POST /api/import/execute    - Create records atomically
```

### Business Logic Functions

**business_logic.py:**

```python
def parse_excel_file(file_path: str, year: int) -> dict
    # Parse .xlsx using openpyxl
    # Extract budget values and formula components
    # Validate: only simple addition, no negatives
    # Detect income vs expenses sections
    # Return structured data

def validate_import(parsed_data: dict, category_mapping: dict) -> dict
    # Verify all categories exist and types match
    # Check for duplicate BudgetEntries
    # Check for duplicate Transactions
    # Return {valid, errors, warnings, summary}
    # NO DATABASE WRITES

def import_budget_and_transactions(parsed_data: dict, category_mapping: dict) -> dict
    # Get/create "Import - Google Sheets" payee
    # Create BudgetEntry records (one per category/month)
    # Create Transaction records (one per formula component)
    # Set transaction date = year-month-01
    # Return {budget_count, transaction_count}
    # Uses @with_transaction (all-or-nothing)

def _ensure_import_payee() -> str
    # Get or create "Import - Google Sheets" payee
    # Return payee UUID

def _extract_amounts_from_formula(cell_value, row_num: int, col_name: str) -> list[int]
    # Parse formula string
    # Validate: only addition, no complex functions
    # Reject negative values
    # Return list of integers
```

### Database Manager Functions

**database_manager.py:**

Reuse existing:
- `get_category_by_id()`
- `create_transaction()`
- `create_payee()`

Add new:
```python
def get_payee_by_name(name: str) -> Optional[Payee]
    # Get payee by exact name match
    # @with_retry decorator

def create_or_update_budget_entry(data: dict) -> BudgetEntry
    # Check if BudgetEntry exists by (category_id, year, month)
    # If exists: update amount, comment, updated_at
    # If not: create new entry
    # @with_transaction decorator
```

### Frontend UI

**templates/import.html:**
- Step 1: File upload + year selection
- Step 2: Category mapping dropdowns (Google → Moneybags)
- Step 3: Validation results (errors/warnings)
- Step 4: Import button (enabled only if validation passes)

**static/js/app.js:**
- `initImportPage()` - Load existing categories
- `handleFileUpload()` - POST to /api/import/parse
- `showCategoryMapping()` - Build dropdowns dynamically
- `handleValidate()` - POST to /api/import/validate
- `showValidationResults()` - Display errors/warnings/summary
- `handleImport()` - POST to /api/import/execute with confirmation

All CSS in `static/css/custom.css`, all JavaScript in `static/js/app.js` (no inline code).

## Data Integrity

**Validation Checks:**
1. All mapped categories exist in Moneybags
2. Category types match (income → income, expenses → expenses)
3. Year is valid (2000-2100)
4. No negative amounts
5. Only simple addition formulas
6. Warn on duplicate BudgetEntries (will overwrite)
7. Warn on duplicate Transactions (same category/date/amount)

**Transaction Safety:**
- All imports wrapped with `@with_transaction` decorator
- Atomic operation (all-or-nothing)
- Automatic rollback on errors
- Retry logic for transient failures

**Payee Marking:**
- All imported transactions tagged with "Import - Google Sheets" payee
- User can easily identify and review imported data
- Payee created automatically if doesn't exist

## Edge Cases

| Case | Behavior |
|------|----------|
| Empty cell in "Resultat" row | Skip that month (no transactions) |
| Row with only empty cells | Skip entire row |
| Formula `=IF(...)` or `=SUM(...)` | Reject with detailed error message |
| Negative value in formula | Reject with error (Row X, Column Y) |
| Zero value `0` | Import (valid transaction) |
| NULL/empty cell | Skip (no transaction) |
| Category not mapped | Validation error before import |
| Duplicate BudgetEntry exists | Warning shown, will overwrite on import |
| Duplicate Transaction exists | Warning shown, will create duplicate |
| File upload fails | Show error toast, no DB changes |
| Validation fails | Disable import button, show errors |

## Testing Strategy

**Unit Tests:**
- `test_extract_amounts_from_formula()` - All accepted/rejected formats
- `test_parse_excel_file()` - Various Excel structures
- `test_validate_import()` - All validation scenarios
- `test_ensure_import_payee()` - Create and get existing

**Integration Tests:**
- Full import workflow (upload → parse → map → validate → import)
- Error handling (invalid file, unmapped categories)
- Transaction atomicity (rollback on failure)

**Manual Testing:**
- Test with actual Google Sheets export
- Verify budget entries created correctly
- Verify transactions created with correct dates
- Verify payee assignment
- Test duplicate detection warnings

## Dependencies

**New Python Packages:**
```
openpyxl==3.1.5       # Excel file parsing
et-xmlfile==2.0.0     # Required by openpyxl
```

**No Database Changes:**
- Reuses existing tables (BudgetEntry, Transaction, Payee)
- No schema migrations needed

## Deployment

1. Add dependencies to `requirements.txt`
2. Install in venv: `pip install openpyxl`
3. Add import link to navigation (templates/base.html)
4. Test with sample Excel file
5. Deploy to Docker (requirements.txt auto-installed)

## Success Criteria

✅ User uploads .xlsx file exported from Google Sheets
✅ System extracts budget totals and individual transaction amounts from formulas
✅ User maps Google Sheet categories to Moneybags categories
✅ Validation catches errors before any DB writes
✅ Import creates BudgetEntry and Transaction records atomically
✅ All imported transactions marked with "Import - Google Sheets" payee
✅ Follows clean architecture (router → business_logic → database_manager)
✅ All JavaScript in app.js, all CSS in custom.css (no inline code)
✅ Comprehensive error messages for debugging

## Future Enhancements

- Support for multiple sheets per file
- Custom date assignment (not just first of month)
- Batch import (multiple files at once)
- Import history tracking (audit log)
- CSV export/import for migration
- Undo/rollback imported data
