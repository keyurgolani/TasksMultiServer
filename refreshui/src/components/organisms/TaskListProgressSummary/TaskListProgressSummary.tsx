import React, { useMemo } from "react";
import { cn } from "../../../lib/utils";
import { Card } from "../../atoms/Card";
import { Typography } from "../../atoms/Typography";
import { Icon } from "../../atoms/Icon";
import { ProgressBar, type StatusCounts } from "../../atoms/ProgressBar";
import type { TaskList, Task } from "../../../core/types/entities";

/**
 * TaskListProgressSummary Organism Component
 *
 * A comprehensive progress display for task lists showing completion percentage,
 * ready task count, and status breakdown.
 *
 * Requirements: 43.3, 43.4, 43.5
 * - Display completion percentage, ready task count, and status breakdown
 * - Recalculate all statistics when task data updates
 * - Apply glassmorphism styling consistent with other organisms
 */

export interface TaskListProgressSummaryProps {
  /** The task list to display progress for */
  taskList: TaskList;
  /** Tasks belonging to this task list */
  tasks: Task[];
  /** Number of ready tasks (tasks with no pending dependencies) */
  readyTaskCount?: number;
  /** Additional CSS classes */
  className?: string;
}

/**
 * Calculate status counts from tasks
 */
const calculateStatusCounts = (tasks: Task[]): StatusCounts => {
  return tasks.reduce(
    (acc, task) => {
      switch (task.status) {
        case "COMPLETED":
          acc.completed++;
          break;
        case "IN_PROGRESS":
          acc.inProgress++;
          break;
        case "BLOCKED":
          acc.blocked++;
          break;
        case "NOT_STARTED":
        default:
          acc.notStarted++;
          break;
      }
      return acc;
    },
    { completed: 0, inProgress: 0, blocked: 0, notStarted: 0 }
  );
};

/**
 * Calculate completion percentage
 */
const calculateCompletionPercentage = (completed: number, total: number): number => {
  if (total === 0) return 0;
  return Math.round((completed / total) * 100);
};

/**
 * Calculate ready percentage
 */
const calculateReadyPercentage = (ready: number, total: number): number => {
  if (total === 0) return 0;
  return Math.round((ready / total) * 100);
};

/**
 * TaskListProgressSummary component
 */
