import React, { useState, useEffect, useCallback, useRef } from "react";
import { Input } from "../../atoms/Input";
import { Icon } from "../../atoms/Icon";
import { cn } from "../../../lib/utils";

/**
 * SearchBar Molecule Component
 *
 * A search input component that combines Input and Icon atoms with
 * debounced search functionality. Emits onChange only after the
 * debounce period has elapsed since the last keystroke.
 *
 * Requirements: 4.1, 25.1, 25.2, 25.3, 25.4, 25.5
 * - Combines Input and Icon atoms
 * - Debounced search functionality
 * - Configurable debounce delay
 * - Shows search icon on right when empty
 * - Shows X (clear) icon on right when containing text
 * - Smooth animation for icon transitions using design system animation speed
 */

export interface SearchBarProps {
  /** Placeholder text for the search input */
  placeholder?: string;
  /** Controlled value of the search input */
  value?: string;
  /** Callback fired after debounce period with the search value */
  onChange?: (value: string) => void;
  /** Debounce delay in milliseconds (default: 300ms) */
  debounceMs?: number;
  /** Additional CSS classes */
  className?: string;
  /** Whether the search bar is disabled */
  disabled?: boolean;
  /** Callback fired immediately on input change (before debounce) */
  onImmediateChange?: (value: string) => void;
  /** Callback fired when the clear button is clicked */
  onClear?: () => void;
  /** Auto-focus the input on mount */
  autoFocus?: boolean;
}

/**
 * SearchBar component with debounced search
 */
export const SearchBar: React.FC<SearchBarProps> = ({
  placeholder = "Search...",
  value: controlledValue,
  onChange,
  debounceMs = 300,
  className,
  disabled = false,
  onImmediateChange,
  onClear,
  autoFocus = false,
}) => {
  // Internal state for immediate UI updates
  const [internalValue, setInternalValue] = useState(controlledValue ?? "");
  const debounceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Sync internal value with controlled value
  /* eslint-disable react-hooks/set-state-in-effect -- Syncing internal state with controlled prop */
  useEffect(() => {
    if (controlledValue !== undefined) {
      setInternalValue(controlledValue);
    }
  }, [controlledValue]);
  /* eslint-enable react-hooks/set-state-in-effect */

  // Cleanup debounce timer on unmount
  useEffect(() => {
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, []);

  // Auto-focus on mount if requested
  useEffect(() => {
    if (autoFocus && inputRef.current) {
      inputRef.current.focus();
    }
  }, [autoFocus]);

  /**
   * Handle input change with debouncing
   */
  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const newValue = e.target.value;

      // Update internal state immediately for responsive UI
      setInternalValue(newValue);

      // Fire immediate change callback if provided
      onImmediateChange?.(newValue);

      // Clear existing debounce timer
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }

      // Set new debounce timer
      debounceTimerRef.current = setTimeout(() => {
        onChange?.(newValue);
      }, debounceMs);
    },
    [onChange, onImmediateChange, debounceMs]
  );

  /**
   * Handle clear button click
   */
  const handleClear = useCallback(() => {
    setInternalValue("");

    // Clear any pending debounce
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }

    // Fire callbacks immediately on clear
    onImmediateChange?.("");
    onChange?.("");
    onClear?.();

    // Focus the input after clearing
    inputRef.current?.focus();
  }, [onChange, onImmediateChange, onClear]);

  /**
   * Handle key down events
   */
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLInputElement>) => {
      // Clear on Escape key
      if (e.key === "Escape" && internalValue) {
        handleClear();
      }
    },
    [internalValue, handleClear]
  );

  const hasValue = internalValue.length > 0;
  const showClearButton = hasValue && !disabled;

  /**
   * Render the right icon with smooth animation transition
   * Requirements 25.1, 25.2, 25.5, 44.1, 44.2, 44.3, 44.4:
   * - Shows exactly one search icon when empty
   * - Shows exactly one X (clear) icon when containing text
   * - Ensures only one icon is visible at any time during transitions
   * - Smooth animation for icon transitions
   */
  const renderRightIcon = () => {
    // Animation styles using design system animation speed
    const iconTransitionStyle = {
      transition: `opacity calc(var(--duration-normal, 0.3s) * var(--animation-speed, 1)), transform calc(var(--duration-normal, 0.3s) * var(--animation-speed, 1))`,
    };

    // Render only one icon at a time to prevent duplicate icons
    // Requirements 44.1, 44.2, 44.3: Ensure exactly one icon is visible
    if (showClearButton) {
      // Clear button - visible when has value and not disabled
      return (
        <div className="relative flex items-center justify-center w-5 h-5">
          <button
            type="button"
            onClick={handleClear}
            className="flex items-center justify-center cursor-pointer hover:text-[var(--text-primary)] p-0.5 rounded-sm hover:bg-[var(--bg-muted)] opacity-100 scale-100"
            style={iconTransitionStyle}
            aria-label="Clear search"
            aria-hidden={false}
            tabIndex={0}
          >
            <Icon name="X" size="sm" />
          </button>
        </div>
      );
    }

    // Search icon - visible when empty or disabled
    return (
      <div className="relative flex items-center justify-center w-5 h-5">
        <span
          className="flex items-center justify-center opacity-100 scale-100"
          style={iconTransitionStyle}
          aria-hidden={false}
        >
          <Icon name="Search" size="sm" />
        </span>
      </div>
    );
  };

  return (
    <div className={cn("relative w-full", className)}>
      <Input
        ref={inputRef}
        type="search"
        placeholder={placeholder}
        value={internalValue}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        disabled={disabled}
        rightIcon={renderRightIcon()}
        aria-label="Search"
      />
    </div>
  );
};

SearchBar.displayName = "SearchBar";

export default SearchBar;
