import axios, { AxiosInstance } from 'axios';

// API client configuration
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Create axios instance with default configuration
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 10000,
});

// Request interceptor for adding auth tokens or logging
apiClient.interceptors.request.use(
  (config) => {
    // Add any request modifications here (e.g., auth tokens)
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    // Handle common errors
    if (error.response) {
      // Server responded with error status
      const status = error.response.status;
      const data = error.response.data;
      
      // Log different types of errors
      if (status === 400) {
        console.error('Validation Error:', data);
      } else if (status === 404) {
        console.error('Not Found:', data);
      } else if (status === 409) {
        console.error('Business Logic Error:', data);
      } else if (status >= 500) {
        console.error('Server Error:', data);
      } else {
        console.error('API Error:', data);
      }
    } else if (error.request) {
      // Request made but no response
      console.error('Network Error: Unable to reach server', error.message);
    } else {
      // Something else happened
      console.error('Error:', error.message);
    }
    return Promise.reject(error);
  }
);

export default apiClient;
