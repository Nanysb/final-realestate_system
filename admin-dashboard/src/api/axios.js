import axios from 'axios';
import { getAuthToken, refreshToken } from '../utils/auth'; // أزل clearAuthToken

const API = axios.create({
  baseURL: 'http://localhost:5000/api',
  timeout: 15000,
});

// Request Interceptor
API.interceptors.request.use((config) => {
  const token = getAuthToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => {
  return Promise.reject(error);
});

// Response Interceptor - معدل لمنع التسجيل الخروج التلقائي
API.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    
    // إذا كان الخطأ 401 ولم نكن قد حاولنا بالفعل refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      console.log('🔄 Attempting token refresh...');
      const refreshed = await refreshToken();
      
      if (refreshed) {
        // إعادة المحاولة بالـ token الجديد
        const newToken = getAuthToken();
        originalRequest.headers.Authorization = `Bearer ${newToken}`;
        return API(originalRequest);
      }
    }
    
    // إذا فشل الـ refresh أو كان خطأ آخر
    if (error.response?.status === 401) {
      console.log('❌ Unauthorized, but NOT logging out automatically');
      // لا تسجيل خروج تلقائي هنا!
    }
    
    return Promise.reject(error);
  }
);

export default API;