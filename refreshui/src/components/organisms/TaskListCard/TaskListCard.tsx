import React, { useState, useMemo } from "react";
import { Card } from "../../atoms/Card";
import { Typography } from "../../atoms/Typography";
import { Icon } from "../../atoms/Icon";
import { ProgressBar, type StatusCounts } from "../../atoms/ProgressBar";
import type { TaskList } from "../../../core/types/entities";
import type { TaskListStats } from "../../../services/types";
import { cn } from "../../../lib/utils";

/**
 * TaskListCard Organism Component
 *
 * A complex card component for displaying task list information with task count
 * and completion percentage. Combines atoms to create a cohesive task list display.
 *
 * Requirements: 5.3, 23.2
 * - Display list name, task count, completion percentage, and status breakdown
 * - Display action buttons for edit and delete on hover
 *
 * Property 16: TaskListCard Content Completeness
 * - For any TaskList object with associated tasks, the TaskListCard SHALL render
 *   the name, task count, and completion percentage.
 *
 * Property 47: Card Action Buttons Visibility
 * - For any TaskListCard on hover, the component SHALL display edit and delete action buttons.
 */

export interface TaskListCardProps {
  /** The task list data to display */
  taskList: TaskList;
  /** Statistics for the task list (task count, completion stats) */
  stats?: TaskListStats;
  /** Click handler for the card */
  onClick?: () => void;
  /** Handler for edit action */
  onEdit?: (taskList: TaskList) => void;
  /** Handler for delete action */
  onDelete?: (taskList: TaskList) => void;
  /** Enable spotlight glow effect following cursor */
  spotlight?: boolean;
  /** Enable parallax tilt effect on hover */
  tilt?: boolean;
  /** Additional CSS classes */
  className?: string;
}

/**
 * Converts TaskListStats to StatusCounts for the ProgressBar component
 */
const convertToStatusCounts = (stats: TaskListStats): StatusCounts => {
  // Calculate not started tasks from total - (completed + in progress + blocked)
  const notStarted = Math.max(
    0,
    stats.taskCount - stats.completedTasks - stats.inProgressTasks - stats.blockedTasks
  );
  
  return {
    completed: stats.completedTasks,
    inProgress: stats.inProgressTasks,
    blocked: stats.blockedTasks,
    notStarted,
  };
};

/**
 * TaskListCard component for displaying task list information
 */
