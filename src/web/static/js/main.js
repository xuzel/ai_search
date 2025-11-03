/**
 * Main JavaScript file for AI Search Engine Web UI
 */

// Utility Functions
const utils = {
    /**
     * Escape HTML to prevent XSS
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    },

    /**
     * Copy text to clipboard
     */
    async copyToClipboard(text) {
        try {
            await navigator.clipboard.writeText(text);
            return true;
        } catch (err) {
            console.error('Failed to copy:', err);
            return false;
        }
    },

    /**
     * Show toast notification
     */
    showToast(message, type = 'info') {
        const toastContainer = document.getElementById('toastContainer') || document.body;
        const toast = document.createElement('div');
        toast.className = `toast`;

        // Set background color based on type
        let bgColor = 'var(--color-primary)';
        let icon = 'ℹ️';
        if (type === 'success') {
            bgColor = 'var(--color-success)';
            icon = '✅';
        } else if (type === 'danger' || type === 'error') {
            bgColor = 'var(--color-danger)';
            icon = '❌';
        } else if (type === 'warning') {
            bgColor = 'var(--color-warning)';
            icon = '⚠️';
        }

        toast.innerHTML = `
            <div style="display: flex; align-items: center; gap: var(--space-2);">
                <span>${icon}</span>
                <span>${message}</span>
            </div>
        `;
        toast.style.cssText = `
            min-width: 300px;
            padding: var(--space-4);
            background-color: ${bgColor};
            color: white;
            border-radius: var(--radius-lg);
            box-shadow: var(--shadow-lg);
            animation: slideIn 0.3s ease;
            margin-bottom: var(--space-3);
        `;

        toastContainer.appendChild(toast);

        setTimeout(() => {
            toast.style.animation = 'slideOut 0.3s ease';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    },

    /**
     * Format timestamp
     */
    formatTimestamp(timestamp) {
        const date = new Date(timestamp);
        return date.toLocaleString();
    }
};

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', function() {
    console.log('AI Search Engine Web UI loaded');

    // Add HTMX event listeners
    document.body.addEventListener('htmx:configRequest', function(evt) {
        console.log('HTMX request:', evt.detail);
    });

    document.body.addEventListener('htmx:afterSwap', function(evt) {
        console.log('HTMX swap completed:', evt.detail);
    });

    document.body.addEventListener('htmx:responseError', function(evt) {
        console.error('HTMX error:', evt.detail);
        utils.showToast('Request failed. Please try again.', 'error');
    });
});

// Make utils available globally
window.utils = utils;

// Add CSS animations
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from {
            transform: translateX(100%);
            opacity: 0;
        }
        to {
            transform: translateX(0);
            opacity: 1;
        }
    }

    @keyframes slideOut {
        from {
            transform: translateX(0);
            opacity: 1;
        }
        to {
            transform: translateX(100%);
            opacity: 0;
        }
    }

    .htmx-indicator {
        display: none;
    }

    .htmx-request .htmx-indicator {
        display: block;
    }

    .htmx-request.htmx-indicator {
        display: block;
    }
`;
document.head.appendChild(style);
