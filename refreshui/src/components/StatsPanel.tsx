import React from 'react';
import { CheckCircle2, Clock, AlertCircle, Circle } from 'lucide-react';
import { SegmentedProgressBar } from './SegmentedProgressBar';
import styles from './StatsPanel.module.css';

interface StatsPanelProps {
  stats: {
    completed: number;
    inProgress: number;
    blocked: number;
    notStarted: number;
    total: number;
  };
  showProgressText?: boolean;
}

export const StatsPanel: React.FC<StatsPanelProps> = ({ stats, showProgressText = true }) => {
  const completionRate = stats.total > 0 ? Math.round((stats.completed / stats.total) * 100) : 0;

  return (
    <div className={styles.container}>
      <div className={styles.metricsGrid}>
        <div className={styles.metricItem}>
          <CheckCircle2 size={14} className={styles.icon} style={{ color: 'var(--success)' }} />
          <span className={styles.value}>{stats.completed}</span>
          <span className={styles.label}>Done</span>
        </div>
        <div className={styles.metricItem}>
          <Clock size={14} className={styles.icon} style={{ color: 'var(--warning)' }} />
          <span className={styles.value}>{stats.inProgress}</span>
          <span className={styles.label}>Active</span>
        </div>
        <div className={styles.metricItem}>
          <AlertCircle size={14} className={styles.icon} style={{ color: 'var(--error)' }} />
          <span className={styles.value}>{stats.blocked}</span>
          <span className={styles.label}>Blocked</span>
        </div>
        <div className={styles.metricItem}>
          <Circle size={14} className={styles.icon} style={{ color: 'var(--text-tertiary)' }} />
          <span className={styles.value}>{stats.notStarted}</span>
          <span className={styles.label}>Todo</span>
        </div>
      </div>

      <div className={styles.progressSection}>
        {showProgressText && (
          <div className={styles.progressHeader}>
            <span className={styles.progressLabel}>Complete</span>
            <span className={styles.progressValue}>{completionRate}%</span>
          </div>
        )}
        <SegmentedProgressBar stats={stats} />
      </div>
    </div>
  );
};
