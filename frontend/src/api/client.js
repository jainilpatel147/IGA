/**
 * API Client
 * Centralized API calls to the IGA backend
 */

// In Docker: Nginx proxies API requests to backend (no CORS needed)
// For local dev: set VITE_API_URL=http://localhost:8000 in .env
const API_BASE = import.meta.env.VITE_API_URL || '';

/**
 * Generic fetch wrapper with error handling
 */
async function fetchAPI(endpoint, options = {}) {
  const url = `${API_BASE}${endpoint}`;
  
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
  };

  try {
    const response = await fetch(url, config);
    
    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error(`API Error [${endpoint}]:`, error);
    throw error;
  }
}

// ============================================
// Identity API
// ============================================

export async function getIdentities() {
  return fetchAPI('/identities');
}

export async function createIdentity(data) {
  return fetchAPI('/identities', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

// ============================================
// Access Request API
// ============================================

export async function getAccessRequests(status = null) {
  const params = status ? `?status=${status}` : '';
  return fetchAPI(`/access/requests${params}`);
}

export async function createAccessRequest(data) {
  return fetchAPI('/access/request', {
    method: 'POST',
    body: JSON.stringify(data),
  });
}

export async function approveRequest(requestId, reason = null) {
  return fetchAPI(`/access/approve/${requestId}`, {
    method: 'POST',
    body: JSON.stringify({ reason }),
  });
}

export async function rejectRequest(requestId, reason = null) {
  return fetchAPI(`/access/reject/${requestId}`, {
    method: 'POST',
    body: JSON.stringify({ reason }),
  });
}

// ============================================
// Audit API
// ============================================

export async function getAuditEvents(eventType = null) {
  const params = eventType ? `?event_type=${eventType}` : '';
  return fetchAPI(`/audit/events${params}`);
}

// ============================================
// Health API
// ============================================

export async function healthCheck() {
  return fetchAPI('/health');
}
