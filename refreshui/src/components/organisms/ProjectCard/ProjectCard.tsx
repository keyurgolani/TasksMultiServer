import React, { useState, useMemo } from "react";
import { Card } from "../../atoms/Card";
import { Typography } from "../../atoms/Typography";
import { Icon } from "../../atoms/Icon";
import { ProgressBar, type StatusCounts } from "../../atoms/ProgressBar";
import type { Project } from "../../../core/types/entities";
import type { ProjectStats } from "../../../services/types";
import { cn } from "../../../lib/utils";

/**
 * ProjectCard Organism Component
 *
 * A complex card component for displaying project information with task list count
 * and completion statistics. Combines atoms to create a cohesive project display.
 *
 * Requirements: 5.2, 23.1
 * - Display project name, task list count, completion stats, and visual progress indicator
 * - Display action buttons for edit and delete on hover
 *
 * Property 15: ProjectCard Content Completeness
 * - For any Project object with associated task lists, the ProjectCard SHALL render
 *   the name, task list count, and completion statistics.
 *
 * Property 47: Card Action Buttons Visibility
 * - For any ProjectCard on hover, the component SHALL display edit and delete action buttons.
 */

export interface ProjectCardProps {
  /** The project data to display */
  project: Project;
  /** Statistics for the project (task list count, completion stats) */
  stats?: ProjectStats;
  /** Click handler for the card */
  onClick?: () => void;
  /** Handler for edit action */
  onEdit?: (project: Project) => void;
  /** Handler for delete action */
  onDelete?: (project: Project) => void;
  /** Enable spotlight glow effect following cursor */
  spotlight?: boolean;
  /** Enable parallax tilt effect on hover */
  tilt?: boolean;
  /** Additional CSS classes */
  className?: string;
}

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
 * Converts ProjectStats to StatusCounts for the ProgressBar component
 */
const convertToStatusCounts = (stats: ProjectStats): StatusCounts => {
  // Calculate not started tasks from total - (completed + in progress + blocked)
  const notStarted = Math.max(
    0,
    stats.totalTasks - stats.completedTasks - stats.inProgressTasks - stats.blockedTasks
  );
  
  return {
    completed: stats.completedTasks,
    inProgress: stats.inProgressTasks,
    blocked: stats.blockedTasks,
    notStarted,
  };
};

/**
 * ProjectCard component for displaying project information
 */
export const ProjectCard: React.FC<ProjectCardProps> = ({
  project,
  stats,
  onClick,
  onEdit,
  onDelete,
  spotlight = true,
  tilt = true,
  className,
}) => {
  const [isHovered, setIsHovered] = useState(false);
  const completionPercentage = calculateCompletionPercentage(stats);
  
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
    onEdit?.(project);
  };

  /**
   * Handle delete button click
   * Stops propagation to prevent card onClick from firing
   */
  const handleDeleteClick = (e: React.MouseEvent) => {
    e.stopPropagation();
    onDelete?.(project);
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
      aria-label={`Project: ${project.name}`}
      data-testid="project-card"
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
          data-testid="project-card-actions"
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
              aria-label={`Edit project: ${project.name}`}
              data-testid="project-card-edit-button"
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
              aria-label={`Delete project: ${project.name}`}
              data-testid="project-card-delete-button"
            >
              <Icon name="Trash2" size="sm" />
            </button>
          )}
        </div>
      )}

      {/* Project Name */}
      <Typography
        variant="h5"
        color="primary"
        className="mb-2 line-clamp-2 pr-16"
        data-testid="project-card-name"
      >
        {project.name}
      </Typography>

      {/* Description (if present) */}
      {project.description && (
        <Typography
          variant="body-sm"
          color="secondary"
          className="mb-4 line-clamp-2"
          data-testid="project-card-description"
        >
          {project.description}
        </Typography>
      )}

      {/* Stats Section */}
      {stats && (
        <div className="mt-3 space-y-3" data-testid="project-card-stats">
          {/* Task List Count */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-[var(--space-2)]">
              <Icon
                name="ClipboardList"
                size="sm"
                className="text-[var(--text-muted)]"
              />
              <Typography variant="body-sm" color="muted">
                Task Lists
              </Typography>
            </div>
            <Typography
              variant="body-sm"
              color="primary"
              data-testid="project-card-tasklist-count"
            >
              {stats.taskListCount}
            </Typography>
          </div>

          {/* Total Tasks */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-[var(--space-2)]">
              <Icon
                name="CheckCircle"
                size="sm"
                className="text-[var(--text-muted)]"
              />
              <Typography variant="body-sm" color="muted">
                Total Tasks
              </Typography>
            </div>
            <Typography
              variant="body-sm"
              color="primary"
              data-testid="project-card-total-tasks"
            >
              {stats.totalTasks}
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
                data-testid="project-card-completion-text"
              >
                {stats.completedTasks}/{stats.totalTasks} ({completionPercentage}%)
              </Typography>
            </div>

            {/* Multi-state Progress Bar using ProgressBar atom */}
            {statusCounts && (
              <ProgressBar
                variant="multi-state-mini"
                statusCounts={statusCounts}
                data-testid="project-card-progress-bar"
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
                data-testid="project-card-in-progress"
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
                data-testid="project-card-blocked"
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
                data-testid="project-card-ready"
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
          data-testid="project-card-no-stats"
        >
          <Typography variant="caption" color="muted">
            No task data available
          </Typography>
        </div>
      )}
    </Card>
  );
};

ProjectCard.displayName = "ProjectCard";

export default ProjectCard;
