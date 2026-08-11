import axios from 'axios';

// Base API Axios Instance ready for FastAPI integration
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 15000,
});

// Request Interceptor: Attach bearer token if available
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('chronanexus_auth_token');
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response Interceptor: Global error handling placeholder
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Clear token on 401
      localStorage.removeItem('chronanexus_auth_token');
    }
    return Promise.reject(error);
  }
);

export default api;
