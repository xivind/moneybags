# Dashboard Widgets Design

**Date:** 2025-12-29
**Status:** Ready for Implementation

## Overview

Implement the first two dashboard widgets using a card/tile layout that supports future expansion to 4-6 widgets total.

## Widgets to Implement

### 1. Recurring Payments Tracker
Helps users track regular payments by identifying payees that appeared in the previous two months and showing whether they've been paid in the current month.

### 2. Recent Transactions
Shows the last 5 transactions for quick activity overview.

## Layout Structure

**Grid System:**
- 3-column Bootstrap grid layout (`col-lg-4`)
- Responsive: 3 columns on desktop, stacks on mobile
- Equal height cards using `h-100`
- Consistent spacing with `g-3`

**Expandability:**
- Easy to add widgets 3-6 by adding more `col-lg-4` divs
- Grid auto-wraps to second row when needed

**Current placeholder cards removal:**
Replace existing static "Income/Expenses/Balance" cards with new widget grid.

## Widget 1: Recurring Payments Tracker

### Business Logic (business_logic.py)

**Function:** `get_recurring_payment_status()`

**Algorithm:**
1. Calculate current month/year, previous month (month-1), and 2-months-ago (month-2)
2. Query transactions for these 3 months from Transaction table
3. Join with Payee table to get payee names
4. Group transactions by payee_id
5. Filter: keep only payees that appear in BOTH month-1 AND month-2
6. For each qualifying payee, check if transaction exists in current month
7. Return sorted list: pending first, then paid (alphabetical within each status)

**Return format:**
```python
[
    {
        'payee_id': str,           # UUID
        'payee_name': str,         # Payee name
        'status': str,             # 'paid' | 'pending'
        'last_payment_date': str,  # YYYY-MM-DD
        'last_amount': int         # Most recent transaction amount
    }
]
```

**Data source:**
- Transaction table (existing)
- Payee table (existing)
- Uses existing database_manager query patterns

### Display (templates/dashboard.html)

**Card structure:**
```html
<div class="card h-100">
  <div class="card-body">
    <h5 class="card-title">
      <i class="bi bi-arrow-repeat me-2"></i>Recurring Payments
    </h5>
    <!-- List of payees with status badges -->
  </div>
</div>
```

**Status indicators:**
- Green badge + checkmark icon: "Paid this month"
- Red/warning badge + alert icon: "Not paid yet"
- Display: payee name, status badge, last payment date, amount

**Empty state:**
If no recurring payees detected, show friendly message: "No recurring payments detected yet. Transactions will appear here once you have payees appearing in consecutive months."

## Widget 2: Recent Transactions

### Business Logic (business_logic.py)

**Function:** `get_recent_transactions(limit=5)`

**Algorithm:**
1. Query Transaction table ordered by transaction_date DESC
2. Join with Payee and Category tables to get names
3. Limit to 5 most recent
4. Return transaction details

**Return format:**
```python
[
    {
        'transaction_id': str,
        'transaction_date': str,   # YYYY-MM-DD
        'payee_name': str,
        'category_name': str,
        'amount': int,
        'category_type': str       # 'income' | 'expense'
    }
]
```

### Display (templates/dashboard.html)

**Card structure:**
```html
<div class="card h-100">
  <div class="card-body">
    <h5 class="card-title">
      <i class="bi bi-clock-history me-2"></i>Recent Transactions
    </h5>
    <!-- List of transactions -->
  </div>
</div>
```

**Transaction display:**
- Compact list format
- Show: date, payee name, category, amount
- Color coding: green for income, red for expenses
- Format amounts using existing currency helper
- Sorted by date descending (newest first)

**Empty state:**
"No transactions yet. Start by entering budget and actual values in the Budget & Actuals page."

## API Endpoints (main.py)

### GET `/api/dashboard/recurring-payments`
Returns recurring payment status for current month.

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "payee_id": "uuid",
      "payee_name": "Electric Company",
      "status": "pending",
      "last_payment_date": "2025-11-15",
      "last_amount": 150000
    }
  ]
}
```

### GET `/api/dashboard/recent-transactions`
Returns last 5 transactions.

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "transaction_id": "uuid",
      "transaction_date": "2025-12-28",
      "payee_name": "Grocery Store",
      "category_name": "Food",
      "amount": 50000,
      "category_type": "expense"
    }
  ]
}
```

## Frontend Loading (static/js/app.js)

**On dashboard page load:**
1. Check if on dashboard page (`window.location.pathname === '/'`)
2. Fetch both endpoints in parallel
3. Render widget content dynamically
4. Handle errors gracefully with toast notifications

**No auto-refresh needed:** Dashboard shows snapshot at page load. User can refresh browser to update.

## Implementation Notes

**Architecture:**
- Follow existing patterns: main.py → business_logic.py → database_manager.py
- All calculations in backend (business_logic.py)
- Frontend just renders the data
- No inline styles or scripts (use static/css/custom.css and static/js/app.js)

**Error handling:**
- Backend: raise ValueError with descriptive messages
- Frontend: show toast notification on API errors
- Empty states for no data scenarios

**Currency formatting:**
- Reuse existing currency display patterns from Budget & Actuals
- Format amounts according to user's currency preference

**Testing:**
- Add tests for new business_logic functions
- Test edge cases: no transactions, partial data, month boundaries

## Future Expansion

When adding widgets 3-6:
1. Add new `col-lg-4` div in dashboard.html grid
2. Create backend function in business_logic.py
3. Add API endpoint in main.py
4. Add fetch/render logic in app.js
5. Style as needed in custom.css

Established patterns make this straightforward.
