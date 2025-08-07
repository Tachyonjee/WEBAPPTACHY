/**
 * API client for Coaching App
 * Centralized API communication with authentication and error handling
 */

class APIClient {
    constructor() {
        this.baseURL = '';
        this.accessToken = localStorage.getItem('access_token');
        this.refreshToken = localStorage.getItem('refresh_token');
        this.isRefreshing = false;
        this.failedQueue = [];
    }
    
    // Set access token
    setAccessToken(token) {
        this.accessToken = token;
        localStorage.setItem('access_token', token);
    }
    
    // Set refresh token
    setRefreshToken(token) {
        this.refreshToken = token;
        localStorage.setItem('refresh_token', token);
    }
    
    // Clear tokens
    clearTokens() {
        this.accessToken = null;
        this.refreshToken = null;
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user_data');
    }
    
    // Get default headers
    getHeaders(includeAuth = true) {
        const headers = {
            'Content-Type': 'application/json'
        };
        
        if (includeAuth && this.accessToken) {
            headers['Authorization'] = `Bearer ${this.accessToken}`;
        }
        
        return headers;
    }
    
    // Handle token refresh
    async refreshAccessToken() {
        if (this.isRefreshing) {
            return new Promise((resolve, reject) => {
                this.failedQueue.push({ resolve, reject });
            });
        }
        
        this.isRefreshing = true;
        
        try {
            const response = await fetch('/api/auth/refresh', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    refresh_token: this.refreshToken
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                this.setAccessToken(data.access_token);
                
                // Process failed queue
                this.failedQueue.forEach(({ resolve }) => resolve(data.access_token));
                this.failedQueue = [];
                
                return data.access_token;
            } else {
                throw new Error('Token refresh failed');
            }
        } catch (error) {
            this.failedQueue.forEach(({ reject }) => reject(error));
            this.failedQueue = [];
            this.clearTokens();
            window.location.href = '/auth/login';
            throw error;
        } finally {
            this.isRefreshing = false;
        }
    }
    
    // Make API request with automatic token refresh
    async request(url, options = {}) {
        const config = {
            ...options,
            headers: {
                ...this.getHeaders(options.auth !== false),
                ...options.headers
            }
        };
        
        try {
            let response = await fetch(`${this.baseURL}${url}`, config);
            
            // If unauthorized and we have a refresh token, try to refresh
            if (response.status === 401 && this.refreshToken && options.auth !== false) {
                await this.refreshAccessToken();
                
                // Retry the original request with new token
                config.headers['Authorization'] = `Bearer ${this.accessToken}`;
                response = await fetch(`${this.baseURL}${url}`, config);
            }
            
            return response;
        } catch (error) {
            // Handle network errors
            if (!navigator.onLine) {
                throw new APIError('Network error - you appear to be offline', 'NETWORK_ERROR');
            }
            throw new APIError('Network error - please check your connection', 'NETWORK_ERROR');
        }
    }
    
    // GET request
    async get(url, params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const fullUrl = queryString ? `${url}?${queryString}` : url;
        
        const response = await this.request(fullUrl);
        return this.handleResponse(response);
    }
    
    // POST request
    async post(url, data = {}) {
        const response = await this.request(url, {
            method: 'POST',
            body: JSON.stringify(data)
        });
        return this.handleResponse(response);
    }
    
    // PUT request
    async put(url, data = {}) {
        const response = await this.request(url, {
            method: 'PUT',
            body: JSON.stringify(data)
        });
        return this.handleResponse(response);
    }
    
    // DELETE request
    async delete(url) {
        const response = await this.request(url, {
            method: 'DELETE'
        });
        return this.handleResponse(response);
    }
    
    // Handle response
    async handleResponse(response) {
        const contentType = response.headers.get('content-type');
        
        if (contentType && contentType.includes('application/json')) {
            const data = await response.json();
            
            if (response.ok) {
                return data;
            } else {
                throw new APIError(
                    data.error || data.message || 'Request failed',
                    'API_ERROR',
                    response.status,
                    data
                );
            }
        } else {
            if (response.ok) {
                return await response.text();
            } else {
                throw new APIError(
                    `HTTP ${response.status} - ${response.statusText}`,
                    'HTTP_ERROR',
                    response.status
                );
            }
        }
    }
    
