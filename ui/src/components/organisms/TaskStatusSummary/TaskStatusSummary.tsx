import React, { useMemo } from "react";
import { cn } from "../../../lib/utils";
import { Card } from "../../atoms/Card";
import { Typography } from "../../atoms/Typography";
import { ProgressBar, type StatusCounts } from "../../atoms/ProgressBar";

/**
 * TaskStatusSummary Organism Component
 *
 * A comprehensive progress display that shows a multi-state progress bar with
 * counts for each status. Provides detailed status breakdown for task collections.
 *
 * Requirements: 43.1, 43.4, 43.5
 * - Display multi-state progress bar with counts for each status
 * - Recalculate all statistics when task data updates
 * - Apply glassmorphism styling consistent with other organisms
 *
 * Property 78: Task Status Summary Counts
 * - For any TaskStatusSummary organism, the displayed counts for each status
 *   SHALL match the actual task counts in the input data.
 */

export interface TaskStatusSummaryProps {
  /** Status counts for the progress bar */
  statusCounts: StatusCounts;
  /** Whether to show individual status labels */
  showLabels?: boolean;
  /** Visual variant - default or compact */
  variant?: "default" | "compact";
  /** Additional CSS classes */
  className?: string;
}

/**
 * Status configuration for display
 */
const statusConfig = [
  { key: "completed" as const, label: "Completed", color: "var(--success)" },
  { key: "inProgress" as const, label: "In Progress", color: "var(--info)" },
  { key: "blocked" as const, label: "Blocked", color: "var(--error)" },
  { key: "notStarted" as const, label: "Not Started", color: "var(--text-muted)" },
];

/**
 * TaskStatusSummary component
 */
export const TaskStatusSummary: React.FC<TaskStatusSummaryProps> = ({
  statusCounts,
  showLabels = true,
  variant = "default",
  className,
}) => {
  const isCompact = variant === "compact";

  // Calculate total for display
  const total = useMemo(() => {
    return (
      statusCounts.completed +
      statusCounts.inProgress +
      statusCounts.blocked +
      statusCounts.notStarted
    );
  }, [statusCounts]);

  return (
    <Card
      variant="glass"
      padding={isCompact ? "sm" : "md"}
      className={cn("w-full", className)}
      data-testid="task-status-summary"
    >
      {/* Header with total */}
      <div className="flex items-center justify-between mb-[var(--space-3)]">
        <Typography
          variant={isCompact ? "body-sm" : "h6"}
          color="primary"
          data-testid="task-status-summary-title"
        >
          Task Status
        </Typography>
        <Typography
          variant={isCompact ? "caption" : "body-sm"}
          color="muted"
          data-testid="task-status-summary-total"
        >
          {total} total
        </Typography>
      </div>

      {/* Multi-state Progress Bar */}
      <ProgressBar
        variant={isCompact ? "multi-state-mini" : "multi-state"}
        statusCounts={statusCounts}
        className="mb-[var(--space-3)]"
        data-testid="task-status-summary-progress-bar"
      />

      {/* Status Breakdown */}
      {showLabels && (
        <div
          className={cn(
            "grid",
            isCompact ? "grid-cols-4 gap-[var(--space-2)]" : "grid-cols-2 gap-[var(--space-3)]"
          )}
          data-testid="task-status-summary-breakdown"
        >
          {statusConfig.map(({ key, label, color }) => (
            <div
              key={key}
              className={cn(
                "flex items-center",
                isCompact ? "gap-[var(--space-1)]" : "gap-[var(--space-2)]"
              )}
              data-testid={`task-status-summary-${key}`}
            >
              <span
                className={cn(
                  "rounded-full flex-shrink-0",
                  isCompact ? "w-2 h-2" : "w-3 h-3"
                )}
                style={{ backgroundColor: color }}
                aria-hidden="true"
              />
              <div className="flex items-center gap-[var(--space-1)] min-w-0">
                <Typography
                  variant="caption"
                  color="muted"
                  className={cn(isCompact && "truncate")}
                >
                  {isCompact ? label.split(" ")[0] : label}
                </Typography>
                <Typography
                  variant="caption"
                  color="secondary"
                  className="font-medium"
                  data-testid={`task-status-summary-${key}-count`}
                >
                  {statusCounts[key]}
                </Typography>
              </div>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
};

TaskStatusSummary.displayName = "TaskStatusSummary";

export default TaskStatusSummary;
