import React, { useMemo } from "react";
import { cn } from "../../../lib/utils";
import { ThemePreviewSkeleton } from "../../molecules/ThemePreviewSkeleton";
import {
  type ColorTheme,
  type FontTheme,
  type EffectSettings,
  colorThemes,
  fontThemes,
  defaultEffectSettings,
} from "../../../styles/themes";

/**
 * CustomizationButton Atom Component
 *
 * A button that displays a tiny preview thumbnail of the current theme.
 * When clicked, it opens the CustomizationPopup for theme customization.
 *
 * Requirements: 34.1, 34.2, 34.3, 34.4, 34.5
 * - Display a tiny preview thumbnail showing the current color scheme
 * - Show a miniature version of the full preview layout
 * - Update the button preview when color scheme changes
 * - Provide visual feedback using design system hover states
 * - Open the customization popup when clicked
 */

export interface CustomizationButtonProps {
  /** Current color scheme to display in the preview */
  currentScheme?: ColorTheme;
  /** Current typography scheme */
  typography?: FontTheme;
  /** Current effect settings */
  effects?: EffectSettings;
  /** Click handler to open the customization popup */
  onClick: () => void;
  /** Whether to show the preview thumbnail */
  showPreview?: boolean;
  /** Additional CSS classes */
  className?: string;
  /** Disabled state */
  disabled?: boolean;
  /** Aria label for accessibility */
  "aria-label"?: string;
}

/**
 * CustomizationButton component with tiny theme preview
 */
export const CustomizationButton: React.FC<CustomizationButtonProps> = ({
  currentScheme = colorThemes.dark,
  typography = fontThemes.inter,
  effects = defaultEffectSettings,
  onClick,
  showPreview = true,
  className,
  disabled = false,
  "aria-label": ariaLabel = "Open theme customization",
}) => {
  // Memoize the preview to avoid unnecessary re-renders
  const previewContent = useMemo(() => {
    if (!showPreview) {
      return null;
    }

    return (
      <ThemePreviewSkeleton
        colorScheme={currentScheme}
        typography={typography}
        effects={effects}
        variant="button"
        className="pointer-events-none"
      />
    );
  }, [currentScheme, typography, effects, showPreview]);

  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={cn(
        // Base styles
        "relative inline-flex items-center justify-center",
        "overflow-hidden rounded-lg",
        "border border-[var(--border)]",
        "transition-all duration-200 ease-out",
        // Size - slightly larger than the preview to add padding
        "w-12 h-9 p-1",
        // Background with glassmorphism
        "bg-[var(--bg-surface)]",
        // Hover states (Requirement 34.4)
        "hover:scale-105",
        "hover:border-[var(--primary)]",
        "hover:shadow-[0_4px_12px_var(--shadow)]",
        "hover:-translate-y-0.5",
        // Focus states
        "focus:outline-none",
        "focus-visible:ring-2",
        "focus-visible:ring-[var(--primary)]",
        "focus-visible:ring-offset-2",
        "focus-visible:ring-offset-[var(--bg-app)]",
        // Active state
        "active:scale-[0.98]",
        // Disabled state
        "disabled:opacity-50",
        "disabled:cursor-not-allowed",
        "disabled:hover:scale-100",
        "disabled:hover:translate-y-0",
        "disabled:hover:shadow-none",
        className
      )}
      aria-label={ariaLabel}
      data-testid="customization-button"
    >
      {/* Preview thumbnail (Requirements 34.1, 34.2) */}
      {previewContent}

      {/* Fallback icon when preview is disabled */}
      {!showPreview && (
        <svg
          width="20"
          height="20"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="text-[var(--text-secondary)]"
        >
          <circle cx="12" cy="12" r="3" />
          <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z" />
        </svg>
      )}

      {/* Hover overlay for visual feedback */}
      <div
        className={cn(
          "absolute inset-0 pointer-events-none",
          "bg-[var(--primary)] opacity-0",
          "transition-opacity duration-200",
          "group-hover:opacity-10"
        )}
      />
    </button>
  );
};

CustomizationButton.displayName = "CustomizationButton";

export default CustomizationButton;
