import React from "react";
import { cn } from "../../../lib/utils";

/**
 * GrainOverlay Component
 *
 * A visual effect component that renders a fixed overlay with a noise/grain pattern.
 * The grain texture adds a subtle film-like quality to the UI, enhancing the
 * premium aesthetic of the application.
 *
 * Requirements: 6.2
 * - Renders a fixed overlay with noise pattern at configurable opacity
 * - Uses CSS variables for default opacity (--grain-opacity)
 * - Can be overridden with explicit opacity prop
 *
 * The noise pattern is generated using an SVG filter with fractal noise,
 * which creates a natural-looking grain texture without requiring external assets.
 */

export interface GrainOverlayProps {
  /**
   * Opacity of the grain overlay (0-1).
   * If not provided, uses the CSS variable --grain-opacity.
   */
  opacity?: number;
  /**
   * Whether the grain overlay is enabled.
   * @default true
   */
  enabled?: boolean;
  /**
   * Additional CSS class names to apply.
   */
  className?: string;
}

/**
 * GrainOverlay renders a full-screen fixed overlay with a noise texture.
 * The overlay is non-interactive (pointer-events: none) and sits above all content.
 */
export const GrainOverlay: React.FC<GrainOverlayProps> = ({
  opacity,
  enabled = true,
  className,
}) => {
  if (!enabled) {
    return null;
  }

  // Build inline style only if opacity is explicitly provided
  const style: React.CSSProperties | undefined =
    opacity !== undefined
      ? { opacity }
      : undefined;

  return (
    <div
      className={cn("grain-overlay", className)}
      style={style}
      aria-hidden="true"
      data-testid="grain-overlay"
    />
  );
};

GrainOverlay.displayName = "GrainOverlay";

export default GrainOverlay;
