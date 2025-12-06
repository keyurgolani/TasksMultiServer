import { useState, useCallback, useRef, type MouseEvent, type RefObject } from 'react';

/**
 * Parallax rotation values for 3D tilt effect
 */
export interface ParallaxRotation {
  /** Rotation around X-axis (vertical tilt) in degrees */
  rotateX: number;
  /** Rotation around Y-axis (horizontal tilt) in degrees */
  rotateY: number;
}

/**
 * CSS style object for parallax transform rendering
 */
export interface ParallaxStyle {
  transform: string;
  transition: string;
  willChange: string;
}

/**
 * Return type for the useParallax hook
 */
export interface UseParallaxReturn {
  /** Current rotation values in degrees */
  rotation: ParallaxRotation;
  /** Whether the parallax effect is currently active (mouse is over element) */
  isActive: boolean;
  /** Mouse enter handler to attach to the target element */
  onMouseEnter: () => void;
  /** Mouse move handler to attach to the target element */
  onMouseMove: (e: MouseEvent<HTMLElement>) => void;
  /** Mouse leave handler to attach to the target element */
  onMouseLeave: () => void;
  /** CSS transform style for parallax effect */
  style: ParallaxStyle;
  /** Ref to attach to the target element (optional, for external ref usage) */
  ref: RefObject<HTMLElement | null>;
}

/**
 * Options for configuring the useParallax hook
 */
export interface UseParallaxOptions {
  /**
   * Whether the parallax effect is enabled
   * @default true
   */
  enabled?: boolean;
  /**
   * Maximum rotation angle in degrees (0-45)
   * If not provided, uses parallax strength from theme settings
   * Theme parallaxStrength (0-100) is converted to degrees (0-15)
   */
  maxRotation?: number;
  /**
   * Perspective distance in pixels for 3D effect
   * @default 1000
   */
  perspective?: number;
  /**
   * Scale factor when hovering (1.0 = no scale)
   * @default 1.0
   */
  scale?: number;
}

/**
 * Calculate rotation values based on mouse position relative to element center
 * 
 * @param mouseX - Mouse X position relative to element (in pixels)
 * @param mouseY - Mouse Y position relative to element (in pixels)
 * @param width - Element width in pixels
 * @param height - Element height in pixels
 * @param maxRotation - Maximum rotation angle in degrees
 * @returns ParallaxRotation with rotateX and rotateY values
 */
export const calculateParallaxRotation = (
  mouseX: number,
  mouseY: number,
  width: number,
  height: number,
  maxRotation: number
): ParallaxRotation => {
  // Calculate center of element
  const centerX = width / 2;
  const centerY = height / 2;
  
  // Calculate offset from center (-1 to 1 range)
  const normalizedX = (mouseX - centerX) / centerX;
  const normalizedY = (mouseY - centerY) / centerY;
  
  // Clamp normalized values to -1 to 1 range
  const clampedX = Math.max(-1, Math.min(1, normalizedX));
  const clampedY = Math.max(-1, Math.min(1, normalizedY));
  
  // Calculate rotation proportional to offset, bounded by maxRotation
  // rotateY: positive when mouse is right of center (tilt right edge toward viewer)
  // rotateX: negative when mouse is below center (tilt bottom edge toward viewer)
  const rotateY = clampedX * maxRotation;
  const rotateX = -clampedY * maxRotation;
  
  return { rotateX, rotateY };
};

/**
 * Convert theme parallax strength (0-100) to max rotation degrees (0-10)
 * 
 * Requirements: 1.18, 3.7, 4.9, 5.7, 6.9, 7.8
 * - Maximum tilt capped at ~8-10 degrees (avoid excessive rotation)
 * - Default parallax strength of 20-30 out of 100
 * 
 * @param parallaxStrength - Theme parallax strength value (0-100)
 * @returns Maximum rotation angle in degrees (0-10)
 */
export const parallaxStrengthToMaxRotation = (parallaxStrength: number): number => {
  // Convert 0-100 range to 0-10 degrees
  // This provides a professional range where 100 = 10 degrees max tilt
  // At default strength 25, max tilt is 2.5 degrees (subtle and professional)
  return (parallaxStrength / 100) * 10;
};

/**
 * Read parallax strength directly from CSS variable for zero-render updates
 * 
 * Requirements: 36.4
 * - Update CSS variable immediately without re-renders
 * 
 * @returns Parallax strength value (0-100)
 */
