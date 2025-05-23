/**
 * Common JavaScript functions for Radio Automation System
 * This file provides fallbacks and common functionality
 */

// Check if jQuery is loaded, provide fallback
if (typeof jQuery === 'undefined') {
    console.warn('jQuery not loaded, some features may not work properly');
    // Create a simple jQuery-like selector function
    window.$ = function(selector) {
        if (typeof selector === 'function') {
            // Document ready fallback
            if (document.readyState === 'loading') {
                document.addEventListener('DOMContentLoaded', selector);
            } else {
                selector();
            }
            return;
        }
        return document.querySelector(selector);
    };
    window.$.ajax = function(options) {
        // Simple AJAX fallback using fetch
        return fetch(options.url, {
            method: options.method || 'GET',
            headers: options.contentType ? {'Content-Type': options.contentType} : {},
            body: options.data ? JSON.stringify(options.data) : null
        })
        .then(response => response.json())
        .then(data => {
            if (options.success) options.success(data);
        })
        .catch(error => {
            if (options.error) options.error(error);
        });
    };
}

// Common utility functions
const RadioAutomation = {
    // Initialize tooltips (Bootstrap 5)
    initTooltips: function() {
        if (typeof bootstrap !== 'undefined') {
            const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
            tooltipTriggerList.map(function (tooltipTriggerEl) {
                return new bootstrap.Tooltip(tooltipTriggerEl);
            });
        }
    },

    // Auto-dismiss alerts
    initAlerts: function() {
        setTimeout(function() {
            const alerts = document.querySelectorAll('.alert');
            alerts.forEach(function(alert) {
                if (typeof jQuery !== 'undefined') {
                    $(alert).fadeOut('slow');
                } else {
                    alert.style.transition = 'opacity 0.5s';
                    alert.style.opacity = '0';
                    setTimeout(() => alert.remove(), 500);
                }
            });
        }, 5000);
    },

    // Format file size
    formatFileSize: function(bytes) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    },

    // Format duration
    formatDuration: function(seconds) {
        if (!seconds || seconds < 0) return 'Unknown';
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        
        if (hours > 0) {
            return `${hours}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        } else {
            return `${minutes}:${secs.toString().padStart(2, '0')}`;
        }
    },

    // Parse filename
    parseFilename: function(filename, callback) {
        fetch('/api/parse-filename', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({filename: filename})
        })
        .then(response => response.json())
        .then(result => callback(result))
        .catch(error => {
            console.error('Error parsing filename:', error);
            callback({show_name: null, date: null, error: error.message});
        });
    },

    // Show loading spinner
    showLoading: function(message) {
        const existingModal = document.getElementById('loadingModal');
        if (existingModal) {
            existingModal.remove();
        }

        const modalHtml = `
            <div class="modal fade" id="loadingModal" tabindex="-1" data-bs-backdrop="static">
                <div class="modal-dialog modal-sm">
                    <div class="modal-content">
                        <div class="modal-body text-center">
                            <div class="spinner-border text-primary mb-3" role="status">
                                <span class="visually-hidden">Loading...</span>
                            </div>
                            <p>${message || 'Processing...'}</p>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.body.insertAdjacentHTML('beforeend', modalHtml);
        
        if (typeof bootstrap !== 'undefined') {
            const modal = new bootstrap.Modal(document.getElementById('loadingModal'));
            modal.show();
        }
    },

    // Hide loading spinner
    hideLoading: function() {
        const modal = document.getElementById('loadingModal');
        if (modal && typeof bootstrap !== 'undefined') {
            const bsModal = bootstrap.Modal.getInstance(modal);
            if (bsModal) {
                bsModal.hide();
            }
        }
    },

    // Show toast notification
    showToast: function(message, type = 'info') {
        const toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            const container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'position-fixed bottom-0 end-0 p-3';
            container.style.zIndex = '11';
            document.body.appendChild(container);
        }

        const toastId = 'toast-' + Date.now();
        const toastHtml = `
            <div id="${toastId}" class="toast align-items-center text-white bg-${type} border-0" role="alert">
                <div class="d-flex">
                    <div class="toast-body">
                        ${message}
                    </div>
                    <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
                </div>
            </div>
        `;
        
        document.getElementById('toast-container').insertAdjacentHTML('beforeend', toastHtml);
        
        if (typeof bootstrap !== 'undefined') {
            const toast = new bootstrap.Toast(document.getElementById(toastId));
            toast.show();
        }
    },

    // Confirm dialog
    confirm: function(message, onConfirm, onCancel) {
        if (typeof bootstrap !== 'undefined') {
            // Use Bootstrap modal for better UX
            const modalHtml = `
                <div class="modal fade" id="confirmModal" tabindex="-1">
                    <div class="modal-dialog">
                        <div class="modal-content">
                            <div class="modal-header">
                                <h5 class="modal-title">Confirm Action</h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                            </div>
                            <div class="modal-body">
                                <p>${message}</p>
                            </div>
                            <div class="modal-footer">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                                <button type="button" class="btn btn-primary" id="confirmBtn">Confirm</button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            
            document.body.insertAdjacentHTML('beforeend', modalHtml);
            const modal = new bootstrap.Modal(document.getElementById('confirmModal'));
            
            document.getElementById('confirmBtn').onclick = function() {
                modal.hide();
                if (onConfirm) onConfirm();
                document.getElementById('confirmModal').remove();
            };
            
            document.getElementById('confirmModal').addEventListener('hidden.bs.modal', function() {
                document.getElementById('confirmModal').remove();
            });
            
            modal.show();
        } else {
            // Fallback to native confirm
            if (confirm(message)) {
                if (onConfirm) onConfirm();
            } else {
                if (onCancel) onCancel();
            }
        }
    }
};

// Initialize common features when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    RadioAutomation.initTooltips();
    RadioAutomation.initAlerts();
});

// Export for use in other scripts
window.RadioAutomation = RadioAutomation;