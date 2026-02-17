import React, { useRef, useEffect, useCallback } from "react";
import { cn } from "../../../lib/utils";
import { type ColorTheme } from "../../../styles/themes";
import { ColorSchemeMiniPreview } from "../ColorSchemeMiniPreview";

/**
 * ColorSchemeRow Molecule Component
 *
 * A horizontally scrollable row of color scheme options that allows users
 * to browse and select from predefined color schemes. Each scheme is displayed
 * as a mini preview thumbnail.
 *
 * Requirements: 32.1, 32.2, 32.3, 32.4, 32.5
 * - Display horizontally scrollable row of color scheme options
 * - Show each scheme as a mini preview thumbnail
 * - Auto-scroll to selected scheme on mount
 * - Handle scheme selection and highlight
 */

export interface ColorSchemeRowProps {
  /** Array of color schemes to display */
  schemes: ColorTheme[];
  /** ID of the currently selected scheme */
  selectedSchemeId: string;
  /** Callback when a scheme is selected */
  onSelect: (schemeId: string) => void;
  /** Whether to auto-scroll to the selected scheme on mount */
  autoScrollToSelected?: boolean;
  /** Additional CSS classes */
  className?: string;
}

/**
 * ColorSchemeRow component for color scheme selection
 */
export const ColorSchemeRow: React.FC<ColorSchemeRowProps> = ({
  schemes,
  selectedSchemeId,
  onSelect,
  autoScrollToSelected = true,
  className,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const selectedRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to selected scheme on mount
  useEffect(() => {
    if (autoScrollToSelected && selectedRef.current && containerRef.current) {
      const container = containerRef.current;
      const selected = selectedRef.current;
      
      // Calculate scroll position to center the selected item
      const containerWidth = container.clientWidth;
      const selectedLeft = selected.offsetLeft;
      const selectedWidth = selected.clientWidth;
      
      const scrollPosition = selectedLeft - (containerWidth / 2) + (selectedWidth / 2);
      
      container.scrollTo({
        left: Math.max(0, scrollPosition),
        behavior: "smooth",
      });
    }
  }, [autoScrollToSelected, selectedSchemeId]);

  const handleSelect = useCallback(
    (schemeId: string) => {
      onSelect(schemeId);
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
      aria-label="Color scheme selection"
    >
      {schemes.map((scheme) => {
        const isSelected = scheme.id === selectedSchemeId;
        return (
          <div
            key={scheme.id}
            ref={isSelected ? selectedRef : undefined}
            className="flex-shrink-0"
            role="option"
            aria-selected={isSelected}
          >
            <ColorSchemeMiniPreview
              scheme={scheme}
              isSelected={isSelected}
              onClick={() => handleSelect(scheme.id)}
              size="md"
            />
          </div>
        );
      })}
    </div>
  );
};

ColorSchemeRow.displayName = "ColorSchemeRow";

export default ColorSchemeRow;
