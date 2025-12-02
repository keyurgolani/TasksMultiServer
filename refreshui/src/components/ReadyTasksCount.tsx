import React from 'react';
import styles from './ReadyTasksCount.module.css';

interface ReadyTasksCountProps {
  count: number;
  variant?: 'default' | 'compact';
}

export const ReadyTasksCount: React.FC<ReadyTasksCountProps> = ({ 
  count, 
  variant = 'default' 
}) => {
  return (
    <span className={`${styles.readyCount} ${styles[variant]}`}>
      <span className={styles.number}>{count}</span>
      {variant === 'default' && <span className={styles.label}> Ready</span>}
    </span>
  );
};
