import React, { useState } from 'react';
import { useApi } from '../hooks/useApi';
import API from '../api/axios';
import FileUploader from './FileUploader';
import './Forms.css';

const AddCompanyForm = () => {
  const [formData, setFormData] = useState({
    slug: '',
    name: '',
    description: '',
    logo: ''
  });
  
  const { loading, error, callApi, clearError } = useApi();

  const handleLogoUpload = (uploadResult) => {
    setFormData(prev => ({
      ...prev,
      logo: uploadResult.path
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    clearError();
    
    try {
      const response = await callApi(() => 
        API.post('/companies', formData)
      );
      
      if (response.ok) {
        alert('✅ تم إضافة الشركة بنجاح!');
        setFormData({ slug: '', name: '', description: '', logo: '' });
      }
    } catch (error) {
      // Error handled by useApi
    }
  };

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  return (
    <div className="form-container">
      <h3>➕ إضافة شركة جديدة</h3>
      
      <form onSubmit={handleSubmit} className="form">
        <div className="form-group">
          <label>الرقم التعريفي (Slug):</label>
          <input
            type="text"
            name="slug"
            value={formData.slug}
            onChange={handleChange}
            required
            placeholder="مثال: emaar-misr"
          />
        </div>

        <div className="form-group">
          <label>اسم الشركة:</label>
          <input
            type="text"
            name="name"
            value={formData.name}
            onChange={handleChange}
            required
            placeholder="مثال: شركة إعمار مصر"
          />
        </div>

        <div className="form-group">
          <label>الوصف:</label>
          <textarea
            name="description"
            value={formData.description}
            onChange={handleChange}
            rows="3"
            placeholder="وصف مختصر عن الشركة..."
          />
        </div>

        <div className="form-group">
          <label>شعار الشركة:</label>
          <FileUploader
            onUploadComplete={handleLogoUpload}
            fileType="image"
            label="📷 رفع شعار الشركة"
            acceptedTypes="image/*"
          />
          {formData.logo && (
            <div className="upload-info">
              <span>✓ تم اختيار الشعار: {formData.logo}</span>
            </div>
          )}
        </div>

        {error && (
          <div className="error-message">
            ⚠️ {error}
          </div>
        )}

        <button type="submit" disabled={loading} className="submit-btn">
          {loading ? 'جاري الإضافة...' : '➕ إضافة الشركة'}
        </button>
      </form>
    </div>
  );
};

export default AddCompanyForm;