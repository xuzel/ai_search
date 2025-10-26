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
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 1rem 1.5rem;
            background-color: var(--accent-warm);
            color: white;
            border-radius: var(--radius-md);
            box-shadow: var(--shadow-lg);
            z-index: 9999;
            animation: slideIn 0.3s ease;
        `;

        document.body.appendChild(toast);

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