export const TaskListCard: React.FC<TaskListCardProps> = ({
  taskList,
  stats,
  onClick,
  onEdit,
  onDelete,
  spotlight = true,
  tilt = true,
  className,
}) => {
  const [isHovered, setIsHovered] = useState(false);
  const completionPercentage = stats?.completionPercentage ?? 0;
  
  // Convert stats to StatusCounts for the multi-state progress bar
  const statusCounts = useMemo(() => {
    if (!stats) return undefined;
    return convertToStatusCounts(stats);
  }, [stats]);

  const showActionButtons = isHovered && (onEdit || onDelete);

  /**
   * Handle edit button click
   * Stops propagation to prevent card onClick from firing
   */
  const handleEditClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    onEdit?.(taskList);
  };

  /**
   * Handle delete button click
   * Stops propagation to prevent card onClick from firing
   */
  const handleDeleteClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    onDelete?.(taskList);
  };

  return (
    <Card
      variant="glass"
      padding="md"
      spotlight={spotlight}
      tilt={tilt}
      className={cn(
        "cursor-pointer",
        "hover:shadow-lg",
        "transition-shadow",
        "duration-300",
        "relative",
        className
      )}
      onClick={onClick}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      role="article"
      aria-label={`Task List: ${taskList.name}`}
      data-testid="tasklist-card"
    >
      {/* Action Buttons - Visible on hover */}
      {showActionButtons && (
        <div
          className={cn(
            "absolute",
            "top-2",
            "right-2",
            "flex",
            "gap-1",
            "z-10",
            "transition-opacity",
            "duration-200"
          )}
          data-testid="tasklist-card-actions"
        >
          {onEdit && (
            <button
              type="button"
              onClick={handleEditClick}
              className={cn(
                "p-[var(--space-1)]",
                "rounded-[var(--radius-md)]",
                "bg-[var(--bg-surface)]",
                "border",
                "border-[var(--border)]",
                "text-[var(--text-secondary)]",
                "hover:text-[var(--primary)]",
                "hover:border-[var(--primary)]",
                "hover:bg-[var(--bg-surface-hover)]",
                "focus:outline-none",
                "focus:ring-2",
                "focus:ring-[var(--input-focus-ring-color)]",
                "transition-all",
                "duration-[var(--duration-fast)]",
                "ease-[var(--ease-default)]",
                "shadow-[var(--shadow-xs)]"
              )}
              aria-label={`Edit task list: ${taskList.name}`}
              data-testid="tasklist-card-edit-button"
            >
              <Icon name="Pencil" size="sm" />
            </button>
          )}
          {onDelete && (
            <button
              type="button"
              onClick={handleDeleteClick}
              className={cn(
                "p-[var(--space-1)]",
                "rounded-[var(--radius-md)]",
                "bg-[var(--bg-surface)]",
                "border",
                "border-[var(--border)]",
                "text-[var(--text-secondary)]",
                "hover:text-[var(--error)]",
                "hover:border-[var(--error)]",
                "hover:bg-[rgba(var(--error-rgb),0.1)]",
                "focus:outline-none",
                "focus:ring-2",
                "focus:ring-[rgba(var(--error-rgb),0.3)]",
                "transition-all",
                "duration-[var(--duration-fast)]",
                "ease-[var(--ease-default)]",
                "shadow-[var(--shadow-xs)]"
              )}
              aria-label={`Delete task list: ${taskList.name}`}
              data-testid="tasklist-card-delete-button"
            >
              <Icon name="Trash2" size="sm" />
            </button>
          )}
        </div>
      )}

      {/* Task List Name */}
      <Typography
        variant="h5"
        color="primary"
        className="mb-2 line-clamp-2 pr-16"
        data-testid="tasklist-card-name"
      >
        {taskList.name}
      </Typography>

      {/* Description (if present) */}
      {taskList.description && (
        <Typography
          variant="body-sm"
          color="secondary"
          className="mb-4 line-clamp-2"
          data-testid="tasklist-card-description"
        >
          {taskList.description}
        </Typography>
      )}

      {/* Stats Section */}
      {stats && (
        <div className="mt-3 space-y-3" data-testid="tasklist-card-stats">
          {/* Task Count */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-[var(--space-2)]">
              <Icon
                name="ListTodo"
                size="sm"
                className="text-[var(--text-muted)]"
              />
              <Typography variant="body-sm" color="muted">
                Tasks
              </Typography>
            </div>
            <Typography
              variant="body-sm"
              color="primary"
              data-testid="tasklist-card-task-count"
            >
              {stats.taskCount}
            </Typography>
          </div>

          {/* Completion Stats */}
          <div className="pt-2 border-t border-[var(--border)]">
            <div className="flex items-center justify-between mb-2">
              <Typography variant="caption" color="muted">
                Completion
              </Typography>
              <Typography
                variant="caption"
                color="secondary"
                data-testid="tasklist-card-completion-text"
              >
                {stats.completedTasks}/{stats.taskCount} ({completionPercentage}%)
              </Typography>
            </div>

            {/* Multi-state Progress Bar using ProgressBar atom */}
            {statusCounts && (
              <ProgressBar
                variant="multi-state-mini"
                statusCounts={statusCounts}
                data-testid="tasklist-card-progress-bar"
              />
            )}
          </div>

          {/* Status Breakdown */}
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center gap-1">
              <span
                className="w-2 h-2 rounded-full bg-[var(--warning)]"
                aria-hidden="true"
              />
              <Typography variant="caption" color="muted">
                In Progress
              </Typography>
              <Typography
                variant="caption"
                color="secondary"
                data-testid="tasklist-card-in-progress"
              >
                {stats.inProgressTasks}
              </Typography>
            </div>
            <div className="flex items-center gap-1">
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
                data-testid="tasklist-card-blocked"
              >
                {stats.blockedTasks}
              </Typography>
            </div>
            <div className="flex items-center gap-1">
              <span
                className="w-2 h-2 rounded-full bg-[var(--info)]"
                aria-hidden="true"
              />
              <Typography variant="caption" color="muted">
                Ready
              </Typography>
              <Typography
                variant="caption"
                color="secondary"
                data-testid="tasklist-card-ready"
              >
                {stats.readyTasks}
              </Typography>
            </div>
          </div>
        </div>
      )}

      {/* Empty state when no stats */}
      {!stats && (
        <div
          className="mt-3 py-2 text-center"
          data-testid="tasklist-card-no-stats"
        >
          <Typography variant="caption" color="muted">
            No task data available
          </Typography>
        </div>
      )}
    </Card>
  );
};

TaskListCard.displayName = "TaskListCard";

export default TaskListCard;
