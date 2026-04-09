import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '/api';

const client = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('glynk_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('glynk_token');
      
      // Import useAuthStore dynamically to avoid circular dependencies if any, or just use statically over there.
      // Wait, let's just make it simpler by importing at the top, but we'll stick to dynamic if we have to. Let's just import it at top.
      import('../store/auth').then(({ useAuthStore }) => {
        useAuthStore.getState().logout();
      });
      
      // Don't force redirect — let components handle auth state
      // (e.g., reader page shows login modal instead of redirecting)
    }
    return Promise.reject(error);
  },
);

export default client;
