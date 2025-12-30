// ==================== IMPORT PAGE ====================
//
// Import page JavaScript - handles file upload, category mapping, validation, and import execution.
// This file is only loaded on the import page.
//
// Dependencies from app.js:
// - showToast(message, type)
// - showSuccessModal(title, message)
// - confirmModal (element)
// - currentYear (global variable)

// Global state for import workflow
let parsedData = null;
let categoryMapping = {};
let existingCategories = [];

// Initialize import page
async function initImportPage() {
    if (!document.getElementById('upload-form')) return;

    // Set current year in input field
    const yearInput = document.getElementById('year-input');
    if (yearInput) {
        yearInput.value = currentYear; // Uses the global currentYear variable
    }

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

    // Add change listeners to highlight duplicates in real-time
    const selects = container.querySelectorAll('.category-mapping');
    selects.forEach(select => {
        select.addEventListener('change', highlightDuplicateMappings);
    });

    document.getElementById('mapping-section').classList.remove('d-none');
}

function highlightDuplicateMappings() {
    const selects = document.querySelectorAll('.category-mapping');
    const selectedValues = {};

    // Count occurrences of each selected value
    selects.forEach(select => {
        if (select.value) {
            selectedValues[select.value] = (selectedValues[select.value] || 0) + 1;
        }
    });

    // Highlight duplicates
    selects.forEach(select => {
        if (select.value && selectedValues[select.value] > 1) {
            select.classList.add('border-danger');
            select.classList.add('border-2');
        } else {
            select.classList.remove('border-danger');
            select.classList.remove('border-2');
        }
    });
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

    // Check for duplicate mappings
    const mappedCategories = Object.values(categoryMapping);
    const uniqueMapped = new Set(mappedCategories);
    if (mappedCategories.length !== uniqueMapped.size) {
        // Find which categories are duplicated
        const counts = {};
        const duplicates = [];
        mappedCategories.forEach(catId => {
            counts[catId] = (counts[catId] || 0) + 1;
            if (counts[catId] === 2) {
                // Find the category name
                const category = existingCategories.find(c => c.id === catId);
                if (category) {
                    duplicates.push(category.name);
                }
            }
        });
        showToast(`Duplicate mapping detected: ${duplicates.join(', ')} is mapped multiple times. Each Moneybags category can only be used once.`, 'danger');
        return;
    }

    // Debug logging
    console.log('=== VALIDATION DEBUG ===');
    console.log('parsedData:', parsedData);
    console.log('categoryMapping:', categoryMapping);
    console.log('parsedData is null?', parsedData === null);
    console.log('categoryMapping is empty?', Object.keys(categoryMapping).length === 0);

    // Validate data exists
    if (!parsedData) {
        console.error('ERROR: parsedData is null or undefined');
        showToast('Error: No parsed data available. Please upload and parse a file first.', 'danger');
        return;
    }

    if (Object.keys(categoryMapping).length === 0) {
        console.error('ERROR: categoryMapping is empty');
        showToast('Error: No category mappings defined.', 'danger');
        return;
    }

    // Show loading
    const validateBtn = document.getElementById('validate-btn');
    const spinner = document.getElementById('validate-spinner');
    validateBtn.disabled = true;
    spinner.classList.remove('d-none');

    try {
        const payload = {
            parsed_data: parsedData,
            category_mapping: categoryMapping
        };

        console.log('Sending validation request with payload:', JSON.stringify(payload, null, 2));

        const response = await fetch('/api/import/validate', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });

        console.log('Validation response status:', response.status);
        console.log('Validation response headers:', response.headers);

        const result = await response.json();
        console.log('Validation response data:', result);

        if (result.success) {
            showValidationResults(result.data);
        } else {
            console.error('Validation failed:', result.error);
            showToast(result.error, 'danger');
        }
    } catch (error) {
        console.error('Validation error:', error);
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
    // Get validation summary data
    const validationResults = document.getElementById('validation-results');
    const summaryText = validationResults.textContent;

    // Extract budget and transaction counts from validation results
    const budgetMatch = summaryText.match(/(\d+)\s+budget entries/);
    const transactionMatch = summaryText.match(/(\d+)\s+transactions/);

    const budgetCount = budgetMatch ? budgetMatch[1] : '?';
    const transactionCount = transactionMatch ? transactionMatch[1] : '?';

    // Build confirmation message HTML
    const summaryHtml = `
        <p><strong>Are you sure you want to import this data?</strong></p>
        <p class="mb-0">This will create:</p>
        <ul>
            <li><strong>${budgetCount}</strong> budget entries</li>
            <li><strong>${transactionCount}</strong> transactions</li>
        </ul>
        <p class="text-muted mb-0"><small>This action cannot be undone.</small></p>
    `;

    // Set modal content
    document.getElementById('confirmModalTitle').textContent = 'Confirm Import';
    document.getElementById('confirmModalMessage').innerHTML = summaryHtml;

    // Attach one-time click handler to confirm button
    const confirmActionBtn = document.getElementById('confirmActionBtn');
    const handleConfirm = async function() {
        const importBtn = document.getElementById('import-btn');
        const spinner = document.getElementById('import-spinner');
        const modal = bootstrap.Modal.getInstance(document.getElementById('confirmModal'));

        // Close modal
        modal.hide();

        // Show loading
        importBtn.disabled = true;
        spinner.classList.remove('d-none');

        try {
            console.log('Sending import request with:', {
                parsed_data: parsedData,
                category_mapping: categoryMapping
            });

            const response = await fetch('/api/import/execute', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    parsed_data: parsedData,
                    category_mapping: categoryMapping
                })
            });

            console.log('Import response status:', response.status);
            const result = await response.json();
            console.log('Import response data:', result);

            if (result.success) {
                // Build success message HTML
                const templateMsg = result.data.template_count > 0
                    ? `<li><strong>${result.data.template_count}</strong> categories added to budget template</li>`
                    : '';

                const message = `
                    <p class="mb-3">Import completed successfully!</p>
                    <ul class="mb-0">
                        <li><strong>${result.data.budget_count}</strong> budget entries imported</li>
                        <li><strong>${result.data.transaction_count}</strong> transactions imported</li>
                        ${templateMsg}
                    </ul>
                `;

                showSuccessModal('Import Complete', message);

                // Reload page when modal is closed
                const successModal = document.getElementById('successModal');
                successModal.addEventListener('hidden.bs.modal', () => {
                    location.reload();
                }, { once: true });
            } else {
                console.error('Import failed:', result.error);
                showToast(result.error || 'Import failed', 'danger');
                importBtn.disabled = false;
            }
        } catch (error) {
            console.error('Import error:', error);
            showToast('Error executing import: ' + error.message, 'danger');
            importBtn.disabled = false;
        } finally {
            spinner.classList.add('d-none');
        }

        // Remove this listener after execution
        confirmActionBtn.removeEventListener('click', handleConfirm);
    };

    // Add the listener
    confirmActionBtn.addEventListener('click', handleConfirm);

    // Show confirmation modal
    const modal = new bootstrap.Modal(document.getElementById('confirmModal'));
    modal.show();
}

// Auto-initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initImportPage);
} else {
    // DOMContentLoaded already fired
    initImportPage();
}
