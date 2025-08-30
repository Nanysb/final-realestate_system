import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { getAuthToken, clearAuthToken } from '../utils/auth';

export const useAuth = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    checkAuth();
  }, []);

  const checkAuth = () => {
    const token = getAuthToken();
    setIsAuthenticated(!!token);
    
    if (!token) {
      console.log('User not authenticated');
    }
  };

  const login = (token, userData) => {
    localStorage.setItem('token', token);
    setUser(userData);
    setIsAuthenticated(true);
  };

  const logout = () => {
    clearAuthToken();
    setUser(null);
    setIsAuthenticated(false);
    navigate('/login');
  };

  const softLogout = () => {
    clearAuthToken();
    setUser(null);
    setIsAuthenticated(false);
    console.log('Soft logout - session cleared but no redirect');
  };

  return {
    isAuthenticated,
    user,
    login,
    logout,
    softLogout,
    checkAuth
  };
};