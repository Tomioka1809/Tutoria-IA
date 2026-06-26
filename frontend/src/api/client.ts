import axios from 'axios';
import Constants from 'expo-constants';
import { Platform } from 'react-native';

// Auto-detect host IP for physical device connection, default to localhost for simulators
const hostUri = Constants.expoConfig?.hostUri;
let ip = '192.168.18.27'; // Force hardcode LAN IP as fallback

if (hostUri) {
  ip = hostUri.split(':')[0];
}

export const API_URL = `http://${ip}:8000/api/v1`;
console.log('===> INIT API_URL:', API_URL);

const client = axios.create({
  baseURL: API_URL,
  timeout: 60000, // 60 seconds timeout to allow LLM processing
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
