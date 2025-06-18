// src/api/axios.ts
import axios from 'axios';
import type { InternalAxiosRequestConfig } from 'axios';

// In dev: VITE_API_URL comes from .env.development, e.g. "http://localhost:8000"
// In prod: VITE_API_URL is undefined → baseURL = '' → requests go to same origin
const baseURL = import.meta.env.VITE_API_URL ?? '';

const api = axios.create({
  baseURL,
  // if you ever use cookies you can uncomment:
  // withCredentials: true,
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
