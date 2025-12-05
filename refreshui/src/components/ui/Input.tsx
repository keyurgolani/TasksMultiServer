import React from 'react';
import { X, AlertCircle } from 'lucide-react';
import styles from './Input.module.css';
import clsx from 'clsx';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  icon?: React.ReactNode;
  onClear?: () => void;
  error?: string;
  state?: 'default' | 'focus' | 'error' | 'disabled';
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ label, icon, onClear, error, state, className, value, disabled, ...props }, ref) => {
    const hasValue = value !== undefined && value !== '';
    const showClearIcon = hasValue && onClear;
    const hasError = !!error || state === 'error';
    const isDisabled = disabled || state === 'disabled';

    return (
      <div className={styles.inputWrapper}>
        {label && (
          <label className={clsx(styles.label, hasError && styles.labelError)}>
            {label}
          </label>
        )}
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
              hasError && styles.inputError,
              isDisabled && styles.inputDisabled,
              className
            )}
            value={value}
            disabled={isDisabled}
            aria-invalid={hasError}
            aria-describedby={error ? `${props.id || 'input'}-error` : undefined}
            {...props}
            />
        </div>
        {error && (
          <div 
            className={styles.errorMessage}
            id={`${props.id || 'input'}-error`}
            role="alert"
          >
            <AlertCircle size={14} className={styles.errorIcon} />
            <span>{error}</span>
          </div>
        )}
      </div>
    );
  }
);

Input.displayName = 'Input';
