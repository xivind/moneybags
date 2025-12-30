// Moneybags Application JavaScript - Connected to Real API

// ==================== STATE ====================

const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
               'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

// Current month (0-11)
const currentMonth = new Date().getMonth();

// Current year
let currentYear = new Date().getFullYear();

// Available years (loaded from API)
let availableYears = [];

// All categories (loaded from API)
let allCategories = [];

// Budget data for current year
let budgetData = null;

// Trend data for current year (keyed by category_id)
let trendData = {};

// All payees (loaded from API)
let payees = [];

// Current currency format (loaded from API)
let currentCurrencyFormat = '';

// Current cell being edited
let currentCell = null;
let currentTransactionIndex = null;

// Tom Select instance
let payeeSelect = null;

// Tempus Dominus instance
let datePicker = null;

// ==================== API FUNCTIONS ====================

async function apiCall(url, options = {}) {
    const { suppressError = false, ...fetchOptions } = options;

    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...fetchOptions.headers
            },
            ...fetchOptions
        });

        const data = await response.json();

        // Check for server errors (500) - likely database connection issues
        if (response.status === 500) {
            const errorMsg = data.error || 'Server error occurred';

            // Database connection errors contain specific patterns
            const isDatabaseError = errorMsg.includes('Lost connection') ||
                                   errorMsg.includes('MySQL') ||
                                   errorMsg.includes('connection') ||
                                   errorMsg.includes('(0,') ||
                                   errorMsg.includes('(2013,');

            if (isDatabaseError) {
                // Show toast for database errors (less intrusive, allows retry to work)
                showToast('Database connection issue. Retrying...', 'error');
                throw new Error('Database connection error');
            }
        }

        if (!data.success) {
            throw new Error(data.error || 'API request failed');
        }

        return data.data;
    } catch (error) {
        console.error('API Error:', error);

        // Only show error modal if not suppressed and not already shown as toast
        if (!suppressError && !error.message.includes('Database connection')) {
            showError(error.message || 'Network error occurred');
        }

        throw error;
    }
}

async function loadCategories() {
    try {
        allCategories = await apiCall('/api/categories', { suppressError: true });
    } catch (error) {
        console.error('Failed to load categories:', error);
        allCategories = [];
    }
}

async function loadPayees() {
    try {
        const payeeData = await apiCall('/api/payees', { suppressError: true });
        payees = payeeData.map(p => ({
            id: p.id,
            name: p.name,
            type: p.type,
            transaction_count: p.transaction_count,
            last_used: p.last_used
        }));
    } catch (error) {
        console.error('Failed to load payees:', error);
        payees = [];
    }
}

async function loadAvailableYears() {
    try {
        availableYears = await apiCall('/api/years', { suppressError: true });
    } catch (error) {
        console.error('Failed to load available years:', error);
        availableYears = [];
    }
}

async function loadBudgetData(year) {
    budgetData = await apiCall(`/api/budget/${year}`);
}

async function loadCategoryTrends(year, categoryId) {
    try {
        const trends = await apiCall(`/api/budget/trends/${year}/${categoryId}`, { suppressError: true });
        trendData[categoryId] = trends;
    } catch (error) {
        console.error(`Failed to load trends for category ${categoryId}:`, error);
        trendData[categoryId] = null;
    }
}

async function loadAllTrends(year) {
    if (!budgetData || !budgetData.categories) return;

    // Load trends for all categories in parallel
    const trendPromises = budgetData.categories.map(cat =>
        loadCategoryTrends(year, cat.id)
    );

    await Promise.all(trendPromises);
}

function getCurrencySymbol() {
    switch (currentCurrencyFormat) {
        case 'nok':
            return 'kr';
        case 'usd':
            return '$';
        case 'eur':
            return '€';
        default:
            return '';
    }
}

function updateCurrencyLabels() {
    const symbol = getCurrencySymbol();
    const labelText = symbol ? ` (${symbol})` : '';

    // Update budget modal label
    const budgetLabel = document.querySelector('label[for="budgetAmount"]');
    if (budgetLabel) {
        budgetLabel.textContent = `Budget${labelText}`;
    }

    // Update transaction amount label
    const amountLabel = document.querySelector('label[for="transactionAmount"]');
    if (amountLabel) {
        amountLabel.textContent = `Amount${labelText}`;
    }
}

async function loadCurrencyFormat() {
    try {
        const result = await apiCall('/api/config/currency', { suppressError: true });
        if (result && result.currency_format) {
            currentCurrencyFormat = result.currency_format;
        } else {
            currentCurrencyFormat = '';
        }
        updateCurrencyLabels();
    } catch (error) {
        console.error('Failed to load currency format:', error);
        currentCurrencyFormat = '';
        updateCurrencyLabels();
    }
}

function formatCurrency(amount) {
    if (amount === null || amount === undefined || amount === '') {
        return '';
    }

    // Format number with space as thousand separator
    const formattedNumber = Number(amount).toLocaleString('en-US').replace(/,/g, ' ');

    // Apply currency symbol based on format (symbol before amount with space)
    switch (currentCurrencyFormat) {
        case 'nok':
            return `kr ${formattedNumber}`;
        case 'usd':
            return `$ ${formattedNumber}`;
        case 'eur':
            return `€ ${formattedNumber}`;
        default:
            // No currency selected - just return the number
            return formattedNumber;
    }
}

async function saveBudgetEntry(categoryId, year, month, amount, comment) {
    return await apiCall('/api/budget/entry', {
        method: 'POST',
        body: JSON.stringify({
            category_id: categoryId,
            year: year,
            month: month,
            amount: amount,
            comment: comment
        })
    });
}

async function deleteBudgetEntryApi(entryId) {
    return await apiCall(`/api/budget/entry/${entryId}`, {
        method: 'DELETE'
    });
}

async function loadTransactions(categoryId, year, month) {
    return await apiCall(`/api/transactions/${categoryId}/${year}/${month}`);
}

async function createTransaction(categoryId, date, amount, payeeId, comment) {
    return await apiCall('/api/transaction', {
        method: 'POST',
        body: JSON.stringify({
            category_id: categoryId,
            date: date,
            amount: amount,
            payee_id: payeeId || null,
            comment: comment || null
        })
    });
}

async function updateTransaction(transactionId, date, amount, payeeId, comment) {
    return await apiCall(`/api/transaction/${transactionId}`, {
        method: 'PUT',
        body: JSON.stringify({
            date: date,
            amount: amount,
            payee_id: payeeId || null,
            comment: comment || null
        })
    });
}

async function deleteTransactionApi(transactionId) {
    return await apiCall(`/api/transaction/${transactionId}`, {
        method: 'DELETE'
    });
}

async function createCategory(name, type) {
    return await apiCall('/api/category', {
        method: 'POST',
        body: JSON.stringify({ name, type })
    });
}

async function updateCategory(categoryId, name) {
    return await apiCall(`/api/category/${categoryId}`, {
        method: 'PUT',
        body: JSON.stringify({ name })
    });
}

async function deleteCategoryApi(categoryId) {
    return await apiCall(`/api/category/${categoryId}`, {
        method: 'DELETE'
    });
}

async function createPayee(name, type) {
    return await apiCall('/api/payee', {
        method: 'POST',
        body: JSON.stringify({ name, type: type || 'Actual' })
    });
}

async function updatePayee(payeeId, name, type) {
    return await apiCall(`/api/payee/${payeeId}`, {
        method: 'PUT',
        body: JSON.stringify({ name, type })
    });
}

async function deletePayeeApi(payeeId) {
    return await apiCall(`/api/payee/${payeeId}`, {
        method: 'DELETE'
    });
}

// ==================== UTILITY FUNCTIONS ====================

let currentLoadingToast = null;

function showLoading(message = 'Loading...') {
    // Show loading toast (doesn't auto-dismiss)
    currentLoadingToast = showToast(message, 'loading');
}

function hideLoading() {
    // Hide the loading toast
    if (currentLoadingToast) {
        removeToast(currentLoadingToast);
        currentLoadingToast = null;
    }
}

function showError(message) {
    // Show error modal instead of alert
    showErrorModal(message);
}

function showSuccess(message) {
    // Show success toast
    showToast(message, 'success');
}

