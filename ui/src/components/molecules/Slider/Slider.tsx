import React, { useCallback, useId, useMemo } from "react";
import { cn } from "../../../lib/utils";

/**
 * Slider Molecule Component
 *
 * A slider component that displays current value, supports min/max/step
 * configuration, and emits change events. The emitted value is always
 * within [min, max] and aligned to step increments.
 *
 * Requirements: 4.3
 * - Display current value
 * - Support min/max/step configuration
 * - Emit change events
 */

export interface SliderProps {
  /** Current value of the slider */
  value: number;
  /** Callback fired when the slider value changes */
  onChange: (value: number) => void;
  /** Minimum value */
  min: number;
  /** Maximum value */
  max: number;
  /** Step increment (default: 1) */
  step?: number;
  /** Optional label text displayed above the slider */
  label?: string;
  /** Whether to show the current value (default: true) */
  showValue?: boolean;
  /** Additional CSS classes */
  className?: string;
  /** Whether the slider is disabled */
  disabled?: boolean;
  /** ID for the slider input (auto-generated if not provided) */
  id?: string;
  /** Format function for displaying the value */
  formatValue?: (value: number) => string;
  /** Unit to display after the value (e.g., "px", "%") */
  unit?: string;
}

/**
 * Clamp a value to be within [min, max] and aligned to step
 */
function clampAndAlign(value: number, min: number, max: number, step: number): number {
  // Clamp to range
  const clamped = Math.min(Math.max(value, min), max);
  // Align to step
  const steps = Math.round((clamped - min) / step);
  const aligned = min + steps * step;
  // Ensure we don't exceed max due to floating point
  return Math.min(aligned, max);
}

/**
 * Slider component with min/max/step configuration
 */
