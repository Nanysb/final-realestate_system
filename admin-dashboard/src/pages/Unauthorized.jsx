import React from 'react';
import { useNavigate } from 'react-router-dom';
import { SEO } from '../components';
import './Unauthorized.css';

const Unauthorized = () => {
  const navigate = useNavigate();

  return (
    <>
      <SEO title="غير مصرح - نظام العقارات" />
      <div className="unauthorized-container">
        <div className="unauthorized-content">
          <div className="error-icon">🚫</div>
          <h1>غير مصرح بالوصول</h1>
          <p>عذراً، ليس لديك الصلاحية للوصول إلى هذه الصفحة.</p>
          <div className="action-buttons">
            <button onClick={() => navigate(-1)} className="back-btn">
              ↩ الرجوع
            </button>
            <button onClick={() => navigate('/dashboard')} className="dashboard-btn">
              📊 لوحة التحكم
            </button>
            <button onClick={() => navigate('/login')} className="login-btn">
              🔐 تسجيل الدخول
            </button>
          </div>
        </div>
      </div>
    </>
  );
};

export default Unauthorized;