import React, { useMemo } from "react";
import { Palette } from "lucide-react";
import { cn } from "../../../lib/utils";
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
 * A button that displays a customization icon, text label, and a simple color
 * preview showing the current theme colors. When clicked, it opens the
 * CustomizationPopup for theme customization.
 *
 * Requirements: 34.1, 34.2, 34.3, 34.4, 34.5, 2.7, 35.1
 * - Display a customization icon (Palette) for clear affordance
 * - Display a descriptive text label ("Theme")
 * - Display a simple color preview showing primary, secondary, and background colors
 * - Use simple, recognizable layout (avoid overly complex miniature UI)
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
  /** Whether to show the customization icon */
  showIcon?: boolean;
  /** Whether to show the text label */
  showLabel?: boolean;
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
 * Playful color preview component showing overlapping color circles
 * Requirements: 35.1
 * - Show primary and secondary colors as distinct color elements
 * - Add background color representation
 * - Use simple, recognizable, playful layout
 */
interface ColorPreviewProps {
  colorScheme: ColorTheme;
  effects: EffectSettings;
}

const ColorPreview: React.FC<ColorPreviewProps> = ({ colorScheme, effects }) => {
  const { colors } = colorScheme;
  const borderRadius = Math.min(effects.borderRadius, 8);

  return (
    <div
      className="relative flex items-center justify-center"
      style={{
        width: 44,
        height: 24,
        borderRadius: `${borderRadius}px`,
        border: "1px solid rgba(128, 128, 128, 0.3)",
        background: `linear-gradient(135deg, ${colors.bgApp} 0%, ${colors.bgSurface} 100%)`,
        boxShadow: "inset 0 1px 2px rgba(0,0,0,0.1)",
      }}
      aria-hidden="true"
    >
      {/* Overlapping color circles - playful palette style */}
      <div className="relative flex items-center" style={{ marginLeft: -2 }}>
        {/* Background/Surface circle */}
        <div
          className="rounded-full shadow-sm"
          style={{
            width: 14,
            height: 14,
            backgroundColor: colors.bgSurface,
            border: `1.5px solid ${colors.textTertiary}`,
            zIndex: 1,
          }}
          title="Surface"
        />
        {/* Primary color circle - overlapping */}
        <div
          className="rounded-full shadow-sm"
          style={{
            width: 14,
            height: 14,
            backgroundColor: colors.primary,
            border: "1.5px solid rgba(255,255,255,0.3)",
            marginLeft: -5,
            zIndex: 2,
          }}
          title="Primary"
        />
        {/* Accent/Success color circle - overlapping */}
        <div
          className="rounded-full shadow-sm"
          style={{
            width: 14,
            height: 14,
            backgroundColor: colors.success,
            border: "1.5px solid rgba(255,255,255,0.3)",
            marginLeft: -5,
            zIndex: 3,
          }}
          title="Accent"
        />
      </div>
    </div>
  );
};

/**
 * CustomizationButton component with icon, label, and simple color preview
 */
export const CustomizationButton: React.FC<CustomizationButtonProps> = ({
  currentScheme = colorThemes.dark,
  typography: _typography = fontThemes.inter, // Kept for API compatibility
  effects = defaultEffectSettings,
  onClick,
  showIcon = true,
  showLabel = true,
  showPreview = true,
  className,
  disabled = false,
  "aria-label": ariaLabel = "Open theme customization",
}) => {
  // _typography is intentionally unused - kept for API compatibility
  void _typography;
  // Memoize the preview to avoid unnecessary re-renders
  const previewContent = useMemo(() => {
    if (!showPreview) {
      return null;
    }

    return (
      <ColorPreview
        colorScheme={currentScheme}
        effects={effects}
      />
    );
  }, [currentScheme, effects, showPreview]);

  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={cn(
        // Base styles
        "relative inline-flex items-center justify-center gap-2",
        "overflow-hidden rounded-lg",
        "border border-[var(--border)]",
        "transition-all duration-200 ease-out",
        // Size - auto width to accommodate icon, label, and preview
        "h-9 px-3 py-1",
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
      {/* Customization icon (Requirement 2.7) */}
      {showIcon && (
        <Palette
          size={16}
          className="text-[var(--text-secondary)] flex-shrink-0"
          aria-hidden="true"
        />
      )}

      {/* Text label (Requirement 2.7) */}
      {showLabel && (
        <span className="text-sm font-medium text-[var(--text-primary)] whitespace-nowrap">
          Theme
        </span>
      )}

      {/* Preview thumbnail (Requirements 34.1, 34.2, 2.7) */}
      {previewContent}

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
