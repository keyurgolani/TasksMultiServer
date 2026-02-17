import React from "react";
import { cn } from "../../../lib/utils";
import { Icon } from "../../atoms/Icon";
import * as LucideIcons from "lucide-react";

/**
 * ViewSelector Organism Component
 *
 * A navigation component for switching between different views in the application.
 * Displays all available views with icons and labels, highlighting the active view.
 *
 * Requirements: 14.1, 14.2, 14.3, 14.4, 14.5
 * - 14.1: Display all available views (Projects, Task Lists, Tasks, Dashboard)
 * - 14.2: Highlight selected view and emit change event on click
 * - 14.3: Update visual state to indicate active view
 * - 14.4: Support icon and label combinations for each view
 * - 14.5: Apply consistent styling using design tokens
 *
 * Property 30: ViewSelector Active State
 * - For any ViewSelector with a currentView value, the component SHALL visually
 *   highlight the corresponding view option.
 *
 * Property 31: ViewSelector Change Event
 * - For any view option click in the ViewSelector, the component SHALL emit
 *   an onViewChange event with the selected view ID.
 */

/** Available dashboard view types */
export type DashboardView = "dashboard" | "projects" | "taskLists" | "tasks";

/** Configuration for a single view option */
export interface ViewOption {
  /** Unique identifier for the view */
  id: DashboardView;
  /** Display label for the view */
  label: string;
  /** Lucide icon name or React node for the view */
  icon: keyof typeof LucideIcons | React.ReactNode;
}

export interface ViewSelectorProps extends Omit<React.HTMLAttributes<HTMLDivElement>, "onChange"> {
  /** Currently active view */
  currentView: DashboardView;
  /** Callback when view changes */
  onViewChange: (view: DashboardView) => void;
  /** Available view options */
  views?: ViewOption[];
  /** Size variant for the selector */
  size?: "sm" | "md" | "lg";
  /** Whether to show labels alongside icons */
  showLabels?: boolean;
  /** Whether to apply glassmorphism effect to the container */
  glass?: boolean;
}

// Import default views from constants to satisfy react-refresh/only-export-components
import { defaultViews } from "./constants";

/** Size configuration for different variants */
const sizeConfig = {
  sm: {
    container: "p-[var(--space-1)] gap-[var(--space-1)]",
    button: "px-[var(--space-2)] py-[var(--space-1)] gap-[var(--space-1)]",
    icon: 14 as const,
    text: "text-[var(--font-size-xs)]",
  },
  md: {
    container: "p-[var(--space-1)] gap-[var(--space-1)]",
    button: "px-[var(--space-3)] py-[var(--space-2)] gap-[var(--space-2)]",
    icon: 18 as const,
    text: "text-[var(--font-size-sm)]",
  },
  lg: {
    container: "p-[var(--space-2)] gap-[var(--space-2)]",
    button: "px-[var(--space-4)] py-[var(--space-3)] gap-[var(--space-2)]",
    icon: 20 as const,
    text: "text-[var(--font-size-base)]",
  },
};

/**
 * Renders the icon for a view option
 */
const renderIcon = (
  icon: keyof typeof LucideIcons | React.ReactNode,
  size: number,
  isActive: boolean
): React.ReactNode => {
  // If icon is a React node, render it directly
  if (React.isValidElement(icon)) {
    return icon;
  }

  // Otherwise, treat it as a Lucide icon name
  const iconName = icon as keyof typeof LucideIcons;
  return (
    <Icon
      name={iconName}
      size={size}
      className={cn(
        "transition-colors",
        "duration-[calc(var(--duration-fast)*1s)]",
        isActive ? "text-white" : "text-[var(--text-secondary)]"
      )}
    />
  );
};

/**
 * ViewSelector component for switching between application views
 */
export const ViewSelector = React.forwardRef<HTMLDivElement, ViewSelectorProps>(
  (
    {
      currentView,
      onViewChange,
      views = defaultViews,
      size = "md",
      showLabels = true,
      glass = true,
      className,
      ...props
    },
    ref
  ) => {
    const config = sizeConfig[size];

    const handleViewClick = (viewId: DashboardView) => {
      if (viewId !== currentView) {
        onViewChange(viewId);
      }
    };

    return (
      <div
        ref={ref}
        className={cn(
          // Base layout
          "flex",
          "items-center",
          config.container,
          // Border radius
          "rounded-[var(--radius-lg)]",
          // Glassmorphism effect (Requirement 14.5)
          glass && [
            "bg-[var(--glass-bg)]",
            "backdrop-blur-[var(--glass-blur)]",
            "border",
            "border-[var(--glass-border)]",
            "shadow-[var(--glass-shadow)]",
          ],
          // Non-glass fallback
          !glass && [
            "bg-[var(--bg-surface)]",
            "border",
            "border-[var(--border-default)]",
          ],
          className
        )}
        role="tablist"
        aria-label="View selector"
        data-testid="view-selector"
        {...props}
      >
        {views.map((view) => {
          const isActive = currentView === view.id;

          return (
            <button
              key={view.id}
              type="button"
              role="tab"
              aria-selected={isActive}
              aria-controls={`${view.id}-panel`}
              tabIndex={isActive ? 0 : -1}
              onClick={() => handleViewClick(view.id)}
              className={cn(
                // Base layout
                "flex",
                "items-center",
                "justify-center",
                config.button,
                // Border radius
                "rounded-[var(--radius-md)]",
                // Typography
                "font-[var(--font-weight-medium)]",
                config.text,
                // Cursor
                "cursor-pointer",
                // Transitions
                "transition-all",
                "duration-[calc(var(--duration-fast)*1s)]",
                "ease-[var(--ease-default)]",
                // Focus styles
                "focus:outline-none",
                "focus-visible:ring-2",
                "focus-visible:ring-[var(--primary)]",
                "focus-visible:ring-offset-2",
                "focus-visible:ring-offset-[var(--bg-app)]",
                // Active state (Requirements 14.2, 14.3)
                isActive && [
                  "bg-[var(--primary)]",
                  "text-white",
                  "shadow-[var(--glow-primary)]",
                ],
                // Inactive state
                !isActive && [
                  "bg-transparent",
                  "text-[var(--text-secondary)]",
                  "hover:bg-[var(--bg-surface-hover)]",
                  "hover:text-[var(--text-primary)]",
                ]
              )}
              data-testid={`view-selector-option-${view.id}`}
              data-active={isActive}
            >
              {/* Icon (Requirement 14.4) */}
              {renderIcon(view.icon, config.icon, isActive)}

              {/* Label (Requirement 14.4) */}
              {showLabels && (
                <span
                  className={cn(
                    "whitespace-nowrap",
                    "transition-colors",
                    "duration-[calc(var(--duration-fast)*1s)]"
                  )}
                >
                  {view.label}
                </span>
              )}
            </button>
          );
        })}
      </div>
    );
  }
);

ViewSelector.displayName = "ViewSelector";

export default ViewSelector;
