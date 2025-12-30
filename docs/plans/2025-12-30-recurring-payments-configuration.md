# Recurring Payments Widget Configuration Design

**Date:** 2025-12-30
**Status:** Approved for implementation

## Overview

Add configuration to the Recurring Payments dashboard widget, allowing users to select which expense categories to monitor for recurring payments. Maintains backward compatibility by showing all expense categories when none are selected.

## User Requirements

- **Category-level selection:** Users select which expense categories (e.g., "Bills", "Subscriptions") to monitor
- **Default behavior:** When no categories selected, show all recurring expense payments (current behavior)
- **UI pattern:** Match the year template category selection pattern (badges with close buttons + dropdown)
- **Location:** Configuration section in config.html

## Design Decisions

### 1. Storage: Configuration Table (MariaDB)

Store selected category IDs in the existing `Configuration` table:

**Key:** `recurring_payment_categories`
**Value:** JSON array of category IDs

Example:
```json
["cat-uuid-1", "cat-uuid-2", "cat-uuid-3"]
```

**Rationale:**
- User preference (not a connection setting)
- Consistent with `currency_format` storage pattern
- Easy to query and update
- No database schema changes required

### 2. Backend Changes

#### New API Endpoints

**GET `/api/config/recurring-categories`**

Returns selected category IDs for recurring payment monitoring.

Response:
```json
{
  "success": true,
  "data": {
    "category_ids": ["cat-id-1", "cat-id-2"]
  }
}
```

Empty array if no configuration exists (defaults to "monitor all").

**PUT `/api/config/recurring-categories`**

Updates selected category IDs.

Request:
```json
{
  "category_ids": ["cat-id-1", "cat-id-2"]
}
```

Response:
```json
{
  "success": true,
  "data": {
    "message": "Recurring payment categories updated"
  }
}
```

#### Business Logic Changes

**Function:** `get_recurring_payment_status(category_filter: list[str] = None)`

Add optional `category_filter` parameter:
- If `None` or empty list: Use current behavior (all expense categories)
- If provided with category IDs: Only include transactions from those categories

**Implementation approach:**
```python
def get_recurring_payment_status(category_filter: list[str] = None) -> list:
    # ... existing code to fetch transactions ...

    for t in transactions:
        if not t.payee_id:
            continue

        # Only include expense transactions (skip income)
        if t.category_id and t.category_id.type == 'income':
            continue

        # NEW: Apply category filter if provided
        if category_filter and len(category_filter) > 0:
            category_id = t.category_id.id if hasattr(t.category_id, 'id') else str(t.category_id)
            if category_id not in category_filter:
                continue  # Skip transactions not in selected categories

        # ... rest of existing logic ...
```

**API route update:**
```python
@app.get("/api/dashboard/recurring-payments")
def get_recurring_payments():
    # Load category filter from configuration
    config_value = business_logic.get_configuration_value('recurring_payment_categories')
    category_filter = json.loads(config_value) if config_value else None

    # Get recurring payments with filter
    recurring_payments = business_logic.get_recurring_payment_status(category_filter)
    return {"success": True, "data": recurring_payments}
```

### 3. Frontend UI (config.html)

**New section:** Add after Currency Settings, before Database Connection

```html
<div class="card mb-4">
    <div class="card-header">
        <h5 class="mb-0">
            <i class="bi bi-arrow-repeat me-2"></i>Recurring Payments Widget
        </h5>
    </div>
    <div class="card-body">
        <p class="text-muted mb-3">
            Select which expense categories to monitor for recurring payments on the dashboard.
        </p>

        <div class="mb-3">
            <label class="form-label">Active Categories for Recurring Payments</label>
            <div class="d-flex flex-wrap gap-2" id="recurringCategoriesBadges">
                <!-- Populated by JavaScript -->
                <span class="text-muted small">No categories selected - monitoring all expenses</span>
            </div>
        </div>

        <div class="mb-3">
            <label for="addRecurringCategory" class="form-label">Add Category</label>
            <select class="form-select" id="addRecurringCategory">
                <option value="">Select expense category to add...</option>
                <!-- Populated by JavaScript -->
            </select>
            <button type="button" class="btn btn-sm btn-primary mt-2" onclick="addRecurringCategory()">
                <i class="bi bi-plus-circle me-1"></i>Add
            </button>
        </div>

        <div class="form-text">
            <i class="bi bi-info-circle me-1"></i>
            Leave empty to monitor all expense categories automatically.
        </div>
    </div>
</div>
```

**Badge display:**
- Expense category badges (red/orange color matching budget table)
- Close button always enabled (users can remove any category)
- Show "No categories selected - monitoring all expenses" when empty

### 4. Frontend JavaScript (app.js)

**New functions:**

