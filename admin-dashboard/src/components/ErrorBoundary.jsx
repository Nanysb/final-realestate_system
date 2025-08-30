import React from 'react';
import './ErrorBoundary.css';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
  }

  handleReload = () => {
    this.setState({ hasError: false, error: null });
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="error-boundary">
          <div className="error-content">
            <h2>⚠️ حدث خطأ غير متوقع</h2>
            <p>عذراً، حدث خطأ في التطبيق. يرجى المحاولة مرة أخرى.</p>
            <div className="error-actions">
              <button onClick={this.handleReload} className="reload-btn">
                🔄 إعادة تحميل الصفحة
              </button>
              <button 
                onClick={() => window.location.href = '/'}
                className="home-btn"
              >
                🏠 الصفحة الرئيسية
              </button>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;