import React, { useRef, useEffect, useCallback } from "react";
import { cn } from "../../../lib/utils";
import { type FontTheme } from "../../../styles/themes";

/**
 * TypographyRow Molecule Component
 *
 * A horizontally scrollable row of typography options that allows users
 * to browse and select from predefined font families. Each option is displayed
 * with a sample text preview in that font.
 *
 * Requirements: 33.1, 33.2, 33.3, 33.4, 33.5
 * - Display horizontally scrollable row of typography options
 * - Show each option with sample text preview in that font
 * - Auto-scroll to selected typography on mount
 * - Handle typography selection and highlight
 */

export interface TypographyRowProps {
  /** Array of typography options to display */
  options: FontTheme[];
  /** ID of the currently selected typography option */
  selectedOptionId: string;
  /** Callback when a typography option is selected */
  onSelect: (optionId: string) => void;
  /** Whether to auto-scroll to the selected option on mount */
  autoScrollToSelected?: boolean;
  /** Additional CSS classes */
  className?: string;
}

/**
 * TypographyRow component for typography selection
 */
export const TypographyRow: React.FC<TypographyRowProps> = ({
  options,
  selectedOptionId,
  onSelect,
  autoScrollToSelected = true,
  className,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const selectedRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to selected typography on mount
  useEffect(() => {
    if (autoScrollToSelected && selectedRef.current && containerRef.current) {
      const container = containerRef.current;
      const selected = selectedRef.current;

      // Calculate scroll position to center the selected item
      const containerWidth = container.clientWidth;
      const selectedLeft = selected.offsetLeft;
      const selectedWidth = selected.clientWidth;

      const scrollPosition =
        selectedLeft - containerWidth / 2 + selectedWidth / 2;

      container.scrollTo({
        left: Math.max(0, scrollPosition),
        behavior: "smooth",
      });
    }
  }, [autoScrollToSelected, selectedOptionId]);

  const handleSelect = useCallback(
    (optionId: string) => {
      onSelect(optionId);
    },
    [onSelect]
  );

  return (
    <div
      ref={containerRef}
      className={cn(
        "flex gap-3 overflow-x-auto py-2 px-1 scrollbar-hide",
        className
      )}
      role="listbox"
      aria-label="Typography selection"
    >
      {options.map((option) => {
        const isSelected = option.id === selectedOptionId;
        return (
          <div
            key={option.id}
            ref={isSelected ? selectedRef : undefined}
            className="flex-shrink-0"
            role="option"
            aria-selected={isSelected}
          >
            <TypographyPreview
              option={option}
              isSelected={isSelected}
              onClick={() => handleSelect(option.id)}
            />
          </div>
        );
      })}
    </div>
  );
};

/**
 * TypographyPreview sub-component for individual typography option
 */
interface TypographyPreviewProps {
  /** Typography option to display */
  option: FontTheme;
  /** Whether this option is currently selected */
  isSelected: boolean;
  /** Click handler for selecting this option */
  onClick: () => void;
}

const TypographyPreview: React.FC<TypographyPreviewProps> = ({
  option,
  isSelected,
  onClick,
}) => {
  // Sample text to demonstrate the font
  const sampleText = "Aa Bb Cc";

  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "relative overflow-hidden rounded-lg transition-all duration-200",
        "focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2",
        "hover:scale-105 hover:shadow-lg",
        isSelected && "ring-2 ring-offset-2"
      )}
      style={{
        width: "120px",
        height: "80px",
        backgroundColor: "var(--bg-surface)",
        borderColor: isSelected ? "var(--primary)" : "var(--border)",
        borderWidth: isSelected ? "2px" : "1px",
        borderStyle: "solid",
        boxShadow: isSelected
          ? "0 0 0 2px var(--primary), 0 4px 12px rgba(0,0,0,0.15)"
          : "0 2px 8px rgba(0,0,0,0.1)",
        // Ring color for focus and selection
        "--tw-ring-color": "var(--primary)",
        "--tw-ring-offset-color": "var(--bg-app)",
      } as React.CSSProperties}
      aria-pressed={isSelected}
      aria-label={`Select ${option.name} typography`}
    >
      {/* Typography Preview Content */}
      <div className="flex flex-col items-center justify-center h-full p-2">
        {/* Sample text in the font */}
        <div
          className="text-lg leading-tight mb-1"
          style={{
            fontFamily: option.fontFamily,
            color: "var(--text-primary)",
          }}
        >
          {sampleText}
        </div>

        {/* Font name */}
        <div
          className="text-xs truncate w-full text-center"
          style={{
            color: "var(--text-secondary)",
          }}
        >
          {option.name}
        </div>

        {/* Category badge */}
        <div
          className="text-[10px] px-1.5 py-0.5 rounded mt-1"
          style={{
            backgroundColor: isSelected
              ? "var(--primary)"
              : "var(--bg-surface-hover)",
            color: isSelected ? "white" : "var(--text-tertiary)",
          }}
        >
          {option.category}
        </div>
      </div>

      {/* Selection indicator overlay */}
      {isSelected && (
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            backgroundColor: "var(--primary)",
            opacity: 0.1,
          }}
        />
      )}
    </button>
  );
};

TypographyRow.displayName = "TypographyRow";

export default TypographyRow;
