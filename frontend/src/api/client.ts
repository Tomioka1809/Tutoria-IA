/* eslint-disable import/no-named-as-default-member */
import axios from 'axios';
import Constants from 'expo-constants';
import { resolveApiUrl } from './api-config';
import { getApiToken, notifyUnauthorized } from './auth-session';

export const API_URL = resolveApiUrl({
  envUrl: process.env.EXPO_PUBLIC_API_URL,
  expoHostUri: Constants.expoConfig?.hostUri,
});

const client = axios.create({
  baseURL: API_URL,
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to attach JWT token
client.interceptors.request.use(
  (config) => {
    const token = getApiToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle expired or invalid token (401 only)
client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const url = error.config?.url ?? '';
    const isAuthRoute = url.includes('/auth/login') || url.includes('/auth/register');
    if (!isAuthRoute && error.response && error.response.status === 401) {
      try {
        await notifyUnauthorized();
      } catch {
        // Ignore errors during logout notification
      }
    }
    return Promise.reject(error);
  }
);

export default client;
