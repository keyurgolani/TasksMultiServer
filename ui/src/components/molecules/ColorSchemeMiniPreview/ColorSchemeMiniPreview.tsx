import React, { useMemo } from "react";
import { cn } from "../../../lib/utils";
import {
  type ColorTheme,
  type EffectSettings,
  getThemeCssVariables,
  fontThemes,
  defaultEffectSettings,
} from "../../../styles/themes";

/**
 * ColorSchemeMiniPreview Molecule Component
 *
 * A miniature UI preview component that displays a color scheme applied to
 * key UI elements. Used in the color scheme selection row to help users
 * visualize how each scheme looks before selecting it.
 *
 * Requirements: 35.1, 35.2, 35.3, 35.4, 35.5, 32.5
 * - Display miniature version of main preview with scheme applied
 * - Include key UI elements (header, card, button, text)
 * - Maintain aspect ratio consistent with main preview
 * - Provide subtle visual feedback on hover
 * - Apply appropriate border and shadow styling
 * - Highlight selected thumbnail with visual indicator
 */

export interface ColorSchemeMiniPreviewProps {
  /** Color scheme to apply to the preview */
  scheme: ColorTheme;
  /** Whether this scheme is currently selected */
  isSelected: boolean;
  /** Click handler for selecting this scheme */
  onClick: () => void;
  /** Size variant of the preview */
  size?: "sm" | "md" | "lg";
  /** Additional CSS classes */
  className?: string;
}

/**
 * Get dimensions based on size variant
 */
const getSizeDimensions = (size: "sm" | "md" | "lg") => {
  switch (size) {
    case "sm":
      return { width: 100, height: 64 };
    case "md":
      return { width: 140, height: 90 };
    case "lg":
      return { width: 180, height: 116 };
    default:
      return { width: 140, height: 90 };
  }
};

// Default font for preview (constant, doesn't change)
const DEFAULT_PREVIEW_FONT = fontThemes.inter;

// Default effects for preview (constant, doesn't change)
const DEFAULT_PREVIEW_EFFECTS: EffectSettings = {
  ...defaultEffectSettings,
  glassOpacity: 50,
  glassBlur: 8,
  shadowStrength: 30,
  borderRadius: 8,
};

/**
 * ColorSchemeMiniPreview component for color scheme selection
 */
