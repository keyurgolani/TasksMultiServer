import React from 'react';
import { X } from 'lucide-react';
import styles from './Input.module.css';
import clsx from 'clsx';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  icon?: React.ReactNode;
  onClear?: () => void;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ label, icon, onClear, className, value, ...props }, ref) => {
    const hasValue = value !== undefined && value !== '';
    const showClearIcon = hasValue && onClear;

    return (
      <div className={styles.inputWrapper}>
        {label && <label className={styles.label}>{label}</label>}
        <div className={styles.inputContainer}>
            {icon && !showClearIcon && <span className={styles.icon}>{icon}</span>}
            {showClearIcon && (
              <button
                type="button"
                className={styles.iconButton}
                onClick={onClear}
                aria-label="Clear input"
              >
                <X size={16} />
              </button>
            )}
            <input
            ref={ref}
            className={clsx(
              styles.input, 
              (icon || showClearIcon) && styles.hasIcon,
              className
            )}
            value={value}
            {...props}
            />
        </div>
      </div>
    );
  }
);

Input.displayName = 'Input';
