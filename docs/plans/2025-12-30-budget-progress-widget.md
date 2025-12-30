# Budget Progress Widget Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add dashboard widget showing budget vs actual spending with progress bars for current month and year.

**Architecture:** Frontend-only feature using existing `/api/budget/{year}` endpoint. Tabbed interface with progress bars, tooltips for details, green/red color coding for under/over budget.

**Tech Stack:** Bootstrap 5 (tabs, progress bars, tooltips), Vanilla JavaScript, existing API endpoints

---

## Task 1: Add CSS Styling

**Files:**
- Modify: `static/css/custom.css` (append to end of file)

**Step 1: Add CSS for budget progress widget**

Add these styles to the end of `static/css/custom.css`:

```css
/* Budget Progress Widget */
.budget-progress-list {
    max-height: 400px;
    overflow-y: auto;
    overflow-x: hidden;
}

.progress-row {
    margin-bottom: 1rem;
}

.progress-row-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.25rem;
    font-size: 0.875rem;
}

.category-name {
    font-weight: 500;
    color: #2d3748;
}

.progress-percentage {
    font-weight: 600;
    font-size: 0.875rem;
    color: #4a5568;
}

.over-budget-text {
    font-size: 0.75rem;
    color: #dc3545;
    margin-top: 0.25rem;
    font-weight: 500;
}

/* Progress bar customization */
.budget-progress-bar {
    height: 1.5rem;
}

/* Scrollbar styling */
.budget-progress-list::-webkit-scrollbar {
    width: 8px;
}

.budget-progress-list::-webkit-scrollbar-track {
    background: #f1f1f1;
    border-radius: 4px;
}

.budget-progress-list::-webkit-scrollbar-thumb {
    background: #888;
    border-radius: 4px;
}

.budget-progress-list::-webkit-scrollbar-thumb:hover {
    background: #555;
}
```

**Step 2: Verify CSS syntax**

Quick visual check - no syntax errors, proper closing braces.

**Step 3: Commit CSS changes**

```bash
git add static/css/custom.css
git commit -m "style: add budget progress widget styles"
```

---

## Task 2: Add HTML Structure to Dashboard

**Files:**
- Modify: `templates/dashboard.html:71-96` (add new widget after existing expense categories widget)

**Step 1: Add budget progress widget HTML**

After the Expense Categories widget (after line 96), add this new widget:

```html
    <!-- Budget Progress Widget -->
    <div class="col-lg-3">
        <div class="card h-100">
            <div class="card-body">
                <h5 class="card-title">
                    <i class="bi bi-speedometer me-2"></i>Budget Progress
                </h5>

                <!-- Nav tabs -->
                <ul class="nav nav-tabs mb-3" role="tablist">
                    <li class="nav-item" role="presentation">
                        <button class="nav-link active" id="month-progress-tab" data-bs-toggle="tab" data-bs-target="#month-progress" type="button" role="tab" aria-controls="month-progress" aria-selected="true">
                            This Month
                        </button>
                    </li>
                    <li class="nav-item" role="presentation">
                        <button class="nav-link" id="year-progress-tab" data-bs-toggle="tab" data-bs-target="#year-progress" type="button" role="tab" aria-controls="year-progress" aria-selected="false">
                            This Year
                        </button>
                    </li>
                </ul>

                <!-- Tab content -->
                <div class="tab-content">
                    <div class="tab-pane fade show active" id="month-progress" role="tabpanel" aria-labelledby="month-progress-tab">
                        <div class="budget-progress-list" id="month-progress-content">
                            <div class="text-center text-muted py-3">
                                <div class="spinner-border spinner-border-sm" role="status">
                                    <span class="visually-hidden">Loading...</span>
                                </div>
                                <p class="small mt-2 mb-0">Loading...</p>
                            </div>
                        </div>
                    </div>
                    <div class="tab-pane fade" id="year-progress" role="tabpanel" aria-labelledby="year-progress-tab">
                        <div class="budget-progress-list" id="year-progress-content">
                            <div class="text-center text-muted py-3">
                                <div class="spinner-border spinner-border-sm" role="status">
                                    <span class="visually-hidden">Loading...</span>
                                </div>
                                <p class="small mt-2 mb-0">Loading...</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
```

