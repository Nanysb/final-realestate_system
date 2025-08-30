import React from 'react';
import { Helmet } from 'react-helmet';

const SEO = ({ 
  title = "نظام إدارة العقارات", 
  description = "نظام متكامل لإدارة المشاريع والعقارات مع واجهة إدارة قوية",
  keywords = "عقارات, إدارة, مشاريع, وحدات, إدارة عقارات"
}) => {
  return (
    <Helmet>
      <title>{title}</title>
      <meta name="description" content={description} />
      <meta name="keywords" content={keywords} />
      <meta name="theme-color" content="#667eea" />
      
      {/* Open Graph */}
      <meta property="og:title" content={title} />
      <meta property="og:description" content={description} />
      <meta property="og:type" content="website" />
      
      {/* Twitter */}
      <meta name="twitter:card" content="summary_large_image" />
      <meta name="twitter:title" content={title} />
      <meta name="twitter:description" content={description} />
    </Helmet>
  );
};

export default SEO;