function showToast(message, type = 'success') {
    const container = document.getElementById('toastContainer');

    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast-notification toast-${type}`;

    toast.innerHTML = `
        <p class="toast-message">${message}</p>
        <button class="toast-close" onclick="removeToast(this.parentElement)">&times;</button>
        <div class="toast-progress"></div>
    `;

    container.appendChild(toast);

    // Auto-dismiss after 3 seconds (only for success/error, not loading)
    if (type !== 'loading') {
        setTimeout(() => {
            removeToast(toast);
        }, 3000);
    }

    return toast;
}

function removeToast(toast) {
    if (!toast || !toast.parentElement) return;

    toast.classList.add('toast-removing');
    setTimeout(() => {
        if (toast.parentElement) {
            toast.parentElement.removeChild(toast);
        }
    }, 300);
}

function showErrorModal(message) {
    document.getElementById('errorModalMessage').textContent = message;
    const modal = new bootstrap.Modal(document.getElementById('errorModal'));
    modal.show();
}

function showSuccessModal(title, message) {
    document.getElementById('successModalTitle').textContent = title;
    document.getElementById('successModalMessage').innerHTML = message;
    const modal = new bootstrap.Modal(document.getElementById('successModal'));
    modal.show();
}

function showConfirmModal(title, message, confirmText = 'Confirm') {
    return new Promise((resolve) => {
        document.getElementById('confirmModalTitle').textContent = title;
        document.getElementById('confirmModalMessage').textContent = message;
        document.getElementById('confirmActionBtn').textContent = confirmText;

        const modal = new bootstrap.Modal(document.getElementById('confirmModal'));
        const confirmBtn = document.getElementById('confirmActionBtn');
        const cancelBtn = document.getElementById('confirmCancelBtn');

        // Remove any existing event listeners by cloning buttons
        const newConfirmBtn = confirmBtn.cloneNode(true);
        const newCancelBtn = cancelBtn.cloneNode(true);
        confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);
        cancelBtn.parentNode.replaceChild(newCancelBtn, cancelBtn);

        // Add new event listeners
        newConfirmBtn.addEventListener('click', () => {
            modal.hide();
            resolve(true);
        });

        newCancelBtn.addEventListener('click', () => {
            modal.hide();
            resolve(false);
        });

        // Handle modal close (X button or backdrop)
        const modalElement = document.getElementById('confirmModal');
        const handleClose = () => {
            resolve(false);
            modalElement.removeEventListener('hidden.bs.modal', handleClose);
        };
        modalElement.addEventListener('hidden.bs.modal', handleClose);

        modal.show();
    });
}

function formatDate(dateStr) {
    // Return date in yyyy-MM-dd format to match application standard
    if (!dateStr) return '';

    // If already in correct format, return as-is
    if (typeof dateStr === 'string' && /^\d{4}-\d{2}-\d{2}/.test(dateStr)) {
        return dateStr.split('T')[0]; // Remove time part if present
    }

    // Convert to yyyy-MM-dd format
    const date = new Date(dateStr);
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

function cleanupBackdrops() {
    const backdrops = document.querySelectorAll('.modal-backdrop');
    backdrops.forEach(backdrop => backdrop.remove());
    document.body.classList.remove('modal-open');
    document.body.style.removeProperty('overflow');
    document.body.style.removeProperty('padding-right');
}

function getCategoryById(categoryId) {
    return allCategories.find(c => c.id === categoryId);
}

function getPayeeById(payeeId) {
    return payees.find(p => p.id === payeeId);
}

// ==================== BUDGET TABLE FUNCTIONS ====================

async function initializeBudgetPage() {
    showLoading('Loading budget data...');

    try {
        await loadCategories();
        await loadPayees();
        await loadCurrencyFormat();
        await loadAvailableYears();
        populateYearSelector();

        // Only load budget data and generate table if we have years
        if (availableYears.length > 0) {
            await loadBudgetData(currentYear);
            await loadAllTrends(currentYear);
            generateTable();
        }

        hideLoading();
    } catch (error) {
        hideLoading();
        showError('Failed to initialize budget page');
    }
}

function populateYearSelector() {
    const selector = document.getElementById('yearSelector');
    const emptyBanner = document.getElementById('emptyStateBanner');
    const tableContainer = document.querySelector('.table-responsive');

    if (!selector) return;

    selector.innerHTML = '';

    // Check if we have any years
    if (availableYears.length === 0) {
        // Show empty state banner, hide table and year selector
        if (emptyBanner) emptyBanner.classList.remove('d-none');
        if (tableContainer) tableContainer.classList.add('d-none');
        selector.parentElement.classList.add('d-none');
        return;
    }

    // Hide empty state banner, show table and year selector
    if (emptyBanner) emptyBanner.classList.add('d-none');
    if (tableContainer) tableContainer.classList.remove('d-none');
    selector.parentElement.classList.remove('d-none');

    // Sort years in descending order (most recent on top)
    const sortedYears = [...availableYears].sort((a, b) => b - a);

    sortedYears.forEach(year => {
        const option = document.createElement('option');
        option.value = year;
        option.textContent = year;
        if (year === currentYear) {
            option.selected = true;
        }
        selector.appendChild(option);
    });
}

async function changeYear() {
    const selector = document.getElementById('yearSelector');
    currentYear = parseInt(selector.value);
    showLoading('Loading year data...');
    await loadBudgetData(currentYear);
    await loadAllTrends(currentYear);
    generateTable();
    hideLoading();
}

function generateTable() {
    const table = document.getElementById('budgetTable');
    if (!table || !budgetData) return;

    let html = '<tbody>';

    // Balance section
    html += `<tr><td colspan="${months.length + 2}" class="section-header balance-header">BALANCE</td></tr>`;
    html += generateMonthHeaderRow();
    html += generateBalanceRows();

    // Income section
    html += `<tr class="section-spacer"><td colspan="${months.length + 2}" class="section-spacer"></td></tr>`;
    html += `<tr><td colspan="${months.length + 2}" class="section-header income-header">INCOME</td></tr>`;
    html += generateMonthHeaderRow();
    html += generateSectionRows('income');

    // Expenses section
    html += `<tr class="section-spacer"><td colspan="${months.length + 2}" class="section-spacer"></td></tr>`;
    html += `<tr><td colspan="${months.length + 2}" class="section-header expense-header">EXPENSES</td></tr>`;
    html += generateMonthHeaderRow();
    html += generateSectionRows('expenses');

    html += '</tbody>';
    table.innerHTML = html;
}

function generateMonthHeaderRow() {
    let html = '<tr class="month-header-row section-tile-row"><th class="month-header-cell"></th>';
    months.forEach((month, idx) => {
        const janClass = idx === 0 ? ' jan-column' : '';
        html += `<th class="month-header-cell${janClass}">${month}</th>`;
    });
    html += '<th class="month-header-cell">Total</th></tr>';
    return html;
}

function generateBalanceRows() {
    let html = '';

    // Budget Balance row
    html += '<tr class="budget-balance-row section-tile-row"><td class="category-cell">Budget Balance</td>';
    months.forEach((month, idx) => {
        const janClass = idx === 0 ? ' jan-column' : '';
        const balance = calculateMonthlyBudgetBalance(idx);
        html += `<td class="balance-white-cell${janClass}">${formatCurrency(balance)}</td>`;
    });
    const totalBalance = months.reduce((sum, month, idx) => sum + calculateMonthlyBudgetBalance(idx), 0);
    html += `<td class="total-column balance-white-cell">${formatCurrency(totalBalance)}</td>`;
    html += '</tr>';

    // Result Balance row
    html += '<tr class="result-balance-row section-tile-row"><td class="category-cell">Result Balance</td>';
    months.forEach((month, idx) => {
        const janClass = idx === 0 ? ' jan-column' : '';
        const actualResult = calculateMonthlyResult(idx);
        const budgetBalance = calculateMonthlyBudgetBalance(idx);
        const colorClass = getBalanceColorClass(actualResult, budgetBalance);
        html += `<td class="${colorClass}${janClass}">${formatCurrency(actualResult)}</td>`;
    });
    const totalResult = months.reduce((sum, month, idx) => sum + calculateMonthlyResult(idx), 0);
    const totalBudget = months.reduce((sum, month, idx) => sum + calculateMonthlyBudgetBalance(idx), 0);
    const totalColorClass = getBalanceColorClass(totalResult, totalBudget);
    html += `<td class="total-column ${totalColorClass}">${formatCurrency(totalResult)}</td>`;
    html += '</tr>';

    // Difference row
    html += '<tr class="difference-row section-tile-row"><td class="category-cell">Difference</td>';
    months.forEach((month, idx) => {
        const janClass = idx === 0 ? ' jan-column' : '';
        const diff = calculateMonthlyDifference(idx);
        const colorClass = getDifferenceColorClass(diff);
        html += `<td class="${colorClass}${janClass}">${formatCurrency(diff)}</td>`;
    });
    const totalDiff = months.reduce((sum, month, idx) => sum + calculateMonthlyDifference(idx), 0);
    const totalDiffColorClass = getDifferenceColorClass(totalDiff);
    html += `<td class="total-column ${totalDiffColorClass}">${formatCurrency(totalDiff)}</td>`;
    html += '</tr>';

    return html;
}

function calculateMonthlyBudgetBalance(monthIndex) {
    const monthNum = monthIndex + 1;
    let budgetIncome = 0;
    let budgetExpenses = 0;

    budgetData.categories.forEach(cat => {
        const entries = budgetData.budget_entries[cat.id] || {};
        const entry = entries[monthNum];
        const amount = entry ? entry.amount : 0;

        if (cat.type === 'income') {
            budgetIncome += amount;
        } else {
            budgetExpenses += amount;
        }
    });

    return budgetIncome - budgetExpenses;
}

function calculateMonthlyResult(monthIndex) {
    const monthNum = monthIndex + 1;
    let income = 0;
    let expenses = 0;

    budgetData.categories.forEach(cat => {
        const transactions = budgetData.transactions[cat.id] || {};
        const monthTransactions = transactions[monthNum] || [];
        const total = monthTransactions.reduce((sum, t) => sum + t.amount, 0);

        if (cat.type === 'income') {
            income += total;
        } else {
            expenses += total;
        }
    });

    return income - expenses;
}

function calculateMonthlyDifference(monthIndex) {
    const budgetBalance = calculateMonthlyBudgetBalance(monthIndex);
    const actualResult = calculateMonthlyResult(monthIndex);
    return actualResult - budgetBalance;
}

function generateSectionRows(sectionType) {
    let html = '';
    const sectionCategories = budgetData.categories.filter(c => c.type === sectionType);

    sectionCategories.forEach(category => {
        // Category header
        html += `<tr class="section-tile-row category-header-row"><td colspan="${months.length + 2}" class="category-header-cell">${category.name}</td></tr>`;

        // Budget row
        html += `<tr class="budget-row section-tile-row">`;
        html += `<td class="subcategory-cell">Budget</td>`;

        const entries = budgetData.budget_entries[category.id] || {};

        months.forEach((month, idx) => {
            const monthNum = idx + 1;
            const entry = entries[monthNum];
            const budgetValue = entry ? entry.amount : 0;
            const isFuture = idx > currentMonth;
            const hasValue = entry ? 'has-value' : '';
            const janClass = idx === 0 ? ' jan-column' : '';
            const cellClass = isFuture ? 'result-future' : hasValue;
            const clickHandler = isFuture ? '' : `openBudgetModal('${category.id}', '${category.name}', ${monthNum})`;
            // No arrow for individual budget months - only on total
            html += `<td class="${cellClass}${janClass}" onclick="${clickHandler}">`;
            html += entry ? formatCurrency(budgetValue) : '<span class="empty-cell">-</span>';
            html += '</td>';
        });

        // Budget total
        const budgetTotal = calculateBudgetYearTotal(category.id);
        const hasAnyBudgetEntry = Object.keys(entries).length > 0;
        const budgetTotalClass = hasAnyBudgetEntry ? 'total-column has-value' : 'total-column';
        const budgetTotalArrow = getTrendArrowHTML(category.id, 'total', 'budget');
        html += `<td class="${budgetTotalClass}">${budgetTotalArrow}${hasAnyBudgetEntry ? formatCurrency(budgetTotal) : '<span class="empty-cell">-</span>'}</td>`;
        html += '</tr>';

        // Result row
        html += `<tr class="result-row section-tile-row">`;
        html += `<td class="subcategory-cell">Actuals</td>`;

        const transactions = budgetData.transactions[category.id] || {};

        months.forEach((month, idx) => {
            const monthNum = idx + 1;
            const monthTransactions = transactions[monthNum] || [];
            const resultTotal = monthTransactions.reduce((sum, t) => sum + t.amount, 0);
            const entry = entries[monthNum];
            const budgetValue = entry ? entry.amount : 0;
            const isFuture = idx > currentMonth;

            const janClass = idx === 0 ? ' jan-column' : '';
            const colorClass = getResultColorClass(resultTotal, budgetValue, sectionType, isFuture, monthTransactions.length > 0);
            const clickHandler = isFuture ? '' : `openTransactionModal('${category.id}', '${category.name}', ${monthNum})`;
            const arrow = getTrendArrowHTML(category.id, monthNum, 'actual');

            html += `<td class="${colorClass}${janClass}" onclick="${clickHandler}">`;
            html += arrow;
            html += monthTransactions.length > 0 ? formatCurrency(resultTotal) : '<span class="empty-cell">-</span>';
            html += '</td>';
        });

        // Result total
        const resultYearTotal = calculateResultYearTotal(category.id);
        const hasAnyTransaction = Object.values(transactions).some(monthTxs => monthTxs.length > 0);
        const resultTotalColorClass = getTotalColorClass(resultYearTotal, budgetTotal, sectionType, hasAnyTransaction);
        const actualTotalArrow = getTrendArrowHTML(category.id, 'total', 'actual');
        html += `<td class="${resultTotalColorClass}">${actualTotalArrow}${hasAnyTransaction ? formatCurrency(resultYearTotal) : '<span class="empty-cell">-</span>'}</td>`;
        html += '</tr>';
    });

    return html;
}

function getResultColorClass(result, budget, section, isFuture, hasTransactions) {
    if (isFuture) return 'result-future';
    if (!hasTransactions) return 'result-no-data';

    if (section === 'expenses') {
        return result <= budget ? 'result-better' : 'result-worse';
    } else {
        return result >= budget ? 'result-better' : 'result-worse';
    }
}

function getTotalColorClass(result, budget, section, hasTransactions) {
    if (!hasTransactions) return 'total-column result-no-data';

    if (section === 'expenses') {
        return result <= budget ? 'total-column result-better' : 'total-column result-worse';
    } else {
        return result >= budget ? 'total-column result-better' : 'total-column result-worse';
    }
}

function getBalanceColorClass(actualResult, budgetBalance) {
    if (actualResult === 0) return 'balance-white-cell';
    return actualResult >= budgetBalance ? 'result-better' : 'result-worse';
}

function getDifferenceColorClass(difference) {
    if (difference === 0) return 'balance-white-cell';
    return difference >= 0 ? 'result-better' : 'result-worse';
}

function calculateBudgetYearTotal(categoryId) {
    const entries = budgetData.budget_entries[categoryId] || {};
    let total = 0;
    for (let month = 1; month <= 12; month++) {
        const entry = entries[month];
        total += entry ? entry.amount : 0;
    }
    return total;
}

function calculateResultYearTotal(categoryId) {
    const transactions = budgetData.transactions[categoryId] || {};
    let total = 0;
    for (let month = 1; month <= 12; month++) {
        const monthTransactions = transactions[month] || [];
        total += monthTransactions.reduce((sum, t) => sum + t.amount, 0);
    }
    return total;
}

function getTrendArrowHTML(categoryId, month, type) {
    /**
     * Generate trend arrow HTML for a cell.
     *
     * @param {string} categoryId - Category ID
     * @param {number|string} month - Month number (1-12) or 'total'
     * @param {string} type - 'budget' or 'actual'
     * @returns {string} HTML for trend arrow or empty string
     */
    const trends = trendData[categoryId];
    if (!trends) return '';

    let trendInfo;
    if (month === 'total') {
        trendInfo = trends.total?.[type];
    } else {
        trendInfo = trends.months?.[String(month)]?.[type];
    }

    if (!trendInfo) return '';

    const arrowClass = `bi-arrow-${trendInfo.arrow}`;
    const colorClass = `text-${trendInfo.color}`;

    return `<i class="bi ${arrowClass} ${colorClass} trend-arrow"></i>`;
}

// ==================== BUDGET MODAL FUNCTIONS ====================

function openBudgetModal(categoryId, categoryName, month) {
    const entries = budgetData.budget_entries[categoryId] || {};
    const entry = entries[month];
    const entryId = entry ? entry.id : null;

    currentCell = { categoryId, categoryName, month, type: 'budget', entryId };

    const modal = new bootstrap.Modal(document.getElementById('budgetModal'));
    document.getElementById('budgetModalTitle').textContent =
        `${categoryName} - Budget - ${months[month - 1]}`;

    const currentValue = entry ? entry.amount : 0;
    document.getElementById('budgetAmount').value = currentValue;

    const currentComment = entry ? (entry.comment || '') : '';
    document.getElementById('budgetComment').value = currentComment;

    // Show delete button only if entry exists
    const deleteBtn = document.getElementById('deleteBudgetBtn');
    if (entryId) {
        deleteBtn.style.display = 'block';
    } else {
        deleteBtn.style.display = 'none';
    }

    modal.show();

    setTimeout(() => {
        document.getElementById('budgetAmount').focus();
        document.getElementById('budgetAmount').select();
    }, 500);
}

async function saveBudget() {
    const amount = parseInt(document.getElementById('budgetAmount').value) || 0;
    const comment = document.getElementById('budgetComment').value || '';
    const { categoryId, month } = currentCell;

    try {
        showLoading('Saving budget...');
        await saveBudgetEntry(categoryId, currentYear, month, amount, comment);

        // Reload budget data and trends for this category
        await loadBudgetData(currentYear);
        await loadCategoryTrends(currentYear, categoryId);

        // Close modal
        bootstrap.Modal.getInstance(document.getElementById('budgetModal')).hide();

        // Refresh table
        generateTable();
        hideLoading();
        showSuccess('Budget saved');
    } catch (error) {
        hideLoading();
        // Error already shown by apiCall
    }
}

async function deleteBudgetEntry() {
    const { entryId } = currentCell;

    if (!entryId) {
        showError('No budget entry to delete');
        return;
    }

    const confirmed = await showConfirmModal(
        'Delete Budget Entry',
        'Are you sure you want to delete this budget entry?',
        'Delete'
    );
    if (!confirmed) {
        return;
    }

    try {
        showLoading('Deleting budget entry...');
        await deleteBudgetEntryApi(entryId);

        // Reload budget data
        await loadBudgetData(currentYear);

        // Close modal
        bootstrap.Modal.getInstance(document.getElementById('budgetModal')).hide();

        // Refresh table
        generateTable();
        hideLoading();
        showSuccess('Budget entry deleted');
    } catch (error) {
        hideLoading();
        // Error already shown by apiCall
    }
}

// ==================== TRANSACTION MODAL FUNCTIONS ====================

async function openTransactionModal(categoryId, categoryName, month) {
    currentCell = { categoryId, categoryName, month, type: 'result' };

    const modal = new bootstrap.Modal(document.getElementById('transactionModal'));

    // Get category to determine type (income/expense)
    const category = getCategoryById(categoryId);
    const categoryBadgeClass = category.type === 'income' ? 'badge-income' : 'badge-expense';

    // Set badges with appropriate colors
    const categoryBadge = document.getElementById('modalCategory');
    categoryBadge.textContent = categoryName;
    categoryBadge.className = 'badge me-2 ' + categoryBadgeClass;

    document.getElementById('modalMonth').textContent = months[month - 1];

    await displayTransactions();
    modal.show();
}

async function displayTransactions() {
    const { categoryId, categoryName, month } = currentCell;
    const transactions = budgetData.transactions[categoryId] || {};
    const monthTransactions = transactions[month] || [];

    const listDiv = document.getElementById('transactionsList');

    if (monthTransactions.length === 0) {
        listDiv.innerHTML = '<div class="no-transactions"><i class="bi bi-inbox"></i><p>No transactions yet</p></div>';
        return;
    }

    let html = '';
    monthTransactions.forEach((t, index) => {
        const payee = t.payee_id ? getPayeeById(t.payee_id) : null;
        const payeeName = payee ? payee.name : '';

        html += `
            <div class="transaction-item">
                <div class="d-flex justify-content-between align-items-start">
                    <div class="flex-grow-1">
                        <div class="transaction-date">
                            <i class="bi bi-calendar3"></i> ${formatDate(t.date)}
                        </div>
                        ${payeeName ? `<div class="transaction-payee"><i class="bi bi-person"></i> ${payeeName}</div>` : ''}
                        <div class="transaction-amount">${formatCurrency(t.amount)}</div>
                        ${t.comment ? `<div class="transaction-comment">${t.comment}</div>` : ''}
                    </div>
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-outline-primary" onclick="editTransaction('${t.id}')">
                            <i class="bi bi-pencil"></i>
                        </button>
                        <button class="btn btn-outline-danger" onclick="deleteTransaction('${t.id}')">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
    });

    // Add summary
    const total = monthTransactions.reduce((sum, t) => sum + t.amount, 0);
    const category = getCategoryById(categoryId);
    const entries = budgetData.budget_entries[categoryId] || {};
    const entry = entries[month];
    const budget = entry ? entry.amount : 0;
    const diff = category.type === 'expenses' ? budget - total : total - budget;
    const diffClass = diff >= 0 ? 'positive' : 'negative';

    html += `
        <div class="alert alert-info mt-3">
            <div class="d-flex justify-content-between">
                <div><strong>Total:</strong> ${formatCurrency(total)}</div>
                <div><strong>Budget:</strong> ${formatCurrency(budget)}</div>
                <div><strong>Difference:</strong> <span class="${diffClass}">${formatCurrency(Math.abs(diff))}</span></div>
            </div>
        </div>
    `;

    listDiv.innerHTML = html;
}

