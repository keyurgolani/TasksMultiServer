import React from "react";
import { cn } from "../../../lib/utils";
import { Card } from "../../atoms/Card";
import { Typography } from "../../atoms/Typography";
import { ProgressBar } from "../../atoms/ProgressBar";
import { StatusIndicator, type StatusType } from "../../molecules/StatusIndicator";

/**
 * OverallProgress Organism Component
 *
 * A comprehensive progress overview component that displays:
 * - Sectioned circular progress bar showing task states
 * - Completion percentage in the center
 * - "Overall Progress" title with completion count
 * - Status breakdown counts on the right edge
 *
 * Supports multiple variants:
 * - "default": Full card with circular progress and detailed breakdown
 * - "compact": Smaller card suitable for embedding in other cards
 * - "mini": Minimal inline display with just progress bar and counts
 *
 * Uses design system status colors (CSS variables):
 * - Completed: --success (green)
 * - In Progress: --warning (orange)
 * - Blocked: --error (red)
 * - Not Started: transparent (background shows through)
 *
 * Requirements: 15.1, 15.2, 15.3, 15.4
 * - Cards should use OverallProgress organism for progress display
 * - Provides consistent styling across all cards
 * - Proper spacing between progress bar and statistics
 * - Responsive layout that adapts to card width
 */

export type OverallProgressVariant = "default" | "compact" | "mini" | "exit-criteria";

export interface StatusCounts {
  completed: number;
  inProgress: number;
  blocked: number;
  notStarted: number;
}

export interface ExitCriteriaProgress {
  completed: number;
  total: number;
}

export interface OverallProgressProps {
  /** Status counts for all tasks (used with default, compact, mini variants) */
  statusCounts?: StatusCounts;
  /** Exit criteria progress (used with exit-criteria variant) */
  exitCriteriaProgress?: ExitCriteriaProgress;
  /** Visual variant - default (full card), compact (smaller card), mini (inline), or exit-criteria (for task cards) */
  variant?: OverallProgressVariant;
  /** Label for exit criteria variant (defaults to "Exit Criteria") */
  exitCriteriaLabel?: string;
  /** Additional CSS classes */
  className?: string;
}

/**
 * Calculate total tasks from status counts
 */
const getTotalCount = (counts: StatusCounts): number => {
  return counts.completed + counts.inProgress + counts.blocked + counts.notStarted;
};

/**
 * Calculate completion percentage
 */
const getCompletionPercentage = (counts: StatusCounts): number => {
  const total = getTotalCount(counts);
  if (total === 0) return 0;
  return Math.round((counts.completed / total) * 100);
};

/**
 * CircularProgressSectioned - Circular progress with colored sections for each status
 * Matches the styling of the linear multi-state ProgressBar
 */
const CircularProgressSectioned: React.FC<{
  statusCounts: StatusCounts;
  size?: number;
}> = ({ statusCounts, size = 72 }) => {
  const total = getTotalCount(statusCounts);
  const percentage = getCompletionPercentage(statusCounts);

  const strokeWidth = 7;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const center = size / 2;

  // Calculate percentages for each status
  const completedPercent = total > 0 ? (statusCounts.completed / total) * 100 : 0;
  const inProgressPercent = total > 0 ? (statusCounts.inProgress / total) * 100 : 0;
  const blockedPercent = total > 0 ? (statusCounts.blocked / total) * 100 : 0;

  // Calculate dash lengths
  const completedDash = (completedPercent / 100) * circumference;
  const inProgressDash = (inProgressPercent / 100) * circumference;
  const blockedDash = (blockedPercent / 100) * circumference;

  // Cumulative offsets (each segment starts where previous ended)
  const completedOffset = 0;
  const inProgressOffset = -completedDash;
  const blockedOffset = -(completedDash + inProgressDash);

  return (
    <div className="relative flex-shrink-0" style={{ width: size, height: size }}>
      <svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        className="transform -rotate-90"
      >
        {/* Background circle */}
        <circle
          cx={center}
          cy={center}
          r={radius}
          fill="none"
          stroke="var(--bg-surface)"
          strokeWidth={strokeWidth}
          className="opacity-50"
        />

        {/* Completed segment - green */}
        {completedPercent > 0 && (
          <circle
            cx={center}
            cy={center}
            r={radius}
            fill="none"
            stroke="var(--success)"
            strokeWidth={strokeWidth}
            strokeDasharray={`${completedDash} ${circumference}`}
            strokeDashoffset={completedOffset}
            strokeLinecap="round"
            className="transition-all duration-300"
          />
        )}

        {/* In Progress segment - orange */}
        {inProgressPercent > 0 && (
          <circle
            cx={center}
            cy={center}
            r={radius}
            fill="none"
            stroke="var(--warning)"
            strokeWidth={strokeWidth}
            strokeDasharray={`${inProgressDash} ${circumference}`}
            strokeDashoffset={inProgressOffset}
            strokeLinecap="round"
            className="transition-all duration-300"
          />
        )}

        {/* Blocked segment - red */}
        {blockedPercent > 0 && (
          <circle
            cx={center}
            cy={center}
            r={radius}
            fill="none"
            stroke="var(--error)"
            strokeWidth={strokeWidth}
            strokeDasharray={`${blockedDash} ${circumference}`}
            strokeDashoffset={blockedOffset}
            strokeLinecap="round"
            className="transition-all duration-300"
          />
        )}
      </svg>

      {/* Center percentage text */}
      <div className="absolute inset-0 flex items-center justify-center">
        <Typography variant="body-sm" color="primary" className="font-semibold">
          {percentage}%
        </Typography>
      </div>
    </div>
  );
};

