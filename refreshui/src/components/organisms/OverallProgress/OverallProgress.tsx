import React from "react";
import { cn } from "../../../lib/utils";
import { Card } from "../../atoms/Card";
import { Typography } from "../../atoms/Typography";
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
 * Uses design system status colors (CSS variables):
 * - Completed: --success (green)
 * - In Progress: --warning (orange)
 * - Blocked: --error (red)
 * - Not Started: transparent (background shows through)
 */

export interface StatusCounts {
  completed: number;
  inProgress: number;
  blocked: number;
  notStarted: number;
}

export interface OverallProgressProps {
  /** Status counts for all tasks */
  statusCounts: StatusCounts;
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
 * OverallProgress component
 */
export const OverallProgress: React.FC<OverallProgressProps> = ({
  statusCounts,
  className,
}) => {
  const total = getTotalCount(statusCounts);

  return (
    <Card
      variant="glass"
      padding="md"
      className={cn("w-full", className)}
      data-testid="overall-progress"
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
