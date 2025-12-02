import React from 'react';
import { Badge } from './ui';
import type { Task } from '../api/client';
import styles from './StatusIndicator.module.css';

interface StatusIndicatorProps {
  status: Task['status'];
  variant?: 'dot' | 'badge';
}

export const StatusIndicator: React.FC<StatusIndicatorProps> = ({ 
  status, 
  variant = 'badge' 
}) => {
  const getStatusBadgeVariant = (status: Task['status']): 'success' | 'warning' | 'error' | 'info' => {
    switch (status) {
      case 'COMPLETED': return 'success';
      case 'IN_PROGRESS': return 'info';
      case 'BLOCKED': return 'error';
      default: return 'warning';
    }
  };

  if (variant === 'dot') {
    return (
      <span className={styles.statusIndicator} data-status={status} />
    );
  }

  return (
    <div className={styles.statusBadgeWrapper}>
      <span className={styles.statusIndicator} data-status={status} />
      <Badge variant={getStatusBadgeVariant(status)}>
        {status.replace('_', ' ')}
      </Badge>
    </div>
  );
};
