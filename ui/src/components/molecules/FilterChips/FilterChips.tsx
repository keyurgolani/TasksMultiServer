import React, { useCallback, useId } from "react";
import { cn } from "../../../lib/utils";

/**
 * FilterChips Molecule Component
 *
 * A component that displays selectable chip options with multi-select capability.
 * Clicking a chip toggles its selection state and emits the updated selection array.
 *
 * Requirements: 4.4
 * - Displays selectable chip options
 * - Multi-select capability
 * - Accessible with proper ARIA attributes
 */

export interface FilterChipOption {
  /** Unique identifier for the option */
  id: string;
  /** Display label for the chip */
  label: string;
}

export interface FilterChipsProps {
  /** Array of options to display as chips */
  options: FilterChipOption[];
  /** Array of selected option IDs */
  selected: string[];
  /** Callback fired when selection changes */
  onChange: (selected: string[]) => void;
  /** Whether multiple chips can be selected (default: true) */
  multiSelect?: boolean;
  /** Additional CSS classes */
  className?: string;
  /** Size variant of the chips */
  size?: "sm" | "md" | "lg";
  /** Whether the chips are disabled */
  disabled?: boolean;
  /** Accessible label for the chip group */
  "aria-label"?: string;
}

const sizeStyles = {
  sm: "h-7 px-2.5 text-xs gap-1.5",
  md: "h-8 px-3 text-sm gap-2",
  lg: "h-10 px-4 text-base gap-2.5",
};

/**
 * FilterChips component with multi-select capability
 */
export const FilterChips: React.FC<FilterChipsProps> = ({
  options,
  selected,
  onChange,
  multiSelect = true,
  className,
  size = "md",
  disabled = false,
  "aria-label": ariaLabel,
}) => {
  const groupId = useId();

  /**
   * Handle chip click - toggles selection state
   */
  const handleChipClick = useCallback(
    (optionId: string) => {
      if (disabled) return;

      const isSelected = selected.includes(optionId);

      if (multiSelect) {
        // Multi-select: toggle the clicked chip
        if (isSelected) {
          onChange(selected.filter((id) => id !== optionId));
        } else {
          onChange([...selected, optionId]);
        }
      } else {
        // Single-select: select only the clicked chip (or deselect if already selected)
        if (isSelected) {
          onChange([]);
        } else {
          onChange([optionId]);
        }
      }
    },
    [disabled, multiSelect, onChange, selected]
  );

  /**
   * Handle keyboard interaction for accessibility
   */
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent, optionId: string) => {
      if (disabled) return;

      if (e.key === " " || e.key === "Enter") {
        e.preventDefault();
        handleChipClick(optionId);
      }
    },
    [disabled, handleChipClick]
  );

  return (
    <div
      role="group"
      aria-label={ariaLabel ?? "Filter options"}
      className={cn("flex flex-wrap gap-2", className)}
    >
      {options.map((option) => {
        const isSelected = selected.includes(option.id);
        const chipId = `${groupId}-chip-${option.id}`;

        return (
          <button
            key={option.id}
            id={chipId}
            type="button"
            role="checkbox"
            aria-checked={isSelected}
            disabled={disabled}
            onClick={() => handleChipClick(option.id)}
            onKeyDown={(e) => handleKeyDown(e, option.id)}
            className={cn(
              // Base styles
              "inline-flex items-center justify-center rounded-full",
              "font-medium whitespace-nowrap cursor-pointer",
              "border-2",
              // Transition for smooth animation
              "transition-all duration-[calc(var(--duration-normal)*var(--animation-speed))] ease-[var(--ease-default)]",
              // Focus styles
              "focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--primary)] focus-visible:ring-offset-2 focus-visible:ring-offset-[var(--bg-surface)]",
              // Size styles
              sizeStyles[size],
              // State styles
              isSelected
                ? [
                    "bg-[var(--primary)]",
                    "text-white",
                    "border-[var(--primary)]",
                    "shadow-sm",
                  ]
                : [
                    "bg-transparent",
                    "text-[var(--text-primary)]",
                    "border-[var(--border-default)]",
                    "hover:border-[var(--primary)]",
                    "hover:text-[var(--primary)]",
                  ],
              // Disabled styles
              disabled && "cursor-not-allowed opacity-50 pointer-events-none"
            )}
          >
            {/* Checkmark icon for selected state */}
            {isSelected && (
              <svg
                className="w-3.5 h-3.5 mr-1"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
                strokeWidth={3}
                aria-hidden="true"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M5 13l4 4L19 7"
                />
              </svg>
            )}
            {option.label}
          </button>
        );
      })}
    </div>
  );
};

FilterChips.displayName = "FilterChips";

export default FilterChips;
