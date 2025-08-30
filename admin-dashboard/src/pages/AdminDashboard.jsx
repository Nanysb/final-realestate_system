import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import AddCompanyForm from '../components/AddCompanyForm';
import AddProjectForm from '../components/AddProjectForm';
import AddUnitForm from '../components/AddUnitForm';
import './AdminDashboard.css';

const AdminDashboard = () => {
  const [activeTab, setActiveTab] = useState('companies');
  const { user } = useAuth();

  if (user?.role !== 'admin') {
    return (
      <div className="admin-container">
        <div className="access-denied">
          <h2>⛔ صلاحية مرفوضة</h2>
          <p>ليس لديك صلاحية للوصول إلى لوحة الإدارة</p>
        </div>
      </div>
    );
  }

  return (
    <div className="admin-container">
      <div className="admin-header">
        <h1>👑 لوحة إدارة البوت</h1>
        <p>إدارة المحتوى المعروض في بوت التليجرام</p>
      </div>

      <div className="admin-tabs">
        <button 
          className={activeTab === 'companies' ? 'active' : ''}
          onClick={() => setActiveTab('companies')}
        >
          🏢 الشركات
        </button>
        <button 
          className={activeTab === 'projects' ? 'active' : ''}
          onClick={() => setActiveTab('projects')}
        >
          🏗️ المشاريع
        </button>
        <button 
          className={activeTab === 'units' ? 'active' : ''}
          onClick={() => setActiveTab('units')}
        >
          🏠 الوحدات
        </button>
      </div>

      <div className="admin-content">
        {activeTab === 'companies' && <AddCompanyForm />}
        {activeTab === 'projects' && <AddProjectForm />}
        {activeTab === 'units' && <AddUnitForm />}
      </div>
    </div>
  );
};

export default AdminDashboard;