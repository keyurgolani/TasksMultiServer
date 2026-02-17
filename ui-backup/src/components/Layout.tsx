import React from 'react';
import { Link, Outlet } from 'react-router-dom';
import { useApp } from '../context/AppContext';
import Notification from './Notification';

const Layout: React.FC = () => {
  const { error, clearError, notifications, removeNotification } = useApp();

  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      {/* Header */}
      <header style={{ 
        padding: '1rem', 
        backgroundColor: '#282c34', 
        color: 'white',
        borderBottom: '2px solid #61dafb'
      }}>
        <nav style={{ display: 'flex', gap: '2rem', alignItems: 'center' }}>
          <h1 style={{ margin: 0, fontSize: '1.5rem' }}>Task Management System</h1>
          <Link to="/" style={{ color: '#61dafb', textDecoration: 'none' }}>
            Projects
          </Link>
        </nav>
      </header>

      {/* Error Banner */}
      {error && (
        <div style={{
          padding: '1rem',
          backgroundColor: '#f8d7da',
          color: '#721c24',
          borderBottom: '1px solid #f5c6cb',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <span>{error}</span>
          <button 
            onClick={clearError}
            style={{
              padding: '0.25rem 0.5rem',
              backgroundColor: 'transparent',
              border: '1px solid #721c24',
              color: '#721c24',
              cursor: 'pointer',
              borderRadius: '4px'
            }}
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Notifications */}
      <div style={{ position: 'fixed', top: '80px', right: '20px', zIndex: 1000 }}>
        {notifications.map((notification, index) => (
          <div key={notification.id} style={{ marginBottom: index < notifications.length - 1 ? '0.5rem' : 0 }}>
            <Notification
              message={notification.message}
              type={notification.type}
              onClose={() => removeNotification(notification.id)}
            />
          </div>
        ))}
      </div>

      {/* Main Content */}
      <main style={{ flex: 1, padding: '2rem' }}>
        <Outlet />
      </main>

      {/* Footer */}
      <footer style={{
        padding: '1rem',
        backgroundColor: '#f5f5f5',
        textAlign: 'center',
        borderTop: '1px solid #ddd'
      }}>
        <p style={{ margin: 0, color: '#666' }}>
          Task Management System - Multi-interface task management
        </p>
      </footer>
    </div>
  );
};

export default Layout;
