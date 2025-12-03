// Moneybags Application JavaScript

// Data structure for budget categories
const categories = {
    income: [
        { name: 'Salary' },
        { name: 'Other income' }
    ],
    expenses: [
        { name: 'Housing & utilities' },
        { name: 'Repairs & maintenance' },
        { name: 'Digital services' },
        { name: 'Cars' },
        { name: 'Clothing & travel' },
        { name: 'Sports' },
        { name: 'Travel' },
        { name: 'Savings' }
    ]
};

const months = ['January', 'February', 'March', 'April', 'May', 'June',
               'July', 'August', 'September', 'October', 'November', 'December'];

// Current month (0-11)
const currentMonth = new Date().getMonth();

// Data structure to store all data
let budgetData = {
    income: {},
    expenses: {}
};

// Current cell being edited
let currentCell = null;
let currentTransactionIndex = null;

// Helper function to clean up modal backdrops
function cleanupBackdrops() {
    const backdrops = document.querySelectorAll('.modal-backdrop');
    backdrops.forEach(backdrop => backdrop.remove());
    document.body.classList.remove('modal-open');
    document.body.style.removeProperty('overflow');
    document.body.style.removeProperty('padding-right');
}

// Initialize budget data structure with mock data
function initializeBudgetData() {
    const sections = ['income', 'expenses'];

    sections.forEach(section => {
        const sectionCategories = categories[section];

        sectionCategories.forEach(category => {
            budgetData[section][category.name] = {
                budget: {},
                result: {}
            };

            months.forEach(month => {
                budgetData[section][category.name].budget[month] = 0;
                budgetData[section][category.name].result[month] = [];
            });
        });
    });

    // Add some mock data
    addMockData();
}

function addMockData() {
    // Mock salary budget and actuals
    budgetData.income['Salary'].budget['January'] = 53000;
    budgetData.income['Salary'].budget['February'] = 53000;
    budgetData.income['Salary'].budget['March'] = 53000;

    budgetData.income['Salary'].result['January'] = [
        { date: '2025-01-15', amount: 55920, comment: 'Salary January' }
    ];
    budgetData.income['Salary'].result['February'] = [
        { date: '2025-02-15', amount: 55501, comment: 'Salary February' }
    ];
    budgetData.income['Salary'].result['March'] = [
        { date: '2025-03-15', amount: 72228, comment: 'Salary March with bonus' }
    ];

    // Mock expense budgets and actuals
    budgetData.expenses['Housing & utilities'].budget['January'] = 20000;
    budgetData.expenses['Housing & utilities'].budget['February'] = 20000;
    budgetData.expenses['Housing & utilities'].budget['March'] = 20000;

    budgetData.expenses['Housing & utilities'].result['January'] = [
        { date: '2025-01-05', amount: 15000, comment: 'Rent' },
        { date: '2025-01-25', amount: 935, comment: 'Electricity bill' }
    ];
    budgetData.expenses['Housing & utilities'].result['February'] = [
        { date: '2025-02-05', amount: 15000, comment: 'Rent' },
        { date: '2025-02-25', amount: 922, comment: 'Electricity bill' }
    ];

    budgetData.expenses['Digital services'].budget['January'] = 1100;
    budgetData.expenses['Digital services'].budget['February'] = 1100;
    budgetData.expenses['Digital services'].budget['March'] = 1100;

    budgetData.expenses['Digital services'].result['January'] = [
        { date: '2025-01-10', amount: 149, comment: 'Netflix' },
        { date: '2025-01-12', amount: 129, comment: 'Spotify' },
        { date: '2025-01-15', amount: 99, comment: 'iCloud' },
        { date: '2025-01-20', amount: 805, comment: 'Adobe Creative Cloud' }
    ];
    budgetData.expenses['Digital services'].result['February'] = [
        { date: '2025-02-10', amount: 149, comment: 'Netflix' },
        { date: '2025-02-12', amount: 129, comment: 'Spotify' },
        { date: '2025-02-15', amount: 99, comment: 'iCloud' },
        { date: '2025-02-20', amount: 682, comment: 'Adobe Creative Cloud' }
    ];

    budgetData.expenses['Sports'].budget['March'] = 30000;
    budgetData.expenses['Sports'].result['March'] = [
        { date: '2025-03-12', amount: 34418, comment: 'New skis' }
    ];
}

