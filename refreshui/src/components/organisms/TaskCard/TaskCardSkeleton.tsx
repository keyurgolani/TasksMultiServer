import React from "react";
import { Skeleton } from "../../atoms/Skeleton";
import { cn } from "../../../lib/utils";

/**
 * TaskCardSkeleton Component
 *
 * A skeleton loading placeholder that matches the expected layout
 * of the TaskCard component.
 *
 * Requirements: 10.5
 * - Display skeleton placeholders matching the expected content layout
 */

export interface TaskCardSkeletonProps {
  /** Additional CSS classes */
  className?: string;
  /** Whether to show extended content (tags, dependencies, notes) */
  showExtended?: boolean;
}

/**
 * TaskCardSkeleton component for loading states
 */
export const TaskCardSkeleton: React.FC<TaskCardSkeletonProps> = ({
  className,
  showExtended = true,
}) => {
  return (
    <div
      className={cn(
        "p-4 rounded-lg",
        "bg-[var(--bg-surface)]",
        "border border-[var(--border-default)]",
        "backdrop-blur-[var(--glass-blur)]",
        className
      )}
      data-testid="task-card-skeleton"
      aria-label="Loading task"
      role="status"
    >
      {/* Header: Status indicator and Priority badge */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Skeleton variant="circular" width={12} height={12} />
          <Skeleton variant="text" width={80} />
        </div>
        <Skeleton variant="rectangular" width={60} height={20} className="rounded-full" />
      </div>

      {/* Title */}
      <Skeleton variant="text" width="85%" height={20} className="mb-2" />

      {/* Description */}
      <Skeleton variant="text" lines={2} className="mb-3" />

      {/* Exit Criteria Progress */}
      <div className="mt-3">
        <div className="flex items-center justify-between mb-1">
          <Skeleton variant="text" width={80} />
          <Skeleton variant="text" width={30} />
        </div>
        <Skeleton variant="rectangular" height={6} className="rounded-full" />
      </div>

      {showExtended && (
        <>
          {/* Tags */}
          <div className="flex flex-wrap gap-1 mt-3">
            <Skeleton variant="rectangular" width={50} height={20} className="rounded-full" />
            <Skeleton variant="rectangular" width={60} height={20} className="rounded-full" />
            <Skeleton variant="rectangular" width={45} height={20} className="rounded-full" />
          </div>

          {/* Dependencies indicator */}
          <div className="flex items-center gap-1 mt-3">
            <Skeleton variant="circular" width={14} height={14} />
            <Skeleton variant="text" width={100} />
          </div>

          {/* Notes indicator */}
          <div className="flex items-center gap-1 mt-2">
            <Skeleton variant="circular" width={14} height={14} />
            <Skeleton variant="text" width={60} />
          </div>
        </>
      )}
    </div>
  );
};

TaskCardSkeleton.displayName = "TaskCardSkeleton";

export default TaskCardSkeleton;
