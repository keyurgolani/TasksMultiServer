import React, { useMemo } from "react";
import { cn } from "../../../lib/utils";
import {
  type ColorTheme,
  type FontTheme,
  type EffectSettings,
  getThemeCssVariables,
} from "../../../styles/themes";
import { StatusIndicator, type StatusType } from "../StatusIndicator";

/**
 * ThemePreviewSkeleton Molecule Component
 *
 * A skeleton preview component that displays a miniature version of the UI
 * with applied color scheme, typography, and effects. Supports three variants:
 * - full: Complete UI skeleton with header, sidebar, cards, buttons, and text
 * - mini: Compact version for color scheme selection thumbnails
 * - button: Tiny preview for the customization button
 *
 * Requirements: 30.2, 30.3, 35.1, 35.2
 * - Display complete UI skeleton with header, cards, buttons, and text
 * - Support dynamic color scheme and typography application
 * - Implement proportional scaling for different sizes
 */

export interface ThemePreviewSkeletonProps {
  /** Color scheme to apply to the preview */
  colorScheme: ColorTheme;
  /** Typography scheme to apply to the preview */
  typography: FontTheme;
  /** Effect settings to apply to the preview */
  effects: EffectSettings;
  /** Variant of the preview skeleton */
  variant?: "full" | "mini" | "button";
  /** Additional CSS classes */
  className?: string;
}

/**
 * Get dimensions based on variant
 */
const getVariantDimensions = (variant: "full" | "mini" | "button") => {
  switch (variant) {
    case "full":
      return { width: "100%", height: 400, scale: 1 };
    case "mini":
      return { width: 160, height: 100, scale: 0.25 };
    case "button":
      return { width: 40, height: 28, scale: 0.07 };
    default:
      return { width: "100%", height: 400, scale: 1 };
  }
};

/**
 * ThemePreviewSkeleton component with full, mini, and button variants
 */
export const ThemePreviewSkeleton: React.FC<ThemePreviewSkeletonProps> = ({
  colorScheme,
  typography,
  effects,
  variant = "full",
  className,
}) => {
  // Generate CSS variables from theme settings
  const cssVars = useMemo(
    () => getThemeCssVariables(colorScheme, typography, effects) as React.CSSProperties,
    [colorScheme, typography, effects]
  );

  const dimensions = getVariantDimensions(variant);
  const isCompact = variant === "mini" || variant === "button";
  const isTiny = variant === "button";

  return (
    <div
      className={cn(
        "relative overflow-hidden rounded-lg border transition-all duration-200",
        className
      )}
      style={{
        ...cssVars,
        width: typeof dimensions.width === "number" ? `${dimensions.width}px` : dimensions.width,
        height: `${dimensions.height}px`,
        backgroundColor: "var(--bg-app)",
        borderColor: "var(--border)",
        fontFamily: "var(--font-default)",
      }}
    >
      {/* Inner container with scaled content */}
      <div
        className="absolute inset-0 origin-top-left"
        style={{
          transform: `scale(${dimensions.scale})`,
          width: `${100 / dimensions.scale}%`,
          height: `${100 / dimensions.scale}%`,
        }}
      >
        {/* Header */}
        <div
          className="flex items-center justify-between px-6 py-4"
          style={{
            backgroundColor: "var(--bg-surface)",
            borderBottom: "1px solid var(--border)",
          }}
        >
          {/* Logo */}
          <div
            className="rounded"
            style={{
              width: isCompact ? 60 : 100,
              height: isCompact ? 16 : 24,
              backgroundColor: "var(--text-primary)",
              opacity: 0.15,
            }}
          />
          
          {/* Search bar (hidden in button variant) */}
          {!isTiny && (
            <div
              className="flex-1 mx-4 rounded-lg"
              style={{
                height: isCompact ? 20 : 32,
                maxWidth: isCompact ? 120 : 300,
                backgroundColor: "var(--bg-app)",
                border: "1px solid var(--border)",
              }}
            />
          )}
          
          {/* Avatar */}
          <div
            className="rounded-full"
            style={{
              width: isCompact ? 20 : 32,
              height: isCompact ? 20 : 32,
              backgroundColor: "var(--primary)",
              opacity: 0.8,
            }}
          />
        </div>

        {/* Content area */}
        <div className="flex" style={{ height: "calc(100% - 64px)" }}>
          {/* Sidebar (hidden in button variant) */}
          {!isTiny && (
            <div
              className="flex flex-col gap-3 p-4"
              style={{
                width: isCompact ? 100 : 180,
                borderRight: "1px solid var(--border)",
              }}
            >
              {[80, 60, 70, 50].map((width, i) => (
                <div
                  key={i}
                  className="rounded"
                  style={{
                    width: `${width}%`,
                    height: isCompact ? 8 : 12,
                    backgroundColor: "var(--text-primary)",
                    opacity: i === 0 ? 0.2 : 0.1,
                  }}
                />
              ))}
            </div>
          )}

          {/* Main content */}
          <div className="flex-1 p-4 overflow-hidden">
            {/* Page title */}
            <div
              className="rounded mb-4"
              style={{
                width: isCompact ? 80 : 140,
                height: isCompact ? 12 : 20,
                backgroundColor: "var(--text-primary)",
                opacity: 0.2,
              }}
            />

            {/* Cards grid */}
            <div className={cn("grid gap-3", isCompact ? "grid-cols-2" : "grid-cols-2 lg:grid-cols-3")}>
              {/* Card 1 - Success status */}
              <PreviewCard
                title="Design System"
                status="success"
                effects={effects}
                isCompact={isCompact}
                isTiny={isTiny}
              />

              {/* Card 2 - Warning status */}
              {!isTiny && (
                <PreviewCard
                  title="Client Meeting"
                  status="warning"
                  effects={effects}
                  isCompact={isCompact}
                  isTiny={isTiny}
                />
              )}

              {/* Card 3 - Error status */}
              {!isTiny && (
                <PreviewCard
                  title="Bug Fixes"
                  status="error"
                  effects={effects}
                  isCompact={isCompact}
                  isTiny={isTiny}
                />
              )}
            </div>

            {/* Button row (hidden in tiny variant) */}
            {!isTiny && (
              <div className="flex gap-2 mt-4">
                <div
                  className="rounded"
                  style={{
                    width: isCompact ? 50 : 80,
                    height: isCompact ? 16 : 28,
                    backgroundColor: "var(--primary)",
                    borderRadius: `${effects.borderRadius}px`,
                  }}
                />
                <div
                  className="rounded"
                  style={{
                    width: isCompact ? 50 : 80,
                    height: isCompact ? 16 : 28,
                    backgroundColor: "var(--bg-surface)",
                    border: "1px solid var(--border)",
                    borderRadius: `${effects.borderRadius}px`,
                  }}
                />
              </div>
            )}
          </div>
        </div>

        {/* FAB */}
        <div
          className="absolute flex items-center justify-center"
          style={{
            bottom: isCompact ? 8 : 16,
            right: isCompact ? 8 : 16,
            width: isCompact ? 28 : 48,
            height: isCompact ? 28 : 48,
            backgroundColor: "var(--primary)",
            borderRadius: effects.fabRoundness === 100 ? "50%" : `${4 + (effects.fabRoundness / 100) * 24}px`,
            boxShadow: `0 4px 12px rgba(0,0,0,${effects.shadowStrength / 200})`,
          }}
        >
          <span
            style={{
              color: "white",
              fontSize: isCompact ? 14 : 20,
              fontWeight: "bold",
            }}
          >
            +
          </span>
        </div>
      </div>
    </div>
  );
};

