import React, { useRef } from "react";
import { Card } from "../../atoms/Card";
import { Badge, type BadgeVariant } from "../../atoms/Badge";
import { Typography } from "../../atoms/Typography";
import { StatusIndicator, type StatusType } from "../../molecules/StatusIndicator";
import { OverallProgress } from "../OverallProgress";
import { useElementSize } from "../../../core/hooks/useElementSize";
import type { Task, TaskPriority, TaskStatus } from "../../../core/types/entities";
import { cn } from "../../../lib/utils";

/**
 * TaskCard Organism Component
 *
 * A complex card component for displaying task information with status,
 * priority, and glassmorphism styling. Combines atoms and molecules
 * to create a cohesive task display.
 *
 * Requirements: 5.1, 1.9
 * - Display task title, status indicator, priority badge, and progress information
 * - Apply glassmorphism styling using CSS variables
 * - Support spotlight glow effect following cursor
 * - Support parallax tilt effect on hover
 * - Support "ready" variant for flatter, wider display in ready tasks sidebar
 *
 * Property 14: TaskCard Content Completeness
 * - For any Task object, the TaskCard SHALL render the title, status indicator,
 *   priority badge, and all non-empty fields.
 */

/** Variant type for TaskCard display modes */
export type TaskCardVariant = "default" | "ready" | "dependency";

