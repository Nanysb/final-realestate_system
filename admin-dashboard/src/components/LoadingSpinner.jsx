import React from 'react';
import './LoadingSpinner.css';

const LoadingSpinner = ({ message = "جاري التحميل...", size = "medium" }) => {
  const sizeClass = {
    small: 'spinner-small',
    medium: 'spinner-medium',
    large: 'spinner-large'
  }[size];

  return (
    <div className="loading-spinner-container">
      <div className="loading-spinner">
        <div className={`spinner ${sizeClass}`}></div>
        {message && <p className="spinner-message">{message}</p>}
      </div>
    </div>
  );
};

export default LoadingSpinner;