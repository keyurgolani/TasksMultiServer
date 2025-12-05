import React from "react";
import { Typography } from "../../atoms/Typography";

/**
 * GlassBlurDemo Component
 *
 * Demonstrates the glass blur effect at varying blur values.
 * Shows multiple cards with different blur intensities to help
 * developers understand how the effect works.
 *
 * Requirements: 37.1, 37.2, 37.3, 37.4
 * - Display dedicated glass blur demonstration section
 * - Show multiple cards with varying blur values
 * - Update in real-time when customization engine values change
 * - Include background pattern to make blur effect visible
 */

export interface GlassBlurDemoProps {
  /** Current glass blur value from customization engine (in pixels) */
  glassBlur?: number;
  /** Current glass opacity value from customization engine (0-1) */
  glassOpacity?: number;
  /** Current glass border opacity value from customization engine (0-1) */
  glassBorderOpacity?: number;
}

// Predefined blur values to demonstrate the effect
const BLUR_VALUES = [0, 4, 8, 12, 16, 20];

export const GlassBlurDemo: React.FC<GlassBlurDemoProps> = ({
  glassBlur,
  glassOpacity = 0.7,
  glassBorderOpacity = 0.3,
}) => {
  return (
    <div className="space-y-4">
      {/* Background pattern container */}
      <div
        className="relative rounded-lg overflow-hidden p-6"
        style={{
          background: `
            linear-gradient(135deg, 
              var(--primary) 0%, 
              var(--info) 50%, 
              var(--success) 100%
            )
          `,
          minHeight: "200px",
        }}
      >
        {/* Decorative pattern overlay to make blur more visible */}
        <div
          className="absolute inset-0 opacity-30"
          style={{
            backgroundImage: `
              repeating-linear-gradient(
                45deg,
                transparent,
                transparent 10px,
                rgba(255, 255, 255, 0.1) 10px,
                rgba(255, 255, 255, 0.1) 20px
              ),
              repeating-linear-gradient(
                -45deg,
                transparent,
                transparent 10px,
                rgba(0, 0, 0, 0.1) 10px,
                rgba(0, 0, 0, 0.1) 20px
              )
            `,
          }}
        />

        {/* Decorative circles to show blur effect */}
        <div className="absolute inset-0 overflow-hidden">
          <div
            className="absolute w-32 h-32 rounded-full"
            style={{
              background: "rgba(255, 255, 255, 0.3)",
              top: "10%",
              left: "5%",
            }}
          />
          <div
            className="absolute w-24 h-24 rounded-full"
            style={{
              background: "rgba(0, 0, 0, 0.2)",
              top: "50%",
              right: "10%",
            }}
          />
          <div
            className="absolute w-16 h-16 rounded-full"
            style={{
              background: "rgba(255, 255, 255, 0.4)",
              bottom: "15%",
              left: "30%",
            }}
          />
          <div
            className="absolute w-20 h-20 rounded-full"
            style={{
              background: "var(--warning)",
              opacity: 0.5,
              top: "20%",
              right: "30%",
            }}
          />
        </div>

        {/* Glass blur cards */}
        <div className="relative z-10 flex flex-wrap gap-4 justify-center">
          {BLUR_VALUES.map((blur) => {
            // Use the customization engine value if provided, otherwise use the predefined blur
            const effectiveBlur = glassBlur !== undefined ? glassBlur : blur;
            const isCurrentValue = glassBlur !== undefined && blur === 0;

            return (
              <div
                key={blur}
                className="flex flex-col items-center"
              >
                <div
                  className="w-28 h-20 rounded-lg flex items-center justify-center transition-all duration-300"
                  style={{
                    background: `rgba(255, 255, 255, ${glassOpacity})`,
                    backdropFilter: `blur(${glassBlur !== undefined ? effectiveBlur : blur}px)`,
                    WebkitBackdropFilter: `blur(${glassBlur !== undefined ? effectiveBlur : blur}px)`,
                    border: `1px solid rgba(255, 255, 255, ${glassBorderOpacity})`,
                    boxShadow: "0 4px 16px rgba(0, 0, 0, 0.1)",
                  }}
                >
                  <Typography
                    variant="h6"
                    className="text-gray-800 font-semibold"
                  >
                    {glassBlur !== undefined ? `${effectiveBlur}px` : `${blur}px`}
                  </Typography>
                </div>
                <Typography
                  variant="caption"
                  className="mt-2 text-white font-medium"
                  style={{ textShadow: "0 1px 2px rgba(0, 0, 0, 0.5)" }}
                >
                  {glassBlur !== undefined
                    ? isCurrentValue
                      ? "Current"
                      : `Blur: ${effectiveBlur}px`
                    : `Blur: ${blur}px`}
                </Typography>
              </div>
            );
          })}
        </div>
      </div>

      {/* Current value indicator when connected to customization engine */}
      {glassBlur !== undefined && (
        <div className="flex items-center gap-2 text-sm">
          <div
            className="w-3 h-3 rounded-full"
            style={{ background: "var(--primary)" }}
          />
          <Typography variant="caption" color="secondary">
            Current glass blur value: <strong>{glassBlur}px</strong> (from customization engine)
          </Typography>
        </div>
      )}
    </div>
  );
};

export default GlassBlurDemo;
