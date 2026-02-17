import React from "react";
import { cn } from "../../../lib/utils";

/**
 * ProgressBar Atom Component
 *
 * A foundational progress bar component with multiple variants for displaying
 * different types of progress information. Uses CSS variables from the design
 * token system for consistent styling.
 *
 * Requirements: 41.1, 41.2, 41.3, 41.4, 41.5, 41.6
 * - Variants: single, single-mini, multi-state, multi-state-mini
 * - Single variants: display one color filling based on percentage
 * - Multi-state variants: display colored sections for different statuses
 * - Uses design system status colors
 */

export type ProgressBarVariant = "single" | "single-mini" | "multi-state" | "multi-state-mini";

export interface StatusCounts {
  completed: number;
  inProgress: number;
  blocked: number;
  notStarted: number;
}

export interface ProgressBarProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Visual style variant */
  variant: ProgressBarVariant;
  /** Percentage for single variants (0-100) */
  percentage?: number;
  /** Custom color for single variants (CSS color value) */
  color?: string;
  /** Status counts for multi-state variants */
  statusCounts?: StatusCounts;
}

/** Height styles - same for all variants */
const heightStyle = "h-2";

/** Width styles for different variants - mini has reduced width for tight spaces */
const widthStyles: Record<ProgressBarVariant, string> = {
  single: "w-full",
  "single-mini": "w-24", // 96px - compact width for tight spaces
  "multi-state": "w-full",
  "multi-state-mini": "w-24", // 96px - compact width for tight spaces
};

/** Base container styles - Enhanced contrast for light themes */
const containerBaseStyles = [
  "rounded-full",
  "overflow-hidden",
  "bg-[var(--progress-bar-empty-bg)]",
  "border",
  "border-[var(--progress-bar-empty-border)]",
].join(" ");

/**
 * Calculate the total count from status counts
 */
const getTotalCount = (counts: StatusCounts): number => {
  return counts.completed + counts.inProgress + counts.blocked + counts.notStarted;
};

/**
 * Calculate percentage width for a status section
 */
const getStatusPercentage = (count: number, total: number): number => {
  if (total === 0) return 0;
  return (count / total) * 100;
};

/**
 * SingleProgressBar - Renders a single-color progress bar
 */
const SingleProgressBar: React.FC<{
  percentage: number;
  color?: string;
  isMini: boolean;
  className?: string;
}> = ({ percentage, color, isMini, className }) => {
  // Clamp percentage between 0 and 100
  const clampedPercentage = Math.max(0, Math.min(100, percentage));
  
  return (
    <div
      className={cn(
        containerBaseStyles,
        heightStyle,
        isMini ? widthStyles["single-mini"] : widthStyles["single"],
        className
      )}
      role="progressbar"
      aria-valuenow={clampedPercentage}
      aria-valuemin={0}
      aria-valuemax={100}
    >
      <div
        className="h-full rounded-full transition-all duration-300 ease-out"
        style={{
          width: `${clampedPercentage}%`,
          backgroundColor: color || "var(--primary)",
        }}
      />
    </div>
  );
};

/**
 * CSS keyframes for progress bar animations:
 * - progressGlow: running glow animation for in-progress sections
 * - blockedPulse: subtle pulsing animation for blocked sections
 */
const progressKeyframes = `
@keyframes progressGlow {
  0% {
    left: -30%;
  }
  100% {
    left: 130%;
  }
}

@keyframes blockedPulse {
  0%, 100% {
    opacity: 0.2;
  }
  50% {
    opacity: 0.6;
  }
}
`;

// Inject keyframes into document head (only once)
if (typeof document !== "undefined") {
  const styleId = "progress-bar-keyframes";
  if (!document.getElementById(styleId)) {
    const style = document.createElement("style");
    style.id = styleId;
    style.textContent = progressKeyframes;
    document.head.appendChild(style);
  }
}

/**
 * MultiStateProgressBar - Renders a progress bar with colored sections for each status
 * Uses gradual color transitions between sections and a running glow on in-progress.
 * 
 * Status colors (Requirement 41.3, 41.6, 46.1, 46.2, 46.3):
 * - completed: green (--success)
 * - in_progress: orange (--warning) with running glow animation
 * - blocked: red (--error)
 * - not_started: empty/transparent
 */
