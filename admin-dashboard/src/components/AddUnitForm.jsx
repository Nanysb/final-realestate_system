import React, { useState, useEffect } from 'react';
import { useApi } from '../hooks/useApi';
import API from '../api/axios';
import './Forms.css';

const AddUnitForm = () => {
  const [projects, setProjects] = useState([]);
  const [formData, setFormData] = useState({
    project_id: '',
    code: '',
    title: '',
    sqm: '',
    price_per_sqm: '',
    floor: '',
    bedrooms: '',
    bathrooms: '',
    status: 'available'
  });
  
  const { loading, error, callApi, clearError } = useApi();

  useEffect(() => {
    fetchProjects();
  }, []);

  const fetchProjects = async () => {
    try {
      const response = await API.get('/projects');
      if (response.data.ok) {
        setProjects(response.data.data);
      }
    } catch (error) {
      console.error('Error fetching projects:', error);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    clearError();
    
    try {
      const response = await callApi(() => 
        API.post('/units', {
          ...formData,
          sqm: parseFloat(formData.sqm),
          price_per_sqm: parseInt(formData.price_per_sqm),
          bedrooms: parseInt(formData.bedrooms),
          bathrooms: parseInt(formData.bathrooms)
        })
      );
      
      if (response.ok) {
        alert('✅ تم إضافة الوحدة بنجاح!');
        setFormData({ 
          project_id: '',
          code: '',
          title: '',
          sqm: '',
          price_per_sqm: '',
          floor: '',
          bedrooms: '',
          bathrooms: '',
          status: 'available'
        });
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
      <h3>🏠 إضافة وحدة جديدة</h3>
      
      <form onSubmit={handleSubmit} className="form">
        <div className="form-group">
          <label>المشروع:</label>
          <select
            name="project_id"
            value={formData.project_id}
            onChange={handleChange}
            required
          >
            <option value="">اختر المشروع</option>
            {projects.map(project => (
              <option key={project.id} value={project.id}>
                {project.title}
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label>كود الوحدة:</label>
          <input
            type="text"
            name="code"
            value={formData.code}
            onChange={handleChange}
            required
            placeholder="مثال: A101"
          />
        </div>

        <div className="form-group">
          <label>عنوان الوحدة (اختياري):</label>
          <input
            type="text"
            name="title"
            value={formData.title}
            onChange={handleChange}
            placeholder="مثال: شقة 3 غرف"
          />
        </div>

        <div className="form-group">
          <label>المساحة (م²):</label>
          <input
            type="number"
            name="sqm"
            value={formData.sqm}
            onChange={handleChange}
            required
            placeholder="مثال: 120"
            step="0.1"
          />
        </div>

        <div className="form-group">
          <label>سعر المتر (جنيه):</label>
          <input
            type="number"
            name="price_per_sqm"
            value={formData.price_per_sqm}
            onChange={handleChange}
            required
            placeholder="مثال: 5000"
          />
        </div>

        <div className="form-group">
          <label>الطابق:</label>
          <input
            type="text"
            name="floor"
            value={formData.floor}
            onChange={handleChange}
            required
            placeholder="مثال: 3"
          />
        </div>

        <div className="form-group">
          <label>عدد الغرف:</label>
          <input
            type="number"
            name="bedrooms"
            value={formData.bedrooms}
            onChange={handleChange}
            required
            placeholder="مثال: 3"
          />
        </div>

        <div className="form-group">
          <label>عدد الحمامات:</label>
          <input
            type="number"
            name="bathrooms"
            value={formData.bathrooms}
            onChange={handleChange}
            required
            placeholder="مثال: 2"
          />
        </div>

        <div className="form-group">
          <label>الحالة:</label>
          <select
            name="status"
            value={formData.status}
            onChange={handleChange}
          >
            <option value="available">متاحة</option>
            <option value="sold">مباعة</option>
            <option value="reserved">محجوزة</option>
          </select>
        </div>

        {error && (
          <div className="error-message">
            ⚠️ {error}
          </div>
        )}

        <button type="submit" disabled={loading} className="submit-btn">
          {loading ? 'جاري الإضافة...' : '🏠 إضافة الوحدة'}
        </button>
      </form>
    </div>
  );
};

export default AddUnitForm;