export const Slider: React.FC<SliderProps> = ({
  value,
  onChange,
  min,
  max,
  step = 1,
  label,
  showValue = true,
  className,
  disabled = false,
  id: providedId,
  formatValue,
  unit,
}) => {
  const generatedId = useId();
  const id = providedId ?? generatedId;

  /**
   * Calculate the percentage position of the thumb
   */
  const percentage = useMemo(() => {
    if (max === min) return 0;
    return ((value - min) / (max - min)) * 100;
  }, [value, min, max]);

  /**
   * Format the displayed value
   */
  const displayValue = useMemo(() => {
    if (formatValue) {
      return formatValue(value);
    }
    // Handle floating point display
    const decimals = step.toString().split(".")[1]?.length ?? 0;
    const formatted = value.toFixed(decimals);
    return unit ? `${formatted}${unit}` : formatted;
  }, [value, formatValue, step, unit]);

  /**
   * Handle slider input change
   */
  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const rawValue = parseFloat(e.target.value);
      const alignedValue = clampAndAlign(rawValue, min, max, step);
      onChange(alignedValue);
    },
    [onChange, min, max, step]
  );

  return (
    <div className={cn("w-full", className)}>
      {/* Label and value display */}
      {(label || showValue) && (
        <div className="flex items-center justify-between mb-2">
          {label && (
            <label
              htmlFor={id}
              className={cn(
                "text-sm font-medium text-[var(--text-primary)]",
                "transition-colors duration-[calc(var(--duration-fast)*var(--animation-speed))]",
                disabled && "opacity-50"
              )}
            >
              {label}
            </label>
          )}
          {showValue && (
            <span
              className={cn(
                "text-sm font-mono text-[var(--text-secondary)]",
                "transition-colors duration-[calc(var(--duration-fast)*var(--animation-speed))]",
                disabled && "opacity-50"
              )}
              aria-live="polite"
            >
              {displayValue}
            </span>
          )}
        </div>
      )}

      {/* Slider track and input */}
      <div className="relative h-5 flex items-center">
        {/* Custom track background */}
        <div
          className={cn(
            "absolute left-0 right-0 h-2 rounded-full bg-[var(--bg-muted)]",
            disabled && "opacity-50"
          )}
        />

        {/* Filled track portion */}
        <div
          className={cn(
            "absolute h-2 rounded-full bg-[var(--primary)]",
            "left-0",
            "transition-all duration-[calc(var(--duration-fast)*var(--animation-speed))]",
            disabled && "opacity-50"
          )}
          style={{ width: `${percentage}%` }}
        />

        {/* Native range input */}
        <input
          type="range"
          id={id}
          value={value}
          onChange={handleChange}
          min={min}
          max={max}
          step={step}
          disabled={disabled}
          className={cn(
            // Input spans full width, height set to match container
            "absolute inset-0 w-full appearance-none bg-transparent cursor-pointer",
            // Thumb styles (WebKit)
            "[&::-webkit-slider-thumb]:appearance-none",
            "[&::-webkit-slider-thumb]:w-5 [&::-webkit-slider-thumb]:h-5",
            "[&::-webkit-slider-thumb]:rounded-full",
            "[&::-webkit-slider-thumb]:bg-white",
            "[&::-webkit-slider-thumb]:shadow-[0_2px_6px_rgba(0,0,0,0.2)]",
            "[&::-webkit-slider-thumb]:border-2 [&::-webkit-slider-thumb]:border-[var(--primary)]",
            "[&::-webkit-slider-thumb]:transition-transform",
            "[&::-webkit-slider-thumb]:duration-[calc(var(--duration-fast)*var(--animation-speed))]",
            "[&::-webkit-slider-thumb]:hover:scale-110",
            "[&::-webkit-slider-thumb]:active:scale-95",
            // Thumb styles (Firefox)
            "[&::-moz-range-thumb]:appearance-none",
            "[&::-moz-range-thumb]:w-5 [&::-moz-range-thumb]:h-5",
            "[&::-moz-range-thumb]:rounded-full",
            "[&::-moz-range-thumb]:bg-white",
            "[&::-moz-range-thumb]:shadow-[0_2px_6px_rgba(0,0,0,0.2)]",
            "[&::-moz-range-thumb]:border-2 [&::-moz-range-thumb]:border-[var(--primary)]",
            "[&::-moz-range-thumb]:transition-transform",
            "[&::-moz-range-thumb]:duration-[calc(var(--duration-fast)*var(--animation-speed))]",
            "[&::-moz-range-thumb]:hover:scale-110",
            "[&::-moz-range-thumb]:active:scale-95",
            "[&::-moz-range-thumb]:border-0",
            // Track styles (WebKit) - transparent, we use custom track divs
            "[&::-webkit-slider-runnable-track]:bg-transparent",
            "[&::-webkit-slider-runnable-track]:h-full",
            // Track styles (Firefox) - transparent, we use custom track divs
            "[&::-moz-range-track]:bg-transparent",
            "[&::-moz-range-track]:h-full",
            // Focus styles
            "focus:outline-none",
            "focus-visible:[&::-webkit-slider-thumb]:ring-2",
            "focus-visible:[&::-webkit-slider-thumb]:ring-[var(--primary)]",
            "focus-visible:[&::-webkit-slider-thumb]:ring-offset-2",
            "focus-visible:[&::-webkit-slider-thumb]:ring-offset-[var(--bg-surface)]",
            "focus-visible:[&::-moz-range-thumb]:ring-2",
            "focus-visible:[&::-moz-range-thumb]:ring-[var(--primary)]",
            "focus-visible:[&::-moz-range-thumb]:ring-offset-2",
            "focus-visible:[&::-moz-range-thumb]:ring-offset-[var(--bg-surface)]",
            // Disabled styles
            disabled && "cursor-not-allowed opacity-50"
          )}
          aria-label={label}
          aria-valuemin={min}
          aria-valuemax={max}
          aria-valuenow={value}
          aria-valuetext={displayValue}
        />
      </div>

      {/* Min/Max labels (optional, shown when no label is provided) */}
      {!label && (
        <div className="flex justify-between mt-1">
          <span
            className={cn(
              "text-xs text-[var(--text-muted)]",
              disabled && "opacity-50"
            )}
          >
            {min}
          </span>
          <span
            className={cn(
              "text-xs text-[var(--text-muted)]",
              disabled && "opacity-50"
            )}
          >
            {max}
          </span>
        </div>
      )}
    </div>
  );
};

Slider.displayName = "Slider";

export default Slider;
