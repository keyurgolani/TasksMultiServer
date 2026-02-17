import React from "react";
import { cn } from "../../../lib/utils";

/**
 * Skeleton Atom Component
 *
 * A foundational loading placeholder component that displays animated
 * skeleton states while content is loading. Uses CSS variables from
 * the design token system for consistent styling and animation.
 *
 * Requirements: 10.5
 * - Display skeleton placeholders matching expected content layout
 * - Support multiple variants: text, rectangular, circular
 * - Animate with pulse effect using theme animation speed
 */

export type SkeletonVariant = "text" | "rectangular" | "circular";

export interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Shape variant of the skeleton */
  variant?: SkeletonVariant;
  /** Width of the skeleton (CSS value or number for pixels) */
  width?: string | number;
  /** Height of the skeleton (CSS value or number for pixels) */
  height?: string | number;
  /** Whether to animate the skeleton */
  animate?: boolean;
  /** Number of lines for text variant */
  lines?: number;
}

/** Base styles applied to all skeletons */
const baseStyles = [
  "bg-[var(--bg-surface-hover)]",
  "relative",
  "overflow-hidden",
].join(" ");

/** Animation styles for the shimmer effect */
const animationStyles = [
  "before:absolute",
  "before:inset-0",
  "before:translate-x-[-100%]",
  "before:animate-[shimmer_calc(1.5s*var(--animation-speed))_infinite]",
  "before:bg-gradient-to-r",
  "before:from-transparent",
  "before:via-[var(--bg-surface-active)]",
  "before:to-transparent",
].join(" ");

/** Variant-specific styles */
const variantStyles: Record<SkeletonVariant, string> = {
  text: "h-4 w-full rounded-[var(--radius-sm)]",
  rectangular: "rounded-[var(--radius-md)]",
  circular: "rounded-full aspect-square",
};

/**
 * Converts a width/height value to a CSS string
 */
const toCssValue = (value: string | number | undefined): string | undefined => {
  if (value === undefined) return undefined;
  return typeof value === "number" ? `${value}px` : value;
};

/**
 * Skeleton component for loading states
 *
 * Supports single elements or multiple text lines for paragraph placeholders.
 */
export const Skeleton = React.forwardRef<HTMLDivElement, SkeletonProps>(
  ({ variant = "text", width, height, animate = true, lines = 1, className, style, ...props }, ref) => {
    const computedStyle: React.CSSProperties = {
      width: toCssValue(width),
      height: toCssValue(height),
      ...style,
    };

    // For text variant with multiple lines, render a container with multiple skeletons
    if (variant === "text" && lines > 1) {
      return (
        <div ref={ref} className={cn("flex flex-col gap-2", className)}>
          {Array.from({ length: lines }).map((_, index) => (
            <div
              key={index}
              className={cn(
                baseStyles,
                variantStyles.text,
                animate && animationStyles
              )}
              style={{
                // Make the last line shorter for a more natural look
                width: index === lines - 1 ? "75%" : "100%",
              }}
              aria-hidden="true"
            />
          ))}
        </div>
      );
    }

    return (
      <div
        ref={ref}
        className={cn(
          baseStyles,
          variantStyles[variant],
          animate && animationStyles,
          className
        )}
        style={computedStyle}
        aria-hidden="true"
        {...props}
      />
    );
  }
);

Skeleton.displayName = "Skeleton";

export default Skeleton;
