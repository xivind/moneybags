/**
 * Moneybags Application JavaScript
 */

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', function() {
    console.log('Moneybags app loaded');

    // Initialize toast container
    initializeToastContainer();
});

/**
 * Format currency based on user preference
 */
function formatCurrency(amount, currency = 'USD') {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: currency
    }).format(amount);
}

/**
 * Debounce function for input fields
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Initialize TomSelect on elements with .tomselect class
 */
function initializeTomSelect() {
    document.querySelectorAll('.tomselect').forEach(function(el) {
        new TomSelect(el, {
            plugins: ['remove_button'],
            create: false
        });
    });
}

/**
 * Initialize Tempus Dominus date pickers
 */
function initializeDatePickers() {
    document.querySelectorAll('.datepicker').forEach(function(el) {
        new tempusDominus.TempusDominus(el, {
            display: {
                components: {
                    clock: false
                }
            }
        });
    });
}

/**
 * Initialize toast container for notifications
 */
function initializeToastContainer() {
    // Create toast container if it doesn't exist
    if (!document.getElementById('toast-container')) {
        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container position-fixed top-0 end-0 p-3';
        container.style.zIndex = '9999';
        document.body.appendChild(container);
    }
}

/**
 * Show a toast notification
 * @param {string} message - The message to display
 * @param {string} type - Type of notification: 'success', 'error', 'warning', 'info'
 * @param {number} duration - Duration in milliseconds (default: 5000)
 */
function showToast(message, type = 'info', duration = 5000) {
    const container = document.getElementById('toast-container');
    if (!container) {
        console.error('Toast container not found');
        return;
    }

    // Create unique ID for this toast
    const toastId = 'toast-' + Date.now();

    // Determine background class and icon
    let bgClass = 'bg-primary';
    let icon = 'ℹ️';

    switch(type) {
        case 'success':
            bgClass = 'bg-success';
            icon = '✓';
            break;
        case 'error':
            bgClass = 'bg-danger';
            icon = '✗';
            break;
        case 'warning':
            bgClass = 'bg-warning';
            icon = '⚠';
            break;
        case 'info':
            bgClass = 'bg-info';
            icon = 'ℹ️';
            break;
    }

    // Create toast HTML
    const toastHTML = `
        <div id="${toastId}" class="toast align-items-center ${bgClass} text-white border-0" role="alert" aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    <span class="me-2">${icon}</span>${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
            </div>
        </div>
    `;

    // Add toast to container
    container.insertAdjacentHTML('beforeend', toastHTML);

    // Initialize and show the toast
    const toastElement = document.getElementById(toastId);
    const toast = new bootstrap.Toast(toastElement, {
        autohide: true,
        delay: duration
    });

    toast.show();

    // Remove toast element after it's hidden
    toastElement.addEventListener('hidden.bs.toast', function() {
        toastElement.remove();
    });
}

/**
 * Handle htmx errors and show toast notifications
 */
document.body.addEventListener('htmx:responseError', function(event) {
    let errorMessage = 'An error occurred';

    // Try to extract error message from response
    if (event.detail.xhr && event.detail.xhr.response) {
        try {
            const response = JSON.parse(event.detail.xhr.response);
            if (response.detail) {
                errorMessage = response.detail;
            }
        } catch (e) {
            // If response is not JSON, try to extract from HTML
            const parser = new DOMParser();
            const doc = parser.parseFromString(event.detail.xhr.response, 'text/html');
            const alertDiv = doc.querySelector('.alert');
            if (alertDiv) {
                errorMessage = alertDiv.textContent.trim();
            }
        }
    }

    showToast(errorMessage, 'error');
});

/**
 * Handle htmx timeout errors
 */
document.body.addEventListener('htmx:timeout', function(event) {
    showToast('Request timed out. Please try again.', 'error');
});

/**
 * Handle successful htmx requests with HX-Trigger header
 */
document.body.addEventListener('htmx:afterRequest', function(event) {
    // Check for success message in response headers
    const successMessage = event.detail.xhr.getResponseHeader('HX-Trigger');
    if (successMessage) {
        try {
            const trigger = JSON.parse(successMessage);
            if (trigger.showToast) {
                showToast(trigger.showToast.message, trigger.showToast.type || 'success');
            }
        } catch (e) {
            // Not JSON, might be a simple trigger name
        }
    }
});

// Reinitialize components after htmx swaps
document.body.addEventListener('htmx:afterSwap', function(event) {
    initializeTomSelect();
    initializeDatePickers();
});

// Make showToast available globally for manual use
window.showToast = showToast;