// Generate the budget table
function generateTable() {
    const table = document.getElementById('budgetTable');
    if (!table) return; // Guard for when table doesn't exist on page

    let html = '<thead><tr><th></th>';

    // Month headers
    months.forEach(month => {
        html += `<th>${month}</th>`;
    });
    html += '<th>Total</th></tr></thead><tbody>';

    // Balance section
    html += `<tr><td colspan="${months.length + 2}" class="section-header balance-header">BALANCE</td></tr>`;
    html += generateBalanceRows();

    // Income section
    html += `<tr><td colspan="${months.length + 2}" class="section-header income-header">INCOME</td></tr>`;
    html += generateSectionRows('income', categories.income);

    // Expenses section
    html += `<tr><td colspan="${months.length + 2}" class="section-header expense-header">EXPENSES</td></tr>`;
    html += generateSectionRows('expenses', categories.expenses);

    html += '</tbody>';
    table.innerHTML = html;
}

function generateBalanceRows() {
    let html = '';

    // Bank row (calculated)
    html += '<tr class="result-row"><td class="category-cell">Bank Balance</td>';
    months.forEach((month, idx) => {
        const balance = calculateMonthlyBalance(idx);
        html += `<td>${formatCurrency(balance)}</td>`;
    });
    const totalBalance = months.reduce((sum, month, idx) => sum + calculateMonthlyBalance(idx), 0);
    html += `<td class="total-column">${formatCurrency(totalBalance)}</td>`;
    html += '</tr>';

    // Net Result row (calculated)
    html += '<tr class="result-row"><td class="category-cell">Net Result</td>';
    months.forEach((month, idx) => {
        const result = calculateMonthlyResult(idx);
        const cssClass = result >= 0 ? 'positive' : 'negative';
        html += `<td><span class="${cssClass}">${formatCurrency(result)}</span></td>`;
    });
    const totalResult = months.reduce((sum, month, idx) => sum + calculateMonthlyResult(idx), 0);
    const totalCssClass = totalResult >= 0 ? 'positive' : 'negative';
    html += `<td class="total-column"><span class="${totalCssClass}">${formatCurrency(totalResult)}</span></td>`;
    html += '</tr>';

    // Difference row (calculated)
    html += '<tr class="difference-row"><td class="category-cell">Difference</td>';
    months.forEach((month, idx) => {
        const diff = calculateMonthlyDifference(idx);
        const cssClass = diff >= 0 ? 'positive' : 'negative';
        html += `<td><span class="${cssClass}">${formatCurrency(diff)}</span></td>`;
    });
    const totalDiff = months.reduce((sum, month, idx) => sum + calculateMonthlyDifference(idx), 0);
    const totalDiffCssClass = totalDiff >= 0 ? 'positive' : 'negative';
    html += `<td class="total-column"><span class="${totalDiffCssClass}">${formatCurrency(totalDiff)}</span></td>`;
    html += '</tr>';

    return html;
}

function calculateMonthlyBalance(monthIndex) {
    const month = months[monthIndex];
    let income = 0;
    let expenses = 0;

    // Sum all actual income
    categories.income.forEach(cat => {
        income += calculateResultTotal(budgetData.income[cat.name].result[month]);
    });

    // Sum all actual expenses
    categories.expenses.forEach(cat => {
        expenses += calculateResultTotal(budgetData.expenses[cat.name].result[month]);
    });

    return income - expenses;
}

