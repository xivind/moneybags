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

const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
               'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

// Current month (0-11)
const currentMonth = new Date().getMonth();

// Current year
let currentYear = new Date().getFullYear();

// Available years (can be expanded)
let availableYears = [2024, 2025, 2026];

// Data structure to store all data by year
let budgetData = {};

// Store all payees
let payees = [];

// Current cell being edited
let currentCell = null;
let currentTransactionIndex = null;

// Tom Select instance
let payeeSelect = null;

// Helper function to clean up modal backdrops
function cleanupBackdrops() {
    const backdrops = document.querySelectorAll('.modal-backdrop');
    backdrops.forEach(backdrop => backdrop.remove());
    document.body.classList.remove('modal-open');
    document.body.style.removeProperty('overflow');
    document.body.style.removeProperty('padding-right');
}

// Initialize budget data structure for all years
function initializeBudgetData() {
    availableYears.forEach(year => {
        budgetData[year] = {
            income: {},
            expenses: {}
        };

        const sections = ['income', 'expenses'];

        sections.forEach(section => {
            const sectionCategories = categories[section];

            sectionCategories.forEach(category => {
                budgetData[year][section][category.name] = {
                    budget: {},
                    result: {}
                };

                months.forEach(month => {
                    budgetData[year][section][category.name].budget[month] = 0;
                    budgetData[year][section][category.name].result[month] = [];
                });
            });
        });
    });

    // Add some mock data
    addMockData();
}

function addMockData() {
    // Mock salary budget and actuals for 2025
    const year2025 = budgetData[2025];

    year2025.income['Salary'].budget['Jan'] = 53000;
    year2025.income['Salary'].budget['Feb'] = 53000;
    year2025.income['Salary'].budget['Mar'] = 53000;

    year2025.income['Salary'].result['Jan'] = [
        { date: '2025-01-15', amount: 55920, payee: 'Employer', comment: 'Salary January' }
    ];
    year2025.income['Salary'].result['Feb'] = [
        { date: '2025-02-15', amount: 55501, payee: 'Employer', comment: 'Salary February' }
    ];
    year2025.income['Salary'].result['Mar'] = [
        { date: '2025-03-15', amount: 72228, payee: 'Employer', comment: 'Salary March with bonus' }
    ];

    // Mock expense budgets and actuals
    year2025.expenses['Housing & utilities'].budget['Jan'] = 20000;
    year2025.expenses['Housing & utilities'].budget['Feb'] = 20000;
    year2025.expenses['Housing & utilities'].budget['Mar'] = 20000;

    year2025.expenses['Housing & utilities'].result['Jan'] = [
        { date: '2025-01-05', amount: 15000, payee: 'Landlord', comment: 'Rent' },
        { date: '2025-01-25', amount: 935, payee: 'Power Company', comment: 'Electricity bill' }
    ];
    year2025.expenses['Housing & utilities'].result['Feb'] = [
        { date: '2025-02-05', amount: 15000, payee: 'Landlord', comment: 'Rent' },
        { date: '2025-02-25', amount: 922, payee: 'Power Company', comment: 'Electricity bill' }
    ];

    year2025.expenses['Digital services'].budget['Jan'] = 1100;
    year2025.expenses['Digital services'].budget['Feb'] = 1100;
    year2025.expenses['Digital services'].budget['Mar'] = 1100;

    year2025.expenses['Digital services'].result['Jan'] = [
        { date: '2025-01-10', amount: 149, payee: 'Netflix', comment: 'Subscription' },
        { date: '2025-01-12', amount: 129, payee: 'Spotify', comment: 'Subscription' },
        { date: '2025-01-15', amount: 99, payee: 'Apple iCloud', comment: 'Storage subscription' },
        { date: '2025-01-20', amount: 805, payee: 'Adobe', comment: 'Creative Cloud subscription' }
    ];
    year2025.expenses['Digital services'].result['Feb'] = [
        { date: '2025-02-10', amount: 149, payee: 'Netflix', comment: 'Subscription' },
        { date: '2025-02-12', amount: 129, payee: 'Spotify', comment: 'Subscription' },
        { date: '2025-02-15', amount: 99, payee: 'Apple iCloud', comment: 'Storage subscription' },
        { date: '2025-02-20', amount: 682, payee: 'Adobe', comment: 'Creative Cloud subscription' }
    ];

    year2025.expenses['Sports'].budget['Mar'] = 30000;
    year2025.expenses['Sports'].result['Mar'] = [
        { date: '2025-03-12', amount: 34418, payee: 'Ski Shop', comment: 'New skis' }
    ];

    // Extract unique payees from mock data
    extractPayeesFromData();
}

