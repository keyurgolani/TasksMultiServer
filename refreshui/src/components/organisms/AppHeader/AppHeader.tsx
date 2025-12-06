import React, { useState } from "react";
import { NavLink, useLocation } from "react-router-dom";
import { cn } from "../../../lib/utils";
import { Typography } from "../../atoms/Typography";
import { Icon } from "../../atoms/Icon";
import { CustomizationButton } from "../../atoms/CustomizationButton";
import { CustomizationPopup } from "../CustomizationPopup";
import { useTheme } from "../../../context/ThemeContext";

/**
 * AppHeader Organism Component
 *
 * A consistent application header with branding, title, logo, navigation links,
 * and glassmorphism styling. Provides visual feedback on hover and supports
 * multiple logo variants.
 *
 * Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 13.1, 13.2, 13.3, 13.4, 13.5, 17.1, 17.2, 17.3, 17.4, 17.5, 17.6
 * - 2.1: Display application logo on the left side
 * - 2.2: Show navigation links for Dashboard, Projects, Lists, and Tasks
 * - 2.3: Navigate to "/" and highlight Dashboard when clicked
 * - 2.4: Navigate to "/projects" and highlight Projects when clicked
 * - 2.5: Navigate to "/lists" and highlight Lists when clicked
 * - 2.6: Navigate to "/tasks" and highlight Tasks when clicked
 * - 2.7: Show CustomizationButton that opens CustomizationPopup
 * - 13.1: Display AppHeader component with application title and logo
 * - 13.2: Use design tokens for typography and colors
 * - 13.3: Support both icon and text variants with configurable sizing
 * - 13.4: Apply glassmorphism effect consistent with other surface elements
 * - 13.5: Provide visual feedback using hover states
 * - 17.1: Logo element has visual isolation in light themes
 * - 17.2: Logo element has visual isolation in dark themes
 * - 17.3: Navigation element has visual isolation in light themes
 * - 17.4: Navigation element has visual isolation in dark themes
 * - 17.5: Theme button has visual isolation in light themes
 * - 17.6: Theme button has visual isolation in dark themes
 *
 * Property 29: AppHeader Branding Display
 * - For any AppHeader configuration, the component SHALL render the title
 *   and/or logo based on the provided props.
 */

export type LogoVariant = "icon" | "text" | "both";
export type LogoSize = "sm" | "md" | "lg";

/** Navigation link configuration */
export interface NavLinkConfig {
  /** Display label for the link */
  label: string;
  /** Route path */
  path: string;
  /** Icon name (Lucide icon) */
  icon?: string;
}

/** Default navigation links */
const defaultNavLinks: NavLinkConfig[] = [
  { label: "Dashboard", path: "/", icon: "LayoutDashboard" },
  { label: "Projects", path: "/projects", icon: "FolderKanban" },
  { label: "Lists", path: "/lists", icon: "ListTodo" },
  { label: "Tasks", path: "/tasks", icon: "CheckSquare" },
];

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
  /** Whether to show navigation links */
  showNavigation?: boolean;
  /** Custom navigation links (defaults to Dashboard, Projects, Lists, Tasks) */
  navLinks?: NavLinkConfig[];
  /** Whether to show the customization button */
  showCustomization?: boolean;
}

/** Logo size mapping to pixel values */
const logoSizeMap: Record<LogoSize, { icon: number; text: string }> = {
  sm: { icon: 20, text: "text-lg" },
  md: { icon: 24, text: "text-xl" },
  lg: { icon: 32, text: "text-2xl" },
};

/**
 * Check if a navigation link is active based on current location
 */
const isNavLinkActive = (path: string, currentPath: string): boolean => {
  // Exact match for root path
  if (path === "/") {
    return currentPath === "/";
  }
  // For other paths, check if current path starts with the nav path
  return currentPath.startsWith(path);
};

