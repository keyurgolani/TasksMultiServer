import React, { useState, useCallback, useMemo } from "react";
import { Card } from "../../atoms/Card";
import { Typography } from "../../atoms/Typography";
import { Icon } from "../../atoms/Icon";
import { TaskListCard } from "../TaskListCard";
import type { Project, TaskList } from "../../../core/types/entities";
import type { ProjectStats, TaskListStats } from "../../../services/types";
import { cn } from "../../../lib/utils";
import { useMasonry, type MasonryItem } from "../../../core/hooks/useMasonry";
import { useResponsiveColumns } from "../../../core/hooks/useResponsiveColumns";

/**
 * Layout type for task lists within the ProjectGroup
 */
export type TaskListLayoutType = "list" | "masonry";

/**
 * Default breakpoints for masonry layout columns
 * - 1 column below 600px
 * - 2 columns 600-1200px
 * - 3 columns above 1200px
 */
const MASONRY_COLUMN_BREAKPOINTS: Record<number, number> = {
  0: 1,
  600: 2,
  1200: 3,
};

/**
 * Default estimated height for task list cards in masonry layout
 */
const DEFAULT_TASK_LIST_CARD_HEIGHT = 200;

/**
 * Gap between items in masonry layout (in pixels)
 * Uses --space-3 (12px) from design tokens
 */
const MASONRY_GAP = 12;

/**
 * Interface for task list items with masonry layout support
 */
interface TaskListMasonryItem extends MasonryItem {
  taskList: TaskList;
}

/**
 * ProjectGroup Organism Component
 *
 * A collapsible group component that displays a project header with its associated
 * task lists. Supports expand/collapse functionality and shows task list count
 * when collapsed. Supports both list and masonry layout for task lists.
 *
 * Requirements: 24.1, 24.2, 24.3, 24.4, 24.5, 48.1, 48.2, 48.3, 48.4
 * - Display the project name as a collapsible header
 * - Toggle visibility of task lists on header click
 * - Show count of task lists in collapsed state
 * - Display all task lists when expanded
 * - Apply glassmorphism effect and design system styling
 * - Support masonry grid layout for task lists
 * - Responsive column count based on viewport width
 * - Minimize vertical gaps using masonry positioning algorithm
 * - Apply consistent gap spacing using design tokens
 *
 * Property 49: ProjectGroup Collapse State
 * - For any ProjectGroup component, clicking the header SHALL toggle the
 *   expanded/collapsed state.
 *
 * Property 50: ProjectGroup Task List Display
 * - For any ProjectGroup in expanded state, the component SHALL render all
 *   task lists belonging to that project.
 *
 * Property 83: ProjectGroup Masonry Layout
 * - For any ProjectGroup with taskListLayout="masonry", the component SHALL
 *   display task lists in a masonry grid layout with responsive columns.
 */

