import React from "react";
import { cn } from "../../../lib/utils";

/**
 * Button Atom Component
 * 
 * A foundational button component supporting multiple variants and sizes.
 * Uses CSS variables from the design token system for consistent styling.
 * 
 * Requirements: 3.1
 * - Variants: primary, secondary, tertiary, ghost, destructive
 * - Sizes: sm, md, lg
 */

export type ButtonVariant = "primary" | "secondary" | "tertiary" | "ghost" | "destructive";
export type ButtonSize = "sm" | "md" | "lg";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  /** Visual style variant */
  variant?: ButtonVariant;
  /** Size of the button */
  size?: ButtonSize;
  /** Whether the button is in a loading state */
  loading?: boolean;
  /** Icon to display on the left side */
  leftIcon?: React.ReactNode;
  /** Icon to display on the right side */
  rightIcon?: React.ReactNode;
  /** Button content */
  children: React.ReactNode;
}

/** Base styles applied to all buttons */
const baseStyles = [
  "inline-flex",
  "items-center",
  "justify-center",
  "gap-2",
  "font-semibold",
  "cursor-pointer",
  "transition-all",
  "duration-200",
  "ease-out",
  "border",
  "outline-none",
  "relative",
  "overflow-hidden",
  "disabled:opacity-50",
  "disabled:cursor-not-allowed",
  "disabled:pointer-events-none",
  "active:scale-[0.98]",
].join(" ");

/** Variant-specific styles */
const variantStyles: Record<ButtonVariant, string> = {
  primary: [
    "bg-[var(--primary)]",
    "text-white",
    "border-transparent",
    "shadow-[0_2px_4px_rgba(var(--primary-rgb),0.2)]",
    "hover:brightness-110",
    "hover:shadow-[0_4px_12px_rgba(var(--primary-rgb),0.3)]",
    "hover:-translate-y-0.5",
    "focus-visible:ring-2",
    "focus-visible:ring-[var(--primary)]",
    "focus-visible:ring-offset-2",
  ].join(" "),
  
  secondary: [
    "bg-[var(--bg-surface)]",
    "text-[var(--text-primary)]",
    "border-[var(--border)]",
    "hover:bg-[var(--bg-surface-hover)]",
    "hover:border-[var(--primary)]",
    "hover:-translate-y-0.5",
    "hover:shadow-[0_2px_8px_var(--shadow)]",
    "focus-visible:ring-2",
    "focus-visible:ring-[var(--primary)]",
    "focus-visible:ring-offset-2",
  ].join(" "),
  
  tertiary: [
    "bg-transparent",
    "text-[var(--primary)]",
    "border-[var(--primary)]",
    "hover:bg-[rgba(var(--primary-rgb),0.1)]",
    "hover:-translate-y-0.5",
    "focus-visible:ring-2",
    "focus-visible:ring-[var(--primary)]",
    "focus-visible:ring-offset-2",
  ].join(" "),
  
  ghost: [
    "bg-transparent",
    "text-[var(--text-secondary)]",
    "border-transparent",
    "hover:bg-[rgba(var(--primary-rgb),0.1)]",
    "hover:text-[var(--primary)]",
    "hover:-translate-y-0.5",
    "focus-visible:ring-2",
    "focus-visible:ring-[var(--primary)]",
    "focus-visible:ring-offset-2",
  ].join(" "),
  
  destructive: [
    "bg-[var(--error)]",
    "text-white",
    "border-transparent",
    "shadow-[0_2px_4px_rgba(var(--error-rgb),0.2)]",
    "hover:brightness-110",
    "hover:shadow-[0_4px_12px_rgba(var(--error-rgb),0.3)]",
    "hover:-translate-y-0.5",
    "focus-visible:ring-2",
    "focus-visible:ring-[var(--error)]",
    "focus-visible:ring-offset-2",
  ].join(" "),
};

/** Size-specific styles */
const sizeStyles: Record<ButtonSize, string> = {
  sm: "h-8 px-3 text-[13px] rounded-md",
  md: "h-10 px-4 text-sm rounded-lg",
  lg: "h-12 px-6 text-base rounded-lg",
};

/**
 * Button component with variants and sizes
 */
export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = "primary",
      size = "md",
      loading = false,
      leftIcon,
      rightIcon,
      children,
      className,
      disabled,
      ...props
    },
    ref
  ) => {
    const isDisabled = disabled || loading;

    return (
      <button
        ref={ref}
        className={cn(
          baseStyles,
          variantStyles[variant],
          sizeStyles[size],
          className
        )}
        disabled={isDisabled}
        aria-busy={loading}
        {...props}
      >
        {loading ? (
          <span className="animate-spin h-4 w-4 border-2 border-current border-t-transparent rounded-full" />
        ) : (
          leftIcon && <span className="flex items-center">{leftIcon}</span>
        )}
        {children}
        {!loading && rightIcon && (
          <span className="flex items-center">{rightIcon}</span>
        )}
      </button>
    );
  }
);

Button.displayName = "Button";

export default Button;
