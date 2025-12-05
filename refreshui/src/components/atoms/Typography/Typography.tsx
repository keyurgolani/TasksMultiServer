/* eslint-disable react-refresh/only-export-components */
import React from "react";
import { cn } from "../../../lib/utils";

/**
 * Typography Atom Component
 *
 * A foundational typography component providing consistent text styling
 * across the application. Uses CSS variables from the design token system.
 *
 * Requirements: 3.4
 * - Heading levels: h1, h2, h3, h4, h5, h6
 * - Body text variants: body, body-sm, body-lg
 * - Caption and label variants
 * - Consistent styling using design tokens
 *
 * Property 7: Typography Element Mapping
 * - Each variant renders the semantically correct HTML element
 */

export type TypographyVariant =
  | "h1"
  | "h2"
  | "h3"
  | "h4"
  | "h5"
  | "h6"
  | "body"
  | "body-sm"
  | "body-lg"
  | "caption"
  | "label";

export type TypographyColor =
  | "primary"
  | "secondary"
  | "muted"
  | "inherit"
  | "success"
  | "warning"
  | "error"
  | "info";

export interface TypographyProps extends React.HTMLAttributes<HTMLElement> {
  /** Typography variant determining size and semantic element */
  variant?: TypographyVariant;
  /** Text color */
  color?: TypographyColor;
  /** Whether to truncate text with ellipsis */
  truncate?: boolean;
  /** Custom HTML element to render (overrides default element mapping) */
  as?: React.ElementType;
  /** Typography content */
  children: React.ReactNode;
}

/**
 * Maps typography variants to their semantic HTML elements
 * This ensures proper document structure and accessibility
 */
const variantElementMap: Record<TypographyVariant, React.ElementType> = {
  h1: "h1",
  h2: "h2",
  h3: "h3",
  h4: "h4",
  h5: "h5",
  h6: "h6",
  body: "p",
  "body-sm": "p",
  "body-lg": "p",
  caption: "span",
  label: "label",
};

/** Variant-specific styles using CSS variables */
const variantStyles: Record<TypographyVariant, string> = {
  h1: [
    "text-[var(--font-size-5xl)]",
    "font-[var(--font-weight-bold)]",
    "leading-[var(--line-height-tight)]",
    "tracking-[var(--letter-spacing-tight)]",
  ].join(" "),

  h2: [
    "text-[var(--font-size-4xl)]",
    "font-[var(--font-weight-bold)]",
    "leading-[var(--line-height-tight)]",
    "tracking-[var(--letter-spacing-tight)]",
  ].join(" "),

  h3: [
    "text-[var(--font-size-3xl)]",
    "font-[var(--font-weight-semibold)]",
    "leading-[var(--line-height-tight)]",
    "tracking-[var(--letter-spacing-normal)]",
  ].join(" "),

  h4: [
    "text-[var(--font-size-2xl)]",
    "font-[var(--font-weight-semibold)]",
    "leading-[var(--line-height-tight)]",
    "tracking-[var(--letter-spacing-normal)]",
  ].join(" "),

  h5: [
    "text-[var(--font-size-xl)]",
    "font-[var(--font-weight-semibold)]",
    "leading-[var(--line-height-normal)]",
    "tracking-[var(--letter-spacing-normal)]",
  ].join(" "),

  h6: [
    "text-[var(--font-size-lg)]",
    "font-[var(--font-weight-semibold)]",
    "leading-[var(--line-height-normal)]",
    "tracking-[var(--letter-spacing-normal)]",
  ].join(" "),

  body: [
    "text-[var(--font-size-base)]",
    "font-[var(--font-weight-normal)]",
    "leading-[var(--line-height-normal)]",
    "tracking-[var(--letter-spacing-normal)]",
  ].join(" "),

  "body-sm": [
    "text-[var(--font-size-sm)]",
    "font-[var(--font-weight-normal)]",
    "leading-[var(--line-height-normal)]",
    "tracking-[var(--letter-spacing-normal)]",
  ].join(" "),

  "body-lg": [
    "text-[var(--font-size-lg)]",
    "font-[var(--font-weight-normal)]",
    "leading-[var(--line-height-relaxed)]",
    "tracking-[var(--letter-spacing-normal)]",
  ].join(" "),

  caption: [
    "text-[var(--font-size-xs)]",
    "font-[var(--font-weight-normal)]",
    "leading-[var(--line-height-normal)]",
    "tracking-[var(--letter-spacing-wide)]",
  ].join(" "),

  label: [
    "text-[var(--font-size-sm)]",
    "font-[var(--font-weight-medium)]",
    "leading-[var(--line-height-normal)]",
    "tracking-[var(--letter-spacing-normal)]",
  ].join(" "),
};

/** Color-specific styles using CSS variables */
const colorStyles: Record<TypographyColor, string> = {
  primary: "text-[var(--text-primary)]",
  secondary: "text-[var(--text-secondary)]",
  muted: "text-[var(--text-muted)]",
  inherit: "text-inherit",
  success: "text-[var(--success)]",
  warning: "text-[var(--warning)]",
  error: "text-[var(--error)]",
  info: "text-[var(--info)]",
};

/**
 * Typography component with semantic element mapping
 */
export const Typography = React.forwardRef<HTMLElement, TypographyProps>(
  (
    {
      variant = "body",
      color = "primary",
      truncate = false,
      as,
      children,
      className,
      ...props
    },
    ref
  ) => {
    // Determine the HTML element to render
    const Component = as || variantElementMap[variant];

    // Truncation styles
    const truncateStyles = truncate
      ? "overflow-hidden text-ellipsis whitespace-nowrap"
      : "";

    return (
      <Component
        ref={ref}
        className={cn(
          variantStyles[variant],
          colorStyles[color],
          truncateStyles,
          className
        )}
        {...props}
      >
        {children}
      </Component>
    );
  }
);

Typography.displayName = "Typography";

export default Typography;

/**
 * Export variant element map for testing purposes
 * This allows property tests to verify correct element mapping
 */
export { variantElementMap };