const MultiStateProgressBar: React.FC<{
  statusCounts: StatusCounts;
  isMini: boolean;
  className?: string;
}> = ({ statusCounts, isMini, className }) => {
  const total = getTotalCount(statusCounts);
  
  // Calculate percentages for each status
  const completedPercent = getStatusPercentage(statusCounts.completed, total);
  const inProgressPercent = getStatusPercentage(statusCounts.inProgress, total);
  const blockedPercent = getStatusPercentage(statusCounts.blocked, total);
  
  // Determine border radius for sections based on position
  const getRadius = (isFirst: boolean, isLast: boolean) => {
    const radius = "9999px";
    if (isFirst && isLast) return radius;
    if (isFirst) return `${radius} 0 0 ${radius}`;
    if (isLast) return `0 ${radius} ${radius} 0`;
    return "0";
  };
  
  const hasCompleted = completedPercent > 0;
  const hasInProgress = inProgressPercent > 0;
  const hasBlocked = blockedPercent > 0;
  
  return (
    <div
      className={cn(
        containerBaseStyles,
        heightStyle,
        isMini ? widthStyles["multi-state-mini"] : widthStyles["multi-state"],
        className
      )}
      role="progressbar"
      aria-valuenow={completedPercent}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label={`Progress: ${statusCounts.completed} completed, ${statusCounts.inProgress} in progress, ${statusCounts.blocked} blocked, ${statusCounts.notStarted} not started`}
    >
      <div className="flex h-full w-full">
        {/* Completed section - green */}
        {hasCompleted && (
          <div
            className="h-full transition-all duration-300 ease-out"
            style={{
              width: `${completedPercent}%`,
              backgroundColor: "var(--success)",
              borderRadius: getRadius(true, !hasInProgress && !hasBlocked),
            }}
            data-status="completed"
          />
        )}
        
        {/* In Progress section - orange with running glow */}
        {hasInProgress && (
          <div
            className="h-full transition-all duration-300 ease-out relative overflow-hidden"
            style={{
              width: `${inProgressPercent}%`,
              backgroundColor: "var(--warning)",
              borderRadius: getRadius(!hasCompleted, !hasBlocked),
            }}
            data-status="in_progress"
          >
            {/* Running glow overlay */}
            <div
              className="absolute inset-0 pointer-events-none"
              style={{
                background: "linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.4) 50%, transparent 100%)",
                width: "30%",
                animation: "progressGlow 1.5s ease-in-out infinite",
              }}
            />
          </div>
        )}
        
        {/* Blocked section - red with pulsing highlight overlay */}
        {hasBlocked && (
          <div
            className="h-full transition-all duration-300 ease-out relative overflow-hidden"
            style={{
              width: `${blockedPercent}%`,
              backgroundColor: "var(--error)",
              borderRadius: getRadius(!hasCompleted && !hasInProgress, true),
            }}
            data-status="blocked"
          >
            {/* Pulsing highlight overlay */}
            <div
              className="absolute inset-0 pointer-events-none"
              style={{
                background: "linear-gradient(90deg, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0.25) 50%, rgba(255,255,255,0.1) 100%)",
                animation: "blockedPulse 1.5s ease-in-out infinite",
              }}
            />
          </div>
        )}
      </div>
    </div>
  );
};

/**
 * ProgressBar component with multiple variants
 */
export const ProgressBar = React.forwardRef<HTMLDivElement, ProgressBarProps>(
  (
    {
      variant,
      percentage = 0,
      color,
      statusCounts = { completed: 0, inProgress: 0, blocked: 0, notStarted: 0 },
      className,
      ...props
    },
    ref
  ) => {
    const isSingleVariant = variant === "single" || variant === "single-mini";
    const isMini = variant === "single-mini" || variant === "multi-state-mini";

    return (
      <div ref={ref} {...props}>
        {isSingleVariant ? (
          <SingleProgressBar
            percentage={percentage}
            color={color}
            isMini={isMini}
            className={className}
          />
        ) : (
          <MultiStateProgressBar
            statusCounts={statusCounts}
            isMini={isMini}
            className={className}
          />
        )}
      </div>
    );
  }
);

ProgressBar.displayName = "ProgressBar";

export default ProgressBar;
