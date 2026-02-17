import React from "react";
import { cn } from "../../../lib/utils";

/**
 * StatusIndicator Molecule Component
 *
 * A status indicator component that displays a colored dot with optional
 * pulse animation for active states. The pulse animation is applied when
 * the status is 'in_progress' or 'blocked' and pulse is enabled.
 *
 * The pulse animation intensity is controlled by the --pulsing-strength CSS variable:
 * - At 0: no pulse effect (animation disabled)
 * - At 100: maximum pulse scale
 *
 * Requirements: 4.5, 40.1, 40.2, 40.3
 * - Displays colored dot
 * - Optional pulse animation for active states
 * - Supports multiple sizes
 * - Pulse animation scale factor controlled by pulsing-strength CSS variable
 * - When pulsing strength is 0, pulse animation is disabled
 * - When pulsing strength is at maximum, most pronounced pulse scale is applied
 */

export type StatusType = "not_started" | "in_progress" | "completed" | "blocked";

export interface StatusIndicatorProps {
  /** The current status to display */
  status: StatusType;
  /** Whether to show pulse animation for active states (in_progress, blocked) */
  pulse?: boolean;
  /** Size variant of the indicator */
  size?: "sm" | "md" | "lg";
  /** Additional CSS classes */
  className?: string;
}

const sizeStyles = {
  sm: "w-2 h-2",
  md: "w-3 h-3",
  lg: "w-4 h-4",
};

const statusColors: Record<StatusType, { bg: string; shadow: string; border?: string }> = {
  not_started: {
    bg: "bg-[var(--status-not-started-bg,#9ca3af)]",
    shadow: "shadow-[0_0_4px_rgba(156,163,175,0.5)]",
    border: "ring-1 ring-[var(--status-indicator-border,rgba(0,0,0,0.15))]",
  },
  in_progress: {
    bg: "bg-[var(--warning)]",
    shadow: "shadow-[0_0_8px_var(--warning)]",
    border: "ring-1 ring-[var(--status-indicator-border,transparent)]",
  },
  completed: {
    bg: "bg-[var(--success)]",
    shadow: "shadow-[0_0_8px_var(--success)]",
    border: "ring-1 ring-[var(--status-indicator-border,transparent)]",
  },
  blocked: {
    bg: "bg-[var(--error)]",
    shadow: "shadow-[0_0_8px_var(--error)]",
    border: "ring-1 ring-[var(--status-indicator-border,transparent)]",
  },
};

/**
 * Determines if the status is an "active" state that should pulse
 */
const isActiveStatus = (status: StatusType): boolean => {
  return status === "in_progress" || status === "blocked";
};

/**
 * StatusIndicator component with pulse animation
 * 
 * The pulse animation uses the --pulsing-strength CSS variable to control
 * the scale factor of the animation. When pulsing-strength is 0, the animation
 * is effectively disabled (no visual change). When at maximum (100), the pulse
 * ring scales to 2x its original size.
 */
export const StatusIndicator: React.FC<StatusIndicatorProps> = ({
  status,
  pulse = false,
  size = "md",
  className,
}) => {
  const shouldPulse = pulse && isActiveStatus(status);
  const colors = statusColors[status];

  return (
    <span
      className={cn(
        // Base styles
        "relative inline-block rounded-full flex-shrink-0",
        // Size
        sizeStyles[size],
        // Color
        colors.bg,
        colors.shadow,
        // Border for contrast in light themes
        colors.border,
        // Additional classes
        className
      )}
      role="status"
      aria-label={`Status: ${status.replace("_", " ")}`}
      data-status={status}
      data-pulse={shouldPulse}
    >
      {/* Pulse animation ring - uses pulsing-strength CSS variable for scale factor */}
      {shouldPulse && (
        <span
          className={cn(
            "absolute inset-0 rounded-full animate-ping",
            colors.bg,
            "opacity-75"
          )}
          style={{
            animationDuration: `calc(2s * var(--animation-speed, 1))`,
            // Use CSS custom property for pulsing strength scale
            // The animation will scale based on --pulsing-strength (0-100)
            // At 0: scale stays at 1 (no visible pulse)
            // At 100: scale goes to 2 (maximum pulse)
            "--tw-scale-x": `calc(1 + (var(--pulsing-strength, 50) / 100))`,
            "--tw-scale-y": `calc(1 + (var(--pulsing-strength, 50) / 100))`,
          } as React.CSSProperties}
          aria-hidden="true"
        />
      )}
    </span>
  );
};

StatusIndicator.displayName = "StatusIndicator";

export default StatusIndicator;