// Helper function to get current year's data
function getCurrentYearData() {
    return budgetData[currentYear];
}

// Extract all unique payees from budget data (all years)
function extractPayeesFromData() {
    const uniquePayees = new Set();

    availableYears.forEach(year => {
        ['income', 'expenses'].forEach(section => {
            Object.keys(budgetData[year][section]).forEach(category => {
                months.forEach(month => {
                    const transactions = budgetData[year][section][category].result[month];
                    transactions.forEach(t => {
                        if (t.payee) {
                            uniquePayees.add(t.payee);
                        }
                    });
                });
            });
        });
    });

    payees = Array.from(uniquePayees).sort();
}

// Populate year selector dropdown
function populateYearSelector() {
    const selector = document.getElementById('yearSelector');
    if (!selector) return;

    selector.innerHTML = '';
    availableYears.forEach(year => {
        const option = document.createElement('option');
        option.value = year;
        option.textContent = year;
        if (year === currentYear) {
            option.selected = true;
        }
        selector.appendChild(option);
    });
}

// Change year and refresh table
function changeYear() {
    const selector = document.getElementById('yearSelector');
    currentYear = parseInt(selector.value);
    generateTable();
}

// Generate the budget table
function generateTable() {
    const table = document.getElementById('budgetTable');
    if (!table) return; // Guard for when table doesn't exist on page

    let html = '<tbody>';

    // Balance section
    html += `<tr><td colspan="${months.length + 2}" class="section-header balance-header">BALANCE</td></tr>`;
    html += generateMonthHeaderRow();
    html += generateBalanceRows();

    // Spacer before Income section
    html += `<tr class="section-spacer"><td colspan="${months.length + 2}" class="section-spacer"></td></tr>`;
    // Income section
    html += `<tr><td colspan="${months.length + 2}" class="section-header income-header">INCOME</td></tr>`;
    html += generateMonthHeaderRow();
    html += generateSectionRows('income', categories.income);

    // Spacer before Expenses section
    html += `<tr class="section-spacer"><td colspan="${months.length + 2}" class="section-spacer"></td></tr>`;
    // Expenses section
    html += `<tr><td colspan="${months.length + 2}" class="section-header expense-header">EXPENSES</td></tr>`;
    html += generateMonthHeaderRow();
    html += generateSectionRows('expenses', categories.expenses);

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

    // Budget Balance row - always white background
    html += '<tr class="budget-balance-row section-tile-row"><td class="category-cell">Budget Balance</td>';
    months.forEach((month, idx) => {
        const balance = calculateMonthlyBudgetBalance(idx);
        html += `<td class="balance-white-cell">${formatCurrency(balance)}</td>`;
    });
    const totalBalance = months.reduce((sum, month, idx) => sum + calculateMonthlyBudgetBalance(idx), 0);
    html += `<td class="total-column balance-white-cell">${formatCurrency(totalBalance)}</td>`;
    html += '</tr>';

    // Result Balance row - color coded like income actuals
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

    // Difference row - color coded based on difference >= 0 (green) or < 0 (red)
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
    const month = months[monthIndex];
    const yearData = getCurrentYearData();
    let budgetIncome = 0;
    let budgetExpenses = 0;

    // Sum all budget income
    categories.income.forEach(cat => {
        budgetIncome += yearData.income[cat.name].budget[month] || 0;
    });

    // Sum all budget expenses
    categories.expenses.forEach(cat => {
        budgetExpenses += yearData.expenses[cat.name].budget[month] || 0;
    });

    return budgetIncome - budgetExpenses;
}

