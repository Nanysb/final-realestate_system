import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useApi } from '../hooks/useApi';
import API from '../api/axios';
import { SEO, LoadingSpinner } from '../components';
import './Dashboard.css';

const Dashboard = () => {
  const [projects, setProjects] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [units, setUnits] = useState([]);
  const { user, logout } = useAuth();
  const { loading, error, callApi } = useApi();
  const navigate = useNavigate();

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [projectsData, companiesData, unitsData] = await Promise.all([
        callApi(() => API.get('/projects')),
        callApi(() => API.get('/companies')),
        callApi(() => API.get('/units'))
      ]);

      if (projectsData.ok) setProjects(projectsData.data);
      if (companiesData.ok) setCompanies(companiesData.data);
      if (unitsData.ok) setUnits(unitsData.data);
    } catch (error) {
      // Error handled by useApi
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login', { replace: true });
  };

  const goToAdminPanel = () => {
    navigate('/admin');
  };

  if (loading) {
    return (
      <>
        <SEO title="لوحة التحكم - جاري التحميل" />
        <LoadingSpinner message="جاري تحميل البيانات..." />
      </>
    );
  }

  return (
    <>
      <SEO title="لوحة التحكم - نظام العقارات" />
      <div className="dashboard-container">
        <div className="dashboard-header">
          <div className="header-content">
            <h1>لوحة التحكم</h1>
            <p>نظام إدارة العقارات والمشاريع</p>
          </div>
          <div className="header-actions">
            {user?.role === 'admin' && (
              <button onClick={goToAdminPanel} className="admin-btn">
                👑 لوحة الإدارة
              </button>
            )}
            <button onClick={handleLogout} className="logout-btn">
              🚪 تسجيل الخروج
            </button>
          </div>
        </div>

        {error && (
          <div className="error-banner">
            ⚠️ {error}
            <button onClick={fetchData} className="retry-btn">
              🔄 إعادة المحاولة
            </button>
          </div>
        )}

        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-icon">🏢</div>
            <div className="stat-content">
              <h3>الشركات</h3>
              <p className="stat-number">{companies.length}</p>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon">🏗️</div>
            <div className="stat-content">
              <h3>المشاريع</h3>
              <p className="stat-number">{projects.length}</p>
            </div>
          </div>

          <div className="stat-card">
            <div className="stat-icon">🏠</div>
            <div className="stat-content">
              <h3>الوحدات</h3>
              <p className="stat-number">{units.length}</p>
            </div>
          </div>
        </div>

        <div className="recent-section">
          <div className="section-header">
            <h2>أحدث المشاريع</h2>
            <button onClick={fetchData} className="refresh-btn">
              🔄 تحديث
            </button>
          </div>

          {projects.length === 0 ? (
            <div className="empty-state">
              <div className="empty-icon">📋</div>
              <h3>لا توجد مشاريع</h3>
              <p>لم يتم إضافة أي مشاريع بعد</p>
              {user?.role === 'admin' && (
                <button onClick={goToAdminPanel} className="admin-btn">
                  👑 اذهب إلى لوحة الإدارة لإضافة مشاريع
                </button>
              )}
            </div>
          ) : (
            <div className="projects-grid">
              {projects.slice(0, 6).map(project => (
                <div key={project.id} className="project-card">
                  <h4>{project.title}</h4>
                  <div className="project-details">
                    <p>📍 {project.location || 'غير محدد'}</p>
                    <p>🏢 الشركة: {project.company_id || 'غير محدد'}</p>
                    <span className={`status status-${project.status}`}>
                      {project.status === 'active' ? 'نشط' : 
                       project.status === 'completed' ? 'مكتمل' : 'قادم'}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  );
};

export default Dashboard;