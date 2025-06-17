// src/api/axios.ts
import axios from 'axios';
import type { InternalAxiosRequestConfig } from 'axios';

// In development, VITE_API_URL is set; in production it's undefined, so baseURL=''
const baseURL = import.meta.env.DEV
  ? (import.meta.env.VITE_API_URL || 'http://localhost:8000')
  : '';

const api = axios.create({
  baseURL,
  // if you need cookies: withCredentials: true,
});

// Attach the JWT token to every request if present
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers = config.headers ?? {};
    config.headers['Authorization'] = `Bearer ${token}`;
  }
  return config;
});

export default api;