/**
 * StatusCountItem - Individual status count display (vertical layout)
 * Uses StatusIndicator molecule for consistent pulsing behavior
 */
const StatusCountItem: React.FC<{
  label: string;
  count: number;
  status?: StatusType;
  showIndicator?: boolean;
}> = ({ label, count, status, showIndicator = true }) => (
  <div className="flex flex-col items-center gap-[var(--space-1)]">
    <div className="flex items-center gap-[var(--space-1)]">
      {showIndicator && status && (
        <StatusIndicator status={status} pulse={status === "in_progress" || status === "blocked"} size="sm" />
      )}
      <Typography variant="caption" color="muted">
        {label}
      </Typography>
    </div>
    <Typography variant="h5" color="primary" className="font-semibold">
      {count}
    </Typography>
  </div>
);

/**
 * MiniStatusItem - Compact status count for mini variant
 */
const MiniStatusItem: React.FC<{
  count: number;
  status: StatusType;
}> = ({ count, status }) => (
  <div className="flex items-center gap-[var(--space-1)]">
    <StatusIndicator status={status} size="sm" pulse={status === "in_progress" || status === "blocked"} />
    <Typography variant="caption" color="muted">
      {count}
    </Typography>
  </div>
);

/**
 * OverallProgress component
 * 
 * Supports four variants:
 * - "default": Full card with circular progress and detailed breakdown
 * - "compact": Smaller display suitable for embedding in cards
 * - "mini": Minimal inline display with just progress bar and counts
 * - "exit-criteria": Simple progress bar for exit criteria in TaskCards
 */
