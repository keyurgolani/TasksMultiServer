import React, { useState, useMemo, useRef } from "react";
import { Card } from "../../atoms/Card";
import { Typography } from "../../atoms/Typography";
import { Icon } from "../../atoms/Icon";
import { ProgressBar, type StatusCounts } from "../../atoms/ProgressBar";
import { OverallProgress } from "../OverallProgress";
import { useElementSize } from "../../../core/hooks/useElementSize";
import type { TaskList } from "../../../core/types/entities";
import type { TaskListStats } from "../../../services/types";
import { cn } from "../../../lib/utils";

/**
 * TaskListCard Organism Component
 *
 * A complex card component for displaying task list information with task count
 * and completion percentage. Combines atoms to create a cohesive task list display.
 *
 * Requirements: 5.3, 23.2, 1.17
 * - Display list name, task count, completion percentage, and status breakdown
 * - Display action buttons for edit and delete on hover
 * - Support minimal variant showing only title and progress bar with very low height
 *
 * Property 16: TaskListCard Content Completeness
 * - For any TaskList object with associated tasks, the TaskListCard SHALL render
 *   the name, task count, and completion percentage.
 *
 * Property 47: Card Action Buttons Visibility
 * - For any TaskListCard on hover, the component SHALL display edit and delete action buttons.
 */

export type TaskListCardVariant = "default" | "minimal";

export interface TaskListCardProps {
  /** The task list data to display */
  taskList: TaskList;
  /** Statistics for the task list (task count, completion stats) */
  stats?: TaskListStats;
  /** Visual variant - "default" shows full card, "minimal" shows only title and progress bar */
  variant?: TaskListCardVariant;
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
 * Converts TaskListStats to StatusCounts for the OverallProgress organism
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
 * 
 * Requirements: 5.9 - Responsive internal layout
 * - Detects card width and adapts internal elements
 * - Shows compact variants of progress indicators, stats when narrow
 * - Hides or resizes secondary information on narrow cards
 */
export const TaskListCard: React.FC<TaskListCardProps> = ({
  taskList,
  stats,
  variant = "default",
  onClick,
  onEdit,
  onDelete,
  spotlight = true,
  tilt = true,
  className,
}) => {
  const [isHovered, setIsHovered] = useState(false);
  const cardRef = useRef<HTMLDivElement>(null);
  const { isCompact, isReduced } = useElementSize(cardRef);
  
  // Convert stats to StatusCounts for the OverallProgress organism
  const statusCounts = useMemo(() => {
    if (!stats) return undefined;
    return convertToStatusCounts(stats);
  }, [stats]);

  // Minimal variant disables parallax effect and action buttons
  const isMinimal = variant === "minimal";
  const effectiveTilt = isMinimal ? false : tilt;
  const effectiveSpotlight = isMinimal ? false : spotlight;
  const showActionButtons = !isMinimal && isHovered && (onEdit || onDelete);
  
  // Responsive layout flags for default variant
  const showDescription = !isCompact && !isReduced;
  const showDetailedStats = !isCompact;
  const showStatusBreakdown = !isCompact && !isReduced;

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

  // Minimal variant: render compact card with only title and progress bar
  if (isMinimal) {
    return (
      <Card
        variant="glass"
        padding="sm"
        spotlight={false}
        tilt={false}
        className={cn(
          "cursor-pointer",
          "hover:shadow-md",
          "transition-shadow",
          "duration-200",
          "relative",
          "h-[52px]", // Fixed low height for minimal variant (~48-56px)
          "flex",
          "flex-col",
          "justify-center",
          className
        )}
        onClick={onClick}
        role="article"
        aria-label={`Task List: ${taskList.name}`}
        data-testid="tasklist-card"
        data-variant="minimal"
      >
        {/* Task List Name - compact */}
        <Typography
          variant="body-sm"
          color="primary"
          className="truncate font-medium mb-1"
          data-testid="tasklist-card-name"
        >
          {taskList.name}
        </Typography>

        {/* Progress Bar - full width */}
        {statusCounts && (
          <ProgressBar
            variant="multi-state"
            statusCounts={statusCounts}
            data-testid="tasklist-card-progress-bar"
          />
        )}
        {!statusCounts && (
          <div className="h-1 bg-[var(--border)] rounded-full" />
        )}
      </Card>
    );
  }

  // Default variant: full card with all details
  // Requirements: 5.9 - Responsive internal layout adapts based on card width
  return (
    <Card
      ref={cardRef}
      variant="glass"
      padding={isCompact ? "sm" : "md"}
      spotlight={effectiveSpotlight}
      tilt={effectiveTilt}
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
      data-variant="default"
      data-layout-mode={isCompact ? "compact" : isReduced ? "reduced" : "full"}
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

      {/* Task List Name - adapts typography based on width */}
      <Typography
        variant={isCompact ? "body-sm" : "h5"}
        color="primary"
        className={cn(
          isCompact ? "truncate font-medium" : "mb-2 line-clamp-2 pr-16"
        )}
        data-testid="tasklist-card-name"
      >
        {taskList.name}
      </Typography>

      {/* Description - hidden on narrow cards (Requirements: 5.9) */}
      {showDescription && taskList.description && (
        <Typography
          variant="body-sm"
          color="secondary"
          className="mb-4 line-clamp-2"
          data-testid="tasklist-card-description"
        >
          {taskList.description}
        </Typography>
      )}

      {/* Stats Section - adapts based on card width */}
      {stats && (
        <div className={cn("mt-3", showDetailedStats ? "space-y-3" : "space-y-2")} data-testid="tasklist-card-stats">
          {/* Compact stats row - shown when card is narrow */}
          {isCompact ? (
            <>
              {/* Compact: Use OverallProgress mini variant */}
              {statusCounts && (
                <OverallProgress
                  statusCounts={statusCounts}
                  variant="mini"
                  data-testid="tasklist-card-progress"
                />
              )}
            </>
          ) : (
            <>
              {/* Task Count - shown in reduced and full modes */}
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

              {/* OverallProgress organism - Requirements: 15.2, 15.4 */}
              {statusCounts && (
                <OverallProgress
                  statusCounts={statusCounts}
                  variant={showStatusBreakdown ? "compact" : "mini"}
                  data-testid="tasklist-card-progress"
                />
              )}
            </>
          )}
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
