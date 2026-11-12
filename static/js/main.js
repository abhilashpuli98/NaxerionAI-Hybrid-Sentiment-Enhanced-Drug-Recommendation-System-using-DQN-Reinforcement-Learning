/* SEDRS JavaScript - Main Utilities and API Client */

class SEDRSClient {
    constructor(baseURL = '/api') {
        this.baseURL = baseURL;
        this.timeout = 30000;
    }

    /**
     * Make API request with error handling
     */
    async request(method, endpoint, data = null, options = {}) {
        const url = `${this.baseURL}${endpoint}`;
        const config = {
            method,
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
                ...options.headers
            },
            timeout: options.timeout || this.timeout
        };

        if (data && method !== 'GET') {
            config.body = JSON.stringify(data);
        }

        try {
            const response = await fetch(url, config);
            const contentType = response.headers.get('content-type');

            let responseData;
            if (contentType && contentType.includes('application/json')) {
                responseData = await response.json();
            } else {
                responseData = await response.text();
            }

            if (!response.ok) {
                throw new Error(responseData.error || `HTTP ${response.status}`);
            }

            return { success: true, data: responseData, status: response.status };
        } catch (error) {
            console.error(`API Error (${method} ${endpoint}):`, error);
            return { success: false, error: error.message, status: 0 };
        }
    }

    // Patient endpoints
    async getPatient(patientId) {
        return this.request('GET', `/patients/${patientId}`);
    }

    async updatePatient(patientId, data) {
        return this.request('PUT', `/patients/${patientId}`, data);
    }

    async createPatient(data) {
        return this.request('POST', '/patients', data);
    }

    // Analysis endpoints
    async analyzeInput(formData) {
        const response = await fetch(`${this.baseURL}/analyze`, {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        return { success: response.ok, data, status: response.status };
    }

    async getInteraction(interactionId) {
        return this.request('GET', `/interactions/${interactionId}`);
    }

    async getPatientHistory(patientId, page = 1, perPage = 10) {
        return this.request('GET', `/patients/${patientId}/history?page=${page}&per_page=${perPage}`);
    }

    // Recommendation endpoints
    async submitFeedback(recommendationId, feedback) {
        return this.request('POST', `/recommendations/${recommendationId}/feedback`, feedback);
    }

    // Metrics endpoints
    async getMetrics() {
        return this.request('GET', '/metrics');
    }

    // Audit endpoints
    async getAuditLogs(page = 1, perPage = 50) {
        return this.request('GET', `/audit-logs?page=${page}&per_page=${perPage}`);
    }
}

// Global client instance
const sedrsClient = new SEDRSClient('/api');

/**
 * Show notification toast
 */
function showNotification(message, type = 'info', duration = 5000) {
    const toastHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        </div>
    `;

    const container = document.querySelector('.container-fluid');
    if (container) {
        const toastElement = document.createElement('div');
        toastElement.innerHTML = toastHtml;
        container.insertBefore(toastElement.firstElementChild, container.firstChild);

        if (duration > 0) {
            setTimeout(() => {
                document.querySelector('.alert')?.remove();
            }, duration);
        }
    }
}

/**
 * Format number to percentage
 */
function formatPercent(value, decimals = 1) {
    return (value * 100).toFixed(decimals) + '%';
}

/**
 * Format number with decimals
 */
function formatNumber(value, decimals = 2) {
    return parseFloat(value).toFixed(decimals);
}

/**
 * Format date
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
 * File upload with preview
 */
class FileUploader {
    constructor(inputSelector, previewSelector, options = {}) {
        this.input = document.querySelector(inputSelector);
        this.preview = document.querySelector(previewSelector);
        this.options = {
            maxSize: 50 * 1024 * 1024,
            allowedTypes: ['audio/wav', 'audio/mp3', 'image/jpeg', 'image/png'],
            ...options
        };

        if (this.input) {
            this.input.addEventListener('change', (e) => this.handleFileSelect(e));
        }
    }

    handleFileSelect(event) {
        const file = event.target.files[0];
        if (!file) return;

        // Validate file size
        if (file.size > this.options.maxSize) {
            showNotification(`File is too large (max ${this.options.maxSize / 1024 / 1024}MB)`, 'danger');
            return;
        }

        // Validate file type
        if (!this.options.allowedTypes.includes(file.type)) {
            showNotification('File type not allowed', 'danger');
            return;
        }

        this.displayPreview(file);
    }

    displayPreview(file) {
        if (!this.preview) return;

        if (file.type.startsWith('audio/')) {
            this.preview.innerHTML = `
                <div class="alert alert-info">
                    <i class="fas fa-music"></i> ${file.name}
                    <small class="d-block">${(file.size / 1024).toFixed(2)} KB</small>
                </div>
                <audio controls class="w-100">
                    <source src="${URL.createObjectURL(file)}" type="${file.type}">
                </audio>
            `;
        } else if (file.type.startsWith('image/')) {
            this.preview.innerHTML = `
                <div class="alert alert-info">
                    <i class="fas fa-image"></i> ${file.name}
                </div>
                <img src="${URL.createObjectURL(file)}" class="img-fluid rounded" style="max-height: 300px;">
            `;
        }
    }
}

/**
 * Loading spinner
 */
function showLoading(container, message = 'Loading...') {
    const html = `
        <div class="text-center py-5">
            <div class="spinner-border text-primary mb-3"></div>
            <p class="text-muted">${message}</p>
        </div>
    `;
    container.innerHTML = html;
}

/**
 * Format confidence score with visual indicator
 */
function getConfidenceColor(score) {
    if (score >= 0.8) return 'success';
    if (score >= 0.6) return 'info';
    if (score >= 0.4) return 'warning';
    return 'danger';
}

/**
 * Create progress badge
 */
function createProgressBadge(value, label) {
    const percentage = (value * 100).toFixed(1);
    const color = getConfidenceColor(value);
    return `
        <div class="progress" style="height: 24px;">
            <div class="progress-bar bg-${color}" role="progressbar" 
                 style="width: ${percentage}%" aria-valuenow="${percentage}">
                ${percentage}%
            </div>
        </div>
    `;
}

/**
 * Debounce function
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
 * Initialize tooltips and popovers
 */
function initializeBootstrapComponents() {
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

/**
 * Setup CSRF token for AJAX requests
 */
function setupCSRFToken() {
    const token = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
    if (token) {
        // Add to all fetch requests automatically
        const originalFetch = window.fetch;
        window.fetch = function (...args) {
            const [resource, config] = args;
            config = config || {};
            config.headers = config.headers || {};
            config.headers['X-CSRF-Token'] = token;
            return originalFetch.apply(this, [resource, config]);
        };
    }
}

/**
 * DOM Content Loaded - Initialize
 */
document.addEventListener('DOMContentLoaded', function () {
    initializeBootstrapComponents();
    setupCSRFToken();

    // Remove alerts after 5 seconds
    document.querySelectorAll('.alert').forEach(alert => {
        if (!alert.querySelector('.btn-close')) {
            setTimeout(() => {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }, 5000);
        }
    });
});

/**
 * Handle form submission with loading state
 */
function handleFormSubmit(form, submitCallback) {
    form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const submitBtn = form.querySelector('[type="submit"]');
        const originalText = submitBtn.textContent;

        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Processing...';

        try {
            await submitCallback(form);
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        }
    });
}

/**
 * Export utilities
 */
/**
 * Modern Toast Notification System
 */
function showToast(message, type = 'info', duration = 5000) {
    let container = document.getElementById('toastContainer');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toastContainer';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    const icons = {
        success: 'fas fa-check-circle',
        danger: 'fas fa-exclamation-circle',
        warning: 'fas fa-exclamation-triangle',
        info: 'fas fa-info-circle'
    };

    const toast = document.createElement('div');
    toast.className = `sedrs-toast toast-${type}`;
    toast.innerHTML = `
        <i class="${icons[type] || icons.info}"></i>
        <span>${message}</span>
        <button class="toast-close" onclick="this.parentElement.remove()">
            <i class="fas fa-times"></i>
        </button>
    `;

    container.appendChild(toast);

    if (duration > 0) {
        setTimeout(() => {
            toast.style.animation = 'toastSlideOut 0.3s ease-in forwards';
            setTimeout(() => toast.remove(), 300);
        }, duration);
    }

    return toast;
}

/**
 * Dark Mode Toggle
 */
function initDarkMode() {
    const savedTheme = localStorage.getItem('sedrs-theme');
    if (savedTheme) {
        document.documentElement.setAttribute('data-theme', savedTheme);
    }

    const toggleBtn = document.getElementById('themeToggle');
    if (toggleBtn) {
        updateThemeIcon(toggleBtn);
        toggleBtn.addEventListener('click', () => {
            const current = document.documentElement.getAttribute('data-theme');
            const newTheme = current === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('sedrs-theme', newTheme);
            updateThemeIcon(toggleBtn);
        });
    }
}

function updateThemeIcon(btn) {
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    btn.innerHTML = isDark
        ? '<i class="fas fa-sun"></i>'
        : '<i class="fas fa-moon"></i>';
    btn.title = isDark ? 'Switch to light mode' : 'Switch to dark mode';
}

/**
 * Back to Top Button
 */
function initBackToTop() {
    const btn = document.getElementById('backToTop');
    if (!btn) return;

    window.addEventListener('scroll', debounce(() => {
        if (window.scrollY > 300) {
            btn.classList.add('visible');
        } else {
            btn.classList.remove('visible');
        }
    }, 100));

    btn.addEventListener('click', () => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
}

/**
 * Scroll Reveal Animation (IntersectionObserver)
 */
function initScrollReveal() {
    const reveals = document.querySelectorAll('.reveal');
    if (reveals.length === 0) return;

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('active');
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });

    reveals.forEach(el => observer.observe(el));
}

/**
 * Keyboard Shortcuts
 */
function initKeyboardShortcuts() {
    document.addEventListener('keydown', (e) => {
        // Ctrl+Shift combinations
        if (e.ctrlKey && e.shiftKey) {
            switch (e.key.toUpperCase()) {
                case 'A': // Analyze
                    e.preventDefault();
                    const analyzeLink = document.querySelector('a[href*="analyze"]');
                    if (analyzeLink) analyzeLink.click();
                    break;
                case 'D': // Dashboard
                    e.preventDefault();
                    const dashLink = document.querySelector('a[href*="dashboard"]');
                    if (dashLink) dashLink.click();
                    break;
                case 'H': // History
                    e.preventDefault();
                    const histLink = document.querySelector('a[href*="history"]');
                    if (histLink) histLink.click();
                    break;
            }
        }
    });
}

/**
 * Session Timeout Warning
 */
function initSessionTimeout() {
    let timeout;
    const TIMEOUT_MS = 25 * 60 * 1000; // 25 minutes

    function resetTimer() {
        clearTimeout(timeout);
        timeout = setTimeout(showSessionWarning, TIMEOUT_MS);
    }

    function showSessionWarning() {
        // Only warn if user is logged in (check for logout link)
        if (!document.querySelector('a[href*="logout"]')) return;

        const overlay = document.createElement('div');
        overlay.className = 'session-warning-overlay';
        overlay.innerHTML = `
            <div class="session-warning-card">
                <i class="fas fa-clock text-warning" style="font-size:2.5rem;"></i>
                <h5 class="mt-3">Session Expiring</h5>
                <p class="text-muted">Your session will expire soon due to inactivity.</p>
                <div class="d-flex gap-2 justify-content-center">
                    <button class="btn btn-primary" onclick="this.closest('.session-warning-overlay').remove()">
                        <i class="fas fa-redo me-1"></i>Stay Logged In
                    </button>
                    <a href="/logout" class="btn btn-outline-secondary">
                        <i class="fas fa-sign-out-alt me-1"></i>Logout
                    </a>
                </div>
            </div>
        `;
        document.body.appendChild(overlay);
    }

    ['mousemove', 'keypress', 'click', 'scroll'].forEach(event => {
        document.addEventListener(event, debounce(resetTimer, 1000), { passive: true });
    });

    resetTimer();
}

/**
 * Password Strength Meter
 */
function initPasswordStrength() {
    const pwdInput = document.getElementById('password');
    const strengthBar = document.querySelector('.password-strength-bar .strength-fill');
    const strengthText = document.querySelector('.password-strength-text');

    if (!pwdInput || !strengthBar) return;

    pwdInput.addEventListener('input', () => {
        const val = pwdInput.value;
        let score = 0;
        if (val.length >= 6) score++;
        if (val.length >= 10) score++;
        if (/[A-Z]/.test(val)) score++;
        if (/[0-9]/.test(val)) score++;
        if (/[^A-Za-z0-9]/.test(val)) score++;

        strengthBar.className = 'strength-fill';
        if (strengthText) strengthText.textContent = '';

        if (val.length === 0) return;

        if (score <= 1) {
            strengthBar.classList.add('weak');
            if (strengthText) { strengthText.textContent = 'Weak'; strengthText.style.color = '#ef4444'; }
        } else if (score === 2) {
            strengthBar.classList.add('fair');
            if (strengthText) { strengthText.textContent = 'Fair'; strengthText.style.color = '#f59e0b'; }
        } else if (score === 3) {
            strengthBar.classList.add('good');
            if (strengthText) { strengthText.textContent = 'Good'; strengthText.style.color = '#0ea5e9'; }
        } else {
            strengthBar.classList.add('strong');
            if (strengthText) { strengthText.textContent = 'Strong'; strengthText.style.color = '#10b981'; }
        }
    });
}

/**
 * Confirm Password Match
 */
function initConfirmPassword() {
    const pwd = document.getElementById('password');
    const confirm = document.getElementById('confirm_password');
    const matchIndicator = document.getElementById('passwordMatchIndicator');

    if (!pwd || !confirm || !matchIndicator) return;

    function checkMatch() {
        if (confirm.value.length === 0) {
            matchIndicator.textContent = '';
            return;
        }
        if (pwd.value === confirm.value) {
            matchIndicator.innerHTML = '<i class="fas fa-check-circle text-success me-1"></i>Passwords match';
            matchIndicator.style.color = '#10b981';
        } else {
            matchIndicator.innerHTML = '<i class="fas fa-times-circle text-danger me-1"></i>Passwords do not match';
            matchIndicator.style.color = '#ef4444';
        }
    }

    confirm.addEventListener('input', checkMatch);
    pwd.addEventListener('input', checkMatch);
}

/**
 * Show/Hide Password Toggle
 */
function initPasswordToggle() {
    document.querySelectorAll('.password-toggle-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const input = btn.closest('.input-group').querySelector('input');
            const icon = btn.querySelector('i');
            if (input.type === 'password') {
                input.type = 'text';
                icon.classList.replace('fa-eye', 'fa-eye-slash');
            } else {
                input.type = 'password';
                icon.classList.replace('fa-eye-slash', 'fa-eye');
            }
        });
    });
}

/**
 * Animated Counter
 */
function animateCounters() {
    document.querySelectorAll('.counter-value').forEach(el => {
        const target = parseInt(el.getAttribute('data-target')) || 0;
        const duration = 1500;
        const step = Math.ceil(target / (duration / 16));
        let current = 0;

        function update() {
            current += step;
            if (current >= target) {
                el.textContent = formatNumber(target);
                return;
            }
            el.textContent = formatNumber(current);
            requestAnimationFrame(update);
        }

        const observer = new IntersectionObserver((entries) => {
            if (entries[0].isIntersecting) {
                update();
                observer.unobserve(el);
            }
        });
        observer.observe(el);
    });
}

/**
 * Time-of-Day Greeting
 */
function getGreeting() {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good Morning';
    if (hour < 18) return 'Good Afternoon';
    return 'Good Evening';
}

/**
 * Initialize all enhancements
 */
function initEnhancements() {
    initDarkMode();
    initBackToTop();
    initScrollReveal();
    initKeyboardShortcuts();
    initSessionTimeout();
    initPasswordStrength();
    initPasswordToggle();
    initConfirmPassword();
    animateCounters();

    // Auto-set greeting if element exists
    const greetEl = document.getElementById('timeGreeting');
    if (greetEl) greetEl.textContent = getGreeting();
}

// Run enhancements on DOMContentLoaded
document.addEventListener('DOMContentLoaded', initEnhancements);

// ========================
// PHASE 2 — PREMIUM JS
// ========================

/**
 * Typewriter effect – types out text character by character.
 */
function typewriterEffect(element, text, speed = 60) {
    if (!element) return;
    element.textContent = '';
    const cursor = document.createElement('span');
    cursor.className = 'typewriter-cursor';
    element.appendChild(cursor);

    let i = 0;
    function type() {
        if (i < text.length) {
            element.insertBefore(document.createTextNode(text.charAt(i)), cursor);
            i++;
            setTimeout(type, speed);
        } else {
            setTimeout(() => cursor.remove(), 2000);
        }
    }
    type();
}

/**
 * Smooth page transitions – fade out before navigation.
 */
function initPageTransitions() {
    document.querySelectorAll('a[href]').forEach(link => {
        const href = link.getAttribute('href');
        // Only transition for internal links, not anchors, javascript:, or new tabs
        if (!href || href.startsWith('#') || href.startsWith('javascript:') ||
            link.target === '_blank' || link.hasAttribute('download') ||
            link.closest('.dropdown-menu')) return;

        link.addEventListener('click', function (e) {
            // Skip if modifier keys held
            if (e.ctrlKey || e.metaKey || e.shiftKey) return;
            e.preventDefault();
            document.body.classList.add('page-exit');
            setTimeout(() => {
                window.location.href = href;
            }, 250);
        });
    });
}

/**
 * Table search – live filter rows based on search input.
 */
function initTableSearch() {
    document.querySelectorAll('[data-table-search]').forEach(input => {
        const tableId = input.getAttribute('data-table-search');
        const table = document.getElementById(tableId);
        if (!table) return;

        input.addEventListener('input', debounce(() => {
            const query = input.value.toLowerCase();
            table.querySelectorAll('tbody tr').forEach(row => {
                const text = row.textContent.toLowerCase();
                row.style.display = text.includes(query) ? '' : 'none';
            });
        }, 200));
    });
}

/**
 * CSV Export – export visible table rows to CSV.
 */
function exportTableCSV(tableId, filename = 'export.csv') {
    const table = document.getElementById(tableId);
    if (!table) return;

    const rows = [];
    // Header
    const headers = Array.from(table.querySelectorAll('thead th')).map(th => th.textContent.trim());
    rows.push(headers.join(','));

    // Rows (only visible)
    table.querySelectorAll('tbody tr').forEach(row => {
        if (row.style.display === 'none') return;
        const cells = Array.from(row.querySelectorAll('td')).map(td => {
            let text = td.textContent.trim().replace(/,/g, ';').replace(/\n/g, ' ');
            return `"${text}"`;
        });
        rows.push(cells.join(','));
    });

    const csvContent = rows.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);

    if (typeof showToast === 'function') {
        showToast(`Exported ${rows.length - 1} records to CSV`, 'success', 3000);
    }
}

/**
 * Generate floating hero particles.
 */
function initHeroParticles() {
    const container = document.querySelector('.hero-particles');
    if (!container) return;

    for (let i = 0; i < 20; i++) {
        const dot = document.createElement('div');
        dot.className = 'dot';
        dot.style.left = Math.random() * 100 + '%';
        dot.style.bottom = '-10px';
        dot.style.animationDuration = (5 + Math.random() * 10) + 's';
        dot.style.animationDelay = (Math.random() * 8) + 's';
        dot.style.width = dot.style.height = (4 + Math.random() * 6) + 'px';
        container.appendChild(dot);
    }
}

/**
 * ARIA accessibility – add labels to interactive elements missing them.
 */
function initAccessibility() {
    // Add aria-label to icon-only buttons
    document.querySelectorAll('button:not([aria-label])').forEach(btn => {
        if (btn.textContent.trim() === '' && btn.querySelector('i')) {
            const icon = btn.querySelector('i');
            const classes = icon.className;
            if (classes.includes('fa-eye')) btn.setAttribute('aria-label', 'Toggle password visibility');
            else if (classes.includes('fa-moon') || classes.includes('fa-sun'))
                btn.setAttribute('aria-label', 'Toggle dark mode');
            else if (classes.includes('fa-chevron-up')) btn.setAttribute('aria-label', 'Back to top');
        }
    });

    // Add role="img" to decorative icons inside links
    document.querySelectorAll('.nav-link i, .btn i').forEach(icon => {
        icon.setAttribute('aria-hidden', 'true');
    });
}

// Call phase 2 inits on DOMContentLoaded
document.addEventListener('DOMContentLoaded', function () {
    initPageTransitions();
    initTableSearch();
    initHeroParticles();
    initAccessibility();
});

/**
 * Global SEDRS namespace – expose all public utilities.
 */
window.SEDRS = {
    client: sedrsClient,
    showNotification,
    showToast,
    formatPercent,
    formatNumber,
    formatDate,
    FileUploader,
    showLoading,
    getConfidenceColor,
    createProgressBadge,
    debounce,
    initializeBootstrapComponents,
    setupCSRFToken,
    handleFormSubmit,
    getGreeting,
    animateCounters,
    typewriterEffect,
    initTableSearch,
    exportTableCSV,
    initHeroParticles,
    initAccessibility
};