function calculateMonthlyResult(monthIndex) {
    // Result = Actual Income - Actual Expenses
    const month = months[monthIndex];
    const yearData = getCurrentYearData();
    let income = 0;
    let expenses = 0;

    categories.income.forEach(cat => {
        income += calculateResultTotal(yearData.income[cat.name].result[month]);
    });

    categories.expenses.forEach(cat => {
        expenses += calculateResultTotal(yearData.expenses[cat.name].result[month]);
    });

    return income - expenses;
}

function calculateMonthlyDifference(monthIndex) {
    // Difference = (Actual Income - Actual Expenses) - (Budget Income - Budget Expenses)
    const month = months[monthIndex];
    const yearData = getCurrentYearData();
    let budgetIncome = 0;
    let budgetExpenses = 0;
    let actualIncome = 0;
    let actualExpenses = 0;

    categories.income.forEach(cat => {
        budgetIncome += yearData.income[cat.name].budget[month] || 0;
        actualIncome += calculateResultTotal(yearData.income[cat.name].result[month]);
    });

    categories.expenses.forEach(cat => {
        budgetExpenses += yearData.expenses[cat.name].budget[month] || 0;
        actualExpenses += calculateResultTotal(yearData.expenses[cat.name].result[month]);
    });

    const budgetResult = budgetIncome - budgetExpenses;
    const actualResult = actualIncome - actualExpenses;

    return actualResult - budgetResult;
}

function generateSectionRows(section, sectionCategories) {
    let html = '';
    const yearData = getCurrentYearData();

    sectionCategories.forEach(category => {
        // Category header - single cell spanning all columns
        html += `<tr class="section-tile-row category-header-row"><td colspan="${months.length + 2}" class="category-header-cell">${category.name}</td></tr>`;

        // Budget row
        html += `<tr class="budget-row section-tile-row">`;
        html += `<td class="subcategory-cell">Budget</td>`;

        months.forEach((month, idx) => {
            const budgetValue = yearData[section][category.name].budget[month] || 0;
            const isFuture = idx > currentMonth;
            const hasValue = budgetValue > 0 ? 'has-value' : '';
            const cellClass = isFuture ? 'result-future' : hasValue;
            html += `<td class="${cellClass}" onclick="${isFuture ? '' : `openBudgetModal('${section}', '${category.name}', '${month}')`}">`;
            html += budgetValue > 0 ? formatCurrency(budgetValue) : '<span class="empty-cell">0</span>';
            html += '</td>';
        });

        // Budget total
        const budgetTotal = calculateBudgetYearTotal(section, category.name);
        const budgetTotalClass = budgetTotal > 0 ? 'total-column has-value' : 'total-column';
        html += `<td class="${budgetTotalClass}">${formatCurrency(budgetTotal)}</td>`;
        html += '</tr>';

        // Result row
        html += `<tr class="result-row section-tile-row">`;
        html += `<td class="subcategory-cell">Actuals</td>`;

        months.forEach((month, idx) => {
            const transactions = yearData[section][category.name].result[month];
            const resultTotal = calculateResultTotal(transactions);
            const budgetValue = yearData[section][category.name].budget[month] || 0;
            const isFuture = idx > currentMonth;

            const colorClass = getResultColorClass(resultTotal, budgetValue, section, isFuture);

            html += `<td class="${colorClass}" onclick="${isFuture ? '' : `openTransactionModal('${section}', '${category.name}', '${month}')`}">`;
            html += resultTotal > 0 ? formatCurrency(resultTotal) : '<span class="empty-cell">0</span>';
            html += '</td>';
        });

        // Result total - apply same color logic
        const resultYearTotal = calculateResultYearTotal(section, category.name);
        const resultTotalColorClass = getTotalColorClass(resultYearTotal, budgetTotal, section);
        html += `<td class="${resultTotalColorClass}">${formatCurrency(resultYearTotal)}</td>`;
        html += '</tr>';
    });

    return html;
}

function getResultColorClass(result, budget, section, isFuture) {
    if (isFuture) {
        return 'result-future';
    }

    // No data - show yellow
    if (result === 0) {
        return 'result-no-data';
    }

    if (section === 'expenses') {
        // For expenses: lower or equal is better (green), higher is worse (red)
        if (result <= budget) return 'result-better';
        if (result > budget) return 'result-worse';
    } else {
        // For income: higher or equal is better (green), lower is worse (red)
        if (result >= budget) return 'result-better';
        if (result < budget) return 'result-worse';
    }
}

