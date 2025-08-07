/**
 * Progressive Web App (PWA) functionality
 */

let deferredPrompt;
let isInstalled = false;

// PWA Installation
window.addEventListener('beforeinstallprompt', (e) => {
    // Prevent Chrome 67 and earlier from automatically showing the prompt
    e.preventDefault();
    // Stash the event so it can be triggered later
    deferredPrompt = e;
    
    // Show the install banner
    const installBanner = document.getElementById('pwa-install-banner');
    if (installBanner) {
        installBanner.classList.remove('d-none');
    }
});

// Install button click handler
document.addEventListener('DOMContentLoaded', function() {
    const installBtn = document.getElementById('pwa-install-btn');
    if (installBtn) {
        installBtn.addEventListener('click', async () => {
            if (deferredPrompt) {
                // Show the install prompt
                deferredPrompt.prompt();
                
                // Wait for the user to respond to the prompt
                const { outcome } = await deferredPrompt.userChoice;
                
                if (outcome === 'accepted') {
                    console.log('User accepted the install prompt');
                    // Hide the install banner
                    const installBanner = document.getElementById('pwa-install-banner');
                    if (installBanner) {
                        installBanner.classList.add('d-none');
                    }
                }
                
                // Clear the prompt
                deferredPrompt = null;
            }
        });
    }
});

// Handle app installation
window.addEventListener('appinstalled', (evt) => {
    console.log('App was installed');
    isInstalled = true;
    
    // Hide the install banner
    const installBanner = document.getElementById('pwa-install-banner');
    if (installBanner) {
        installBanner.classList.add('d-none');
    }
    
    // Track installation analytics
    if (typeof gtag !== 'undefined') {
        gtag('event', 'app_installed', {
            event_category: 'PWA'
        });
    }
});

// Service Worker Registration
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        navigator.serviceWorker.register('/static/sw.js')
            .then(function(registration) {
                console.log('ServiceWorker registration successful');
                
                // Check for updates
                registration.addEventListener('updatefound', () => {
                    const newWorker = registration.installing;
                    newWorker.addEventListener('statechange', () => {
                        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                            // New update available
                            showUpdateNotification();
                        }
                    });
                });
            })
            .catch(function(registrationError) {
                console.log('ServiceWorker registration failed: ', registrationError);
            });
    });
}

// Update notification
function showUpdateNotification() {
    if (Notification.permission === 'granted') {
        new Notification('App Update Available', {
            body: 'A new version of the app is available. Please refresh to update.',
            icon: '/static/icons/icon-192x192.png',
            badge: '/static/icons/badge-72x72.png'
        });
    }
}

// Network status handling
window.addEventListener('online', function() {
    showToast('Connection restored', 'success');
});

window.addEventListener('offline', function() {
    showToast('You are now offline. Some features may be limited.', 'warning');
});

// Utility function for toasts
function showToast(message, type = 'info') {
    const toastContainer = document.getElementById('toast-container') || createToastContainer();
    
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">${message}</div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    toastContainer.appendChild(toast);
    
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    // Remove toast after it's hidden
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    container.style.zIndex = '1055';
    document.body.appendChild(container);
    return container;
}

// Screen orientation lock for practice mode
function lockOrientation() {
    if (screen.orientation && screen.orientation.lock) {
        screen.orientation.lock('portrait').catch(err => {
            console.log('Orientation lock not supported:', err);
        });
    }
}

function unlockOrientation() {
    if (screen.orientation && screen.orientation.unlock) {
        screen.orientation.unlock();
    }
}

// Export functions for use in other scripts
window.PWA = {
    lockOrientation,
    unlockOrientation,
    showToast,
    isInstalled: () => isInstalled
};