/**
 * AuthentiQ Frontend API Client
 * Connects frontend UI to real FastAPI backend endpoints at /api/v1.
 */

const API_BASE = import.meta.env.VITE_API_URL || '/api/v1'

// Local demo token generated for reviewer/admin role to allow instant out-of-the-box local testing
const DEFAULT_DEMO_TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c3JfcmV2aWV3ZXJfMDEiLCJpYXQiOjE3OTMxMDk1NjQsImV4cCI6MjEwODQ2OTU2NCwiZW1haWwiOiJyZXZpZXdlckBjb250ZW50aXEuaW8iLCJuYW1lIjoiTGVhZCBSZXZpZXdlciIsInJvbGUiOiJyZXZpZXdlciJ9.o8yF2MvQt6FExdK-3XQvtLYpSsdfwzi6FjAqFd0043A'

export const tokenStorage = {
  get: () => localStorage.getItem('authentiq_token') || localStorage.getItem('contentiq_token') || DEFAULT_DEMO_TOKEN,
  set: (token) => {
    localStorage.setItem('authentiq_token', token)
    localStorage.setItem('contentiq_token', token)
  },
  clear: () => {
    localStorage.removeItem('authentiq_token')
    localStorage.removeItem('contentiq_token')
  },
}

async function request(endpoint, options = {}) {
  const url = endpoint.startsWith('http') ? endpoint : `${API_BASE}${endpoint}`
  const headers = {
    ...options.headers,
  }

  // Add auth header if not already present
  const token = tokenStorage.get()
  if (token && !headers['Authorization']) {
    headers['Authorization'] = `Bearer ${token}`
  }

  // Do not set Content-Type if FormData (browser sets boundary automatically)
  if (!(options.body instanceof FormData) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json'
  }

  try {
    const res = await fetch(url, { ...options, headers })
    
    // Check if response is JSON
    const contentType = res.headers.get('content-type') || ''
    if (!res.ok) {
      if (contentType.includes('application/json')) {
        const errJson = await res.json()
        const errMsg = errJson?.error?.message || errJson?.detail || errJson?.message || `HTTP ${res.status}`
        throw new Error(errMsg)
      } else {
        const errText = await res.text()
        throw new Error(errText || `HTTP ${res.status} error`)
      }
    }

    if (contentType.includes('application/json')) {
      return await res.json()
    }
    return await res.text()
  } catch (err) {
    console.warn(`[AuthentiQ API] Request to ${endpoint} failed:`, err.message)
    throw err
  }
}

// ── Auth Endpoints ────────────────────────────────────────────────────────────
export const authApi = {
  login: async (email, password) => {
    const data = await request('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    })
    if (data?.data?.access_token) {
      tokenStorage.set(data.data.access_token)
    }
    return data
  },
  register: async (email, password, fullName, role = 'user') => {
    return request('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, full_name: fullName, role }),
    })
  },
  getMe: async () => request('/auth/me'),
  logout: () => tokenStorage.clear(),
}

// ── Dashboard Endpoints ───────────────────────────────────────────────────────
export const dashboardApi = {
  getMetrics: async () => request('/dashboard/metrics'),
  getActivities: async () => request('/dashboard/activities'),
  getCohortDistribution: async () => request('/dashboard/cohort-distribution'),
}

// ── Text Analysis Endpoints ───────────────────────────────────────────────────
export const textAnalysisApi = {
  analyzeText: async (text, options = {}) => {
    return request('/analysis/text', {
      method: 'POST',
      body: JSON.stringify({
        text,
        analysis_types: options.analysisTypes || ['text', 'similarity'],
        model_version: options.modelVersion || 'text-detector-v2.4',
        enable_heatmaps: true,
      }),
    })
  },
}

// ── Media Analysis Endpoints ──────────────────────────────────────────────────
export const mediaAnalysisApi = {
  // Direct file upload endpoint (checks size, magic bytes, storage)
  uploadMedia: async (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return request('/media/upload', {
      method: 'POST',
      body: formData,
    })
  },

  // Submit media job for async celery/background processing
  submitJob: async (uploadId, enabledDetectors = []) => {
    return request('/media/jobs', {
      method: 'POST',
      body: JSON.stringify({
        upload_id: uploadId,
        enabled_detectors: enabledDetectors,
      }),
    })
  },

  // Poll media job status
  getJobStatus: async (jobId) => request(`/media/jobs/${jobId}`),

  // Retrieve media findings and frame anomalies
  getJobResult: async (jobId) => request(`/media/jobs/${jobId}/result`),

  // Delete media job & private upload files
  deleteJob: async (jobId) => request(`/media/jobs/${jobId}`, { method: 'DELETE' }),

  // List configured/unconfigured detector adapters
  getAdapters: async () => request('/media/adapters'),

  // Fallback demo simulator for direct synchronous analysis
  syncAnalyzeMedia: async (detectors) => {
    return request('/analysis/media', {
      method: 'POST',
      body: JSON.stringify({
        media_type: 'video',
        detectors: detectors || ['Face Blend Artifacts', 'Lighting Inconsistency', 'Audio/Video Sync'],
      }),
    })
  },
}

