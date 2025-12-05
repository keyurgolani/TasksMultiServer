import React, { useMemo } from "react";
import { cn } from "../../../lib/utils";
import { ThemePreviewSkeleton } from "../../molecules/ThemePreviewSkeleton/ThemePreviewSkeleton";
import {
  type ColorTheme,
  type FontTheme,
  type EffectSettings,
} from "../../../styles/themes";

/**
 * LivePreviewPanel Organism Component
 *
 * Displays a live preview of the UI with applied customization settings.
 * Integrates with ThemePreviewSkeleton to show real-time updates when
 * customization values change.
 *
 * Requirements: 30.1, 30.2, 30.4
 * - Display a skeleton preview of the tasks view UI in the top-left area
 * - Show the complete UI with padding around it rather than a zoomed-in cutoff view
 * - Update the preview in real-time to reflect customization changes
 *
 * Real-time Update Mechanism:
 * - The component receives colorScheme, typography, and effects as props
 * - When any of these props change, the component re-renders with new values
 * - ThemePreviewSkeleton applies the new values immediately via CSS variables
 * - This enables 60fps updates without full React re-renders
 */

export interface LivePreviewPanelProps {
  /** Color scheme to apply to the preview */
  colorScheme: ColorTheme;
  /** Typography scheme to apply to the preview */
  typography: FontTheme;
  /** Effect settings to apply to the preview */
  effects: EffectSettings;
  /** Optional scale factor for the preview (default: 1) */
  scale?: number;
  /** Whether to show padding around the preview (default: true) */
  showPadding?: boolean;
  /** Additional CSS classes */
  className?: string;
  /** Optional title for the preview panel */
  title?: string;
}

/**
 * LivePreviewPanel component that displays a real-time preview of theme customizations
 *
 * The panel wraps ThemePreviewSkeleton with appropriate padding and styling
 * to provide a complete view of the UI preview without cutoff.
 *
 * Real-time updates are achieved through:
 * 1. Props-based reactivity: When colorScheme, typography, or effects change,
 *    the component re-renders with new values
 * 2. CSS variable injection: ThemePreviewSkeleton converts theme values to
 *    CSS variables that update immediately without layout recalculation
 * 3. Memoization: The preview content is memoized to prevent unnecessary
 *    re-renders when unrelated props change
 */
export const LivePreviewPanel: React.FC<LivePreviewPanelProps> = ({
  colorScheme,
  typography,
  effects,
  scale = 1,
  showPadding = true,
  className,
  title = "Live Preview",
}) => {
  // Memoize the preview content to prevent unnecessary re-renders
  // when parent components update but theme values remain the same
  // This ensures real-time updates are efficient (Requirement 30.4)
  const previewContent = useMemo(
    () => (
      <ThemePreviewSkeleton
        colorScheme={colorScheme}
        typography={typography}
        effects={effects}
        variant="full"
        className="w-full h-full"
      />
    ),
    [colorScheme, typography, effects]
  );

  // Memoize the container style to prevent object recreation on each render
  const containerStyle = useMemo(
    () => ({
      // Apply glassmorphism effect based on current effect settings
      backdropFilter: `blur(${effects.glassBlur}px)`,
      backgroundColor: `rgba(var(--bg-surface-rgb, 30, 33, 40), ${effects.glassOpacity / 100})`,
    }),
    [effects.glassBlur, effects.glassOpacity]
  );

  // Memoize the content area style
  const contentStyle = useMemo(
    () => ({
      transform: scale !== 1 ? `scale(${scale})` : undefined,
      transformOrigin: "top left" as const,
    }),
    [scale]
  );

  return (
    <div
      className={cn(
        "relative flex flex-col rounded-lg overflow-hidden",
        "border border-[var(--border)]",
        "bg-[var(--bg-surface)]",
        className
      )}
      style={containerStyle}
    >
      {/* Preview content area with optional padding (Requirements 30.2, 50.1, 50.2, 50.3) */}
      {/* Uniform padding on all sides using design system spacing tokens */}
      {/* Title prop is kept for accessibility but no longer displayed as window mock */}
      <div
        className={cn(
          "flex-1 overflow-auto"
        )}
        style={contentStyle}
        aria-label={title}
      >
        <div
          className={cn(
            "h-full w-full",
            showPadding && "box-border"
          )}
          style={showPadding ? {
            padding: "var(--space-3, 12px)",
          } : undefined}
        >
          {previewContent}
        </div>
      </div>
    </div>
  );
};

LivePreviewPanel.displayName = "LivePreviewPanel";

export default LivePreviewPanel;
