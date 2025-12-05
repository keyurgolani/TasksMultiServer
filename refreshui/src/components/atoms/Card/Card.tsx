import React, { useCallback, useState, useMemo, type MouseEvent } from "react";
import { cn } from "../../../lib/utils";
import { calculateParallaxShadow, baseShadows } from "./parallaxShadow";

/**
 * Card Atom Component
 *
 * A foundational card component with glassmorphism effect using CSS variables.
 * Supports multiple variants, padding sizes, and optional spotlight/tilt effects.
 *
 * Requirements: 3.3, 39.1, 39.2, 39.3, 39.4, 39.5
 * - Variants: glass, solid, outline
 * - Padding: none, sm, md, lg
 * - Glassmorphism effect using CSS variables (glass-opacity, glass-blur, glass-border-opacity)
 * - Optional spotlight glow effect following cursor
 * - Optional parallax tilt effect with additive shadow behavior
 * - Parallax shadow is additive to base shadow (card tilts in its current plane)
 * - Smooth transition for shadow changes on hover/unhover
 */

export type CardVariant = "glass" | "solid" | "outline";
export type CardPadding = "none" | "sm" | "md" | "lg";

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  /** Visual style variant */
  variant?: CardVariant;
  /** Padding size */
  padding?: CardPadding;
  /** Enable spotlight glow effect following cursor */
  spotlight?: boolean;
  /** Enable parallax tilt effect on hover */
  tilt?: boolean;
  /** Card content */
  children: React.ReactNode;
}

/** Base styles applied to all cards */
const baseStyles = [
  "relative",
  "overflow-hidden",
  "rounded-[var(--border-radius)]",
  "transition-all",
  "duration-[calc(var(--duration-normal)*1s)]",
  "ease-[var(--ease-default)]",
].join(" ");

/** 
 * Variant-specific styles
 * Note: Shadow is now handled dynamically via inline styles for parallax support
 * Requirements: 39.1 - Base shadow is displayed in default state
 */
const variantStyles: Record<CardVariant, string> = {
  glass: [
    "bg-[var(--glass-bg)]",
    "backdrop-blur-[var(--glass-blur)]",
    "border",
    "border-[var(--glass-border)]",
  ].join(" "),

  solid: [
    "bg-[var(--bg-surface)]",
    "border",
    "border-[var(--border)]",
  ].join(" "),

  outline: [
    "bg-transparent",
    "border-2",
    "border-[var(--border-strong)]",
  ].join(" "),
};

/** Padding-specific styles */
const paddingStyles: Record<CardPadding, string> = {
  none: "p-0",
  sm: "p-[var(--space-3)]",
  md: "p-[var(--space-4)]",
  lg: "p-[var(--space-6)]",
};

/**
 * Card component with glassmorphism effect and optional interactive features
 * 
 * Requirements: 39.1, 39.2, 39.3, 39.4, 39.5
 * - Base shadow is displayed in default state
 * - Parallax shadow is additive to base shadow on hover
 * - Base shadow opacity and blur values are maintained
 * - Only parallax shadow offset changes while preserving base shadow
 * - Smooth transition back to only base shadow on unhover
 */
