import React from 'react';
import { useTilt } from '../../hooks/useTilt';
import styles from './Card.module.css';
import clsx from 'clsx';
import { motion } from 'framer-motion';
import type { HTMLMotionProps } from 'framer-motion';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  interactive?: boolean;
  children: React.ReactNode;
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ interactive = false, children, className, style, ...props }, ref) => {
    const { onMouseMove, onMouseLeave, style: tiltStyle } = useTilt({ effect: 'lift' });

    return (
      <motion.div
        ref={ref}
        className={clsx(
          styles.card, 
          interactive && styles.interactive, 
          interactive && 'hover-lift',
          className
        )}
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
        onMouseMove={interactive ? onMouseMove : undefined}
        onMouseLeave={interactive ? onMouseLeave : undefined}
        style={{ ...style, ...(interactive ? tiltStyle : {}) }}
        {...(props as HTMLMotionProps<"div">)}
      >
        {children}
      </motion.div>
    );
  }
);

Card.displayName = 'Card';
