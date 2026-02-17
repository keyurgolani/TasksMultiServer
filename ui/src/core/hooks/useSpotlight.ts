import { useState, useCallback, useRef, type MouseEvent, type RefObject } from 'react';
import { useTheme } from '../../context/ThemeContext';

/**
 * Spotlight position coordinates relative to the element
 */
export interface SpotlightPosition {
  x: number;
  y: number;
}

/**
 * CSS style object for spotlight gradient rendering
 */
export interface SpotlightStyle {
  '--mouse-x': string;
  '--mouse-y': string;
  '--spotlight-opacity': string;
}

/**
 * Return type for the useSpotlight hook
 */
export interface UseSpotlightReturn {
  /** Current spotlight position (0-100% relative to element) */
  position: SpotlightPosition;
  /** Whether the spotlight is currently active (mouse is over element) */
  isActive: boolean;
  /** Mouse enter handler to attach to the target element */
  onMouseEnter: () => void;
  /** Mouse move handler to attach to the target element */
  onMouseMove: (e: MouseEvent<HTMLElement>) => void;
  /** Mouse leave handler to attach to the target element */
  onMouseLeave: () => void;
  /** CSS variables for spotlight positioning */
  style: SpotlightStyle;
  /** Ref to attach to the target element (optional, for external ref usage) */
  ref: RefObject<HTMLElement | null>;
}

/**
 * Options for configuring the useSpotlight hook
 */
export interface UseSpotlightOptions {
  /**
   * Whether the spotlight effect is enabled
   * @default true
   */
  enabled?: boolean;
  /**
   * Opacity of the spotlight gradient (0-1)
   * If not provided, uses glow strength from theme settings
   */
  opacity?: number;
  /**
   * Size of the spotlight gradient in pixels
   * @default 200
   */
  size?: number;
}

/**
 * useSpotlight Hook
 * 
 * A hook for tracking mouse position within an element and rendering
 * a radial gradient spotlight effect following the cursor.
 * 
 * Requirements: 6.3
 * - Tracks mouse position and renders radial gradient following cursor
 * - Updates CSS variables --mouse-x and --mouse-y for gradient positioning
 * - Integrates with theme glow strength settings
 * 
 * @example
 * ```tsx
 * const { onMouseMove, onMouseLeave, onMouseEnter, style, isActive } = useSpotlight();
 * 
 * return (
 *   <div
 *     onMouseEnter={onMouseEnter}
 *     onMouseMove={onMouseMove}
 *     onMouseLeave={onMouseLeave}
 *     style={style}
 *     className={isActive ? 'spotlight-active' : ''}
 *   >
 *     Content with spotlight effect
 *   </div>
 * );
 * ```
 */
export const useSpotlight = (options: UseSpotlightOptions = {}): UseSpotlightReturn => {
  const { enabled = true, opacity } = options;
  const { activeEffectSettings } = useTheme();
  
  const ref = useRef<HTMLElement | null>(null);
  const [position, setPosition] = useState<SpotlightPosition>({ x: 50, y: 50 });
  const [isActive, setIsActive] = useState(false);

  /**
   * Calculate spotlight opacity based on theme glow strength or explicit opacity
   */
  const getSpotlightOpacity = useCallback((): number => {
    if (opacity !== undefined) {
      return opacity;
    }
    // Convert glow strength (0-100) to opacity (0-0.5)
    return (activeEffectSettings.glowStrength / 100) * 0.5;
  }, [opacity, activeEffectSettings.glowStrength]);

  /**
   * Handle mouse enter - activate spotlight
   */
  const onMouseEnter = useCallback(() => {
    if (!enabled) return;
    setIsActive(true);
  }, [enabled]);

  /**
   * Handle mouse movement - update spotlight position
   * Calculates position as percentage relative to element bounds
   */
  const onMouseMove = useCallback((e: MouseEvent<HTMLElement>) => {
    if (!enabled) return;
    
    const element = e.currentTarget;
    const rect = element.getBoundingClientRect();
    
    // Calculate mouse position relative to element (in pixels)
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    // Convert to percentage (0-100)
    const percentX = (x / rect.width) * 100;
    const percentY = (y / rect.height) * 100;
    
    // Clamp values to 0-100 range
    const clampedX = Math.max(0, Math.min(100, percentX));
    const clampedY = Math.max(0, Math.min(100, percentY));
    
    setPosition({ x: clampedX, y: clampedY });
    setIsActive(true);
  }, [enabled]);

  /**
   * Handle mouse leave - deactivate spotlight
   */
  const onMouseLeave = useCallback(() => {
    setIsActive(false);
    // Reset position to center when mouse leaves
    setPosition({ x: 50, y: 50 });
  }, []);

  /**
   * Generate CSS variables for spotlight positioning
   * These can be used in CSS to position a radial gradient
   */
  const style: SpotlightStyle = {
    '--mouse-x': `${position.x}%`,
    '--mouse-y': `${position.y}%`,
    '--spotlight-opacity': isActive && enabled ? String(getSpotlightOpacity()) : '0',
  };

  return {
    position,
    isActive: isActive && enabled,
    onMouseEnter,
    onMouseMove,
    onMouseLeave,
    style,
    ref,
  };
};

/**
 * Generate CSS for spotlight gradient background
 * This utility function creates the CSS string for a radial gradient
 * that follows the mouse position using CSS variables.
 * 
 * @param color - The color of the spotlight (default: primary color)
 * @param size - The size of the spotlight in pixels (default: 200)
 * @returns CSS background property value
 * 
 * @example
 * ```css
 * .spotlight-card {
 *   background: var(--bg-surface);
 * }
 * .spotlight-card::before {
 *   content: '';
 *   position: absolute;
 *   inset: 0;
 *   background: radial-gradient(
 *     200px circle at var(--mouse-x) var(--mouse-y),
 *     rgba(var(--primary-rgb), var(--spotlight-opacity)),
 *     transparent
 *   );
 *   pointer-events: none;
 * }
 * ```
 */
export const getSpotlightGradient = (
  color: string = 'var(--primary-rgb)',
  size: number = 200
): string => {
  return `radial-gradient(
    ${size}px circle at var(--mouse-x, 50%) var(--mouse-y, 50%),
    rgba(${color}, var(--spotlight-opacity, 0)),
    transparent
  )`;
};

export default useSpotlight;
