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

// All payees (loaded from API)
let payees = [];

// Current cell being edited
let currentCell = null;
let currentTransactionIndex = null;

// Tom Select instance
let payeeSelect = null;

// Tempus Dominus instance
let datePicker = null;

// ==================== API FUNCTIONS ====================

async function apiCall(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });

        const data = await response.json();

        if (!data.success) {
            throw new Error(data.error || 'API request failed');
        }

        return data.data;
    } catch (error) {
        console.error('API Error:', error);
        showError(error.message || 'Network error occurred');
        throw error;
    }
}

async function loadCategories() {
    allCategories = await apiCall('/api/categories');
}

async function loadPayees() {
    const payeeData = await apiCall('/api/payees');
    payees = payeeData.map(p => ({
        id: p.id,
        name: p.name,
        type: p.type,
        transaction_count: p.transaction_count,
        last_used: p.last_used
    }));
}

async function loadAvailableYears() {
    availableYears = await apiCall('/api/years');
    if (availableYears.length === 0) {
        availableYears = [currentYear];
    }
}

async function loadBudgetData(year) {
    budgetData = await apiCall(`/api/budget/${year}`);
}

async function saveBudgetEntry(categoryId, year, month, amount) {
    return await apiCall('/api/budget/entry', {
        method: 'POST',
        body: JSON.stringify({
            category_id: categoryId,
            year: year,
            month: month,
            amount: amount
        })
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

function formatCurrency(amount) {
    return 'kr ' + Math.round(amount).toLocaleString('nb-NO');
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
        await loadAvailableYears();
        await populateYearSelector();
        await loadBudgetData(currentYear);
        generateTable();
        hideLoading();
    } catch (error) {
        hideLoading();
        showError('Failed to initialize budget page');
    }
}

function populateYearSelector() {
    const selector = document.getElementById('yearSelector');
    if (!selector) return;

    selector.innerHTML = '';

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
    months.forEach(month => {
        html += `<th class="month-header-cell">${month}</th>`;
    });
    html += '<th class="month-header-cell">Total</th></tr>';
    return html;
}

function generateBalanceRows() {
    let html = '';

    // Budget Balance row
    html += '<tr class="budget-balance-row section-tile-row"><td class="category-cell">Budget Balance</td>';
    months.forEach((month, idx) => {
        const balance = calculateMonthlyBudgetBalance(idx);
        html += `<td class="balance-white-cell">${formatCurrency(balance)}</td>`;
    });
    const totalBalance = months.reduce((sum, month, idx) => sum + calculateMonthlyBudgetBalance(idx), 0);
    html += `<td class="total-column balance-white-cell">${formatCurrency(totalBalance)}</td>`;
    html += '</tr>';

    // Result Balance row
    html += '<tr class="result-balance-row section-tile-row"><td class="category-cell">Result Balance</td>';
    months.forEach((month, idx) => {
        const actualResult = calculateMonthlyResult(idx);
        const budgetBalance = calculateMonthlyBudgetBalance(idx);
        const colorClass = getBalanceColorClass(actualResult, budgetBalance);
        html += `<td class="${colorClass}">${formatCurrency(actualResult)}</td>`;
    });
    const totalResult = months.reduce((sum, month, idx) => sum + calculateMonthlyResult(idx), 0);
    const totalBudget = months.reduce((sum, month, idx) => sum + calculateMonthlyBudgetBalance(idx), 0);
    const totalColorClass = getBalanceColorClass(totalResult, totalBudget);
    html += `<td class="total-column ${totalColorClass}">${formatCurrency(totalResult)}</td>`;
    html += '</tr>';

    // Difference row
    html += '<tr class="difference-row section-tile-row"><td class="category-cell">Difference</td>';
    months.forEach((month, idx) => {
        const diff = calculateMonthlyDifference(idx);
        const colorClass = getDifferenceColorClass(diff);
        html += `<td class="${colorClass}">${formatCurrency(diff)}</td>`;
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
            const hasValue = budgetValue > 0 ? 'has-value' : '';
            const cellClass = isFuture ? 'result-future' : hasValue;
            const clickHandler = isFuture ? '' : `openBudgetModal('${category.id}', '${category.name}', ${monthNum})`;
            html += `<td class="${cellClass}" onclick="${clickHandler}">`;
            html += budgetValue > 0 ? formatCurrency(budgetValue) : '<span class="empty-cell">0</span>';
            html += '</td>';
        });

        // Budget total
        const budgetTotal = calculateBudgetYearTotal(category.id);
        const budgetTotalClass = budgetTotal > 0 ? 'total-column has-value' : 'total-column';
        html += `<td class="${budgetTotalClass}">${formatCurrency(budgetTotal)}</td>`;
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

            const colorClass = getResultColorClass(resultTotal, budgetValue, sectionType, isFuture);
            const clickHandler = isFuture ? '' : `openTransactionModal('${category.id}', '${category.name}', ${monthNum})`;

            html += `<td class="${colorClass}" onclick="${clickHandler}">`;
            html += resultTotal > 0 ? formatCurrency(resultTotal) : '<span class="empty-cell">0</span>';
            html += '</td>';
        });

        // Result total
        const resultYearTotal = calculateResultYearTotal(category.id);
        const resultTotalColorClass = getTotalColorClass(resultYearTotal, budgetTotal, sectionType);
        html += `<td class="${resultTotalColorClass}">${formatCurrency(resultYearTotal)}</td>`;
        html += '</tr>';
    });

    return html;
}

function getResultColorClass(result, budget, section, isFuture) {
    if (isFuture) return 'result-future';
    if (result === 0) return 'result-no-data';

    if (section === 'expenses') {
        return result <= budget ? 'result-better' : 'result-worse';
    } else {
        return result >= budget ? 'result-better' : 'result-worse';
    }
}

