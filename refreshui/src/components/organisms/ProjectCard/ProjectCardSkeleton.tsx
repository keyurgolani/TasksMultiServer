import React from "react";
import { Skeleton } from "../../atoms/Skeleton";
import { cn } from "../../../lib/utils";

/**
 * ProjectCardSkeleton Component
 *
 * A skeleton loading placeholder that matches the expected layout
 * of the ProjectCard component.
 *
 * Requirements: 10.5
 * - Display skeleton placeholders matching the expected content layout
 */

export interface ProjectCardSkeletonProps {
  /** Additional CSS classes */
  className?: string;
}

/**
 * ProjectCardSkeleton component for loading states
 */
export const ProjectCardSkeleton: React.FC<ProjectCardSkeletonProps> = ({
  className,
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
      data-testid="project-card-skeleton"
      aria-label="Loading project"
      role="status"
    >
      {/* Project Name */}
      <Skeleton variant="text" width="70%" height={24} className="mb-3" />

      {/* Description */}
      <Skeleton variant="text" lines={2} className="mb-4" />

      {/* Stats Section */}
      <div className="mt-3 space-y-3">
        {/* Task List Count */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Skeleton variant="circular" width={16} height={16} />
            <Skeleton variant="text" width={80} />
          </div>
          <Skeleton variant="text" width={24} />
        </div>

        {/* Total Tasks */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Skeleton variant="circular" width={16} height={16} />
            <Skeleton variant="text" width={80} />
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

ProjectCardSkeleton.displayName = "ProjectCardSkeleton";

export default ProjectCardSkeleton;
