import React, { useState, useRef } from 'react';
import { useApi } from '../hooks/useApi';
import API from '../api/axios';
import './FileUploader.css';

const FileUploader = ({ 
  onUploadComplete, 
  fileType = 'image', 
  multiple = false,
  maxFiles = 10,
  label = "رفع ملف",
  acceptedTypes = "image/*,video/*"
}) => {
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [previews, setPreviews] = useState([]);
  const fileInputRef = useRef();
  const { callApi } = useApi();

  const handleFileSelect = async (e) => {
    const files = Array.from(e.target.files);
    if (files.length === 0) return;

    setUploading(true);
    setProgress(0);

    const uploadedFiles = [];

    for (let i = 0; i < Math.min(files.length, maxFiles); i++) {
      const file = files[i];
      
      // معاينة الصور
      if (file.type.startsWith('image/')) {
        const previewUrl = URL.createObjectURL(file);
        setPreviews(prev => [...prev, { url: previewUrl, name: file.name }]);
      }

      try {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('type', fileType);

        const response = await callApi(() => 
          API.post('/api/upload', formData, {
            headers: {
              'Content-Type': 'multipart/form-data'
            },
            onUploadProgress: (progressEvent) => {
              const percent = Math.round(
                (progressEvent.loaded * 100) / progressEvent.total
              );
              setProgress(percent);
            }
          })
        );

        if (response.ok) {
          uploadedFiles.push(response);
        }
      } catch (error) {
        console.error('Upload error:', error);
      }
    }

    setUploading(false);
    setProgress(0);
    
    if (uploadedFiles.length > 0 && onUploadComplete) {
      onUploadComplete(multiple ? uploadedFiles : uploadedFiles[0]);
    }

    // Reset file input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const removePreview = (index) => {
    setPreviews(prev => prev.filter((_, i) => i !== index));
  };

  return (
    <div className="file-uploader">
      <label className="upload-label">
        <span className="upload-icon">📁</span>
        {label}
        <input
          ref={fileInputRef}
          type="file"
          multiple={multiple}
          accept={acceptedTypes}
          onChange={handleFileSelect}
          disabled={uploading}
          className="file-input"
        />
      </label>

      {uploading && (
        <div className="upload-progress">
          <div className="progress-bar">
            <div 
              className="progress-fill" 
              style={{ width: `${progress}%` }}
            ></div>
          </div>
          <span className="progress-text">{progress}%</span>
        </div>
      )}

      {previews.length > 0 && (
        <div className="previews-container">
          <h4>معاينة الملفات:</h4>
          <div className="previews-grid">
            {previews.map((preview, index) => (
              <div key={index} className="preview-item">
                {preview.url ? (
                  <img src={preview.url} alt="معاينة" />
                ) : (
                  <div className="file-icon">📄</div>
                )}
                <span className="file-name">{preview.name}</span>
                <button
                  type="button"
                  onClick={() => removePreview(index)}
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
  );
};

export default FileUploader;