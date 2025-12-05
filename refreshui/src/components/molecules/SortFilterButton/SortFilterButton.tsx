import React from "react";
import { cn } from "../../../lib/utils";
import { Icon } from "../../atoms/Icon";

/**
 * SortFilterButton Molecule Component
 *
 * A button component for triggering sort/filter popups with visual feedback
 * for active filter states. Displays an icon and label, with an X icon for
 * quick reset when filters are active.
 *
 * Requirements: 26.1, 26.2, 26.3, 26.4, 26.5
 * - Displays a button with sort/filter icon and label
 * - Opens popup on click
 * - Shows active state styling when non-default filters are selected
 * - Displays X icon when filters are active for quick reset
 * - Clicking X icon resets filters without opening popup
 */

export interface SortFilterButtonProps {
  /** Whether any non-default sort or filter is currently active */
  isActive: boolean;
  /** Callback fired when the button is clicked to open the popup */
  onOpenPopup: () => void;
  /** Callback fired when the reset (X) icon is clicked */
  onReset: () => void;
  /** Label text for the button */
  label?: string;
  /** Additional CSS classes */
  className?: string;
  /** Whether the button is disabled */
  disabled?: boolean;
}

/** Base styles applied to the button */
const baseStyles = [
  "inline-flex",
  "items-center",
  "justify-center",
  "gap-2",
  "h-10",
  "px-3",
  "font-medium",
  "text-sm",
  "cursor-pointer",
  "transition-all",
  "duration-200",
  "ease-out",
  "border",
  "rounded-lg",
  "outline-none",
  "relative",
  "select-none",
  "disabled:opacity-50",
  "disabled:cursor-not-allowed",
  "disabled:pointer-events-none",
].join(" ");

/** Default (inactive) state styles */
const inactiveStyles = [
  "bg-[var(--bg-surface)]",
  "text-[var(--text-secondary)]",
  "border-[var(--border)]",
  "hover:bg-[var(--bg-surface-hover)]",
  "hover:text-[var(--text-primary)]",
  "hover:border-[var(--primary)]",
  "focus-visible:ring-2",
  "focus-visible:ring-[var(--primary)]",
  "focus-visible:ring-offset-2",
].join(" ");

/** Active state styles when filters are applied */
const activeStyles = [
  "bg-[rgba(var(--primary-rgb),0.1)]",
  "text-[var(--primary)]",
  "border-[var(--primary)]",
  "hover:bg-[rgba(var(--primary-rgb),0.15)]",
  "focus-visible:ring-2",
  "focus-visible:ring-[var(--primary)]",
  "focus-visible:ring-offset-2",
].join(" ");

/**
 * SortFilterButton component
 */
export const SortFilterButton: React.FC<SortFilterButtonProps> = ({
  isActive,
  onOpenPopup,
  onReset,
  label = "Sort & Filter",
  className,
  disabled = false,
}) => {
  /**
   * Handle button click - opens the popup
   * Requirements: 26.2
   */
  const handleButtonClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    if (disabled) return;
    
    // If clicking on the reset icon area, don't open popup
    const target = e.target as HTMLElement;
    if (target.closest('[data-reset-button]')) {
      return;
    }
    
    onOpenPopup();
  };

  /**
   * Handle reset icon click - resets filters without opening popup
   * Requirements: 26.5
   */
  const handleResetClick = (e: React.MouseEvent<HTMLButtonElement>) => {
    e.stopPropagation();
    if (disabled) return;
    onReset();
  };

  // Animation styles for icon transitions
  const iconTransitionStyle = {
    transition: `opacity calc(var(--duration-normal, 0.3s) * var(--animation-speed, 1)), transform calc(var(--duration-normal, 0.3s) * var(--animation-speed, 1))`,
  };

  return (
    <button
      type="button"
      onClick={handleButtonClick}
      className={cn(
        baseStyles,
        isActive ? activeStyles : inactiveStyles,
        className
      )}
      disabled={disabled}
      aria-label={isActive ? `${label} (filters active)` : label}
      aria-pressed={isActive}
    >
      {/* Sort/Filter icon */}
      <Icon name="SlidersHorizontal" size="sm" />

      {/* Label */}
      <span className="whitespace-nowrap">{label}</span>

      {/* Reset (X) icon - visible only when filters are active */}
      {/* Requirements: 26.4, 26.5 */}
      <span
        className={cn(
          "relative flex items-center justify-center w-4 h-4 ml-1",
          isActive ? "opacity-100" : "opacity-0 pointer-events-none"
        )}
        style={iconTransitionStyle}
      >
        <button
          type="button"
          data-reset-button
          onClick={handleResetClick}
          className={cn(
            "flex items-center justify-center w-full h-full rounded-full",
            "hover:bg-[rgba(var(--primary-rgb),0.2)]",
            "transition-colors duration-150",
            !isActive && "pointer-events-none"
          )}
          aria-label="Reset filters"
          tabIndex={isActive ? 0 : -1}
          disabled={!isActive || disabled}
        >
          <Icon name="X" size={14} />
        </button>
      </span>
    </button>
  );
};

SortFilterButton.displayName = "SortFilterButton";

export default SortFilterButton;