**Step 2: Verify HTML structure**

- No inline styles (all classes reference custom.css or Bootstrap)
- No inline scripts
- Proper Bootstrap tab structure
- Loading spinners in both tab panes

**Step 3: Commit HTML changes**

```bash
git add templates/dashboard.html
git commit -m "feat: add budget progress widget HTML structure"
```

---

## Task 3: Implement JavaScript - Data Processing

**Files:**
- Modify: `static/js/app.js` (add new functions before `initializeDashboard()` around line 1780)

**Step 1: Add helper function to calculate category totals**

Add this function before `initializeDashboard()`:

```javascript
function calculateCategoryTotals(budgetData, categoryId, period) {
    // period: 'month' or 'year'
    const entries = budgetData.budget_entries[categoryId] || {};
    const transactions = budgetData.transactions[categoryId] || {};

    let budgetTotal = 0;
    let actualTotal = 0;

    if (period === 'month') {
        // Current month only (currentMonth is 0-11, but API uses 1-12)
        const month = currentMonth + 1;
        const entry = entries[month];
        budgetTotal = entry ? entry.amount : 0;

        const monthTransactions = transactions[month] || [];
        actualTotal = monthTransactions.reduce((sum, t) => sum + t.amount, 0);
    } else {
        // Year total (all 12 months)
        for (let month = 1; month <= 12; month++) {
            const entry = entries[month];
            if (entry) {
                budgetTotal += entry.amount;
            }

            const monthTransactions = transactions[month] || [];
            actualTotal += monthTransactions.reduce((sum, t) => sum + t.amount, 0);
        }
    }

    return { budgetTotal, actualTotal };
}
```

**Step 2: Add function to generate progress bar HTML**

Add this function after `calculateCategoryTotals()`:

```javascript
function generateProgressBarHTML(categoryName, budgetTotal, actualTotal) {
    // Skip if no budget set
    if (budgetTotal === 0) {
        return '';
    }

    const percentage = Math.min((actualTotal / budgetTotal) * 100, 100);
    const isOverBudget = actualTotal >= budgetTotal;
    const barColor = isOverBudget ? 'bg-danger' : 'bg-success';
    const percentageText = Math.round((actualTotal / budgetTotal) * 100);
    const overAmount = actualTotal - budgetTotal;

    // Tooltip content
    const tooltipContent = `Budget: ${formatCurrency(budgetTotal)} | Actual: ${formatCurrency(actualTotal)}`;

    let html = `
        <div class="progress-row" data-bs-toggle="tooltip" data-bs-placement="top" title="${tooltipContent}">
            <div class="progress-row-header">
                <span class="category-name">${categoryName}</span>
                <span class="progress-percentage">${percentageText}%</span>
            </div>
            <div class="progress budget-progress-bar">
                <div class="progress-bar ${barColor}" role="progressbar" style="width: ${percentage}%" aria-valuenow="${percentage}" aria-valuemin="0" aria-valuemax="100"></div>
            </div>`;

    if (isOverBudget) {
        html += `<div class="over-budget-text">Over by ${formatCurrency(overAmount)}</div>`;
    }

    html += `</div>`;

    return html;
}
```

**Step 3: Verify functions are correct**

- Check logic: month vs year calculations
- Check formatting: uses `formatCurrency()`
- Check Bootstrap classes: `bg-success`, `bg-danger`, `progress`, `progress-bar`

**Step 4: Commit data processing functions**

```bash
git add static/js/app.js
git commit -m "feat: add budget progress calculation functions"
```

---

## Task 4: Implement JavaScript - Main Load Function

**Files:**
- Modify: `static/js/app.js` (add `loadBudgetProgress()` function)

