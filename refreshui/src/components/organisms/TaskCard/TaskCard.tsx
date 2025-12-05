import React from "react";
import { Card } from "../../atoms/Card";
import { Badge, type BadgeVariant } from "../../atoms/Badge";
import { Typography } from "../../atoms/Typography";
import { StatusIndicator, type StatusType } from "../../molecules/StatusIndicator";
import type { Task, TaskPriority, TaskStatus } from "../../../core/types/entities";
import { cn } from "../../../lib/utils";

/**
 * TaskCard Organism Component
 *
 * A complex card component for displaying task information with status,
 * priority, and glassmorphism styling. Combines atoms and molecules
 * to create a cohesive task display.
 *
 * Requirements: 5.1
 * - Display task title, status indicator, priority badge, and progress information
 * - Apply glassmorphism styling using CSS variables
 * - Support spotlight glow effect following cursor
 * - Support parallax tilt effect on hover
 *
 * Property 14: TaskCard Content Completeness
 * - For any Task object, the TaskCard SHALL render the title, status indicator,
 *   priority badge, and all non-empty fields.
 */

export interface TaskCardProps {
  /** The task data to display */
  task: Task;
  /** Click handler for the card */
  onClick?: () => void;
  /** Enable spotlight glow effect following cursor */
  spotlight?: boolean;
  /** Enable parallax tilt effect on hover */
  tilt?: boolean;
  /** Additional CSS classes */
  className?: string;
}

/**
 * Maps TaskStatus to StatusIndicator status type
 */
const mapTaskStatusToIndicator = (status: TaskStatus): StatusType => {
  const statusMap: Record<TaskStatus, StatusType> = {
    NOT_STARTED: "not_started",
    IN_PROGRESS: "in_progress",
    COMPLETED: "completed",
    BLOCKED: "blocked",
  };
  return statusMap[status];
};

/**
 * Maps TaskPriority to Badge variant
 */
const mapPriorityToVariant = (priority: TaskPriority): BadgeVariant => {
  const priorityMap: Record<TaskPriority, BadgeVariant> = {
    CRITICAL: "error",
    HIGH: "warning",
    MEDIUM: "info",
    LOW: "neutral",
    TRIVIAL: "neutral",
  };
  return priorityMap[priority];
};


/**
 * Formats priority text for display
 */
const formatPriority = (priority: TaskPriority): string => {
  return priority.charAt(0) + priority.slice(1).toLowerCase();
};

/**
 * Formats status text for display
 */
const formatStatus = (status: TaskStatus): string => {
  return status.replace(/_/g, " ").toLowerCase().replace(/\b\w/g, (c) => c.toUpperCase());
};

/**
 * Calculates exit criteria completion percentage
 */
const calculateExitCriteriaProgress = (
  exitCriteria: Task["exitCriteria"]
): { completed: number; total: number; percentage: number } => {
  if (!exitCriteria || exitCriteria.length === 0) {
    return { completed: 0, total: 0, percentage: 0 };
  }
  const completed = exitCriteria.filter((ec) => ec.status === "COMPLETE").length;
  const total = exitCriteria.length;
  const percentage = Math.round((completed / total) * 100);
  return { completed, total, percentage };
};

/**
 * Gets the status-based background gradient for the card
 */
const getStatusGradient = (status: TaskStatus): string => {
  const gradients: Record<TaskStatus, string> = {
    IN_PROGRESS:
      "radial-gradient(circle at top left, color-mix(in srgb, var(--warning) 15%, transparent) 0%, transparent 70%)",
    COMPLETED:
      "radial-gradient(circle at top left, color-mix(in srgb, var(--success) 15%, transparent) 0%, transparent 70%)",
    BLOCKED:
      "radial-gradient(circle at top left, color-mix(in srgb, var(--error) 15%, transparent) 0%, transparent 70%)",
    NOT_STARTED:
      "radial-gradient(circle at top left, color-mix(in srgb, #808080 10%, transparent) 0%, transparent 70%)",
  };
  return gradients[status];
};

/**
 * TaskCard component for displaying task information
 */
