# Import Functionality Refactoring Design

**Date:** 2025-12-30
**Status:** Approved for implementation
**Goal:** Move seldom-used import functionality into separate Python and JavaScript modules

## Problem Statement

Import functionality (~500 lines Python, ~380 lines JavaScript) is embedded in core modules (business_logic.py, app.js) but only used on one page. This adds unnecessary size to core modules and couples seldom-used code with frequently-used code.

## Solution Overview

Extract import functionality into dedicated modules:
- **import_logic.py** - All Excel parsing, validation, and import execution
- **static/js/import.js** - Import page UI and workflow
- **main.py** - Keep API routes, change function calls to import_logic
- **templates/import.html** - Load both app.js (shared) and import.js (page-specific)

## Architecture Decisions

### 1. API Routes: Keep in main.py ✓
**Rationale:** Simple approach - all routes in one place. Import routes are just 3 endpoints calling the new import module.

### 2. JavaScript: Separate file (static/js/import.js) ✓
**Rationale:** Clean separation - only loaded on import page. Reduces main app.js size by ~380 lines. Easier to maintain import-specific code.

### 3. Python: Single module (import_logic.py) ✓
**Rationale:** All import logic in one file (~500 lines). Simple and sufficient. Mirrors business_logic.py pattern.

### 4. Helper Function: Move to import_logic.py ✓
**Rationale:** `_extract_amounts_from_formula()` is import-specific. Should live with import code. Reduces business_logic.py by ~80 lines.

## File Structure

```
/home/xivind/code/moneybags/
├── import_logic.py          # NEW - All import business logic (~500 lines)
├── business_logic.py        # MODIFIED - Remove import functions (-580 lines)
├── main.py                  # MODIFIED - Import routes call import_logic
├── static/
│   └── js/
│       ├── app.js           # MODIFIED - Remove import section (-380 lines)
│       └── import.js        # NEW - All import page JavaScript
└── templates/
    └── import.html          # MODIFIED - Load import.js
```

## Detailed Design

### import_logic.py Structure

```python
# ==================== HELPER FUNCTIONS ====================
def _extract_amounts_from_formula(cell_value, row_num: int, col_name: str) -> list[int]:
    """Extract amounts from Excel formulas"""

def _ensure_import_payee() -> str:
    """Ensure 'Import' payee exists"""

# ==================== EXCEL PARSING ====================
def parse_excel_file(file_path: str, year: int) -> dict:
    """Main entry point - detects format and delegates"""

def _parse_hovedark_format(wb, year: int) -> dict:
    """Parse 'Hovedark' Excel format"""

def _parse_original_format(wb, year: int) -> dict:
    """Parse original Excel format"""

# ==================== VALIDATION & EXECUTION ====================
def validate_import(parsed_data: dict, category_mapping: dict) -> dict:
    """Validate import data before execution"""

def import_budget_and_transactions(parsed_data: dict, category_mapping: dict) -> dict:
    """Execute import - create records"""
```

**Imports:**
```python
import logging
from datetime import datetime
from typing import Optional
from openpyxl import load_workbook
from openpyxl.utils import get_column_letter

from utils import generate_uid, empty_to_none, validate_month, validate_year
import database_manager as db
```

**Architectural principles maintained:**
- No direct database calls - uses database_manager for CRUD
- Transaction wrapping via db manager's transaction support
- UUID generation via utils.generate_uid()
- Validation-first workflow: parse → validate → execute

### static/js/import.js Structure

```javascript
// ==================== GLOBAL STATE ====================
let parsedData = null;
let categoryMapping = {};
let existingCategories = [];

// ==================== INITIALIZATION ====================
async function initImportPage()

// ==================== FILE UPLOAD & PARSING ====================
async function handleFileUpload(event)

// ==================== VALIDATION ====================
async function validateImport()
function renderValidationResults(validation)

// ==================== IMPORT EXECUTION ====================
async function handleImport()

// ==================== AUTO-INITIALIZATION ====================
if (document.getElementById('upload-form')) {
    initImportPage();
}
```

