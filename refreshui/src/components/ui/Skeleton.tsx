import React from 'react';
import styles from './Skeleton.module.css';

interface SkeletonProps {
  variant?: 'text' | 'rect' | 'circle';
  width?: string | number;
  height?: string | number;
  className?: string;
  style?: React.CSSProperties;
}

export const Skeleton: React.FC<SkeletonProps> = ({ 
  variant = 'text', 
  width, 
  height, 
  className = '',
  style: customStyle,
}) => {
  const style = {
    width,
    height,
    ...customStyle,
  };

  return (
    <div 
      className={`${styles.skeleton} ${styles[`skeleton_${variant}`]} ${className}`}
      style={style}
    />
  );
};
