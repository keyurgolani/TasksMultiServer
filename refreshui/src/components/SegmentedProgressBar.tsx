import React from 'react';
import styles from './SegmentedProgressBar.module.css';

interface SegmentedProgressBarProps {
  stats: {
    completed: number;
    inProgress: number;
    blocked: number;
    notStarted: number;
    total: number;
  };
  height?: number;
}

export const SegmentedProgressBar: React.FC<SegmentedProgressBarProps> = ({ stats, height = 6 }) => {
  const { completed, inProgress, blocked, notStarted, total } = stats;
  
  if (total === 0) {
    return (
      <div className={styles.progressBar} style={{ height }}>
        <div style={{ width: '100%', height: '100%', backgroundColor: 'rgba(127, 127, 127, 0.2)' }} />
      </div>
    );
  }

  const getPercentage = (value: number) => (value / total) * 100;

  const pCompleted = getPercentage(completed);
  const pInProgress = getPercentage(inProgress);
  const pBlocked = getPercentage(blocked);
  // pNotStarted is the remainder

  // Calculate cumulative points
  const c1 = pCompleted;
  const c2 = c1 + pInProgress;
  const c3 = c2 + pBlocked;
  
  // Blend width in percentage
  const blend = 2;

  // Helper to ensure monotonicity and bounds
  const clamp = (val: number) => Math.max(0, Math.min(100, val));

  // Build gradient string
  // Sequence: Success -> Warning -> Error -> Empty
  // We use hard stops with a small blend distance to create the "smooth" but distinct transition
  
  const gradient = `linear-gradient(to right, 
    var(--success) 0%, 
    var(--success) ${clamp(c1 - blend)}%, 
    var(--warning) ${clamp(c1 + blend)}%, 
    var(--warning) ${clamp(c2 - blend)}%, 
    var(--error) ${clamp(c2 + blend)}%, 
    var(--error) ${clamp(c3 - blend)}%, 
    rgba(127, 127, 127, 0.2) ${clamp(c3 + blend)}%, 
    rgba(127, 127, 127, 0.2) 100%
  )`;

  return (
    <div 
      className={styles.progressBar} 
      style={{ 
        height, 
        background: gradient,
        transition: 'background 0.3s ease'
      }} 
      title={`Done: ${completed}, Active: ${inProgress}, Blocked: ${blocked}, Todo: ${notStarted}`}
    />
  );
};