function showAddTransactionForm() {
    currentTransactionIndex = null;
    document.getElementById('addTransactionTitle').textContent = 'Add transaction';
    document.getElementById('transactionForm').reset();

    // Set badges with appropriate colors
    const category = getCategoryById(currentCell.categoryId);
    const categoryBadgeClass = category.type === 'income' ? 'badge-income' : 'badge-expense';

    const categoryBadge = document.getElementById('addModalCategory');
    categoryBadge.textContent = currentCell.categoryName;
    categoryBadge.className = 'badge me-2 ' + categoryBadgeClass;

    document.getElementById('addModalMonth').textContent = months[currentCell.month - 1];

    // Set default date to 1st of the selected month
    const year = currentYear;
    const month = String(currentCell.month).padStart(2, '0');
    const day = '01';
    const defaultDate = `${year}-${month}-${day}`;

    // Set date using Tempus Dominus API if available
    if (datePicker) {
        datePicker.dates.setValue(new tempusDominus.DateTime(defaultDate));
    } else {
        // Fallback for plain input
        document.getElementById('transactionDate').value = defaultDate;
    }

    // Reset payee dropdown
    if (payeeSelect) {
        payeeSelect.clear();
        payeeSelect.clearOptions();
        payees.forEach(payee => {
            payeeSelect.addOption({value: payee.id, text: payee.name});
        });
    }

    const modal = new bootstrap.Modal(document.getElementById('addTransactionModal'));
    modal.show();
}