```javascript
// ==================== RECURRING CATEGORIES CONFIGURATION ====================

async function loadRecurringCategories() {
    try {
        const result = await apiCall('/api/config/recurring-categories', { suppressError: true });
        const selectedIds = result?.category_ids || [];

        updateRecurringCategoriesBadges(selectedIds);
        updateRecurringCategorySelect(selectedIds);
    } catch (error) {
        console.error('Failed to load recurring categories:', error);
    }
}

function updateRecurringCategoriesBadges(selectedIds) {
    const container = document.getElementById('recurringCategoriesBadges');
    if (!container) return;

    if (selectedIds.length === 0) {
        container.innerHTML = '<span class="text-muted small">No categories selected - monitoring all expenses</span>';
        return;
    }

    let html = '';
    selectedIds.forEach(catId => {
        const category = allCategories.find(c => c.id === catId);
        if (category && category.type === 'expenses') {
            html += `
                <div class="badge badge-expense d-flex align-items-center gap-2">
                    ${category.name}
                    <button type="button" class="btn-close btn-close-white btn-close-small"
                            onclick="removeRecurringCategory('${catId}')"></button>
                </div>
            `;
        }
    });

    container.innerHTML = html;
}

function updateRecurringCategorySelect(selectedIds) {
    const select = document.getElementById('addRecurringCategory');
    if (!select) return;

    select.innerHTML = '<option value="">Select expense category to add...</option>';

    // Add expense categories not yet selected
    allCategories
        .filter(c => c.type === 'expenses' && !selectedIds.includes(c.id))
        .forEach(cat => {
            select.innerHTML += `<option value="${cat.id}">${cat.name}</option>`;
        });
}

async function addRecurringCategory() {
    const select = document.getElementById('addRecurringCategory');
    const categoryId = select.value;

    if (!categoryId) {
        showErrorModal('Please select a category');
        return;
    }

    try {
        showLoading('Adding category...');

        // Get current list
        const result = await apiCall('/api/config/recurring-categories', { suppressError: true });
        const selectedIds = result?.category_ids || [];

        // Add new category
        selectedIds.push(categoryId);

        // Save
        await apiCall('/api/config/recurring-categories', {
            method: 'PUT',
            body: JSON.stringify({ category_ids: selectedIds })
        });

        await loadRecurringCategories();
        hideLoading();
        showSuccess('Category added');
    } catch (error) {
        hideLoading();
    }
}

async function removeRecurringCategory(categoryId) {
    try {
        showLoading('Removing category...');

        // Get current list
        const result = await apiCall('/api/config/recurring-categories', { suppressError: true });
        const selectedIds = result?.category_ids || [];

        // Remove category
        const newIds = selectedIds.filter(id => id !== categoryId);

        // Save
        await apiCall('/api/config/recurring-categories', {
            method: 'PUT',
            body: JSON.stringify({ category_ids: newIds })
        });

        await loadRecurringCategories();
        hideLoading();
        showSuccess('Category removed');
    } catch (error) {
        hideLoading();
    }
}
```

**Initialization update:**

Add to config page initialization:
```javascript
if (document.getElementById('categoriesTable')) {
    // ... existing initialization ...
    await loadRecurringCategories();  // NEW
    // ... rest of initialization ...
}
```

## Implementation Steps

1. **Backend - business_logic.py:**
   - Add `category_filter` parameter to `get_recurring_payment_status()`
   - Implement category filtering logic
   - Test with different filter scenarios

2. **Backend - main.py:**
   - Add GET `/api/config/recurring-categories` endpoint
   - Add PUT `/api/config/recurring-categories` endpoint
   - Update `/api/dashboard/recurring-payments` to load and apply filter
   - Add validation for category IDs

3. **Frontend - config.html:**
   - Add new Recurring Payments Widget configuration section
   - Include badge container and dropdown

4. **Frontend - app.js:**
   - Implement `loadRecurringCategories()`
   - Implement `updateRecurringCategoriesBadges()`
   - Implement `updateRecurringCategorySelect()`
   - Implement `addRecurringCategory()`
   - Implement `removeRecurringCategory()`
   - Update config page initialization

5. **Testing:**
   - Test with no categories selected (should show all)
   - Test with 1+ categories selected (should filter)
   - Test adding/removing categories
   - Test dashboard widget updates after config changes
   - Test invalid category IDs (deleted categories)

## Backward Compatibility

- **Default behavior:** When `recurring_payment_categories` config is missing or empty, show all expense categories
- **No migration needed:** Existing installations work without changes
- **Graceful degradation:** If category is deleted but still in config, skip it silently

## Edge Cases

1. **Category deleted:** If selected category is deleted, skip it when rendering badges
2. **No expense categories exist:** Dropdown shows "No expense categories available"
3. **All categories selected then one deleted:** Filter continues working with remaining categories
4. **Config value corrupted:** Fall back to empty array (monitor all)

## Success Criteria

- [ ] Users can select expense categories to monitor in config page
- [ ] Dashboard widget respects category filter
- [ ] Default behavior (monitor all) preserved when no selection
- [ ] UI matches year template pattern (badges + dropdown)
- [ ] No backend errors with missing/invalid category IDs
- [ ] Configuration persists across application restarts
