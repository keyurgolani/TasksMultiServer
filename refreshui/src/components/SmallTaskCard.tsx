import React from 'react';
import styles from './SmallTaskCard.module.css';
import type { Task } from '../api/client';

interface SmallTaskCardProps {
  task: Task;
  onClick?: () => void;
}

export const SmallTaskCard: React.FC<SmallTaskCardProps> = ({ task, onClick }) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case "COMPLETED": return "#2ed573";
      case "IN_PROGRESS": return "#ffa502";
      case "BLOCKED": return "#ff4757";
      case "NOT_STARTED": return "#a4b0be";
      default: return "#a4b0be";
    }
  };

  return (
    <div 
      className={styles.card}
      onClick={onClick}
      style={{ cursor: onClick ? 'pointer' : 'default' }}
    >
      <div className={styles.titleRow}>
        <div 
          className={styles.priorityDot}
          style={{ 
            width: '8px', 
            height: '8px', 
            borderRadius: '50%', 
            backgroundColor: getStatusColor(task.status),
            flexShrink: 0,
            marginRight: '8px'
          }}
          title={task.status.replace('_', ' ')}
        />
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
