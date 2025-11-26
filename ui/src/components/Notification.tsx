import React, { useEffect } from 'react';
import { ErrorType } from '../utils/errorHandler';

export interface NotificationProps {
  message: string;
  type: ErrorType | 'success' | 'info';
  onClose: () => void;
  duration?: number;
}

const Notification: React.FC<NotificationProps> = ({ message, type, onClose, duration = 5000 }) => {
  useEffect(() => {
    if (duration > 0) {
      const timer = setTimeout(() => {
        onClose();
      }, duration);
      return () => clearTimeout(timer);
    }
  }, [duration, onClose]);

  const getBackgroundColor = (): string => {
    switch (type) {
      case ErrorType.VALIDATION:
        return '#fff3cd';
      case ErrorType.BUSINESS_LOGIC:
        return '#f8d7da';
      case ErrorType.STORAGE:
        return '#f8d7da';
      case ErrorType.NOT_FOUND:
        return '#d1ecf1';
      case ErrorType.NETWORK:
        return '#f8d7da';
      case 'success':
        return '#d4edda';
      case 'info':
        return '#d1ecf1';
      default:
        return '#f8d7da';
    }
  };

  const getTextColor = (): string => {
    switch (type) {
      case ErrorType.VALIDATION:
        return '#856404';
      case ErrorType.BUSINESS_LOGIC:
        return '#721c24';
      case ErrorType.STORAGE:
        return '#721c24';
      case ErrorType.NOT_FOUND:
        return '#0c5460';
      case ErrorType.NETWORK:
        return '#721c24';
      case 'success':
        return '#155724';
      case 'info':
        return '#0c5460';
      default:
        return '#721c24';
    }
  };

  const getBorderColor = (): string => {
    switch (type) {
      case ErrorType.VALIDATION:
        return '#ffeaa7';
      case ErrorType.BUSINESS_LOGIC:
        return '#f5c6cb';
      case ErrorType.STORAGE:
        return '#f5c6cb';
      case ErrorType.NOT_FOUND:
        return '#bee5eb';
      case ErrorType.NETWORK:
        return '#f5c6cb';
      case 'success':
        return '#c3e6cb';
      case 'info':
        return '#bee5eb';
      default:
        return '#f5c6cb';
    }
  };

  const getIcon = (): string => {
    switch (type) {
      case ErrorType.VALIDATION:
        return '⚠️';
      case ErrorType.BUSINESS_LOGIC:
        return '❌';
      case ErrorType.STORAGE:
        return '💾';
      case ErrorType.NOT_FOUND:
        return '🔍';
      case ErrorType.NETWORK:
        return '🌐';
      case 'success':
        return '✅';
      case 'info':
        return 'ℹ️';
      default:
        return '❌';
    }
  };

  return (
    <div
      style={{
        position: 'fixed',
        top: '80px',
        right: '20px',
        maxWidth: '400px',
        padding: '1rem',
        backgroundColor: getBackgroundColor(),
        color: getTextColor(),
        border: `1px solid ${getBorderColor()}`,
        borderRadius: '8px',
        boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
        display: 'flex',
        alignItems: 'start',
        gap: '0.75rem',
        zIndex: 1000,
        animation: 'slideIn 0.3s ease-out',
      }}
    >
      <span style={{ fontSize: '1.25rem', flexShrink: 0 }}>{getIcon()}</span>
      <div style={{ flex: 1, wordBreak: 'break-word' }}>{message}</div>
      <button
        onClick={onClose}
        style={{
          padding: '0.25rem 0.5rem',
          backgroundColor: 'transparent',
          border: `1px solid ${getTextColor()}`,
          color: getTextColor(),
          cursor: 'pointer',
          borderRadius: '4px',
          fontSize: '0.875rem',
          flexShrink: 0,
        }}
      >
        ✕
      </button>
      <style>
        {`
          @keyframes slideIn {
            from {
              transform: translateX(100%);
              opacity: 0;
            }
            to {
              transform: translateX(0);
              opacity: 1;
            }
          }
        `}
      </style>
    </div>
  );
};

export default Notification;
