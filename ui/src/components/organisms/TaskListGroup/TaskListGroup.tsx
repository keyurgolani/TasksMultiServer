import React, { useState, useCallback, useMemo } from "react";
import { Card } from "../../atoms/Card";
import { Typography } from "../../atoms/Typography";
import { Icon } from "../../atoms/Icon";
import { TaskCard } from "../TaskCard";
import type { TaskList, Task } from "../../../core/types/entities";
import type { TaskListStats } from "../../../services/types";
import { cn } from "../../../lib/utils";
import { useMasonry, type MasonryItem } from "../../../core/hooks/useMasonry";
import { useResponsiveColumns } from "../../../core/hooks/useResponsiveColumns";

/**
 * Layout type for tasks within the TaskListGroup
 */
export type TaskLayoutType = "list" | "masonry";

/**
 * Default breakpoints for masonry layout columns
 * Capped at 2 columns to fit grouping width
 */
const MASONRY_COLUMN_BREAKPOINTS: Record<number, number> = {
  0: 1,
  600: 2,
};

/**
 * Default estimated height for task cards in masonry layout
 */
const DEFAULT_TASK_CARD_HEIGHT = 180;

/**
 * Gap between items in masonry layout (in pixels)
 */
const MASONRY_GAP = 12;

/**
 * Interface for task items with masonry layout support
 */
interface TaskMasonryItem extends MasonryItem {
  task: Task;
}

/**
 * TaskListGroup Organism Component
 *
 * A collapsible group component that displays a task list header with its associated
 * tasks. Supports expand/collapse functionality and shows task count when collapsed.
 * Supports both list and masonry layout for tasks.
 *
 * Requirements: 7.3
 * - Display TaskCard components grouped by their parent task lists
 */

export interface TaskListGroupProps {
  /** The task list data to display */
  taskList: TaskList;
  /** Tasks belonging to this task list */
  tasks: Task[];
  /** Statistics for the task list */
  stats?: TaskListStats;
  /** Whether the group is expanded by default */
  defaultExpanded?: boolean;
  /** Handler for task click */
  onTaskClick?: (taskId: string) => void;
  /** 
   * Layout type for tasks
   * @default "masonry"
   */
  taskLayout?: TaskLayoutType;
  /** 
   * Custom breakpoints for masonry layout columns
   */
  masonryBreakpoints?: Record<number, number>;
  /**
   * Enable parallax tilt effect on TaskCards
   * @default false
   */
  enableCardTilt?: boolean;
  /**
   * Enable spotlight effect on TaskCards
   * @default false
   */
  enableCardSpotlight?: boolean;
  /** Additional CSS classes */
  className?: string;
}

/**
 * Gets the progress bar color based on completion percentage
 */
const getProgressColor = (percentage: number): string => {
  if (percentage >= 100) return "var(--success)";
  if (percentage >= 75) return "var(--info)";
  if (percentage >= 50) return "var(--warning)";
  return "var(--primary)";
};

/**
 * Calculates completion percentage from stats
 */
const calculateCompletionPercentage = (stats?: TaskListStats): number => {
  if (!stats || stats.taskCount === 0) {
    return 0;
  }
  return Math.round(stats.completionPercentage);
};

/**
 * Estimates card height based on task content
 */
const estimateTaskCardHeight = (task: Task): number => {
  let height = DEFAULT_TASK_CARD_HEIGHT;
  if (task.description) height += 40;
  if (task.exitCriteria && task.exitCriteria.length > 0) height += 50;
  if (task.tags && task.tags.length > 0) height += 30;
  if (task.dependencies && task.dependencies.length > 0) height += 25;
  return height;
};

/**
 * TaskListGroup component for displaying a task list with its tasks
 */
