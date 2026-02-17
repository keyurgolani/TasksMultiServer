import React from "react";
import { cn } from "../../../lib/utils";
import { ProgressBar } from "../../atoms/ProgressBar";
import { Typography } from "../../atoms/Typography";

/**
 * ReadyTasksProgress Molecule Component
 *
 * A progress bar molecule that displays the proportion of ready tasks with an "X% ready" label.
 * Ready tasks are those with no pending dependencies or all dependencies completed.
 * Combines the ProgressBar atom with Typography for meaningful progress data display.
 *
 * Requirements: 42.3, 42.4, 42.5
 * - Displays progress bar with "X% ready" label showing proportion of ready tasks
 * - Recalculates and updates both bar and label when data changes
 * - Applies consistent typography and spacing from design tokens
 */

export interface ReadyTasksProgressProps {
  /** Number of ready tasks */
  readyCount: number;
  /** Total number of tasks */
  totalCount: number;
  /** Visual variant - default or mini */
  variant?: "default" | "mini";
  /** Additional CSS classes */
  className?: string;
}

/**
 * Calculate ready percentage
 */
const calculatePercentage = (ready: number, total: number): number => {
  if (total === 0) return 0;
  return Math.round((ready / total) * 100);
};

/**
 * ReadyTasksProgress component
 */
export const ReadyTasksProgress: React.FC<ReadyTasksProgressProps> = ({
  readyCount,
  totalCount,
  variant = "default",
  className,
}) => {
  const percentage = calculatePercentage(readyCount, totalCount);
  const isMini = variant === "mini";

  // Mini variant: horizontal layout with minimal text
  if (isMini) {
    return (
      <div
        className={cn(
          "flex items-center gap-[var(--space-2)]",
          className
        )}
        data-testid="ready-tasks-progress"
      >
        <ProgressBar
          variant="single-mini"
          percentage={percentage}
          color="var(--info)"
        />
        <Typography
          variant="caption"
          color="muted"
          className="whitespace-nowrap"
          data-testid="ready-tasks-label"
        >
          {readyCount}/{totalCount}
        </Typography>
      </div>
    );
  }

  // Default variant: vertical layout with full labels
  return (
    <div
      className={cn(
        "flex flex-col gap-[var(--space-2)]",
        className
      )}
      data-testid="ready-tasks-progress"
    >
      {/* Label */}
      <div className="flex items-center justify-between">
        <Typography
          variant="body-sm"
          color="secondary"
          data-testid="ready-tasks-label"
        >
          {percentage}% ready
        </Typography>
        <Typography
          variant="body-sm"
          color="muted"
        >
          {readyCount}/{totalCount}
        </Typography>
      </div>

      {/* Progress Bar */}
      <ProgressBar
        variant="single"
        percentage={percentage}
        color="var(--info)"
      />
    </div>
  );
};

ReadyTasksProgress.displayName = "ReadyTasksProgress";

export default ReadyTasksProgress;