function getTotalColorClass(result, budget, section) {
    // Total column always has computed values
    // If no actual results, show yellow
    if (result === 0) {
        return 'total-column result-no-data';
    }

    if (section === 'expenses') {
        // For expenses: lower or equal is better (green), higher is worse (red)
        if (result <= budget) return 'total-column result-better';
        if (result > budget) return 'total-column result-worse';
    } else {
        // For income: higher or equal is better (green), lower is worse (red)
        if (result >= budget) return 'total-column result-better';
        if (result < budget) return 'total-column result-worse';
    }
}

function getBalanceColorClass(actualResult, budgetBalance) {
    // White when no data to sum
    if (actualResult === 0) {
        return 'balance-white-cell';
    }

    // Follow income logic: higher or equal is better (green), lower is worse (red)
    if (actualResult >= budgetBalance) return 'result-better';
    if (actualResult < budgetBalance) return 'result-worse';
}

function getDifferenceColorClass(difference) {
    // White when no data
    if (difference === 0) {
        return 'balance-white-cell';
    }

    // Green if >= 0 (at budget or better), red if < 0 (worse than budget)
    if (difference >= 0) return 'result-better';
    return 'result-worse';
}

function calculateResultTotal(transactions) {
    return transactions.reduce((sum, t) => sum + parseFloat(t.amount), 0);
}

function calculateBudgetYearTotal(section, category) {
    const yearData = getCurrentYearData();
    let total = 0;
    months.forEach(month => {
        total += yearData[section][category].budget[month] || 0;
    });
    return total;
}

function calculateResultYearTotal(section, category) {
    const yearData = getCurrentYearData();
    let total = 0;
    months.forEach(month => {
        total += calculateResultTotal(yearData[section][category].result[month]);
    });
    return total;
}

function formatCurrency(amount) {
    return 'kr ' + Math.round(amount).toLocaleString('nb-NO');
}

// Budget Modal Functions
function openBudgetModal(section, category, month) {
    currentCell = { section, category, month, type: 'budget' };
    const yearData = getCurrentYearData();

    const modal = new bootstrap.Modal(document.getElementById('budgetModal'));
    document.getElementById('budgetModalTitle').textContent =
        `${category} - Budget - ${month}`;

    const currentValue = yearData[section][category].budget[month] || 0;
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
    const yearData = getCurrentYearData();

    yearData[section][category].budget[month] = amount;

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
    const yearData = getCurrentYearData();
    const transactions = yearData[section][category].result[month];

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
                        ${t.payee ? `<div class="transaction-payee"><i class="bi bi-person"></i> ${t.payee}</div>` : ''}
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
    const budget = yearData[section][category].budget[month] || 0;
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

    // Set default date to current month of selected year
    const monthIndex = months.indexOf(currentCell.month);
    const defaultDate = new Date(currentYear, monthIndex, 1);
    document.getElementById('transactionDate').value = defaultDate.toISOString().split('T')[0];

    // Reset and populate payee dropdown
    if (payeeSelect) {
        payeeSelect.clear();
        payeeSelect.clearOptions();
        payees.forEach(payee => {
            payeeSelect.addOption({value: payee, text: payee});
        });
    }

    const modal = new bootstrap.Modal(document.getElementById('addTransactionModal'));
    modal.show();
}

function editTransaction(index) {
    currentTransactionIndex = index;
    const { section, category, month } = currentCell;
    const yearData = getCurrentYearData();
    const transaction = yearData[section][category].result[month][index];

    document.getElementById('addTransactionTitle').textContent = 'Edit transaction';

    // Set badges
    document.getElementById('addModalCategory').textContent = category;
    document.getElementById('addModalMonth').textContent = month;

    document.getElementById('transactionDate').value = transaction.date;
    document.getElementById('transactionAmount').value = transaction.amount;
    document.getElementById('transactionComment').value = transaction.comment || '';

    // Set payee dropdown
    if (payeeSelect) {
        payeeSelect.clear();
        payeeSelect.clearOptions();
        payees.forEach(payee => {
            payeeSelect.addOption({value: payee, text: payee});
        });
        if (transaction.payee) {
            payeeSelect.setValue(transaction.payee);
        }
    }

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
    const yearData = getCurrentYearData();
    yearData[section][category].result[month].splice(index, 1);

    displayTransactions();
    generateTable(); // Refresh table to update totals
}

