import React from 'react';
import { StatusIndicator } from './StatusIndicator';
import styles from './SmallTaskCard.module.css';
import type { Task } from '../api/client';

interface SmallTaskCardProps {
  task: Task;
  onClick?: () => void;
}

export const SmallTaskCard: React.FC<SmallTaskCardProps> = ({ task, onClick }) => {
  const getStatusBackground = (status: string) => {
    switch (status) {
      case 'IN_PROGRESS':
        return 'radial-gradient(circle at top left, color-mix(in srgb, var(--warning) 15%, transparent) 0%, transparent 70%)';
      case 'COMPLETED':
        return 'radial-gradient(circle at top left, color-mix(in srgb, var(--success) 15%, transparent) 0%, transparent 70%)';
      case 'BLOCKED':
        return 'radial-gradient(circle at top left, color-mix(in srgb, var(--error) 15%, transparent) 0%, transparent 70%)';
      case 'NOT_STARTED':
        return 'radial-gradient(circle at top left, color-mix(in srgb, #808080 10%, transparent) 0%, transparent 70%)';
      default:
        return undefined;
    }
  };

  return (
    <div 
      className={styles.card}
      onClick={onClick}
      style={{ 
        cursor: onClick ? 'pointer' : 'default',
        background: getStatusBackground(task.status)
      }}
    >
      <div className={styles.titleRow}>
        <StatusIndicator status={task.status} variant="dot" />
        <h4 className={styles.title}>{task.title}</h4>
        
        {/* Exit Criteria Progress Bar - inline on right */}
        {task.exit_criteria && task.exit_criteria.length > 0 && (
          <div className={styles.exitCriteriaContainer} title="Exit Criteria Progress">
            <div className={styles.progressBar}>
              <div 
                className={styles.progressFill}
                style={{ 
                  width: `${(task.exit_criteria.filter(ec => ec.status === 'COMPLETE').length / task.exit_criteria.length) * 100}%` 
                }}
              />
            </div>
            <span className={styles.progressText}>
              {task.exit_criteria.filter(ec => ec.status === 'COMPLETE').length}/{task.exit_criteria.length}
            </span>
          </div>
        )}
      </div>
    </div>
  );
};