function getTotalColorClass(result, budget, section) {
    if (result === 0) return 'total-column result-no-data';

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

// ==================== BUDGET MODAL FUNCTIONS ====================

function openBudgetModal(categoryId, categoryName, month) {
    currentCell = { categoryId, categoryName, month, type: 'budget' };

    const modal = new bootstrap.Modal(document.getElementById('budgetModal'));
    document.getElementById('budgetModalTitle').textContent =
        `${categoryName} - Budget - ${months[month - 1]}`;

    const entries = budgetData.budget_entries[categoryId] || {};
    const entry = entries[month];
    const currentValue = entry ? entry.amount : 0;
    document.getElementById('budgetAmount').value = currentValue;

    modal.show();

    setTimeout(() => {
        document.getElementById('budgetAmount').focus();
        document.getElementById('budgetAmount').select();
    }, 500);
}

async function saveBudget() {
    const amount = parseInt(document.getElementById('budgetAmount').value) || 0;
    const { categoryId, month } = currentCell;

    try {
        showLoading('Saving budget...');
        await saveBudgetEntry(categoryId, currentYear, month, amount);

        // Reload budget data
        await loadBudgetData(currentYear);

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
        listDiv.innerHTML = '<div class="no-transactions"><i class="bi bi-inbox" style="font-size: 3rem;"></i><p>No transactions yet</p></div>';
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

        // Reload budget data
        await loadBudgetData(currentYear);

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
                    <button class="btn btn-sm btn-outline-primary me-1" onclick="editCategory('${cat.id}', '${cat.name}', '${cat.type}')">
                        <i class="bi bi-pencil"></i>
                    </button>
                    ${deleteBtn}
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
                    <button class="btn btn-sm btn-outline-primary me-1" onclick="editPayee('${payee.id}', '${payee.name}', '${payee.type}')">
                        <i class="bi bi-pencil"></i>
                    </button>
                    ${deleteBtn}
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
                // Allow creating new payees (any non-empty string)
                return input.length > 0;
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
        showLoading('Loading configuration...');
        await loadCategories();
        await loadPayees();
        await populateCategoriesTable();
        await populatePayeesTable();
        await loadDatabaseSettings();
        await loadBudgetTemplates();
        hideLoading();
    }
});

// ==================== DATABASE CONNECTION FUNCTIONS ====================

async function loadDatabaseSettings() {
    try {
        const config = await apiCall('/api/config');

        // Populate form fields
        if (config.db_host) document.getElementById('dbHost').value = config.db_host;
        if (config.db_port) document.getElementById('dbPort').value = config.db_port;
        if (config.db_name) document.getElementById('dbName').value = config.db_name;
        if (config.db_user) document.getElementById('dbUser').value = config.db_user;
        if (config.db_pool_size) document.getElementById('dbPoolSize').value = config.db_pool_size;
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

        statusEl.classList.add('alert-success');
        statusEl.innerHTML = '<i class="bi bi-check-circle me-2"></i>Connection successful!';
        hideLoading();
    } catch (error) {
        statusEl.classList.add('alert-danger');
        statusEl.innerHTML = '<i class="bi bi-x-circle me-2"></i>Connection failed: ' + error.message;
        hideLoading();
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
        db_port: document.getElementById('dbPort').value,
        db_name: document.getElementById('dbName').value,
        db_user: document.getElementById('dbUser').value,
        db_pool_size: document.getElementById('dbPoolSize').value
    };

    const password = document.getElementById('dbPassword').value;
    if (password) {
        data.db_password = password;
    }

    try {
        showLoading('Saving settings...');
        await apiCall('/api/config', {
            method: 'PUT',
            body: JSON.stringify(data)
        });

        hideLoading();
        showToast('Database settings saved. Please restart the application for changes to take effect.', 'success');
    } catch (error) {
        hideLoading();
    }
}

// ==================== BUDGET TEMPLATES FUNCTIONS ====================

async function loadBudgetTemplates() {
    try {
        const years = await apiCall('/api/years');

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
            const template = await apiCall(`/api/budget-template/${year}`);
            accordion.innerHTML += generateYearAccordionItem(year, template);
        }
    } catch (error) {
        console.error('Failed to load budget templates:', error);
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
                <button type="button" class="btn-close btn-close-white" style="font-size: 0.7rem;" onclick="removeCategoryFromYear(${year}, '${cat.id}')" ${cat.has_data ? 'disabled title="Cannot remove - has budget data"' : ''}></button>
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
    const currentYear = new Date().getFullYear();
    document.getElementById('newYear').value = currentYear + 1;

    const modal = new bootstrap.Modal(document.getElementById('addYearModal'));
    modal.show();
}

async function saveNewYear() {
    const year = parseInt(document.getElementById('newYear').value);
    const copyFromPrevious = document.getElementById('copyFromPreviousYear').checked;

    if (!year || year < 2020 || year > 2100) {
        showErrorModal('Please enter a valid year between 2020 and 2100');
        return;
    }

    try {
        showLoading('Creating year...');

        if (copyFromPrevious) {
            // Get most recent year
            const years = await apiCall('/api/years');
            if (years.length > 0) {
                const fromYear = Math.max(...years);
                await apiCall('/api/budget-template/copy', {
                    method: 'POST',
                    body: JSON.stringify({ from_year: fromYear, to_year: year })
                });
            }
        }

        // Reload templates
        await loadBudgetTemplates();

        bootstrap.Modal.getInstance(document.getElementById('addYearModal')).hide();
        hideLoading();
        showSuccess(`Year ${year} created`);
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