    // Upload file
    async uploadFile(url, file, additionalData = {}) {
        const formData = new FormData();
        formData.append('file', file);
        
        // Add additional data
        Object.entries(additionalData).forEach(([key, value]) => {
            formData.append(key, value);
        });
        
        const response = await this.request(url, {
            method: 'POST',
            headers: {
                ...this.getHeaders(),
                'Content-Type': undefined // Let browser set multipart boundary
            },
            body: formData
        });
        
        return this.handleResponse(response);
    }
}

// Custom API Error class
class APIError extends Error {
    constructor(message, type = 'API_ERROR', status = null, data = null) {
        super(message);
        this.name = 'APIError';
        this.type = type;
        this.status = status;
        this.data = data;
    }
}

// Create global API client instance
const api = new APIClient();

// API endpoints organized by feature
const API = {
    // Authentication
    auth: {
        sendOTP: (identifier) => api.post('/api/auth/send-otp', { identifier }),
        verifyOTP: (otp_code) => api.post('/api/auth/verify-otp', { otp_code }),
        refresh: () => api.post('/api/auth/refresh'),
        logout: () => api.post('/api/auth/logout')
    },
    
    // Student endpoints
    students: {
        getProfile: () => api.get('/api/students/profile'),
        
        // Practice
        startPractice: (sessionData) => api.post('/api/students/practice/start', sessionData),
        getNextQuestion: (sessionId) => api.get(`/api/students/practice/${sessionId}/next`),
        submitAnswer: (sessionId, answerData) => api.post(`/api/students/practice/${sessionId}/attempt`, answerData),
        endSession: (sessionId) => api.post(`/api/students/practice/${sessionId}/end`),
        
        // Bookmarks
        getBookmarks: (params) => api.get('/api/students/bookmarks', params),
        toggleBookmark: (questionId) => api.post(`/api/students/bookmarks/${questionId}`),
        removeBookmark: (questionId) => api.delete(`/api/students/bookmarks/${questionId}`),
        
        // Doubts
        getDoubts: (params) => api.get('/api/students/doubts', params),
        createDoubt: (doubtData) => api.post('/api/students/doubts', doubtData),
        
        // Progress
        getProgress: (params) => api.get('/api/students/progress', params),
        getRecommendations: (params) => api.get('/api/students/recommendations', params)
    },
    
    // Questions
    questions: {
        getSubjects: () => api.get('/api/questions/subjects'),
        getChapters: (subject) => api.get('/api/questions/chapters', { subject }),
        getTopics: (params) => api.get('/api/questions/topics', params),
        getQuestion: (questionId) => api.get(`/api/questions/${questionId}`),
        getSolution: (questionId, studentId) => api.get(`/api/questions/${questionId}/solution`, { student_id: studentId })
    },
    
    // Operator endpoints
    operators: {
        // Question management
        createQuestion: (questionData) => api.post('/api/questions', questionData),
        updateQuestion: (questionId, questionData) => api.put(`/api/questions/${questionId}`, questionData),
        deleteQuestion: (questionId) => api.delete(`/api/questions/${questionId}`),
        getQuestionBank: (params) => api.get('/api/questions', params),
        
        // Bulk upload
        uploadQuestions: (file, options) => api.uploadFile('/api/questions/bulk-upload', file, options),
        validateFile: (file) => api.uploadFile('/api/questions/validate', file),
        getTemplate: () => api.get('/api/questions/template'),
        
        // Statistics
        getStats: () => api.get('/api/questions/stats')
    }
};

// Offline support
class OfflineManager {
    constructor() {
        this.dbName = 'CoachingAppDB';
        this.dbVersion = 1;
        this.db = null;
        this.init();
    }
    
    async init() {
        try {
            this.db = await this.openDB();
        } catch (error) {
            console.error('Failed to initialize offline database:', error);
        }
    }
    
    openDB() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(this.dbName, this.dbVersion);
            