async function editTransaction(transactionId) {
    const { categoryId, month } = currentCell;
    const transactions = budgetData.transactions[categoryId] || {};
    const monthTransactions = transactions[month] || [];
    const transaction = monthTransactions.find(t => t.id === transactionId);

    if (!transaction) return;

    currentTransactionIndex = transactionId;
    document.getElementById('addTransactionTitle').textContent = 'Edit transaction';

    // Set badges with appropriate colors
    const category = getCategoryById(currentCell.categoryId);
    const categoryBadgeClass = category.type === 'income' ? 'badge-income' : 'badge-expense';

    const categoryBadge = document.getElementById('addModalCategory');
    categoryBadge.textContent = currentCell.categoryName;
    categoryBadge.className = 'badge me-2 ' + categoryBadgeClass;

    document.getElementById('addModalMonth').textContent = months[currentCell.month - 1];

    // Set date using Tempus Dominus API if available
    if (datePicker) {
        datePicker.dates.setValue(new tempusDominus.DateTime(transaction.date));
    } else {
        // Fallback for plain input
        document.getElementById('transactionDate').value = transaction.date;
    }

    document.getElementById('transactionAmount').value = transaction.amount;
    document.getElementById('transactionComment').value = transaction.comment || '';

    // Set payee dropdown
    if (payeeSelect) {
        payeeSelect.clear();
        payeeSelect.clearOptions();
        payees.forEach(payee => {
            payeeSelect.addOption({value: payee.id, text: payee.name});
        });
        if (transaction.payee_id) {
            payeeSelect.setValue(transaction.payee_id);
        }
    }

    // Close transaction list modal
    bootstrap.Modal.getInstance(document.getElementById('transactionModal')).hide();

    // Open edit modal
    const modal = new bootstrap.Modal(document.getElementById('addTransactionModal'));
    modal.show();
}