// ── FP/FN Simulator Endpoints ─────────────────────────────────────────────────
export const simulatorApi = {
  simulate: async (threshold, modelVersion = 'v2.4', dataset = 'edu-2400') => {
    return request('/analysis/simulator', {
      method: 'POST',
      body: JSON.stringify({
        threshold,
        model_version: modelVersion,
        dataset,
      }),
    })
  },
}

// ── Shortlisting & Rubrics Endpoints ──────────────────────────────────────────
export const shortlistingApi = {
  getProjects: async () => request('/shortlisting/projects'),
  getSubmissions: async (projectId) => {
    const query = projectId ? `?project_id=${encodeURIComponent(projectId)}` : ''
    return request(`/shortlisting/submissions${query}`)
  },
  updateSubmissionStatus: async (submissionId, status) => {
    return request(`/shortlisting/submissions/${submissionId}/status`, {
      method: 'PATCH',
      body: JSON.stringify({ status }),
    })
  },
  getRubrics: async () => request('/rubrics'),
  createRubric: async (data) => {
    return request('/rubrics', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },
  validateRubric: async (criteria) => {
    return request('/rubrics/validate', {
      method: 'POST',
      body: JSON.stringify({ criteria }),
    })
  },
}

// ── Audit & Reviews Endpoints ─────────────────────────────────────────────────
export const auditApi = {
  getEvents: async (params = {}) => {
    const query = new URLSearchParams()
    if (params.limit) query.append('limit', params.limit)
    if (params.action) query.append('action', params.action)
    if (params.search) query.append('search', params.search)
    const qs = query.toString() ? `?${query.toString()}` : ''
    return request(`/audit/events${qs}`)
  },
  recordDecision: async (submissionId, data) => {
    return request(`/reviews/${submissionId}/decision`, {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },
  recordOverride: async (submissionId, data) => {
    return request(`/reviews/${submissionId}/override`, {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },
  getReview: async (submissionId) => request(`/reviews/${submissionId}`),
}

// ── Batch Processing & Cohort Reporting Endpoints ─────────────────────────────
export const batchApi = {
  listBatches: async (params = {}) => {
    const query = new URLSearchParams()
    if (params.page) query.append('page', params.page)
    if (params.page_size) query.append('page_size', params.page_size)
    if (params.status) query.append('status', params.status)
    if (params.analysis_type) query.append('analysis_type', params.analysis_type)
    const qs = query.toString() ? `?${query.toString()}` : ''
    return request(`/batches${qs}`)
  },
  createBatch: async (data) => {
    return request('/batches', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },
  getBatch: async (id) => request(`/batches/${id}`),
  attachSubmissions: async (id, submissions) => {
    return request(`/batches/${id}/submissions`, {
      method: 'POST',
      body: JSON.stringify({ submissions }),
    })
  },
  runBatch: async (id, options = {}) => {
    return request(`/batches/${id}/run`, {
      method: 'POST',
      body: JSON.stringify(options),
    })
  },
  getReport: async (id) => request(`/batches/${id}/report`),
  exportReportUrl: (id, format = 'csv') => `${API_BASE}/batches/${id}/export?format=${format}`,
}

// ── External Integrations & Webhooks Endpoints ────────────────────────────────
export const integrationsApi = {
  getProviders: async () => request('/integrations/providers'),
  list: async (params = {}) => {
    const query = new URLSearchParams()
    if (params.provider) query.append('provider', params.provider)
    if (params.connection_status) query.append('connection_status', params.connection_status)
    const qs = query.toString() ? `?${query.toString()}` : ''
    return request(`/integrations${qs}`)
  },
  create: async (data) => {
    return request('/integrations', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },
  testConnection: async (id) => request(`/integrations/${id}/test`, { method: 'POST' }),
  disconnect: async (id) => request(`/integrations/${id}/disconnect`, { method: 'POST' }),
  delete: async (id) => request(`/integrations/${id}`, { method: 'DELETE' }),
}

export const webhooksApi = {
  registerEndpoint: async (data) => {
    return request('/webhooks/endpoints', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },
  listEndpoints: async () => request('/webhooks/endpoints'),
  testEndpoint: async (id) => request(`/webhooks/endpoints/${id}/test`, { method: 'POST' }),
  getDeliveries: async (id) => request(`/webhooks/endpoints/${id}/deliveries`),
  verifySignature: async (data) => {
    return request('/webhooks/verify', {
      method: 'POST',
      body: JSON.stringify(data),
    })
  },
}