function calculateMonthlyResult(monthIndex) {
    // Result = Actual Income - Actual Expenses
    const month = months[monthIndex];
    let income = 0;
    let expenses = 0;

    categories.income.forEach(cat => {
        income += calculateResultTotal(budgetData.income[cat.name].result[month]);
    });

    categories.expenses.forEach(cat => {
        expenses += calculateResultTotal(budgetData.expenses[cat.name].result[month]);
    });

    return income - expenses;
}

function calculateMonthlyDifference(monthIndex) {
    // Difference = (Actual Income - Actual Expenses) - (Budget Income - Budget Expenses)
    const month = months[monthIndex];
    let budgetIncome = 0;
    let budgetExpenses = 0;
    let actualIncome = 0;
    let actualExpenses = 0;

    categories.income.forEach(cat => {
        budgetIncome += budgetData.income[cat.name].budget[month] || 0;
        actualIncome += calculateResultTotal(budgetData.income[cat.name].result[month]);
    });

    categories.expenses.forEach(cat => {
        budgetExpenses += budgetData.expenses[cat.name].budget[month] || 0;
        actualExpenses += calculateResultTotal(budgetData.expenses[cat.name].result[month]);
    });

    const budgetResult = budgetIncome - budgetExpenses;
    const actualResult = actualIncome - actualExpenses;

    return actualResult - budgetResult;
}

function generateSectionRows(section, sectionCategories) {
    let html = '';

    sectionCategories.forEach(category => {
        // Category header
        html += `<tr><td class="category-cell">${category.name}</td>`;
        for (let i = 0; i < months.length + 1; i++) {
            html += '<td class="category-cell"></td>';
        }
        html += '</tr>';

        // Budget row
        html += `<tr class="budget-row">`;
        html += `<td class="subcategory-cell">Budget</td>`;

        months.forEach((month, idx) => {
            const budgetValue = budgetData[section][category.name].budget[month] || 0;
            const isFuture = idx > currentMonth;
            const cellClass = isFuture ? 'result-future' : '';
            html += `<td class="${cellClass}" onclick="${isFuture ? '' : `openBudgetModal('${section}', '${category.name}', '${month}')`}">`;
            html += budgetValue > 0 ? formatCurrency(budgetValue) : '<span class="empty-cell">0</span>';
            html += '</td>';
        });

        // Budget total
        const budgetTotal = calculateBudgetYearTotal(section, category.name);
        html += `<td class="total-column">${formatCurrency(budgetTotal)}</td>`;
        html += '</tr>';

        // Result row
        html += `<tr class="result-row">`;
        html += `<td class="subcategory-cell">Actuals</td>`;

        months.forEach((month, idx) => {
            const transactions = budgetData[section][category.name].result[month];
            const resultTotal = calculateResultTotal(transactions);
            const budgetValue = budgetData[section][category.name].budget[month] || 0;
            const isFuture = idx > currentMonth;

            const colorClass = getResultColorClass(resultTotal, budgetValue, section, isFuture);

            html += `<td class="${colorClass}" onclick="${isFuture ? '' : `openTransactionModal('${section}', '${category.name}', '${month}')`}">`;
            html += resultTotal > 0 ? formatCurrency(resultTotal) : '<span class="empty-cell">0</span>';
            html += '</td>';
        });

        // Result total
        const resultTotal = calculateResultYearTotal(section, category.name);
        html += `<td class="total-column">${formatCurrency(resultTotal)}</td>`;
        html += '</tr>';
    });

    return html;
}

function getResultColorClass(result, budget, section, isFuture) {
    if (isFuture) {
        return 'result-future';
    }

    if (result === 0 && budget > 0) {
        return 'result-no-data';
    }

    if (budget === 0) {
        return 'result-no-data';
    }

    if (section === 'expenses') {
        // For expenses: lower is better
        if (result < budget) return 'result-better';
        if (result > budget) return 'result-worse';
        return 'result-equal';
    } else {
        // For income: higher is better
        if (result > budget) return 'result-better';
        if (result < budget) return 'result-worse';
        return 'result-equal';
    }
}

