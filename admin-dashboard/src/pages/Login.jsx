import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useApi } from '../hooks/useApi';
import API from '../api/axios';
import { setAuthToken } from '../utils/auth';
import { SEO, LoadingSpinner } from '../components';
import './Login.css';

const Login = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const { login, isAuthenticated } = useAuth();
  const { loading, error, callApi, clearError } = useApi();
  const navigate = useNavigate();

  useEffect(() => {
    if (isAuthenticated) {
      navigate('/dashboard', { replace: true });
    }
  }, [isAuthenticated, navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    clearError();

    if (!username.trim() || !password.trim()) {
      return;
    }

    try {
      const response = await callApi(() => 
        API.post('/auth/login', {
          username: username.trim(),
          password: password.trim()
        })
      );

      if (response.ok) {
        setAuthToken(response.access_token);
        login(response.access_token, { 
          username: username.trim(), 
          role: 'admin' 
        });
        navigate('/dashboard', { replace: true });
      }
    } catch (error) {
      // Error is handled by useApi hook
    }
  };

  const handleDemoLogin = () => {
    setUsername('admin');
    setPassword('');
    setTimeout(() => {
      handleSubmit(new Event('submit'));
    }, 100);
  };

  if (loading) {
    return <LoadingSpinner message="جاري تسجيل الدخول..." />;
  }

  return (
    <>
      <SEO title="تسجيل الدخول - نظام العقارات" />
      <div className="login-container">
        <div className="login-card">
          <div className="login-header">
            <div className="logo">
              <h1>🏢 نظام العقارات</h1>
            </div>
            <p>يرجى تسجيل الدخول للمتابعة</p>
          </div>

          <form onSubmit={handleSubmit} className="login-form">
            <div className="input-group">
              <label>اسم المستخدم</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="أدخل اسم المستخدم"
                required
                autoComplete="username"
                className="login-input"
                disabled={loading}
              />
            </div>

            <div className="input-group">
              <label>كلمة المرور</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="أدخل كلمة المرور"
                required
                autoComplete="current-password"
                className="login-input"
                disabled={loading}
              />
            </div>

            {error && (
              <div className="error-message">
                ⚠️ {error}
                <button 
                  type="button" 
                  onClick={clearError}
                  className="error-close"
                >
                  ✕
                </button>
              </div>
            )}

            <button 
              type="submit" 
              className="login-btn"
              disabled={loading}
            >
              {loading ? (
                <>
                  <span className="spinner"></span>
                  جاري التسجيل...
                </>
              ) : (
                'تسجيل الدخول'
              )}
            </button>

            <div className="login-options">
              <button 
                type="button" 
                className="demo-login-btn"
                onClick={handleDemoLogin}
                disabled={loading}
              >
                🚀 تجربة سريعة (بيانات تجريبية)
              </button>
            </div>
          </form>

          <div className="login-footer">
            <p>نظام إدارة العقارات © 2024</p>
          </div>
        </div>
      </div>
    </>
  );
};

export default Login;