export const getParallaxStrengthFromCSS = (): number => {
  if (typeof document === 'undefined') return 20; // Default for SSR
  const value = getComputedStyle(document.documentElement).getPropertyValue('--parallax-strength').trim();
  const parsed = parseFloat(value);
  return isNaN(parsed) ? 20 : parsed;
};

/**
 * useParallax Hook
 * 
 * A hook for creating 3D tilt/parallax effects on elements based on mouse position.
 * The rotation is calculated relative to the element center and bounded by the
 * configured parallax depth.
 * 
 * Requirements: 6.4, 36.1, 36.2, 36.3, 36.4
 * - Calculates rotation based on mouse position relative to card center
 * - Rotation values are proportional to the offset from center
 * - Rotation is bounded by parallax-depth (parallaxStrength from CSS variable)
 * - When parallax strength is 0, the effect is disabled entirely
 * - When parallax strength is at maximum (100), applies most pronounced tilt
 * - Reads from CSS variable for immediate updates without re-renders
 * 
 * @example
 * ```tsx
 * const { onMouseMove, onMouseLeave, onMouseEnter, style, isActive } = useParallax();
 * 
 * return (
 *   <div
 *     onMouseEnter={onMouseEnter}
 *     onMouseMove={onMouseMove}
 *     onMouseLeave={onMouseLeave}
 *     style={style}
 *     className={isActive ? 'parallax-active' : ''}
 *   >
 *     Content with 3D tilt effect
 *   </div>
 * );
 * ```
 */
export const useParallax = (options: UseParallaxOptions = {}): UseParallaxReturn => {
  const { enabled = true, maxRotation, perspective = 1000, scale = 1.0 } = options;
  
  const ref = useRef<HTMLElement | null>(null);
  const [rotation, setRotation] = useState<ParallaxRotation>({ rotateX: 0, rotateY: 0 });
  const [isActive, setIsActive] = useState(false);

  /**
   * Get the effective max rotation based on options or CSS variable
   * Reads directly from CSS variable for zero-render updates (Requirement 36.4)
   */
  const getMaxRotation = useCallback((): number => {
    if (maxRotation !== undefined) {
      return maxRotation;
    }
    // Read parallax strength directly from CSS variable for immediate updates
    const parallaxStrength = getParallaxStrengthFromCSS();
    // Convert theme parallaxStrength (0-100) to degrees (0-15)
    return parallaxStrengthToMaxRotation(parallaxStrength);
  }, [maxRotation]);

  /**
   * Handle mouse enter - activate parallax
   */
  const onMouseEnter = useCallback(() => {
    if (!enabled) return;
    setIsActive(true);
  }, [enabled]);

  /**
   * Handle mouse movement - update rotation based on position
   * Calculates rotation proportional to offset from element center
   */
  const onMouseMove = useCallback((e: MouseEvent<HTMLElement>) => {
    if (!enabled) return;
    
    const element = e.currentTarget;
    const rect = element.getBoundingClientRect();
    
    // Calculate mouse position relative to element (in pixels)
    const mouseX = e.clientX - rect.left;
    const mouseY = e.clientY - rect.top;
    
    // Calculate rotation bounded by max rotation
    const effectiveMaxRotation = getMaxRotation();
    const newRotation = calculateParallaxRotation(
      mouseX,
      mouseY,
      rect.width,
      rect.height,
      effectiveMaxRotation
    );
    
    setRotation(newRotation);
    setIsActive(true);
  }, [enabled, getMaxRotation]);

  /**
   * Handle mouse leave - reset rotation with smooth transition
   */
  const onMouseLeave = useCallback(() => {
    setIsActive(false);
    // Reset rotation to neutral position
    setRotation({ rotateX: 0, rotateY: 0 });
  }, []);

  /**
   * Generate CSS transform style for parallax effect
   * Uses perspective for 3D depth and applies rotation values
   */
  const style: ParallaxStyle = {
    transform: enabled && isActive
      ? `perspective(${perspective}px) rotateX(${rotation.rotateX}deg) rotateY(${rotation.rotateY}deg) scale(${scale})`
      : `perspective(${perspective}px) rotateX(0deg) rotateY(0deg) scale(1)`,
    transition: isActive 
      ? 'transform 0.1s ease-out' 
      : 'transform 0.3s ease-out',
    willChange: 'transform',
  };

  return {
    rotation,
    isActive: isActive && enabled,
    onMouseEnter,
    onMouseMove,
    onMouseLeave,
    style,
    ref,
  };
};

export default useParallax;