function calculateResultTotal(transactions) {
    return transactions.reduce((sum, t) => sum + parseFloat(t.amount), 0);
}

function calculateBudgetYearTotal(section, category) {
    let total = 0;
    months.forEach(month => {
        total += budgetData[section][category].budget[month] || 0;
    });
    return total;
}

function calculateResultYearTotal(section, category) {
    let total = 0;
    months.forEach(month => {
        total += calculateResultTotal(budgetData[section][category].result[month]);
    });
    return total;
}

function formatCurrency(amount) {
    return 'kr ' + Math.round(amount).toLocaleString('nb-NO');
}

// Budget Modal Functions
function openBudgetModal(section, category, month) {
    currentCell = { section, category, month, type: 'budget' };

    const modal = new bootstrap.Modal(document.getElementById('budgetModal'));
    document.getElementById('budgetModalTitle').textContent =
        `${category} - Budget - ${month}`;

    const currentValue = budgetData[section][category].budget[month] || 0;
    document.getElementById('budgetAmount').value = currentValue;

    modal.show();

    // Focus the input field
    setTimeout(() => {
        document.getElementById('budgetAmount').focus();
        document.getElementById('budgetAmount').select();
    }, 500);
}

function saveBudget() {
    const amount = parseFloat(document.getElementById('budgetAmount').value) || 0;
    const { section, category, month } = currentCell;

    budgetData[section][category].budget[month] = amount;

    // Close modal
    bootstrap.Modal.getInstance(document.getElementById('budgetModal')).hide();

    // Refresh table
    generateTable();
}

// Transaction Modal Functions
function openTransactionModal(section, category, month) {
    currentCell = { section, category, month, type: 'result' };

    const modal = new bootstrap.Modal(document.getElementById('transactionModal'));

    // Set badges
    document.getElementById('modalCategory').textContent = category;
    document.getElementById('modalMonth').textContent = month;

    displayTransactions();
    modal.show();
}