async function deleteTransaction(transactionId) {
    const confirmed = await showConfirmModal(
        'Delete Transaction',
        'Are you sure you want to delete this transaction?',
        'Delete'
    );
    if (!confirmed) {
        return;
    }

    try {
        showLoading('Deleting transaction...');
        await deleteTransactionApi(transactionId);

        // Reload budget data
        await loadBudgetData(currentYear);

        await displayTransactions();
        generateTable();
        hideLoading();
        showSuccess('Transaction deleted');
    } catch (error) {
        hideLoading();
    }
}

async function saveTransaction() {
    // Force TomSelect to create option from typed input before getting value
    // This prevents the double-click issue when user types a new payee
    if (payeeSelect) {
        payeeSelect.blur();
        // Give TomSelect a moment to process the blur and create the option
        await new Promise(resolve => setTimeout(resolve, 100));
    }

    const date = document.getElementById('transactionDate').value;
    const amount = parseInt(document.getElementById('transactionAmount').value);
    let payeeValue = payeeSelect ? payeeSelect.getValue() : '';
    const comment = document.getElementById('transactionComment').value;

    if (!date || isNaN(amount)) {
        showErrorModal('Please fill in all required fields');
        return;
    }

    try {
        showLoading('Saving transaction...');

        // Check if payee is a new value (not an existing ID or name)
        let payeeId = payeeValue;
        const existingPayee = payees.find(p =>
            p.id === payeeValue || p.name.toLowerCase() === payeeValue.toLowerCase()
        );

        if (payeeValue && !existingPayee) {
            // Create new payee
            const newPayee = await apiCall('/api/payee', {
                method: 'POST',
                body: JSON.stringify({
                    name: payeeValue,
                    type: 'Actual'
                })
            });
            payeeId = newPayee.id;

            // Reload payees list
            await loadPayees();
            updatePayeeSelect();
        } else if (existingPayee && existingPayee.name.toLowerCase() === payeeValue.toLowerCase()) {
            // User typed existing payee name - use existing payee's ID
            payeeId = existingPayee.id;
        }

        if (currentTransactionIndex) {
            // Edit existing
            await updateTransaction(currentTransactionIndex, date, amount, payeeId, comment);
        } else {
            // Create new
            await createTransaction(currentCell.categoryId, date, amount, payeeId, comment);
        }

        // Reload budget data and trends for this category
        await loadBudgetData(currentYear);
        await loadCategoryTrends(currentYear, currentCell.categoryId);

        // Close add modal
        const addModal = bootstrap.Modal.getInstance(document.getElementById('addTransactionModal'));
        addModal.hide();

        // Refresh display
        await displayTransactions();
        generateTable();
        hideLoading();
        showSuccess('Transaction saved');

        // Reopen transaction list modal
        setTimeout(() => {
            const listModal = new bootstrap.Modal(document.getElementById('transactionModal'));
            listModal.show();
        }, 350);
    } catch (error) {
        hideLoading();
    }
}

// ==================== CONFIG PAGE FUNCTIONS ====================

let currentEditingCategory = null;
let currentEditingPayee = null;

async function populateCategoriesTable() {
    const tbody = document.querySelector('#categoriesTable tbody');
    if (!tbody) return;

    let html = '';

    // Sort categories alphabetically by name
    const sortedCategories = [...allCategories].sort((a, b) => a.name.localeCompare(b.name));

    sortedCategories.forEach(cat => {
        const typeBadge = cat.type === 'income'
            ? '<span class="badge badge-income">Income</span>'
            : '<span class="badge badge-expense">Expenses</span>';

        const yearsText = cat.years_used && cat.years_used.length > 0
            ? cat.years_used.join(', ')
            : '<span class="text-muted">Not used</span>';

        const deleteBtn = cat.has_data
            ? `<button class="btn btn-sm btn-outline-secondary" disabled title="Cannot delete - category is in use">
                <i class="bi bi-trash"></i>
               </button>`
            : `<button class="btn btn-sm btn-outline-danger" onclick="deleteCategory('${cat.id}')">
                <i class="bi bi-trash"></i>
               </button>`;

        html += `
            <tr>
                <td>${cat.name}</td>
                <td>${typeBadge}</td>
                <td>${yearsText}</td>
                <td class="text-end">
                    <div class="btn-group" role="group">
                        <button class="btn btn-sm btn-outline-primary" onclick="editCategory('${cat.id}', '${cat.name}', '${cat.type}')">
                            <i class="bi bi-pencil"></i>
                        </button>
                        ${deleteBtn}
                    </div>
                </td>
            </tr>
        `;
    });

    tbody.innerHTML = html || '<tr><td colspan="4" class="text-center text-muted">No categories yet</td></tr>';
}

async function populatePayeesTable() {
    const tbody = document.querySelector('#payeesTable tbody');
    if (!tbody) return;

    let html = '';

    // Sort payees alphabetically by name
    const sortedPayees = [...payees].sort((a, b) => a.name.localeCompare(b.name));

    sortedPayees.forEach(payee => {
        const lastUsedText = payee.last_used
            ? formatDate(payee.last_used)
            : '<span class="text-muted">Never</span>';

        const deleteBtn = payee.transaction_count > 0
            ? `<button class="btn btn-sm btn-outline-secondary" disabled title="Cannot delete - payee is in use (${payee.transaction_count} transactions)">
                <i class="bi bi-trash"></i>
               </button>`
            : `<button class="btn btn-sm btn-outline-danger" onclick="deletePayee('${payee.id}')">
                <i class="bi bi-trash"></i>
               </button>`;

        html += `
            <tr class="payee-row" data-payee="${payee.name.toLowerCase()}">
                <td>${payee.name}</td>
                <td>${payee.transaction_count || 0}</td>
                <td>${lastUsedText}</td>
                <td class="text-end">
                    <div class="btn-group" role="group">
                        <button class="btn btn-sm btn-outline-primary" onclick="editPayee('${payee.id}', '${payee.name}', '${payee.type}')">
                            <i class="bi bi-pencil"></i>
                        </button>
                        ${deleteBtn}
                    </div>
                </td>
            </tr>
        `;
    });

    tbody.innerHTML = html || '<tr><td colspan="4" class="text-center text-muted">No payees yet</td></tr>';
}

function filterPayees() {
    const searchTerm = document.getElementById('payeeSearch').value.toLowerCase();
    const rows = document.querySelectorAll('.payee-row');

    rows.forEach(row => {
        const payeeName = row.getAttribute('data-payee');
        row.style.display = payeeName.includes(searchTerm) ? '' : 'none';
    });
}

function openAddCategoryModal() {
    currentEditingCategory = null;
    document.getElementById('categoryModalTitle').textContent = 'Add Category';
    document.getElementById('categoryName').value = '';
    document.getElementById('categoryType').value = '';
    document.getElementById('categoryType').disabled = false;

    const modal = new bootstrap.Modal(document.getElementById('categoryModal'));
    modal.show();
}

function editCategory(id, name, type) {
    currentEditingCategory = { id, name, type };
    document.getElementById('categoryModalTitle').textContent = 'Edit Category';
    document.getElementById('categoryName').value = name;
    document.getElementById('categoryType').value = type;
    document.getElementById('categoryType').disabled = true;

    const modal = new bootstrap.Modal(document.getElementById('categoryModal'));
    modal.show();
}

async function saveCategory() {
    const name = document.getElementById('categoryName').value.trim();
    const type = document.getElementById('categoryType').value;

    if (!name || !type) {
        showErrorModal('Please fill in all fields');
        return;
    }

    // Check for case-insensitive duplicates
    const nameLower = name.toLowerCase();
    const duplicate = allCategories.find(c =>
        c.name.toLowerCase() === nameLower &&
        (!currentEditingCategory || c.id !== currentEditingCategory.id)
    );
    if (duplicate) {
        showErrorModal(`Category "${duplicate.name}" already exists`);
        return;
    }

    try {
        showLoading('Saving category...');

        if (currentEditingCategory) {
            await updateCategory(currentEditingCategory.id, name);
        } else {
            await createCategory(name, type);
        }

        await loadCategories();

        document.getElementById('categoryType').disabled = false;
        bootstrap.Modal.getInstance(document.getElementById('categoryModal')).hide();
        await populateCategoriesTable();
        hideLoading();
        showSuccess('Category saved');

        // Refresh budget table if on that page
        if (document.getElementById('budgetTable')) {
            await loadBudgetData(currentYear);
            generateTable();
        }
    } catch (error) {
        hideLoading();
    }
}

