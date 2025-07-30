/**
 * Marina Web Client - Common JavaScript Functions
 * 
 * This file contains common utility functions used across the web client.
 */

// Global variables
let sessionInfo = null;

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    loadSessionInfo();
    setupActiveNavigation();
});

/**
 * Load session information and update UI
 */
async function loadSessionInfo() {
    try {
        const response = await fetch('/api/session/info');
        sessionInfo = await response.json();
        
        // Update session indicator
        const sessionIndicator = document.getElementById('session-indicator');
        if (sessionIndicator && sessionInfo.session_id) {
            sessionIndicator.textContent = sessionInfo.session_id;
        }
    } catch (error) {
        console.error('Failed to load session info:', error);
        const sessionIndicator = document.getElementById('session-indicator');
        if (sessionIndicator) {
            sessionIndicator.textContent = 'Error';
        }
    }
}

/**
 * Set active navigation item based on current page
 */
function setupActiveNavigation() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        } else {
            link.classList.remove('active');
        }
    });
}

/**
 * Show alert message to user
 * @param {string} message - The message to display
 * @param {string} type - Alert type (success, danger, warning, info)
 * @param {number} duration - Auto-hide duration in milliseconds (0 = no auto-hide)
 */
function addAlert(message, type = 'info', duration = 5000) {
    const alertContainer = document.getElementById('alert-container');
    if (!alertContainer) return;
    
    // Create alert element
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.setAttribute('role', 'alert');
    
    // Choose icon based on type
    let icon = 'fas fa-info-circle';
    switch (type) {
        case 'success':
            icon = 'fas fa-check-circle';
            break;
        case 'danger':
            icon = 'fas fa-exclamation-circle';
            break;
        case 'warning':
            icon = 'fas fa-exclamation-triangle';
            break;
    }
    
    alertDiv.innerHTML = `
        <i class="${icon}"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    // Add to container
    alertContainer.appendChild(alertDiv);
    
    // Auto-hide if duration is set
    if (duration > 0) {
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.classList.remove('show');
                setTimeout(() => {
                    if (alertDiv.parentNode) {
                        alertDiv.remove();
                    }
                }, 150);
            }
        }, duration);
    }
}

/**
 * Show loading state on button
 * @param {HTMLElement} button - Button element
 * @param {boolean} loading - Whether to show loading state
 */
function setButtonLoading(button, loading) {
    if (loading) {
        button.classList.add('loading');
        button.disabled = true;
    } else {
        button.classList.remove('loading');
        button.disabled = false;
    }
}

/**
 * Format file size in human readable format
 * @param {number} bytes - File size in bytes
 * @returns {string} Formatted file size
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Format date in human readable format
 * @param {string} dateString - ISO date string
 * @returns {string} Formatted date
 */
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

/**
 * Copy text to clipboard
 * @param {string} text - Text to copy
 * @returns {Promise<boolean>} Success status
 */
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        addAlert('Copied to clipboard!', 'success', 2000);
        return true;
    } catch (error) {
        console.error('Failed to copy to clipboard:', error);
        addAlert('Failed to copy to clipboard', 'danger', 3000);
        return false;
    }
}

/**
 * Debounce function calls
 * @param {Function} func - Function to debounce
 * @param {number} wait - Wait time in milliseconds
 * @returns {Function} Debounced function
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
 * Throttle function calls
 * @param {Function} func - Function to throttle
 * @param {number} limit - Time limit in milliseconds
 * @returns {Function} Throttled function
 */
function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

/**
 * Escape HTML to prevent XSS
 * @param {string} text - Text to escape
 * @returns {string} Escaped text
 */
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

/**
 * Make API request with error handling
 * @param {string} url - API endpoint
 * @param {Object} options - Fetch options
 * @returns {Promise<Object>} API response
 */
async function apiRequest(url, options = {}) {
    try {
        const response = await fetch(url, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        return await response.json();
    } catch (error) {
        console.error('API request failed:', error);
        addAlert(`API request failed: ${error.message}`, 'danger');
        throw error;
    }
}

/**
 * Download file from blob
 * @param {Blob} blob - File blob
 * @param {string} filename - Filename for download
 */
function downloadBlob(blob, filename) {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}

/**
 * Check if element is in viewport
 * @param {HTMLElement} element - Element to check
 * @returns {boolean} Whether element is in viewport
 */
function isElementInViewport(element) {
    const rect = element.getBoundingClientRect();
    return (
        rect.top >= 0 &&
        rect.left >= 0 &&
        rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
        rect.right <= (window.innerWidth || document.documentElement.clientWidth)
    );
}

/**
 * Scroll element into view smoothly
 * @param {HTMLElement} element - Element to scroll to
 */
function scrollToElement(element) {
    element.scrollIntoView({
        behavior: 'smooth',
        block: 'center'
    });
}

/**
 * Get session storage item with JSON parsing
 * @param {string} key - Storage key
 * @returns {*} Parsed value or null
 */
function getSessionStorage(key) {
    try {
        const item = sessionStorage.getItem(key);
        return item ? JSON.parse(item) : null;
    } catch (error) {
        console.error('Failed to parse session storage item:', error);
        return null;
    }
}

/**
 * Set session storage item with JSON stringification
 * @param {string} key - Storage key
 * @param {*} value - Value to store
 */
function setSessionStorage(key, value) {
    try {
        sessionStorage.setItem(key, JSON.stringify(value));
    } catch (error) {
        console.error('Failed to set session storage item:', error);
    }
}

/**
 * Clear all alerts
 */
function clearAlerts() {
    const alertContainer = document.getElementById('alert-container');
    if (alertContainer) {
        alertContainer.innerHTML = '';
    }
}

/**
 * Handle form submission with loading state
 * @param {HTMLFormElement} form - Form element
 * @param {Function} handler - Submit handler function
 */
function handleFormSubmit(form, handler) {
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const submitButton = form.querySelector('button[type="submit"]');
        if (submitButton) {
            setButtonLoading(submitButton, true);
        }
        
        try {
            await handler(e);
        } catch (error) {
            console.error('Form submission failed:', error);
            addAlert(`Error: ${error.message}`, 'danger');
        } finally {
            if (submitButton) {
                setButtonLoading(submitButton, false);
            }
        }
    });
}

/**
 * Initialize tooltips (if Bootstrap is available)
 */
function initializeTooltips() {
    if (typeof bootstrap !== 'undefined' && bootstrap.Tooltip) {
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }
}

/**
 * Initialize the common functionality
 */
function initializeCommon() {
    initializeTooltips();
    
    // Set up global error handler
    window.addEventListener('error', function(e) {
        console.error('Global error:', e.error);
        addAlert('An unexpected error occurred. Please refresh the page.', 'danger');
    });
    
    // Set up unhandled promise rejection handler
    window.addEventListener('unhandledrejection', function(e) {
        console.error('Unhandled promise rejection:', e.reason);
        addAlert('An unexpected error occurred. Please try again.', 'danger');
    });
}

// Initialize common functionality when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeCommon);
} else {
    initializeCommon();
}
