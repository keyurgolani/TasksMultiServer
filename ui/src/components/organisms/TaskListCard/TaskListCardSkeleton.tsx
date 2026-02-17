import React from "react";
import { Skeleton } from "../../atoms/Skeleton";
import { cn } from "../../../lib/utils";
import type { TaskListCardVariant } from "./TaskListCard";

/**
 * TaskListCardSkeleton Component
 *
 * A skeleton loading placeholder that matches the expected layout
 * of the TaskListCard component.
 *
 * Requirements: 10.5, 1.17
 * - Display skeleton placeholders matching the expected content layout
 * - Support minimal variant with compact skeleton layout
 */

export interface TaskListCardSkeletonProps {
  /** Visual variant - "default" shows full skeleton, "minimal" shows compact skeleton */
  variant?: TaskListCardVariant;
  /** Additional CSS classes */
  className?: string;
}

/**
 * TaskListCardSkeleton component for loading states
 */
export const TaskListCardSkeleton: React.FC<TaskListCardSkeletonProps> = ({
  variant = "default",
  className,
}) => {
  // Minimal variant: compact skeleton with only title and progress bar
  if (variant === "minimal") {
    return (
      <div
        className={cn(
          "p-3 rounded-lg",
          "bg-[var(--bg-surface)]",
          "border border-[var(--border-default)]",
          "backdrop-blur-[var(--glass-blur)]",
          "h-[52px]",
          "flex flex-col justify-center",
          className
        )}
        data-testid="tasklist-card-skeleton"
        data-variant="minimal"
        aria-label="Loading task list"
        role="status"
      >
        {/* Task List Name - compact */}
        <Skeleton variant="text" width="60%" height={16} className="mb-1" />
        {/* Progress Bar - compact */}
        <Skeleton variant="rectangular" height={4} className="rounded-full" />
      </div>
    );
  }

  // Default variant: full skeleton
  return (
    <div
      className={cn(
        "p-4 rounded-lg",
        "bg-[var(--bg-surface)]",
        "border border-[var(--border-default)]",
        "backdrop-blur-[var(--glass-blur)]",
        className
      )}
      data-testid="tasklist-card-skeleton"
      data-variant="default"
      aria-label="Loading task list"
      role="status"
    >
      {/* Task List Name */}
      <Skeleton variant="text" width="70%" height={24} className="mb-3" />

      {/* Description */}
      <Skeleton variant="text" lines={2} className="mb-4" />

      {/* Stats Section */}
      <div className="mt-3 space-y-3">
        {/* Task Count */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Skeleton variant="circular" width={16} height={16} />
            <Skeleton variant="text" width={50} />
          </div>
          <Skeleton variant="text" width={24} />
        </div>

        {/* Completion Stats */}
        <div className="pt-2 border-t border-[var(--border-default)]">
          <div className="flex items-center justify-between mb-2">
            <Skeleton variant="text" width={70} />
            <Skeleton variant="text" width={80} />
          </div>

          {/* Progress Bar */}
          <Skeleton variant="rectangular" height={8} className="rounded-full" />
        </div>

        {/* Status Breakdown */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-1">
            <Skeleton variant="circular" width={8} height={8} />
            <Skeleton variant="text" width={60} />
          </div>
          <div className="flex items-center gap-1">
            <Skeleton variant="circular" width={8} height={8} />
            <Skeleton variant="text" width={50} />
          </div>
          <div className="flex items-center gap-1">
            <Skeleton variant="circular" width={8} height={8} />
            <Skeleton variant="text" width={40} />
          </div>
        </div>
      </div>
    </div>
  );
};

TaskListCardSkeleton.displayName = "TaskListCardSkeleton";

export default TaskListCardSkeleton;
