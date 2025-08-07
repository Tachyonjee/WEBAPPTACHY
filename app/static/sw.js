/**
 * Service Worker for Coaching App PWA
 */

const CACHE_NAME = 'coaching-app-v1';
const DYNAMIC_CACHE = 'coaching-app-dynamic-v1';

// Files to cache immediately
const STATIC_ASSETS = [
    '/',
    '/static/css/styles.css',
    '/static/js/pwa.js',
    '/static/js/practice.js',
    '/static/js/charts.js',
    '/static/manifest.json',
    'https://cdn.replit.com/agent/bootstrap-agent-dark-theme.min.css',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js',
    'https://cdn.jsdelivr.net/npm/chart.js'
];

// Install event - cache static assets
self.addEventListener('install', event => {
    console.log('Service Worker installing...');
    
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('Caching static assets');
                return cache.addAll(STATIC_ASSETS);
            })
            .then(() => {
                console.log('Static assets cached successfully');
                return self.skipWaiting();
            })
            .catch(error => {
                console.error('Error caching static assets:', error);
            })
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
    console.log('Service Worker activating...');
    
    event.waitUntil(
        caches.keys()
            .then(cacheNames => {
                return Promise.all(
                    cacheNames.map(cacheName => {
                        if (cacheName !== CACHE_NAME && cacheName !== DYNAMIC_CACHE) {
                            console.log('Deleting old cache:', cacheName);
                            return caches.delete(cacheName);
                        }
                    })
                );
            })
            .then(() => {
                console.log('Old caches cleaned up');
                return self.clients.claim();
            })
    );
});

// Fetch event - serve from cache, fallback to network
self.addEventListener('fetch', event => {
    const { request } = event;
    const url = new URL(request.url);
    
    // Skip cross-origin requests
    if (url.origin !== location.origin) {
        return;
    }
    
    // API requests - network first, cache as fallback
    if (url.pathname.startsWith('/api/')) {
        event.respondWith(networkFirstStrategy(request));
        return;
    }
    
    // Static assets - cache first
    if (isStaticAsset(url.pathname)) {
        event.respondWith(cacheFirstStrategy(request));
        return;
    }
    
    // Pages - stale while revalidate
    if (isPageRequest(request)) {
        event.respondWith(staleWhileRevalidateStrategy(request));
        return;
    }
    
    // Default to network first
    event.respondWith(networkFirstStrategy(request));
});

// Cache first strategy (for static assets)
async function cacheFirstStrategy(request) {
    try {
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        
        const networkResponse = await fetch(request);
        
        // Cache successful responses
        if (networkResponse.status === 200) {
            const cache = await caches.open(CACHE_NAME);
            cache.put(request, networkResponse.clone());
        }
        
        return networkResponse;
    } catch (error) {
        console.error('Cache first strategy failed:', error);
        return new Response('Offline - Asset not available', { status: 503 });
    }
}

// Network first strategy (for API requests)
async function networkFirstStrategy(request) {
    try {
        const networkResponse = await fetch(request);
        
        // Cache successful GET requests
        if (request.method === 'GET' && networkResponse.status === 200) {
            const cache = await caches.open(DYNAMIC_CACHE);
            cache.put(request, networkResponse.clone());
        }
        
        return networkResponse;
    } catch (error) {
        console.log('Network failed, trying cache:', error);
        
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        
        // Return offline response for API requests
        if (request.url.includes('/api/')) {
            return new Response(
                JSON.stringify({
                    error: 'Offline - Please check your connection',
                    offline: true
                }),
                {
                    status: 503,
                    headers: { 'Content-Type': 'application/json' }
                }
            );
        }
        
        return new Response('Offline - Please check your connection', { status: 503 });
    }
}

// Stale while revalidate strategy (for pages)
async function staleWhileRevalidateStrategy(request) {
    const cache = await caches.open(DYNAMIC_CACHE);
    const cachedResponse = await cache.match(request);
    
    const fetchPromise = fetch(request).then(networkResponse => {
        if (networkResponse.status === 200) {
            cache.put(request, networkResponse.clone());
        }
        return networkResponse;
    }).catch(error => {
        console.log('Network request failed:', error);
        return cachedResponse || new Response('Offline', { status: 503 });
    });
    
    return cachedResponse || fetchPromise;
}

// Helper functions
function isStaticAsset(pathname) {
    return pathname.startsWith('/static/') || 
           pathname.endsWith('.css') || 
           pathname.endsWith('.js') || 
           pathname.endsWith('.png') || 
           pathname.endsWith('.jpg') || 
           pathname.endsWith('.svg');
}

function isPageRequest(request) {
    return request.method === 'GET' && 
           request.headers.get('accept').includes('text/html');
}