async function deleteCategory(categoryId) {
    const category = allCategories.find(c => c.id === categoryId);
    const confirmed = await showConfirmModal(
        'Delete Category',
        `Are you sure you want to delete the category "${category.name}"?`,
        'Delete'
    );
    if (!confirmed) {
        return;
    }

    try {
        showLoading('Deleting category...');
        await deleteCategoryApi(categoryId);
        await loadCategories();
        await populateCategoriesTable();
        hideLoading();
        showSuccess('Category deleted');

        // Refresh budget table if on that page
        if (document.getElementById('budgetTable')) {
            await loadBudgetData(currentYear);
            generateTable();
        }
    } catch (error) {
        hideLoading();
    }
}

function openAddPayeeModal() {
    currentEditingPayee = null;
    document.getElementById('payeeModalTitle').textContent = 'Add Payee';
    document.getElementById('payeeName').value = '';

    const modal = new bootstrap.Modal(document.getElementById('payeeModal'));
    modal.show();
}

function editPayee(id, name, type) {
    currentEditingPayee = { id, name, type };
    document.getElementById('payeeModalTitle').textContent = 'Edit Payee';
    document.getElementById('payeeName').value = name;

    const modal = new bootstrap.Modal(document.getElementById('payeeModal'));
    modal.show();
}

async function savePayee() {
    const name = document.getElementById('payeeName').value.trim();

    if (!name) {
        showErrorModal('Please enter a payee name');
        return;
    }

    // Check for case-insensitive duplicates
    const nameLower = name.toLowerCase();
    const duplicate = payees.find(p =>
        p.name.toLowerCase() === nameLower &&
        (!currentEditingPayee || p.id !== currentEditingPayee.id)
    );
    if (duplicate) {
        showErrorModal(`Payee "${duplicate.name}" already exists`);
        return;
    }

    try {
        showLoading('Saving payee...');

        if (currentEditingPayee) {
            await updatePayee(currentEditingPayee.id, name, currentEditingPayee.type);
        } else {
            await createPayee(name, 'Actual');
        }

        await loadPayees();
        bootstrap.Modal.getInstance(document.getElementById('payeeModal')).hide();
        await populatePayeesTable();
        hideLoading();
        showSuccess('Payee saved');
    } catch (error) {
        hideLoading();
    }
}

async function deletePayee(payeeId) {
    const payee = payees.find(p => p.id === payeeId);
    const confirmed = await showConfirmModal(
        'Delete Payee',
        `Are you sure you want to delete the payee "${payee.name}"?`,
        'Delete'
    );
    if (!confirmed) {
        return;
    }

    try {
        showLoading('Deleting payee...');
        await deletePayeeApi(payeeId);
        await loadPayees();
        await populatePayeesTable();
        hideLoading();
        showSuccess('Payee deleted');
    } catch (error) {
        hideLoading();
    }
}

// ==================== INITIALIZATION ====================

function initializePayeeSelect() {
    const payeeElement = document.getElementById('transactionPayee');
    if (payeeElement && !payeeSelect) {
        payeeSelect = new TomSelect('#transactionPayee', {
            create: true,
            createOnBlur: true,
            sortField: 'text',
            placeholder: 'Select or type new payee...',
            maxOptions: 100,
            createFilter: function(input) {
                // Prevent creating duplicate payees (case-insensitive check)
                if (!input || input.length === 0) {
                    return false;
                }

                // Check if payee already exists (case-insensitive)
                const inputLower = input.toLowerCase().trim();
                const exists = payees.some(p => p.name.toLowerCase() === inputLower);

                return !exists; // Only allow creation if it doesn't exist
            }
        });
    }
}

function initializeDatePicker() {
    const dateElement = document.getElementById('transactionDatePicker');
    if (dateElement && typeof tempusDominus !== 'undefined') {
        datePicker = new tempusDominus.TempusDominus(dateElement, {
            display: {
                viewMode: 'calendar',
                components: {
                    decades: true,
                    year: true,
                    month: true,
                    date: true,
                    hours: false,
                    minutes: false,
                    seconds: false
                },
                buttons: {
                    today: true,
                    clear: false,
                    close: false
                },
                icons: {
                    type: 'icons',
                    time: 'bi bi-clock',
                    date: 'bi bi-calendar',
                    up: 'bi bi-arrow-up',
                    down: 'bi bi-arrow-down',
                    previous: 'bi bi-chevron-left',
                    next: 'bi bi-chevron-right',
                    today: 'bi bi-calendar-check',
                    clear: 'bi bi-trash',
                    close: 'bi bi-x'
                },
                theme: 'light'
            },
            localization: {
                format: 'yyyy-MM-dd',
                locale: 'en',
                dayViewHeaderFormat: { month: 'long', year: 'numeric' }
            }
        });
    }
}

// ==================== DASHBOARD WIDGET FUNCTIONS ====================

async function loadRecurringPayments() {
    const container = document.getElementById('recurring-payments-content');
    if (!container) return;

    try {
        const recurringPayments = await apiCall('/api/dashboard/recurring-payments', { suppressError: true });

        if (!recurringPayments || recurringPayments.length === 0) {
            container.innerHTML = `
                <div class="text-center text-muted py-3">
                    <i class="bi bi-info-circle" style="font-size: 2rem;"></i>
                    <p class="small mt-2 mb-0">No recurring payments detected yet. Transactions will appear here once you have payees appearing in consecutive months.</p>
                </div>
            `;
            return;
        }

        // Group by status
        const pending = recurringPayments.filter(p => p.status === 'pending');
        const paid = recurringPayments.filter(p => p.status === 'paid');

        let html = '<div class="list-group list-group-flush">';

        // Show pending first
        pending.forEach(payment => {
            html += `
                <div class="list-group-item d-flex justify-content-between align-items-start px-0">
                    <div class="flex-grow-1">
                        <div class="fw-bold">${payment.payee_name}</div>
                        <small class="text-muted">Last: ${payment.last_payment_date} - ${formatCurrency(payment.last_amount)}</small>
                    </div>
                    <span class="badge bg-warning text-dark">
                        <i class="bi bi-exclamation-triangle me-1"></i>Pending
                    </span>
                </div>
            `;
        });

        // Show paid after
        paid.forEach(payment => {
            html += `
                <div class="list-group-item d-flex justify-content-between align-items-start px-0">
                    <div class="flex-grow-1">
                        <div class="fw-bold">${payment.payee_name}</div>
                        <small class="text-muted">Last: ${payment.last_payment_date} - ${formatCurrency(payment.last_amount)}</small>
                    </div>
                    <span class="badge bg-success">
                        <i class="bi bi-check-circle me-1"></i>Paid
                    </span>
                </div>
            `;
        });

        html += '</div>';
        container.innerHTML = html;

    } catch (error) {
        console.error('Failed to load recurring payments:', error);
        container.innerHTML = `
            <div class="alert alert-danger mb-0" role="alert">
                <i class="bi bi-exclamation-circle me-2"></i>Failed to load recurring payments
            </div>
        `;
    }
}

async function loadRecentTransactions() {
    const container = document.getElementById('recent-transactions-content');
    if (!container) return;

    try {
        const transactions = await apiCall('/api/dashboard/recent-transactions', { suppressError: true });

        if (!transactions || transactions.length === 0) {
            container.innerHTML = `
                <div class="text-center text-muted py-3">
                    <i class="bi bi-info-circle" style="font-size: 2rem;"></i>
                    <p class="small mt-2 mb-0">No transactions yet. Start by entering budget and actual values in the Budget & Actuals page.</p>
                </div>
            `;
            return;
        }

        let html = '<div class="list-group list-group-flush">';

        transactions.forEach(tx => {
            const amountClass = tx.category_type === 'income' ? 'text-success' : 'text-danger';
            const amountPrefix = tx.category_type === 'income' ? '+' : '-';

            html += `
                <div class="list-group-item px-0">
                    <div class="d-flex justify-content-between align-items-start">
                        <div class="flex-grow-1">
                            <div class="fw-bold">${tx.payee_name}</div>
                            <small class="text-muted">${tx.category_name} • ${tx.transaction_date}</small>
                        </div>
                        <div class="${amountClass} fw-bold">
                            ${amountPrefix}${formatCurrency(Math.abs(tx.amount))}
                        </div>
                    </div>
                </div>
            `;
        });

        html += '</div>';
        container.innerHTML = html;

    } catch (error) {
        console.error('Failed to load recent transactions:', error);
        container.innerHTML = `
            <div class="alert alert-danger mb-0" role="alert">
                <i class="bi bi-exclamation-circle me-2"></i>Failed to load recent transactions
            </div>
        `;
    }
}