**Dependencies on app.js (shared utilities):**
- `showToast(message, type)` - Toast notifications
- `showSuccessModal(title, message)` - Success modal
- `confirmModal` - Confirmation dialog element
- `currentYear` - Global year variable

### API Routes Changes (main.py)

```python
# Add import at top
import import_logic

# Update function calls in 3 endpoints:
# /api/import/parse
business_logic.parse_excel_file(...) → import_logic.parse_excel_file(...)

# /api/import/validate
business_logic.validate_import(...) → import_logic.validate_import(...)

# /api/import/execute
business_logic.import_budget_and_transactions(...) → import_logic.import_budget_and_transactions(...)
```

**No other changes:**
- Route paths stay the same
- Request/response formats unchanged
- Error handling logic unchanged

### Template Changes (import.html)

```html
<!-- Add second script tag -->
<script src="/static/js/app.js"></script>
<script src="/static/js/import.js"></script>
```

## Migration Strategy

**Safe, incremental steps:**

1. Create import_logic.py - Copy functions from business_logic.py
2. Create static/js/import.js - Copy import section from app.js
3. Update imports in import_logic.py - Ensure dependencies work
4. Update main.py - Add import, change function calls
5. Update templates/import.html - Add import.js script tag
6. Update tests - Change imports to use import_logic
7. Run tests - Verify all 34 tests still pass
8. Test import page manually - Upload, validate, execute
9. Remove old code - Delete from business_logic.py and app.js
10. Final test run - Confirm everything works

**Rollback safety:**
- Git commit after each major step
- Old code stays until new code verified
- Can revert easily if issues arise

## Testing Requirements

**Test updates:**
```python
# tests/test_business_logic.py
# BEFORE: from business_logic import parse_excel_file, validate_import, ...
# AFTER: from import_logic import parse_excel_file, validate_import, ...
```

**Manual testing checklist:**
- [ ] Upload Excel file (Hovedark format)
- [ ] Upload Excel file (original format)
- [ ] Category mapping UI displays correctly
- [ ] Validation shows errors/warnings/summary
- [ ] Import button enabled only when valid
- [ ] Import executes successfully
- [ ] Success modal shows correct counts
- [ ] Error handling works (invalid files, validation failures)

**Automated testing:**
- [ ] All 34 existing tests pass
- [ ] Import-specific tests use import_logic module

## Benefits

**Immediate:**
1. Reduced file sizes:
   - business_logic.py: 2144 → 1564 lines (-580 lines, -27%)
   - app.js: ~2500 → ~2120 lines (-380 lines, -15%)

2. Better performance:
   - Import page only loads import.js when needed
   - Other pages don't load 380 lines of unused code

3. Easier maintenance:
   - Import bugs/features isolated to dedicated modules
   - Clear module boundaries reduce cognitive load
   - Easier onboarding for new developers

4. Architectural clarity:
   - Seldom-used features clearly separated
   - Core modules focus on frequently-used operations

**Future extensibility:**
- Easy to add new import formats (CSV, JSON, etc.)
- Can split into sub-modules if import grows beyond ~1000 lines
- Pattern established for other seldom-used features

## Impact Analysis

**No impact on:**
- Docker deployment (same container image process)
- Database configuration (same moneybags_db_config.json)
- API contracts (same endpoints, same formats)
- Production behavior (zero functional changes)
- Database schema (no migrations needed)

**Zero risk areas:**
- Same database_manager calls
- Same data models
- Same transaction handling
- Same validation logic

## Success Criteria

1. All 34 tests pass
2. Import page works identically to current behavior
3. business_logic.py reduced by ~580 lines
4. app.js reduced by ~380 lines
5. No regressions in other pages
6. Clean git history with logical commits

## Estimated Effort

**Total time:** 1-2 hours
- File creation: 15 minutes
- Code movement: 30 minutes
- Testing: 30-45 minutes
- Cleanup: 15 minutes

## Future Considerations

If import functionality grows significantly:

**Option A:** Keep in import_logic.py (good until ~1000 lines)

**Option B:** Split into package structure:
```
import_logic/
├── __init__.py
├── excel_parser.py
├── csv_parser.py
├── validator.py
└── executor.py
```

Current decision: Start with single module, split only if needed.
