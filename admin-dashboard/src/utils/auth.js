// أضف هذا الاستيراد في الأعلى
import API from '../api/axios';

export const setAuthToken = (token) => {
  const tokenExpiry = Date.now() + (24 * 60 * 60 * 1000); // 24 ساعة
  localStorage.setItem('token', token);
  localStorage.setItem('token_expiry', tokenExpiry);
  console.log('✅ Token saved, expires at:', new Date(tokenExpiry).toLocaleString());
};

export const getAuthToken = () => {
  const token = localStorage.getItem('token');
  const expiry = localStorage.getItem('token_expiry');
  
  if (!token || !expiry) {
    console.log('❌ No token or expiry found');
    return null;
  }
  
  if (Date.now() > parseInt(expiry)) {
    console.log('❌ Token expired');
    clearAuthToken();
    return null;
  }
  
  console.log('✅ Token is valid');
  return token;
};

export const clearAuthToken = () => {
  localStorage.removeItem('token');
  localStorage.removeItem('token_expiry');
  console.log('🗑️ Token cleared');
};

export const isTokenValid = () => {
  return !!getAuthToken();
};

export const refreshToken = async () => {
  try {
    const response = await API.post('/auth/refresh');
    if (response.data.ok) {
      setAuthToken(response.data.access_token);
      return true;
    }
  } catch (error) {
    console.error('Token refresh failed:', error);
  }
  return false;
};