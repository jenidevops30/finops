import axios from 'axios';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:5000',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    console.log(`API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error('API Response Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// API service methods
export const apiService = {
  // Health check
  getHealth: () => api.get('/health'),
  getApiHealth: () => api.get('/api/health'),

  // Resources
  getResources: (params = {}) => api.get('/api/resources', { params }),
  getResource: (id) => api.get(`/api/resources/${id}`),
  createResource: (data) => api.post('/api/resources', data),
  updateResource: (id, data) => api.put(`/api/resources/${id}`, data),
  deleteResource: (id) => api.delete(`/api/resources/${id}`),

  // Optimizations
  getOptimizations: (params = {}) => api.get('/api/optimizations', { params }),
  getOptimization: (id) => api.get(`/api/optimizations/${id}`),
  approveOptimization: (id, data) => api.post(`/api/optimizations/${id}/approve`, data),
  executeOptimization: (id) => api.post(`/api/optimizations/${id}/execute`),

  // Budgets
  getBudgets: (params = {}) => api.get('/api/budgets', { params }),
  getBudget: (id) => api.get(`/api/budgets/${id}`),
  createBudget: (data) => api.post('/api/budgets', data),
  updateBudget: (id, data) => api.put(`/api/budgets/${id}`, data),
  deleteBudget: (id) => api.delete(`/api/budgets/${id}`),

  // Anomalies
  getAnomalies: (params = {}) => api.get('/api/anomalies', { params }),
  getAnomaly: (id) => api.get(`/api/anomalies/${id}`),
  acknowledgeAnomaly: (id) => api.post(`/api/anomalies/${id}/acknowledge`),

  // Savings
  getSavings: (params = {}) => api.get('/api/savings', { params }),
  getSavingsSummary: (params = {}) => api.get('/api/savings/summary', { params }),

  // Pricing
  getPricing: (params = {}) => api.get('/api/pricing', { params }),
  getPricingRecommendations: () => api.get('/api/pricing/recommendations'),

  // Dashboard
  getDashboardData: (params = {}) => api.get('/api/dashboard', { params }),
  getDashboardMetrics: (params = {}) => api.get('/api/dashboard/metrics', { params }),
  getDashboardCharts: (params = {}) => api.get('/api/dashboard/charts', { params }),
  
  // Monitoring
  getSystemHealth: () => api.get('/api/monitoring/health'),
  getSystemMetrics: () => api.get('/api/monitoring/metrics'),
  getAlerts: () => api.get('/api/monitoring/alerts'),
};

export default api;