export const ColorSchemeMiniPreview: React.FC<ColorSchemeMiniPreviewProps> = ({
  scheme,
  isSelected,
  onClick,
  size = "md",
  className,
}) => {
  // Generate CSS variables from theme settings
  const cssVars = useMemo(
    () => getThemeCssVariables(scheme, DEFAULT_PREVIEW_FONT, DEFAULT_PREVIEW_EFFECTS) as React.CSSProperties,
    [scheme]
  );

  const dimensions = getSizeDimensions(size);
  const isCompact = size === "sm";

  return (
    <button
      type="button"
      onClick={onClick}
      className={cn(
        "relative overflow-hidden rounded-lg transition-all duration-200",
        "focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2",
        "hover:scale-105 hover:shadow-lg",
        isSelected && "ring-2 ring-offset-2",
        className
      )}
      style={{
        ...cssVars,
        width: `${dimensions.width}px`,
        height: `${dimensions.height}px`,
        backgroundColor: "var(--bg-app)",
        borderColor: isSelected ? "var(--primary)" : "var(--border)",
        borderWidth: isSelected ? "2px" : "1px",
        borderStyle: "solid",
        boxShadow: isSelected
          ? `0 0 0 2px var(--primary), 0 4px 12px rgba(0,0,0,0.15)`
          : "0 2px 8px rgba(0,0,0,0.1)",
        // Ring color for focus and selection
        "--tw-ring-color": "var(--primary)",
        "--tw-ring-offset-color": "var(--bg-app)",
      } as React.CSSProperties}
      aria-pressed={isSelected}
      aria-label={`Select ${scheme.name} color scheme`}
    >
      {/* Mini UI Preview Content */}
      <div className="absolute inset-0 p-1">
        {/* Header */}
        <div
          className="flex items-center justify-between px-2 py-1 rounded-t"
          style={{
            backgroundColor: "var(--bg-surface)",
            borderBottom: "1px solid var(--border)",
          }}
        >
          {/* Logo placeholder */}
          <div
            className="rounded"
            style={{
              width: isCompact ? 16 : 24,
              height: isCompact ? 4 : 6,
              backgroundColor: "var(--text-primary)",
              opacity: 0.2,
            }}
          />
          {/* Avatar placeholder */}
          <div
            className="rounded-full"
            style={{
              width: isCompact ? 6 : 8,
              height: isCompact ? 6 : 8,
              backgroundColor: "var(--primary)",
              opacity: 0.8,
            }}
          />
        </div>

        {/* Content area */}
        <div className="flex p-1" style={{ height: `calc(100% - ${isCompact ? 16 : 20}px)` }}>
          {/* Sidebar */}
          <div
            className="flex flex-col gap-1 pr-1"
            style={{
              width: isCompact ? 20 : 28,
              borderRight: "1px solid var(--border)",
            }}
          >
            {[70, 50, 60].map((width, i) => (
              <div
                key={i}
                className="rounded"
                style={{
                  width: `${width}%`,
                  height: isCompact ? 2 : 3,
                  backgroundColor: "var(--text-primary)",
                  opacity: i === 0 ? 0.2 : 0.1,
                }}
              />
            ))}
          </div>

          {/* Main content */}
          <div className="flex-1 pl-1">
            {/* Title */}
            <div
              className="rounded mb-1"
              style={{
                width: isCompact ? 20 : 30,
                height: isCompact ? 3 : 4,
                backgroundColor: "var(--text-primary)",
                opacity: 0.2,
              }}
            />

            {/* Cards grid */}
            <div className="grid grid-cols-2 gap-1">
              {/* Card 1 - Success */}
              <MiniCard status="success" isCompact={isCompact} />
              {/* Card 2 - Warning */}
              <MiniCard status="warning" isCompact={isCompact} />
            </div>

            {/* Button row */}
            <div className="flex gap-1 mt-1">
              <div
                className="rounded"
                style={{
                  width: isCompact ? 14 : 20,
                  height: isCompact ? 4 : 6,
                  backgroundColor: "var(--primary)",
                }}
              />
              <div
                className="rounded"
                style={{
                  width: isCompact ? 14 : 20,
                  height: isCompact ? 4 : 6,
                  backgroundColor: "var(--bg-surface)",
                  border: "1px solid var(--border)",
                }}
              />
            </div>
          </div>
        </div>

        {/* FAB */}
        <div
          className="absolute flex items-center justify-center"
          style={{
            bottom: isCompact ? 3 : 4,
            right: isCompact ? 3 : 4,
            width: isCompact ? 8 : 12,
            height: isCompact ? 8 : 12,
            backgroundColor: "var(--primary)",
            borderRadius: "50%",
          }}
        >
          <span
            style={{
              color: "white",
              fontSize: isCompact ? 6 : 8,
              fontWeight: "bold",
              lineHeight: 1,
            }}
          >
            +
          </span>
        </div>
      </div>

      {/* Selection indicator overlay */}
      {isSelected && (
        <div
          className="absolute inset-0 pointer-events-none"
          style={{
            backgroundColor: "var(--primary)",
            opacity: 0.1,
          }}
        />
      )}
    </button>
  );
};

/**
 * Mini card sub-component for the preview
 */
interface MiniCardProps {
  status: "success" | "warning" | "error" | "info";
  isCompact: boolean;
}

const MiniCard: React.FC<MiniCardProps> = ({ status, isCompact }) => {
  const statusColors: Record<string, string> = {
    success: "var(--success)",
    warning: "var(--warning)",
    error: "var(--error)",
    info: "var(--info)",
  };

  return (
    <div
      className="rounded overflow-hidden"
      style={{
        backgroundColor: "var(--bg-surface)",
        padding: isCompact ? 2 : 3,
        border: "1px solid var(--border)",
      }}
    >
      <div className="flex items-center justify-between">
        {/* Title placeholder */}
        <div
          style={{
            width: isCompact ? 10 : 16,
            height: isCompact ? 2 : 3,
            backgroundColor: "var(--text-primary)",
            opacity: 0.3,
            borderRadius: 1,
          }}
        />
        {/* Status indicator */}
        <div
          style={{
            width: isCompact ? 3 : 4,
            height: isCompact ? 3 : 4,
            borderRadius: "50%",
            backgroundColor: statusColors[status],
          }}
        />
      </div>
      {/* Content line */}
      <div
        style={{
          width: "60%",
          height: isCompact ? 1 : 2,
          backgroundColor: "var(--text-tertiary)",
          opacity: 0.3,
          borderRadius: 1,
          marginTop: isCompact ? 1 : 2,
        }}
      />
    </div>
  );
};

ColorSchemeMiniPreview.displayName = "ColorSchemeMiniPreview";

export default ColorSchemeMiniPreview;
