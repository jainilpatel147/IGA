/**
 * API Client
 * Centralized API calls to the IGA backend
 * Uses the unified request wrapper from ./request.js
 */

import api from './request';

// ============================================
// Identity API
// ============================================

export async function getIdentities() {
  return api.get('/identities');
}

export async function createIdentity(data) {
  return api.post('/identities', data);
}

// ============================================
// Access Request API
// ============================================

export async function getAccessRequests(status = null, tenantId = null) {
  const queryParams = new URLSearchParams();
  if (status) queryParams.append('status', status);
  if (tenantId) queryParams.append('tenant_id', tenantId);
  
  const queryString = queryParams.toString() ? `?${queryParams.toString()}` : '';
  return api.get(`/access/requests${queryString}`);
}

export async function createAccessRequest(data) {
  return api.post('/access/request', data);
}

export async function approveRequest(requestId, reason = null) {
  return api.post(`/access/approve/${requestId}`, { reason });
}

export async function rejectRequest(requestId, reason = null) {
  return api.post(`/access/reject/${requestId}`, { reason });
}

// ============================================
// Audit API
// ============================================

export async function getAuditEvents(eventType = null) {
  const params = eventType ? `?event_type=${eventType}` : '';
  return api.get(`/audit/events${params}`);
}

// ============================================
// Health API
// ============================================

export async function healthCheck() {
  return api.get('/health');
}