export const TaskListGroup: React.FC<TaskListGroupProps> = ({
  taskList,
  tasks,
  stats,
  defaultExpanded = true,
  onTaskClick,
  taskLayout = "masonry",
  masonryBreakpoints = MASONRY_COLUMN_BREAKPOINTS,
  enableCardTilt = false,
  enableCardSpotlight = false,
  className,
}) => {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  const completionPercentage = calculateCompletionPercentage(stats);
  const progressColor = getProgressColor(completionPercentage);
  const taskCount = tasks.length;

  // Get responsive column count for masonry layout
  const { columnCount } = useResponsiveColumns({
    breakpoints: masonryBreakpoints,
  });

  // Convert tasks to masonry items with estimated heights
  const masonryItems = useMemo((): TaskMasonryItem[] => {
    if (taskLayout !== "masonry") return [];
    
    return tasks.map((task) => ({
      id: task.id,
      height: estimateTaskCardHeight(task),
      task,
    }));
  }, [tasks, taskLayout]);

  // Use masonry hook for column distribution
  const { columns } = useMasonry(masonryItems, {
    columnCount,
    gap: MASONRY_GAP,
  });

  /**
   * Toggle expanded/collapsed state
   */
  const handleToggle = useCallback(() => {
    setIsExpanded((prev) => !prev);
  }, []);

  /**
   * Handle keyboard interaction for accessibility
   */
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        handleToggle();
      }
    },
    [handleToggle]
  );

  return (
    <div
      className={cn("space-y-2", className)} // Reduced margin-bottom: 8px per Requirements 21.2, 21.3
      data-testid="task-list-group"
    >
      {/* Collapsible Header - Compact styling per Requirements 21.2, 21.3 */}
      <Card
        variant="glass"
        padding="none"
        className={cn(
          "cursor-pointer",
          "hover:shadow-lg",
          "transition-all",
          "duration-[var(--duration-normal)]",
          "py-2 px-3" // Compact padding: 8px 12px
        )}
        onClick={handleToggle}
        onKeyDown={handleKeyDown}
        role="button"
        tabIndex={0}
        aria-expanded={isExpanded}
        aria-controls={`task-list-group-content-${taskList.id}`}
        aria-label={`${taskList.name} - ${taskCount} tasks - ${isExpanded ? "collapse" : "expand"}`}
        data-testid="task-list-group-header"
      >
        <div className="flex items-center justify-between">
          {/* Left side: Chevron and Task List Name */}
          <div className="flex items-center gap-[var(--space-2)]">
            <Icon
              name={isExpanded ? "ChevronDown" : "ChevronRight"}
              size="sm"
              className={cn(
                "text-[var(--text-muted)]",
                "transition-transform",
                "duration-[var(--duration-fast)]"
              )}
              data-testid="task-list-group-chevron"
            />
            <div>
              <Typography
                variant="body-sm"
                color="primary"
                className="line-clamp-1 font-semibold"
                data-testid="task-list-group-name"
              >
                {taskList.name}
              </Typography>
              {taskList.description && (
                <Typography
                  variant="caption"
                  color="muted"
                  className="line-clamp-1 text-xs"
                  data-testid="task-list-group-description"
                >
                  {taskList.description}
                </Typography>
              )}
            </div>
          </div>

          {/* Right side: Task Count and Stats - Compact styling */}
          <div className="flex items-center gap-[var(--space-3)]">
            {/* Task Count Badge */}
            <div
              className={cn(
                "flex",
                "items-center",
                "gap-[var(--space-1)]",
                "px-2",
                "py-0.5",
                "rounded-full",
                "bg-[var(--bg-surface)]",
                "border",
                "border-[var(--border)]"
              )}
              data-testid="task-list-group-task-count"
            >
              <Icon
                name="CheckSquare"
                size="sm"
                className="text-[var(--text-muted)]"
              />
              <Typography variant="caption" color="secondary">
                {taskCount} {taskCount === 1 ? "task" : "tasks"}
              </Typography>
            </div>

            {/* Progress indicator (when stats available) */}
            {stats && stats.taskCount > 0 && (
              <div
                className="flex items-center gap-[var(--space-1)]"
                data-testid="task-list-group-progress"
              >
                <div
                  className="w-12 h-1.5 bg-[var(--progress-bar-bg)] rounded-full overflow-hidden"
                  data-testid="task-list-group-progress-bar"
                >
                  <div
                    className="h-full rounded-full transition-all duration-500 ease-out"
                    style={{
                      width: `${completionPercentage}%`,
                      backgroundColor: progressColor,
                    }}
                    role="progressbar"
                    aria-valuenow={completionPercentage}
                    aria-valuemin={0}
                    aria-valuemax={100}
                    aria-label={`Task list completion: ${completionPercentage}%`}
                  />
                </div>
                <Typography
                  variant="caption"
                  color="muted"
                  className="text-xs"
                  data-testid="task-list-group-completion-text"
                >
                  {completionPercentage}%
                </Typography>
              </div>
            )}
          </div>
        </div>
      </Card>

      {/* Tasks Content (when expanded) */}
      {isExpanded && (
        <div
          id={`task-list-group-content-${taskList.id}`}
          className={cn(
            "animate-in",
            "fade-in",
            "slide-in-from-top-2",
            "duration-200"
          )}
          data-testid="task-list-group-content"
        >
          {tasks.length > 0 ? (
            taskLayout === "masonry" ? (
              /* Masonry Grid Layout */
              <div
                className="flex gap-[var(--space-3)] w-fit"
                data-testid="task-list-group-masonry-grid"
                data-layout="masonry"
                data-columns={columnCount}
              >
                {columns.map((column, columnIndex) => (
                  <div
                    key={`column-${columnIndex}`}
                    className="flex flex-col gap-[var(--space-3)] w-[425px]"
                    data-testid={`task-list-group-masonry-column-${columnIndex}`}
                  >
                    {column.items.map((item) => (
                      <TaskCard
                        key={item.id}
                        task={(item as TaskMasonryItem).task}
                        onClick={() => onTaskClick?.((item as TaskMasonryItem).task.id)}
                        spotlight={enableCardSpotlight}
                        tilt={enableCardTilt}
                      />
                    ))}
                  </div>
                ))}
              </div>
            ) : (
              /* Traditional List Layout */
              <div
                className="space-y-[var(--space-3)]"
                data-testid="task-list-group-list"
                data-layout="list"
              >
                {tasks.map((task) => (
                  <TaskCard
                    key={task.id}
                    task={task}
                    onClick={() => onTaskClick?.(task.id)}
                    spotlight={enableCardSpotlight}
                    tilt={enableCardTilt}
                  />
                ))}
              </div>
            )
          ) : (
            <Card
              variant="outline"
              padding="md"
              className="text-center"
              data-testid="task-list-group-empty"
            >
              <Typography variant="body-sm" color="muted">
                No tasks in this list
              </Typography>
            </Card>
          )}
        </div>
      )}
    </div>
  );
};

TaskListGroup.displayName = "TaskListGroup";

export default TaskListGroup;