            request.onerror = () => reject(request.error);
            request.onsuccess = () => resolve(request.result);
            
            request.onupgradeneeded = () => {
                const db = request.result;
                
                // Create stores for offline data
                if (!db.objectStoreNames.contains('offlineAnswers')) {
                    db.createObjectStore('offlineAnswers', { keyPath: 'id', autoIncrement: true });
                }
                
                if (!db.objectStoreNames.contains('offlineDoubts')) {
                    db.createObjectStore('offlineDoubts', { keyPath: 'id', autoIncrement: true });
                }
                
                if (!db.objectStoreNames.contains('cachedQuestions')) {
                    db.createObjectStore('cachedQuestions', { keyPath: 'id' });
                }
            };
        });
    }
    
    async storeOfflineAnswer(sessionId, questionId, chosenAnswer, timeTaken) {
        if (!this.db) return;
        
        const answerData = {
            sessionId,
            questionId,
            chosenAnswer,
            timeTaken,
            timestamp: Date.now(),
            token: api.accessToken
        };
        
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['offlineAnswers'], 'readwrite');
            const store = transaction.objectStore('offlineAnswers');
            const request = store.add(answerData);
            
            request.onerror = () => reject(request.error);
            request.onsuccess = () => {
                resolve(request.result);
                
                // Register background sync if available
                if ('serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype) {
                    navigator.serviceWorker.ready.then(registration => {
                        registration.sync.register('offline-answer-submission');
                    });
                }
            };
        });
    }
    
    async storeOfflineDoubt(questionId, message) {
        if (!this.db) return;
        
        const doubtData = {
            questionId,
            message,
            timestamp: Date.now(),
            token: api.accessToken
        };
        
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['offlineDoubts'], 'readwrite');
            const store = transaction.objectStore('offlineDoubts');
            const request = store.add(doubtData);
            
            request.onerror = () => reject(request.error);
            request.onsuccess = () => {
                resolve(request.result);
                
                // Register background sync if available
                if ('serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype) {
                    navigator.serviceWorker.ready.then(registration => {
                        registration.sync.register('offline-doubt-submission');
                    });
                }
            };
        });
    }
}

// Create offline manager instance
const offlineManager = new OfflineManager();

// Enhanced API with offline support
const enhancedAPI = {
    ...API,
    
    students: {
        ...API.students,
        
        async submitAnswer(sessionId, answerData) {
            try {
                return await API.students.submitAnswer(sessionId, answerData);
            } catch (error) {
                if (error.type === 'NETWORK_ERROR') {
                    // Store offline for later sync
                    await offlineManager.storeOfflineAnswer(
                        sessionId,
                        answerData.question_id,
                        answerData.chosen_answer,
                        answerData.time_taken
                    );
                    
                    // Return offline response
                    return {
                        offline: true,
                        message: 'Answer saved offline. Will sync when connection is restored.'
                    };
                }
                throw error;
            }
        },
        
        async createDoubt(doubtData) {
            try {
                return await API.students.createDoubt(doubtData);
            } catch (error) {
                if (error.type === 'NETWORK_ERROR') {
                    // Store offline for later sync
                    await offlineManager.storeOfflineDoubt(
                        doubtData.question_id,
                        doubtData.message
                    );
                    
                    // Return offline response
                    return {
                        offline: true,
                        message: 'Doubt saved offline. Will sync when connection is restored.'
                    };
                }
                throw error;
            }
        }
    }
};

// Global error handler for API errors
window.addEventListener('unhandledrejection', function(event) {
    if (event.reason instanceof APIError) {
        console.error('Unhandled API Error:', event.reason);
        
        // Show user-friendly error message
        if (window.PWA && window.PWA.showToast) {
            const message = event.reason.type === 'NETWORK_ERROR' 
                ? 'Connection error. Please check your internet connection.'
                : event.reason.message;
            
            window.PWA.showToast(message, 'error');
        }
        
        event.preventDefault();
    }
});

// Export for global use
window.API = enhancedAPI;
window.APIClient = APIClient;
window.APIError = APIError;
window.offlineManager = offlineManager;