// Background sync for offline actions
self.addEventListener('sync', event => {
    console.log('Background sync triggered:', event.tag);
    
    if (event.tag === 'offline-answer-submission') {
        event.waitUntil(syncOfflineAnswers());
    }
    
    if (event.tag === 'offline-doubt-submission') {
        event.waitUntil(syncOfflineDoubts());
    }
});

// Sync offline answer submissions
async function syncOfflineAnswers() {
    try {
        const db = await openDB();
        const offlineAnswers = await getOfflineAnswers(db);
        
        for (const answer of offlineAnswers) {
            try {
                await submitAnswerToServer(answer);
                await removeOfflineAnswer(db, answer.id);
                console.log('Synced offline answer:', answer.id);
            } catch (error) {
                console.error('Failed to sync answer:', answer.id, error);
            }
        }
    } catch (error) {
        console.error('Background sync failed:', error);
    }
}

// Sync offline doubt submissions
async function syncOfflineDoubts() {
    try {
        const db = await openDB();
        const offlineDoubts = await getOfflineDoubts(db);
        
        for (const doubt of offlineDoubts) {
            try {
                await submitDoubtToServer(doubt);
                await removeOfflineDoubt(db, doubt.id);
                console.log('Synced offline doubt:', doubt.id);
            } catch (error) {
                console.error('Failed to sync doubt:', doubt.id, error);
            }
        }
    } catch (error) {
        console.error('Background sync failed:', error);
    }
}

// IndexedDB operations (simplified)
async function openDB() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open('CoachingAppDB', 1);
        
        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve(request.result);
        
        request.onupgradeneeded = () => {
            const db = request.result;
            
            if (!db.objectStoreNames.contains('offlineAnswers')) {
                db.createObjectStore('offlineAnswers', { keyPath: 'id', autoIncrement: true });
            }
            
            if (!db.objectStoreNames.contains('offlineDoubts')) {
                db.createObjectStore('offlineDoubts', { keyPath: 'id', autoIncrement: true });
            }
        };
    });
}

async function getOfflineAnswers(db) {
    return new Promise((resolve, reject) => {
        const transaction = db.transaction(['offlineAnswers'], 'readonly');
        const store = transaction.objectStore('offlineAnswers');
        const request = store.getAll();
        
        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve(request.result);
    });
}

async function getOfflineDoubts(db) {
    return new Promise((resolve, reject) => {
        const transaction = db.transaction(['offlineDoubts'], 'readonly');
        const store = transaction.objectStore('offlineDoubts');
        const request = store.getAll();
        
        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve(request.result);
    });
}

async function removeOfflineAnswer(db, id) {
    return new Promise((resolve, reject) => {
        const transaction = db.transaction(['offlineAnswers'], 'readwrite');
        const store = transaction.objectStore('offlineAnswers');
        const request = store.delete(id);
        
        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve();
    });
}

async function removeOfflineDoubt(db, id) {
    return new Promise((resolve, reject) => {
        const transaction = db.transaction(['offlineDoubts'], 'readwrite');
        const store = transaction.objectStore('offlineDoubts');
        const request = store.delete(id);
        
        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve();
    });
}

async function submitAnswerToServer(answer) {
    const response = await fetch(`/api/students/practice/${answer.sessionId}/attempt`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${answer.token}`
        },
        body: JSON.stringify({
            question_id: answer.questionId,
            chosen_answer: answer.chosenAnswer,
            time_taken: answer.timeTaken
        })
    });
    
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
    }
    
    return response.json();
}

async function submitDoubtToServer(doubt) {
    const response = await fetch('/api/students/doubts', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${doubt.token}`
        },
        body: JSON.stringify({
            question_id: doubt.questionId,
            message: doubt.message
        })
    });
    
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
    }
    
    return response.json();
}

// Push notification handling
self.addEventListener('push', event => {
    console.log('Push notification received:', event);
    
    const options = {
        body: 'You have new updates in your coaching app!',
        icon: '/static/icons/icon-192x192.png',
        badge: '/static/icons/badge-72x72.png',
        tag: 'coaching-app-notification',
        data: {
            url: '/'
        }
    };
    
    if (event.data) {
        const data = event.data.json();
        options.body = data.body || options.body;
        options.data.url = data.url || options.data.url;
    }
    
    event.waitUntil(
        self.registration.showNotification('Coaching App', options)
    );
});

// Notification click handling
self.addEventListener('notificationclick', event => {
    console.log('Notification clicked:', event);
    
    event.notification.close();
    
    const url = event.notification.data.url || '/';
    
    event.waitUntil(
        clients.matchAll({ type: 'window' }).then(clientList => {
            // Check if a window is already open
            for (const client of clientList) {
                if (client.url === url && 'focus' in client) {
                    return client.focus();
                }
            }
            
            // Open new window
            if (clients.openWindow) {
                return clients.openWindow(url);
            }
        })
    );
});

console.log('Service Worker loaded successfully');