async function initializeDashboard() {
    // Load currency format first (needed for formatting)
    await loadCurrencyFormat();

    // Load both widgets in parallel
    await Promise.all([
        loadRecurringPayments(),
        loadRecentTransactions()
    ]);
}

async function loadCurrencyFormat() {
    try {
        const result = await apiCall('/api/config/currency', { suppressError: true });
        if (result && result.currency_format) {
            currentCurrencyFormat = result.currency_format;
        } else {
            currentCurrencyFormat = '';
        }
    } catch (error) {
        console.error('Failed to load currency format:', error);
        currentCurrencyFormat = '';
    }
}

document.addEventListener('DOMContentLoaded', async function() {
    // Global modal cleanup on hide - ensures scroll is always restored
    document.addEventListener('hidden.bs.modal', function() {
        cleanupBackdrops();
    });

    // Initialize budget page
    if (document.getElementById('budgetTable')) {
        await initializeBudgetPage();
        initializePayeeSelect();
        initializeDatePicker();

        // Enter key support for budget modal
        const budgetAmount = document.getElementById('budgetAmount');
        if (budgetAmount) {
            budgetAmount.addEventListener('keypress', function(e) {
                if (e.key === 'Enter') {
                    e.preventDefault();
                    saveBudget();
                }
            });
        }
    }

    // Initialize config page
    if (document.getElementById('categoriesTable')) {
        // Read database configuration state from data attribute
        const configData = document.getElementById('configPageData');
        window.DATABASE_CONFIGURED = configData ? configData.dataset.databaseConfigured === 'true' : false;

        // Always load database settings (from moneybags_db_config.json)
        await loadDatabaseSettings();

        // Only load data from database if database is configured
        if (window.DATABASE_CONFIGURED) {
            showLoading('Loading configuration...');
            await loadCategories();
            await loadPayees();
            await loadCurrencySettings();
            await populateCategoriesTable();
            await populatePayeesTable();
            await loadBudgetTemplates();
            hideLoading();
        } else {
            // Database not configured - show message and focus on database connection section
            console.log('Database not configured. Please enter database connection details.');
        }
    }

    // Initialize dashboard page
    if (document.getElementById('recurring-payments-content') || document.getElementById('recent-transactions-content')) {
        await initializeDashboard();
    }

    // ==================== EVENT LISTENERS ====================

    // Budget page event listeners
    const yearSelector = document.getElementById('yearSelector');
    if (yearSelector) {
        yearSelector.addEventListener('change', changeYear);
    }

    const deleteBudgetBtn = document.getElementById('deleteBudgetBtn');
    if (deleteBudgetBtn) {
        deleteBudgetBtn.addEventListener('click', deleteBudgetEntry);
    }

    const saveBudgetBtn = document.getElementById('saveBudgetBtn');
    if (saveBudgetBtn) {
        saveBudgetBtn.addEventListener('click', saveBudget);
    }

    const addTransactionBtn = document.getElementById('addTransactionBtn');
    if (addTransactionBtn) {
        addTransactionBtn.addEventListener('click', showAddTransactionForm);
    }

    const saveTransactionBtn = document.getElementById('saveTransactionBtn');
    if (saveTransactionBtn) {
        saveTransactionBtn.addEventListener('click', saveTransaction);
    }

    // Config page event listeners
    const addYearBtn = document.getElementById('addYearBtn');
    if (addYearBtn) {
        addYearBtn.addEventListener('click', openAddYearModal);
    }

    const addCategoryBtn = document.getElementById('addCategoryBtn');
    if (addCategoryBtn) {
        addCategoryBtn.addEventListener('click', openAddCategoryModal);
    }

    const addPayeeBtn = document.getElementById('addPayeeBtn');
    if (addPayeeBtn) {
        addPayeeBtn.addEventListener('click', openAddPayeeModal);
    }

    const payeeSearch = document.getElementById('payeeSearch');
    if (payeeSearch) {
        payeeSearch.addEventListener('keyup', filterPayees);
    }

    const currencyFormat = document.getElementById('currencyFormat');
    if (currencyFormat) {
        currencyFormat.addEventListener('change', enableCurrencySaveButton);
    }

    const saveCurrencyBtn = document.getElementById('saveCurrencyBtn');
    if (saveCurrencyBtn) {
        saveCurrencyBtn.addEventListener('click', saveCurrencySettings);
    }

    const testDbConnectionBtn = document.getElementById('testDbConnectionBtn');
    if (testDbConnectionBtn) {
        testDbConnectionBtn.addEventListener('click', testDatabaseConnection);
    }

    const saveDbConnectionBtn = document.getElementById('saveDbConnectionBtn');
    if (saveDbConnectionBtn) {
        saveDbConnectionBtn.addEventListener('click', saveDatabaseConnection);
    }

    const saveCategoryModalBtn = document.getElementById('saveCategoryModalBtn');
    if (saveCategoryModalBtn) {
        saveCategoryModalBtn.addEventListener('click', saveCategory);
    }

    const savePayeeModalBtn = document.getElementById('savePayeeModalBtn');
    if (savePayeeModalBtn) {
        savePayeeModalBtn.addEventListener('click', savePayee);
    }

    const saveNewYearBtn = document.getElementById('saveNewYearBtn');
    if (saveNewYearBtn) {
        saveNewYearBtn.addEventListener('click', saveNewYear);
    }
});

// ==================== CURRENCY SETTINGS FUNCTIONS ====================

let originalCurrencyFormat = '';

async function loadCurrencySettings() {
    try {
        const result = await apiCall('/api/config/currency', { suppressError: true });
        const currencySelect = document.getElementById('currencyFormat');

        if (result && result.currency_format) {
            currencySelect.value = result.currency_format;
            originalCurrencyFormat = result.currency_format;
        } else {
            // No currency format set - default to empty
            currencySelect.value = '';
            originalCurrencyFormat = '';
        }

        // Disable save button initially
        document.getElementById('saveCurrencyBtn').disabled = true;
    } catch (error) {
        console.error('Failed to load currency settings:', error);
        // On error, leave as "Not selected"
        document.getElementById('currencyFormat').value = '';
        originalCurrencyFormat = '';
    }
}

function enableCurrencySaveButton() {
    const currencySelect = document.getElementById('currencyFormat');
    const saveBtn = document.getElementById('saveCurrencyBtn');

    // Enable save button only if value has changed
    saveBtn.disabled = (currencySelect.value === originalCurrencyFormat);
}

async function saveCurrencySettings() {
    const currencyFormat = document.getElementById('currencyFormat').value;

    if (!currencyFormat) {
        showError('Please select a currency format');
        return;
    }

    try {
        showLoading('Saving currency settings...');

        await apiCall('/api/config/currency', {
            method: 'PUT',
            body: JSON.stringify({
                currency_format: currencyFormat
            })
        });

        hideLoading();
        showToast('Currency settings saved successfully', 'success');

        // Update original value and disable save button
        originalCurrencyFormat = currencyFormat;
        currentCurrencyFormat = currencyFormat;
        document.getElementById('saveCurrencyBtn').disabled = true;

        // Update currency labels in modals
        updateCurrencyLabels();

        // Reload budget page if it's open to apply new currency format
        if (document.getElementById('budgetTable')) {
            generateTable();
        }
    } catch (error) {
        hideLoading();
        showError('Failed to save currency settings: ' + error.message);
    }
}

// ==================== DATABASE CONNECTION FUNCTIONS ====================

async function loadDatabaseSettings() {
    try {
        const result = await apiCall('/api/config/db-connection');

        // Populate form fields with values from moneybags_db_config.json
        if (result.db_host) document.getElementById('dbHost').value = result.db_host;
        if (result.db_port) document.getElementById('dbPort').value = result.db_port;
        if (result.db_name) document.getElementById('dbName').value = result.db_name;
        if (result.db_user) document.getElementById('dbUser').value = result.db_user;
        if (result.db_pool_size) document.getElementById('dbPoolSize').value = result.db_pool_size;

        // Note: Password is not returned for security reasons
        // User must re-enter password to save changes
    } catch (error) {
        console.error('Failed to load database settings:', error);
    }
}