/**
 * AppHeader component with glassmorphism styling, branding, and navigation
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
      showNavigation = true,
      navLinks = defaultNavLinks,
      showCustomization = true,
      className,
      ...props
    },
    ref
  ) => {
    const sizeConfig = logoSizeMap[logoSize];
    const displayLogoText = logoText || title;
    const location = useLocation();
    const [isCustomizationOpen, setIsCustomizationOpen] = useState(false);

    // Get theme context for customization
    const {
      activeColorTheme,
      activeFontTheme,
      activeEffectSettings,
      setColorTheme,
      setFontTheme,
      updateEffectSetting,
    } = useTheme();

    // Determine what to show based on logoVariant
    const showIcon = showLogo && (logoVariant === "icon" || logoVariant === "both");
    const showText = showLogo && (logoVariant === "text" || logoVariant === "both");

    // Handle customization popup
    const handleOpenCustomization = () => setIsCustomizationOpen(true);
    const handleCloseCustomization = () => setIsCustomizationOpen(false);

    // Handle theme changes from CustomizationPopup
    const handleColorSchemeChange = (scheme: typeof activeColorTheme) => {
      setColorTheme(scheme.id);
    };

    const handleTypographyChange = (typography: typeof activeFontTheme) => {
      setFontTheme(typography.id);
    };

    const handleEffectsChange = (key: keyof typeof activeEffectSettings, value: number) => {
      updateEffectSetting(key, value);
    };

    return (
      <>
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
          {/* Logo and Title Section (Requirement 2.1, 17.1, 17.2) */}
          <NavLink
            to="/"
            className={cn(
              "flex",
              "items-center",
              "gap-[var(--space-3)]",
              // Hover effect (Requirement 13.5)
              "group",
              "cursor-pointer",
              "rounded-[var(--radius-md)]",
              "px-[var(--space-3)]",
              "py-[var(--space-2)]",
              // Visual isolation with subtle background and border (Requirements 17.1, 17.2)
              "bg-[var(--bg-surface)]",
              "border",
              "border-[var(--border-light)]",
              "shadow-sm",
              // Minimum gap from adjacent elements
              "mr-[var(--space-4)]",
              "transition-all",
              "duration-[calc(var(--duration-fast)*1s)]",
              "hover:bg-[var(--bg-surface-hover)]",
              "hover:border-[var(--border)]",
              "hover:shadow-md",
              "no-underline"
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
          </NavLink>

          {/* Navigation Links (Requirement 2.2, 17.3, 17.4) */}
          {showNavigation && navLinks.length > 0 && (
            <nav
              className={cn(
                "flex items-center gap-[var(--space-1)]",
                // Visual isolation with container background and border (Requirements 17.3, 17.4)
                "bg-[var(--bg-surface)]",
                "border",
                "border-[var(--border-light)]",
                "rounded-[var(--radius-lg)]",
                "px-[var(--space-2)]",
                "py-[var(--space-1)]",
                "shadow-sm",
                // Minimum gap from adjacent elements
                "mx-[var(--space-4)]"
              )}
              aria-label="Main navigation"
              data-testid="app-header-navigation"
            >
              {navLinks.map((link) => {
                const isActive = isNavLinkActive(link.path, location.pathname);
                return (
                  <NavLink
                    key={link.path}
                    to={link.path}
                    className={cn(
                      "flex items-center gap-[var(--space-2)]",
                      "px-[var(--space-3)] py-[var(--space-2)]",
                      "rounded-[var(--radius-md)]",
                      "text-sm font-medium",
                      "transition-all duration-200",
                      "no-underline",
                      // Active state (Requirements 2.3, 2.4, 2.5, 2.6)
                      isActive
                        ? [
                            "bg-[var(--primary)]",
                            "text-[var(--primary-foreground)]",
                          ]
                        : [
                            "text-[var(--text-secondary)]",
                            "hover:bg-[var(--bg-surface-hover)]",
                            "hover:text-[var(--text-primary)]",
                          ]
                    )}
                    data-testid={`app-header-nav-${link.label.toLowerCase()}`}
                    aria-current={isActive ? "page" : undefined}
                  >
                    {link.icon && (
                      <Icon
                        name={link.icon as keyof typeof import("lucide-react")}
                        size={16}
                        className={isActive ? "text-[var(--primary-foreground)]" : ""}
                      />
                    )}
                    <span>{link.label}</span>
                  </NavLink>
                );
              })}
            </nav>
          )}

          {/* Right side: Children and Customization Button (Requirements 17.5, 17.6) */}
          <div className="flex items-center gap-[var(--space-3)] ml-auto">
            {/* Children (additional navigation, actions, etc.) */}
            {children && (
              <div
                className="flex items-center gap-[var(--space-4)]"
                data-testid="app-header-content"
              >
                {children}
              </div>
            )}

            {/* Customization Button (Requirement 2.7, 17.5, 17.6) */}
            {showCustomization && (
              <div
                className={cn(
                  // Visual isolation with container background and border (Requirements 17.5, 17.6)
                  "bg-[var(--bg-surface)]",
                  "border",
                  "border-[var(--border-light)]",
                  "rounded-[var(--radius-lg)]",
                  "p-[var(--space-1)]",
                  "shadow-sm",
                  // Minimum gap from adjacent elements
                  "ml-[var(--space-4)]",
                  "transition-all",
                  "duration-[calc(var(--duration-fast)*1s)]",
                  "hover:border-[var(--border)]",
                  "hover:shadow-md"
                )}
              >
                <CustomizationButton
                  currentScheme={activeColorTheme}
                  typography={activeFontTheme}
                  effects={activeEffectSettings}
                  onClick={handleOpenCustomization}
                  data-testid="app-header-customization-button"
                />
              </div>
            )}
          </div>
        </header>

        {/* Customization Popup (Requirement 2.7) */}
        {showCustomization && (
          <CustomizationPopup
            isOpen={isCustomizationOpen}
            onClose={handleCloseCustomization}
            colorScheme={activeColorTheme}
            typography={activeFontTheme}
            effects={activeEffectSettings}
            onColorSchemeChange={handleColorSchemeChange}
            onTypographyChange={handleTypographyChange}
            onEffectsChange={handleEffectsChange}
          />
        )}
      </>
    );
  }
);

AppHeader.displayName = "AppHeader";

export default AppHeader;