function saveTransaction() {
    const date = document.getElementById('transactionDate').value;
    const amount = parseFloat(document.getElementById('transactionAmount').value);
    const payee = payeeSelect ? payeeSelect.getValue() : '';
    const comment = document.getElementById('transactionComment').value;

    if (!date || isNaN(amount)) {
        alert('Please fill in all required fields');
        return;
    }

    const transaction = { date, amount, payee, comment };
    const { section, category, month } = currentCell;
    const yearData = getCurrentYearData();

    if (currentTransactionIndex !== null) {
        // Edit existing transaction
        yearData[section][category].result[month][currentTransactionIndex] = transaction;
    } else {
        // Add new transaction
        yearData[section][category].result[month].push(transaction);
    }

    // Update payees list if new payee was added
    if (payee && !payees.includes(payee)) {
        payees.push(payee);
        payees.sort();
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

// Initialize Tom Select for payee field
function initializePayeeSelect() {
    const payeeElement = document.getElementById('transactionPayee');
    if (payeeElement && !payeeSelect) {
        payeeSelect = new TomSelect('#transactionPayee', {
            create: true,
            sortField: 'text',
            placeholder: 'Select or add payee...',
            maxOptions: 100,
            onChange: function(value) {
                // Add new payee to the list if not already there
                if (value && !payees.includes(value)) {
                    payees.push(value);
                }
            }
        });
    }
}

// ==================== CONFIG PAGE FUNCTIONS ====================

let currentEditingCategory = null;
let currentEditingPayee = null;

// Populate categories table
function populateCategoriesTable() {
    const tbody = document.querySelector('#categoriesTable tbody');
    if (!tbody) return;

    let html = '';

    // Get all unique categories across income and expenses
    const allCategories = [];

    ['income', 'expenses'].forEach(section => {
        categories[section].forEach(cat => {
            const yearsUsed = getCategoryYearsUsed(section, cat.name);
            allCategories.push({
                name: cat.name,
                type: section,
                yearsUsed: yearsUsed,
                hasData: yearsUsed.length > 0
            });
        });
    });

    allCategories.forEach(cat => {
        const typeBadge = cat.type === 'income'
            ? '<span class="badge bg-success">Income</span>'
            : '<span class="badge bg-warning">Expenses</span>';

        const yearsText = cat.yearsUsed.length > 0
            ? cat.yearsUsed.join(', ')
            : '<span class="text-muted">Not used</span>';

        const deleteBtn = cat.hasData
            ? `<button class="btn btn-sm btn-outline-secondary" disabled title="Cannot delete - category is in use">
                <i class="bi bi-trash"></i>
               </button>`
            : `<button class="btn btn-sm btn-outline-danger" onclick="deleteCategory('${cat.type}', '${cat.name}')">
                <i class="bi bi-trash"></i>
               </button>`;

        html += `
            <tr>
                <td>${cat.name}</td>
                <td>${typeBadge}</td>
                <td>${yearsText}</td>
                <td class="text-end">
                    <button class="btn btn-sm btn-outline-primary me-1" onclick="editCategory('${cat.type}', '${cat.name}')">
                        <i class="bi bi-pencil"></i>
                    </button>
                    ${deleteBtn}
                </td>
            </tr>
        `;
    });

    tbody.innerHTML = html || '<tr><td colspan="4" class="text-center text-muted">No categories yet</td></tr>';
}

// Get years where category has data
function getCategoryYearsUsed(section, categoryName) {
    const yearsWithData = [];

    availableYears.forEach(year => {
        const yearData = budgetData[year];
        if (!yearData || !yearData[section] || !yearData[section][categoryName]) return;

        let hasData = false;

        // Check if budget has non-zero values
        months.forEach(month => {
            if (yearData[section][categoryName].budget[month] > 0) {
                hasData = true;
            }
        });

        // Check if there are any transactions
        months.forEach(month => {
            if (yearData[section][categoryName].result[month].length > 0) {
                hasData = true;
            }
        });

        if (hasData) {
            yearsWithData.push(year);
        }
    });

    return yearsWithData;
}

// Populate payees table
function populatePayeesTable() {
    const tbody = document.querySelector('#payeesTable tbody');
    if (!tbody) return;

    let html = '';

    // Get payee statistics
    const payeeStats = getPayeeStatistics();

    payeeStats.forEach(stat => {
        const lastUsedText = stat.lastUsed
            ? new Date(stat.lastUsed).toLocaleDateString('nb-NO')
            : '<span class="text-muted">Never</span>';

        const deleteBtn = stat.transactionCount > 0
            ? `<button class="btn btn-sm btn-outline-secondary" disabled title="Cannot delete - payee is in use (${stat.transactionCount} transactions)">
                <i class="bi bi-trash"></i>
               </button>`
            : `<button class="btn btn-sm btn-outline-danger" onclick="deletePayee('${stat.name}')">
                <i class="bi bi-trash"></i>
               </button>`;

        html += `
            <tr class="payee-row" data-payee="${stat.name.toLowerCase()}">
                <td>${stat.name}</td>
                <td>${stat.transactionCount}</td>
                <td>${lastUsedText}</td>
                <td class="text-end">
                    <button class="btn btn-sm btn-outline-primary me-1" onclick="editPayee('${stat.name}')">
                        <i class="bi bi-pencil"></i>
                    </button>
                    ${deleteBtn}
                </td>
            </tr>
        `;
    });

    tbody.innerHTML = html || '<tr><td colspan="4" class="text-center text-muted">No payees yet</td></tr>';
}

// Get payee statistics across all years
function getPayeeStatistics() {
    const stats = {};

    availableYears.forEach(year => {
        const yearData = budgetData[year];
        ['income', 'expenses'].forEach(section => {
            Object.keys(yearData[section]).forEach(category => {
                months.forEach(month => {
                    const transactions = yearData[section][category].result[month];
                    transactions.forEach(t => {
                        if (t.payee) {
                            if (!stats[t.payee]) {
                                stats[t.payee] = {
                                    name: t.payee,
                                    transactionCount: 0,
                                    lastUsed: null
                                };
                            }
                            stats[t.payee].transactionCount++;
                            if (!stats[t.payee].lastUsed || t.date > stats[t.payee].lastUsed) {
                                stats[t.payee].lastUsed = t.date;
                            }
                        }
                    });
                });
            });
        });
    });

    return Object.values(stats).sort((a, b) => a.name.localeCompare(b.name));
}

// Filter payees based on search
function filterPayees() {
    const searchTerm = document.getElementById('payeeSearch').value.toLowerCase();
    const rows = document.querySelectorAll('.payee-row');

    rows.forEach(row => {
        const payeeName = row.getAttribute('data-payee');
        if (payeeName.includes(searchTerm)) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}

// Modal functions for categories
function openAddCategoryModal() {
    currentEditingCategory = null;
    document.getElementById('categoryModalTitle').textContent = 'Add Category';
    document.getElementById('categoryName').value = '';
    document.getElementById('categoryType').value = '';

    const modal = new bootstrap.Modal(document.getElementById('categoryModal'));
    modal.show();
}

function editCategory(type, name) {
    currentEditingCategory = { type, name };
    document.getElementById('categoryModalTitle').textContent = 'Edit Category';
    document.getElementById('categoryName').value = name;
    document.getElementById('categoryType').value = type;
    document.getElementById('categoryType').disabled = true; // Can't change type when editing

    const modal = new bootstrap.Modal(document.getElementById('categoryModal'));
    modal.show();
}

function saveCategory() {
    const name = document.getElementById('categoryName').value.trim();
    const type = document.getElementById('categoryType').value;

    if (!name || !type) {
        alert('Please fill in all fields');
        return;
    }

    if (currentEditingCategory) {
        // Editing existing category - rename it across all years
        const oldName = currentEditingCategory.name;

        availableYears.forEach(year => {
            const yearData = budgetData[year];
            if (yearData[type][oldName]) {
                yearData[type][name] = yearData[type][oldName];
                if (name !== oldName) {
                    delete yearData[type][oldName];
                }
            }
        });

        // Update in categories array
        const catArray = categories[type];
        const index = catArray.findIndex(c => c.name === oldName);
        if (index !== -1) {
            catArray[index].name = name;
        }
    } else {
        // Adding new category
        // Check if it already exists
        if (categories[type].find(c => c.name === name)) {
            alert('A category with this name already exists');
            return;
        }

        // Add to categories array
        categories[type].push({ name });

        // Initialize in all years
        availableYears.forEach(year => {
            budgetData[year][type][name] = {
                budget: {},
                result: {}
            };
            months.forEach(month => {
                budgetData[year][type][name].budget[month] = 0;
                budgetData[year][type][name].result[month] = [];
            });
        });
    }

    // Re-enable type dropdown
    document.getElementById('categoryType').disabled = false;

    // Close modal and refresh
    bootstrap.Modal.getInstance(document.getElementById('categoryModal')).hide();
    populateCategoriesTable();

    // Refresh budget table if we're on that page
    if (document.getElementById('budgetTable')) {
        generateTable();
    }
}

function deleteCategory(type, name) {
    if (!confirm(`Are you sure you want to delete the category "${name}"?`)) {
        return;
    }

    // Remove from categories array
    const index = categories[type].findIndex(c => c.name === name);
    if (index !== -1) {
        categories[type].splice(index, 1);
    }

    // Remove from all years
    availableYears.forEach(year => {
        if (budgetData[year][type][name]) {
            delete budgetData[year][type][name];
        }
    });

    populateCategoriesTable();

    // Refresh budget table if we're on that page
    if (document.getElementById('budgetTable')) {
        generateTable();
    }
}

// Modal functions for payees
function openAddPayeeModal() {
    currentEditingPayee = null;
    document.getElementById('payeeModalTitle').textContent = 'Add Payee';
    document.getElementById('payeeName').value = '';

    const modal = new bootstrap.Modal(document.getElementById('payeeModal'));
    modal.show();
}

function editPayee(name) {
    currentEditingPayee = name;
    document.getElementById('payeeModalTitle').textContent = 'Edit Payee';
    document.getElementById('payeeName').value = name;

    const modal = new bootstrap.Modal(document.getElementById('payeeModal'));
    modal.show();
}

function savePayee() {
    const name = document.getElementById('payeeName').value.trim();

    if (!name) {
        alert('Please enter a payee name');
        return;
    }

    if (currentEditingPayee) {
        // Editing - rename across all transactions
        const oldName = currentEditingPayee;

        availableYears.forEach(year => {
            const yearData = budgetData[year];
            ['income', 'expenses'].forEach(section => {
                Object.keys(yearData[section]).forEach(category => {
                    months.forEach(month => {
                        yearData[section][category].result[month].forEach(t => {
                            if (t.payee === oldName) {
                                t.payee = name;
                            }
                        });
                    });
                });
            });
        });

        // Update in payees list
        const index = payees.indexOf(oldName);
        if (index !== -1) {
            payees[index] = name;
            payees.sort();
        }
    } else {
        // Adding new payee
        if (payees.includes(name)) {
            alert('This payee already exists');
            return;
        }

        payees.push(name);
        payees.sort();
    }

    bootstrap.Modal.getInstance(document.getElementById('payeeModal')).hide();
    populatePayeesTable();
}

function deletePayee(name) {
    if (!confirm(`Are you sure you want to delete the payee "${name}"?`)) {
        return;
    }

    const index = payees.indexOf(name);
    if (index !== -1) {
        payees.splice(index, 1);
    }

    populatePayeesTable();
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize if we're on the budget page
    if (document.getElementById('budgetTable')) {
        initializeBudgetData();
        // loadData(); // Uncomment to load from localStorage

        // Populate year selector
        populateYearSelector();

        // Generate table for current year
        generateTable();

        // Initialize Tom Select for payee
        initializePayeeSelect();

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

    // Initialize config page if present
    if (document.getElementById('categoriesTable')) {
        // Initialize budget data if not already done
        if (Object.keys(budgetData).length === 0) {
            initializeBudgetData();
        }
        populateCategoriesTable();
        populatePayeesTable();
    }
});
