/**
 * Centralized API Client
 * 
 * Usage:
 * import api from './request';
 * 
 * const data = await api.get('/tenants');
 * await api.post('/users', { name: 'John' });
 */

// API Base URL Configuration
// - Local dev: set VITE_API_URL=http://localhost:8000 in .env
// - Docker/Prod: defaults to '/api' which Nginx proxies to backend
const API_BASE = (import.meta.env.VITE_API_URL || '/api').replace(/\/$/, '');

class ApiClient {
    constructor() {
        this.base = API_BASE;
    }

    /**
     * Get the current auth token from storage
     */
    getToken() {
        return localStorage.getItem('iga-token');
    }

    /**
     * Unified request handler
     */
    async request(method, endpoint, data = null, customHeaders = {}) {
        // Ensure endpoint starts with /
        const path = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
        const url = `${this.base}${path}`;

        const headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            ...customHeaders
        };

        // Auto-inject Auth Token
        const token = this.getToken();
        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const config = {
            method,
            headers,
        };

        if (data) {
            config.body = JSON.stringify(data);
        }

        try {
            const response = await fetch(url, config);

            // Handle 401 Unauthorized globally
            if (response.status === 401) {
                // Optional: Trigger global logout or redirect
                // window.location.href = '/login';
                localStorage.removeItem('iga-token');
                throw new Error('Session expired. Please login again.');
            }

            // Parse JSON response
            // Handle 204 No Content
            if (response.status === 204) {
                return null;
            }

            const result = await response.json().catch(() => ({}));

            if (!response.ok) {
                throw new Error(result.detail || result.message || `API Error ${response.status}`);
            }

            return result;
        } catch (error) {
            console.error(`API Request Failed: [${method}] ${path}`, error);
            throw error;
        }
    }

    // Convenience methods
    get(endpoint, headers = {}) {
        return this.request('GET', endpoint, null, headers);
    }

    post(endpoint, data, headers = {}) {
        return this.request('POST', endpoint, data, headers);
    }

    put(endpoint, data, headers = {}) {
        return this.request('PUT', endpoint, data, headers);
    }

    patch(endpoint, data, headers = {}) {
        return this.request('PATCH', endpoint, data, headers);
    }

    delete(endpoint, headers = {}) {
        return this.request('DELETE', endpoint, null, headers);
    }
}

const api = new ApiClient();
export default api;
