import axios from 'axios';
import Constants from 'expo-constants';

// Auto-detect host IP for physical device connection, default to localhost for simulators
const hostUri = Constants.expoConfig?.hostUri;
const ip = hostUri ? hostUri.split(':')[0] : 'localhost';

export const API_URL = `http://${ip}:8000/api/v1`;

const client = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to attach JWT token
client.interceptors.request.use(
  async (config) => {
    // We will dynamically get the token from our Zustand store
    // to avoid import cycle issues, we'll read it from our storage or state
    try {
      const { useAuthStore } = require('../store/auth');
      const token = useAuthStore.getState().token;
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
    } catch (e) {
      // Ignore errors if store is not loaded yet
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle expired or invalid token (401/403)
client.interceptors.response.use(
  (response) => response,
  async (error) => {
    if (error.response && (error.response.status === 401 || error.response.status === 403)) {
      try {
        const { useAuthStore } = require('../store/auth');
        useAuthStore.getState().logout();
      } catch (e) {
        // Ignore errors if store is not loaded yet
      }
    }
    return Promise.reject(error);
  }
);

export default client;
