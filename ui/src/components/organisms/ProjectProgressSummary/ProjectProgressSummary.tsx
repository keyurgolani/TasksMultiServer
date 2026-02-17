import React, { useMemo } from "react";
import { cn } from "../../../lib/utils";
import { Card } from "../../atoms/Card";
import { Typography } from "../../atoms/Typography";
import { Icon } from "../../atoms/Icon";
import { ProgressBar, type StatusCounts } from "../../atoms/ProgressBar";
import type { Project, TaskList, Task } from "../../../core/types/entities";

/**
 * ProjectProgressSummary Organism Component
 *
 * A comprehensive progress display for projects showing overall completion
 * percentage, task counts, and a multi-state progress bar.
 *
 * Requirements: 43.2, 43.4, 43.5
 * - Display overall completion percentage, task counts, and multi-state progress bar
 * - Recalculate all statistics when task data updates
 * - Apply glassmorphism styling consistent with other organisms
 */

export interface ProjectProgressSummaryProps {
  /** The project to display progress for */
  project: Project;
  /** Task lists belonging to this project */
  taskLists: TaskList[];
  /** Tasks belonging to this project's task lists */
  tasks: Task[];
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
 * ProjectProgressSummary component
 */
export const ProjectProgressSummary: React.FC<ProjectProgressSummaryProps> = ({
  project,
  taskLists,
  tasks,
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

    return {
      statusCounts,
      totalTasks,
      completionPercentage,
      taskListCount: taskLists.length,
    };
  }, [tasks, taskLists]);

  return (
    <Card
      variant="glass"
      padding="md"
      className={cn("w-full", className)}
      data-testid="project-progress-summary"
    >
      {/* Header */}
      <div className="flex items-center justify-between mb-[var(--space-4)]">
        <div className="flex items-center gap-[var(--space-2)]">
          <Icon name="FolderKanban" size="md" className="text-[var(--primary)]" />
          <Typography
            variant="h6"
            color="primary"
            className="line-clamp-1"
            data-testid="project-progress-summary-name"
          >
            {project.name}
          </Typography>
        </div>
        <Typography
          variant="h5"
          color="primary"
          data-testid="project-progress-summary-percentage"
        >
          {stats.completionPercentage}%
        </Typography>
      </div>

      {/* Multi-state Progress Bar */}
      <ProgressBar
        variant="multi-state"
        statusCounts={stats.statusCounts}
        className="mb-[var(--space-4)]"
        data-testid="project-progress-summary-progress-bar"
      />

      {/* Stats Grid */}
      <div className="grid grid-cols-2 gap-[var(--space-4)]">
        {/* Task Lists Count */}
        <div
          className="flex items-center gap-[var(--space-2)]"
          data-testid="project-progress-summary-tasklists"
        >
          <Icon name="ClipboardList" size="sm" className="text-[var(--text-muted)]" />
          <div>
            <Typography variant="caption" color="muted">
              Task Lists
            </Typography>
            <Typography variant="body-sm" color="secondary" className="font-medium">
              {stats.taskListCount}
            </Typography>
          </div>
        </div>

        {/* Total Tasks */}
        <div
          className="flex items-center gap-[var(--space-2)]"
          data-testid="project-progress-summary-total"
        >
          <Icon name="ListTodo" size="sm" className="text-[var(--text-muted)]" />
          <div>
            <Typography variant="caption" color="muted">
              Total Tasks
            </Typography>
            <Typography variant="body-sm" color="secondary" className="font-medium">
              {stats.totalTasks}
            </Typography>
          </div>
        </div>

        {/* Completed Tasks */}
        <div
          className="flex items-center gap-[var(--space-2)]"
          data-testid="project-progress-summary-completed"
        >
          <Icon name="CheckCircle" size="sm" className="text-[var(--success)]" />
          <div>
            <Typography variant="caption" color="muted">
              Completed
            </Typography>
            <Typography variant="body-sm" color="secondary" className="font-medium">
              {stats.statusCounts.completed}
            </Typography>
          </div>
        </div>

        {/* In Progress Tasks */}
        <div
          className="flex items-center gap-[var(--space-2)]"
          data-testid="project-progress-summary-in-progress"
        >
          <Icon name="Clock" size="sm" className="text-[var(--info)]" />
          <div>
            <Typography variant="caption" color="muted">
              In Progress
            </Typography>
            <Typography variant="body-sm" color="secondary" className="font-medium">
              {stats.statusCounts.inProgress}
            </Typography>
          </div>
        </div>
      </div>

      {/* Status Breakdown Row */}
      <div
        className="mt-[var(--space-4)] pt-[var(--space-3)] border-t border-[var(--border)] flex items-center justify-between"
        data-testid="project-progress-summary-breakdown"
      >
        <div className="flex items-center gap-[var(--space-1)]">
          <span
            className="w-2 h-2 rounded-full bg-[var(--error)]"
            aria-hidden="true"
          />
          <Typography variant="caption" color="muted">
            Blocked
          </Typography>
          <Typography
            variant="caption"
            color="secondary"
            className="font-medium"
            data-testid="project-progress-summary-blocked-count"
          >
            {stats.statusCounts.blocked}
          </Typography>
        </div>
        <div className="flex items-center gap-[var(--space-1)]">
          <span
            className="w-2 h-2 rounded-full bg-[var(--text-muted)]"
            aria-hidden="true"
          />
          <Typography variant="caption" color="muted">
            Not Started
          </Typography>
          <Typography
            variant="caption"
            color="secondary"
            className="font-medium"
            data-testid="project-progress-summary-not-started-count"
          >
            {stats.statusCounts.notStarted}
          </Typography>
        </div>
      </div>
    </Card>
  );
};

ProjectProgressSummary.displayName = "ProjectProgressSummary";

export default ProjectProgressSummary;