async function testDatabaseConnection() {
    const statusEl = document.getElementById('connectionStatus');
    statusEl.classList.remove('d-none', 'alert-success', 'alert-danger');

    const data = {
        host: document.getElementById('dbHost').value,
        port: parseInt(document.getElementById('dbPort').value),
        database: document.getElementById('dbName').value,
        user: document.getElementById('dbUser').value,
        password: document.getElementById('dbPassword').value
    };

    try {
        showLoading('Testing connection...');
        const result = await apiCall('/api/config/test-db-connection', {
            method: 'POST',
            body: JSON.stringify(data)
        });

        hideLoading();
        statusEl.classList.remove('d-none');
        statusEl.classList.add('alert-success');
        statusEl.innerHTML = '<i class="bi bi-check-circle me-2"></i>' + (result.message || 'Connection successful!');
    } catch (error) {
        hideLoading();
        statusEl.classList.remove('d-none');
        statusEl.classList.add('alert-danger');
        statusEl.innerHTML = '<i class="bi bi-x-circle me-2"></i>Connection failed: ' + error.message;
    }
}

async function saveDatabaseConnection() {
    const confirmed = await showConfirmModal(
        'Restart Required',
        'Changing database settings requires an application restart. Continue?',
        'Continue'
    );
    if (!confirmed) {
        return;
    }

    const data = {
        db_host: document.getElementById('dbHost').value,
        db_port: parseInt(document.getElementById('dbPort').value),
        db_name: document.getElementById('dbName').value,
        db_user: document.getElementById('dbUser').value,
        db_password: document.getElementById('dbPassword').value,
        db_pool_size: parseInt(document.getElementById('dbPoolSize').value)
    };

    // Validate required fields
    if (!data.db_host || !data.db_name || !data.db_user || !data.db_password) {
        showToast('Please fill in all required fields', 'error');
        return;
    }

    try {
        showLoading('Saving settings...');
        const result = await apiCall('/api/config/save-db-connection', {
            method: 'POST',
            body: JSON.stringify(data)
        });

        hideLoading();
        showToast(result.message || 'Database settings saved. Please restart the application for changes to take effect.', 'success');
    } catch (error) {
        hideLoading();
    }
}

// ==================== BUDGET TEMPLATES FUNCTIONS ====================

async function loadBudgetTemplates() {
    try {
        const years = await apiCall('/api/years', { suppressError: true });

        if (years.length === 0) {
            document.getElementById('noYearsMessage').style.display = 'block';
            document.getElementById('budgetTemplatesAccordion').style.display = 'none';
            return;
        }

        document.getElementById('noYearsMessage').style.display = 'none';
        document.getElementById('budgetTemplatesAccordion').style.display = 'block';

        // Sort years in descending order (most recent on top)
        const sortedYears = [...years].sort((a, b) => b - a);

        // Load templates for each year
        const accordion = document.getElementById('budgetTemplatesAccordion');
        accordion.innerHTML = '';

        for (const year of sortedYears) {
            const template = await apiCall(`/api/budget-template/${year}`, { suppressError: true });
            accordion.innerHTML += generateYearAccordionItem(year, template);
        }
    } catch (error) {
        console.error('Failed to load budget templates:', error);
        // Show empty state on error
        document.getElementById('noYearsMessage').style.display = 'block';
        document.getElementById('budgetTemplatesAccordion').style.display = 'none';
    }
}

function generateYearAccordionItem(year, categories) {
    const thisYear = new Date().getFullYear();
    const isCurrentYear = year === thisYear;
    const collapseId = `collapse${year}`;

    let html = `
        <div class="accordion-item">
            <h2 class="accordion-header">
                <button class="accordion-button ${!isCurrentYear ? 'collapsed' : ''}" type="button" data-bs-toggle="collapse" data-bs-target="#${collapseId}">
                    <strong>${year}</strong>
                    <span class="badge bg-primary ms-2">${categories.length} categories</span>
                </button>
            </h2>
            <div id="${collapseId}" class="accordion-collapse collapse ${isCurrentYear ? 'show' : ''}" data-bs-parent="#budgetTemplatesAccordion">
                <div class="accordion-body">
                    <div class="mb-3">
                        <label class="form-label">Active Categories for ${year}</label>
                        <div class="d-flex flex-wrap gap-2" id="categories${year}">
    `;

    categories.forEach(cat => {
        html += `
            <div class="badge badge-${cat.type === 'income' ? 'income' : 'expense'} d-flex align-items-center gap-2">
                ${cat.name}
                <button type="button" class="btn-close btn-close-white btn-close-small" onclick="removeCategoryFromYear(${year}, '${cat.id}')" ${cat.has_data ? 'disabled title="Cannot remove - has budget data"' : ''}></button>
            </div>
        `;
    });

    html += `
                        </div>
                    </div>
                    <div class="mb-3">
                        <label for="addCategory${year}" class="form-label">Add Category</label>
                        <select class="form-select" id="addCategory${year}">
                            <option value="">Select category to add...</option>
    `;

    // Add all categories not yet in this year
    const activeIds = categories.map(c => c.id);
    allCategories.forEach(cat => {
        if (!activeIds.includes(cat.id)) {
            html += `<option value="${cat.id}">${cat.name} (${cat.type})</option>`;
        }
    });

    html += `
                        </select>
                        <button type="button" class="btn btn-sm btn-primary mt-2" onclick="addCategoryToYear(${year})">
                            <i class="bi bi-plus-circle me-1"></i>Add
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `;

    return html;
}

function openAddYearModal() {
    const thisYear = new Date().getFullYear();
    document.getElementById('newYear').value = thisYear + 1;

    const modal = new bootstrap.Modal(document.getElementById('addYearModal'));
    modal.show();
}

async function saveNewYear() {
    const year = parseInt(document.getElementById('newYear').value);
    const copyFromPrevious = document.getElementById('copyFromPreviousYear').checked;

    if (!year || year < 2000 || year > 2100) {
        showErrorModal('Please enter a valid year between 2000 and 2100');
        return;
    }

    // Check if year already exists
    const existingYears = await apiCall('/api/years');
    if (existingYears.includes(year)) {
        showErrorModal(`Year ${year} already exists`);
        return;
    }

    // Check if there are any categories available
    if (allCategories.length === 0) {
        showErrorModal('Please create categories first before adding a year');
        return;
    }

    try {
        showLoading('Creating year...');

        if (copyFromPrevious && existingYears.length > 0) {
            // Copy from most recent year
            const fromYear = Math.max(...existingYears);
            await apiCall('/api/budget-template/copy', {
                method: 'POST',
                body: JSON.stringify({ from_year: fromYear, to_year: year })
            });
        } else {
            // Create year by adding all available categories
            // This ensures the year appears in the UI
            for (const category of allCategories) {
                await apiCall('/api/budget-template', {
                    method: 'POST',
                    body: JSON.stringify({ year: year, category_id: category.id })
                });
            }
        }

        // Reload templates
        await loadBudgetTemplates();

        bootstrap.Modal.getInstance(document.getElementById('addYearModal')).hide();
        hideLoading();
        showSuccess(`Year ${year} created with ${allCategories.length} categories`);
    } catch (error) {
        hideLoading();
    }
}

async function addCategoryToYear(year) {
    const selectId = `addCategory${year}`;
    const categoryId = document.getElementById(selectId).value;

    if (!categoryId) {
        showErrorModal('Please select a category');
        return;
    }

    try {
        showLoading('Adding category...');
        await apiCall('/api/budget-template', {
            method: 'POST',
            body: JSON.stringify({ year: year, category_id: categoryId })
        });

        await loadBudgetTemplates();
        hideLoading();
        showSuccess('Category added to year');
    } catch (error) {
        hideLoading();
    }
}

async function removeCategoryFromYear(year, categoryId) {
    const category = allCategories.find(c => c.id === categoryId);

    const confirmed = await showConfirmModal(
        'Remove Category',
        `Remove "${category.name}" from ${year}? This is only possible if no budget data exists for this category in ${year}.`,
        'Remove'
    );
    if (!confirmed) {
        return;
    }

    try {
        showLoading('Removing category...');
        await apiCall(`/api/budget-template/${year}/${categoryId}`, {
            method: 'DELETE'
        });

        await loadBudgetTemplates();
        hideLoading();
        showSuccess('Category removed from year');
    } catch (error) {
        hideLoading();
    }
}

// ==================== IMPORT PAGE ====================

// Global state for import workflow
