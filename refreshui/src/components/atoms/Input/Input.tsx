import React from "react";
import { cn } from "../../../lib/utils";

/**
 * Input Atom Component
 *
 * A foundational input component supporting multiple types and states.
 * Uses CSS variables from the design token system for consistent styling.
 *
 * Requirements: 3.2
 * - Types: text, search, password
 * - States: default, focus, error, disabled
 * - Optional icons (left and right)
 */

export type InputType = "text" | "search" | "password";
export type InputState = "default" | "focus" | "error" | "disabled";

export interface InputProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, "type"> {
  /** Input type */
  type?: InputType;
  /** Visual state of the input */
  state?: InputState;
  /** Icon to display on the left side */
  leftIcon?: React.ReactNode;
  /** Icon to display on the right side */
  rightIcon?: React.ReactNode;
  /** Label text above the input */
  label?: string;
  /** Error message to display below the input */
  errorMessage?: string;
}

/** Base styles applied to all inputs */
const baseStyles = [
  "w-full",
  "px-4",
  "py-2.5",
  "text-sm",
  "rounded-lg",
  "border",
  "bg-[var(--bg-surface)]",
  "text-[var(--text-primary)]",
  "placeholder:text-[var(--text-tertiary)]",
  "transition-all",
  "duration-200",
  "ease-out",
  "outline-none",
].join(" ");

/** State-specific styles */
const stateStyles: Record<InputState, string> = {
  default: [
    "border-[var(--border)]",
    "hover:border-[var(--border-hover,var(--primary))]",
    "focus:border-[var(--primary)]",
    "focus:ring-2",
    "focus:ring-[rgba(var(--primary-rgb),0.2)]",
    "focus:shadow-[0_0_0_1px_var(--primary)]",
  ].join(" "),

  focus: [
    "border-[var(--primary)]",
    "ring-2",
    "ring-[rgba(var(--primary-rgb),0.2)]",
    "shadow-[0_0_0_1px_var(--primary)]",
  ].join(" "),

  error: [
    "border-[var(--error)]",
    "focus:border-[var(--error)]",
    "focus:ring-2",
    "focus:ring-[rgba(var(--error-rgb),0.2)]",
    "focus:shadow-[0_0_0_1px_var(--error)]",
  ].join(" "),

  disabled: [
    "border-[var(--border)]",
    "bg-[var(--bg-muted,rgba(0,0,0,0.05))]",
    "text-[var(--text-muted)]",
    "cursor-not-allowed",
    "opacity-60",
  ].join(" "),
};

/** Icon container styles */
const iconContainerStyles = {
  left: "absolute left-3 top-1/2 -translate-y-1/2 text-[var(--text-tertiary)] pointer-events-none flex items-center",
  right:
    "absolute right-3 top-1/2 -translate-y-1/2 text-[var(--text-tertiary)] pointer-events-none flex items-center",
};

/**
 * Input component with types, states, and icon support
 */
export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  (
    {
      type = "text",
      state = "default",
      leftIcon,
      rightIcon,
      label,
      errorMessage,
      className,
      disabled,
      ...props
    },
    ref
  ) => {
    // Determine the actual state based on disabled prop
    const actualState = disabled ? "disabled" : state;

    // Calculate padding adjustments for icons
    const paddingLeft = leftIcon ? "pl-10" : "";
    const paddingRight = rightIcon ? "pr-10" : "";

    return (
      <div className="flex flex-col gap-1.5 w-full">
        {label && (
          <label className="text-xs font-medium text-[var(--text-secondary)]">
            {label}
          </label>
        )}
        <div className="relative">
          {leftIcon && (
            <span className={iconContainerStyles.left}>{leftIcon}</span>
          )}
          <input
            ref={ref}
            type={type}
            className={cn(
              baseStyles,
              stateStyles[actualState],
              paddingLeft,
              paddingRight,
              className
            )}
            disabled={disabled || actualState === "disabled"}
            aria-invalid={actualState === "error"}
            aria-describedby={errorMessage ? "input-error" : undefined}
            {...props}
          />
          {rightIcon && (
            <span className={iconContainerStyles.right}>{rightIcon}</span>
          )}
        </div>
        {errorMessage && actualState === "error" && (
          <span
            id="input-error"
            className="text-xs text-[var(--error)] mt-0.5"
            role="alert"
          >
            {errorMessage}
          </span>
        )}
      </div>
    );
  }
);

Input.displayName = "Input";

export default Input;
