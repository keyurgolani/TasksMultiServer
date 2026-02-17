import React, { useCallback, useId } from "react";
import { cn } from "../../../lib/utils";

/**
 * Toggle Molecule Component
 *
 * A toggle switch component that provides on/off state with smooth
 * animation using CSS transitions. Clicking inverts the checked state
 * and triggers onChange with the new value.
 *
 * Requirements: 4.2
 * - Provides on/off state
 * - Smooth animation using CSS transitions
 * - Accessible with proper ARIA attributes
 */

export interface ToggleProps {
  /** Whether the toggle is checked (on) */
  checked: boolean;
  /** Callback fired when the toggle state changes */
  onChange: (checked: boolean) => void;
  /** Optional label text displayed next to the toggle */
  label?: string;
  /** Whether the toggle is disabled */
  disabled?: boolean;
  /** Additional CSS classes */
  className?: string;
  /** Size variant of the toggle */
  size?: "sm" | "md" | "lg";
  /** ID for the toggle input (auto-generated if not provided) */
  id?: string;
}

const sizeStyles = {
  sm: {
    track: "w-8 h-4",
    thumb: "w-3 h-3",
    thumbTranslate: "translate-x-4",
    label: "text-sm",
  },
  md: {
    track: "w-11 h-6",
    thumb: "w-5 h-5",
    thumbTranslate: "translate-x-5",
    label: "text-base",
  },
  lg: {
    track: "w-14 h-7",
    thumb: "w-6 h-6",
    thumbTranslate: "translate-x-7",
    label: "text-lg",
  },
};

/**
 * Toggle component with smooth animation
 */
export const Toggle: React.FC<ToggleProps> = ({
  checked,
  onChange,
  label,
  disabled = false,
  className,
  size = "md",
  id: providedId,
}) => {
  const generatedId = useId();
  const id = providedId ?? generatedId;
  const styles = sizeStyles[size];

  /**
   * Handle toggle click - inverts the checked state
   */
  const handleClick = useCallback(() => {
    if (!disabled) {
      onChange(!checked);
    }
  }, [checked, disabled, onChange]);

  /**
   * Handle keyboard interaction for accessibility
   */
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (disabled) return;

      if (e.key === " " || e.key === "Enter") {
        e.preventDefault();
        onChange(!checked);
      }
    },
    [checked, disabled, onChange]
  );

  return (
    <div className={cn("inline-flex items-center gap-3", className)}>
      {/* Hidden checkbox for form compatibility */}
      <input
        type="checkbox"
        id={id}
        checked={checked}
        onChange={() => onChange(!checked)}
        disabled={disabled}
        className="sr-only"
        aria-hidden="true"
      />

      {/* Toggle track and thumb */}
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        aria-labelledby={label ? `${id}-label` : undefined}
        disabled={disabled}
        onClick={handleClick}
        onKeyDown={handleKeyDown}
        className={cn(
          // Base track styles
          "relative inline-flex shrink-0 cursor-pointer rounded-full",
          "border-2 border-transparent",
          // Transition for smooth animation
          "transition-colors duration-[calc(var(--duration-normal)*var(--animation-speed))] ease-[var(--ease-default)]",
          // Focus styles
          "focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--primary)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--bg-surface)]",
          // Size styles
          styles.track,
          // State styles
          checked
            ? "bg-[var(--primary)]"
            : "bg-[var(--border-strong)]",
          // Disabled styles
          disabled && "cursor-not-allowed opacity-50"
        )}
      >
        {/* Thumb */}
        <span
          aria-hidden="true"
          className={cn(
            // Base thumb styles
            "pointer-events-none inline-block rounded-full bg-white shadow-lg ring-0",
            // Transition for smooth animation
            "transform transition-transform duration-[calc(var(--duration-normal)*var(--animation-speed))] ease-[var(--ease-bounce)]",
            // Size styles
            styles.thumb,
            // Position based on checked state
            checked ? styles.thumbTranslate : "translate-x-0"
          )}
        />
      </button>

      {/* Label */}
      {label && (
        <span
          id={`${id}-label`}
          className={cn(
            "cursor-pointer select-none text-[var(--text-primary)]",
            "transition-colors duration-[calc(var(--duration-fast)*var(--animation-speed))]",
            styles.label,
            disabled && "cursor-not-allowed opacity-50"
          )}
          onClick={handleClick}
        >
          {label}
        </span>
      )}
    </div>
  );
};

Toggle.displayName = "Toggle";

export default Toggle;