**Step 1: Add main load function**

Add this function after the progress bar generation functions:

```javascript
async function loadBudgetProgress() {
    const monthContainer = document.getElementById('month-progress-content');
    const yearContainer = document.getElementById('year-progress-content');

    if (!monthContainer || !yearContainer) return;

    try {
        // Fetch budget data for current year
        const data = await apiCall(`/api/budget/${currentYear}`, { suppressError: true });

        if (!data) {
            monthContainer.innerHTML = `<p class="text-muted text-center small">No budget data available</p>`;
            yearContainer.innerHTML = `<p class="text-muted text-center small">No budget data available</p>`;
            return;
        }

        // Filter expense categories only
        const expenseCategories = data.categories.filter(cat => cat.category_type === 'expense');

        // Sort alphabetically
        expenseCategories.sort((a, b) => a.category_name.localeCompare(b.category_name));

        // Generate progress bars for each period
        let monthHTML = '';
        let yearHTML = '';

        for (const category of expenseCategories) {
            const monthTotals = calculateCategoryTotals(data, category.category_id, 'month');
            const yearTotals = calculateCategoryTotals(data, category.category_id, 'year');

            const monthBar = generateProgressBarHTML(
                category.category_name,
                monthTotals.budgetTotal,
                monthTotals.actualTotal
            );

            const yearBar = generateProgressBarHTML(
                category.category_name,
                yearTotals.budgetTotal,
                yearTotals.actualTotal
            );

            monthHTML += monthBar;
            yearHTML += yearBar;
        }

        // Handle empty states
        if (!monthHTML) {
            monthHTML = `<p class="text-muted text-center small">No budget entries for this month</p>`;
        }

        if (!yearHTML) {
            yearHTML = `<p class="text-muted text-center small">No budget entries for this year</p>`;
        }

        // Update containers
        monthContainer.innerHTML = monthHTML;
        yearContainer.innerHTML = yearHTML;

        // Initialize Bootstrap tooltips
        const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));

    } catch (error) {
        console.error('Failed to load budget progress:', error);
        monthContainer.innerHTML = `<p class="text-muted text-center small">Failed to load data</p>`;
        yearContainer.innerHTML = `<p class="text-muted text-center small">Failed to load data</p>`;
    }
}
```

**Step 2: Verify load function**

- Check error handling
- Check empty state handling
- Check tooltip initialization
- Uses existing `apiCall()` wrapper

**Step 3: Commit load function**

```bash
git add static/js/app.js
git commit -m "feat: add loadBudgetProgress function"
```

---

## Task 5: Integrate into Dashboard Initialization

**Files:**
- Modify: `static/js/app.js:1780-1790` (update `initializeDashboard()` function)

**Step 1: Update initializeDashboard to include budget progress**

Find the `initializeDashboard()` function (around line 1780) and update it:

```javascript
async function initializeDashboard() {
    // Load currency format first (needed for formatting)
    await loadCurrencyFormat();

    // Load all widgets in parallel
    await Promise.all([
        loadRecurringPayments(),
        loadRecentTransactions(),
        loadExpensePieCharts(),
        loadBudgetProgress()
    ]);
}
```

**Step 2: Verify integration**

- `loadBudgetProgress()` added to Promise.all array
- Runs in parallel with other widgets
- Currency format loaded first (needed for formatting)

**Step 3: Commit integration**

```bash
git add static/js/app.js
git commit -m "feat: integrate budget progress into dashboard initialization"
```

---

## Task 6: Manual Testing

**Files:** N/A (testing only)

**Step 1: Start the application**

```bash
source /home/xivind/code/moneybags-runtime/bin/activate
cd /home/xivind/code/moneybags
uvicorn main:app --host 0.0.0.0 --port 8009 --log-config uvicorn_log_config.ini --reload
```

Expected: Application starts successfully

**Step 2: Open dashboard in browser**

Navigate to: `http://localhost:8009`