export const TaskCard: React.FC<TaskCardProps> = ({
  task,
  onClick,
  spotlight = true,
  tilt = true,
  className,
}) => {
  const statusType = mapTaskStatusToIndicator(task.status);
  const priorityVariant = mapPriorityToVariant(task.priority);
  const exitCriteriaProgress = calculateExitCriteriaProgress(task.exitCriteria);
  const statusGradient = getStatusGradient(task.status);

  // Determine if status should pulse (in_progress or blocked)
  const shouldPulse = task.status === "IN_PROGRESS" || task.status === "BLOCKED";

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
        className
      )}
      style={{ background: statusGradient }}
      onClick={onClick}
      role="article"
      aria-label={`Task: ${task.title}`}
      data-testid="task-card"
    >
      {/* Header: Status indicator and Priority badge */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <StatusIndicator
            status={statusType}
            pulse={shouldPulse}
            size="md"
          />
          <Typography
            variant="caption"
            color="muted"
            className="uppercase tracking-wider"
          >
            {formatStatus(task.status)}
          </Typography>
        </div>
        <Badge variant={priorityVariant} size="sm">
          {formatPriority(task.priority)}
        </Badge>
      </div>

      {/* Title */}
      <Typography
        variant="h6"
        color="primary"
        className="mb-2 line-clamp-2"
        data-testid="task-card-title"
      >
        {task.title}
      </Typography>

      {/* Description (if present) */}
      {task.description && (
        <Typography
          variant="body-sm"
          color="secondary"
          className="mb-3 line-clamp-2"
          data-testid="task-card-description"
        >
          {task.description}
        </Typography>
      )}

      {/* Exit Criteria Progress (if present) */}
      {exitCriteriaProgress.total > 0 && (
        <div className="mt-3" data-testid="task-card-progress">
          <div className="flex items-center justify-between mb-1">
            <Typography variant="caption" color="muted">
              Exit Criteria
            </Typography>
            <Typography variant="caption" color="secondary">
              {exitCriteriaProgress.completed}/{exitCriteriaProgress.total}
            </Typography>
          </div>
          <div className="h-1.5 bg-[var(--progress-bar-bg)] rounded-full overflow-hidden">
            <div
              className="h-full bg-[var(--primary)] rounded-full transition-all duration-300"
              style={{ width: `${exitCriteriaProgress.percentage}%` }}
              role="progressbar"
              aria-valuenow={exitCriteriaProgress.percentage}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label={`Exit criteria progress: ${exitCriteriaProgress.percentage}%`}
            />
          </div>
        </div>
      )}

      {/* Tags (if present) */}
      {task.tags && task.tags.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-3" data-testid="task-card-tags">
          {task.tags.slice(0, 3).map((tag, index) => (
            <span
              key={`${tag}-${index}`}
              className="px-2 py-0.5 text-xs rounded-full bg-[var(--bg-surface-hover)] text-[var(--text-secondary)]"
            >
              {tag}
            </span>
          ))}
          {task.tags.length > 3 && (
            <span className="px-2 py-0.5 text-xs rounded-full bg-[var(--bg-surface-hover)] text-[var(--text-muted)]">
              +{task.tags.length - 3}
            </span>
          )}
        </div>
      )}

      {/* Dependencies indicator (if present) */}
      {task.dependencies && task.dependencies.length > 0 && (
        <div
          className="flex items-center gap-1 mt-3 text-[var(--text-muted)]"
          data-testid="task-card-dependencies"
        >
          <svg
            className="w-3.5 h-3.5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"
            />
          </svg>
          <Typography variant="caption" color="muted">
            {task.dependencies.length} {task.dependencies.length === 1 ? "dependency" : "dependencies"}
          </Typography>
        </div>
      )}

      {/* Notes indicator (if present) */}
      {(task.notes?.length > 0 ||
        task.researchNotes?.length > 0 ||
        task.executionNotes?.length > 0) && (
        <div
          className="flex items-center gap-1 mt-2 text-[var(--text-muted)]"
          data-testid="task-card-notes"
        >
          <svg
            className="w-3.5 h-3.5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
            />
          </svg>
          <Typography variant="caption" color="muted">
            {(task.notes?.length || 0) +
              (task.researchNotes?.length || 0) +
              (task.executionNotes?.length || 0)}{" "}
            notes
          </Typography>
        </div>
      )}
    </Card>
  );
};

TaskCard.displayName = "TaskCard";

export default TaskCard;