/**
 * Preview card sub-component
 */
interface PreviewCardProps {
  title: string;
  status: "success" | "warning" | "error" | "info";
  effects: EffectSettings;
  isCompact: boolean;
  isTiny: boolean;
}

/**
 * Maps preview card status to StatusIndicator status type
 */
const mapPreviewStatusToIndicator = (status: "success" | "warning" | "error" | "info"): StatusType => {
  const statusMap: Record<string, StatusType> = {
    success: "completed",
    warning: "in_progress",
    error: "blocked",
    info: "not_started",
  };
  return statusMap[status];
};

const PreviewCard: React.FC<PreviewCardProps> = ({
  title,
  status,
  effects,
  isCompact,
  isTiny,
}) => {
  // Map preview status to StatusIndicator status type
  const indicatorStatus = mapPreviewStatusToIndicator(status);
  // Determine if this status should pulse (in_progress/warning and blocked/error statuses pulse)
  const shouldPulse = (status === "warning" || status === "error") && effects.pulsingStrength > 0;

  return (
    <div
      className="relative overflow-hidden"
      style={{
        backgroundColor: "var(--bg-surface)",
        borderRadius: `${effects.borderRadius}px`,
        padding: isCompact ? 8 : 16,
        border: "1px solid var(--border)",
        boxShadow: `0 4px 12px rgba(0,0,0,${effects.shadowStrength / 400})`,
      }}
    >
      {/* Glass overlay */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          backgroundColor: "var(--glass-bg)",
          opacity: effects.glassOpacity / 100,
          backdropFilter: `blur(${effects.glassBlur}px)`,
        }}
      />

      {/* Card content */}
      <div className="relative z-10">
        <div className="flex items-center justify-between mb-2">
          {/* Title */}
          {!isTiny ? (
            <span
              style={{
                fontSize: isCompact ? 8 : 14,
                fontWeight: 600,
                color: "var(--text-primary)",
                textShadow: effects.glowStrength > 0 
                  ? `0 0 ${effects.glowStrength * 0.1}px var(--glow-primary)` 
                  : "none",
              }}
            >
              {title}
            </span>
          ) : (
            <div
              style={{
                width: 30,
                height: 4,
                backgroundColor: "var(--text-primary)",
                opacity: 0.3,
                borderRadius: 2,
              }}
            />
          )}

          {/* Use the actual StatusIndicator molecule component */}
          <StatusIndicator
            status={indicatorStatus}
            pulse={shouldPulse}
            size={isCompact ? "sm" : "md"}
          />
        </div>

        {/* Content lines */}
        {!isTiny && (
          <>
            <div
              style={{
                width: "60%",
                height: isCompact ? 4 : 8,
                backgroundColor: "var(--text-tertiary)",
                opacity: 0.3,
                borderRadius: 4,
                marginBottom: isCompact ? 4 : 8,
              }}
            />
            <div
              style={{
                width: "40%",
                height: isCompact ? 4 : 8,
                backgroundColor: "var(--text-tertiary)",
                opacity: 0.3,
                borderRadius: 4,
              }}
            />
          </>
        )}
      </div>
    </div>
  );
};

ThemePreviewSkeleton.displayName = "ThemePreviewSkeleton";

export default ThemePreviewSkeleton;
