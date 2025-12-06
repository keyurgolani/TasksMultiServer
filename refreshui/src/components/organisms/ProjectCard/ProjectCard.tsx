import React, { useState, useMemo, useRef } from "react";
import { Card } from "../../atoms/Card";
import { Typography } from "../../atoms/Typography";
import { Icon } from "../../atoms/Icon";
import { ProgressBar, type StatusCounts } from "../../atoms/ProgressBar";
import { OverallProgress } from "../OverallProgress";
import { useElementSize } from "../../../core/hooks/useElementSize";
import type { Project } from "../../../core/types/entities";
import type { ProjectStats } from "../../../services/types";
import { cn } from "../../../lib/utils";

/**
 * ProjectCard Organism Component
 *
 * A complex card component for displaying project information with task list count
 * and completion statistics. Combines atoms to create a cohesive project display.
 *
 * Requirements: 5.2, 23.1, 1.16
 * - Display project name, task list count, completion stats, and visual progress indicator
 * - Display action buttons for edit and delete on hover
 * - Support minimal variant showing only title and progress bar with very low height
 *
 * Property 15: ProjectCard Content Completeness
 * - For any Project object with associated task lists, the ProjectCard SHALL render
 *   the name, task list count, and completion statistics.
 *
 * Property 47: Card Action Buttons Visibility
 * - For any ProjectCard on hover, the component SHALL display edit and delete action buttons.
 */

export type ProjectCardVariant = "default" | "minimal";

export interface ProjectCardProps {
  /** The project data to display */
  project: Project;
  /** Statistics for the project (task list count, completion stats) */
  stats?: ProjectStats;
  /** Visual variant - "default" shows full card, "minimal" shows only title and progress bar */
  variant?: ProjectCardVariant;
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
 * Converts ProjectStats to StatusCounts for the OverallProgress organism
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
 * 
 * Requirements: 3.8 - Responsive internal layout
 * - Detects card width and adapts internal elements
 * - Shows compact variants of progress indicators, stats when narrow
 * - Hides or resizes secondary information on narrow cards
 */
export const ProjectCard: React.FC<ProjectCardProps> = ({
  project,
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
        aria-label={`Project: ${project.name}`}
        data-testid="project-card"
        data-variant="minimal"
      >
        {/* Project Name - compact */}
        <Typography
          variant="body-sm"
          color="primary"
          className="truncate font-medium mb-1"
          data-testid="project-card-name"
        >
          {project.name}
        </Typography>

        {/* Progress Bar - full width */}
        {statusCounts && (
          <ProgressBar
            variant="multi-state"
            statusCounts={statusCounts}
            data-testid="project-card-progress-bar"
          />
        )}
        {!statusCounts && (
          <div className="h-1 bg-[var(--border)] rounded-full" />
        )}
      </Card>
    );
  }

  // Default variant: full card with all details
  // Requirements: 3.8 - Responsive internal layout adapts based on card width
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
      aria-label={`Project: ${project.name}`}
      data-testid="project-card"
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

      {/* Project Name - adapts typography based on width */}
      <Typography
        variant={isCompact ? "body-sm" : "h5"}
        color="primary"
        className={cn(
          isCompact ? "truncate font-medium" : "mb-2 line-clamp-2 pr-16"
        )}
        data-testid="project-card-name"
      >
        {project.name}
      </Typography>

      {/* Description - hidden on narrow cards (Requirements: 3.8) */}
      {showDescription && project.description && (
        <Typography
          variant="body-sm"
          color="secondary"
          className="mb-4 line-clamp-2"
          data-testid="project-card-description"
        >
          {project.description}
        </Typography>
      )}

      {/* Stats Section - adapts based on card width */}
      {stats && (
        <div className={cn("mt-3", showDetailedStats ? "space-y-3" : "space-y-2")} data-testid="project-card-stats">
          {/* Compact stats row - shown when card is narrow */}
          {isCompact ? (
            <>
              {/* Compact: Use OverallProgress mini variant */}
              {statusCounts && (
                <OverallProgress
                  statusCounts={statusCounts}
                  variant="mini"
                  data-testid="project-card-progress"
                />
              )}
            </>
          ) : (
            <>
              {/* Task List Count - shown in reduced and full modes */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-[var(--space-2)]">
                  <Icon
                    name="ClipboardList"
                    size="sm"
                    className="text-[var(--text-muted)]"
                  />
                  <Typography variant="body-sm" color="muted">
                    {isReduced ? "Lists" : "Task Lists"}
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

              {/* Total Tasks - shown in reduced and full modes */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-[var(--space-2)]">
                  <Icon
                    name="CheckCircle"
                    size="sm"
                    className="text-[var(--text-muted)]"
                  />
                  <Typography variant="body-sm" color="muted">
                    {isReduced ? "Tasks" : "Total Tasks"}
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

              {/* OverallProgress organism - Requirements: 15.1, 15.4 */}
              {statusCounts && (
                <OverallProgress
                  statusCounts={statusCounts}
                  variant={showStatusBreakdown ? "compact" : "mini"}
                  data-testid="project-card-progress"
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
