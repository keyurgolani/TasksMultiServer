import React from "react";
import { cn } from "../../../lib/utils";

/**
 * Badge Atom Component
 *
 * A foundational badge component for displaying status indicators and labels.
 * Uses CSS variables from the design token system for consistent styling.
 *
 * Requirements: 3.6
 * - Variants: success, warning, error, info, neutral
 * - Sizes: sm, md
 */

export type BadgeVariant = "success" | "warning" | "error" | "info" | "neutral";
export type BadgeSize = "sm" | "md";

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  /** Visual style variant based on status */
  variant?: BadgeVariant;
  /** Size of the badge */
  size?: BadgeSize;
  /** Badge content */
  children: React.ReactNode;
}

/** Base styles applied to all badges */
const baseStyles = [
  "inline-flex",
  "items-center",
  "justify-center",
  "font-semibold",
  "uppercase",
  "tracking-wide",
  "whitespace-nowrap",
  "transition-all",
  "duration-200",
  "ease-out",
  "rounded-full",
].join(" ");

/** Variant-specific styles using CSS variables */
const variantStyles: Record<BadgeVariant, string> = {
  success: [
    "bg-[var(--status-success-bg)]",
    "text-[var(--status-success-text)]",
  ].join(" "),

  warning: [
    "bg-[var(--status-warning-bg)]",
    "text-[var(--status-warning-text)]",
  ].join(" "),

  error: [
    "bg-[var(--status-error-bg)]",
    "text-[var(--status-error-text)]",
  ].join(" "),

  info: [
    "bg-[var(--status-info-bg)]",
    "text-[var(--status-info-text)]",
  ].join(" "),

  neutral: [
    "bg-[var(--status-neutral-bg)]",
    "text-[var(--status-neutral-text)]",
  ].join(" "),
};

/** Size-specific styles */
const sizeStyles: Record<BadgeSize, string> = {
  sm: "h-5 px-2 text-[10px] tracking-[0.3px]",
  md: "h-6 px-3 text-[11px] tracking-[0.4px]",
};

/**
 * Badge component with status variants and sizes
 */
export const Badge = React.forwardRef<HTMLSpanElement, BadgeProps>(
  ({ variant = "neutral", size = "md", children, className, ...props }, ref) => {
    return (
      <span
        ref={ref}
        className={cn(baseStyles, variantStyles[variant], sizeStyles[size], className)}
        {...props}
      >
        {children}
      </span>
    );
  }
);

Badge.displayName = "Badge";

export default Badge;