export interface ProjectGroupProps {
  /** The project data to display */
  project: Project;
  /** Task lists belonging to this project */
  taskLists: TaskList[];
  /** Statistics for the project */
  stats?: ProjectStats;
  /** Statistics for each task list, keyed by task list ID */
  taskListStats?: Record<string, TaskListStats>;
  /** Whether the group is expanded by default */
  defaultExpanded?: boolean;
  /** Handler for task list click */
  onTaskListClick?: (taskListId: string) => void;
  /** Handler for task list edit */
  onTaskListEdit?: (taskList: TaskList) => void;
  /** Handler for task list delete */
  onTaskListDelete?: (taskList: TaskList) => void;
  /** 
   * Layout type for task lists
   * - "list": Traditional vertical list layout (default)
   * - "masonry": Masonry grid layout with responsive columns
   * @default "list"
   */
  taskListLayout?: TaskListLayoutType;
  /** 
   * Custom breakpoints for masonry layout columns
   * Keys are minimum viewport widths, values are column counts
   * Only used when taskListLayout is "masonry"
   */
  masonryBreakpoints?: Record<number, number>;
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
const calculateCompletionPercentage = (stats?: ProjectStats): number => {
  if (!stats || stats.totalTasks === 0) {
    return 0;
  }
  return Math.round((stats.completedTasks / stats.totalTasks) * 100);
};

/**
 * ProjectGroup component for displaying a project with its task lists
 */
export const ProjectGroup: React.FC<ProjectGroupProps> = ({
  project,
  taskLists,
  stats,
  taskListStats,
  defaultExpanded = true,
  onTaskListClick,
  onTaskListEdit,
  onTaskListDelete,
  taskListLayout = "list",
  masonryBreakpoints = MASONRY_COLUMN_BREAKPOINTS,
  className,
}) => {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  const completionPercentage = calculateCompletionPercentage(stats);
  const progressColor = getProgressColor(completionPercentage);
  const taskListCount = taskLists.length;

  // Get responsive column count for masonry layout
  const { columnCount } = useResponsiveColumns({
    breakpoints: masonryBreakpoints,
  });

  // Convert task lists to masonry items with estimated heights
  const masonryItems = useMemo((): TaskListMasonryItem[] => {
    if (taskListLayout !== "masonry") return [];
    
    return taskLists.map((taskList) => {
      // Estimate height based on content
      // Base height + description + stats section
      let estimatedHeight = DEFAULT_TASK_LIST_CARD_HEIGHT;
      
      // Add height for description if present
      if (taskList.description) {
        estimatedHeight += 40;
      }
      
      // Add height for stats if present
      const hasStats = taskListStats?.[taskList.id];
      if (hasStats) {
        estimatedHeight += 60;
      }
      
      return {
        id: taskList.id,
        height: estimatedHeight,
        taskList,
      };
    });
  }, [taskLists, taskListStats, taskListLayout]);

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
      className={cn("space-y-[var(--space-3)]", className)}
      data-testid="project-group"
    >
      {/* Collapsible Header */}
      <Card
        variant="glass"
        padding="md"
        className={cn(
          "cursor-pointer",
          "hover:shadow-lg",
          "transition-all",
          "duration-[var(--duration-normal)]"
        )}
        onClick={handleToggle}
        onKeyDown={handleKeyDown}
        role="button"
        tabIndex={0}
        aria-expanded={isExpanded}
        aria-controls={`project-group-content-${project.id}`}
        aria-label={`${project.name} - ${taskListCount} task lists - ${isExpanded ? "collapse" : "expand"}`}
        data-testid="project-group-header"
      >
        <div className="flex items-center justify-between">
          {/* Left side: Chevron and Project Name */}
          <div className="flex items-center gap-[var(--space-3)]">
            <Icon
              name={isExpanded ? "ChevronDown" : "ChevronRight"}
              size="md"
              className={cn(
                "text-[var(--text-muted)]",
                "transition-transform",
                "duration-[var(--duration-fast)]"
              )}
              data-testid="project-group-chevron"
            />
            <div>
              <Typography
                variant="h5"
                color="primary"
                className="line-clamp-1"
                data-testid="project-group-name"
              >
                {project.name}
              </Typography>
              {project.description && (
                <Typography
                  variant="caption"
                  color="muted"
                  className="line-clamp-1 mt-1"
                  data-testid="project-group-description"
                >
                  {project.description}
                </Typography>
              )}
            </div>
          </div>

          {/* Right side: Task List Count and Stats */}
          <div className="flex items-center gap-[var(--space-4)]">
            {/* Task List Count Badge */}
            <div
              className={cn(
                "flex",
                "items-center",
                "gap-[var(--space-2)]",
                "px-[var(--space-3)]",
                "py-[var(--space-1)]",
                "rounded-full",
                "bg-[var(--bg-surface)]",
                "border",
                "border-[var(--border)]"
              )}
              data-testid="project-group-tasklist-count"
            >
              <Icon
                name="ClipboardList"
                size="sm"
                className="text-[var(--text-muted)]"
              />
              <Typography variant="body-sm" color="secondary">
                {taskListCount} {taskListCount === 1 ? "list" : "lists"}
              </Typography>
            </div>

            {/* Progress indicator (when stats available) */}
            {stats && stats.totalTasks > 0 && (
              <div
                className="flex items-center gap-[var(--space-2)]"
                data-testid="project-group-progress"
              >
                <div
                  className="w-16 h-2 bg-[var(--progress-bar-bg)] rounded-full overflow-hidden"
                  data-testid="project-group-progress-bar"
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
                    aria-label={`Project completion: ${completionPercentage}%`}
                  />
                </div>
                <Typography
                  variant="caption"
                  color="muted"
                  data-testid="project-group-completion-text"
                >
                  {completionPercentage}%
                </Typography>
              </div>
            )}
          </div>
        </div>
      </Card>

      {/* Task Lists Content (when expanded) */}
      {isExpanded && (
        <div
          id={`project-group-content-${project.id}`}
          className={cn(
            "pl-[var(--space-6)]",
            "animate-in",
            "fade-in",
            "slide-in-from-top-2",
            "duration-200"
          )}
          data-testid="project-group-content"
        >
          {taskLists.length > 0 ? (
            taskListLayout === "masonry" ? (
              /* Masonry Grid Layout */
              <div
                className="flex gap-[var(--space-3)]"
                data-testid="project-group-masonry-grid"
                data-layout="masonry"
                data-columns={columnCount}
              >
                {columns.map((column, columnIndex) => (
                  <div
                    key={`column-${columnIndex}`}
                    className="flex-1 flex flex-col gap-[var(--space-3)] min-w-0"
                    data-testid={`project-group-masonry-column-${columnIndex}`}
                  >
                    {column.items.map((item) => (
                      <TaskListCard
                        key={item.id}
                        taskList={(item as TaskListMasonryItem).taskList}
                        stats={taskListStats?.[(item as TaskListMasonryItem).taskList.id]}
                        onClick={() => onTaskListClick?.((item as TaskListMasonryItem).taskList.id)}
                        onEdit={onTaskListEdit}
                        onDelete={onTaskListDelete}
                        spotlight={false}
                        tilt={false}
                      />
                    ))}
                  </div>
                ))}
              </div>
            ) : (
              /* Traditional List Layout */
              <div
                className="space-y-[var(--space-3)]"
                data-testid="project-group-list"
                data-layout="list"
              >
                {taskLists.map((taskList) => (
                  <TaskListCard
                    key={taskList.id}
                    taskList={taskList}
                    stats={taskListStats?.[taskList.id]}
                    onClick={() => onTaskListClick?.(taskList.id)}
                    onEdit={onTaskListEdit}
                    onDelete={onTaskListDelete}
                    spotlight={false}
                    tilt={false}
                  />
                ))}
              </div>
            )
          ) : (
            <Card
              variant="outline"
              padding="md"
              className="text-center"
              data-testid="project-group-empty"
            >
              <Typography variant="body-sm" color="muted">
                No task lists in this project
              </Typography>
            </Card>
          )}
        </div>
      )}
    </div>
  );
};

ProjectGroup.displayName = "ProjectGroup";

export default ProjectGroup;