export const TaskListProgressSummary: React.FC<TaskListProgressSummaryProps> = ({
  taskList,
  tasks,
  readyTaskCount,
  className,
}) => {
  // Calculate statistics from tasks
  const stats = useMemo(() => {
    const statusCounts = calculateStatusCounts(tasks);
    const totalTasks = tasks.length;
    const completionPercentage = calculateCompletionPercentage(
      statusCounts.completed,
      totalTasks
    );
    // If readyTaskCount is not provided, estimate based on NOT_STARTED + IN_PROGRESS
    const ready = readyTaskCount ?? (statusCounts.notStarted + statusCounts.inProgress);
    const readyPercentage = calculateReadyPercentage(ready, totalTasks);

    return {
      statusCounts,
      totalTasks,
      completionPercentage,
      readyTasks: ready,
      readyPercentage,
    };
  }, [tasks, readyTaskCount]);

  return (
    <Card
      variant="glass"
      padding="md"
      className={cn("w-full", className)}
      data-testid="tasklist-progress-summary"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-[var(--space-4)]">
        <div className="flex items-center gap-[var(--space-2)]">
          <Icon name="ListTodo" size="md" className="text-[var(--primary)]" />
          <Typography
            variant="h6"
            color="primary"
            className="line-clamp-1"
            data-testid="tasklist-progress-summary-name"
          >
            {taskList.name}
          </Typography>
        </div>
        <Typography
          variant="h5"
          color="primary"
          data-testid="tasklist-progress-summary-percentage"
        >
          {stats.completionPercentage}%
        </Typography>
      </div>

      {/* Multi-state Progress Bar */}
      <ProgressBar
        variant="multi-state"
        statusCounts={stats.statusCounts}
        className="mb-[var(--space-4)]"
        data-testid="tasklist-progress-summary-progress-bar"
      />

      {/* Stats Row */}
      <div className="grid grid-cols-3 gap-[var(--space-3)] mb-[var(--space-4)]">
        {/* Total Tasks */}
        <div
          className="text-center"
          data-testid="tasklist-progress-summary-total"
        >
          <Typography variant="h5" color="secondary" className="font-semibold">
            {stats.totalTasks}
          </Typography>
          <Typography variant="caption" color="muted">
            Total
          </Typography>
        </div>

        {/* Completed Tasks */}
        <div
          className="text-center"
          data-testid="tasklist-progress-summary-completed"
        >
          <Typography variant="h5" color="secondary" className="font-semibold text-[var(--success)]">
            {stats.statusCounts.completed}
          </Typography>
          <Typography variant="caption" color="muted">
            Completed
          </Typography>
        </div>

        {/* Ready Tasks */}
        <div
          className="text-center"
          data-testid="tasklist-progress-summary-ready"
        >
          <Typography variant="h5" color="secondary" className="font-semibold text-[var(--info)]">
            {stats.readyTasks}
          </Typography>
          <Typography variant="caption" color="muted">
            Ready
          </Typography>
        </div>
      </div>

      {/* Status Breakdown */}
      <div
        className="pt-[var(--space-3)] border-t border-[var(--border)] grid grid-cols-4 gap-[var(--space-2)]"
        data-testid="tasklist-progress-summary-breakdown"
      >
        {/* Completed */}
        <div className="flex items-center gap-[var(--space-1)]">
          <span
            className="w-2 h-2 rounded-full bg-[var(--success)]"
            aria-hidden="true"
          />
          <Typography
            variant="caption"
            color="secondary"
            data-testid="tasklist-progress-summary-completed-count"
          >
            {stats.statusCounts.completed}
          </Typography>
        </div>

        {/* In Progress */}
        <div className="flex items-center gap-[var(--space-1)]">
          <span
            className="w-2 h-2 rounded-full bg-[var(--info)]"
            aria-hidden="true"
          />
          <Typography
            variant="caption"
            color="secondary"
            data-testid="tasklist-progress-summary-in-progress-count"
          >
            {stats.statusCounts.inProgress}
          </Typography>
        </div>

        {/* Blocked */}
        <div className="flex items-center gap-[var(--space-1)]">
          <span
            className="w-2 h-2 rounded-full bg-[var(--error)]"
            aria-hidden="true"
          />
          <Typography
            variant="caption"
            color="secondary"
            data-testid="tasklist-progress-summary-blocked-count"
          >
            {stats.statusCounts.blocked}
          </Typography>
        </div>

        {/* Not Started */}
        <div className="flex items-center gap-[var(--space-1)]">
          <span
            className="w-2 h-2 rounded-full bg-[var(--text-muted)]"
            aria-hidden="true"
          />
          <Typography
            variant="caption"
            color="secondary"
            data-testid="tasklist-progress-summary-not-started-count"
          >
            {stats.statusCounts.notStarted}
          </Typography>
        </div>
      </div>

      {/* Ready Tasks Info */}
      <div
        className="mt-[var(--space-3)] flex items-center justify-between"
        data-testid="tasklist-progress-summary-ready-info"
      >
        <div className="flex items-center gap-[var(--space-2)]">
          <Icon name="Zap" size="sm" className="text-[var(--info)]" />
          <Typography variant="body-sm" color="muted">
            Ready to work
          </Typography>
        </div>
        <Typography variant="body-sm" color="secondary" className="font-medium">
          {stats.readyPercentage}% ({stats.readyTasks}/{stats.totalTasks})
        </Typography>
      </div>
    </Card>
  );
};

TaskListProgressSummary.displayName = "TaskListProgressSummary";

export default TaskListProgressSummary;
