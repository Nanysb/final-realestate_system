import React, { useState, useEffect } from 'react';
import { useApi } from '../hooks/useApi';
import API from '../api/axios';
import FileUploader from './FileUploader';
import './Forms.css';

const AddProjectForm = () => {
  const [companies, setCompanies] = useState([]);
  const [images, setImages] = useState([]);
  const [videos, setVideos] = useState([]);
  const [formData, setFormData] = useState({
    company_slug: '',
    slug: '',
    title: '',
    location: '',
    description: '',
    status: 'active',
    images: '',
    videos: ''
  });
  
  const { loading: submitting, error: submitError, callApi, clearError } = useApi();
  const [loadingCompanies, setLoadingCompanies] = useState(true);

  useEffect(() => {
    fetchCompanies();
  }, []);

  const fetchCompanies = async () => {
    try {
      const response = await API.get('/companies');
      if (response.data.ok) {
        setCompanies(response.data.data);
      }
    } catch (error) {
      console.error('Error fetching companies:', error);
    } finally {
      setLoadingCompanies(false);
    }
  };

  const handleImagesUpload = (uploadResults) => {
    const imagePaths = Array.isArray(uploadResults) 
      ? uploadResults.map(result => result.path)
      : [uploadResults.path];
    
    setImages(prev => [...prev, ...imagePaths]);
    setFormData(prev => ({
      ...prev,
      images: JSON.stringify([...prev.images ? JSON.parse(prev.images) : [], ...imagePaths])
    }));
  };

  const handleVideosUpload = (uploadResults) => {
    const videoPaths = Array.isArray(uploadResults) 
      ? uploadResults.map(result => result.path)
      : [uploadResults.path];
    
    setVideos(prev => [...prev, ...videoPaths]);
    setFormData(prev => ({
      ...prev,
      videos: JSON.stringify([...prev.videos ? JSON.parse(prev.videos) : [], ...videoPaths])
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    clearError();
    
    try {
      const response = await callApi(() => 
        API.post('/projects', formData)
      );
      
      if (response.ok) {
        alert('✅ تم إضافة المشروع بنجاح!');
        setFormData({ 
          company_slug: '', 
          slug: '', 
          title: '', 
          location: '', 
          description: '',
          status: 'active',
          images: '',
          videos: ''
        });
        setImages([]);
        setVideos([]);
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

  const removeImage = (index) => {
    const newImages = images.filter((_, i) => i !== index);
    setImages(newImages);
    setFormData(prev => ({
      ...prev,
      images: JSON.stringify(newImages)
    }));
  };

  const removeVideo = (index) => {
    const newVideos = videos.filter((_, i) => i !== index);
    setVideos(newVideos);
    setFormData(prev => ({
      ...prev,
      videos: JSON.stringify(newVideos)
    }));
  };

  return (
    <div className="form-container">
      <h3>🏗️ إضافة مشروع جديد</h3>
      
      <form onSubmit={handleSubmit} className="form">
        <div className="form-group">
          <label>الشركة:</label>
          <select
            name="company_slug"
            value={formData.company_slug}
            onChange={handleChange}
            required
            disabled={loadingCompanies}
          >
            <option value="">{loadingCompanies ? 'جاري تحميل الشركات...' : 'اختر الشركة'}</option>
            {companies.map(company => (
              <option key={company.id} value={company.slug}>
                {company.name}
              </option>
            ))}
          </select>
        </div>

        <div className="form-group">
          <label>الرقم التعريفي (Slug):</label>
          <input
            type="text"
            name="slug"
            value={formData.slug}
            onChange={handleChange}
            required
            placeholder="مثال: emaar-downtown"
          />
        </div>

        <div className="form-group">
          <label>اسم المشروع:</label>
          <input
            type="text"
            name="title"
            value={formData.title}
            onChange={handleChange}
            required
            placeholder="مثال: إعمار داون تاون"
          />
        </div>

        <div className="form-group">
          <label>الموقع:</label>
          <input
            type="text"
            name="location"
            value={formData.location}
            onChange={handleChange}
            required
            placeholder="مثال: القاهرة الجديدة"
          />
        </div>

        <div className="form-group">
          <label>الحالة:</label>
          <select
            name="status"
            value={formData.status}
            onChange={handleChange}
          >
            <option value="active">نشط</option>
            <option value="completed">مكتمل</option>
            <option value="upcoming">قادم</option>
          </select>
        </div>

        <div className="form-group">
          <label>الوصف:</label>
          <textarea
            name="description"
            value={formData.description}
            onChange={handleChange}
            rows="3"
            placeholder="وصف المشروع..."
          />
        </div>

        <div className="form-group">
          <label>صور المشروع:</label>
          <FileUploader
            onUploadComplete={handleImagesUpload}
            fileType="image"
            multiple={true}
            maxFiles={10}
            label="🖼️ رفع صور المشروع"
            acceptedTypes="image/*"
          />
          {images.length > 0 && (
            <div className="media-previews">
              <h4>الصور المرفوعة:</h4>
              <div className="media-grid">
                {images.map((image, index) => (
                  <div key={index} className="media-item">
                    <img src={`/api/uploads/${image}`} alt={`صورة ${index + 1}`} />
                    <span className="media-name">صورة {index + 1}</span>
                    <button
                      type="button"
                      onClick={() => removeImage(index)}
                      className="remove-btn"
                    >
                      ✕
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="form-group">
          <label>فيديوهات المشروع:</label>
          <FileUploader
            onUploadComplete={handleVideosUpload}
            fileType="video"
            multiple={true}
            maxFiles={5}
            label="🎥 رفع فيديوهات المشروع"
            acceptedTypes="video/*"
          />
          {videos.length > 0 && (
            <div className="media-previews">
              <h4>الفيديوهات المرفوعة:</h4>
              <div className="media-grid">
                {videos.map((video, index) => (
                  <div key={index} className="media-item">
                    <div className="video-icon">🎥</div>
                    <span className="media-name">فيديو {index + 1}</span>
                    <button
                      type="button"
                      onClick={() => removeVideo(index)}
                      className="remove-btn"
                    >
                      ✕
                    </button>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {submitError && (
          <div className="error-message">
            ⚠️ {submitError}
          </div>
        )}

        <button type="submit" disabled={submitting} className="submit-btn">
          {submitting ? 'جاري الإضافة...' : '🏗️ إضافة المشروع'}
        </button>
      </form>
    </div>
  );
};

export default AddProjectForm;