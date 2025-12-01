import React from 'react';
import styles from './Input.module.css';
import clsx from 'clsx';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  icon?: React.ReactNode;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ label, icon, className, ...props }, ref) => {
    return (
      <div className={styles.inputWrapper}>
        {label && <label className={styles.label}>{label}</label>}
        <div className={styles.inputContainer}>
            {icon && <span className={styles.icon}>{icon}</span>}
            <input
            ref={ref}
            className={clsx(styles.input, icon && styles.hasIcon, className)}
            {...props}
            />
        </div>
      </div>
    );
  }
);

Input.displayName = 'Input';