export interface TaskCardProps {
  /** The task data to display */
  task: Task;
  /** Display variant - "default" for standard card, "ready" for flatter sidebar display */
  variant?: TaskCardVariant;
  /** Task list name to display (used in "ready" variant) */
  taskListName?: string;
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
 * Supports two variants:
 * - "default": Standard card with full details
 * - "ready": Flatter, wider card for ready tasks sidebar with essential info
 *
 * Requirements: 1.9 - ReadyTaskCard variant displays flatter, wider layout
 * Requirements: 7.10 - Responsive internal layout
 * - Detects card width and adapts internal elements
 * - Shows compact variants of status, priority, tags when narrow
 * - Hides or resizes secondary information on narrow cards
 */
export const TaskCard: React.FC<TaskCardProps> = ({
  task,
  variant = "default",
  taskListName,
  onClick,
  spotlight = true,
  tilt = true,
  className,
}) => {
  const cardRef = useRef<HTMLDivElement>(null);
  const { isCompact, isReduced } = useElementSize(cardRef);
  const statusType = mapTaskStatusToIndicator(task.status);
  const priorityVariant = mapPriorityToVariant(task.priority);
  const exitCriteriaProgress = calculateExitCriteriaProgress(task.exitCriteria);
  const statusGradient = getStatusGradient(task.status);

  // Determine if status should pulse (in_progress or blocked)
  const shouldPulse = task.status === "IN_PROGRESS" || task.status === "BLOCKED";
  
  // Responsive layout flags for default variant
  const showDescription = !isCompact && !isReduced;
  const showStatusText = !isCompact;
  const showExitCriteria = !isCompact;
  const showTags = !isCompact;
  const showDependencies = !isCompact && !isReduced;
  const showNotes = !isCompact && !isReduced;

  // Dependency variant: compact inline card for displaying task dependencies
  // Shows status, priority, title, and action plan count in a single row
  if (variant === "dependency") {
    const actionPlanCount = task.actionPlan?.length ?? 0;
    
    return (
      <Card
        variant="glass"
        padding="sm"
        spotlight={false}
        tilt={false}
        className={cn(
          "cursor-pointer",
          "hover:shadow-sm",
          "transition-shadow",
          "duration-200",
          "w-full",
          className
        )}
        style={{ 
          background: statusGradient,
          minHeight: "48px",
          maxHeight: "56px",
        }}
        onClick={onClick}
        role="article"
        aria-label={`Dependency task: ${task.title}`}
        data-testid="task-card-dependency"
      >
        <div className="flex items-center gap-2">
          <StatusIndicator
            status={statusType}
            pulse={shouldPulse}
            size="sm"
          />
          <Badge variant={priorityVariant} size="sm">
            {task.priority.charAt(0)}
          </Badge>
          <Typography
            variant="body-sm"
            color="primary"
            className="font-medium truncate flex-1"
            data-testid="task-card-title"
            title={task.title}
          >
            {task.title}
          </Typography>
          {/* Action plan count indicator - always shown, even when 0 */}
          <div
            className="flex items-center gap-1 text-[var(--text-muted)] flex-shrink-0"
            data-testid="task-card-dependency-action-plan"
            title={`${actionPlanCount} action plan ${actionPlanCount === 1 ? "item" : "items"}`}
          >
            <svg
              className="w-3 h-3"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"
              />
            </svg>
            <Typography variant="caption" color="muted">
              {actionPlanCount}
            </Typography>
          </div>
          {exitCriteriaProgress.total > 0 && (
            <Typography variant="caption" color="muted" className="flex-shrink-0">
              {exitCriteriaProgress.completed}/{exitCriteriaProgress.total}
            </Typography>
          )}
        </div>
      </Card>
    );
  }

  // Ready variant: flatter, wider card with essential info only
  // Requirements: 1.9, 1.12 - Fixed height that doesn't change with viewport
  // Requirements: 19.1, 19.2, 19.3 - Action plan count badge in top-right corner
  // Displays action plan count and tags
  if (variant === "ready") {
    const actionPlanCount = task.actionPlan?.length ?? 0;
    
    return (
      <Card
        variant="glass"
        padding="sm"
        spotlight={spotlight}
        tilt={tilt}
        className={cn(
          "cursor-pointer",
          "hover:shadow-md",
          "transition-shadow",
          "duration-200",
          "w-full",
          "relative", // Enable absolute positioning for badge
          className
        )}
        style={{ 
          background: statusGradient,
          height: "auto", // Allow height to accommodate additional info
          minHeight: "88px", // Increased min height for additional content
          maxHeight: "120px", // Cap max height
        }}
        onClick={onClick}
        role="article"
        aria-label={`Ready task: ${task.title}`}
        data-testid="task-card-ready"
      >
        {/* Action plan count badge - Requirements: 19.1, 19.2, 19.3 */}
        {/* Positioned in top-right corner of the card - always shown, even when 0 */}
        <div
          className="absolute top-2 right-2 flex items-center gap-1 px-1.5 py-0.5 rounded-full bg-[var(--bg-surface-hover)] text-[var(--text-muted)]"
          data-testid="task-card-ready-action-plan-badge"
          title={`${actionPlanCount} action plan ${actionPlanCount === 1 ? "item" : "items"}`}
        >
          <svg
            className="w-3 h-3"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"
            />
          </svg>
          <Typography variant="caption" color="muted" className="text-[10px]">
            {actionPlanCount}
          </Typography>
        </div>

        {/* Compact header with status dot and priority */}
        <div className="flex items-center gap-2 mb-1">
          <StatusIndicator
            status={statusType}
            pulse={shouldPulse}
            size="sm"
          />
          <Badge variant={priorityVariant} size="sm">
            {formatPriority(task.priority)}
          </Badge>
        </div>

        {/* Title - single line with truncation */}
        <Typography
          variant="body-sm"
          color="primary"
          className="font-medium truncate mb-1 pr-12" // Add right padding to avoid overlap with badge
          data-testid="task-card-title"
          title={task.title}
        >
          {task.title}
        </Typography>

        {/* Tags row - Requirements: 1.9 */}
        {task.tags && task.tags.length > 0 && (
          <div className="flex items-center gap-1 flex-wrap" data-testid="task-card-ready-tags">
            {task.tags.slice(0, 2).map((tag, index) => (
              <span
                key={`${tag}-${index}`}
                className="px-1.5 py-0.5 text-[10px] rounded-full bg-[var(--bg-surface-hover)] text-[var(--text-secondary)]"
              >
                {tag}
              </span>
            ))}
            {task.tags.length > 2 && (
              <span className="px-1.5 py-0.5 text-[10px] rounded-full bg-[var(--bg-surface-hover)] text-[var(--text-muted)]">
                +{task.tags.length - 2}
              </span>
            )}
          </div>
        )}
      </Card>
    );
  }

  // Default variant: full card with all details
  // Requirements: 7.10 - Responsive internal layout adapts based on card width
  return (
    <Card
      ref={cardRef}
      variant="glass"
      padding={isCompact ? "sm" : "md"}
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
      data-layout-mode={isCompact ? "compact" : isReduced ? "reduced" : "full"}
    >
      {/* Header: Status indicator and Priority badge - adapts based on width */}
      <div className={cn("flex items-center justify-between", isCompact ? "mb-1" : "mb-3")}>
        <div className="flex items-center gap-2">
          <StatusIndicator
            status={statusType}
            pulse={shouldPulse}
            size="sm"
          />
          {/* Status text - hidden on compact cards (Requirements: 7.10) */}
          {showStatusText && (
            <Typography
              variant="caption"
              color="muted"
              className="uppercase tracking-wider"
            >
              {formatStatus(task.status)}
            </Typography>
          )}
        </div>
        <Badge variant={priorityVariant} size="sm">
          {isCompact ? task.priority.charAt(0) : formatPriority(task.priority)}
        </Badge>
      </div>

      {/* Title - adapts typography based on width */}
      <Typography
        variant={isCompact ? "body-sm" : "h6"}
        color="primary"
        className={cn(
          isCompact ? "truncate font-medium" : "mb-2 line-clamp-2"
        )}
        data-testid="task-card-title"
      >
        {task.title}
      </Typography>

      {/* Description - hidden on narrow cards (Requirements: 7.10) */}
      {showDescription && task.description && (
        <Typography
          variant="body-sm"
          color="secondary"
          className="mb-3 line-clamp-2"
          data-testid="task-card-description"
        >
          {task.description}
        </Typography>
      )}

      {/* Exit Criteria Progress - hidden on compact cards (Requirements: 7.10, 15.3, 15.4) */}
      {showExitCriteria && exitCriteriaProgress.total > 0 && (
        <div className="mt-3" data-testid="task-card-progress">
          <OverallProgress
            variant="exit-criteria"
            exitCriteriaProgress={{
              completed: exitCriteriaProgress.completed,
              total: exitCriteriaProgress.total,
            }}
            exitCriteriaLabel={isReduced ? "Criteria" : "Exit Criteria"}
          />
        </div>
      )}

      {/* Compact mode: show minimal info row */}
      {isCompact && (
        <div className="flex items-center gap-2 mt-1 text-[var(--text-muted)]">
          {exitCriteriaProgress.total > 0 && (
            <Typography variant="caption" color="muted">
              {exitCriteriaProgress.completed}/{exitCriteriaProgress.total}
            </Typography>
          )}
          {task.tags && task.tags.length > 0 && (
            <Typography variant="caption" color="muted">
              {task.tags.length} tags
            </Typography>
          )}
        </div>
      )}

      {/* Tags - hidden on compact cards, limited on reduced (Requirements: 7.10) */}
      {showTags && task.tags && task.tags.length > 0 && (
        <div className="flex flex-wrap gap-1 mt-3" data-testid="task-card-tags">
          {task.tags.slice(0, isReduced ? 2 : 3).map((tag, index) => (
            <span
              key={`${tag}-${index}`}
              className="px-2 py-0.5 text-xs rounded-full bg-[var(--bg-surface-hover)] text-[var(--text-secondary)]"
            >
              {tag}
            </span>
          ))}
          {task.tags.length > (isReduced ? 2 : 3) && (
            <span className="px-2 py-0.5 text-xs rounded-full bg-[var(--bg-surface-hover)] text-[var(--text-muted)]">
              +{task.tags.length - (isReduced ? 2 : 3)}
            </span>
          )}
        </div>
      )}

      {/* Dependencies indicator - hidden on narrow cards (Requirements: 7.10) */}
      {showDependencies && task.dependencies && task.dependencies.length > 0 && (
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

      {/* Notes indicator - hidden on narrow cards (Requirements: 7.10) */}
      {showNotes && (task.notes?.length > 0 ||
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

      {/* Action plan indicator - hidden on narrow cards (Requirements: 7.10) - always shown, even when 0 */}
      {showNotes && (
        <div
          className="flex items-center gap-1 mt-2 text-[var(--text-muted)]"
          data-testid="task-card-action-plan"
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
              d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"
            />
          </svg>
          <Typography variant="caption" color="muted">
            {task.actionPlan?.length ?? 0} action {(task.actionPlan?.length ?? 0) === 1 ? "item" : "items"}
          </Typography>
        </div>
      )}
    </Card>
  );
};

TaskCard.displayName = "TaskCard";

export default TaskCard;
