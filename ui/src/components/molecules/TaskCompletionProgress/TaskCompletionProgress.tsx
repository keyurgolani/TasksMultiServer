import React from "react";
import { cn } from "../../../lib/utils";
import { ProgressBar } from "../../atoms/ProgressBar";
import { Typography } from "../../atoms/Typography";

/**
 * TaskCompletionProgress Molecule Component
 *
 * A progress bar molecule that displays task completion with a "n/m tasks completed" label.
 * Combines the ProgressBar atom with Typography for meaningful progress data display.
 *
 * Requirements: 42.1, 42.4, 42.5
 * - Displays progress bar with "n/m tasks completed" label
 * - Recalculates and updates both bar and label when data changes
 * - Applies consistent typography and spacing from design tokens
 *
 * Property 77: Task Completion Progress Label Accuracy
 * - For any n completed tasks out of m total, the label SHALL display "n/m tasks completed"
 */

export interface TaskCompletionProgressProps {
  /** Number of completed tasks */
  completed: number;
  /** Total number of tasks */
  total: number;
  /** Visual variant - default or mini */
  variant?: "default" | "mini";
  /** Additional CSS classes */
  className?: string;
}

/**
 * Calculate completion percentage
 */
const calculatePercentage = (completed: number, total: number): number => {
  if (total === 0) return 0;
  return Math.round((completed / total) * 100);
};

/**
 * TaskCompletionProgress component
 */
export const TaskCompletionProgress: React.FC<TaskCompletionProgressProps> = ({
  completed,
  total,
  variant = "default",
  className,
}) => {
  const percentage = calculatePercentage(completed, total);
  const isMini = variant === "mini";

  // Mini variant: horizontal layout with minimal text
  if (isMini) {
    return (
      <div
        className={cn(
          "flex items-center gap-[var(--space-2)]",
          className
        )}
        data-testid="task-completion-progress"
      >
        <ProgressBar
          variant="single-mini"
          percentage={percentage}
          color="var(--success)"
        />
        <Typography
          variant="caption"
          color="muted"
          className="whitespace-nowrap"
          data-testid="task-completion-label"
        >
          {completed}/{total}
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
      data-testid="task-completion-progress"
    >
      {/* Label */}
      <div className="flex items-center justify-between">
        <Typography
          variant="body-sm"
          color="secondary"
          data-testid="task-completion-label"
        >
          {completed}/{total} tasks completed
        </Typography>
        <Typography
          variant="body-sm"
          color="muted"
        >
          {percentage}%
        </Typography>
      </div>

      {/* Progress Bar */}
      <ProgressBar
        variant="single"
        percentage={percentage}
        color="var(--success)"
      />
    </div>
  );
};

TaskCompletionProgress.displayName = "TaskCompletionProgress";

export default TaskCompletionProgress;