Expected:
- Four widgets visible: Recurring Payments, Recent Transactions, Expense Categories, Budget Progress
- Budget Progress widget shows two tabs: "This Month" and "This Year"
- "This Month" tab is active by default

**Step 3: Test "This Month" tab**

Expected:
- Progress bars for all expense categories with budget entries
- Green bars for under budget
- Red bars for over budget
- "Over by X" text for over-budget categories
- Percentage displayed on right side

**Step 4: Test "This Year" tab**

Click "This Year" tab

Expected:
- Tab switches successfully
- Shows year-to-date progress bars
- Same color coding as month tab
- Different totals (year vs month)

**Step 5: Test tooltips**

Hover over any progress bar row

Expected:
- Tooltip appears showing "Budget: kr X,XXX | Actual: kr X,XXX"
- Formatted with currency symbol and thousand separators
- Works on both tabs

**Step 6: Test scrolling (if many categories)**

If there are more than ~8 categories:

Expected:
- Scrollbar appears
- List scrolls smoothly
- Fixed height maintained

**Step 7: Test responsive behavior**

Resize browser window to mobile width

Expected:
- Widget stacks vertically
- Progress bars adapt to width
- Tabs still functional
- Tooltips still work

**Step 8: Test empty states**

If you have access to a year with no budget data, navigate to that year

Expected:
- Shows "No budget entries for this month/year" message
- No errors in console

**Step 9: Check browser console**

Expected:
- No JavaScript errors
- No warnings
- API calls successful

**Step 10: Verify architectural compliance**

- View page source: No inline styles in HTML ✓
- View page source: No inline scripts in HTML ✓
- All styles in custom.css ✓
- All JavaScript in app.js ✓

---

## Task 7: Final Commit

**Files:**
- All modified files already committed in previous steps

**Step 1: Review git log**

```bash
git log --oneline -7
```

Expected: Should see all commits from this implementation

**Step 2: Verify all changes committed**

```bash
git status
```

Expected: `working tree clean`

**Step 3: Optional - Create feature summary commit (if using feature branch)**

If you want a summary commit:

```bash
git commit --allow-empty -m "$(cat <<'EOF'
feat: complete budget progress widget implementation

Added dashboard widget showing budget vs actual spending with:
- Tabbed interface (This Month / This Year)
- Progress bars with green/red color coding
- Tooltips showing budget and actual amounts
- "Over by X" text for over-budget categories
- Responsive design with scrollable list
- Frontend-only changes using existing API

All architectural constraints followed:
- No inline styles or scripts
- All CSS in custom.css
- All JavaScript in app.js
- Uses existing /api/budget/{year} endpoint

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
EOF
)"
```

---

## Success Criteria Checklist

After completing all tasks, verify:

- [ ] Widget displays on dashboard alongside existing three widgets
- [ ] Two tabs: "This Month" (default) and "This Year"
- [ ] Progress bars show accurate budget vs actual comparison
- [ ] Green bars for under budget, red for over budget
- [ ] "Over by X" text appears when over budget
- [ ] Tooltips show budget and actual amounts on hover
- [ ] Scrollable list handles many categories gracefully
- [ ] Mobile responsive
- [ ] No inline styles in HTML
- [ ] No inline scripts in HTML
- [ ] All styles in static/css/custom.css
- [ ] All JavaScript in static/js/app.js
- [ ] No backend changes (uses existing API)
- [ ] Currency formatting matches existing format
- [ ] No JavaScript errors in console
- [ ] All commits follow conventional commit format

---

## Rollback Plan

If something goes wrong:

```bash
# See recent commits
git log --oneline -10

# Rollback to before this feature (adjust number as needed)
git reset --hard HEAD~7

# Or rollback to specific commit
git reset --hard <commit-hash>
```

---

## Future Enhancements (Out of Scope)

- Click category to drill down to transactions
- Filter by tags
- Show income categories separately
- Export budget progress report
- Historical comparison (vs last month/year)
- Budget adjustment suggestions
- Alert notifications for over-budget categories
