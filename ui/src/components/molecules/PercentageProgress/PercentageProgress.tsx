import React from "react";
import { cn } from "../../../lib/utils";
import { ProgressBar } from "../../atoms/ProgressBar";
import { Typography } from "../../atoms/Typography";

/**
 * PercentageProgress Molecule Component
 *
 * A progress bar molecule that displays completion percentage with an "X% completed" label.
 * Combines the ProgressBar atom with Typography for meaningful progress data display.
 *
 * Requirements: 42.2, 42.4, 42.5
 * - Displays progress bar with "X% completed" label
 * - Recalculates and updates both bar and label when data changes
 * - Applies consistent typography and spacing from design tokens
 */

export interface PercentageProgressProps {
  /** Completion percentage (0-100) */
  percentage: number;
  /** Optional label text (defaults to "completed") */
  label?: string;
  /** Visual variant - default or mini */
  variant?: "default" | "mini";
  /** Custom color for the progress bar (CSS color value) */
  color?: string;
  /** Additional CSS classes */
  className?: string;
}

/**
 * Clamp percentage between 0 and 100
 */
const clampPercentage = (value: number): number => {
  return Math.max(0, Math.min(100, Math.round(value)));
};

/**
 * PercentageProgress component
 */
export const PercentageProgress: React.FC<PercentageProgressProps> = ({
  percentage,
  label = "completed",
  variant = "default",
  color = "var(--primary)",
  className,
}) => {
  const clampedPercentage = clampPercentage(percentage);
  const isMini = variant === "mini";

  // Mini variant: horizontal layout with minimal text (percentage only)
  if (isMini) {
    return (
      <div
        className={cn(
          "flex items-center gap-[var(--space-2)]",
          className
        )}
        data-testid="percentage-progress"
      >
        <ProgressBar
          variant="single-mini"
          percentage={clampedPercentage}
          color={color}
        />
        <Typography
          variant="caption"
          color="muted"
          className="whitespace-nowrap"
          data-testid="percentage-progress-label"
        >
          {clampedPercentage}%
        </Typography>
      </div>
    );
  }

  // Default variant: vertical layout with full label
  return (
    <div
      className={cn(
        "flex flex-col gap-[var(--space-2)]",
        className
      )}
      data-testid="percentage-progress"
    >
      {/* Label */}
      <div className="flex items-center justify-between">
        <Typography
          variant="body-sm"
          color="secondary"
          data-testid="percentage-progress-label"
        >
          {clampedPercentage}% {label}
        </Typography>
      </div>

      {/* Progress Bar */}
      <ProgressBar
        variant="single"
        percentage={clampedPercentage}
        color={color}
      />
    </div>
  );
};

PercentageProgress.displayName = "PercentageProgress";

export default PercentageProgress;
