/**
 * Moneybags Application JavaScript
 */

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', function() {
    console.log('Moneybags app loaded');
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

// Reinitialize components after htmx swaps
document.body.addEventListener('htmx:afterSwap', function(event) {
    initializeTomSelect();
    initializeDatePickers();
});
