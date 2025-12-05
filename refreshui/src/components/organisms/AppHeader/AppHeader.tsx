import React from "react";
import { cn } from "../../../lib/utils";
import { Typography } from "../../atoms/Typography";
import { Icon } from "../../atoms/Icon";

/**
 * AppHeader Organism Component
 *
 * A consistent application header with branding, title, logo, and glassmorphism styling.
 * Provides visual feedback on hover and supports multiple logo variants.
 *
 * Requirements: 13.1, 13.2, 13.3, 13.4, 13.5
 * - 13.1: Display AppHeader component with application title and logo
 * - 13.2: Use design tokens for typography and colors
 * - 13.3: Support both icon and text variants with configurable sizing
 * - 13.4: Apply glassmorphism effect consistent with other surface elements
 * - 13.5: Provide visual feedback using hover states
 *
 * Property 29: AppHeader Branding Display
 * - For any AppHeader configuration, the component SHALL render the title
 *   and/or logo based on the provided props.
 */

export type LogoVariant = "icon" | "text" | "both";
export type LogoSize = "sm" | "md" | "lg";

export interface AppHeaderProps extends React.HTMLAttributes<HTMLElement> {
  /** Application title to display */
  title?: string;
  /** Whether to show the logo */
  showLogo?: boolean;
  /** Logo display variant: icon only, text only, or both */
  logoVariant?: LogoVariant;
  /** Size of the logo */
  logoSize?: LogoSize;
  /** Custom logo icon name (Lucide icon) */
  logoIcon?: string;
  /** Custom logo text (defaults to title if not provided) */
  logoText?: string;
  /** Additional content to render in the header (e.g., navigation, actions) */
  children?: React.ReactNode;
  /** Whether to apply sticky positioning */
  sticky?: boolean;
}

/** Logo size mapping to pixel values */
const logoSizeMap: Record<LogoSize, { icon: number; text: string }> = {
  sm: { icon: 20, text: "text-lg" },
  md: { icon: 24, text: "text-xl" },
  lg: { icon: 32, text: "text-2xl" },
};

/**
 * AppHeader component with glassmorphism styling and branding
 */
export const AppHeader = React.forwardRef<HTMLElement, AppHeaderProps>(
  (
    {
      title = "Task Manager",
      showLogo = true,
      logoVariant = "both",
      logoSize = "md",
      logoIcon = "CheckSquare",
      logoText,
      children,
      sticky = true,
      className,
      ...props
    },
    ref
  ) => {
    const sizeConfig = logoSizeMap[logoSize];
    const displayLogoText = logoText || title;

    // Determine what to show based on logoVariant
    const showIcon = showLogo && (logoVariant === "icon" || logoVariant === "both");
    const showText = showLogo && (logoVariant === "text" || logoVariant === "both");

    return (
      <header
        ref={ref}
        className={cn(
          // Base styles
          "w-full",
          "h-[var(--header-height)]",
          "px-[var(--space-6)]",
          "flex",
          "items-center",
          "justify-between",
          "gap-[var(--space-4)]",
          // Glassmorphism effect (Requirement 13.4)
          "bg-[var(--glass-bg)]",
          "backdrop-blur-[var(--glass-blur)]",
          "border-b",
          "border-[var(--glass-border)]",
          "shadow-[var(--glass-shadow)]",
          // Sticky positioning
          sticky && [
            "sticky",
            "top-0",
            "z-[var(--z-sticky)]",
          ],
          // Transition for hover effects
          "transition-all",
          "duration-[calc(var(--duration-normal)*1s)]",
          "ease-[var(--ease-default)]",
          className
        )}
        role="banner"
        aria-label="Application header"
        data-testid="app-header"
        {...props}
      >
        {/* Logo and Title Section */}
        <div
          className={cn(
            "flex",
            "items-center",
            "gap-[var(--space-3)]",
            // Hover effect (Requirement 13.5)
            "group",
            "cursor-pointer",
            "rounded-[var(--radius-md)]",
            "px-[var(--space-2)]",
            "py-[var(--space-1)]",
            "-ml-[var(--space-2)]",
            "transition-all",
            "duration-[calc(var(--duration-fast)*1s)]",
            "hover:bg-[var(--bg-surface-hover)]"
          )}
          data-testid="app-header-branding"
        >
          {/* Logo Icon */}
          {showIcon && (
            <div
              className={cn(
                "flex",
                "items-center",
                "justify-center",
                "text-[var(--primary)]",
                "transition-transform",
                "duration-[calc(var(--duration-fast)*1s)]",
                "group-hover:scale-110"
              )}
              data-testid="app-header-logo-icon"
            >
              <Icon
                name={logoIcon as keyof typeof import("lucide-react")}
                size={sizeConfig.icon}
                className="text-[var(--primary)]"
              />
            </div>
          )}

          {/* Logo Text / Title */}
          {showText && (
            <Typography
              variant="h5"
              color="primary"
              className={cn(
                sizeConfig.text,
                "font-[var(--font-weight-bold)]",
                "tracking-[var(--letter-spacing-tight)]",
                "transition-colors",
                "duration-[calc(var(--duration-fast)*1s)]",
                "group-hover:text-[var(--primary)]"
              )}
              data-testid="app-header-title"
            >
              {displayLogoText}
            </Typography>
          )}
        </div>

        {/* Children (navigation, actions, etc.) */}
        {children && (
          <div
            className="flex items-center gap-[var(--space-4)] flex-1 justify-end"
            data-testid="app-header-content"
          >
            {children}
          </div>
        )}
      </header>
    );
  }
);

AppHeader.displayName = "AppHeader";

export default AppHeader;