function displayTransactions() {
    const { section, category, month } = currentCell;
    const transactions = budgetData[section][category].result[month];

    const listDiv = document.getElementById('transactionsList');

    if (transactions.length === 0) {
        listDiv.innerHTML = '<div class="no-transactions"><i class="bi bi-inbox" style="font-size: 3rem;"></i><p>No transactions yet</p></div>';
        return;
    }

    let html = '';
    transactions.forEach((t, index) => {
        html += `
            <div class="transaction-item">
                <div class="d-flex justify-content-between align-items-start">
                    <div class="flex-grow-1">
                        <div class="transaction-date">
                            <i class="bi bi-calendar3"></i> ${formatDate(t.date)}
                        </div>
                        <div class="transaction-amount">${formatCurrency(t.amount)}</div>
                        ${t.comment ? `<div class="transaction-comment">${t.comment}</div>` : ''}
                    </div>
                    <div class="btn-group btn-group-sm">
                        <button class="btn btn-outline-primary" onclick="editTransaction(${index})">
                            <i class="bi bi-pencil"></i>
                        </button>
                        <button class="btn btn-outline-danger" onclick="deleteTransaction(${index})">
                            <i class="bi bi-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
    });

    // Add total
    const total = calculateResultTotal(transactions);
    const budget = budgetData[section][category].budget[month] || 0;
    const diff = section === 'expenses' ? budget - total : total - budget;
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

function formatDate(dateStr) {
    const date = new Date(dateStr);
    return date.toLocaleDateString('nb-NO', { day: '2-digit', month: 'short', year: 'numeric' });
}

function showAddTransactionForm() {
    currentTransactionIndex = null;
    document.getElementById('addTransactionTitle').textContent = 'Add transaction';
    document.getElementById('transactionForm').reset();

    // Set badges
    document.getElementById('addModalCategory').textContent = currentCell.category;
    document.getElementById('addModalMonth').textContent = currentCell.month;

    // Set default date to current month
    const monthIndex = months.indexOf(currentCell.month);
    const year = 2025;
    const defaultDate = new Date(year, monthIndex, 1);
    document.getElementById('transactionDate').value = defaultDate.toISOString().split('T')[0];

    const modal = new bootstrap.Modal(document.getElementById('addTransactionModal'));
    modal.show();
}

function editTransaction(index) {
    currentTransactionIndex = index;
    const { section, category, month } = currentCell;
    const transaction = budgetData[section][category].result[month][index];

    document.getElementById('addTransactionTitle').textContent = 'Edit transaction';

    // Set badges
    document.getElementById('addModalCategory').textContent = category;
    document.getElementById('addModalMonth').textContent = month;

    document.getElementById('transactionDate').value = transaction.date;
    document.getElementById('transactionAmount').value = transaction.amount;
    document.getElementById('transactionComment').value = transaction.comment || '';

    // Close transaction list modal
    bootstrap.Modal.getInstance(document.getElementById('transactionModal')).hide();

    // Open edit modal
    const modal = new bootstrap.Modal(document.getElementById('addTransactionModal'));
    modal.show();
}

function deleteTransaction(index) {
    if (!confirm('Are you sure you want to delete this transaction?')) {
        return;
    }

    const { section, category, month } = currentCell;
    budgetData[section][category].result[month].splice(index, 1);

    displayTransactions();
    generateTable(); // Refresh table to update totals
}

function saveTransaction() {
    const date = document.getElementById('transactionDate').value;
    const amount = parseFloat(document.getElementById('transactionAmount').value);
    const comment = document.getElementById('transactionComment').value;

    if (!date || isNaN(amount)) {
        alert('Please fill in all required fields');
        return;
    }

    const transaction = { date, amount, comment };
    const { section, category, month } = currentCell;

    if (currentTransactionIndex !== null) {
        // Edit existing transaction
        budgetData[section][category].result[month][currentTransactionIndex] = transaction;
    } else {
        // Add new transaction
        budgetData[section][category].result[month].push(transaction);
    }

    // Close add transaction modal
    const addModal = bootstrap.Modal.getInstance(document.getElementById('addTransactionModal'));
    addModal.hide();

    // Clean up any stray backdrops
    setTimeout(() => {
        cleanupBackdrops();
    }, 100);

    // Refresh display
    displayTransactions();
    generateTable(); // Refresh table to update totals

    // Reopen transaction list modal
    setTimeout(() => {
        const listModal = bootstrap.Modal.getInstance(document.getElementById('transactionModal'));
        if (listModal) {
            listModal.show();
        } else {
            const modal = new bootstrap.Modal(document.getElementById('transactionModal'));
            modal.show();
        }
    }, 350);
}

function saveData() {
    const dataStr = JSON.stringify(budgetData, null, 2);
    localStorage.setItem('budgetData', dataStr);
    alert('Data saved!');
}

function exportData() {
    const dataStr = JSON.stringify(budgetData, null, 2);
    const blob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'budget_2025.json';
    a.click();
}

function loadData() {
    const saved = localStorage.getItem('budgetData');
    if (saved) {
        budgetData = JSON.parse(saved);
    }
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize if we're on the budget page
    if (document.getElementById('budgetTable')) {
        initializeBudgetData();
        // loadData(); // Uncomment to load from localStorage
        generateTable();

        // Handle modal close to refresh main modal
        const addTransactionModal = document.getElementById('addTransactionModal');
        if (addTransactionModal) {
            addTransactionModal.addEventListener('hidden.bs.modal', function() {
                if (currentCell) {
                    displayTransactions();
                }
            });
        }

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
});