export const OverallProgress: React.FC<OverallProgressProps> = ({
  statusCounts,
  exitCriteriaProgress,
  variant = "default",
  exitCriteriaLabel = "Exit Criteria",
  className,
}) => {
  // For exit-criteria variant, use exitCriteriaProgress
  // For other variants, use statusCounts
  const total = variant === "exit-criteria" 
    ? (exitCriteriaProgress?.total ?? 0)
    : (statusCounts ? getTotalCount(statusCounts) : 0);
  const completed = variant === "exit-criteria"
    ? (exitCriteriaProgress?.completed ?? 0)
    : (statusCounts?.completed ?? 0);
  const percentage = total > 0 ? Math.round((completed / total) * 100) : 0;

  // Exit-criteria variant: simple progress bar for TaskCard exit criteria
  // Requirements: 15.3, 15.4
  if (variant === "exit-criteria" && exitCriteriaProgress) {
    return (
      <div
        className={cn("w-full", className)}
        data-testid="overall-progress"
        data-variant="exit-criteria"
      >
        {/* Label and count row */}
        <div className="flex items-center justify-between mb-1">
          <Typography variant="caption" color="muted">
            {exitCriteriaLabel}
          </Typography>
          <Typography variant="caption" color="secondary">
            {exitCriteriaProgress.completed}/{exitCriteriaProgress.total}
          </Typography>
        </div>
        
        {/* Single-color progress bar */}
        <div className="h-1.5 bg-[var(--progress-bar-bg)] rounded-full overflow-hidden">
          <div
            className="h-full bg-[var(--primary)] rounded-full transition-all duration-300"
            style={{ width: `${percentage}%` }}
            role="progressbar"
            aria-valuenow={percentage}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label={`${exitCriteriaLabel} progress: ${percentage}%`}
          />
        </div>
      </div>
    );
  }

  // Mini variant: inline progress bar with compact status counts
  // Suitable for embedding within cards
  if (variant === "mini" && statusCounts) {
    return (
      <div
        className={cn("w-full", className)}
        data-testid="overall-progress"
        data-variant="mini"
      >
        {/* Completion text row */}
        <div className="flex items-center justify-between mb-1">
          <Typography variant="caption" color="muted">
            Completion
          </Typography>
          <Typography variant="caption" color="secondary">
            {statusCounts.completed}/{total} ({percentage}%)
          </Typography>
        </div>
        
        {/* Multi-state progress bar - full width */}
        <ProgressBar
          variant="multi-state"
          statusCounts={statusCounts}
          data-testid="overall-progress-bar"
        />
        
        {/* Compact status breakdown */}
        <div className="flex items-center justify-between mt-2 text-xs">
          <MiniStatusItem count={statusCounts.inProgress} status="in_progress" />
          <MiniStatusItem count={statusCounts.blocked} status="blocked" />
          <MiniStatusItem count={statusCounts.notStarted} status="not_started" />
        </div>
      </div>
    );
  }

  // Compact variant: smaller card-like display
  // Suitable for embedding within cards with more detail than mini
  if (variant === "compact" && statusCounts) {
    return (
      <div
        className={cn("w-full pt-2 border-t border-[var(--border)]", className)}
        data-testid="overall-progress"
        data-variant="compact"
      >
        {/* Completion header */}
        <div className="flex items-center justify-between mb-2">
          <Typography variant="caption" color="muted">
            Completion
          </Typography>
          <Typography variant="caption" color="secondary">
            {statusCounts.completed}/{total} ({percentage}%)
          </Typography>
        </div>
        
        {/* Multi-state progress bar - full width */}
        <ProgressBar
          variant="multi-state"
          statusCounts={statusCounts}
          data-testid="overall-progress-bar"
        />
        
        {/* Status breakdown row */}
        <div className="flex items-center justify-between mt-2 text-xs">
          <div className="flex items-center gap-1">
            <StatusIndicator status="in_progress" size="sm" />
            <Typography variant="caption" color="muted">In Progress</Typography>
            <Typography variant="caption" color="secondary">{statusCounts.inProgress}</Typography>
          </div>
          <div className="flex items-center gap-1">
            <StatusIndicator status="blocked" size="sm" />
            <Typography variant="caption" color="muted">Blocked</Typography>
            <Typography variant="caption" color="secondary">{statusCounts.blocked}</Typography>
          </div>
          <div className="flex items-center gap-1">
            <StatusIndicator status="not_started" size="sm" />
            <Typography variant="caption" color="muted">Ready</Typography>
            <Typography variant="caption" color="secondary">{statusCounts.notStarted}</Typography>
          </div>
        </div>
      </div>
    );
  }

  // Default variant: full card with circular progress
  // Requires statusCounts to be provided
  if (!statusCounts) {
    return null;
  }

  return (
    <Card
      variant="glass"
      padding="md"
      className={cn("w-full", className)}
      data-testid="overall-progress"
      data-variant="default"
    >
      <div className="flex items-center gap-[var(--space-6)]">
        {/* Left: Circular progress with title */}
        <div className="flex items-center gap-[var(--space-4)] flex-shrink-0">
          <CircularProgressSectioned statusCounts={statusCounts} size={72} />
          <div className="flex flex-col gap-[var(--space-1)]">
            <Typography variant="h6" color="primary">
              Overall Progress
            </Typography>
            <Typography variant="body-sm" color="muted">
              {statusCounts.completed}/{total} completed
            </Typography>
          </div>
        </div>

        {/* Divider */}
        <div className="h-12 w-px bg-[var(--border)] flex-shrink-0" />

        {/* Center/Right: Status breakdown in horizontal row */}
        <div className="flex items-center justify-around flex-1 gap-[var(--space-4)]">
          <StatusCountItem label="Total" count={total} showIndicator={false} />
          <StatusCountItem label="Completed" count={statusCounts.completed} status="completed" />
          <StatusCountItem label="In Progress" count={statusCounts.inProgress} status="in_progress" />
          <StatusCountItem label="Blocked" count={statusCounts.blocked} status="blocked" />
          <StatusCountItem label="Not Started" count={statusCounts.notStarted} status="not_started" />
        </div>
      </div>
    </Card>
  );
};

OverallProgress.displayName = "OverallProgress";

export default OverallProgress;