export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  (
    {
      variant = "glass",
      padding = "md",
      spotlight = false,
      tilt = false,
      children,
      className,
      style,
      onMouseMove: externalOnMouseMove,
      onMouseLeave: externalOnMouseLeave,
      ...props
    },
    ref
  ) => {
    // State for spotlight effect
    const [mousePosition, setMousePosition] = useState({ x: 50, y: 50 });
    
    // State for tilt effect
    const [tiltStyle, setTiltStyle] = useState({
      rotateX: 0,
      rotateY: 0,
      scale: 1,
    });
    const [isHovered, setIsHovered] = useState(false);

    const handleMouseMove = useCallback(
      (e: MouseEvent<HTMLDivElement>) => {
        const card = e.currentTarget;
        const rect = card.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;

        // Update spotlight position (as percentage)
        if (spotlight) {
          const percentX = (x / rect.width) * 100;
          const percentY = (y / rect.height) * 100;
          setMousePosition({ x: percentX, y: percentY });
        }

        // Update tilt rotation
        if (tilt) {
          const centerX = rect.width / 2;
          const centerY = rect.height / 2;
          const normalizedX = (x - centerX) / centerX;
          const normalizedY = (y - centerY) / centerY;

          // Use CSS variable for parallax depth, default to 20
          const maxTilt = 8; // Maximum tilt in degrees
          setTiltStyle({
            rotateX: -normalizedY * maxTilt,
            rotateY: normalizedX * maxTilt,
            scale: 1.02,
          });
        }

        // Call external handler if provided
        externalOnMouseMove?.(e);
      },
      [spotlight, tilt, externalOnMouseMove]
    );

    const handleMouseLeave = useCallback(
      (e: MouseEvent<HTMLDivElement>) => {
        setIsHovered(false);
        
        // Reset spotlight to center
        if (spotlight) {
          setMousePosition({ x: 50, y: 50 });
        }

        // Reset tilt
        if (tilt) {
          setTiltStyle({ rotateX: 0, rotateY: 0, scale: 1 });
        }

        // Call external handler if provided
        externalOnMouseLeave?.(e);
      },
      [spotlight, tilt, externalOnMouseLeave]
    );

    const handleMouseEnter = useCallback(() => {
      setIsHovered(true);
    }, []);

    /**
     * Calculate the combined shadow (base + parallax)
     * Requirements: 39.2, 39.3, 39.4
     * - Add parallax shadow to existing base shadow
     * - Maintain base shadow opacity and blur values
     * - Adjust only parallax shadow offset while preserving base shadow
     */
    const combinedShadow = useMemo(() => {
      const baseShadow = baseShadows[variant];
      
      // If tilt is not enabled, just use base shadow
      if (!tilt) {
        return baseShadow;
      }
      
      // Calculate parallax shadow based on current tilt
      const parallaxShadow = calculateParallaxShadow(
        tiltStyle.rotateX,
        tiltStyle.rotateY,
        isHovered
      );
      
      // Combine shadows: base shadow + parallax shadow (additive)
      // Requirements: 39.2 - Add parallax shadow to existing base shadow
      if (parallaxShadow === "none" || baseShadow === "none") {
        return baseShadow === "none" ? parallaxShadow : baseShadow;
      }
      
      return `${baseShadow}, ${parallaxShadow}`;
    }, [variant, tilt, tiltStyle.rotateX, tiltStyle.rotateY, isHovered]);

    // Compute combined styles
    // Requirements: 39.5 - Smooth transition for shadow changes
    const computedStyle: React.CSSProperties = {
      ...style,
      // CSS custom properties for spotlight effect
      "--mouse-x": `${mousePosition.x}%`,
      "--mouse-y": `${mousePosition.y}%`,
      // Apply combined shadow (base + parallax)
      boxShadow: combinedShadow,
      // Tilt transform
      ...(tilt && {
        transform: `
          perspective(1000px)
          rotateX(${tiltStyle.rotateX}deg)
          rotateY(${tiltStyle.rotateY}deg)
          scale(${tiltStyle.scale})
        `,
        // Requirements: 39.5 - Smooth transition for shadow changes on hover/unhover
        transition: isHovered
          ? "transform 0.1s ease-out, box-shadow 0.1s ease-out"
          : "transform 0.3s ease-out, box-shadow 0.3s ease-out",
        transformStyle: "preserve-3d" as const,
      }),
      // Add shadow transition even when tilt is disabled (for consistency)
      ...(!tilt && {
        transition: "box-shadow 0.3s ease-out",
      }),
    } as React.CSSProperties;

    // Interactive styles for hover effects
    const interactiveStyles = (spotlight || tilt) ? "cursor-pointer" : "";

    return (
      <div
        ref={ref}
        className={cn(
          baseStyles,
          variantStyles[variant],
          paddingStyles[padding],
          interactiveStyles,
          className
        )}
        style={computedStyle}
        onMouseMove={(spotlight || tilt) ? handleMouseMove : externalOnMouseMove}
        onMouseLeave={(spotlight || tilt) ? handleMouseLeave : externalOnMouseLeave}
        onMouseEnter={(spotlight || tilt) ? handleMouseEnter : undefined}
        {...props}
      >
        {/* Spotlight overlay */}
        {spotlight && (
          <div
            className="absolute inset-0 pointer-events-none opacity-[calc(var(--glow-strength)/100)]"
            style={{
              background: `radial-gradient(
                circle at var(--mouse-x) var(--mouse-y),
                var(--glow-primary) 0%,
                transparent 50%
              )`,
              transition: "opacity var(--duration-fast) var(--ease-out)",
            }}
            aria-hidden="true"
          />
        )}
        {/* Card content */}
        <div className="relative z-[1]">{children}</div>
      </div>
    );
  }
);

Card.displayName = "Card";

export default Card;
