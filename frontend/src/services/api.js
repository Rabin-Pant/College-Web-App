import axios from 'axios';
import toast from 'react-hot-toast';

const API_URL = 'http://127.0.0.1:5000/api';  

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000, // 10 second timeout
});

// Request interceptor to add token
// Request interceptor to add token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    console.log('🚀 Request:', config.method.toUpperCase(), config.url);
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor for token refresh and error handling
api.interceptors.response.use(
  (response) => {
    console.log('✅ Response:', response.status, response.config.url);
    return response;
  },
  async (error) => {
    console.error('❌ Response Error:', error.response?.status, error.config?.url, error.response?.data);

    // Handle network errors
    if (!error.response) {
      toast.error('Cannot connect to server. Please check if backend is running.');
      return Promise.reject(error);
    }

    const originalRequest = error.config;

    // Handle 401 Unauthorized errors (token expired)
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      // Don't try to refresh on login or register endpoints
      if (originalRequest.url.includes('/auth/login') || 
          originalRequest.url.includes('/auth/register')) {
        return Promise.reject(error);
      }

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (!refreshToken) {
          throw new Error('No refresh token');
        }

        const response = await axios.post(`${API_URL}/auth/refresh`, {}, {
          headers: { Authorization: `Bearer ${refreshToken}` }
        });

        const { access_token } = response.data;
        localStorage.setItem('access_token', access_token);

        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        return api(originalRequest);
      } catch (refreshError) {
        console.error('Token refresh failed:', refreshError);
        localStorage.clear();
        window.location.href = '/login';
        toast.error('Session expired. Please login again.');
        return Promise.reject(refreshError);
      }
    }

    // Handle other errors
    const errorMessage = error.response?.data?.error || 
                        error.response?.data?.message || 
                        'Something went wrong';
    
    // Don't show toast for 401 on login/register
    if (!(error.response?.status === 401 && 
          (originalRequest?.url?.includes('/auth/login') || 
           originalRequest?.url?.includes('/auth/register')))) {
      toast.error(errorMessage);
    }
    
    return Promise.reject(error);
  }
);

export default api;